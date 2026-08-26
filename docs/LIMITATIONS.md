This document highlights the **current design choices** that create **opportunities for future enhancement**. Rather than limitations, these are **foundational decisions** that provide clear paths for extension and improvement.

## Short Assessment Summary

The crawler catalogs metadata from public seed catalogues, but catalogue
quality and availability vary. The following information may be unavailable or
unreliable for individual datasets:

- Source or download URLs may be stale, inaccessible, malformed, or blocked.
- Licence information may be missing or inconsistent.
- Geographic coverage may be absent or inferred only from text and tags.
- Access status reflects the validation request and can change later.
- Resource contents are not downloaded or independently verified.
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
- Source discovery is intentionally bounded by configured source, page, and
  depth limits.
- Duplicate detection uses heuristic fingerprints and may not identify every
  semantic duplicate.
- URL validation checks reachability and HTTP status but does not guarantee
  that a resource remains available after the crawl.
- The crawler catalogs metadata and avoids downloading large underlying files.
- Results depend on the availability and relevance of the configured public
  seed portals; the crawler does not fabricate missing metadata.

---
