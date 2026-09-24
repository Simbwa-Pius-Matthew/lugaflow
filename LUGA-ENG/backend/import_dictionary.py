import argparse

from dictionary_loader import import_csv


parser = argparse.ArgumentParser(
    description="Import a vetted Luganda-English CSV dictionary")
parser.add_argument(
    "csv_file", help="CSV file with luganda and english columns")
args = parser.parse_args()

count = import_csv(args.csv_file)
print(f"Imported {count} dictionary entries into dictionary_data.json")
