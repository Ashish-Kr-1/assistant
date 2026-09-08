from fastapi import APIRouter, Query
from app.services.abs_service import ABSComplianceService

router = APIRouter()

@router.get("/abs/calculate")
async def calculate_abs(
    entity_type: str = Query("indian_company", description="Entity type: 'indian_company', 'foreign_entity', 'ayush_practitioner'"),
    annual_turnover_inr: float = Query(5000000.0, description="Annual turnover in INR"),
    is_cultivated_species: bool = Query(True, description="Are biological resources cultivated species?"),
    is_export: bool = Query(False, description="Is product intended for export?")
):
    """
    ABS Helper Endpoint under India's Biological Diversity Act 2002 (2023 Amendment).
    """
    return ABSComplianceService.calculate_abs_duty(
        entity_type=entity_type,
        annual_turnover_inr=annual_turnover_inr,
        is_cultivated_species=is_cultivated_species,
        is_export=is_export
    )
