from app.services.abs_service import ABSComplianceService

def test_ayush_practitioner_abs_exemption():
    result = ABSComplianceService.calculate_abs_duty(
        entity_type="ayush_practitioner",
        annual_turnover_inr=1000000,
        is_cultivated_species=False,
        is_export=False
    )
    assert result["abs_required"] == False
    assert result["benefit_sharing_fee_percentage"] == 0.0

def test_foreign_entity_abs_requirement():
    result = ABSComplianceService.calculate_abs_duty(
        entity_type="foreign_entity",
        annual_turnover_inr=50000000,
        is_cultivated_species=False,
        is_export=True
    )
    assert result["abs_required"] == True
    assert "Form III" in result["nba_form_required"]
