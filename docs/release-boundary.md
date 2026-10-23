# Public release boundary

This repository publishes executable engineering evidence with minimal research
disclosure. It is separate from the working research directories and starts with
a new Git history.

| Included | Retained outside the repository |
|---|---|
| General harmonic fitting, explicit I/O and quality checks | Full research estimator and experiment-specific decision logic |
| Invented simulation and its computed workflow | Raw or processed measured images and videos |
| Synthetic amplitude-recovery metrics | Sample-level results, outcome tables and calibration records |
| Tests, CI, packaging and mathematical documentation | Research notebooks, manuscripts and internal reports |
| Synthetic display assets and exact generation code | Experimental figures, slides and their source tables |

Removing labels from a measured image or cropping a figure does not remove all
scientific information. This release therefore uses no experimental thumbnail,
anonymized trace, downsampled raw image or selected unpublished result.

## Publication gate

`PUBLIC_FILES.json` is an explicit list of reviewed paths. `RELEASE_MANIFEST.json`
records hashes for those files (canonical LF text), excluding its own self-hash. The publication
checker examines **Git index bytes**, rejects unexpected/missing paths, checks
the manifest and screens text for credentials and machine-specific absolute
paths. Only the declared synthetic PNG/SVG assets may be binary/embedded images.

The gate is a mechanical backstop. It cannot establish scientific confidentiality
from arbitrary prose or prove that an image is synthetic. Human review of the
content boundary and reproducible generation of the included gallery are still
part of release preparation. Do not auto-discover and approve a whole research
directory. `.gitignore` alone cannot protect files already present in Git history.

## Future changes

Keep new results in ignored local outputs first. Review any new path before
adding it to the allowlist. Publication of experimental data, detection rules or
manuscript results requires a separate scope decision by the project author.
This release does not change the visibility or history of other repositories.
