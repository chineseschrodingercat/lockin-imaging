"""Small command-line interface with explicit input and output contracts."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np

from . import __version__
from .core import LockinConfig, demodulate
from .io import begin_run, finish_run, save_result, sha256_file, write_json


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Exposure-aware lock-in imaging")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    demo = commands.add_parser("demo", help="Generate and demodulate a synthetic image stack")
    demo.add_argument("--output", type=Path, required=True, help="New output directory")
    demo.add_argument("--seed", type=int, default=20261023)
    demo.add_argument("--no-figures", action="store_true")
    analyze = commands.add_parser("analyze", help="Analyze a local grayscale .npy stack")
    analyze.add_argument("--stack", type=Path, required=True)
    analyze.add_argument("--times", type=Path, required=True, help="1D frame-center seconds (.npy)")
    analyze.add_argument("--config", type=Path, required=True, help="Explicit LockinConfig JSON")
    analyze.add_argument("--output", type=Path, required=True, help="New output directory")
    return parser


def _demo(args: argparse.Namespace) -> dict:
    from .synthetic import make_scene

    scene = make_scene(args.seed)
    signal = demodulate(scene.signal, scene.times_s, scene.config)
    control = demodulate(scene.control, scene.times_s, scene.config)
    save_result(args.output, signal, "signal")
    save_result(args.output, control, "control")
    np.save(args.output / "synthetic_signal.npy", scene.signal, allow_pickle=False)
    np.save(args.output / "synthetic_control.npy", scene.control, allow_pickle=False)
    np.save(args.output / "times.npy", scene.times_s, allow_pickle=False)
    write_json(args.output / "config.json", asdict(scene.config))
    from .plotting import synthetic_metrics

    metrics = synthetic_metrics(scene, signal, control)
    write_json(args.output / "synthetic_metrics.json", metrics)
    if not args.no_figures:
        from .plotting import plot_scene

        plot_scene(scene, signal, control, args.output)
    return {
        "synthetic_only": True,
        "seed": args.seed,
        "configuration": asdict(scene.config),
        "metrics": metrics,
    }


def _analyze(args: argparse.Namespace) -> dict:
    before = {
        key: sha256_file(path)
        for key, path in (("stack", args.stack), ("times", args.times), ("config", args.config))
    }
    config = LockinConfig(**json.loads(args.config.read_text(encoding="utf-8")))
    stack = np.load(args.stack, mmap_mode="r", allow_pickle=False)
    times = np.load(args.times, allow_pickle=False)
    if stack.ndim != 3:
        raise ValueError("CLI input must be a grayscale (frames, height, width) stack")
    result = demodulate(stack, times, config)
    after = {
        key: sha256_file(path)
        for key, path in (("stack", args.stack), ("times", args.times), ("config", args.config))
    }
    if before != after:
        raise ValueError("Input changed during analysis")
    save_result(args.output, result)
    return {
        "synthetic_only": False,
        "input_sha256": before,
        "configuration": asdict(config),
        "valid_pixels": result.metadata["valid_pixels"],
    }


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    started = False
    try:
        begin_run(args.output, args.command)
        started = True
        details = _demo(args) if args.command == "demo" else _analyze(args)
        receipt = finish_run(args.output, args.command, details)
    except (OSError, ValueError, TypeError, ImportError, np.linalg.LinAlgError) as error:
        if started:
            write_json(
                args.output / "run.json",
                {
                    "schema": "lockin-imaging.run.v1",
                    "complete": False,
                    "status": "failed",
                    "kind": args.command,
                    "error_type": type(error).__name__,
                },
            )
        print(f"lockin-imaging: {error}", file=sys.stderr)
        return 2
    print(json.dumps({"status": receipt["status"], "output": str(args.output)}, indent=2))
    return 0
