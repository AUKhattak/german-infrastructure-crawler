from unittest.mock import MagicMock

from src.utils.http_client import HttpClient


def test_default_timeout_is_used():
	client = HttpClient(timeout=17)
	response = MagicMock()
	response.elapsed.total_seconds.return_value = 0
	client.session.get = MagicMock(return_value=response)

	client.get('https://example.test')

	assert client.session.get.call_args.kwargs['timeout'] == 17


def test_custom_timeout_override_is_used_once():
	client = HttpClient(timeout=17)
	response = MagicMock()
	response.elapsed.total_seconds.return_value = 0
	client.session.get = MagicMock(return_value=response)

	client.get('https://example.test', timeout=4)

	assert client.session.get.call_args.kwargs['timeout'] == 4
	assert list(client.session.get.call_args.kwargs).count('timeout') == 1