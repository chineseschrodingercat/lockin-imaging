# Lock-in imaging

**Recover periodic fluorescence from image stacks with an inspectable, exposure-aware numerical pipeline.**

[![CI](https://github.com/chineseschrodingercat/lockin-imaging/actions/workflows/ci.yml/badge.svg)](https://github.com/chineseschrodingercat/lockin-imaging/actions/workflows/ci.yml)
![Python 3.11–3.13](https://img.shields.io/badge/python-3.11%E2%80%933.13-3776AB)
![Evidence: synthetic](https://img.shields.io/badge/evidence-synthetic_only-006b68)

![Workflow: a grayscale image stack and explicit timing feed a joint drift and harmonic fit; cosine and sine coefficients form amplitude and phase maps, accompanied by quality flags and hashed run records.](docs/assets/workflow.svg)

Fluorescence brightness alone does not reveal whether a location responds to a
periodic stimulus. This package estimates the component at a supplied reference
frequency for every pixel, while accounting for slow drift and finite camera
exposure. It provides a small Python API, a command-line workflow, deterministic
synthetic examples, and tests of the numerical and data-handling contracts.

This is a **public engineering companion to ongoing fluorescence/quantum-sensing
research led by Minhao Liu**. It is a deliberately reduced, refactored software
example, not the complete experimental analysis or a reproduction of unpublished
findings. Every image and result in this repository is synthetic or schematic.

## Run the demo

Python 3.11–3.13. Run these commands from a clone of this repository:

```bash
python -m venv .venv
# Activate the environment using your shell's usual activation command.
python -m pip install -e ".[demo]"
python -m lockin_imaging demo --output outputs/demo
```

Open `outputs/demo/synthetic_demo.png`. The directory also contains signal/control
maps, generated input arrays, configuration, synthetic error metrics, and a
`run.json` record with output hashes. Use a new output directory for each run;
existing results are never silently replaced. No dataset download or credential
is required. [Reproduction instructions](docs/reproducing.md) include exact
dependency pins and the local-input workflow.

![Synthetic results: bright static and modulating spots appear together in mean fluorescence; recovered lock-in amplitude follows the known modulating spots, while a separate zero-modulation control retains a small positive noise floor. A single-pixel trace and diagnostic frequency scan show the supplied reference.](docs/assets/synthetic_demo.png)

**Figure:** three modulating and three static synthetic spots; independent
Gaussian noise in signal and control. Amplitude maps share a color scale. No
detection threshold is applied. The frequency scan is a diagnostic visualization;
the image estimator uses the supplied reference. Exact settings and generated
error measurements are in [synthetic_metrics.json](docs/assets/synthetic_metrics.json).
These are software examples, not instrument sensitivity, particle-identification
accuracy, or a measurement of experimental performance.

## What the code demonstrates

| Engineering concern | Implementation | Evidence to inspect |
|---|---|---|
| Numerical stability | One SVD factorization; polynomial drift and I/Q fitted jointly; conditioning guard | [core.py](src/lockin_imaging/core.py), signed recovery and exposure-integration tests |
| Large image stacks | Read-only NumPy memory maps; bounded pixel chunks; no whole-movie float conversion | Chunk equivalence, unsigned-input and input-integrity tests |
| Explicit scientific meaning | Peak amplitude, phase convention, exposure response and baseline normalization are defined | [Mathematical model](docs/method.md) |
| Failure handling | Strict timing/shape checks; pixel-level flags; incomplete run receipts; refusal to overwrite | [CLI tests](tests/test_cli.py) |
| Reproducibility | Fixed synthetic seeds; pinned development environment; content-hashed outputs | [Reproduction guide](docs/reproducing.md), GitHub Actions |
| Controlled publication | A fresh repository, explicit file allowlist and hash-checked publication gate | [Release boundary](docs/release-boundary.md), [check_release.py](tools/check_release.py) |

## Python API

```python
import numpy as np
from lockin_imaging import LockinConfig, demodulate

times = np.arange(512) / 32.0  # frame-center seconds
trace = 100.0 + 4.0 * np.cos(2 * np.pi * 1.25 * times - 0.3)
result = demodulate(trace, times, LockinConfig(frequency_hz=1.25))
print(float(result.amplitude))  # approximately 4.0
print(float(result.phase_rad))  # approximately 0.3
```

The same API accepts `(frames, traces)` or `(frames, height, width)` arrays. It
does not infer timing, color channels, bit depth, particle identity or a detection
threshold. Local input must already be a stationary, uniformly sampled grayscale
stack. Registration and experiment-specific selection remain outside this release.

## Repository map

```text
src/lockin_imaging/  numerical core, input/output, CLI, simulation, plotting
tests/              analytic truth, numerical integration, covariance, failure paths
docs/               mathematics, architecture, reproducibility and release scope
docs/assets/        generated synthetic figures and compact demonstration metrics
examples/           explicit synthetic configuration
tools/              gallery generation and publication checks
.github/workflows/  Linux/Windows test and packaging matrix
```

Start with [architecture and design decisions](docs/architecture.md), then the
[mathematical model](docs/method.md). The [project summary](docs/project-summary.md)
explains how this public implementation relates to the research workflow.

## Development

```bash
python -m pip install -r requirements/ci.txt
python -m pip install -e . --no-deps
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m build --no-isolation
python tools/check_release.py
```

The release check inspects the Git index, including hashes. After reviewing a
change to an already approved file, refresh the manifest and stage the updated
files as described in [CONTRIBUTING.md](CONTRIBUTING.md).

## Author and scope

**Minhao Liu** — PhD candidate in Chemistry & Biochemistry, Texas Tech University;
MS in Computational and Applied Mathematics, University of Chicago.

The repository highlights scientific software design, numerical signal
processing, data integrity, reproducible analysis and technical communication.
Implementation and documentation were developed with AI assistance under author
direction; see [provenance and acknowledgments](docs/provenance.md).

Source is published for inspection; no general reuse license is granted in this
release. See [RIGHTS.md](RIGHTS.md). Research data and unpublished findings are not
included.
