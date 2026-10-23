"""Scientific semantics of the plotted arrays, not a pixel-perfect style snapshot."""

import numpy as np
import pytest

from lockin_imaging import demodulate
from lockin_imaging.plotting import _amplitude_limit, _example_series, _frequency_scan
from lockin_imaging.synthetic import make_scene


@pytest.fixture(scope="module")
def gallery():
    scene = make_scene()
    signal = demodulate(scene.signal, scene.times_s, scene.config)
    control = demodulate(scene.control, scene.times_s, scene.config)
    return scene, signal, control


def test_example_coefficients_and_normalization_match_the_map(gallery):
    scene, signal, control = gallery
    series = _example_series(scene)
    y, x = scene.example_yx
    beta = series["coefficients"]
    mean = series["baseline"].mean(axis=0)
    for index, result in enumerate((signal, control)):
        np.testing.assert_allclose(
            beta[-2:, index], [result.cosine[y, x], result.sine[y, x]], atol=1e-11
        )
        np.testing.assert_allclose(mean[index], result.baseline[y, x], atol=1e-11)
    reconstructed = series["relative"] * mean / 100 + series["baseline"] - mean
    np.testing.assert_allclose(reconstructed, series["observed"], atol=1e-12)
    h = np.sinc(scene.config.frequency_hz * scene.config.exposure_s)
    angle = 2 * np.pi * scene.config.frequency_hz * scene.times_s
    predicted = 100 * (
        1
        + h
        * (signal.cosine[y, x] * np.cos(angle) + signal.sine[y, x] * np.sin(angle))
        / signal.baseline[y, x]
    )
    np.testing.assert_allclose(series["relative_fit"][:, 0], predicted, atol=1e-11)


def test_scan_reference_and_shared_map_scale_do_not_change_results(gallery):
    scene, signal, control = gallery
    series = _example_series(scene)
    frequencies, scans = _frequency_scan(scene, series["observed"])
    matched = np.flatnonzero(frequencies == scene.config.frequency_hz)
    assert len(matched) == 1
    y, x = scene.example_yx
    np.testing.assert_allclose(
        scans[matched[0]], [signal.amplitude[y, x], control.amplitude[y, x]], atol=1e-11
    )
    limit = _amplitude_limit(scene, signal, control)
    assert limit == 24
    for data in (scene.truth_amplitude, signal.amplitude, control.amplitude):
        assert np.all((data >= 0) & (data <= limit))
    assert np.all(control.amplitude > 0)  # No null magnitudes have been zeroed.
    visible = scene.times_s < 3
    assert np.count_nonzero(visible) == 96
    assert scene.times_s[visible][-1] == 2.96875
