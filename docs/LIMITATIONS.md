This document records the crawler's current limitations and the boundaries of
its generated evidence. These constraints are intentional where they protect
source availability and responsible crawling.

## Short Assessment Summary

The crawler catalogs metadata from configured seeds and bounded discovered
candidates, but catalogue quality and availability vary. The following
information may be unavailable or unreliable for individual datasets:

- Source or download URLs may be stale, inaccessible, malformed, or blocked.
- Licence information may be missing or inconsistent.
- Geographic coverage may be absent or inferred only from text and tags.
- Access status reflects the live validation request and can change later.
- Offline runs intentionally report `unknown`/`not_checked` and are not
  evidence of reachability.
- Resource contents are not downloaded or independently verified; resource URL
  validation only checks the recorded HTTP response.
- Unsupported custom APIs, authentication-protected portals, CAPTCHAs, and
    robots-restricted pages are skipped.

## Assessment Scope and Current Limitations

- Not all German open-data portals expose machine-readable APIs.
- Metadata fields vary significantly between catalogues, so URLs, licences,
  and geographic coverage may be unavailable.
- CKAN is the primary structured adapter; custom APIs and unsupported catalogue
  types are not crawled automatically.
- Generic HTML extraction is less reliable than structured API extraction.
- robots.txt, authentication, CAPTCHA, or other access restrictions may cause
  a source to be skipped.
- Candidate discovery is intentionally bounded by configured source, page,
  depth, domain, and robots limits. It is not a general search engine.
- Duplicate detection uses heuristic fingerprints and may not identify every
  semantic duplicate.
- URL validation checks reachability and HTTP status but does not guarantee
  that a resource remains available after the crawl.
- `scripts/validate_output.py` checks recorded evidence without making new HTTP
  requests. Its PASS result means the artifact is internally supported by the
  recorded evidence; it is not a guarantee that URLs remain live.
- The validated-only CSV excludes inaccessible, unknown, invalid, and
  incomplete-evidence records. The full JSON/CSV remains the audit source.
- Keyword classification can produce `uncategorized` when title, description,
  and tags contain no configured match; it is not semantic classification.
- The crawler catalogs metadata and avoids downloading large underlying files.
- Results depend on the availability and relevance of configured seeds and
  discovered candidates; the crawler does not fabricate missing metadata.

---
