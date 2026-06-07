# **Swinburne Unified Academic Calendar**

A high-performance, accessible, and reactive Single Page Application (SPA) designed to solve the UX and data architecture failures of standard institutional PDF calendars.

## **Architecture & Data Governance**

Institutional PDFs are inherently unstable. Tables change, columns merge, and typographical errors occur year-over-year. Relying on automated PDF scraping for critical academic, financial, and census dates introduces unacceptable systemic risk.  
This project enforces a decoupled, highly-validated data pipeline:

1. **Automated Data Aggregation:** Event data is aggressively scraped and merged from the official HTML Swinburne calendar into a strict JSON schema.
2. **Decentralised Payload:** Data is stored as individual yearly JSON files (`/src/data/{YYYY}.json`).
3. **Automated Validation:** A Python linter (`scripts/build_sde_matrix.py`) aggressively validates the schema, data types, and date formatting (ISO 8601) of every file during the CI/CD pipeline. The build will intentionally fail if corrupt or malformed data is detected, protecting the production runtime environment.
4. **Reactive UI Engine:** The frontend consumes the verified JSON using Svelte 5 Runes, enabling complex, instantaneous cross-filtering with zero DOM overhead.

## **Tech Stack**

* **Frontend:** Svelte 5, Vite, Tailwind CSS  
* **Data Storage:** Decentralised static JSON files (`/src/data/{YYYY}.json`)  
* **Validation / Linter:** Python 3.11+ (Features subcommands: `scrape`, `lint`, `all`)
* **CI/CD:** GitHub Actions (Automated weekly scraping, automated validation, and deployment to GitHub Pages)

## **Local Development**

### **Prerequisites**

* Node.js (v20+)
* Python (3.11+)
* Python Packages: `requests`, `beautifulsoup4`

### **Setup**

1. Clone the repository and install frontend dependencies:  

```bash
   npm install
```

1. Run the data validation suite to ensure your local JSON files are schema-compliant:

```bash
   npm run sde:build
```

1. Start the local development server:  

```bash
   npm run dev
```

## **Protocol for Adding New Academic Years**

New academic calendars are automatically fetched, parsed, and deployed! A weekly **GitHub Action** natively runs our custom Python scraper against the official Swinburne endpoints. 

1. **Dynamic Generation:** When Swinburne creates the navigation target for a new year (e.g. 2028), the scraper will automatically fetch the HTML tables.
2. **Merging & Diffing:** The scraper safely merges existing metadata (like manually enforced `id` or `intake` booleans) while integrating the latest accurate dates.
3. **Event Catch-All:** Beyond teaching periods, it will capture non-teaching events including Holidays and Fee Deadlines.
4. **Validation:** The schema linting enforces ISO 8601 strict adherence.
5. **Local Scrape (Optional):** If you wish to trigger it locally, run `python scripts/build_sde_matrix.py scrape`. The process maintains 2 rotating backups (`.bak` and `.bak2`).

## **License**

This project is licensed under the terms outlined in the [LICENSE](http://docs.google.com/LICENSE) file.  
Made with ❤️ for Swinburne — By E. Ketterer
