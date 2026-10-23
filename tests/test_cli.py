import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from lockin_imaging import LockinConfig, demodulate
from lockin_imaging.cli import main
from lockin_imaging.io import sha256_file
from lockin_imaging.synthetic import make_scene


def test_analyze_roundtrip_provenance_and_no_overwrite(tmp_path):
    t = np.arange(100) / 20
    raw = np.ascontiguousarray(
        np.broadcast_to((100 + 5 * np.cos(2 * np.pi * t))[:, None, None], (100, 3, 4))
    )
    stack = tmp_path / "input.npy"
    times = tmp_path / "times.npy"
    config = tmp_path / "config.json"
    np.save(stack, raw)
    np.save(times, t)
    config.write_text(json.dumps(asdict(LockinConfig(1))), encoding="utf-8")
    before = sha256_file(stack)
    out = tmp_path / "result"
    args = [
        "analyze",
        "--stack",
        str(stack),
        "--times",
        str(times),
        "--config",
        str(config),
        "--output",
        str(out),
    ]
    assert main(args) == 0
    receipt = json.loads((out / "run.json").read_text())
    assert receipt["complete"] and receipt["details"]["input_sha256"]["stack"] == before
    assert sha256_file(stack) == before
    for filename, expected in receipt["sha256"].items():
        assert sha256_file(out / filename) == expected
    with np.load(out / "maps.npz", allow_pickle=False) as saved:
        np.testing.assert_allclose(saved["amplitude"], 5, atol=1e-10)
    original_receipt = (out / "run.json").read_bytes()
    assert main(args) == 2
    assert (out / "run.json").read_bytes() == original_receipt


def test_failed_run_has_incomplete_receipt(tmp_path):
    out = tmp_path / "failed"
    assert (
        main(
            [
                "analyze",
                "--stack",
                str(tmp_path / "missing.npy"),
                "--times",
                "missing.npy",
                "--config",
                "missing.json",
                "--output",
                str(out),
            ]
        )
        == 2
    )
    receipt = json.loads((out / "run.json").read_text())
    assert receipt["status"] == "failed" and not receipt["complete"]
    assert "missing.json" not in (out / "run.json").read_text()


def test_synthetic_scene_is_deterministic_and_control_is_independent():
    a, b = make_scene(12), make_scene(12)
    np.testing.assert_array_equal(a.signal, b.signal)
    np.testing.assert_array_equal(a.control, b.control)
    assert not np.array_equal(a.signal, a.control)
    result = demodulate(a.signal, a.times_s, a.config)
    error = np.sqrt(np.mean((result.amplitude - a.truth_amplitude) ** 2))
    assert error < 0.5


def test_demo_headless_command(tmp_path):
    out = tmp_path / "demo"
    assert main(["demo", "--output", str(out), "--no-figures"]) == 0
    receipt = json.loads((out / "run.json").read_text())
    assert receipt["details"]["synthetic_only"] is True
    assert receipt["details"]["metrics"]["detection_threshold_applied"] is False


def test_configuration_change_during_read_is_detected(tmp_path, monkeypatch):
    times, stack, config = (tmp_path / name for name in ("times.npy", "input.npy", "config.json"))
    t = np.arange(100) / 20
    np.save(times, t)
    np.save(stack, (100 + np.cos(2 * np.pi * t))[:, None, None])
    config.write_text(json.dumps(asdict(LockinConfig(1))), encoding="utf-8")
    read_text = Path.read_text

    def read_then_change(path, *args, **kwargs):
        text = read_text(path, *args, **kwargs)
        if path == config:
            path.write_text(json.dumps(asdict(LockinConfig(2))), encoding="utf-8")
        return text

    monkeypatch.setattr(Path, "read_text", read_then_change)
    out = tmp_path / "changed-config"
    assert (
        main(
            [
                "analyze",
                "--stack",
                str(stack),
                "--times",
                str(times),
                "--config",
                str(config),
                "--output",
                str(out),
            ]
        )
        == 2
    )
    receipt = json.loads((out / "run.json").read_text())
    assert receipt["status"] == "failed"
    assert not (out / "maps.npz").exists()
