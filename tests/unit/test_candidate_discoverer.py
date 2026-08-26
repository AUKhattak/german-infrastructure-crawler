from src.discovery.candidate_discoverer import CandidateDiscoverer


class Response:
	status_code = 200
	text = '''
		<a href="https://catalogue.example.test/dataset/1">Open dataset catalogue</a>
		<a href="https://catalogue.example.test/api">Duplicate API</a>
		<a href="https://other.example.test/catalog">Other catalogue</a>
	'''


class AllowAllRobots:
	def allowed(self, url):
		return True


def test_discover_finds_additional_catalogue_and_deduplicates_origins():
	seed = {"id": "seed", "base_url": "https://seed.example.test"}
	discoverer = CandidateDiscoverer(
		http=type("Http", (), {"get": lambda self, url: Response()})(),
		robots=AllowAllRobots(),
	)

	candidates = discoverer.discover([seed], max_sources=3)

	assert len(candidates) == 2
	assert {candidate["base_url"] for candidate in candidates} == {
		"https://catalogue.example.test", "https://other.example.test"
	}
	assert all(candidate["discovered_from"] == "seed" for candidate in candidates)


def test_discover_respects_allowed_domains_and_source_limit():
	seed = {"id": "seed", "base_url": "https://seed.example.test"}
	discoverer = CandidateDiscoverer(
		http=type("Http", (), {"get": lambda self, url: Response()})(),
		robots=AllowAllRobots(),
	)

	assert discoverer.discover(
		[seed], max_sources=2, allowed_domains=["other.example.test"]
	) == [{
		"id": "other_example_test", "name": "other.example.test",
		"base_url": "https://other.example.test", "type": "auto", "active": True,
		"discovered_from": "seed", "discovery_depth": 1,
	}]