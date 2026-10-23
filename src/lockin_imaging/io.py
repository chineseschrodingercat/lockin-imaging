"""Explicit, non-overwriting run outputs with content hashes."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path

import numpy as np

from . import __version__
from .core import DemodulationResult


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for part in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(part)
    return digest.hexdigest()


def write_json(path: Path, data: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def begin_run(directory: Path, kind: str) -> Path:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    write_json(
        directory / "run.json",
        {"schema": "lockin-imaging.run.v1", "kind": kind, "complete": False, "status": "running"},
    )
    return directory


def save_result(directory: Path, result: DemodulationResult, name: str = "maps") -> None:
    np.savez_compressed(directory / f"{name}.npz", **result.arrays())
    write_json(directory / f"{name}.json", result.metadata)


def finish_run(directory: Path, kind: str, details: dict) -> dict:
    files = {
        p.name: sha256_file(p)
        for p in sorted(directory.iterdir())
        if p.is_file() and p.name != "run.json"
    }
    receipt = {
        "schema": "lockin-imaging.run.v1",
        "kind": kind,
        "complete": True,
        "status": "complete",
        "package_version": __version__,
        "python": platform.python_version(),
        "platform": platform.system(),
        "numpy": importlib.metadata.version("numpy"),
        "details": details,
        "sha256": files,
    }
    write_json(directory / "run.json", receipt)
    return receipt
