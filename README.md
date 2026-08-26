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

## Faster Run

For a quick local run with a small scope and no URL validation:

```powershell
python scripts\run.py --max-sources 2 --max-datasets 5 --query energy --offline
```

The `--offline` option makes this run faster, but it skips live URL validation. For a small live run that still validates URLs, omit `--offline`:

```powershell
python scripts\run.py --max-sources 2 --max-datasets 5 --query energy
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
