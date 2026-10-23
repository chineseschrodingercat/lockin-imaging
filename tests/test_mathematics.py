"""Independent constructions for the identities stated in the public appendix."""

import numpy as np
import pytest

from lockin_imaging import LockinConfig, demodulate


def test_partial_regression_identity_and_one_sided_detrending_failure():
    t = np.arange(71) * 0.07
    u = np.linspace(-1, 1, len(t))
    drift = np.column_stack([np.ones(len(t)), u, u**2])
    harmonic = np.column_stack([np.cos(2 * np.pi * 0.41 * t), np.sin(2 * np.pi * 0.41 * t)])
    truth = np.array([3.2, -1.4])
    y = drift @ np.array([120, 7, 3]) + harmonic @ truth
    # An independent QR projection, using ordinary powers rather than Legendre columns.
    q, _ = np.linalg.qr(drift)
    residual_y = y - q @ (q.T @ y)
    residual_h = harmonic - q @ (q.T @ harmonic)
    partial = np.linalg.lstsq(residual_h, residual_y, rcond=None)[0]
    naive = np.linalg.lstsq(harmonic, residual_y, rcond=None)[0]
    joint = demodulate(y, t, LockinConfig(0.41, drift_degree=2))
    np.testing.assert_allclose(partial, truth, atol=1e-12)
    np.testing.assert_allclose([joint.cosine, joint.sine], truth, atol=1e-12)
    bias = -np.linalg.solve(harmonic.T @ harmonic, harmonic.T @ q @ q.T @ harmonic @ truth)
    np.testing.assert_allclose(naive - truth, bias, atol=1e-12)
    assert np.linalg.norm(naive - truth) > 0.05


def test_isotropic_null_magnitude_moments_from_independent_noise():
    rng = np.random.default_rng(752)
    n, sigma = 64, 2.4
    t = np.arange(n) / 32
    config = LockinConfig(3, exposure_s=0.02, drift_degree=0, chunk_pixels=377)
    traces = 100 + rng.normal(0, sigma, size=(n, 9000))
    result = demodulate(traces, t, config)
    s = np.sqrt(2 / n) * sigma / np.sinc(config.frequency_hz * config.exposure_s)
    # Integer cycles + constant baseline make the two errors exactly isotropic.
    np.testing.assert_allclose(np.mean(result.amplitude), s * np.sqrt(np.pi / 2), rtol=0.03)
    np.testing.assert_allclose(np.median(result.amplitude), s * np.sqrt(2 * np.log(2)), rtol=0.03)
    np.testing.assert_allclose(np.mean(result.amplitude**2), 2 * s**2, rtol=0.04)
    np.testing.assert_allclose(result.iq_covariance[0, 0], result.iq_covariance[1, 1], rtol=1e-12)


@pytest.mark.parametrize("duty", [0.2, 0.5, 0.8])
def test_rectangular_wave_fundamental_and_contrast_against_quadrature(duty):
    high, delta = 1200.0, 180.0
    period = 0.8
    # Integrate just the low-state interval; the high constant has zero coefficient.
    low_times = np.linspace(0, duty * period, 20001)
    coefficient = (
        -delta / period * np.trapezoid(np.exp(-2j * np.pi * low_times / period), low_times)
    )
    numerical_amplitude = 2 * abs(coefficient)
    expected_amplitude = 2 * delta * np.sin(np.pi * duty) / np.pi
    np.testing.assert_allclose(numerical_amplitude, expected_amplitude, rtol=1e-8)
    fraction = numerical_amplitude / (high - duty * delta)
    recovered_contrast = np.pi * fraction / (2 * np.sin(np.pi * duty) + np.pi * duty * fraction)
    np.testing.assert_allclose(recovered_contrast, delta / high, rtol=1e-8)


@pytest.mark.parametrize("offset", [0.0, 0.03, -0.14, 1.5])
def test_finite_window_response_matches_complex_geometric_sum(offset):
    n, dt = 117, 0.07
    direct = np.exp(2j * np.pi * offset * np.arange(n) * dt).mean()
    derived = (
        np.exp(1j * np.pi * offset * (n - 1) * dt) * np.sinc(n * offset * dt) / np.sinc(offset * dt)
    )
    np.testing.assert_allclose(direct, derived, atol=1e-14)


def test_real_signal_frequency_response_includes_both_frequency_branches():
    n, dt, f0, f, phase, amplitude, exposure = 117, 0.07, 1.31, 1.17, 0.63, 4.2, 0.06
    t = np.arange(n) * dt
    h0, h = np.sinc(f0 * exposure), np.sinc(f * exposure)
    y = amplitude * h0 * np.cos(2 * np.pi * f0 * t - phase)
    actual = 2 / (n * h) * np.sum(y * np.exp(-2j * np.pi * f * t))

    def window(offset):
        return (
            np.exp(1j * np.pi * offset * (n - 1) * dt)
            * np.sinc(n * offset * dt)
            / np.sinc(offset * dt)
        )

    expected = (
        amplitude
        * h0
        / h
        * (np.exp(-1j * phase) * window(f0 - f) + np.exp(1j * phase) * window(-f0 - f))
    )
    np.testing.assert_allclose(actual, expected, atol=1e-13)


def test_exact_off_frequency_response_with_joint_baseline_projection():
    t = np.arange(113) / 20
    u = np.linspace(-1, 1, len(t))
    d = np.column_stack([np.ones(len(t)), u, u**2])
    q, _ = np.linalg.qr(d)
    f0, f, exposure = 1.21, 1.26, 0.035

    def harmonic(frequency):
        return np.sinc(frequency * exposure) * np.column_stack(
            [np.cos(2 * np.pi * frequency * t), np.sin(2 * np.pi * frequency * t)]
        )

    h0, hf = harmonic(f0), harmonic(f)
    truth = np.array([4, -2])
    y = d @ np.array([150, 6, 2]) + h0 @ truth
    residual_h = hf - q @ (q.T @ hf)
    residual_h0 = h0 - q @ (q.T @ h0)
    response = np.linalg.solve(residual_h.T @ residual_h, residual_h.T @ residual_h0) @ truth
    result = demodulate(y, t, LockinConfig(f, exposure, drift_degree=2))
    np.testing.assert_allclose([result.cosine, result.sine], response, atol=1e-12)
