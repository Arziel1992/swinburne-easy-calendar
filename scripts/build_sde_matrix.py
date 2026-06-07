import json
import os
import glob
import sys
import re
import argparse
import shutil
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# --- Configuration ---
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "src", "data")
REQUIRED_FIELDS = ["id", "cohort", "period", "type", "start"]
TEACHING_REQUIRED_FIELDS = ["end", "census"]
NON_TEACHING_TYPES = ["Event", "Holiday", "Deadline"]

def validate_entry(entry, filename, index):
    # 1. Check for basic required fields
    for field in REQUIRED_FIELDS:
        if field not in entry:
            raise ValueError(
                f"[{filename} @ index {index}]: Missing required field '{field}'."
            )

    # 1b. Check for teaching period required fields
    if entry.get("type") not in NON_TEACHING_TYPES:
        for field in TEACHING_REQUIRED_FIELDS:
            if field not in entry:
                raise ValueError(
                    f"[{filename} @ {entry.get('id')}]: Missing required field '{field}' for teaching period."
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
    print("\n--- Initiating SDE Schema Validation ---")

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

            for index, entry in enumerate(yearly_data):
                try:
                    validate_entry(entry, filename, index)
                except ValueError as ve:
                    print(f"FATAL DATA ERROR: {str(ve)}")
                    sys.exit(1)

            total_records_validated += len(yearly_data)

    print(
        f"SUCCESS: All {total_records_validated} records across {len(json_files)} files passed strict schema validation.\n"
    )

# --- SCRAPER LOGIC ---

def parse_date(date_str, year):
    match = re.search(r'(\d{1,2})\s+([A-Za-z]+)', date_str)
    if not match:
        return None
    day_str, month_str = match.groups()
    try:
        dt = datetime.strptime(f"{day_str} {month_str} {year}", "%d %B %Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return None

def extract_dates(date_cell_text, year):
    parts = date_cell_text.split('-')
    start_date = parse_date(parts[0], year)
    end_date = parse_date(parts[1], year) if len(parts) > 1 else None
    return start_date, end_date

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

def match_existing_entry(cohort, scraped_period, existing_data):
    # exact match
    for entry in existing_data:
        if entry.get('cohort') == cohort and entry.get('period') == scraped_period:
            return entry
    # case-insensitive match
    for entry in existing_data:
        if entry.get('cohort') == cohort and entry.get('period', '').lower() == scraped_period.lower():
            return entry
    # fuzzy match for teaching periods (skip events, which have very long descriptions)
    if len(scraped_period) < 40:
        scraped_slug = slugify(scraped_period)
        for entry in existing_data:
            if entry.get('cohort') == cohort and len(entry.get('period', '')) < 40:
                exist_slug = slugify(entry.get('period', ''))
                scraped_core = scraped_slug.replace('higher-education-', '').replace('vocational-education-', '').replace('tafe-', '')
                exist_core = exist_slug.replace('he-', '').replace('oua-', '').replace('ve-', '')
                if scraped_core == exist_core or scraped_core in exist_core or exist_core in scraped_core:
                    return entry
    return None

def get_available_years():
    base_url = "https://www.swinburne.edu.au/student-administration/calendar/"
    print(f"Fetching base calendar URL to find available years...")
    resp = requests.get(base_url)
    if resp.status_code != 200:
        print(f"FATAL: Cannot fetch base URL (Status Code: {resp.status_code}).")
        return []
    soup = BeautifulSoup(resp.text, 'html.parser')
    h4 = soup.find('h4')
    if not h4:
        print("FATAL: Could not find years navigation.")
        return []
    years = []
    for a in h4.find_all('a'):
        txt = a.get_text(strip=True)
        if txt.isdigit():
            years.append(txt)
    return years

def scrape_year(year):
    print(f"Scraping Swinburne calendar for {year}...")
    url = f"https://www.swinburne.edu.au/student-administration/calendar/?year={year}"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"WARNING: Failed to fetch {year} (Status Code: {response.status_code})")
        return {}
    
    soup = BeautifulSoup(response.text, 'html.parser')
    tables = soup.find_all('table', class_='grid-clean')
    
    periods = {}
    current_date_text = ""

    for table in tables:
        for row in table.find_all('tr'):
            cols = row.find_all('td')
            if len(cols) < 2:
                continue
            
            date_col = cols[0].get_text(strip=True)
            if date_col and date_col != '&nbsp;':
                current_date_text = date_col
            else:
                date_col = current_date_text

            start_dt, end_dt = extract_dates(date_col, year)
            if not start_dt:
                continue

            desc_td = cols[1]
            span = desc_td.find('span', class_='teachingArea')
            if span:
                cohort = span.get_text(strip=True)
                if cohort.startswith('('): cohort = cohort[1:]
                if cohort.endswith(')'): cohort = cohort[:-1]
                span.extract()
            else:
                cohort = "Unknown"

            event_text = desc_td.get_text(separator=' ', strip=True)
            matched = False

            def get_period_dict(c, p):
                key = (c, p)
                if key not in periods: periods[key] = {}
                return periods[key]

            if '(Units Study Period)' in event_text:
                period_name = event_text.replace('(Units Study Period)', '').strip()
                pd = get_period_dict(cohort, period_name)
                pd['start'] = start_dt
                if end_dt: pd['end'] = end_dt
                matched = True
            elif match := re.search(r'(.*?)\s+(?:classes\s+)?commence', event_text, re.IGNORECASE):
                period_name = match.group(1).strip()
                pd = get_period_dict(cohort, period_name)
                pd['start'] = start_dt
                matched = True
            elif match := re.search(r'(.*?)\s+(?:classes\s+)?end\b', event_text, re.IGNORECASE):
                period_name = match.group(1).strip()
                pd = get_period_dict(cohort, period_name)
                pd['end'] = start_dt
                matched = True
            elif match := re.search(r'Census [dD]ate for\s+(.*?)(?:\.|$)', event_text, re.IGNORECASE):
                period_name = match.group(1).strip()
                pd = get_period_dict(cohort, period_name)
                pd['census'] = start_dt
                matched = True
            elif match := re.search(r'Result(?:s)? publication(?: date)? for(?::)?\s*(.*?)(?:\.|$)', event_text, re.IGNORECASE):
                period_name = match.group(1).strip()
                pd = get_period_dict(cohort, period_name)
                pd['results'] = start_dt
                matched = True
            elif match := re.search(r'(.*?)\s+Final Assessment Period', event_text, re.IGNORECASE):
                period_name = match.group(1).replace(' and Last To Complete', '').strip()
                pd = get_period_dict(cohort, period_name)
                pd['fapStart'] = start_dt
                if end_dt: pd['fapEnd'] = end_dt
                matched = True
            
            if not matched:
                # Event logic
                event_type = "Event"
                lower_event = event_text.lower()
                if "holiday" in lower_event:
                    event_type = "Holiday"
                elif any(kw in lower_event for kw in ["due date", "last day", "last date", "deadline"]):
                    event_type = "Deadline"

                period_name = event_text
                key = (cohort, period_name)
                if key not in periods:
                    periods[key] = {'start': start_dt, '_event_type': event_type}
                    if end_dt:
                        periods[key]['end'] = end_dt

    return periods

def run_scraper_for_all():
    print("\n--- Initiating Scraper ---")
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    years = get_available_years()
    if not years:
        years = [str(y) for y in range(2021, 2028)] # fallback
        print("Fallback to static years list: " + ", ".join(years))
    else:
        print("Found available years: " + ", ".join(years))

    file_data = {}
    for year_str in years:
        file_path = os.path.join(DATA_DIR, f"{year_str}.json")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                try: file_data[year_str] = json.load(f)
                except Exception: file_data[year_str] = []
        else:
            file_data[year_str] = []

    all_scraped = {}
    for year_str in years:
        periods = scrape_year(year_str)
        for (cohort, period_name), dates in periods.items():
            key = (cohort, period_name)
            if key not in all_scraped:
                all_scraped[key] = {'_source_year': year_str}
            all_scraped[key].update(dates)

    def find_match(c, p):
        for y, data_list in file_data.items():
            entry = match_existing_entry(c, p, data_list)
            if entry: return y, entry
        return None, None

    new_entries = {y: [] for y in years}

    for (cohort, period_name), dates in all_scraped.items():
        matched_year, entry = find_match(cohort, period_name)
        if entry:
            for k, v in dates.items():
                if not k.startswith('_'):
                    entry[k] = v
        else:
            new_type = dates.get('_event_type', "Term")
            if "_event_type" not in dates:
                if "Semester" in period_name: new_type = "Semester"
                elif "Block" in period_name: new_type = "Block"
                elif "Study Period" in period_name: new_type = "Study Period"
                elif "Teaching Period" in period_name: new_type = "Teaching Period"
            
            source_year = dates['_source_year']
            short_desc = period_name[:100]
            new_id = f"{slugify(cohort)}-{slugify(short_desc)}-{source_year}"
            if new_type in NON_TEACHING_TYPES and 'start' in dates:
                new_id += f"-{dates['start']}"
            
            new_entry = {
                "id": new_id,
                "cohort": cohort,
                "period": period_name,
                "type": new_type,
                "intake": False
            }
            for k, v in dates.items():
                if not k.startswith('_'):
                    new_entry[k] = v

            if new_type in NON_TEACHING_TYPES:
                if "start" in new_entry:
                    new_entries[source_year].append(new_entry)
            else:
                if all(req in new_entry for req in ["start", "end", "census"]):
                    new_entries[source_year].append(new_entry)
                else:
                    # Fallback to standalone events for orphaned dates
                    if 'results' in dates:
                        new_entries[source_year].append({
                            "id": f"{slugify(cohort)}-results-{slugify(period_name[:50])}-{source_year}",
                            "cohort": cohort,
                            "period": f"Results publication for {period_name}",
                            "type": "Deadline",
                            "intake": False,
                            "start": dates['results']
                        })
                    if 'census' in dates:
                        new_entries[source_year].append({
                            "id": f"{slugify(cohort)}-census-{slugify(period_name[:50])}-{source_year}",
                            "cohort": cohort,
                            "period": f"Census date for {period_name}",
                            "type": "Deadline",
                            "intake": False,
                            "start": dates['census']
                        })
                    if 'fapStart' in dates:
                        new_entries[source_year].append({
                            "id": f"{slugify(cohort)}-fap-{slugify(period_name[:50])}-{source_year}",
                            "cohort": cohort,
                            "period": f"Final Assessment Period for {period_name}",
                            "type": "Event",
                            "intake": False,
                            "start": dates['fapStart'],
                            **({"end": dates['fapEnd']} if 'fapEnd' in dates else {})
                        })
                    if 'start' in dates and 'end' not in dates and 'census' not in dates:
                        # It just had a start date but wasn't a full teaching period
                        new_entries[source_year].append({
                            "id": f"{slugify(cohort)}-commence-{slugify(period_name[:50])}-{source_year}",
                            "cohort": cohort,
                            "period": f"Commencement of {period_name}",
                            "type": "Event",
                            "intake": False,
                            "start": dates['start']
                        })

    for y, items in new_entries.items():
        file_data[y].extend(items)

    import shutil
    for year_str, merged_data in file_data.items():
        file_path = os.path.join(DATA_DIR, f"{year_str}.json")
        if os.path.exists(file_path):
            bak1 = file_path + ".bak"
            bak2 = file_path + ".bak2"
            if os.path.exists(bak1):
                os.replace(bak1, bak2)
            shutil.copy2(file_path, bak1)
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(merged_data, f, indent=4)
        print(f"  -> Saved {len(merged_data)} records to {year_str}.json")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build and validate SDE calendar matrix.")
    parser.add_argument("mode", nargs="?", choices=["scrape", "lint", "all"], default="all",
                        help="Mode to run: 'scrape' fetching new data, 'lint' validating json, 'all' for both.")

    args = parser.parse_args()

    if args.mode in ["scrape", "all"]:
        run_scraper_for_all()
    
    if args.mode in ["lint", "all"]:
        run_linter()
