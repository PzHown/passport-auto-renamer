from __future__ import annotations

import importlib.metadata
import os
import subprocess
import sys
from pathlib import Path

import paddlex


ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "src" / "launcher.py"
MODELS = ROOT / "bundled_models"


def _installed_distributions() -> dict[str, str]:
    installed: dict[str, str] = {}
    for dist in importlib.metadata.distributions():
        name = dist.metadata.get("Name")
        if name:
            installed[name.lower()] = name
    return installed


def main() -> int:
    if not ENTRY.is_file():
        raise FileNotFoundError(f"PyInstaller entry not found: {ENTRY}")
    if not MODELS.is_dir():
        raise FileNotFoundError(f"Bundled OCR models not found: {MODELS}")

    installed = _installed_distributions()
    paddlex_dep_names = {
        str(name).lower() for name in paddlex.utils.deps.BASE_DEP_SPECS.keys()
    }

    # PaddleOCR's official PyInstaller guide recommends collecting PaddleX data,
    # Paddle binaries, and distribution metadata for installed PaddleX dependencies.
    metadata_names = {
        canonical
        for lower_name, canonical in installed.items()
        if lower_name in paddlex_dep_names
    }

    # Keep metadata for the three core distributions as well. Some code paths use
    # importlib.metadata at runtime to detect versions/capabilities.
    for name in ("paddleocr", "paddlex", "paddlepaddle"):
        if name in installed:
            metadata_names.add(installed[name])

    add_data = f"{MODELS}{os.pathsep}models"
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--onedir",
        "--name",
        "PassportAutoRenamer",
        "--paths",
        str(ROOT / "src"),
        "--add-data",
        add_data,
        "--collect-data",
        "paddlex",
        "--collect-binaries",
        "paddle",
    ]

    for name in sorted(metadata_names, key=str.lower):
        cmd.extend(["--copy-metadata", name])

    cmd.append(str(ENTRY))

    print("PyInstaller command:")
    print(" ".join(f'\"{part}\"' if " " in part else part for part in cmd))
    print(f"Copying metadata for {len(metadata_names)} distributions")

    subprocess.run(cmd, cwd=ROOT, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
