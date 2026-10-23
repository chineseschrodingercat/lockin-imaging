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
        "font.size": 13,
        "axes.titlesize": 16,
        "axes.labelsize": 13,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.titleweight": "bold",
        "text.color": "#111111",
        "axes.labelcolor": "#111111",
        "xtick.color": "#111111",
        "ytick.color": "#111111",
        "svg.fonttype": "none",
        "svg.hashsalt": "lockin-imaging-synthetic-v2",
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    }


def _example_series(scene) -> dict[str, np.ndarray]:
    """Use one full-record fit for the workflow and diagnostic trace panels."""
    y, x = scene.example_yx
    design, _ = _design(scene.times_s, scene.config)
    observed = np.column_stack((scene.signal[:, y, x], scene.control[:, y, x])).astype(float)
    origin = observed[0].copy()
    beta = np.linalg.lstsq(design, observed - origin, rcond=None)[0]
    beta[0] += origin
    baseline = design[:, :-2] @ beta[:-2]
    fitted = design @ beta
    mean = baseline.mean(axis=0)
    return {
        "observed": observed,
        "baseline": baseline,
        "fitted": fitted,
        "coefficients": beta,
        "relative": 100 * (observed - baseline + mean) / mean,
        "relative_fit": 100 * (fitted - baseline + mean) / mean,
    }


def _frequency_scan(scene, observed: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    frequencies = np.linspace(0.25, 3, 177)
    scans = []
    for frequency in frequencies:
        config = LockinConfig(
            frequency_hz=float(frequency),
            exposure_s=scene.config.exposure_s,
            drift_degree=scene.config.drift_degree,
        )
        scans.append(demodulate(observed, scene.times_s, config).amplitude)
    return frequencies, np.array(scans)


def _amplitude_limit(scene, signal, control) -> float:
    # One linear scale covers all three maps; no high-amplitude pixels are clipped.
    maximum = max(
        float(a.max()) for a in (scene.truth_amplitude, signal.amplitude, control.amplitude)
    )
    return max(24.0, float(np.ceil(maximum)))


def plot_scene(scene, signal, control, destination: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    with plt.rc_context(_style()):
        fig = plt.figure(figsize=(18, 10.5))
        grid = fig.add_gridspec(
            2, 3, left=0.065, right=0.955, bottom=0.09, top=0.85, wspace=0.44, hspace=0.48
        )
        axes = [fig.add_subplot(grid[i, j]) for i in range(2) for j in range(3)]
        fig.text(0.065, 0.945, "Recovering periodic fluorescence", fontsize=29, fontweight="bold")
        fig.text(
            0.955, 0.95, "SYNTHETIC", fontsize=18, ha="right", color="#006b68", fontweight="bold"
        )
        mean = scene.signal.mean(axis=0, dtype=np.float64)
        mean_limit = max(600.0, float(np.ceil(mean.max() / 100) * 100))
        mean_image = axes[0].imshow(
            mean, cmap="gray", vmin=0, vmax=mean_limit, interpolation="nearest"
        )
        axes[0].set_title("a   Mean fluorescence", loc="left")
        fig.colorbar(mean_image, ax=axes[0], fraction=0.045, pad=0.035).set_label(
            "Intensity (a.u.)"
        )
        vmax = _amplitude_limit(scene, signal, control)
        for ax, data, title in zip(
            (axes[1], axes[2], axes[3]),
            (scene.truth_amplitude, signal.amplitude, control.amplitude),
            ("b   True amplitude", "c   Recovered amplitude", "d   Zero-modulation control"),
            strict=True,
        ):
            im = ax.imshow(data, cmap="magma", vmin=0, vmax=vmax, interpolation="nearest")
            ax.set_title(title, loc="left")
            fig.colorbar(im, ax=ax, fraction=0.045, pad=0.035, ticks=[0, vmax / 2, vmax]).set_label(
                "Peak amplitude (a.u.)"
            )
        for ax in axes[:4]:
            ax.set_xlabel("x (pixels)")
            ax.set_ylabel("y (pixels)")
        y, x = scene.example_yx
        axes[2].plot(x, y, "o", markerfacecolor="none", markeredgecolor="#00e5e5", ms=11, mew=1.8)
        series = _example_series(scene)
        relative, fit = series["relative"], series["relative_fit"]
        visible = scene.times_s < 3
        axes[4].plot(
            scene.times_s[visible], relative[visible, 0], color="#0072b2", lw=1.1, label="Modulated"
        )
        axes[4].plot(
            scene.times_s[visible],
            relative[visible, 1],
            color="#007a60",
            lw=1.2,
            ls=":",
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
        axes[4].set_title("e   Drift-corrected trace", loc="left")
        axes[4].set(xlabel="Time (s)", ylabel="Baseline-normalized intensity (%)", xlim=(0, 3))
        axes[4].set_ylim(
            min(92, float(relative[visible].min()) - 1),
            max(113, float(relative[visible].max()) + 6),
        )
        axes[4].legend(fontsize=11, loc="upper center", frameon=False, ncol=2)
        frequencies, scans = _frequency_scan(scene, series["observed"])
        axes[5].plot(frequencies, scans[:, 0], color="#0072b2", label="Modulated")
        axes[5].plot(frequencies, scans[:, 1], color="#007a60", ls=":", label="Control")
        axes[5].axvline(
            scene.config.frequency_hz, color="#a45200", ls="--", lw=1.5, label="Reference"
        )
        axes[5].set_title("f   Diagnostic frequency scan", loc="left")
        axes[5].set(
            xlabel="Reference frequency (Hz)",
            ylabel="Peak amplitude (a.u.)",
            ylim=(0, max(vmax, float(scans.max()) * 1.03)),
        )
        axes[5].legend(fontsize=11, frameon=False, loc="upper right")
        for suffix in ("svg", "png"):
            fig.savefig(
                destination / f"synthetic_demo.{suffix}",
                dpi=180,
                metadata={"Description": "Entirely synthetic lock-in imaging demonstration"},
            )
        plt.close(fig)
