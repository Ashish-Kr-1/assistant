from typing import Union
from fastapi import APIRouter, HTTPException
from app.schemas.classification_schema import ClassificationRequest, ClassificationResponse
from app.services.classification_service import AyurvedicFormulationClassifier
from ml_pipeline.schemas.intent_schema import IntentResult
from ml_pipeline.classifier.intent_classifier import IntentClassifier

router = APIRouter()


@router.post("/classify", response_model=Union[IntentResult, ClassificationResponse])
async def classify_endpoint(request: ClassificationRequest):
    """
    Unified Classification Endpoint (Phase 1 + Formulation Wizard).
    - If `message` is provided: executes Phase 1 Intent & Entity Classifier.
    - If `is_in_first_schedule` is provided: executes 5-tier Ayurvedic Formulation Classifier.
    """
    if request.message is not None:
        message_text = request.message.strip()
        if not message_text:
            return IntentClassifier._build_unknown_fallback(
                "Please enter a non-empty message to classify."
            )
        return IntentClassifier.classify(message_text)

    if request.is_in_first_schedule is not None:
        result = AyurvedicFormulationClassifier.classify(request.model_dump())
        return ClassificationResponse(**result)

    raise HTTPException(
        status_code=400,
        detail=(
            "Please provide either 'message' (for Phase 1 Intent + Entity classification) "
            "or 'is_in_first_schedule' (for Ayurvedic formulation classification wizard)."
        )
    )
