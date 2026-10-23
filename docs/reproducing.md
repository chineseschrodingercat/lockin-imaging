# Reproducing the public demonstration

## Installation

Create and activate a Python 3.11–3.13 virtual environment. For PowerShell:

```powershell
python -m venv .venv
.venv/Scripts/Activate.ps1
python -m pip install -r requirements/ci.txt
python -m pip install -e . --no-deps
```

On Linux/macOS, activate with `source .venv/bin/activate`. If environment
activation is restricted, invoke the environment's Python executable directly.
`requirements/ci.txt` pins the validation dependencies. Package metadata uses
bounded compatible ranges for ordinary installation; pins are a reproducibility
snapshot, not a claim that all future versions work.

## Synthetic run and gallery

```bash
python -m lockin_imaging demo --output outputs/demo
python tools/build_gallery.py --output outputs/gallery
```

The demo uses seed `20261023`, 512 frames at 32 frames/s, 1.25 Hz, 18 ms exposure,
and a 64 × 80 pixel scene. These are invented demonstration parameters, not an
experimental operating recipe. Signal and control share a synthetic baseline
and have independent Gaussian noise. The control has no injected modulation.

The numerical outputs should agree to floating-point tolerance across supported
environments. Figure bytes may differ with fonts, operating systems and rendering
library versions. Rendering metadata and array hashes do not imply scientific
validation. The gallery generator writes the public workflow, synthetic figure
and compact metrics without copying any experimental asset.

The workflow uses the same recording as the six-panel figure. Both figures have
[complete external legends](figure-legends.md); editable SVG and high-resolution
PNG exports contain only titles, axes, curve keys, essential equations and the
prominent synthetic-data label.

## Analyze an explicit local array

The demo also writes valid inputs for testing the local-array interface:

```bash
python -m lockin_imaging analyze \
  --stack outputs/demo/synthetic_signal.npy \
  --times outputs/demo/times.npy \
  --config examples/synthetic_config.json \
  --output outputs/reanalysis
```

For PowerShell, enter this as a single line or use its backtick continuation.
Inputs are a C-contiguous numeric `(frames, height, width)` `.npy` file and a
uniformly spaced 1D frame-center time vector. Object arrays/pickle, compressed
archives, color channels and implicit FPS assumptions are not accepted. The
same format accepts user-owned data locally; outputs are ignored by Git.

## Verification

```bash
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m build --no-isolation
python tools/check_release.py
```

Tests cover signed I/Q recovery under multiple phases/drifts/exposures,
exposure correction against numerical integration, noise covariance under its
assumptions, pixel exclusions, memory-map/chunk equivalence, deterministic
simulation, input hashes, failure receipts and refusal to overwrite. CI repeats
the suite on Linux and Windows with Python 3.11 and 3.13 and exercises a built
wheel outside the source directory.

Additional checks verify the appendix's partial-regression identity, the bias
from one-sided detrending, Rayleigh magnitude moments under an isotropic null,
square-wave fundamental/contrast conversion, and finite-window/off-frequency
response. Figure tests connect the displayed example-pixel coefficients,
normalized trace and diagnostic scan to the actual maps. A regression test
changes the configuration file during reading and checks that the run fails.

Consult the linked CI run for the actual status of a commit. A workflow definition
alone is not evidence that the run passed.
