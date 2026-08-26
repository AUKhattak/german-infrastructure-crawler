"""Validate generated crawler output without making network requests."""

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse, urlunparse


REQUIRED_VALIDATED_SOURCES = 20
SUPPORTED_CATEGORIES = (
	"power", "renewable", "land", "telecom", "public_facility"
)
STATUS_NAMES = {"accessible", "inaccessible", "error", "invalid", "unknown", "not_checked"}


def normalize_url(url):
	"""Normalize a URL for structural comparison without making a request."""
	if not isinstance(url, str) or not url.strip():
		return None
	parsed = urlparse(url.strip())
	if parsed.scheme.lower() not in ("http", "https") or not parsed.netloc:
		return None
	return urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path or "/", "", parsed.query, ""))


def _json_value(value, default):
	if not value:
		return default
	try:
		return json.loads(value)
	except (TypeError, json.JSONDecodeError):
		return default


def load_records(input_path):
	"""Load records from the supported JSON or CSV output formats."""
	path = Path(input_path)
	if path.suffix.lower() == ".json":
		with path.open(encoding="utf-8") as handle:
			payload = json.load(handle)
		if isinstance(payload, dict):
			return payload.get("datasets", []), payload.get("metadata", {})
		return payload, {}
	if path.suffix.lower() == ".csv":
		with path.open(encoding="utf-8", newline="") as handle:
			records = []
			for row in csv.DictReader(handle):
				for field in ("resources", "source_url_validation", "resource_validation"):
					row[field] = _json_value(row.get(field), [] if field != "source_url_validation" else {})
				for field in ("infrastructure_categories", "download_urls", "data_formats"):
					row[field] = [item for item in row.get(field, "").split("; ") if item]
				records.append(row)
		return records, {}
	raise ValueError("Input must be a .json or .csv file")


def _validation_evidence(record):
	evidence = record.get("source_url_validation") or {}
	return evidence if isinstance(evidence, dict) else {}


def _is_validated(record):
	"""Return whether a record contains complete runtime validation evidence."""
	evidence = _validation_evidence(record)
	source_url = normalize_url(record.get("source_url", ""))
	http_status = evidence.get("http_status", record.get("http_status"))
	timestamp = evidence.get("validated_at") or record.get("validation_timestamp")
	return (
		str(record.get("access_status") or "unknown").lower() == "accessible"
		and source_url is not None
		and http_status is not None
		and timestamp
	)


def validated_unique_records(records):
	"""Return the first validated record for each normalized source URL."""
	unique = []
	seen_urls = set()
	for record in records:
		source_url = normalize_url(record.get("source_url", ""))
		if _is_validated(record) and source_url not in seen_urls:
			seen_urls.add(source_url)
			unique.append(record)
	return unique


def write_validated_csv(records, output_path):
	"""Write validated unique records while preserving structured metadata."""
	if not records:
		raise ValueError("No validated records available for CSV output")
	fieldnames = list(dict.fromkeys(field for record in records for field in record))
	with Path(output_path).open("w", encoding="utf-8", newline="") as handle:
		writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
		writer.writeheader()
		for record in records:
			row = {}
			for field in fieldnames:
				value = record.get(field, "")
				row[field] = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value
			writer.writerow(row)


def validate_records(records):
	"""Return a machine-readable evidence report for output records."""
	total = len(records)
	normalized_urls = [normalize_url(record.get("source_url", "")) for record in records]
	valid_urls = [url for url in normalized_urls if url]
	url_counts = Counter(valid_urls)
	duplicate_count = sum(count - 1 for count in url_counts.values() if count > 1)
	unique_source_count = len(url_counts)

	category_counts = Counter()
	status_counts = Counter()
	evidence_problems = []
	descriptions = licences = resources = api_urls = 0

	for index, record in enumerate(records, 1):
		categories = record.get("infrastructure_categories") or []
		if isinstance(categories, str):
			categories = [item for item in categories.split("; ") if item]
		for category in categories:
			category_counts[category] += 1

		status = str(record.get("access_status") or "unknown").lower()
		status_counts[status] += 1
		evidence = _validation_evidence(record)
		http_status = evidence.get("http_status", record.get("http_status"))
		timestamp = evidence.get("validated_at") or record.get("validation_timestamp")
		source_url = record.get("source_url", "")
		structural_url = normalized_urls[index - 1]
		is_accessible = status == "accessible"

		missing = []
		if not structural_url:
			missing.append("source URL")
		if not (record.get("dataset_title") or record.get("title")):
			missing.append("dataset title")
		category_problem = not categories or not any(category in SUPPORTED_CATEGORIES for category in categories)
		if http_status is None:
			missing.append("HTTP status")
		if not timestamp:
			missing.append("validation timestamp")
		if missing:
			evidence_problems.append({"record": index, "problems": missing})
		if category_problem:
			evidence_problems.append({"record": index, "problems": ["supported category"]})

		evidence_status = str(evidence.get("status") or record.get("source_url_status") or "not_checked").lower()
		resource_evidence = record.get("resource_validation") or []
		resource_accessible = any(
			isinstance(item, dict) and item.get("status") == "accessible"
			for item in resource_evidence
		)
		if status == "accessible" and evidence_status != "accessible" and not resource_accessible:
			evidence_problems.append({"record": index, "problems": [
				"accessible status without accessible URL evidence"
			]})
		if status in {"unknown", "not_checked"} and (http_status is not None or timestamp):
			evidence_problems.append({"record": index, "problems": [
				"unknown status has validation evidence"
			]})
		if status == "inaccessible" and (evidence_status == "accessible" or resource_accessible):
			evidence_problems.append({"record": index, "problems": [
				"inaccessible status conflicts with accessible URL evidence"
			]})
		if record.get("description"):
			descriptions += 1
		if record.get("license") and str(record["license"]).lower() != "unknown":
			licences += 1
		if record.get("resources") or record.get("download_urls"):
			resources += 1
		if record.get("api_url"):
			api_urls += 1

	return {
		"status": "PASS" if len(validated_unique_records(records)) >= REQUIRED_VALIDATED_SOURCES else "FAIL",
		"required_validated_sources": REQUIRED_VALIDATED_SOURCES,
		"validated_unique_sources": len(validated_unique_records(records)),
		"total_records": total,
		"unique_sources": unique_source_count,
		"duplicates": duplicate_count,
		"status_counts": dict(status_counts),
		"category_counts": {category: category_counts.get(category, 0) for category in SUPPORTED_CATEGORIES},
		"uncategorized": category_counts.get("uncategorized", 0),
		"metadata": {
			"descriptions_present": descriptions,
			"descriptions_missing": total - descriptions,
			"known_licences": licences,
			"unknown_licences": total - licences,
			"records_with_resources": resources,
			"records_with_api_urls": api_urls,
			"records_with_neither_download_or_api": total - resources - api_urls + sum(
				1 for record in records if (record.get("resources") or record.get("download_urls")) and record.get("api_url")
			),
		},
		"evidence_problems": evidence_problems,
		"invalid_urls": sum(1 for url in normalized_urls if not url),
	}


def print_report(report, input_path):
	print("=" * 50)
	print("20-SOURCE OUTPUT VALIDATION")
	print("=" * 50)
	print(f"\nInput: {input_path}\n")
	print("Records:")
	print(f"  Total:              {report['total_records']}")
	print(f"  Unique sources:     {report['unique_sources']}")
	print(f"  Duplicates:         {report['duplicates']}")
	print("\nValidation:")
	for status in ("accessible", "inaccessible", "error", "unknown", "not_checked", "invalid"):
		print(f"  {status.capitalize():18} {report['status_counts'].get(status, 0)}")
	print(f"  Validated unique:   {report['validated_unique_sources']}")
	print(f"  Required:           {report['required_validated_sources']}")
	print("\nCategory coverage:")
	labels = {"land": "Land/Municipality", "public_facility": "Public Facilities"}
	for category, count in report["category_counts"].items():
		print(f"  {labels.get(category, category.title()):18} {count}")
	print(f"  {'Uncategorized':18} {report['uncategorized']}")
	metadata = report["metadata"]
	print("\nMetadata:")
	print(f"  Descriptions:       {metadata['descriptions_present']}/{report['total_records']}")
	print(f"  Known licence:      {metadata['known_licences']}/{report['total_records']}")
	print(f"  Download/resource:  {metadata['records_with_resources']}/{report['total_records']}")
	print(f"  API URL:            {metadata['records_with_api_urls']}/{report['total_records']}")
	print("\nEvidence problems:")
	print(f"  Records with issues: {len(report['evidence_problems'])}")
	print(f"  Invalid URLs:        {report['invalid_urls']}")
	print(f"\nFINAL STATUS: {report['status']}")


def main(argv=None):
	parser = argparse.ArgumentParser(description="Validate generated crawler output evidence")
	parser.add_argument("input", help="Generated JSON or CSV output file")
	parser.add_argument("--report", help="Optional path for validation_report.json")
	parser.add_argument("--validated-csv", help="Optional path for validated unique records CSV")
	args = parser.parse_args(argv)
	try:
		records, _ = load_records(args.input)
		report = validate_records(records)
		if args.validated_csv:
			write_validated_csv(validated_unique_records(records), args.validated_csv)
	except (OSError, ValueError, json.JSONDecodeError) as exc:
		print(f"ERROR: {exc}", file=sys.stderr)
		return 2
	print_report(report, args.input)
	if args.report:
		with Path(args.report).open("w", encoding="utf-8") as handle:
			json.dump(report, handle, indent=2, ensure_ascii=False)
	return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
	sys.exit(main())
