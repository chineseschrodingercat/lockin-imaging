# Version 0.2.0 review record

The review covers the public code, both gallery figures, captions, mathematical
definitions, provenance and release-file boundary. It is an engineering and
scientific-consistency review, not an independent experimental validation or
external peer review.

| Finding | Correction | Verification |
|---|---|---|
| Gray explanatory text was too small and duplicated caption material | Moved settings and interpretation to full figure legends; used large black labels and a prominent colored synthetic-data marker | Inspected rendered PNGs and editable SVG text |
| Workflow curves and heatmap were separate schematic elements, making the causal sequence easy to overread | All stages now use the same synthetic recording, example pixel and actual fit; I/Q shown as an equal-axis phasor | Example coefficients agree with the map outputs |
| Mean fluorescence lacked a quantitative colorbar | Added an explicit intensity scale; every amplitude map displays the same amplitude limits | Display ranges cover every displayed pixel |
| Drift-corrected trace labeling did not fully specify the transform | Provided the exact formula, separate signal/control baselines and exposure attenuation in the caption | Reconstructed the original trace from the display transform |
| A nearly dark control could be mistaken for a zeroed or thresholded map | Retained every positive noise magnitude on the shared scale and reported descriptive control metrics in the legend | Verified no control values were set to zero |
| “16 s recording” could be confused with the first-to-last-center span | Distinguished 16 s nominal record length from the 15.96875 s center span; gave exact excerpt endpoints | Timestamp and excerpt checks |
| A fine scan grid could imply more independent frequency information | Explained per-frequency refitting, the fixed map reference, finite-window response and scope of the scan | Reference-frequency scan matches the image estimator |
| Mathematical assumptions and background sources were too terse | Added foundations, derivations and a source guide with explicit source roles | Independent projection, integration, noise-moment and frequency-response tests |
| GitHub's math renderer rejected operator-name markup in several equations | Replaced it with compatible upright text notation without changing the formulas | Inspected the rendered method and appendix pages |
| Configuration was read before its first integrity hash | Moved the initial hash before parsing, so a change during reading is compared against the original file | A mutation-during-read regression test fails the run and prevents map output |
| The source distribution omitted helper tools required by its tests | Added explicit source-archive entries for the public guides, figures and tools | Ran the tests from an extracted source distribution |

The default synthetic numerical metrics are unchanged from 0.1.0. The numerical
core and synthetic generator are unchanged; the mean image now accumulates in
float64 for consistency with the calculation precision. No real image, sample
identifier, research threshold, calibrated recipe or unpublished result was
added to the public tree. The prior release remains available in Git history.

Local validation includes 87 tests, lint/format checks, synthetic replay,
gallery rendering, package construction and the explicit publication gate.
The repository's CI repeats tests, rendering, replay and wheel execution on
Linux/Windows and Python 3.11/3.13. Consult the run for the corresponding commit
for its actual status. Captions and the mathematical appendix state the limits
of what these checks establish.
