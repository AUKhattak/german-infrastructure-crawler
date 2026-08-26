from src.processors.geocoder import GeographicExtractor


def test_spatial_field_has_priority():
	assert GeographicExtractor().extract({"spatial": "Bayern", "title": "Berlin"}) == "Bayern"


def test_location_tag_is_detected():
	assert GeographicExtractor().extract({"tags": [{"name": "Hamburg"}]}) == "Hamburg"


def test_missing_location_is_unknown():
	assert GeographicExtractor().extract({"title": "Energy", "notes": "Power"}) == "Unknown"
