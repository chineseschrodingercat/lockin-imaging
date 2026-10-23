"""Verify the staged public tree. This is a backstop, not a confidentiality proof."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path, PurePosixPath

TEXT_SUFFIXES = {".py", ".md", ".json", ".txt", ".toml", ".yml", ".cff", ".svg"}
TEXT_NAMES = {".gitignore", ".gitattributes", "MANIFEST.in"}
PATTERNS = {
    "credential": re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "workstation path": re.compile(r"(?<![A-Za-z])(?:[A-Za-z]:[\\/]|/(?:Users|home)/[^/\s]+/)"),
}


def inspect_text(name: str, text: str) -> list[str]:
    return [
        f"{name}: {label} pattern" for label, pattern in PATTERNS.items() if pattern.search(text)
    ]


def git(root: Path, *args: str) -> bytes:
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True).stdout


def check(root: Path) -> dict:
    entries = git(root, "ls-files", "--stage", "-z").decode("utf-8").split("\0")
    paths = []
    failures = []
    for entry in filter(None, entries):
        metadata, name = entry.split("\t", 1)
        mode, _, stage = metadata.split()
        paths.append(name)
        if mode != "100644" or stage != "0":
            failures.append(f"Unapproved mode or conflict stage: {name}")

    def read(name):
        return git(root, "show", f":{name}")

    approved = json.loads(read("PUBLIC_FILES.json"))["files"]
    staged_list = read("PUBLIC_FILES.txt").decode("utf-8").splitlines()
    if approved != sorted(set(approved)) or approved != staged_list:
        failures.append("Allowlists do not match, or contain duplicate/unsorted paths")
    if set(paths) != set(approved):
        failures.append(f"Unexpected files: {sorted(set(paths) - set(approved))}")
        failures.append(f"Missing files: {sorted(set(approved) - set(paths))}")
    manifest = json.loads(read("RELEASE_MANIFEST.json"))
    expected_hashes = manifest["files"]
    if set(expected_hashes) != set(approved) - {"RELEASE_MANIFEST.json"}:
        failures.append("Manifest membership differs from the approved set")
    total = 0
    for name in paths:
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts:
            failures.append(f"Unsafe path: {name}")
        data = read(name)
        total += len(data)
        if len(data) > 3_000_000:
            failures.append(f"File exceeds this release's size budget: {name}")
        if name != "RELEASE_MANIFEST.json":
            if hashlib.sha256(data).hexdigest() != expected_hashes.get(name):
                failures.append(f"Staged hash mismatch: {name}")
        if path.suffix == ".png" and name.startswith("docs/assets/"):
            if not data.startswith(b"\x89PNG\r\n\x1a\n"):
                failures.append(f"Invalid PNG signature: {name}")
        elif path.suffix in TEXT_SUFFIXES or name in TEXT_NAMES:
            try:
                failures.extend(inspect_text(name, data.decode("utf-8")))
            except UnicodeDecodeError:
                failures.append(f"Non-UTF8 content: {name}")
        else:
            failures.append(f"Unapproved file type: {name}")
    return {
        "passed": not failures,
        "tracked_files": len(paths),
        "bytes": total,
        "failures": failures,
        "scope": "Git index paths, hashes, file types and text patterns",
    }


def main() -> None:
    report = check(Path(__file__).resolve().parents[1])
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
