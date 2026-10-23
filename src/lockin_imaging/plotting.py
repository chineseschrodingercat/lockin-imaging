"""Reproducible synthetic figures; plotting is an optional dependency."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .core import LockinConfig, _design, demodulate


def synthetic_metrics(scene, signal, control) -> dict:
    error = signal.amplitude - scene.truth_amplitude
    y, x = scene.example_yx
    return {
        "evidence": "synthetic software demonstration; not experimental validation",
        "seed": scene.seed,
        "frames": len(scene.times_s),
        "image_shape": list(scene.truth_amplitude.shape),
        "amplitude_rmse_all_pixels_au": float(np.sqrt(np.mean(error**2))),
        "control_amplitude_median_au": float(np.median(control.amplitude)),
        "control_amplitude_p95_au": float(np.percentile(control.amplitude, 95)),
        "example_pixel_yx": [y, x],
        "example_true_amplitude_au": float(scene.truth_amplitude[y, x]),
        "example_recovered_amplitude_au": float(signal.amplitude[y, x]),
        "normalization": "100 * exposure-corrected sinusoidal peak amplitude / fitted mean baseline",
        "detection_threshold_applied": False,
    }


def _style():
    return {
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.labelsize": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.titleweight": "bold",
        "text.color": "#142f43",
        "axes.labelcolor": "#142f43",
        "xtick.color": "#40596b",
        "ytick.color": "#40596b",
        "svg.fonttype": "none",
        "svg.hashsalt": "lockin-imaging-synthetic-v1",
        "figure.facecolor": "#fbfcfe",
        "axes.facecolor": "#fbfcfe",
    }


def plot_scene(scene, signal, control, destination: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    with plt.rc_context(_style()):
        fig = plt.figure(figsize=(16, 9))
        grid = fig.add_gridspec(
            2, 3, left=0.055, right=0.94, bottom=0.16, top=0.83, wspace=0.3, hspace=0.42
        )
        axes = [fig.add_subplot(grid[i, j]) for i in range(2) for j in range(3)]
        fig.text(
            0.055, 0.95, "A bright image is not a modulation map.", fontsize=27, fontweight="bold"
        )
        fig.text(
            0.055,
            0.902,
            "Known synthetic truth  /  independent control noise  /  one fixed reference frequency",
            fontsize=12,
            color="#40596b",
        )
        fig.text(
            0.94,
            0.955,
            "SYNTHETIC ONLY",
            fontsize=11,
            ha="right",
            color="#006b68",
            fontweight="bold",
        )
        mean = scene.signal.mean(axis=0)
        axes[0].imshow(mean, cmap="gray", vmin=0, vmax=float(np.max(mean)), interpolation="nearest")
        axes[0].set_title("a   Mean fluorescence", loc="left")
        vmax = float(scene.truth_amplitude.max() * 1.08)
        for ax, data, title in zip(
            (axes[1], axes[2], axes[3]),
            (scene.truth_amplitude, signal.amplitude, control.amplitude),
            (
                "b   True harmonic amplitude",
                "c   Recovered harmonic amplitude",
                "d   Zero-modulation control",
            ),
            strict=True,
        ):
            im = ax.imshow(data, cmap="magma", vmin=0, vmax=vmax, interpolation="nearest")
            ax.set_title(title, loc="left")
        for ax in axes[:4]:
            ax.set_xlabel("x (pixels)")
            ax.set_ylabel("y (pixels)")
        cb_ax = fig.add_axes((0.955, 0.58, 0.011, 0.21))
        fig.colorbar(im, cax=cb_ax, label="Peak amplitude (a.u.); shared b–d")
        y, x = scene.example_yx
        axes[2].plot(x, y, "o", markerfacecolor="none", markeredgecolor="cyan", ms=10, mew=1.5)
        design, _ = _design(scene.times_s, scene.config)
        traces = np.column_stack((scene.signal[:, y, x], scene.control[:, y, x]))
        beta = np.linalg.lstsq(design, traces, rcond=None)[0]
        polynomial = design[:, :-2] @ beta[:-2]
        baseline = polynomial.mean(axis=0)
        relative = 100 * (traces - polynomial + baseline) / baseline
        fit = 100 * (design @ beta - polynomial + baseline) / baseline
        visible = scene.times_s < 3
        axes[4].plot(
            scene.times_s[visible],
            relative[visible, 0],
            color="#0072b2",
            lw=1,
            alpha=0.7,
            label="Modulated",
        )
        axes[4].plot(
            scene.times_s[visible],
            relative[visible, 1],
            color="#6b7280",
            lw=1,
            alpha=0.7,
            label="Control",
        )
        axes[4].plot(
            scene.times_s[visible],
            fit[visible, 0],
            color="#a45200",
            ls="--",
            lw=2,
            label="Harmonic fit",
        )
        axes[4].set(
            title="e   One fixed pixel; drift removed",
            xlabel="Time (s)",
            ylabel="Fluorescence / fitted mean (%)",
        )
        axes[4].set_ylim(92, 111)
        axes[4].legend(fontsize=7, loc="upper center", ncol=3, frameon=False)
        frequencies = np.linspace(0.25, 3, 177)
        scans = []
        for frequency in frequencies:
            config = LockinConfig(
                frequency_hz=float(frequency),
                exposure_s=scene.config.exposure_s,
                drift_degree=scene.config.drift_degree,
            )
            scans.append(demodulate(np.ascontiguousarray(traces), scene.times_s, config).amplitude)
        scans = np.array(scans)
        axes[5].plot(frequencies, scans[:, 0], color="#0072b2", label="Modulated")
        axes[5].plot(frequencies, scans[:, 1], color="#6b7280", ls=":", label="Control")
        axes[5].axvline(
            scene.config.frequency_hz, color="#a45200", ls="--", lw=1, label="Supplied reference"
        )
        axes[5].set(
            title="f   Diagnostic frequency scan",
            xlabel="Reference frequency (Hz)",
            ylabel="Peak amplitude (a.u.)",
            ylim=(0, vmax),
        )
        axes[5].legend(fontsize=8, frameon=False, loc="upper right")
        fig.text(
            0.055,
            0.047,
            f"512 frames · 32 frames/s · 18 ms exposure · 1.25 Hz reference · seed {scene.seed}\n"
            "Full 16 s recording fitted. Panel e shows 3 s. No detection threshold or per-image amplitude rescaling.",
            fontsize=10,
            color="#40596b",
        )
        for suffix in ("svg", "png"):
            fig.savefig(
                destination / f"synthetic_demo.{suffix}",
                dpi=180,
                metadata={"Description": "Entirely synthetic lock-in imaging demonstration"}
                if suffix == "svg"
                else {"Description": "Entirely synthetic demonstration"},
            )
        plt.close(fig)
