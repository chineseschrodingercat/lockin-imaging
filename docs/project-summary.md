# Project summary

The research project develops computational workflows for periodic fluorescence
imaging in a quantum-sensing setting. The engineering problem is to separate
modulation from ordinary brightness while keeping timing, preprocessing and
measurement definitions inspectable.

The broader local workflow includes acquisition quality assessment, image
alignment, per-pixel temporal analysis, spatial evidence review, matched control
comparison and figure preparation. Those capabilities provide context for this
repository; their experiment-specific implementations and scientific findings
are not released here.

## What is executable here

1. Generate a reproducible image sequence with known periodic and static objects.
2. Fit polynomial drift and exposure-integrated cosine/sine components jointly.
3. Produce amplitude, phase, normalized amplitude, residual and quality maps.
4. Compare the demonstration with its known truth and an independent-noise control.
5. Save the configuration, diagnostics and content hashes in a separate run folder.

The package accepts local preconverted grayscale arrays in addition to the
synthetic example. It is a simplified public implementation of the general
numerical substrate, with new packaging, tests and demonstration code. It does
not reproduce the complete research estimator or its results.

## Skills made inspectable

The code demonstrates translation of a measurement model into numerical linear
algebra; explicit handling of exposure integration and normalization; bounded
working-memory processing; traceable data handling; test design using known
truth; cross-platform packaging; and clear communication of result semantics.

## Evidence boundary

All public figures and metrics are generated from invented signals. No raw
experimental image, sample identity, calibrated acquisition recipe, final
selection rule, unpublished effect size, sensitivity/specificity estimate or
manuscript figure is present. A separate local research inventory records the
latest experimental code and results; it is intentionally outside this Git
repository. Public examples demonstrate software behavior, not publication
claims or priority for an undisclosed scientific result.
