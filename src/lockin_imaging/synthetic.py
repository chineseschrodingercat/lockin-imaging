"""Deterministic illustrative scene. No measured images or fitted lab parameters."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .core import LockinConfig


@dataclass(frozen=True)
class SyntheticScene:
    times_s: np.ndarray
    signal: np.ndarray
    control: np.ndarray
    truth_amplitude: np.ndarray
    truth_baseline: np.ndarray
    config: LockinConfig
    seed: int
    example_yx: tuple[int, int]


def make_scene(seed: int = 20261023) -> SyntheticScene:
    """Create independent signal/control noise with a shared invented scene.

    Three spots modulate; three bright static spots contribute only fluorescence.
    The harmonic amplitude is 6% of the responsive fluorescence component, not
    6% of total intensity. White Gaussian noise is an illustrative camera model.
    """
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    rng = np.random.default_rng(seed)
    times = np.arange(512, dtype=np.float64) / 32
    yy, xx = np.mgrid[:64, :80]
    responsive = np.zeros((64, 80))
    stationary = np.zeros_like(responsive)
    for y, x, height in ((17, 19, 360), (43, 54, 290), (19, 62, 260)):
        responsive += height * np.exp(-((yy - y) ** 2 + (xx - x) ** 2) / (2 * 2.2**2))
    for y, x, height in ((44, 17, 520), (33, 36, 450), (49, 70, 380)):
        stationary += height * np.exp(-((yy - y) ** 2 + (xx - x) ** 2) / (2 * 2.5**2))
    baseline = 80 + responsive + stationary
    amplitude = 0.06 * responsive
    config = LockinConfig(frequency_hz=1.25, exposure_s=0.018, drift_degree=2)
    u = np.linspace(-1, 1, len(times))
    drift = 0.035 * u + 0.02 * (u**2 - np.mean(u**2))
    slow = baseline[None] * (1 + drift[:, None, None])
    # Explicit forward model, separate from the solver's design construction.
    angle = 2 * np.pi * config.frequency_hz * times - 0.65
    integrated = np.sinc(config.frequency_hz * config.exposure_s) * np.cos(angle)
    noise_sd = 4.5
    signal = slow + integrated[:, None, None] * amplitude + rng.normal(0, noise_sd, slow.shape)
    control = slow + rng.normal(0, noise_sd, slow.shape)
    return SyntheticScene(
        times,
        signal.astype(np.float32),
        control.astype(np.float32),
        amplitude,
        baseline,
        config,
        seed,
        (17, 19),
    )
