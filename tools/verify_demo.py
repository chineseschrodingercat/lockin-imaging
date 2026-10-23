"""Check run hashes and replay numerical metrics against the public reference."""

import json
import sys
from pathlib import Path

import numpy as np

from lockin_imaging.io import sha256_file


def main() -> None:
    run = Path(sys.argv[1])
    receipt = json.loads((run / "run.json").read_text(encoding="utf-8"))
    if not receipt["complete"] or not receipt["details"]["synthetic_only"]:
        raise ValueError("A completed synthetic demo is required")
    for name, expected in receipt["sha256"].items():
        if sha256_file(run / name) != expected:
            raise ValueError(f"Output hash mismatch: {name}")
    reference = json.loads(
        (Path(__file__).resolve().parents[1] / "docs/assets/synthetic_metrics.json").read_text(
            encoding="utf-8"
        )
    )
    observed = receipt["details"]["metrics"]
    for key, value in reference.items():
        if isinstance(value, float):
            np.testing.assert_allclose(observed[key], value, rtol=1e-7, atol=1e-9)
        elif observed[key] != value:
            raise ValueError(f"Synthetic metadata mismatch: {key}")
    print("Demo hashes and synthetic metrics verified.")


if __name__ == "__main__":
    main()
