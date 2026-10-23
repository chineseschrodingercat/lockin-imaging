"""Fit a polynomial baseline and an exposure-integrated harmonic jointly.

The reference frequency is supplied by the caller. No sample labels, spatial
selection, frequency optimization, or detection thresholds enter this module.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import IntFlag
from numbers import Integral, Real

import numpy as np
from numpy.typing import ArrayLike, NDArray


class QualityFlag(IntFlag):
    """Bit flags; multiple failures may apply to one pixel."""

    OK = 0
    NONFINITE = 1
    SATURATED = 2
    NONPOSITIVE_BASELINE = 4


@dataclass(frozen=True)
class LockinConfig:
    """All timing is in seconds; frequency is in Hz.

    `exposure_s` is the rectangular integration width centered on each supplied
    timestamp. `drift_degree` controls one global polynomial for the recording.
    `saturation_level=None` disables clipping checks; it never infers bit depth.
    """

    frequency_hz: float
    exposure_s: float = 0.0
    drift_degree: int = 1
    chunk_pixels: int = 1024
    saturation_level: float | None = None
    minimum_transfer: float = 0.1

    def __post_init__(self) -> None:
        for name in ("frequency_hz", "exposure_s", "minimum_transfer"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, Real) or not np.isfinite(value):
                raise ValueError(f"{name} must be a finite number")
        if self.frequency_hz <= 0 or self.exposure_s < 0:
            raise ValueError("frequency_hz must be positive and exposure_s nonnegative")
        if not 0 < self.minimum_transfer <= 1:
            raise ValueError("minimum_transfer must be in (0, 1]")
        for name in ("drift_degree", "chunk_pixels"):
            if isinstance(getattr(self, name), bool) or not isinstance(
                getattr(self, name), Integral
            ):
                raise ValueError(f"{name} must be an integer")
        if self.drift_degree not in (0, 1, 2, 3) or self.chunk_pixels < 1:
            raise ValueError("drift_degree must be 0..3 and chunk_pixels must be positive")
        if self.saturation_level is not None:
            if (
                isinstance(self.saturation_level, bool)
                or not isinstance(self.saturation_level, Real)
                or not np.isfinite(self.saturation_level)
                or self.saturation_level <= 0
            ):
                raise ValueError("saturation_level must be finite and positive")
            object.__setattr__(self, "saturation_level", float(self.saturation_level))
        for name in ("frequency_hz", "exposure_s", "minimum_transfer"):
            object.__setattr__(self, name, float(getattr(self, name)))
        for name in ("drift_degree", "chunk_pixels"):
            object.__setattr__(self, name, int(getattr(self, name)))


@dataclass(frozen=True)
class DemodulationResult:
    """Spatial maps retain the input's trailing shape (scalar for one trace).

    I/Q covariance is conditional on independent, equal-variance temporal
    residuals and a fixed frequency; it is not an empirical detection score.
    """

    cosine: NDArray[np.float64]
    sine: NDArray[np.float64]
    amplitude: NDArray[np.float64]
    phase_rad: NDArray[np.float64]
    baseline: NDArray[np.float64]
    normalized_amplitude_percent: NDArray[np.float64]
    residual_std: NDArray[np.float64]
    iq_covariance: NDArray[np.float64]
    quality_flags: NDArray[np.uint8]
    metadata: dict

    @property
    def valid(self) -> NDArray[np.bool_]:
        return self.quality_flags == int(QualityFlag.OK)

    def arrays(self) -> dict[str, np.ndarray]:
        return {
            name: getattr(self, name) for name in self.__dataclass_fields__ if name != "metadata"
        } | {"valid": self.valid}


def _design(times: ArrayLike, config: LockinConfig) -> tuple[np.ndarray, dict]:
    t = np.asarray(times, dtype=np.float64)
    columns = config.drift_degree + 3
    if t.ndim != 1 or len(t) <= columns or not np.isfinite(t).all():
        raise ValueError("Finite 1D timestamps with positive residual degrees of freedom required")
    intervals = np.diff(t)
    dt = float(np.median(intervals))
    if dt <= 0 or not np.all(intervals > 0):
        raise ValueError("Timestamps must be strictly increasing")
    if not np.allclose(intervals, dt, rtol=1e-6, atol=dt * 1e-8):
        raise ValueError("Uniform frame-center timestamps required; gaps are not silently filled")
    if config.frequency_hz >= 0.5 / dt:
        raise ValueError("Reference frequency must be strictly below the sampling Nyquist limit")
    if config.exposure_s > dt * (1 + 1e-6):
        raise ValueError("Overlapping frame exposures are outside this public model")
    transfer = float(np.sinc(config.frequency_hz * config.exposure_s))
    if abs(transfer) < config.minimum_transfer:
        raise ValueError("Exposure transfer is too small for the requested correction")
    relative = t - t[0]
    u = 2 * relative / relative[-1] - 1
    phase = 2 * np.pi * config.frequency_hz * relative
    polynomial = np.polynomial.legendre.legvander(u, config.drift_degree)
    design = np.column_stack((polynomial, transfer * np.cos(phase), transfer * np.sin(phase)))
    return design, {
        "frames": len(t),
        "frame_interval_s": dt,
        "first_frame_center_s": float(t[0]),
        "last_frame_center_s": float(t[-1]),
        "exposure_transfer": transfer,
        "phase_origin": "first supplied frame center",
        "baseline_definition": "temporal mean of the fitted polynomial component",
    }


def demodulate(stack: ArrayLike, times_s: ArrayLike, config: LockinConfig) -> DemodulationResult:
    """Demodulate a C-contiguous (time, ...) array without a full float copy.

    Supports an individual trace, a trace matrix, or a grayscale image stack.
    Complex/object arrays and implicit color channels are rejected. Every pixel
    is fitted independently using the same design. A nonfinite or clipped sample
    excludes that pixel's entire trace, not a selectively edited set of frames.

    Phase follows y = baseline + A*cos(2*pi*f*(t-t0) - phase). Amplitude is the
    pre-exposure sinusoidal peak amplitude, not peak-to-peak or ON/OFF contrast.
    """
    values = np.asarray(stack)
    if values.ndim not in (1, 2, 3) or any(n == 0 for n in values.shape):
        raise ValueError("Expected a nonempty (time,), (time, traces), or (time, y, x) array")
    if values.dtype.kind not in "uif" or not values.flags.c_contiguous:
        raise ValueError("Real numeric, C-contiguous input required; no implicit image conversion")
    design, metadata = _design(times_s, config)
    if len(values) != len(design):
        raise ValueError("Timestamp count must match the number of frames")
    # Factor the design once; never solve normal equations or invert X.T @ X.
    left, singular, right = np.linalg.svd(design, full_matrices=False)
    tolerance = np.finfo(float).eps * max(design.shape) * singular[0]
    if singular[-1] <= tolerance or singular[0] / singular[-1] > 1e8:
        raise ValueError("Rank-deficient or ill-conditioned baseline/harmonic design")
    projector = (right.T / singular) @ left.T
    iq_gram = projector[-2:] @ projector[-2:].T
    degrees = len(design) - design.shape[1]
    shape = values.shape[1:]
    traces = values.reshape(len(values), -1)
    count = traces.shape[1]
    maps = {
        k: np.full(count, np.nan)
        for k in (
            "cosine",
            "sine",
            "amplitude",
            "phase_rad",
            "baseline",
            "normalized_amplitude_percent",
            "residual_std",
        )
    }
    covariance = np.full((2, 2, count), np.nan)
    flags = np.zeros(count, dtype=np.uint8)
    nbase = config.drift_degree + 1
    mean_polynomial = design[:, :nbase].mean(axis=0)
    for start in range(0, count, config.chunk_pixels):
        stop = min(start + config.chunk_pixels, count)
        chunk = np.array(traces[:, start:stop], dtype=np.float64, copy=True)
        bad = ~np.isfinite(chunk).all(axis=0)
        flags[start:stop] |= bad.astype(np.uint8) * int(QualityFlag.NONFINITE)
        if config.saturation_level is not None:
            clipped = np.any(chunk >= config.saturation_level, axis=0)
            flags[start:stop] |= clipped.astype(np.uint8) * int(QualityFlag.SATURATED)
        good = flags[start:stop] == 0
        if not good.any():
            continue
        selected = chunk[:, good]
        # Center large camera offsets before projection; restore only baseline.
        origin = selected[0].copy()
        selected -= origin
        beta = projector @ selected
        residual = selected - design @ beta
        variance = np.sum(residual**2, axis=0) / degrees
        baseline = mean_polynomial @ beta[:nbase] + origin
        cosine, sine = beta[-2:]
        amplitude = np.hypot(cosine, sine)
        idx = start + np.flatnonzero(good)
        nonpositive = baseline <= 0
        flags[idx[nonpositive]] |= int(QualityFlag.NONPOSITIVE_BASELINE)
        normalized = np.full(len(idx), np.nan)
        np.divide(100 * amplitude, baseline, out=normalized, where=~nonpositive)
        for name, data in {
            "cosine": cosine,
            "sine": sine,
            "amplitude": amplitude,
            "phase_rad": np.arctan2(sine, cosine),
            "baseline": baseline,
            "normalized_amplitude_percent": normalized,
            "residual_std": np.sqrt(variance),
        }.items():
            maps[name][idx] = data
        covariance[:, :, idx] = iq_gram[:, :, None] * variance
    metadata.update(
        {
            "configuration": asdict(config),
            "spatial_shape": list(shape),
            "input_dtype": str(values.dtype),
            "design_rank": design.shape[1],
            "design_condition_number": float(singular[0] / singular[-1]),
            "residual_degrees_of_freedom": degrees,
            "valid_pixels": int(np.count_nonzero(flags == 0)),
            "total_pixels": count,
            "quality_flag_counts": {
                flag.name.lower(): int(np.count_nonzero(flags & int(flag))) for flag in QualityFlag
            },
            "covariance_assumption": "independent equal-variance temporal residuals; fixed frequency",
            "amplitude_definition": "exposure-corrected sinusoidal peak amplitude",
            "normalized_amplitude_definition": "100 * amplitude / fitted mean baseline",
        }
    )
    return DemodulationResult(
        **{k: v.reshape(shape) for k, v in maps.items()},
        iq_covariance=covariance.reshape((2, 2) + shape),
        quality_flags=flags.reshape(shape),
        metadata=metadata,
    )
