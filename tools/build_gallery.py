"""Build a synthetic-only gallery into a NEW directory."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from lockin_imaging import demodulate
from lockin_imaging.io import write_json
from lockin_imaging.plotting import _example_series, _style, plot_scene, synthetic_metrics
from lockin_imaging.synthetic import make_scene


def draw_workflow(output: Path, scene, signal) -> None:
    """Every curve, phasor and map comes from the same synthetic recording."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Arc, FancyArrowPatch

    ink, teal, amber, blue = "#111111", "#006b68", "#a45200", "#0072b2"
    series = _example_series(scene)
    y, x = scene.example_yx
    cosine, sine = float(signal.cosine[y, x]), float(signal.sine[y, x])
    phase = float(signal.phase_rad[y, x])
    visible = scene.times_s < 3
    t = scene.times_s[visible]
    with plt.rc_context(_style()):
        fig = plt.figure(figsize=(18, 6.8))
        canvas = fig.add_axes((0, 0, 1, 1))
        canvas.set(xlim=(0, 1), ylim=(0, 1))
        canvas.axis("off")
        fig.text(0.055, 0.89, "Lock-in imaging", fontsize=32, fontweight="bold")
        fig.text(0.95, 0.90, "SYNTHETIC", fontsize=18, ha="right", color=teal, fontweight="bold")
        columns = (0.055, 0.30, 0.545, 0.79)
        labels = ("01  Input trace", "02  Joint fit", "03  Quadrature", "04  Amplitude map")
        for left, title in zip(columns, labels, strict=True):
            fig.text(left, 0.75, title, fontsize=18, fontweight="bold")

        axes = [fig.add_axes((left, 0.30, 0.16, 0.32)) for left in columns]
        axes[0].plot(t, series["observed"][visible, 0], color=blue, lw=1.3)
        axes[1].plot(t, series["fitted"][visible, 0], color=blue, lw=2, label="Joint fit")
        axes[1].plot(
            t, series["baseline"][visible, 0], color=amber, ls="--", lw=2, label="Baseline"
        )
        low = float(series["observed"][visible, 0].min()) - 4
        high = float(series["observed"][visible, 0].max()) + 4
        for ax in axes[:2]:
            ax.set(xlim=(0, 3), ylim=(low, high), xlabel="Time (s)", ylabel="Intensity (a.u.)")
            ax.set_xticks([0, 1, 2, 3])
        axes[1].legend(
            loc="lower center", bbox_to_anchor=(0.5, 1.02), frameon=False, fontsize=12, ncol=2
        )

        ax = axes[2]
        bound = max(25.0, float(np.ceil(max(cosine, sine) + 2)))
        ax.set(
            xlim=(-2, bound), ylim=(-2, bound), xlabel="I (a.u.)", ylabel="Q (a.u.)", aspect="equal"
        )
        ax.set_xticks([0, 10, 20])
        ax.set_yticks([0, 10, 20])
        ax.plot([0, cosine, cosine], [sine, sine, 0], color=teal, ls=":", lw=1.5)
        ax.add_patch(
            FancyArrowPatch(
                (0, 0), (cosine, sine), arrowstyle="-|>", mutation_scale=20, color=blue, lw=2
            )
        )
        ax.add_patch(Arc((0, 0), 13, 13, theta1=0, theta2=np.degrees(phase), color=amber, lw=2))
        ax.text(7.2, 1.8, r"$\phi$", fontsize=20, color=amber)
        ax.text(cosine / 2 - 3, sine / 2 + 3, r"$A$", fontsize=20, color=blue)

        ax = axes[3]
        vmax = max(24.0, float(np.ceil(signal.amplitude.max())))
        im = ax.imshow(signal.amplitude, cmap="magma", vmin=0, vmax=vmax, interpolation="nearest")
        ax.plot(x, y, "o", markerfacecolor="none", markeredgecolor="#00e5e5", ms=9, mew=1.5)
        ax.set(xlabel="x (pixels)", ylabel="y (pixels)")
        ax.set_xticks([0, 40, 79])
        ax.set_yticks([0, 30, 63])
        fig.colorbar(im, ax=ax, fraction=0.048, pad=0.04, ticks=[0, vmax / 2, vmax]).set_label(
            "Peak amplitude (a.u.)"
        )
        for left in (0.235, 0.48, 0.725):
            canvas.add_patch(
                FancyArrowPatch(
                    (left, 0.46),
                    (left + 0.018, 0.46),
                    arrowstyle="-|>",
                    mutation_scale=22,
                    linewidth=1.8,
                    color=ink,
                )
            )
        fig.text(0.30, 0.10, r"$A=\sqrt{I^2+Q^2}$", fontsize=23)
        fig.text(0.60, 0.10, r"$\phi=\mathrm{atan2}(Q,I)$", fontsize=23)
        for extension in ("png", "svg"):
            fig.savefig(
                output / f"workflow.{extension}",
                dpi=180,
                metadata={
                    "Description": "One synthetic recording and its fitted workflow; no experimental data"
                },
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
    draw_workflow(args.output, scene, signal)
    # Normalize text serialization only; coordinates and image bytes are unchanged.
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
