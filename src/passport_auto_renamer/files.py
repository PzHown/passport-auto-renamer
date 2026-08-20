from __future__ import annotations

import re
import shutil
from pathlib import Path

WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip().rstrip(".")
    name = re.sub(r"\s+", " ", name)
    if not name:
        name = "未识别"
    if name.upper() in WINDOWS_RESERVED:
        name = f"_{name}"
    return name[:180]


def unique_destination(directory: Path, stem: str, suffix: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    candidate = directory / f"{stem}{suffix}"
    index = 2
    while candidate.exists():
        candidate = directory / f"{stem} ({index}){suffix}"
        index += 1
    return candidate


def transfer_file(source: Path, destination: Path, mode: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if mode == "move":
        shutil.move(str(source), str(destination))
    else:
        shutil.copy2(source, destination)
