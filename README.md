# **Swinburne Unified Academic Calendar**

A high-performance, accessible, and reactive Single Page Application (SPA) designed to solve the UX and data architecture failures of standard institutional PDF calendars.

## **Architecture & Data Governance**

Institutional PDFs are inherently unstable. Tables change, columns merge, and typographical errors occur year-over-year. Relying on automated PDF scraping for critical academic, financial, and census dates introduces unacceptable systemic risk.  
This project enforces a decoupled, highly-validated data pipeline:

1. **Human-in-the-Loop Normalisation:** Raw PDF data is manually transcribed and verified into a strict JSON schema per academic year.
2. **Decentralised Payload:** Data is stored as individual yearly JSON files (`/src/data/{YYYY}.json`).
3. **Automated Validation:** A Python linter (`scripts/build_sde_matrix.py`) aggressively validates the schema, data types, and date formatting (ISO 8601) of every file during the CI/CD pipeline. The build will intentionally fail if corrupt or malformed data is detected, protecting the production runtime environment.
4. **Reactive UI Engine:** The frontend consumes the verified JSON using Svelte 5 Runes, enabling complex, instantaneous cross-filtering with zero DOM overhead.

## **Tech Stack**

* **Frontend:** Svelte 5, Vite, Tailwind CSS  
* **Data Storage:** Decentralised static JSON files (`/src/data/{YYYY}.json`)  
* **Validation / Linter:** Python 3.11+
* **CI/CD:** GitHub Actions (Automated validation and deployment to GitHub Pages)

## **Local Development**

### **Prerequisites**

* Node.js (v20+)
* Python (3.11+)

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

When a new academic calendar is published, **do not attempt to build a PDF scraper**. Follow this manual protocol to maintain data integrity:

1. Create a new JSON file in the data directory named for the academic year (e.g., `2027.json`).  
2. Transcribe the data using the established array-of-objects schema.  
3. **Critical Validation:** Ensure all dates are strictly formatted in ISO 8601 (`YYYY-MM-DD`).  
4. Run `npm run sde:build` locally. If the linter throws a fatal error, fix your data.  
5. Test the new year locally by selecting it in the UI dropdown.  
6. Commit your new `YYYY.json` file and push to the `main` branch. The GitHub Actions pipeline will re-validate your data before deployment.

## **License**

This project is licensed under the terms outlined in the [LICENSE](http://docs.google.com/LICENSE) file.  
Made with ❤️ for Swinburne — By E. Ketterer
