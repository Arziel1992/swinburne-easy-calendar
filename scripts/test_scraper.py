import re
from datetime import datetime
from bs4 import BeautifulSoup

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

def test_scraper():
    with open('calendar_web_sample.txt', 'r', encoding='utf-8') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')
    tables = soup.find_all('table', class_='grid-clean')
    
    periods = {}
    year = "2021"

    current_date_text = ""

    unmatched_events = []

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
                cohort = span.get_text(strip=True).strip('()')
                span.extract()
            else:
                cohort = "Unknown"

            # removing <br> if needed, bs4 get_text handles it
            event_text = desc_td.get_text(separator=' ', strip=True)

            matched = False

            # Rule 1: Explicit Range with (Units Study Period)
            # e.g., VE Block 1 (Units Study Period)
            if '(Units Study Period)' in event_text:
                period_name = event_text.replace('(Units Study Period)', '').strip()
                key = (cohort, period_name)
                if key not in periods: periods[key] = {}
                periods[key]['start'] = start_dt
                if end_dt: periods[key]['end'] = end_dt
                matched = True

            # Rule 2: commences
            elif match := re.search(r'(.*?)\s+(?:classes\s+)?commence', event_text, re.IGNORECASE):
                period_name = match.group(1).strip()
                key = (cohort, period_name)
                if key not in periods: periods[key] = {}
                periods[key]['start'] = start_dt
                matched = True

            # Rule 3: ends
            elif match := re.search(r'(.*?)\s+(?:classes\s+)?end\b', event_text, re.IGNORECASE):
                period_name = match.group(1).strip()
                key = (cohort, period_name)
                if key not in periods: periods[key] = {}
                periods[key]['end'] = start_dt # if range, maybe end_dt? Ends usually are single day
                matched = True

            # Rule 4: census
            elif match := re.search(r'Census [dD]ate for\s+(.*?)(?:\.|$)', event_text, re.IGNORECASE):
                period_name = match.group(1).strip()
                key = (cohort, period_name)
                if key not in periods: periods[key] = {}
                periods[key]['census'] = start_dt
                matched = True

            # Rule 5: Results
            elif match := re.search(r'Result(?:s)? publication(?: date)? for(?::)?\s*(.*?)(?:\.|$)', event_text, re.IGNORECASE):
                period_name = match.group(1).strip()
                # could be multiple if there's bullet points, but let's test simple first
                key = (cohort, period_name)
                if key not in periods: periods[key] = {}
                periods[key]['results'] = start_dt
                matched = True
            
            # Rule 6: FAP
            elif match := re.search(r'(.*?)\s+Final Assessment Period', event_text, re.IGNORECASE):
                period_name = match.group(1).replace(' and Last To Complete', '').strip()
                key = (cohort, period_name)
                if key not in periods: periods[key] = {}
                periods[key]['fapStart'] = start_dt
                if end_dt:
                    periods[key]['fapEnd'] = end_dt
                matched = True
            
            if not matched:
                unmatched_events.append(event_text)

    import json
    # just print first 5 unmatched
    print("UNMATCHED:")
    for u in unmatched_events[:10]:
        print(" -", u)
    
    print("\nPERIODS:")
    for k, v in list(periods.items())[:5]:
        print(f"{k}: {v}")

if __name__ == "__main__":
    test_scraper()
