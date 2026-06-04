# Changelog

## 2026-06-04 - 23:03
- Add Academic Year filter to the Svelte 5 engine.
- Default Academic Year to the real-world current year, with fallback to the most recent loaded year.
- Refactor calendar initializer to anchor itself to today (`today.getFullYear()` and `today.getMonth()`).
- Upgrade filtration engine `$derived` to cross-reference `academicYear`.
- Switch data loading from `calendar_matrix.json` to individual yearly JSONs (`src/data/20*.json`).
- Add copyright footer pointing to repo and license.
