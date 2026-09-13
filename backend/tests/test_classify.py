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

def test_ayurveda_aahar_classification():
    data = {
        "is_in_first_schedule": True,
        "uses_modified_ratio_or_novel_combo": False,
        "is_standardized_extract": False,
        "intended_for_food": True,
        "intended_for_cosmetic": False
    }
    result = AyurvedicFormulationClassifier.classify(data)
    assert result["category_code"] == "AYURVEDA_AAHAR"
    assert "Ayurveda Aahar" in result["regulatory_framework"]
    assert "71 authoritative" in result["description"]
    assert "Excludes Ayurvedic drugs" in result["description"]

def test_cosmetic_classification():
    data = {
        "is_in_first_schedule": False,
        "uses_modified_ratio_or_novel_combo": False,
        "is_standardized_extract": False,
        "intended_for_food": False,
        "intended_for_cosmetic": True
    }
    result = AyurvedicFormulationClassifier.classify(data)
    assert result["category_code"] == "COSMETIC"
    assert "Cosmetics Rules 2020" in result["regulatory_framework"]

def test_agent_71_texts_classical_classifier():
    from ml_pipeline.agents.classifier_agent import FormulationClassifierAgent
    # Test text from Laghu Trayi (Sharngadhara Samhita)
    res1 = FormulationClassifierAgent.classify("Classical Kwatha formulation from Sharngadhara Samhita")
    assert res1.category == "classical_generic"
    assert "Section 3(p)" in res1.ip_bar_flag

    # Test text from 71 authoritative compendium (Bhaishajya Ratnavali)
    res2 = FormulationClassifierAgent.classify("Prepared from Bhaishajya Ratnavali without modification")
    assert res2.category == "classical_generic"

    # Test Ayurveda Aahar exclusion
    res3 = FormulationClassifierAgent.classify("Nutraceutical herbal dietary supplement for digestion")
    assert res3.category == "ayurveda_aahar"
    assert "Excludes Ayurvedic drugs" in res3.ip_bar_flag
