import importlib.util
import csv
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "validate_output.py"
SPEC = importlib.util.spec_from_file_location("validate_output", SCRIPT)
validate_output = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_output)


def record(index, category="power", status="accessible", evidence=True, license_value="Unknown"):
    item = {
        "dataset_id": f"dataset-{index}",
        "dataset_title": f"Dataset {index}",
        "description": "A real dataset description",
        "source_url": f"https://source{index}.example.test/dataset",
        "api_url": f"https://source{index}.example.test/api",
        "resources": [{"url": f"https://source{index}.example.test/data.csv"}],
        "license": license_value,
        "infrastructure_categories": [category],
        "access_status": status,
    }
    if evidence:
        item["source_url_validation"] = {
            "url": item["source_url"],
            "status": status,
            "http_status": 200 if status == "accessible" else 404,
            "validated_at": "2026-08-27T00:00:00+00:00",
        }
        item["validation_timestamp"] = "2026-08-27T00:00:00+00:00"
    return item


def test_twenty_unique_validated_records_pass():
    report = validate_output.validate_records([record(index) for index in range(20)])

    assert report["status"] == "PASS"
    assert report["validated_unique_sources"] == 20


def test_nineteen_validated_records_fail():
    report = validate_output.validate_records([record(index) for index in range(19)])

    assert report["status"] == "FAIL"
    assert report["validated_unique_sources"] == 19


def test_duplicate_sources_are_not_counted_twice():
    records = [record(index) for index in range(19)]
    records.extend([records[0].copy(), records[1].copy()])

    report = validate_output.validate_records(records)

    assert report["total_records"] == 21
    assert report["unique_sources"] == 19
    assert report["duplicates"] == 2
    assert report["validated_unique_sources"] == 19
    assert report["status"] == "FAIL"


def test_missing_evidence_is_reported_and_not_validated():
    item = record(1, evidence=False)
    item["source_url"] = "not-a-url"

    report = validate_output.validate_records([item])

    assert report["validated_unique_sources"] == 0
    assert report["invalid_urls"] == 1
    assert {"HTTP status", "validation timestamp", "source URL"}.issubset(
        set(report["evidence_problems"][0]["problems"])
    )


def test_unknown_and_not_checked_do_not_count():
    records = [record(1, status="unknown"), record(2, status="not_checked")]

    report = validate_output.validate_records(records)

    assert report["validated_unique_sources"] == 0
    assert report["status_counts"] == {"unknown": 1, "not_checked": 1}


def test_contradictory_validation_metadata_is_reported():
    item = record(1, status="unknown")
    item["source_url_validation"] = {"status": "accessible", "http_status": 200}

    report = validate_output.validate_records([item])

    assert any(
        "unknown status has validation evidence" in problem
        for issue in report["evidence_problems"]
        for problem in issue["problems"]
    )


def test_category_coverage_and_optional_licence_reporting():
    records = [
        record(1, "power", license_value="CC BY 4.0"),
        record(2, "renewable"),
        record(3, "land"),
        record(4, "telecom"),
        record(5, "public_facility"),
    ]

    report = validate_output.validate_records(records)

    assert report["category_counts"] == {
        "power": 1,
        "renewable": 1,
        "land": 1,
        "telecom": 1,
        "public_facility": 1,
    }
    assert report["metadata"]["known_licences"] == 1
    assert report["metadata"]["unknown_licences"] == 4


def test_validated_unique_records_remove_duplicates():
    records = [record(1), record(1), record(2, status="inaccessible")]

    validated = validate_output.validated_unique_records(records)

    assert len(validated) == 1
    assert validated[0]["dataset_id"] == "dataset-1"


def test_validated_csv_preserves_metadata(tmp_path):
    output_path = tmp_path / "validated.csv"
    validate_output.write_validated_csv([record(1)], output_path)

    with output_path.open(encoding="utf-8", newline="") as handle:
        row = next(csv.DictReader(handle))
    assert row["dataset_title"] == "Dataset 1"
    assert row["access_status"] == "accessible"
    assert '"http_status": 200' in row["source_url_validation"]
