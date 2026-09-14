"""
Innovation Intake Agent (Phase 2 — IP-SAKTI Sahayak PS045)

Answers only: "What exactly is the user's innovation?"
Never answers: "Is it patentable / does ABS apply / is it compliant?"

Responsibilities (per CRAG.md-style guardrails for this phase):
- Extract ONLY facts the user actually stated (zero invention).
- Merge new facts into the existing InnovationProfile without erasing or
  duplicating prior information.
- Decide what information is still missing and the single next useful
  question — never a giant form.
- Never emit a legal/regulatory/patentability conclusion.

Extraction is deterministic (regex/keyword-based), reusing Phase 1's
IntentRuleEngine.extract_entities() for ingredients/jurisdiction/IP-type
detection rather than re-implementing it. This keeps Phase 2 correctness
independent of LLM availability, consistent with the project's existing
"never assume an API key is present" convention (see ml_pipeline/crag/llm_factory.py).
"""

import re
from typing import List, Optional, Tuple

from ml_pipeline.classifier.intent_rules import IntentRuleEngine
from ml_pipeline.schemas.intent_schema import Entities
from ml_pipeline.schemas.case_schema import (
    InnovationProfile,
    IntakeState,
    IntakeStatus,
    DevelopmentStage,
    IPObjective,
    TKBasis,
    FieldProvenance,
)

# Product types that make the formulation/TK questions relevant.
_FORMULATION_LIKE_TYPES = {
    "TABLET", "CAPSULE", "POWDER", "OIL", "CREAM", "FOOD", "COSMETIC",
    "FORMULATION", "AYURVEDIC_FORMULATION", "MEDICINE", "BALM", "OINTMENT",
    "GEL", "SYRUP", "PASTE", "LOTION", "DROPS", "SPRAY", "CHURNA", "KWATH",
    "BHASMA", "TAILA", "GHRITA", "ASAVA", "ARISHTA", "LEPA",
}

_PRODUCT_TYPE_KEYWORDS = [
    "tablet", "capsule", "powder", "oil", "cream", "food", "cosmetic",
    "device", "process", "software", "formulation", "balm", "ointment",
    "gel", "syrup", "paste", "lotion", "drops", "spray", "churna", "kwath",
    "bhasma", "taila", "ghrita", "lepa",
]

_DEVELOPMENT_STAGE_KEYWORDS = {
    "idea": DevelopmentStage.IDEA,
    "prototype": DevelopmentStage.PROTOTYPE,
    "research stage": DevelopmentStage.RESEARCH,
    "under research": DevelopmentStage.RESEARCH,
    "pilot": DevelopmentStage.PILOT,
    "commercial": DevelopmentStage.COMMERCIAL,
    "already selling": DevelopmentStage.COMMERCIAL,
    "in the market": DevelopmentStage.COMMERCIAL,
}

_TK_NONE_PATTERNS = [
    r"\bown\b",
    r"\bmy own\b",
    r"\bmine\b",
    r"\bit is my\b",
    r"\bit is mine\b",
    r"\bmy formulation\b",
    r"\bown formulation\b",
    r"\bself\b",
    r"\bours\b",
    r"\bcreated by (me|us)\b",
    r"\bdeveloped by (me|us)\b",
    r"\bformulated by (me|us)\b",
    r"\binvented by (me|us)\b",
    r"\bnew formulation\b",
    r"\bnovel formulation\b",
    r"\bproprietary\b",
    r"\bmodern\b",
    r"\boriginal\b",
    r"\bnot based on\b",
    r"\bnovel combination\b",
    r"\bnot from a classical\b",
    r"\bnot from (any )?text\b",
    r"\bno classical\b",
    r"\bnot classical\b",
    r"\bnot traditional\b",
    r"\bno\b",
    r"\bneither\b",
    r"\bnone\b",
    r"\bpersonal\b",
]
_TK_CLASSICAL_PATTERNS = [
    r"\bclassical\b",
    r"\bclassical (text|reference|formula|formulation|book|source)\b",
    r"\bcharaka\b",
    r"\bsushruta\b",
    r"\bashtanga\b",
    r"\bsharangadhara\b",
    r"\bbhaishajya\b",
    r"\bshastra\b",
    r"\bsamhita\b",
    r"\bgranth\b",
    r"\bved(a|ic)?\b",
    r"\bfirst schedule\b",
    r"\bayurvedic text\b",
    r"\bayurveda text\b",
    r"\btext\b",
    r"\bancient text\b",
]
_TK_TRADITIONAL_PATTERNS = [
    r"\btraditional\b",
    r"\btraditional use\b",
    r"\btraditional knowledge\b",
    r"\bcommunity knowledge\b",
    r"\bpassed down\b",
    r"\blocal community\b",
    r"\bfolk(lore)?\b",
    r"\btribal\b",
    r"\bindigenous\b",
    r"\bancestral\b",
    r"\bgrandma\b",
    r"\bfamily recipe\b",
    r"\btk\b",
]

_EXPANDED_JURISDICTIONS = {
    "india": "INDIA", "indian": "INDIA",
    "usa": "USA", "us": "USA", "united states": "USA", "america": "USA",
    "uk": "UK", "united kingdom": "UK", "britain": "UK", "england": "UK",
    "germany": "GERMANY", "german": "GERMANY",
    "europe": "EUROPE", "eu": "EU", "european": "EU",
    "japan": "JAPAN", "japanese": "JAPAN",
    "australia": "AUSTRALIA", "australian": "AUSTRALIA",
    "canada": "CANADA", "canadian": "CANADA",
    "singapore": "SINGAPORE",
    "uae": "UAE", "dubai": "UAE",
    "china": "CHINA", "chinese": "CHINA",
    "brazil": "BRAZIL",
    "france": "FRANCE",
    "switzerland": "SWITZERLAND",
    "new zealand": "NEW ZEALAND",
    "global": "GLOBAL", "worldwide": "GLOBAL", "international": "GLOBAL", "world": "GLOBAL",
}

_NEW_CASE_TRIGGER_PATTERNS = [
    r"\banother (invention|formulation|product|idea)\b",
    r"\ba different (invention|formulation|product|idea)\b",
    r"\bi have (another|a second|a new) (invention|formulation|product|idea)\b",
    r"\bstart a new case\b",
    r"\bcreate a new case\b",
    r"\bseparate case\b",
]

_AFFIRMATIVE_PATTERNS = [
    r"^(yes|yeah|yep|yup|sure|ok|okay)\b",
    r"\bplease do\b", r"\bcreate (a |the )?new case\b", r"\bstart (a |the )?new case\b",
    r"\bgo ahead\b",
]

_IP_TYPE_TO_OBJECTIVE = {
    "PATENT": IPObjective.PATENT,
    "TRADEMARK": IPObjective.TRADEMARK,
    "COPYRIGHT": IPObjective.COPYRIGHT,
    "DESIGN": IPObjective.DESIGN,
    "GI": IPObjective.GI,
}


def _dedupe_preserve_order(items: List[str]) -> List[str]:
    seen = set()
    result = []
    for item in items:
        key = item.strip().lower()
        if key and key not in seen:
            seen.add(key)
            result.append(item.strip())
    return result


class InnovationIntakeAgent:
    """Deterministic progressive intake engine for Phase 2."""

    @classmethod
    def looks_like_new_case_request(cls, message: str) -> bool:
        lower = (message or "").lower()
        return any(re.search(p, lower) for p in _NEW_CASE_TRIGGER_PATTERNS)

    @classmethod
    def is_affirmative(cls, message: str) -> bool:
        lower = (message or "").strip().lower()
        return any(re.search(p, lower) for p in _AFFIRMATIVE_PATTERNS)

    # Ordered, context-dependent question plan — the "minimum information" checklist
    # from CRAG.md-style Phase 2 spec §10 (items 1-6, plus 7 for patent cases and 8-9
    # for formulation cases). Each entry: (field_name, section, question_text).
    # Fields outside this plan (e.g. development_stage, product_name) are still
    # captured opportunistically when volunteered, but never block a next_question
    # or prevent READY — they aren't part of the minimum-information checklist.
    @classmethod
    def _question_plan(cls, profile: InnovationProfile) -> List[Tuple[str, str, str]]:
        is_patent_case = (
            profile.primary_ip_objective == IPObjective.PATENT
            or IPObjective.PATENT in profile.ip_objectives
        )
        is_formulation_case = (
            (profile.product_type or "").upper() in _FORMULATION_LIKE_TYPES
            or bool(profile.ingredients)
        )

        plan = [
            (
                "primary_ip_objective", "OBJECTIVE",
                "What would you like help with — patent protection, trademark registration, "
                "or something else?",
            ),
            (
                "short_description", "INNOVATION",
                "Tell me briefly what your innovation does and what problem it is intended to solve.",
            ),
        ]

        if is_patent_case:
            plan.append((
                "claimed_novelty", "INNOVATION",
                "What do you believe is novel about it — for example, its ingredients, ratio, "
                "extraction process, dosage form, or manufacturing method?",
            ))

        if is_formulation_case:
            plan.append((
                "tk_basis", "TRADITIONAL_KNOWLEDGE",
                "Is this based on an existing classical Ayurvedic text or traditional knowledge, "
                "or is it your own formulation?",
            ))
            plan.append((
                "ingredients", "FORMULATION",
                "What are the main ingredients in your formulation?",
            ))

        plan.append((
            "target_jurisdictions", "JURISDICTIONS",
            "Which countries or markets are you considering protecting or commercializing this in?",
        ))

        return plan

    @classmethod
    def _is_field_empty(cls, profile: InnovationProfile, field: str) -> bool:
        value = getattr(profile, field)
        # NOTE: TKBasis/DevelopmentStage are `str, Enum` subclasses, so `isinstance(value, str)`
        # below would also match them — these field-specific checks MUST run first.
        if field == "tk_basis":
            return value == TKBasis.UNKNOWN
        if field == "development_stage":
            return value == DevelopmentStage.UNKNOWN
        if field == "primary_ip_objective":
            return value is None
        if value is None:
            return True
        if isinstance(value, list):
            return len(value) == 0
        if isinstance(value, str):
            return len(value.strip()) == 0
        return False

    @classmethod
    def _mark(cls, profile: InnovationProfile, field: str, provenance: FieldProvenance = FieldProvenance.USER_STATED):
        profile.field_provenance[field] = provenance

    @classmethod
    def _apply_entities(cls, profile: InnovationProfile, entities: Entities) -> None:
        """Merges Phase-1-style extracted entities (this turn's message) into the profile."""
        if entities.ingredient_names:
            merged = _dedupe_preserve_order(profile.ingredients + entities.ingredient_names)
            if merged != profile.ingredients:
                profile.ingredients = merged
                cls._mark(profile, "ingredients")

        if entities.jurisdictions:
            merged = _dedupe_preserve_order(profile.target_jurisdictions + entities.jurisdictions)
            if merged != profile.target_jurisdictions:
                profile.target_jurisdictions = merged
                cls._mark(profile, "target_jurisdictions")
        elif entities.jurisdiction and entities.jurisdiction not in profile.target_jurisdictions:
            profile.target_jurisdictions = _dedupe_preserve_order(
                profile.target_jurisdictions + [entities.jurisdiction]
            )
            cls._mark(profile, "target_jurisdictions")

        if entities.ip_type:
            objective = _IP_TYPE_TO_OBJECTIVE.get(entities.ip_type)
            if objective:
                cls._add_ip_objective(profile, objective)

        if entities.product_type and not profile.product_type:
            profile.product_type = entities.product_type
            cls._mark(profile, "product_type")

    @classmethod
    def _add_ip_objective(cls, profile: InnovationProfile, objective: IPObjective) -> None:
        if objective in profile.ip_objectives:
            return
        profile.ip_objectives.append(objective)
        if profile.primary_ip_objective is None:
            profile.primary_ip_objective = objective
        elif objective not in profile.secondary_ip_objectives and objective != profile.primary_ip_objective:
            profile.secondary_ip_objectives.append(objective)
        cls._mark(profile, "primary_ip_objective")

    @classmethod
    def _extract_product_type_keyword(cls, text: str) -> Optional[str]:
        lower = text.lower()
        for kw in _PRODUCT_TYPE_KEYWORDS:
            if re.search(rf"\b{kw}\b", lower):
                return kw.upper()
        return None

    @classmethod
    def _extract_development_stage(cls, text: str) -> Optional[DevelopmentStage]:
        lower = text.lower()
        for kw, stage in _DEVELOPMENT_STAGE_KEYWORDS.items():
            if kw in lower:
                return stage
        return None

    @classmethod
    def _extract_ip_objective(cls, text: str) -> Optional[IPObjective]:
        lower = text.lower().strip()
        if not lower:
            return None
        if any(re.search(p, lower) for p in [
            r"\bpatents?\b", r"\bpatenting\b", r"\binvention\b", r"\bprotect\b",
            r"\bprotection\b", r"\bip\b", r"\bsafeguard\b", r"\bmonopoly\b", r"\bfile\b", r"\bfiling\b"
        ]):
            return IPObjective.PATENT
        if any(re.search(p, lower) for p in [
            r"\btrademarks?\b", r"\btm\b", r"\bbrand\b", r"\bbrand name\b", r"\blogo\b", r"\btrade mark\b"
        ]):
            return IPObjective.TRADEMARK
        if any(re.search(p, lower) for p in [
            r"\bcopyrights?\b", r"\bliterary\b", r"\bcode\b", r"\bbook\b"
        ]):
            return IPObjective.COPYRIGHT
        if any(re.search(p, lower) for p in [
            r"\bdesigns?\b", r"\baesthetic\b", r"\bshape\b", r"\bpackaging design\b"
        ]):
            return IPObjective.DESIGN
        if any(re.search(p, lower) for p in [
            r"\bgi\b", r"\bgeographical indication\b"
        ]):
            return IPObjective.GI
        return None

    @classmethod
    def _extract_ingredients_from_text(cls, text: str) -> List[str]:
        clean = re.sub(
            r"^(the\s+)?(main\s+)?ingredients?\s+(are|is|include|include:)?", "", text, flags=re.IGNORECASE
        ).strip()
        clean = re.sub(r"^(it\s+)?(contains|is\s+made\s+of|uses|combines)\s+", "", clean, flags=re.IGNORECASE).strip()
        clean = re.sub(r"^(we\s+use|i\s+use|formulated\s+with)\s+", "", clean, flags=re.IGNORECASE).strip()

        parts = re.split(r"[,;\n\r•\+\&]+|\band\b", clean, flags=re.IGNORECASE)
        ingredients = []
        for p in parts:
            item = p.strip(" .!?:;-")
            item = re.sub(r"^(a\s+|an\s+|the\s+|some\s+)", "", item, flags=re.IGNORECASE).strip()
            if len(item) >= 2 and item.lower() not in [
                "and", "with", "etc", "none", "nothing", "also", "in", "specific", "ratio", "formulation"
            ]:
                ingredients.append(item.title())
        return _dedupe_preserve_order(ingredients)

    @classmethod
    def _extract_jurisdictions_from_text(cls, text: str) -> List[str]:
        lower = text.lower()
        found = []
        for k, v in _EXPANDED_JURISDICTIONS.items():
            if re.search(rf"\b{k}\b", lower):
                if v not in found:
                    found.append(v)
        return found

    @classmethod
    def _extract_tk_basis(cls, text: str) -> Optional[TKBasis]:
        lower = text.lower().strip()
        if not lower:
            return None
        if any(re.search(p, lower) for p in _TK_NONE_PATTERNS):
            return TKBasis.NONE
        if any(re.search(p, lower) for p in _TK_CLASSICAL_PATTERNS):
            return TKBasis.CLASSICAL_TEXT
        if any(re.search(p, lower) for p in _TK_TRADITIONAL_PATTERNS):
            return TKBasis.TRADITIONAL_USE
        return None

    @classmethod
    def apply_message(
        cls,
        profile: InnovationProfile,
        intake_state: IntakeState,
        message: str,
        phase1_entities: Optional[Entities] = None,
    ) -> None:
        """
        Applies one user message to the profile in place:
        1. Global, low-false-positive heuristic scan (ingredients / jurisdictions / IP objective /
           product type) — safe to run on every message since these are specific proper nouns.
        2. Attribution of the raw answer to whichever field the previous question targeted
           (narrative fields), scoped so we never invent structured facts.
        Existing fields are preserved; list fields are merged, not overwritten.
        """
        message = (message or "").strip()
        if not message:
            return

        # 1. Reuse Phase 1's deterministic entity extractor for this specific message.
        entities = IntentRuleEngine.extract_entities(message)
        cls._apply_entities(profile, entities)
        if phase1_entities is not None:
            cls._apply_entities(profile, phase1_entities)

        product_kw = cls._extract_product_type_keyword(message)
        if product_kw and not profile.product_type:
            profile.product_type = product_kw
            cls._mark(profile, "product_type")

        # Opportunistic extraction across turns
        if profile.primary_ip_objective is None:
            obj = cls._extract_ip_objective(message)
            if obj is not None:
                cls._add_ip_objective(profile, obj)

        if profile.tk_basis == TKBasis.UNKNOWN:
            tk = cls._extract_tk_basis(message)
            if tk is not None:
                profile.tk_basis = tk
                cls._mark(profile, "tk_basis")

        # 2. Attribute the raw answer to the field we asked about (if any).
        pending_field = intake_state.pending_field
        if pending_field == "primary_ip_objective":
            if profile.primary_ip_objective is None:
                obj = cls._extract_ip_objective(message)
                if obj is not None:
                    cls._add_ip_objective(profile, obj)
                elif any(w in message.lower() for w in ["both", "all", "everything"]):
                    cls._add_ip_objective(profile, IPObjective.PATENT)
                    cls._add_ip_objective(profile, IPObjective.TRADEMARK)
                elif not any(w in message.lower() for w in ["not sure", "don't know", "what do you mean"]):
                    cls._add_ip_objective(profile, IPObjective.PATENT)
        elif pending_field == "short_description" and not profile.short_description:
            profile.short_description = message
            cls._mark(profile, "short_description")
            if not profile.problem_statement:
                profile.problem_statement = message
                cls._mark(profile, "problem_statement")
        elif pending_field == "claimed_novelty" and not profile.claimed_novelty:
            profile.claimed_novelty = message
            cls._mark(profile, "claimed_novelty")
        elif pending_field == "tk_basis":
            tk = cls._extract_tk_basis(message)
            if tk is None:
                lower_msg = message.lower().strip()
                if any(w in lower_msg for w in ["my", "i", "we", "lab", "new", "made", "secret", "recipe", "balm"]):
                    tk = TKBasis.NONE
                elif any(w in lower_msg for w in ["yes", "samhita", "old", "book", "classical"]):
                    tk = TKBasis.CLASSICAL_TEXT
                elif not any(k in lower_msg for k in ["not sure", "don't know", "what do you mean"]):
                    tk = TKBasis.NONE
            if tk is not None:
                profile.tk_basis = tk
                cls._mark(profile, "tk_basis")
            if not profile.traditional_use_description:
                profile.traditional_use_description = message
                cls._mark(profile, "traditional_use_description")
        elif pending_field == "ingredients":
            extracted = cls._extract_ingredients_from_text(message)
            if extracted:
                profile.ingredients = _dedupe_preserve_order(profile.ingredients + extracted)
                cls._mark(profile, "ingredients")
            elif not profile.ingredients and message.strip() and not any(k in message.lower() for k in ["not sure", "don't know"]):
                profile.ingredients = [message.strip().title()]
                cls._mark(profile, "ingredients")
        elif pending_field == "target_jurisdictions":
            found = cls._extract_jurisdictions_from_text(message)
            if found:
                profile.target_jurisdictions = _dedupe_preserve_order(profile.target_jurisdictions + found)
                cls._mark(profile, "target_jurisdictions")
            elif not profile.target_jurisdictions and message.strip() and not any(k in message.lower() for k in ["not sure", "don't know"]):
                clean_j = [p.strip().upper() for p in re.split(r"[,;\n]+|\band\b", message) if len(p.strip()) >= 2]
                profile.target_jurisdictions = clean_j or [message.strip().upper()]
                cls._mark(profile, "target_jurisdictions")
        elif pending_field == "development_stage" and profile.development_stage == DevelopmentStage.UNKNOWN:
            stage = cls._extract_development_stage(message)
            if stage is not None:
                profile.development_stage = stage
                cls._mark(profile, "development_stage")

        # Opportunistic detection that doesn't depend on which question was pending.
        if profile.development_stage == DevelopmentStage.UNKNOWN:
            stage = cls._extract_development_stage(message)
            if stage is not None:
                profile.development_stage = stage
                cls._mark(profile, "development_stage")

    @classmethod
    def next_question(
        cls, profile: InnovationProfile
    ) -> Tuple[Optional[str], Optional[str], List[str]]:
        """
        Returns (next_field, next_question_text, missing_information).
        missing_information lists every currently-empty applicable field, in plan order.
        """
        plan = cls._question_plan(profile)
        missing = [field for field, _section, _q in plan if cls._is_field_empty(profile, field)]
        for field, _section, question in plan:
            if cls._is_field_empty(profile, field):
                return field, question, missing
        return None, None, missing

    @classmethod
    def evaluate(
        cls, profile: InnovationProfile, intake_state: IntakeState
    ) -> IntakeState:
        """Recomputes IntakeState (status/missing_information/next_question) from the profile."""
        next_field, next_q, missing = cls.next_question(profile)
        intake_state.missing_information = missing
        intake_state.next_question = next_q
        intake_state.pending_field = next_field
        if next_field is None:
            intake_state.status = IntakeStatus.READY
            intake_state.current_section = None
        else:
            intake_state.status = IntakeStatus.IN_PROGRESS
            plan = cls._question_plan(profile)
            section_by_field = {f: s for f, s, _q in plan}
            intake_state.current_section = section_by_field.get(next_field)
            completed = [
                s for f, s, _q in plan
                if not cls._is_field_empty(profile, f) and s not in intake_state.completed_sections
            ]
            for s in completed:
                if s not in intake_state.completed_sections:
                    intake_state.completed_sections.append(s)
        return intake_state
