from src.processors.classifier import InfrastructureClassifier


def test_classifies_power_keyword():
	classifier = InfrastructureClassifier()
	assert "power" in classifier.classify("Stromnetz", "", [])


def test_classification_is_explainable():
	categories, matches = InfrastructureClassifier().classify_with_matches(
		"Windanlage", "", []
	)
	assert categories == ["renewable"]
	assert "wind" in matches


def test_unknown_dataset_is_uncategorized():
	assert InfrastructureClassifier().classify("Books", "Literature", []) == ["uncategorized"]


def test_multiple_categories_are_deterministic():
	classifier = InfrastructureClassifier()
	assert classifier.classify("Solarstrom", "Breitband", []) == ["power", "renewable", "telecom"]
