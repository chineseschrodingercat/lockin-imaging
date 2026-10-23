"""Scientific contracts: signed recovery, integration, chunking and covariance."""

from dataclasses import replace

import numpy as np
import pytest

from lockin_imaging import LockinConfig, QualityFlag, demodulate


@pytest.mark.parametrize("phase", [-2.7, -0.6, 0, 0.8, 2.9])
@pytest.mark.parametrize("degree", [0, 1, 2, 3])
@pytest.mark.parametrize("exposure", [0.0, 0.023])
def test_known_signed_harmonic_with_joint_drift(phase, degree, exposure):
    t = np.arange(323) / 30
    f, amplitude = 1.37, 7.3
    u = np.linspace(-1, 1, len(t))
    baseline = np.full_like(u, 430) + sum(2.7 * u**power for power in range(1, degree + 1))
    trace = baseline + amplitude * np.sinc(f * exposure) * np.cos(2 * np.pi * f * t - phase)
    result = demodulate(trace, t, LockinConfig(f, exposure, degree))
    np.testing.assert_allclose(result.cosine, amplitude * np.cos(phase), atol=1e-11)
    np.testing.assert_allclose(result.sine, amplitude * np.sin(phase), atol=1e-11)
    np.testing.assert_allclose(result.amplitude, amplitude, atol=1e-11)
    np.testing.assert_allclose(result.baseline, baseline.mean(), atol=1e-11)
    np.testing.assert_allclose(
        result.normalized_amplitude_percent, 100 * amplitude / baseline.mean(), atol=1e-11
    )


def test_exposure_correction_against_independent_numerical_integral():
    t = np.arange(128) / 16
    exposure, frequency, amplitude = 0.055, 5.3, 19.2
    offsets = np.linspace(-exposure / 2, exposure / 2, 4001)
    samples = 700 + amplitude * np.cos(2 * np.pi * frequency * (t[:, None] + offsets))
    integrated = np.trapezoid(samples, offsets, axis=1) / exposure
    corrected = demodulate(integrated, t, LockinConfig(frequency, exposure))
    uncorrected = demodulate(integrated, t, LockinConfig(frequency, 0))
    assert abs(float(corrected.amplitude) - amplitude) < 1e-6
    assert float(uncorrected.amplitude) < amplitude * 0.9


def test_chunked_memmap_preserves_unsigned_input(tmp_path):
    rng = np.random.default_rng(98)
    data = rng.integers(1000, 5000, size=(141, 7, 9), dtype=np.uint16)
    path = tmp_path / "stack.npy"
    np.save(path, data)
    raw = np.load(path, mmap_mode="r")
    t = np.arange(len(raw)) / 31
    config = LockinConfig(1.1, chunk_pixels=5)
    small = demodulate(raw, t, config)
    large = demodulate(data, t, replace(config, chunk_pixels=1000))
    for name, array in small.arrays().items():
        np.testing.assert_allclose(array, large.arrays()[name], atol=1e-11)
    np.testing.assert_array_equal(raw, data)
    assert raw.dtype == np.uint16


def test_pixel_local_exclusions_do_not_contaminate_neighbors():
    t = np.arange(100) / 20
    trace = 100 + 3 * np.cos(2 * np.pi * t)
    data = np.column_stack([trace] * 5)
    data[8, 1] = np.nan
    data[9, 2] = 4095
    data[:, 3] -= 200
    data[2, 4], data[3, 4] = np.inf, 4095
    result = demodulate(data, t, LockinConfig(1, saturation_level=4095))
    np.testing.assert_array_equal(result.quality_flags, [0, 1, 2, 4, 3])
    assert result.metadata["valid_pixels"] == 1
    np.testing.assert_allclose(result.amplitude[0], 3, atol=1e-12)
    assert np.isnan(result.amplitude[[1, 2, 4]]).all()
    assert np.isfinite(result.amplitude[3])
    assert np.isnan(result.normalized_amplitude_percent[3])
    assert result.quality_flags[4] & QualityFlag.NONFINITE


def test_iq_covariance_matches_repeated_white_noise_simulations():
    rng = np.random.default_rng(137)
    t = np.arange(256) / 32
    data = 100 + rng.normal(0, 4, size=(256, 900))
    result = demodulate(data, t, LockinConfig(1.25, drift_degree=1, chunk_pixels=71))
    empirical = np.cov(np.vstack([result.cosine, result.sine]), ddof=1)
    predicted = result.iq_covariance.mean(axis=-1)
    np.testing.assert_allclose(np.diag(empirical), np.diag(predicted), rtol=0.12)
    assert abs(empirical[0, 1] - predicted[0, 1]) < 0.02
    # A zero true amplitude still has a positive estimated magnitude (noise bias).
    assert np.median(result.amplitude) > 0


def test_phase_is_relative_to_first_supplied_frame_center():
    t = np.arange(90) / 30
    trace = 100 + 4 * np.sin(2 * np.pi * 1.2 * t)
    a = demodulate(trace, t, LockinConfig(1.2))
    b = demodulate(trace, t + 100, LockinConfig(1.2))
    np.testing.assert_allclose(a.cosine, b.cosine, atol=1e-10)
    np.testing.assert_allclose(a.sine, b.sine, atol=1e-10)


@pytest.mark.parametrize(
    "times",
    [
        np.array([0.0, 1.0, 1.0, 2.0, 3.0, 4.0]),
        np.arange(10, 0, -1, dtype=float),
        np.array([0.0, 1.0, 2.0, 4.0, 5.0, 6.0]),
        np.array([0.0, 1.0, 2.0, np.nan, 4.0, 5.0]),
    ],
)
def test_bad_timing_rejected(times):
    with pytest.raises(ValueError):
        demodulate(np.ones(len(times)), times, LockinConfig(0.1))


@pytest.mark.parametrize(
    "kwargs",
    [
        {"frequency_hz": 0},
        {"frequency_hz": np.nan},
        {"frequency_hz": True},
        {"frequency_hz": 1, "exposure_s": -1},
        {"frequency_hz": 1, "drift_degree": 2.5},
        {"frequency_hz": 1, "chunk_pixels": 0},
        {"frequency_hz": 1, "chunk_pixels": True},
        {"frequency_hz": 1, "minimum_transfer": 0},
        {"frequency_hz": 1, "saturation_level": float("inf")},
    ],
)
def test_invalid_config(kwargs):
    with pytest.raises(ValueError):
        LockinConfig(**kwargs)


def test_aliasing_overlapping_exposures_and_unstable_design_rejected():
    t = np.arange(100) / 20
    y = np.ones(100)
    for config in (
        LockinConfig(10),
        LockinConfig(1, exposure_s=0.1),
        LockinConfig(1e-10),
        LockinConfig(8, exposure_s=0.05, minimum_transfer=0.99),
    ):
        with pytest.raises(ValueError):
            demodulate(y, t, config)


@pytest.mark.parametrize(
    "data",
    [
        np.ones((10, 2, 3, 3)),
        np.ones((10, 0)),
        np.ones(10, dtype=complex),
        np.ones(10, dtype=object),
        np.ones((10, 5))[:, ::2],
        np.ones(10, dtype=bool),
    ],
)
def test_no_implicit_shape_or_dtype_conversion(data):
    with pytest.raises(ValueError):
        demodulate(data, np.arange(10) / 20, LockinConfig(1))


def test_no_hidden_frame_removal_or_insufficient_dof():
    with pytest.raises(ValueError):
        demodulate(np.ones(6), np.arange(7), LockinConfig(0.1))
    with pytest.raises(ValueError):
        demodulate(np.ones(4), np.arange(4), LockinConfig(0.1))
