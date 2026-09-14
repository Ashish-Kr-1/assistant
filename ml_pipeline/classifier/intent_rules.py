"""
Deterministic Quick Rules & Entity Extraction (Phase 1 — IP-SAKTI Sahayak PS045)
Provides cheap, O(1) and regex-based classification for obvious intents:
- Greetings / CHAT (bypasses CRAG completely)
- Clear IP Protection requests
- Patent Research / Prior Art requests
- Regulatory / AYUSH / FSSAI requests
- ABS / Biodiversity requests
- International / Export requests
- Traditional Knowledge / TKDL requests
- Specific Legal Q&A (e.g. "What is a patent?", "What is Section 3(e)?")
- Ambiguous inputs triggering clarification
- Unrelated Out-of-Scope queries
"""

import re
from typing import Optional, Tuple, List, Dict
from ml_pipeline.schemas.intent_schema import Intent, Route, Entities, IntentResult, resolve_route


class IntentRuleEngine:
    """High-speed deterministic classifier and heuristic entity extractor."""

    GREETINGS = {
        "hi", "hii", "hiii", "hello", "hey", "namaste", "namaskar",
        "pranam", "good morning", "good afternoon", "good evening",
        "greetings", "bye", "goodbye", "thanks", "thank you",
        "dhanyawad", "shukriya", "नमस्ते", "प्रणाम", "धन्यवाद", "शुक्रिया"
    }

    OUT_OF_SCOPE_KEYWORDS = [
        "cake", "bake", "recipe for cake", "weather", "forecast", "football",
        "cricket score", "movie", "song", "poem", "capital of", "who is the president",
        "python code", "binary search", "quantum gravity teleportation"
    ]

    BOTANICAL_NAMES = [
        "ashwagandha", "turmeric", "curcuma", "withania", "neem", "guggulu",
        "tulsi", "triphala", "amla", "brahmi", "shatavari", "sarpagandha"
    ]

    JURISDICTIONS_MAP = {
        "germany": "GERMANY",
        "europe": "EUROPE",
        "eu": "EU",
        "usa": "USA",
        "us": "USA",
        "united states": "USA",
        "uk": "UK",
        "japan": "JAPAN",
        "india": "INDIA",
        "australia": "AUSTRALIA",
        "canada": "CANADA"
    }

    @classmethod
    def evaluate(cls, text: str) -> Optional[IntentResult]:
        """
        Runs deterministic quick rules against the preprocessed query.
        Returns IntentResult if a clear rule matches, or None if LLM fallback is needed.
        """
        raw_text = text.strip()
        lower = raw_text.lower()
        cleaned = re.sub(r"[^\w\s]", "", lower).strip()

        if not cleaned:
            return IntentResult(
                intent=Intent.UNKNOWN,
                confidence=0.0,
                route=Route.CLARIFICATION,
                entities=Entities(),
                needs_clarification=True,
                clarification_question="Please enter a question or describe what you need assistance with.",
                method="RULE"
            )

        # 1. Greetings (CHAT) — STRICT MUST BYPASS CRAG
        if cleaned in cls.GREETINGS or lower in cls.GREETINGS:
            return IntentResult(
                intent=Intent.CHAT,
                confidence=0.99,
                route=Route.CHAT,
                entities=Entities(),
                requires_case=False,
                needs_clarification=False,
                method="RULE"
            )
        # Check if entire query is just a greeting phrase (e.g. "hey there", "hello assistant")
        if re.match(r"^(hi|hello|hey|namaste|namaskar|good (morning|afternoon|evening))\s*(there|assistant|bot)?$", cleaned):
            return IntentResult(
                intent=Intent.CHAT,
                confidence=0.99,
                route=Route.CHAT,
                entities=Entities(),
                requires_case=False,
                needs_clarification=False,
                method="RULE"
            )

        # 2. Out of Scope (General Knowledge, Cooking, Weather, etc.)
        for kw in cls.OUT_OF_SCOPE_KEYWORDS:
            if kw in lower:
                return IntentResult(
                    intent=Intent.OUT_OF_SCOPE,
                    confidence=0.95,
                    route=Route.OUT_OF_SCOPE,
                    entities=Entities(),
                    requires_case=False,
                    needs_clarification=False,
                    method="RULE"
                )

        # 3. Ambiguous short inputs requiring clarification
        ambiguous_patterns = [
            r"^i have a new product\.?$",
            r"^i have a product\.?$",
            r"^i need help with my formulation\.?$",
            r"^help with my product\.?$",
            r"^new product\.?$",
            r"^my formulation\.?$"
        ]
        for pattern in ambiguous_patterns:
            if re.match(pattern, lower):
                return IntentResult(
                    intent=Intent.UNKNOWN,
                    confidence=0.50,
                    route=Route.CLARIFICATION,
                    entities=cls._extract_entities(lower),
                    requires_case=False,
                    needs_clarification=True,
                    clarification_question="What would you like help with—IP protection, patent research, regulatory requirements, biodiversity/ABS, or something else?",
                    method="RULE"
                )

        # 4. Patent Research / Prior Art
        prior_art_patterns = [
            r"\b(find|search|look for|check)\s+(patents|prior art|similar patents)\b",
            r"\bprior art search\b",
            r"\bsearch prior art\b",
            r"\bpatent (search|searching)\b",
            r"\bpatents similar to\b",
            r"\bprior art search karna\b",
            r"\bpatents dhundo\b"
        ]
        if any(re.search(p, lower) for p in prior_art_patterns):
            entities = cls._extract_entities(lower)
            entities.ip_type = entities.ip_type or "PATENT"
            entities.requested_action = "PRIOR_ART_SEARCH"
            return IntentResult(
                intent=Intent.PATENT_RESEARCH,
                confidence=0.95,
                route=Route.INNOVATION_INTAKE,
                entities=entities,
                requires_case=True,
                needs_clarification=False,
                method="RULE"
            )

        # 5. IP Protection
        ip_protection_patterns = [
            r"\b(i want to|how (can|do) i|help me|wish to)\s+(patent|file a patent|protect|trademark|register)\b",
            r"\b(want|how) to (patent|trademark|protect|register)\b",
            r"\b(patent karwana|patent karna|trademark karwana|trademark lena)\b",
            r"\bapne .* (patent|trademark)\b",
            r"मुझे पेटेंट कराना है",
            r"पेटेंट कैसे कराएं",
            r"\bi want to patent\b",
            r"\bi want to trademark\b",
            r"\bi want to protect my (invention|formulation|brand|product)\b"
        ]
        if any(re.search(p, lower) for p in ip_protection_patterns):
            entities = cls._extract_entities(lower)
            if "trademark" in lower:
                entities.ip_type = "TRADEMARK"
                entities.requested_action = "TRADEMARK_PROTECTION"
            else:
                entities.ip_type = entities.ip_type or "PATENT"
                entities.requested_action = entities.requested_action or "PATENT_PROTECTION"
            return IntentResult(
                intent=Intent.IP_PROTECTION,
                confidence=0.95,
                route=Route.INNOVATION_INTAKE,
                entities=entities,
                requires_case=True,
                needs_clarification=False,
                method="RULE"
            )

        # 6. International Assessment / Export
        intl_patterns = [
            r"\b(can i )?(sell|export|commercialize|register) .* (in|to) (germany|europe|us|usa|japan|uk)\b",
            r"\b(patent|patenting) in (germany|europe|us|usa|japan|uk)\b",
            r"\bexport (my )?ayurvedic .* to (germany|europe|us|usa|japan|uk)\b",
            r"\b(wipo gratk|nagoya protocol|pct application|madrid system|madrid protocol)\b"
        ]
        if any(re.search(p, lower) for p in intl_patterns):
            entities = cls._extract_entities(lower)
            return IntentResult(
                intent=Intent.INTERNATIONAL_ASSESSMENT,
                confidence=0.92,
                route=Route.RESEARCH,
                entities=entities,
                requires_case=False,
                needs_clarification=False,
                method="RULE"
            )

        # 7. ABS / Biodiversity Assessment
        abs_patterns = [
            r"\b(what is abs\??)\b",
            r"\b(what are )?biodiversity regulations\b",
            r"\baccess and benefit sharing\b",
            r"\bbiological diversity act\b",
            r"\b(national biodiversity authority|\bnba\b approval|\bnba\b form)\b",
            r"\b(state biodiversity board|\bsbb\b)\b",
            r"\bbiological resources? compliance\b",
            r"\bbenefit sharing slab\b"
        ]
        if any(re.search(p, lower) for p in abs_patterns):
            entities = cls._extract_entities(lower)
            entities.domain = entities.domain or "BIODIVERSITY"
            entities.act = entities.act or "Biological Diversity Act, 2002"
            return IntentResult(
                intent=Intent.ABS_ASSESSMENT,
                confidence=0.92,
                route=Route.RESEARCH,
                entities=entities,
                requires_case=False,
                needs_clarification=False,
                method="RULE"
            )

        # 8. Traditional Knowledge Assessment
        tk_patterns = [
            r"\bwhat is traditional knowledge\??\b",
            r"\btraditional knowledge digital library\b",
            r"\btkdl\b",
            r"\btraditional knowledge misappropriation\b",
            r"\bbiopiracy\b",
            r"\bfirst schedule authoritative texts\b"
        ]
        # Make sure it's not asking specifically about Section 3(p) as a statutory question
        if any(re.search(p, lower) for p in tk_patterns) and not re.search(r"section 3\(p\)", lower):
            entities = cls._extract_entities(lower)
            entities.domain = entities.domain or "TRADITIONAL_KNOWLEDGE"
            return IntentResult(
                intent=Intent.TK_ASSESSMENT,
                confidence=0.90,
                route=Route.RESEARCH,
                entities=entities,
                requires_case=False,
                needs_clarification=False,
                method="RULE"
            )

        # 9. Regulatory Assessment
        regulatory_patterns = [
            r"\b(what are )?ayush regulatory requirements\b",
            r"\bayush approval\b",
            r"\bayush license\b",
            r"\bdrug licen[cs]e\b",
            r"\bregulatory requirements\b",
            r"\bfssai compliance\b",
            r"\bfssai approval\b",
            r"\bcosmetic licen[cs]e\b",
            r"\brule 122e\b",
            r"\brule 158b\b",
            r"\bayurveda aahar regulations\b",
            r"\bgmp compliance\b",
            r"\bayush approval ke liye\b"
        ]
        if any(re.search(p, lower) for p in regulatory_patterns):
            entities = cls._extract_entities(lower)
            entities.domain = entities.domain or "REGULATORY"
            return IntentResult(
                intent=Intent.REGULATORY_ASSESSMENT,
                confidence=0.92,
                route=Route.RESEARCH,
                entities=entities,
                requires_case=False,
                needs_clarification=False,
                method="RULE"
            )

        # 10. Legal Q&A & Case Queries (Statutes, sections, case law databases)
        legal_qa_patterns = [
            r"^what is a patent\??$",
            r"^what is a trademark\??$",
            r"^what is copyright\??$",
            r"^what is section \d+.*",
            r"^explain section \d+.*",
            r"^what are the requirements of section \d+.*",
            r"^can i patent traditional knowledge .* under section 3\(p\)\??",
            r"^what are the mandatory disclosure requirements .* under wipo.*",
            r"\b(manupatra|indian kanoon|supreme court judgment|high court ruling|case law|precedents?)\b",
            r"^what does .* say (about|on)\b"
        ]
        if any(re.search(p, lower) for p in legal_qa_patterns):
            entities = cls._extract_entities(lower)
            intent = (
                Intent.LEGAL_CASE_QUERY
                if any(k in lower for k in ["manupatra", "indian kanoon", "court", "judgment", "case law"])
                else Intent.LEGAL_QA
            )
            return IntentResult(
                intent=intent,
                confidence=0.95,
                route=Route.CRAG,
                entities=entities,
                requires_case=False,
                needs_clarification=False,
                method="RULE"
            )

        # If no deterministic rule is confident enough, return None to trigger LLM fallback
        return None

    @classmethod
    def extract_entities(cls, text: str) -> Entities:
        """
        Public entry point for heuristic entity extraction, reused by downstream
        phases (e.g. Phase 2 Innovation Intake) that need routing-style entities
        from a raw message without re-running full intent classification.
        """
        return cls._extract_entities(text.lower())

    @classmethod
    def _extract_entities(cls, text: str) -> Entities:
        """Extracts routing-level entities using deterministic heuristics."""
        entities = Entities()
        lower = text.lower()

        # IP Type
        if "patent" in lower:
            entities.ip_type = "PATENT"
        elif "trademark" in lower:
            entities.ip_type = "TRADEMARK"
        elif "copyright" in lower:
            entities.ip_type = "COPYRIGHT"
        elif "design" in lower:
            entities.ip_type = "DESIGN"
        elif "geographical indication" in lower or r"\bgi\b" in lower:
            entities.ip_type = "GI"

        # Domain
        if any(k in lower for k in ["ayurveda", "ayurvedic", "churna", "herbal", "bhasma"]):
            entities.domain = "AYURVEDA"
        elif any(k in lower for k in ["biodiversity", "biological resource", "abs", "nba", "sbb"]):
            entities.domain = "BIODIVERSITY"
        elif any(k in lower for k in ["food", "supplement", "nutraceutical", "aahar"]):
            entities.domain = "FOOD"
        elif any(k in lower for k in ["cosmetic", "skin", "hair", "cream", "shampoo"]):
            entities.domain = "COSMETIC"

        # Product & Object type
        if any(k in lower for k in ["formulation", "recipe", "churna", "kwatha", "blend"]):
            entities.object_type = "FORMULATION"
            entities.product_type = "AYURVEDIC_FORMULATION" if entities.domain == "AYURVEDA" else "FORMULATION"
        elif any(k in lower for k in ["medicine", "drug"]):
            entities.object_type = "MEDICINE"
            entities.product_type = "MEDICINE"
        elif any(k in lower for k in ["invention", "process", "method", "device"]):
            entities.object_type = "INVENTION"
        elif "brand" in lower or "logo" in lower:
            entities.object_type = "BRAND"

        # Jurisdiction
        for j_key, j_val in cls.JURISDICTIONS_MAP.items():
            if re.search(rf"\b{j_key}\b", lower):
                entities.jurisdiction = j_val
                if j_val not in entities.jurisdictions:
                    entities.jurisdictions.append(j_val)

        # Act and Section detection
        sec_match = re.search(r"\bsection\s+(\d+[a-z]?(\([a-z0-9]+\))*)", lower)
        if sec_match:
            entities.section = sec_match.group(0).title()

        rule_match = re.search(r"\brule\s+(\d+[a-z]*)", lower)
        if rule_match:
            entities.section = rule_match.group(0).title()

        if "patents act" in lower:
            entities.act = "The Patents Act, 1970"
        elif "biological diversity act" in lower or "bda" in lower:
            entities.act = "Biological Diversity Act, 2002"
        elif "drugs and cosmetics" in lower:
            entities.act = "Drugs and Cosmetics Act, 1940"
        elif "fssai" in lower:
            entities.act = "Food Safety and Standards Act, 2006"

        # Ingredients
        for bot in cls.BOTANICAL_NAMES:
            if bot in lower:
                entities.ingredient_names.append(bot.capitalize())

        # Requested Action
        if any(k in lower for k in ["export", "sell in", "ship"]):
            entities.requested_action = "EXPORT"
        elif any(k in lower for k in ["prior art", "find patent", "search patent"]):
            entities.requested_action = "PRIOR_ART_SEARCH"
        elif "patent" in lower and any(k in lower for k in ["want", "how can", "file", "protect"]):
            entities.requested_action = "PATENT_PROTECTION"
        elif "trademark" in lower and any(k in lower for k in ["want", "how can", "register"]):
            entities.requested_action = "TRADEMARK_PROTECTION"
        elif any(k in lower for k in ["compliance", "approval", "license"]):
            entities.requested_action = "REGULATORY_COMPLIANCE"

        return entities
