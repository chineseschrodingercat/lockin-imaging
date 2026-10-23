# Lock-in imaging

**Exposure-aware I/Q demodulation for fluorescence image stacks, with independent numerical checks and reproducible run records.**

[![CI](https://github.com/chineseschrodingercat/lockin-imaging/actions/workflows/ci.yml/badge.svg)](https://github.com/chineseschrodingercat/lockin-imaging/actions/workflows/ci.yml)
![Python 3.11–3.13](https://img.shields.io/badge/python-3.11%E2%80%933.13-3776AB)
![Evidence: synthetic](https://img.shields.io/badge/evidence-synthetic_only-006b68)

**Minhao Liu — project lead and author.** I develop computational workflows for
periodic fluorescence imaging. This repository connects a measurement model to
a tested numerical estimator, a reusable Python API and an auditable analysis
workflow.

The problem is to estimate a periodic fluorescence component when ordinary
brightness, slow drift and camera exposure also affect the observations.
This public companion demonstrates my work in **lock-in algorithm formulation,
numerical validation and scientific software engineering** using established
signal-processing and least-squares methods.

**Evidence scope:** all fluorescence images, traces and recovery metrics shown
here come from synthetic inputs. They demonstrate software behavior under stated
assumptions, not measured instrument sensitivity or experimental detection
accuracy. This is a reduced companion to ongoing research; experimental data,
unpublished outcomes and experiment-specific decision rules are excluded.

## My contributions

**Lock-in formulation and numerical solution.** Formulated a per-pixel model
that fits polynomial drift and signed cosine/sine coefficients jointly at a
supplied reference frequency. Incorporated rectangular-exposure integration into
the design matrix and specified the phase, peak-amplitude and normalization
conventions. The implementation factors the shared design once with SVD, checks
rank and conditioning, and estimates each pixel independently. Joint fitting
addresses the finite-record bias that can arise from detrending only the
observations before demodulation.
[Inspect the estimator](src/lockin_imaging/core.py) and
[the derivation](docs/appendix-mathematics.md).

**Numerical validation with independent constructions.** Built checks that go
beyond whether the code runs: analytic injected signals, a separate numerical
exposure integral, QR-based partial regression, and repeated noise simulations.
The tests examine signed I/Q recovery, covariance under its stated assumptions,
positive magnitude bias under a null signal, and finite-record frequency
response. Additional checks tie the plotted trace and frequency scan back to
the actual image estimates.
[Inspect the core tests](tests/test_core.py),
[mathematical checks](tests/test_mathematics.py) and
[figure-consistency tests](tests/test_figures.py).

**Engineering implementation and reproducibility.** Separated the NumPy
estimator from file handling, the CLI, simulation and plotting. Implemented
read-only memory-mapped input and bounded pixel chunks; explicit timing,
shape and pixel-quality checks; input/output hashes; failed-run records; and
refusal to overwrite an existing run. Packaged the code with pinned validation
dependencies, wheel-installation checks, Linux/Windows CI and an explicit
public-file release gate.
[Inspect the architecture](docs/architecture.md),
[CLI](src/lockin_imaging/cli.py), [I/O](src/lockin_imaging/io.py) and
[CI workflow](.github/workflows/ci.yml).

I lead the scientific problem framing and technical direction. The public
implementation, tests and documentation were developed with AI assistance under
my direction; [provenance](docs/provenance.md) records that development process.

![Synthetic workflow: the same pixel's observed trace and joint fit lead to a fitted I/Q vector and the full amplitude map.](docs/assets/workflow.svg)

**Figure 1. A consistent synthetic workflow.** The input trace, joint fit and
I/Q vector correspond to the fixed pixel marked by the cyan ring in the amplitude
map. All 512 frames are fitted; the trace panels display the first 3 s. The vector
length is exposure-corrected sinusoidal peak amplitude, and its angle follows
`A cos[2πf(t−t₀)−φ]`. [Full figure legend and settings](docs/figure-legends.md#figure-1-from-a-recorded-trace-to-a-pixelwise-amplitude-map).

## Verification evidence

The [v0.2.0 release](https://github.com/chineseschrodingercat/lockin-imaging/releases/tag/v0.2.0)
passed **87 tests** on Linux and Windows with Python 3.11 and 3.13;
[the recorded CI run](https://github.com/chineseschrodingercat/lockin-imaging/actions/runs/39929469064)
also includes synthetic replay, figure rendering, package construction and
installed-wheel execution. The badge above reports the current branch status.

| Question a reviewer can check | Evidence in the repository |
|---|---|
| Does the estimator recover the specified signed signal? | 40 noiseless phase/drift/exposure combinations and an independently integrated exposure model in [test_core.py](tests/test_core.py) |
| Are the mathematical assumptions exercised independently? | QR residualization, a counterexample to one-sided detrending, noise-magnitude moments and off-frequency response in [test_mathematics.py](tests/test_mathematics.py) |
| Do failures and input changes remain visible? | Pixel exclusions, unsigned-input/chunk agreement, configuration-change detection, incomplete receipts and overwrite rejection in [core](tests/test_core.py) and [CLI tests](tests/test_cli.py) |
| Can the public artifact be reproduced and inspected? | Pinned dependencies, content hashes, a staged-file allowlist, numerical replay and installation checks in [the reproduction guide](docs/reproducing.md) and [release gate](tools/check_release.py) |

These checks establish behavior on known inputs. The synthetic image's error
metrics are not an experimental benchmark.

The estimator makes deliberate choices: one fixed frequency, one polynomial
baseline and one I/Q pair per pixel over the full recording. It requires uniform
frame-center timing and a stationary grayscale input. Reported I/Q covariance
assumes independent, equal-variance temporal errors. Motion correction,
time-varying phase, calibrated detection thresholds and experimental inference
are outside this public implementation. [Method and limits](docs/method.md).

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
`run.json` record with output hashes. Use a new output directory for each run.
No dataset download or credential is required.
[Reproduction instructions](docs/reproducing.md) include exact dependency pins
and the local-input workflow.

![Synthetic results: bright static and modulating spots appear together in mean fluorescence; recovered lock-in amplitude follows the known modulating spots, while a separate zero-modulation control retains a small positive noise floor. A single-pixel trace and diagnostic frequency scan show the supplied reference.](docs/assets/synthetic_demo.png)

**Figure 2. Synthetic truth, recovery and control.** (a) Mean intensity of three
modulating and three static sources. (b–d) Injected, recovered and control peak
amplitudes on one linear 0–24 a.u. scale. The control has independent Gaussian
noise and no injected modulation; its positive magnitude floor is retained.
(e) The predetermined pixel's drift-corrected signal and control, displayed as
`100 × (intensity − fitted drift + mean baseline) / mean baseline`.
(f) A diagnostic scan that refits the full trace at each reference frequency;
the image estimator itself uses the supplied 1.25 Hz reference.

The demonstration uses 512 frames at 32 frames/s, 18 ms rectangular exposure,
quadratic drift and seed `20261023`. All frames are fitted; panel e shows frame
centers in `[0, 3)` s. No detection threshold, per-image amplitude rescaling or
spatial smoothing is applied. [The full legend](docs/figure-legends.md#figure-2-synthetic-truth-recovery-and-a-zero-modulation-control)
defines all panels, timing, noise, normalization and display limits;
[exact synthetic metrics](docs/assets/synthetic_metrics.json) describe this one
realization. These are software examples, not measured experimental performance.

## Python API

```python
import numpy as np
from lockin_imaging import LockinConfig, demodulate

times = np.arange(512) / 32.0  # frame-center seconds
trace = 100.0 + 4.0 * np.cos(2 * np.pi * 1.25 * times - 0.3)
result = demodulate(trace, times, LockinConfig(frequency_hz=1.25, exposure_s=0.0))
print(float(result.amplitude))  # approximately 4.0
print(float(result.phase_rad))  # approximately 0.3
```

The same API accepts `(frames, traces)` or `(frames, height, width)` arrays.
It does not infer timing, color channels, bit depth or object identity.
Array preparation is explicit; [the method](docs/method.md) defines the input
contract and every output quantity.

## Technical documentation

| Start here | What it covers |
|---|---|
| [Foundations](docs/foundations.md) | What a lock-in image measures and how to interpret controls |
| [Method](docs/method.md) and [mathematical appendix](docs/appendix-mathematics.md) | Exposure integration, joint regression, SVD, covariance, magnitude bias, waveform contrast and finite-record response |
| [Architecture](docs/architecture.md) | Dependency boundaries, working-memory scaling and implementation tradeoffs |
| [Figure legends](docs/figure-legends.md) and [references](docs/references.md) | Complete display definitions and supporting primary sources |
| [Review notes](docs/review-notes.md) and [project summary](docs/project-summary.md) | Corrections, verification scope and the relationship to the broader research workflow |

Source modules live in `src/lockin_imaging/`; tests in `tests/`; gallery
generation and publication checks in `tools/`.

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
change, refresh the manifest and stage the approved files as described in
[CONTRIBUTING.md](CONTRIBUTING.md).

## Author and availability

**Minhao Liu** — PhD candidate in Chemistry & Biochemistry, Texas Tech University;
MS in Computational and Applied Mathematics, University of Chicago.

Source is available for inspection under [RIGHTS.md](RIGHTS.md); this release
does not grant a general reuse license. The [release boundary](docs/release-boundary.md)
describes the public file set. Experimental data and unpublished findings remain
outside this repository.
