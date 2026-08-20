from __future__ import annotations

import logging
import sys
from pathlib import Path
from tkinter import messagebox

from .config import config_path, load_config
from .processor import PassportProcessor
from .ui import SettingsWindow


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

    try:
        processor = PassportProcessor(cfg)
    except Exception as exc:
        messagebox.showerror("OCR 初始化失败", str(exc))
        return 2

    success = 0
    failed = 0
    lines: list[str] = []

    for raw in paths:
        result = processor.process(Path(raw))
        if result.success:
            success += 1
            lines.append(f"✓ {result.source.name} -> {result.destination.name if result.destination else ''}")
        else:
            failed += 1
            lines.append(f"✗ {result.source.name}: {result.message}")

    summary = f"处理完成：成功 {success} 个，失败 {failed} 个。"
    detail = "\n".join(lines[:20])
    if len(lines) > 20:
        detail += f"\n... 另有 {len(lines) - 20} 个文件"
    messagebox.showinfo("护照自动命名", summary + ("\n\n" + detail if detail else ""))
    return 0 if failed == 0 else 1


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        SettingsWindow().run()
        return 0
    return process_files(args)
