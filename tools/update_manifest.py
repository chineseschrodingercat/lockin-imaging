"""Hash only the existing, explicitly approved public file list."""

import hashlib
import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    paths = json.loads((root / "PUBLIC_FILES.json").read_text(encoding="utf-8"))["files"]
    stage_list = (root / "PUBLIC_FILES.txt").read_text(encoding="utf-8").splitlines()
    if paths != sorted(set(paths)) or paths != stage_list:
        raise ValueError("The JSON and staging allowlists must match, sorted without duplicates")
    files = {}
    for name in paths:
        if name == "RELEASE_MANIFEST.json":
            continue
        path = root / name
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root):
            raise ValueError(f"Unsafe or missing approved path: {name}")
        data = path.read_bytes()
        # Match .gitattributes' canonical Git bytes on Windows and Unix.
        if path.suffix != ".png":
            data = data.replace(b"\r\n", b"\n")
        files[name] = hashlib.sha256(data).hexdigest()
    (root / "RELEASE_MANIFEST.json").write_text(
        json.dumps(
            {
                "schema": "lockin-imaging.public-release.v1",
                "files": files,
                "self_hash_excluded": "RELEASE_MANIFEST.json",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Hashed {len(files)} explicitly approved files.")


if __name__ == "__main__":
    main()
