from src.sources.html_source import HTMLSource


def test_html_source_has_html_capabilities():
	capabilities = HTMLSource({"name": "HTML", "base_url": "https://example.test", "type": "html"}).get_capabilities()
	assert capabilities["query_format"] == "url_params"
	assert capabilities["supports_pagination"] is False


def test_html_source_extracts_absolute_url():
	source = HTMLSource({"name": "HTML", "base_url": "https://example.test", "type": "html"})
	from bs4 import BeautifulSoup
	element = BeautifulSoup('<a href="/dataset/1"><h2>Dataset</h2></a>', "html.parser").a
	assert source._extract_from_element(element).url == "https://example.test/dataset/1"
