from fastapi import APIRouter
from app.schemas.classification_schema import ClassificationRequest, ClassificationResponse
from app.services.classification_service import AyurvedicFormulationClassifier

router = APIRouter()

@router.post("/classify", response_model=ClassificationResponse)
async def classify_formulation(request: ClassificationRequest):
    """
    Formulation Classification Wizard Endpoint.
    Classifies Ayurvedic products into generic/classical, proprietary, phytopharmaceutical, food, or cosmetic,
    and states exact IP posture and ABS duties.
    """
    result = AyurvedicFormulationClassifier.classify(request.model_dump())
    return ClassificationResponse(**result)
