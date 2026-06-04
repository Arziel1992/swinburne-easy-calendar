import json
import os
import glob
from datetime import datetime

# --- Configuration ---
YEARLY_DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'yearly')
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), '..', 'src', 'data', 'calendar_matrix.json')
PDF_BASE_URL = "https://www.swinburne.edu.au/app/student-admin-files/docs/calendar-higher-education/{year}/he-{year}-calendar.pdf"

# --- Schema Enforcement ---
# As a data governance standard, we fail the build if mandatory fields are missing.
REQUIRED_FIELDS = ['id', 'cohort', 'period', 'type', 'start', 'end', 'census']

def validate_entry(entry, filename):
    for field in REQUIRED_FIELDS:
        if field not in entry:
            raise ValueError(f"Validation Error in {filename}: Missing required field '{field}' in entry '{entry.get('id', 'UNKNOWN')}'")
        
    # Ensure dates are valid ISO format (YYYY-MM-DD)
    for date_field in ['start', 'end', 'census']:
        if entry.get(date_field):
            try:
                datetime.strptime(entry[date_field], '%Y-%m-%d')
            except ValueError:
                raise ValueError(f"Validation Error in {filename}: Invalid date format for '{date_field}' in entry '{entry.get('id')}'. Must be YYYY-MM-DD.")

def build_matrix():
    print("Initiating SDE Matrix Build...")
    
    if not os.path.exists(YEARLY_DATA_DIR):
        print(f"Error: Directory {YEARLY_DATA_DIR} does not exist.")
        print("Please create it and add your modularised {year}.json files.")
        return

    all_periods = []
    json_files = glob.glob(os.path.join(YEARLY_DATA_DIR, '*.json'))
    
    if not json_files:
        print(f"Warning: No JSON files found in {YEARLY_DATA_DIR}.")
        return

    for file_path in json_files:
        filename = os.path.basename(file_path)
        year_str = filename.replace('.json', '')
        
        if not year_str.isdigit():
            print(f"Warning: Skipping {filename}. Filename must be a valid year (e.g., 2025.json).")
            continue
            
        year = int(year_str)
        official_pdf_url = PDF_BASE_URL.format(year=year)

        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                yearly_data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON in {filename}: {e}")
                continue
            
            print(f"Processing {filename} ({len(yearly_data)} records)...")
            
            for entry in yearly_data:
                validate_entry(entry, filename)
                
                # Inject the official source link for auditing and verification
                entry['officialSourceUrl'] = official_pdf_url
                entry['academicYear'] = year
                
                # Normalise optional fields to null if not present to prevent frontend undefined errors
                entry['fapStart'] = entry.get('fapStart', None)
                entry['fapEnd'] = entry.get('fapEnd', None)
                entry['results'] = entry.get('results', None)
                entry['intake'] = entry.get('intake', False)
                
                all_periods.append(entry)

    # Sort the entire matrix chronologically
    all_periods.sort(key=lambda x: x['start'])

    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_periods, f, indent=2)

    print(f"\nSuccess! Compiled {len(all_periods)} teaching periods into {OUTPUT_FILE}")

if __name__ == "__main__":
    try:
        build_matrix()
    except Exception as e:
        print(f"\nBUILD FAILED: {str(e)}")
        exit(1)