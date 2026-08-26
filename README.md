# German Infrastructure Crawler

A configurable Python crawler that discovers and catalogs public German infrastructure datasets. It supports power, renewable energy, land and municipality information, telecom, and public facilities.

The crawler starts with seed portals from `config/sources.yaml`, detects supported catalogue types, searches for relevant datasets, extracts metadata, classifies results, validates URLs, removes duplicates, and writes JSON and CSV output files.

## Setup

Open PowerShell in the project root and install the dependencies:

```powershell
pip install -r requirements\base.txt
```

For development and testing dependencies, use:

```powershell
pip install -r requirements\dev.txt
```

## Run The Complete Crawl

Run the full configured crawl with:

```powershell
python scripts\run.py
```

This uses all active seed sources and configured search queries. In the current environment, a complete run took approximately **36 minutes**. The duration can vary because the crawler respects rate limits, retries temporary failures, and validates many dataset and resource URLs.

Results are written to the `output` directory as timestamped JSON and CSV files.

## Bounded Live Run

For a bounded live run that searches several categories and validates source and
resource URLs, use:

```powershell
python scripts\run.py --max-sources 8 --max-datasets 20 --query energy infrastructure telecom renewable power
```

This run is intentionally larger than the quick example and normally takes at
least a couple of minutes because it uses multiple sources, applies the
configured rate limit, and performs live validation. Runtime depends on source
availability and network response times.

For a quick local run without live URL validation, add `--offline` and reduce
the scope:

```powershell
python scripts\run.py --max-sources 2 --max-datasets 5 --query energy --offline
```

## Validate Results

After an online crawl, the generated files are written to `output`. The JSON
file is the authoritative structured result. The regular CSV contains all
records, including records whose validation failed.

Run the post-crawl evidence checker against the generated JSON:

```powershell
python scripts\validate_output.py output\infrastructure_data_YYYYMMDD_HHMMSS.json `
	--report output\validation_report.json `
	--validated-csv output\validated_sources_YYYYMMDD_HHMMSS.csv
```

Replace `YYYYMMDD_HHMMSS` with the timestamp in the generated filename. The
checker does not make network requests. It verifies record counts, duplicate
source URLs, validation evidence, categories, metadata quality, and whether at
least 20 unique records have accessible status plus HTTP status and validation
timestamp evidence.

Exit codes are suitable for scripts and CI:

- `0`: at least 20 validated unique records
- `1`: fewer than 20 validated unique records
- `2`: invalid input or command usage error

The validation command creates:

- `output\validation_report.json`: machine-readable counts and evidence issues
- `output\validated_sources_*.csv`: only unique records with complete accessible
	validation evidence

The validated CSV preserves titles, descriptions, categories, source URLs, API
URLs, resources, licences, access status, and validation metadata. To inspect a
CSV directly, the validator also accepts the regular crawl CSV:

```powershell
python scripts\validate_output.py output\infrastructure_data_YYYYMMDD_HHMMSS.csv
```

## Discover Sources Separately

To detect and validate the configured seed catalogues without crawling datasets:

```powershell
python scripts\discover_sources.py
```

This writes source information to `output\discovered_sources.json` and does not modify the configured seed list.

## Run Tests

The automated tests use mocked or local inputs and do not require live websites:

```powershell
pytest -q
```

## Documentation

- [Architecture and data flow](docs/ARCHITECTURE.md)
- [Limitations and known constraints](docs/LIMITATIONS.md)
- [Future platform upgrades](docs/FUTURE_PLATFORM.md)

## Responsible Crawling

The crawler uses public information only. It applies configured rate limits, retries transient failures, checks `robots.txt` for HTML crawling, and does not bypass authentication, CAPTCHAs, or access restrictions. It catalogs metadata and does not download large underlying datasets.
