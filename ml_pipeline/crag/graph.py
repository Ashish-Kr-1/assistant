"""
LangGraph Orchestration for Corrective RAG (CRAG.md §1, §4).
Compiles the state graph with nodes for retrieval, grading, fallback, generation,
verification, and output assembly enforcing rules R1-R10.
"""

import logging
from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from ml_pipeline.crag.schema import (
    CRAGState,
    LegalChunk,
    GradingOutcome,
    JurisdictionType,
    ProvenanceStatus
)
from ml_pipeline.embeddings.vector_store_manager import VectorStoreManager
from ml_pipeline.crag.grader import RelevanceGrader
from ml_pipeline.crag.generator import GroundedGenerator
from ml_pipeline.crag.verifier import CitationVerifier
from ml_pipeline.crag.assembler import OutputAssembler

logger = logging.getLogger("crag_graph")


class CRAGPipeline:
    """
    End-to-end Corrective RAG (CRAG) pipeline backed by LangGraph.
    """

    def __init__(self, vector_store: VectorStoreManager = None):
        self.vector_store = vector_store or VectorStoreManager()
        self.grader = RelevanceGrader()
        self.generator = GroundedGenerator()
        self.verifier = CitationVerifier()
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(CRAGState)

        # Register nodes
        workflow.add_node("retrieve", self._node_retrieve)
        workflow.add_node("grade", self._node_grade)
        workflow.add_node("fallback", self._node_fallback)
        workflow.add_node("generate", self._node_generate)
        workflow.add_node("verify", self._node_verify)
        workflow.add_node("assemble", self._node_assemble)
        workflow.add_node("abstain", self._node_abstain)

        # Set entry point
        workflow.set_entry_point("retrieve")

        # Edges
        workflow.add_edge("retrieve", "grade")
        workflow.add_conditional_edges(
            "grade",
            self._edge_post_grade,
            {
                "fallback": "fallback",
                "generate": "generate",
                "abstain": "abstain"
            }
        )
        workflow.add_edge("fallback", "grade")
        workflow.add_edge("generate", "verify")
        workflow.add_edge("verify", "assemble")
        workflow.add_edge("assemble", END)
        workflow.add_edge("abstain", "assemble")

        return workflow.compile()

    # --- NODE IMPLEMENTATIONS ---

    def _node_retrieve(self, state: CRAGState) -> Dict[str, Any]:
        """Retrieves top legal chunks filtered by jurisdiction and provenance (R4, R7). Also checks ABS pointer."""
        logger.info(f"Retrieving chunks for query: '{state.query}' [{state.jurisdiction}]")
        chunks = self.vector_store.search(
            query=state.query,
            jurisdiction=state.jurisdiction,
            top_k=4,
            exclude_mock=True
        )
        
        # Rule-based ABS check (CRAG.md §3.6)
        from ml_pipeline.crag.abs_pointer import ABSPointer
        abs_flag = ABSPointer.evaluate(state.query)

        return {
            "retrieved_chunks": chunks,
            "abs_pointer": abs_flag if abs_flag.triggered else None
        }

    def _node_grade(self, state: CRAGState) -> Dict[str, Any]:
        """Grades retrieved chunks: CORRECT / AMBIGUOUS / INCORRECT."""
        graded = self.grader.grade_batch(state.query, state.retrieved_chunks)
        correct = [g.chunk for g in graded if g.outcome == GradingOutcome.CORRECT]
        return {
            "graded_chunks": graded,
            "correct_chunks": correct
        }

    def _node_fallback(self, state: CRAGState) -> Dict[str, Any]:
        """Broadens search within the same jurisdiction scope when initial results are ambiguous (R4)."""
        logger.info(f"Triggering fallback retrieval within jurisdiction scope [{state.jurisdiction}]...")
        fallback = self.vector_store.search(
            query=state.query,
            jurisdiction=state.jurisdiction,
            top_k=6,
            exclude_mock=True
        )
        # Deduplicate
        existing_ids = {c.chunk_id for c in state.retrieved_chunks}
        new_chunks = [c for c in fallback if c.chunk_id not in existing_ids]
        combined = state.retrieved_chunks + new_chunks
        return {
            "retrieved_chunks": combined,
            "fallback_triggered": True
        }

    def _node_generate(self, state: CRAGState) -> Dict[str, Any]:
        """Grounded answer generation from verified/correct chunks or retrieved context."""
        active_chunks = state.correct_chunks
        if not active_chunks:
            ambiguous = [g.chunk for g in state.graded_chunks if g.outcome == GradingOutcome.AMBIGUOUS]
            active_chunks = ambiguous if ambiguous else state.retrieved_chunks

        answers = self.generator.generate_answer(
            query=state.query,
            chunks=active_chunks,
            jurisdiction=state.jurisdiction
        )
        return {"generated_answers": answers}

    def _node_verify(self, state: CRAGState) -> Dict[str, Any]:
        """Citation entailment and orphan claim audit (R2, R3)."""
        chunk_map = {c.chunk_id: c for c in state.retrieved_chunks}
        sanitized_answers: Dict[str, str] = {}
        all_verifications = []
        ratios = []

        for regime, text in state.generated_answers.items():
            clean_text, verifs, ratio = self.verifier.audit_and_sanitize(text, chunk_map)
            sanitized_answers[regime] = clean_text
            all_verifications.extend(verifs)
            ratios.append(ratio)

        avg_ratio = sum(ratios) / max(len(ratios), 1)
        return {
            "generated_answers": sanitized_answers,
            "verifications": all_verifications,
            "confidence_score": avg_ratio
        }

    def _node_abstain(self, state: CRAGState) -> Dict[str, Any]:
        """Rule R1 Safe Abstention."""
        return {
            "is_abstained": True,
            "generated_answers": {}
        }

    def _node_assemble(self, state: CRAGState) -> Dict[str, Any]:
        """Assembles final API dictionary with mandatory disclaimer (R5) and confidence (R8)."""
        active_chunks = state.correct_chunks or [g.chunk for g in state.graded_chunks if g.outcome == GradingOutcome.AMBIGUOUS]
        response = OutputAssembler.assemble_response(
            query=state.query,
            jurisdiction=state.jurisdiction.value,
            answers_by_regime=state.generated_answers,
            verified_chunks=active_chunks,
            verification_ratio=state.confidence_score,
            is_abstained=state.is_abstained,
            abs_flag=state.abs_pointer
        )
        return {"final_output": response}

    # --- CONDITIONAL ROUTER EDGES ---

    def _edge_post_grade(self, state: CRAGState) -> str:
        """Determines routing following the CRAG relevance grading pass (Rule R1 Safe Abstention)."""
        correct_count = len(state.correct_chunks)
        ambiguous_count = len([g for g in state.graded_chunks if g.outcome == GradingOutcome.AMBIGUOUS])
        incorrect_count = len([g for g in state.graded_chunks if g.outcome == GradingOutcome.INCORRECT])

        # If we have at least one high-confidence correct chunk
        if correct_count >= 1:
            return "generate"

        # If all retrieved chunks are INCORRECT
        if incorrect_count == len(state.graded_chunks) and len(state.graded_chunks) > 0:
            if not state.fallback_triggered:
                return "fallback"
            return "abstain"  # Rule R1: Abstain when all sources fail

        # If results are ambiguous and fallback hasn't fired yet
        if ambiguous_count > 0 and not state.fallback_triggered:
            return "fallback"

        # If fallback already fired and still ambiguous, generate from ambiguous
        if ambiguous_count > 0:
            return "generate"

        return "abstain"

    def _run_single_jurisdiction(
        self,
        query: str,
        jurisdiction: JurisdictionType,
        formulation_category: str = None
    ) -> Dict[str, Any]:
        """Executes the full CRAG graph strictly within a single isolated jurisdiction."""
        initial_state = CRAGState(
            query=query,
            jurisdiction=jurisdiction,
            formulation_category=formulation_category,
            formulation_classified=bool(formulation_category)
        )
        final_state = self.graph.invoke(initial_state)
        return final_state["final_output"]

    def run(
        self,
        query: str,
        jurisdiction: str = "national",
        skip_classification_gate: bool = True,
        formulation_category: str = None
    ) -> Dict[str, Any]:
        """
        Runs the pipeline for an end-user query directly without blocking gates.
        """
        target_jurisdiction = JurisdictionType.from_str(jurisdiction)

        if target_jurisdiction == JurisdictionType.BOTH:
            # Rule R4: Run two separate retrieval + answer calls, one per jurisdiction
            res_nat = self._run_single_jurisdiction(
                query=query,
                jurisdiction=JurisdictionType.NATIONAL,
                formulation_category=formulation_category
            )
            res_intl = self._run_single_jurisdiction(
                query=query,
                jurisdiction=JurisdictionType.INTERNATIONAL,
                formulation_category=formulation_category
            )

            # Deduplicate and combine citations
            seen_ids = set()
            combined_citations = []
            for c in res_nat.get("citations", []) + res_intl.get("citations", []):
                cid = c.get("chunk_id")
                if cid and cid not in seen_ids:
                    seen_ids.add(cid)
                    combined_citations.append(c)
                elif not cid:
                    combined_citations.append(c)

            both_abstained = res_nat.get("is_abstained", False) and res_intl.get("is_abstained", False)

            scores = []
            if not res_nat.get("is_abstained"):
                scores.append(res_nat.get("confidence_score", 0.0))
            if not res_intl.get("is_abstained"):
                scores.append(res_intl.get("confidence_score", 0.0))
            avg_score = round(sum(scores) / max(len(scores), 1), 2)

            # Separate clearly labeled sections
            sections = []
            if not res_nat.get("is_abstained"):
                sections.append(f"### National (India) Legal Regime\n\n{res_nat.get('answer', '')}")
            else:
                sections.append(f"### National (India) Legal Regime\n\n*No verified Indian statutory source found for this query under safe abstention protocols.*")

            if not res_intl.get("is_abstained"):
                sections.append(f"### International Legal Regime\n\n{res_intl.get('answer', '')}")
            else:
                sections.append(f"### International Legal Regime\n\n*No verified international treaty source found for this query under safe abstention protocols.*")

            composite_answer = "\n\n---\n\n".join(sections)

            return {
                "query": query,
                "jurisdiction": "both",
                "is_abstained": both_abstained,
                "answer": composite_answer if not both_abstained else OutputAssembler.ABSTENTION_TEMPLATE,
                "answers_by_regime": {
                    "national": res_nat.get("answer", ""),
                    "international": res_intl.get("answer", "")
                },
                "citations": combined_citations,
                "confidence_score": avg_score if not both_abstained else 0.0,
                "confidence_level": "HIGH" if avg_score >= 0.85 else ("MEDIUM" if avg_score >= 0.50 else "LOW"),
                "escalate_to_human": both_abstained,
                "escalation_reason": "Insufficient verified statutory sources across both jurisdictions." if both_abstained else None,
                "abs_guidance": res_nat.get("abs_guidance") or res_intl.get("abs_guidance"),
                "disclaimer": OutputAssembler.MANDATORY_DISCLAIMER
            }

        return self._run_single_jurisdiction(
            query=query,
            jurisdiction=target_jurisdiction,
            formulation_category=formulation_category
        )
