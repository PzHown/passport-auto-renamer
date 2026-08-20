from __future__ import annotations

import logging
import sys

from .config import config_path, load_config
from .ui import ProcessingWindow, SettingsWindow


def _setup_logging() -> None:
    path = config_path().parent / "passport-auto-renamer.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=path,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        encoding="utf-8",
    )


def process_files(paths: list[str]) -> int:
    _setup_logging()
    cfg = load_config()
    return ProcessingWindow(paths, cfg).run()


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        SettingsWindow().run()
        return 0
    return process_files(args)
