# Changelog

## 2026-06-07 - 21:03
- Fix Svelte duplicate key bug (`each_key_duplicate`) by using a longer 100-character truncation and appending start dates for standalone events.
- Enhance Python scraper to capture all non-teaching standalone events (Holidays, Deadlines, Events).
- Implement dynamic year discovery and automated local backups (`.bak` and `.bak2`).
- Setup GitHub Actions weekly cron workflow to automatically update the calendar.


## 2026-06-04 - 23:03
- Add Academic Year filter to the Svelte 5 engine.
- Default Academic Year to the real-world current year, with fallback to the most recent loaded year.
- Refactor calendar initializer to anchor itself to today (`today.getFullYear()` and `today.getMonth()`).
- Upgrade filtration engine `$derived` to cross-reference `academicYear`.
- Switch data loading from `calendar_matrix.json` to individual yearly JSONs (`src/data/20*.json`).
- Add copyright footer pointing to repo and license.
