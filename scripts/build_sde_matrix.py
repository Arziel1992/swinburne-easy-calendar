import json
import os
import glob
import sys
from datetime import datetime

# --- Configuration ---
# NOTE: If you are using fetch() in Vite, these should ideally be in '../public/data'
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "src", "data")

# --- Schema Enforcement ---
REQUIRED_FIELDS = ["id", "cohort", "period", "type", "start", "end", "census"]


def validate_entry(entry, filename, index):
    # 1. Check for required fields
    for field in REQUIRED_FIELDS:
        if field not in entry:
            raise ValueError(
                f"[{filename} @ index {index}]: Missing required field '{field}'."
            )

    # 2. Validate ISO 8601 Date Formats (YYYY-MM-DD)
    for date_field in ["start", "end", "census", "fapStart", "fapEnd", "results"]:
        date_value = entry.get(date_field)
        if date_value:
            try:
                datetime.strptime(date_value, "%Y-%m-%d")
            except ValueError:
                raise ValueError(
                    f"[{filename} @ {entry.get('id')}]: Invalid date '{date_value}' in '{date_field}'. Must be YYYY-MM-DD."
                )

    # 3. Validate Boolean types
    if "intake" in entry and not isinstance(entry["intake"], bool):
        raise ValueError(
            f"[{filename} @ {entry.get('id')}]: Field 'intake' must be a boolean."
        )


def run_linter():
    print("Initiating SDE Schema Validation...")

    if not os.path.exists(DATA_DIR):
        print(f"FATAL: Directory {DATA_DIR} does not exist.")
        sys.exit(1)

    json_files = glob.glob(os.path.join(DATA_DIR, "*.json"))

    if not json_files:
        print(f"FATAL: No JSON files found in {DATA_DIR}.")
        sys.exit(1)

    total_records_validated = 0

    for file_path in json_files:
        filename = os.path.basename(file_path)
        year_str = filename.replace(".json", "")

        # Ensure filename is a valid year
        if not year_str.isdigit() or len(year_str) != 4:
            print(
                f"FATAL: Invalid filename '{filename}'. Must be a 4-digit year (e.g., 2026.json)."
            )
            sys.exit(1)

        with open(file_path, "r", encoding="utf-8") as f:
            try:
                yearly_data = json.load(f)
            except json.JSONDecodeError as e:
                print(
                    f"FATAL: JSON parsing failed in {filename}. Ensure it is valid JSON. Error: {e}"
                )
                sys.exit(1)

            if not isinstance(yearly_data, list):
                print(f"FATAL: Root element in {filename} must be a JSON array [...].")
                sys.exit(1)

            print(f"Validating {filename} ({len(yearly_data)} records)...")

            for index, entry in enumerate(yearly_data):
                try:
                    validate_entry(entry, filename, index)
                except ValueError as ve:
                    print(f"FATAL DATA ERROR: {str(ve)}")
                    sys.exit(1)

            total_records_validated += len(yearly_data)

    print(
        f"\nSUCCESS: All {total_records_validated} teaching periods across {len(json_files)} files passed strict schema validation."
    )


if __name__ == "__main__":
    run_linter()
