# Changelog

## 1.1.0

### Added

- Direct explanations for individual inventoried files, including named-file questions and clickable file citations. Both the evidence guide and optional local model use metadata only.
- Largest-folder drill-down, named snapshots, and reuse of a snapshot's folder selection.
- Pagination for review findings and large duplicate lists; cached sorting for large file inventories.
- Compressed large JSON transfers and bounded local-model context.
- CSV inventory exports with Unicode support and spreadsheet-formula guards. HTML reports retain snapshot labels and expand evidence locations for printing.
- Reproducible source packaging, an integrity manifest, and a fresh-extraction startup check without Python site-packages.
- Regression tests, hidden-browser workflow tests, seeded metadata property checks, synthetic performance measurements, and an opt-in sustained reliability test.

### Fixed

- Project directories named `bin`, `Lib`, and `dev` were incorrectly excluded as system directories. Unix system-folder rules now apply only at filesystem roots on Unix.
- Demo-only mode could expose saved live snapshots through history. It now stays isolated from live state.
- A cancellation arriving during the database commit could give a misleading cancellation response. The final save and cancellation decision are now serialized.
- Late snapshot, comparison, and assistant responses could overwrite a newer selection. Responses now follow the active snapshot and request generation.
- Corrupt browser review data could crash rendering; shared labels could leak between snapshots. Labels are validated and stored per snapshot.
- A stalled response could outlive a socket timeout. Local-model transport now enforces a wall-clock deadline and size limit, with no proxy or redirect handling.
- Invalid model catalogs, capabilities, and answers now produce a usable fallback message. Cloud-backed aliases are checked before inference.
- SQLite reads no longer create or alter tables. An unrelated database in the configured state location is rejected without being changed.
- Windows “Copy as path” quoting is accepted; mapped network drives are rejected before filesystem lookup.
- Unicode session tokens and unusual filename encodings no longer crash requests or HTML exports.
- Escape removes closed dialogs, failed exports and model refreshes restore controls, and denied clipboard access offers a selected manual-copy path.
- Failed history loading no longer prevents opening the demo. Lost scan connections retry and offer a reconnect control.
- Review-storage failures remain visible; the Windows path example preserves its separators.
- Draft questions survive engine changes and navigation. Long snapshot labels wrap on mobile.
- History failures after a completed scan now stop after the retry limit and offer Reconnect.

### Compatibility

- Python 3.10+ and a modern browser remain the only runtime requirements.
- Existing Lumen snapshots remain readable. Old shared browser labels are intentionally not migrated to the new per-snapshot format.
- No file-removal, uninstall, administrator, shell-execution, or cloud-inference feature was added.

## 1.0.0

Initial local storage inventory, duplicate verification, evidence guide, optional Ollama adapter, SQLite snapshots, exports, and fictional demo.
