import csv

from src.models.dataset import Dataset
from src.processors.formatter import write_csv


def test_csv_includes_description_and_api_url(tmp_path):
	dataset = Dataset(
		'id', 'Title', 'A useful description', 'Org', 'Portal', 'ckan',
		url='https://example.test/dataset/id',
		api_url='https://example.test/api/action/package_search',
	)
	csv_file = tmp_path / 'datasets.csv'

	write_csv([dataset], csv_file)

	with csv_file.open(encoding='utf-8', newline='') as handle:
		row = next(csv.DictReader(handle))
	assert row['description'] == 'A useful description'
	assert row['api_url'] == 'https://example.test/api/action/package_search'


def test_csv_handles_empty_description(tmp_path):
	dataset = Dataset('id', 'Title', '', 'Org', 'Portal', 'ckan')
	csv_file = tmp_path / 'datasets.csv'

	write_csv([dataset], csv_file)

	with csv_file.open(encoding='utf-8', newline='') as handle:
		row = next(csv.DictReader(handle))
	assert row['description'] == ''


def test_csv_contains_json_scalar_metadata_columns(tmp_path):
	dataset = Dataset('id', 'Title', 'Description', 'Org', 'Portal', 'ckan')
	csv_file = tmp_path / 'datasets.csv'
	write_csv([dataset], csv_file)

	with csv_file.open(encoding='utf-8', newline='') as handle:
		columns = set(next(csv.reader(handle)))
	serialized = set(dataset.to_dict())

	assert serialized.issubset(columns)