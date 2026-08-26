"""Output formatting helpers."""

import csv
import json


def write_csv(datasets, csv_file):
	"""Write datasets using the public CSV output schema."""
	fieldnames = ['dataset_id', 'dataset_title', 'description', 'organization', 'organization_id',
				  'source_name', 'source_type', 'api_url', 'data_formats', 'geographic_coverage',
				  'license', 'last_updated', 'infrastructure_categories', 'source_url', 'download_urls',
				  'resources', 'access_status', 'source_url_status', 'source_url_validation',
				  'resource_validation', 'validation_timestamp', 'matched_keywords', 'tags',
				  'resource_count', 'views', 'downloads']
	with open(csv_file, 'w', newline='', encoding='utf-8') as handle:
		writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction='ignore')
		writer.writeheader()
		for dataset in datasets:
			row = dataset.to_dict()
			row['data_formats'] = '; '.join(row.get('data_formats', []))
			row['infrastructure_categories'] = '; '.join(row.get('infrastructure_categories', []))
			row['download_urls'] = '; '.join(row.get('download_urls', []))
			row['matched_keywords'] = '; '.join(row.get('matched_keywords', []))
			row['tags'] = '; '.join(row.get('tags', []))
			row['resources'] = json.dumps(row.get('resources', []), ensure_ascii=False)
			row['source_url_validation'] = json.dumps(row.get('source_url_validation', {}), ensure_ascii=False)
			row['resource_validation'] = json.dumps(row.get('resource_validation', []), ensure_ascii=False)
			writer.writerow(row)
