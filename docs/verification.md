# Verification record — Lumen 1.1

Checks were run on the Windows development remote desktop using self-created fixtures inside this checkout. Personal folders, drives, and the real installed-application registry were not inventoried. No administrator commands or model installation were used.

## Completed checks

| Check | Result |
| --- | --- |
| Backend regression suite | 76 tests passed on Python 3.14 |
| Hidden Chromium/Electron workflows | 32 checks passed; desktop and 390 px mobile views inspected, including offline report rendering and PDF output |
| Seeded property checks | 2,000 generated metadata cases passed |
| Synthetic metadata benchmark | 100,000 files, 5,000 findings; SQLite round trip verified |
| Real filesystem fixture benchmark | 10,000 generated 1 KiB files; all contents and modification times verified unchanged |
| Sustained HTTP/scan/store test | Passed: 3,600.05 seconds, 356 scan/save cycles, 3,434 HTTP requests, zero errors |
| Extracted source release | Deterministic build, manifest integrity, extracted backend tests, and demo startup with `python -S` passed |

The property checks validate category totals, review-byte bounds, duplicate/generated-folder overlap, bounded model context, masked selected roots, and snapshot size deltas. Generated metadata does not correspond to files on the host.

The sustained run exercised inventory, full duplicate hashing, SQLite saves, concurrent HTTP reads, and evidence-guide requests. It verified all 80 generated fixture files after every cycle and finished without changing their contents. Later interface and export improvements were checked separately by the final regression and browser suites.

## Performance scope

A measured backend run on this machine processed 100,000 generated metadata records in 0.56 seconds, saved them in 0.51 seconds, reloaded them in 0.45 seconds, and compared them in 0.17 seconds. The resulting SQLite database was about 54 MiB. These are **analysis and persistence timings after inventory**, not filesystem-scan throughput.

The hidden-browser benchmark displayed a 100,000-record inventory and filtered it in well under 100 ms in measured runs. It checks JavaScript rendering work, not network transfer or physical disk reads. Review and duplicate DOM sizes are bounded to 24 findings and 12 groups with 20 paths each. Hardware, data distribution, browser, and concurrent work affect results; these measurements are not speed guarantees.

A separate filesystem benchmark created 10,000 small files inside the project, then inventoried and fully hashed them in **55.12 seconds**, finding all 5,000 expected duplicate pairs. CSV generation took 1.16 seconds and a SQLite save/reload took 0.41 seconds. Every file's content hash and modification timestamp matched its pre-scan value. The temporary fixture was then removed. This workload uses newly created 1 KiB files and a warm filesystem cache; large files, other storage devices, and other machines will behave differently. The scanner rechecks file identities and parent paths before hashing, which adds metadata I/O.

## What remains environment-dependent

- The optional Ollama adapter was tested using fake model responses and a fixture HTTP server. No real model was installed or benchmarked here; natural-language answer quality is unmeasured.
- Windows is the locally exercised platform. CI is configured for Windows/Ubuntu and Python 3.10/3.14, but that remote workflow has not run from this workspace.
- Installed-app metadata is an optional, read-only registry feature. Development verification deliberately did not enumerate real applications on this remote desktop.
- Metadata may be incomplete due to exclusions, permissions, or scan limits. Access time cannot establish when a person last opened a file.

Commands for reproducing each check are in the [README](../README.md#verification). Test outputs live under ignored `.qa/` and are excluded from the portable release.
