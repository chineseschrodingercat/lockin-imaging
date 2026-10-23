"""The publication check must inspect index bytes, not only local files."""

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path


def load_checker():
    path = Path(__file__).resolve().parents[1] / "tools/check_release.py"
    spec = importlib.util.spec_from_file_location("check_release", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_public_tree(root):
    names = ["PUBLIC_FILES.json", "PUBLIC_FILES.txt", "README.md", "RELEASE_MANIFEST.json"]
    (root / "README.md").write_text("Synthetic demonstration only.\n", encoding="utf-8")
    (root / "PUBLIC_FILES.json").write_text(json.dumps({"files": names}), encoding="utf-8")
    (root / "PUBLIC_FILES.txt").write_text("\n".join(names) + "\n", encoding="utf-8")
    hashes = {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest()
        for name in names
        if name != "RELEASE_MANIFEST.json"
    }
    (root / "RELEASE_MANIFEST.json").write_text(json.dumps({"files": hashes}), encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "config", "core.autocrlf", "false"], check=True)
    subprocess.run(["git", "-C", str(root), "add", *names], check=True)


def test_clean_tree_passes_and_unapproved_file_fails(tmp_path):
    checker = load_checker()
    make_public_tree(tmp_path)
    assert checker.check(tmp_path)["passed"]
    (tmp_path / "unreviewed.csv").write_text("result,value\nexample,1\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "unreviewed.csv"], check=True)
    assert not checker.check(tmp_path)["passed"]


def test_staged_bytes_take_precedence_over_worktree(tmp_path):
    checker = load_checker()
    make_public_tree(tmp_path)
    (tmp_path / "README.md").write_text("Changed in index\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "README.md"], check=True)
    (tmp_path / "README.md").write_text("Synthetic demonstration only.\n", encoding="utf-8")
    report = checker.check(tmp_path)
    assert not report["passed"]
    assert any("hash mismatch" in message for message in report["failures"])


def test_text_screening_uses_synthetic_secret_patterns():
    checker = load_checker()
    fake_credential = "gh" + "p_" + "x" * 36
    assert checker.inspect_text("sample.md", fake_credential)
    machine_path = "C" + ":" + "/" + "local/project/file"
    assert checker.inspect_text("sample.md", machine_path)
    assert not checker.inspect_text("sample.md", "https://example.org/project")
