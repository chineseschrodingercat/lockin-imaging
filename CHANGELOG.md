# Changelog

## 0.2.0 — 2026-10-23

- Rebuilt both figures with large black labels, a prominent synthetic-data marker and complete external figure legends; removed the gray explanatory footnotes.
- Made every workflow stage use the same synthetic recording and fitted example pixel; added a true I/Q phasor and explicit intensity/amplitude colorbars.
- Preserved shared amplitude scales, the positive control noise floor and all default numerical metrics; clarified drift correction, exposure response, timing and the diagnostic frequency scan.
- Added a foundations guide, a detailed mathematical appendix, verified source references and a review record.
- Added independent mathematical and figure-consistency tests.
- Fixed configuration-integrity checking so changes during configuration reading are detected before output maps are saved.
- Included the approved documentation and test helper tools in the source distribution, using explicit file paths.

The numerical demodulation core and synthetic forward model are unchanged. This
release adds no experimental data or unpublished scientific results.

## 0.1.0 — 2026-10-23

Initial public engineering companion:

- Fixed-frequency, exposure-aware I/Q regression with a jointly fitted polynomial baseline.
- Independent per-pixel fits, chunked processing, read-only local-array input and explicit quality flags.
- CLI with new-directory outputs, failure receipts and content hashes.
- Deterministic synthetic scenes, truth/control comparisons and editable workflow figures.
- Analytic, numerical, noise-model, I/O and publication-gate tests.
- Linux/Windows validation workflow, pinned dependencies, wheel packaging and release manifest.

This release contains no experimental data, full research decision pipeline or
unpublished scientific results. Validation scope is documented in the method
and reproduction guides.
