from app.services.classification_service import AyurvedicFormulationClassifier

def test_classical_medicine_classification():
    data = {
        "is_in_first_schedule": True,
        "uses_modified_ratio_or_novel_combo": False,
        "is_standardized_extract": False,
        "intended_for_food": False,
        "intended_for_cosmetic": False
    }
    result = AyurvedicFormulationClassifier.classify(data)
    assert result["category_code"] == "CLASSICAL_MEDICINE"
    assert "Section 3(p)" in result["ip_posture"]

def test_phytopharmaceutical_classification():
    data = {
        "is_in_first_schedule": False,
        "uses_modified_ratio_or_novel_combo": True,
        "is_standardized_extract": True,
        "intended_for_food": False,
        "intended_for_cosmetic": False
    }
    result = AyurvedicFormulationClassifier.classify(data)
    assert result["category_code"] == "PHYTOPHARMACEUTICAL"
    assert "Rule 122E" in result["regulatory_framework"]
