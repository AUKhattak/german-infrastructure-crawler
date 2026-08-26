##  Overview

The German Infrastructure Crawler is a **modular, extensible, and configuration-driven** web scraping system designed to harvest datasets from multiple open data portals. Built with scalability in mind, it supports various source types (CKAN, HTML, and extensible to others) while maintaining a consistent data model and enrichment pipeline.

**Key Features:**
- 🏗️ Plugin-based architecture for easy source addition
- 📊 Source-specific data enrichment (geographic coverage, infrastructure categories)
- 🔄 Retry logic with exponential backoff
- 🚦 Rate limiting for polite crawling
- 📝 Configurable validation and quality checks
- 📁 Multiple output formats (JSON, CSV)
- 🏥 Health checking and source validation

---

##  High-Level Architecture

```
CONFIGURATION
  sources.yaml + settings.yaml + categories.yaml
                         │
                         ▼
DISCOVERY
  seed loader -> bounded candidate discovery -> catalogue detector
                         │
                         ▼
CORE ENGINE
  SourceRegistry -> SourceFactory -> BaseCrawler
                         │
                         ▼
CRAWLERS
  CKANSource | HTMLSource (robots.txt checked for HTML searches)
                         │
                         ▼
PROCESSING
  Dataset transformation -> classification/geographic extraction
  -> URL validation/evidence -> deduplication
                         │
                         ▼
OUTPUT
  timestamped JSON/CSV -> validate_output.py evidence report
```

---

##  Component Architecture

### 1. **Configuration Layer**

#### `config/sources.yaml`
- **Purpose**: Configurable seed portals and discovery settings
- **Contents**:
  - Active `seed_sources` portal definitions
  - Source types and API paths
  - Discovery limits and search queries
  - Legacy `sources` mapping for compatibility
#### `config/categories.yaml`
- **Purpose**: Keyword mappings used by the infrastructure classifier
- **Authority**: Single source of truth used by CKAN and HTML sources

#### `config/settings.yaml`
- **Purpose**: Stores system-wide behavior settings
- **Runtime status**: Loaded by `scripts/run.py` and passed to the registry and
  crawler components.
- **Contents**:
  - HTTP settings (timeout, retries, rate limit)
  - Crawler limits (max datasets/source, max queries/source)
  - Logging configuration
  - Validation requirements
  - Bounded discovery settings and category configuration path

### 2. **Core Engine Layer**

#### `BaseCrawler` (Abstract Base Class)
**File**: `src/core/base_crawler.py`

**Purpose**: Defines the contract for all crawler implementations

**Key Methods**:
```python
class BaseCrawler(ABC):
    @abstractmethod
    def search(self, context: CrawlerContext) -> List[Dataset]: ...
    
    @abstractmethod
    def validate(self) -> bool: ...
    
    @abstractmethod
    def get_capabilities(self) -> Dict: ...
    
    def batch_search(self, queries: List[str], limit: int) -> List[Dataset]: ...
```

**Design Pattern**: Template Method - defines skeleton, child classes fill details

---

#### `SourceFactory`
**File**: `src/core/source_factory.py`

**Purpose**: Creates crawler instances based on source type using Factory Pattern
**Registry**:
CONFIGURATION
  seed_sources, queries, categories, discovery limits
                         │
                         ▼
DISCOVERY
  seed loader -> catalogue detector (configured CKAN or auto CKAN/HTML)
                         │
                         ▼
CORE ENGINE
  SourceRegistry -> SourceFactory -> BaseCrawler
                         │
                         ▼
CRAWLERS
  CKANSource | HTMLSource (robots.txt checked for HTML searches)
                         │
                         ▼
PROCESSING
  Dataset transformation -> classification/geographic extraction
  -> URL validation -> deduplication
                         │
                         ▼
OUTPUT
  timestamped JSON and CSV written by scripts/run.py

---

### 3. **Discovery Layer**

#### `Seed Loader`
**File**: `src/discovery/seed_loader.py`

Loads active `seed_sources` from `config/sources.yaml` and falls back to the
legacy `sources` mapping when needed.

#### `Catalogue Detector`
**File**: `src/discovery/catalogue_detector.py`

Checks configured or common CKAN API paths and falls back to HTML detection.
Unsupported candidates are logged and skipped. Discovery is intentionally
bounded and does not perform unrestricted internet crawling.

#### `CandidateDiscoverer`
**File**: `src/discovery/candidate_discoverer.py`

Follows relevant links from seed pages within configured depth, page, domain,
and robots limits. Candidates are deduplicated by normalized origin and retain
their discovery provenance.

### 4. **Crawler Implementations**

#### `CKANSource`
**File**: `src/sources/ckan_source.py`

**Purpose**: Handles CKAN-compatible open data portals

**Key Features**:
- CKAN API integration (`/api/action/package_search`)
- Resource extraction (formats, URLs, sizes)
- Organization extraction
- Tag parsing
- Automatic enrichment (geographic, infrastructure)

**Supported Portals**:
- govdata.de
- Any CKAN-compliant portal (via configuration)

---

#### `HTMLSource`
**File**: `src/sources/html_source.py`

**Purpose**: Generic HTML website scraping

**Key Features**:
- Configurable selector-based extraction
- Fallback for non-API portals
- `robots.txt` check before search requests
- Shared infrastructure classification and optional licence/resource selectors

---

### 5. **Enrichment and Validation Layer**

#### `InfrastructureClassifier`
**File**: `src/processors/classifier.py`

**Purpose**: Categorizes datasets into infrastructure domains

**Categories**:
- `power`: Energy/electricity datasets
- `renewable`: Renewable energy (wind, solar, etc.)
- `land`: Land/parcel/geospatial data
- `telecom`: Telecommunications infrastructure
- `public_facility`: Schools, hospitals, police stations

**Method**: Keyword matching on title + description + tags

**Extensibility**: Keywords are loaded from `config/categories.yaml`, with
fallback keywords if the configuration cannot be loaded.

---

#### `GeographicExtractor`
**File**: `src/processors/geocoder.py`

**Purpose**: Identifies geographic coverage of datasets

**Extraction Priority**:
1. `spatial` field (most reliable)
2. Tags (known location tags)
3. Text scanning (title + notes)
4. Default: 'Unknown'

**Recognized Locations**:
- 16 German federal states
- Major German cities
- National level (Germany, Bundesweit)

---

#### URL Validation
**File**: `src/utils/validators.py`

Normalizes HTTP(S) URLs and validates them with a streamed GET request. The
result records a normalized URL, HTTP status, validation timestamp, and
distinguishes invalid, inaccessible, and error states without stopping the
crawl. Offline runs leave records as `unknown`/`not_checked`.

#### Post-run Evidence Validation
**File**: `scripts/validate_output.py`

Checks generated JSON or CSV without making network requests. It verifies
unique source counts, validation evidence, URL structure, category coverage,
metadata quality, contradictions, and the 20-validated-source threshold. It
can produce a validation report and validated-only CSV.

#### Robots Checking
**File**: `src/utils/robots.py`

Checks `robots.txt` before HTML search requests.

#### Deduplication
**File**: `src/processors/deduplicator.py`

Uses dataset IDs, canonical dataset URLs, resource URLs, and normalized title
plus organization fingerprints. When records match, the more complete record
is retained.

### 6. **Data Layer**

#### `Dataset` Model
**File**: `src/models/dataset.py`

**Purpose**: Standardized data model for all datasets

**Schema**:
```python
@dataclass
class Dataset:
    # Required fields
    id: str
    title: str
    description: str
    organization: str
    source: str
    source_type: str
    
    # Optional fields
    url: str = ''
    api_url: str = ''
    license: str = 'Unknown'
    geographic_coverage: str = 'Unknown'
    infrastructure_categories: List[str] = field(default_factory=list)
    access_status: str = 'unknown'
    source_url_status: str = 'not_checked'
    source_url_validation: Dict = field(default_factory=dict)
    resource_validation: List[Dict] = field(default_factory=list)
    validation_timestamp: str = ''
    matched_keywords: List[str] = field(default_factory=list)
    # ... more fields
```

  Serialized output uses descriptive names including `dataset_id`,
  `dataset_title`, `source_name`, `source_url`, `download_urls`, and
  `data_formats`.

**Methods**:
- `to_dict()`: Serialize for output
- `to_json()`: JSON string
- `from_dict()`: Deserialize from raw data

---

## 🔄 Data Flow

### Complete Crawling Pipeline

```
1. Load `sources.yaml` and `settings.yaml` configuration
  - The default path is resolved from the project root.
  - Active seed portals come from `seed_sources`; the legacy `sources` mapping
    remains supported.
  - Queries come from `--query`, `discovery.queries`, or `default_queries`.
  ↓
2. Discover bounded candidates and detect catalogue types
  - Follow relevant links within configured depth, page, domain, and robots
    limits.
  - Configured CKAN/HTML types are used directly.
  - `auto` seeds are checked against common CKAN API paths, then HTML.
  - Unsupported seeds are skipped and logged.
  ↓
3. Initialize `SourceRegistry`
  - Create a crawler for each detected seed through `SourceFactory`.
  ↓
4. Validate all initialized sources
  - Each source performs its own health check.
  - Invalid or failed sources are logged and excluded from crawling.
  ↓
5. Crawl each working source
  - Call `batch_search()` once for each configured query.
  - CKAN sources build API requests, use `HttpClient` for rate limiting and
    retries, transform responses into `Dataset` objects, and apply the
    classifier and geographic extractor.
  - HTML sources fetch the configured search page, parse dataset links, apply
    shared classification, and extract configured metadata after a
    `robots.txt` check.
  ↓
6. Validate dataset and resource URLs
  - Record source/resource URL status, HTTP status, normalized URLs, timestamps,
    and overall access status without aborting the crawl for individual
    failures.
  ↓
7. Collect all datasets from all working sources
  ↓
8. Deduplicate results
  - Use canonical ID, source URL, resource URL, and title/organization
    fingerprints.
  - Retain the more complete record when duplicates match.
  ↓
9. Write results when datasets were found
  - Create the selected output directory.
  - Write timestamped JSON and CSV files from the `Dataset` objects with
    descriptive serialized field names and structured resource evidence.
  ↓
10. Validate generated evidence with `scripts/validate_output.py`
  - Optionally write `validation_report.json` and a validated-only CSV.
```

---

## 📁 Project Structure

```
german-infrastructure-crawler/
├── config/
│   ├── categories.yaml            # Category configuration
│   ├── settings.yaml              # Global settings
│   └── sources.yaml               # Source configurations and queries
├── docs/
│   ├── ARCHITECTURE.md            # System architecture and data flow
│   ├── LIMITATIONS.md             # Known limitations
│   └── README.md                  # Documentation overview
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── base_crawler.py       # Abstract base class
│   │   ├── source_factory.py     # Factory pattern for crawlers
│   │   └── registry.py           # Source management
│   ├── sources/
│   │   ├── __init__.py
│   │   ├── ckan_source.py        # CKAN implementation
│   │   ├── custom_source.py       # Reserved custom source module
│   │   └── html_source.py         # HTML implementation
│   ├── models/
│   │   ├── __init__.py
│   │   ├── dataset.py            # Data model
│   │   └── source.py             # Reserved source model module
│   ├── discovery/
│   │   ├── __init__.py
│   │   ├── seed_loader.py         # Seed configuration loading
│   │   ├── catalogue_detector.py  # CKAN/HTML type detection
│   │   └── candidate_discoverer.py # Bounded candidate discovery
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── classifier.py         # Infrastructure classifier
│   │   ├── deduplicator.py       # Duplicate detection and selection
│   │   ├── formatter.py          # JSON/CSV formatting helpers
│   │   └── geocoder.py            # Geographic extractor
│   └── utils/
│       ├── __init__.py
│       ├── http_client.py        # HTTP client with retries
│       ├── logger.py              # Logging setup
│       ├── robots.py              # robots.txt checks
│       └── validators.py         # Reserved validation helpers
├── scripts/
│   ├── discover_sources.py       # Source discovery utility
│   ├── run.py                    # Main crawler entry point and output writing
│   ├── validate_output.py        # Post-run evidence validator
│   └── logs/                     # Runtime logs
├── output/                       # Generated JSON and CSV results
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
├── tests/
│   ├── conftest.py                # Test import configuration
│   ├── integration/
│   │   ├── test_ckan_source.py
│   │   └── test_html_source.py
│   └── unit/
│       ├── test_configuration.py
│       ├── test_deduplicator.py
│       ├── test_detector.py
│       ├── test_classifier.py
│       ├── test_geocoder.py
│       ├── test_models.py
│       └── test_validators.py
├── README.md
├── Makefile
└── pyproject.toml
```

---

##  Extensibility Guide

### Adding a New Source Type

**Step 1**: Create crawler class
```python
# src/sources/socrata_source.py
class SocrataSource(BaseCrawler):
    def __init__(self, config):
        super().__init__(config)
        # Socrata-specific initialization
    
    def search(self, context):
        # Socrata API implementation
    
    def validate(self):
        # Health check
        pass
    
    def get_capabilities(self):
        return {'supports_geolocation': True, ...}
```

**Step 2**: Register with factory
```python
# In src/core/source_factory.py
SourceFactory.register('socrata', SocrataSource)
```

**Step 3**: Add to configuration
```yaml
# config/sources.yaml
my_socrata_portal:
  name: My Socrata Portal
  base_url: https://data.mycity.com
  type: socrata
  active: true
```

---

### Adding New Categories

**Edit**: `config/sources.yaml`
```yaml
categories:
  healthcare:
    - krankenhaus
    - hospital
    - arzt
    - health
    - clinic
  # New category
  education:
    - schule
    - university
    - bildung
    - campus
```

---

### Adding New Enrichment Processor

**Step 1**: Create processor
```python
# src/processors/quality_scorer.py
class QualityScorer:
    def score(self, dataset):
        # Calculate quality score based on completeness
        score = 0
        if dataset.url: score += 20
        if dataset.license != 'Unknown': score += 20
        if dataset.resources: score += 30
        if dataset.geographic_coverage != 'Unknown': score += 30
        return score
```

**Step 2**: Integrate into pipeline
```python
# src/sources/ckan_source.py
class CKANSource(BaseCrawler):
    def __init__(self, config):
        # ...
        self.scorer = QualityScorer()
    
    def _transform(self, raw):
        dataset = Dataset(...)
        # Add quality score
        dataset.quality_score = self.scorer.score(dataset)
        return dataset
```

---

## ⚙️ Configuration Reference

### Settings (`settings.yaml`)
The file stores global settings for HTTP, crawling, bounded discovery,
validation, category configuration, output, and logging. The main runner loads
this file by default and passes the settings to the crawler components.
```yaml
http:
  timeout: 30                    # Request timeout (seconds)
  max_retries: 3                 # Retry attempts
  backoff_factor: 1              # Exponential backoff base
  rate_limit: 1.0               # Requests per second

crawler:
  max_datasets_per_source: 100   # Cap per source
  max_queries_per_source: 5      # Queries to execute
  deduplicate: true             # Remove duplicates

validation:
  require_url: true
  require_title: true
  min_description_length: 10

logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: logs/crawler.log
```

### Source Configuration (`sources.yaml`)
```yaml
sources:
  govdata:
    name: GovData
    base_url: https://www.govdata.de
    type: ckan
    api_path: /ckan/api/action/package_search
    organization: German Federal Government
    active: true
    rate_limit: 1.0
    max_retries: 3
    priority: 1

default_queries:
  - energy
  - infrastructure
  - telecom

output:
  formats: [json, csv]
  compression: false
  max_file_size_mb: 100
```

---

##  Testing Strategy

### Unit Tests
```python
# tests/integration/test_ckan_source.py
def test_ckan_search():
    config = {'base_url': 'https://test.com', 'type': 'ckan'}
    crawler = CKANSource(config)
    context = CrawlerContext(query='energy', limit=10, offset=0)
    results = crawler.search(context)
    assert len(results) > 0
    assert isinstance(results[0], Dataset)
```

### Integration Tests
- Mock HTTP responses for CI/CD
- Test against staging endpoints
- Validate output format

### Validation Tests
- Test invalid source handling
- Test retry mechanism
- Test rate limiting
- Test URL normalization and validation
- Test duplicate detection and completeness selection

---

## 📊 Monitoring & Logging

### Log Levels
- **DEBUG**: Detailed request/response data
- **INFO**: Major operations (source init, search results)
- **WARNING**: Validation failures, missing fields
- **ERROR**: API errors, exceptions

### Log Format
```
2026-08-25 14:30:15 - src.sources.ckan_source - INFO - CKAN search returned 15 datasets
2026-08-25 14:30:16 - src.core.registry - WARNING - Source validation failed: berlin
2026-08-25 14:30:17 - src.core.source_factory - ERROR - Failed to initialize bw_data: DNS resolution failed
```

### Health Metrics
- Active/inactive sources
- Validation pass/fail rates
- Datasets per source
- Average response times

---

## 🔒 Security Considerations

### API Rate Limiting
- Respects source rate limits
- Prevents IP blocking
- Configurable per source

### Input Validation
- Sanitizes API responses
- Validates URLs and data types
- Prevents injection attacks

### Data Privacy
- Only public data sources
- No authentication required
- All data is open/public

---

## Performance Optimization

### Current
- Sequential crawling (simple, reliable)
- In-memory deduplication
- Configurable limits

### Future Optimizations
- [ ] Parallel crawling (async/await)
- [ ] Database storage (PostgreSQL)
- [ ] Incremental crawling (only new data)
- [ ] Caching mechanism
- [ ] Distributed crawling (multiple workers)
- [ ] Custom pagination handling per source

---

## Future Roadmap

### Phase 1 (Current)
- ✅ CKAN support
- ✅ HTML scraping
- ✅ Basic enrichment
- ✅ JSON/CSV output
- ✅ Bounded candidate discovery
- ✅ Runtime URL validation and post-run evidence checking

### Phase 2
- [ ] Socrata source
- [ ] ArcGIS Open Data
- [ ] Asynchronous crawling
- [ ] Database integration

### Phase 3
- [ ] Machine learning classification
- [ ] Registry-backed auto-discovery of data portals
- [ ] Real-time updates
- [ ] Web dashboard

### Phase 4
- [ ] API for querying crawled data
- [ ] Data quality scoring
- [ ] Change detection
- [ ] Data lineage tracking

---


## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| requests | >=2.28 | HTTP client |
| pyyaml | >=6.0 | YAML parsing |
| dataclasses | >=0.7 | Data models |
| pytest | >=7.0 | Testing |

---

**Last Updated**: August 2026
**Version**: 1.0.0