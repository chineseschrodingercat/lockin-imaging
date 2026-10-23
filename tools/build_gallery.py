"""Build a synthetic-only gallery into a NEW directory."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from lockin_imaging import demodulate
from lockin_imaging.io import write_json
from lockin_imaging.plotting import _style, plot_scene, synthetic_metrics
from lockin_imaging.synthetic import make_scene


def draw_workflow(output: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch

    ink, muted, teal, amber = "#142f43", "#40596b", "#006b68", "#a45200"
    with plt.rc_context(_style()):
        fig = plt.figure(figsize=(16, 6.8))
        canvas = fig.add_axes((0, 0, 1, 1))
        canvas.set(xlim=(0, 1), ylim=(0, 1))
        canvas.axis("off")
        fig.text(0.05, 0.91, "LOCK-IN IMAGING", color=teal, fontsize=12, fontweight="bold")
        fig.text(
            0.05,
            0.81,
            "From noisy frames to periodic signal.",
            fontsize=32,
            color=ink,
            fontweight="bold",
        )
        fig.text(
            0.05,
            0.75,
            "A reproducible software companion for fluorescence imaging",
            fontsize=14,
            color=muted,
        )
        fig.text(
            0.95, 0.91, "PUBLIC EDITION  /  SYNTHETIC ONLY", fontsize=10, ha="right", color=muted
        )
        columns = (0.05, 0.295, 0.54, 0.785)
        labels = (
            ("01", "EXPLICIT INPUT", "Image stack + frame times"),
            ("02", "JOINT MODEL", "Drift + exposure-aware harmonic"),
            ("03", "QUADRATURE", "I/Q coefficients for each pixel"),
            ("04", "AUDITABLE OUTPUT", "Amplitude, phase and quality"),
        )
        for x, (number, title, subtitle) in zip(columns, labels, strict=True):
            fig.text(x, 0.64, number, color=teal, fontsize=12, fontweight="bold")
            fig.text(x, 0.59, title, color=ink, fontsize=12, fontweight="bold")
            fig.text(x, 0.54, subtitle, color=muted, fontsize=10)
        rng = np.random.default_rng(7)
        t = np.linspace(0, 1, 120)
        ax = fig.add_axes((0.05, 0.30, 0.18, 0.19))
        raw = 0.7 * np.cos(2 * np.pi * 3 * t) + rng.normal(0, 0.45, len(t)) + 0.5 * t
        ax.plot(t, raw, color="#0072b2", lw=1.1)
        ax.set(xlim=(0, 1), ylim=(-2.1, 2.1))
        ax.axis("off")
        fig.text(0.05, 0.27, "Noisy intensity at one location", fontsize=10, color=muted)
        ax = fig.add_axes((0.295, 0.30, 0.18, 0.19))
        ax.plot(t, 0.65 * np.cos(2 * np.pi * 3 * t) + 0.5 * t, color=teal, lw=2)
        ax.plot(t, 0.5 * t, color=amber, lw=1.5, ls="--")
        ax.set(xlim=(0, 1), ylim=(-2.1, 2.1))
        ax.axis("off")
        fig.text(0.295, 0.27, "One shared design; no phase search", fontsize=10, color=muted)
        ax = fig.add_axes((0.54, 0.30, 0.18, 0.19))
        ax.axhline(0, color="#c5ced5", lw=1)
        ax.plot(t, np.cos(2 * np.pi * 3 * t), color=teal, lw=2)
        ax.plot(t, np.sin(2 * np.pi * 3 * t), color=amber, lw=1.5, ls="--")
        ax.set(xlim=(0, 1), ylim=(-1.3, 1.3))
        ax.axis("off")
        fig.text(0.54, 0.27, "Cosine I      Sine Q", fontsize=10, color=muted)
        ax = fig.add_axes((0.79, 0.31, 0.155, 0.19))
        yy, xx = np.mgrid[:36, :48]
        values = np.zeros_like(xx, dtype=float)
        for y, x, amplitude in ((10, 11, 1), (25, 31, 0.8), (9, 37, 0.65)):
            values += amplitude * np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / 8)
        ax.imshow(values, cmap="magma", interpolation="nearest", vmin=0, vmax=1)
        ax.axis("off")
        fig.text(0.785, 0.27, "Schematic map; no measured pixels", fontsize=10, color=muted)
        for left in (0.248, 0.493, 0.738):
            canvas.add_patch(
                FancyArrowPatch(
                    (left, 0.41),
                    (left + 0.03, 0.41),
                    arrowstyle="-|>",
                    mutation_scale=18,
                    linewidth=1.5,
                    color=muted,
                )
            )
        canvas.plot([0.05, 0.95], [0.20, 0.20], color="#d9e1e7", lw=1)
        fig.text(0.05, 0.13, r"$A=\sqrt{I^2+Q^2}$", fontsize=22, color=ink)
        fig.text(0.275, 0.135, "Finite-exposure correction", fontsize=11, color=teal)
        fig.text(0.52, 0.135, "Bounded pixel chunks", fontsize=11, color=teal)
        fig.text(0.755, 0.135, "Hash-checked run records", fontsize=11, color=teal)
        fig.text(
            0.05,
            0.052,
            "General-purpose numerical core. Research data and unpublished findings stay outside this repository.",
            fontsize=11,
            color=muted,
        )
        for extension in ("png", "svg"):
            fig.savefig(
                output / f"workflow.{extension}",
                dpi=160,
                metadata={"Description": "Schematic workflow; no experimental data"},
            )
        plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    scene = make_scene()
    signal = demodulate(scene.signal, scene.times_s, scene.config)
    control = demodulate(scene.control, scene.times_s, scene.config)
    plot_scene(scene, signal, control, args.output)
    draw_workflow(args.output)
    # Matplotlib emits trailing blanks inside SVG path attributes. Normalize the
    # text serialization only; coordinates, image bytes and styling are unchanged.
    for path in args.output.glob("*.svg"):
        text = path.read_text(encoding="utf-8")
        path.write_text(
            "\n".join(line.rstrip() for line in text.splitlines()) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    write_json(args.output / "synthetic_metrics.json", synthetic_metrics(scene, signal, control))
    print("Synthetic gallery generated.")


if __name__ == "__main__":
    main()
