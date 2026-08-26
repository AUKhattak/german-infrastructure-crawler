from src.sources.html_source import HTMLSource


def test_html_source_has_html_capabilities():
	capabilities = HTMLSource({"name": "HTML", "base_url": "https://example.test", "type": "html"}).get_capabilities()
	assert capabilities["query_format"] == "url_params"
	assert capabilities["supports_pagination"] is False
	assert capabilities["supports_license"] is True
	assert capabilities["supports_formats"] is True


def test_html_source_extracts_absolute_url():
	source = HTMLSource({"name": "HTML", "base_url": "https://example.test", "type": "html"})
	from bs4 import BeautifulSoup
	element = BeautifulSoup('<a href="/dataset/1"><h2>Dataset</h2></a>', "html.parser").a
	assert source._extract_from_element(element).url == "https://example.test/dataset/1"


def test_html_source_classifies_dataset():
	source = HTMLSource({"name": "HTML", "base_url": "https://example.test", "type": "html"})
	from bs4 import BeautifulSoup
	element = BeautifulSoup(
		'<a href="/dataset/1"><h2>Breitband Ausbau</h2><p>Internet coverage</p></a>',
		"html.parser",
	).a
	dataset = source._extract_from_element(element)

	assert dataset.infrastructure_categories == ["telecom"]
	assert "breitband" in dataset.matched_keywords


def test_html_source_extracts_configured_license():
	source = HTMLSource({
		"name": "HTML", "base_url": "https://example.test", "type": "html",
		"parser": {"selectors": {"license": [".license"]}},
	})
	from bs4 import BeautifulSoup
	element = BeautifulSoup(
		'<a href="/dataset/1"><h2>Dataset</h2><span class="license">CC BY 4.0</span></a>',
		"html.parser",
	).a

	assert source._extract_from_element(element).license == "CC BY 4.0"


def test_html_source_normalizes_license_link():
	source = HTMLSource({
		"name": "HTML", "base_url": "https://example.test", "type": "html",
		"parser": {"selectors": {"license": [".license"]}},
	})
	from bs4 import BeautifulSoup
	element = BeautifulSoup(
		'<a href="/dataset/1"><h2>Dataset</h2>'
		'<a class="license" href="/licence">Licence</a></a>',
		"html.parser",
	).a

	assert source._extract_from_element(element).license == "https://example.test/licence"


def test_html_source_preserves_configured_resources():
	source = HTMLSource({
		"name": "HTML", "base_url": "https://example.test", "type": "html",
		"parser": {"selectors": {"resources": ["a.resource"]}},
	})
	from bs4 import BeautifulSoup
	element = BeautifulSoup(
		'<a href="/dataset/1"><h2>Dataset</h2>'
		'<a class="resource" data-format="CSV" href="/data.csv">Download</a></a>',
		"html.parser",
	).a

	dataset = source._extract_from_element(element)
	assert dataset.resources[0]["url"] == "https://example.test/data.csv"
	assert dataset.formats == ["CSV"]


def test_html_source_uses_configured_categories(tmp_path):
	config_path = tmp_path / "categories.yaml"
	config_path.write_text("custom: [unique-term]\n", encoding="utf-8")
	source = HTMLSource({
		"name": "HTML", "base_url": "https://example.test", "type": "html",
		"runtime_settings": {"categories": {"config_path": str(config_path)}},
	})
	from bs4 import BeautifulSoup
	element = BeautifulSoup('<a href="/dataset/1"><h2>Unique-Term</h2></a>', "html.parser").a

	assert source._extract_from_element(element).infrastructure_categories == ["custom"]
