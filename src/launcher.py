from __future__ import annotations

import os
import sys
import tempfile
import traceback
from pathlib import Path

from passport_auto_renamer.app import main


def _self_test_log_path() -> Path:
    configured = os.environ.get("PASSPORT_SELF_TEST_LOG")
    if configured:
        return Path(configured)
    return Path(tempfile.gettempdir()) / "PassportAutoRenamer-self-test.log"


def _write_self_test_log(text: str) -> None:
    path = _self_test_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _self_test() -> int:
    """Smoke-test the frozen application without opening the UI."""
    try:
        import paddle  # noqa: F401
        import paddleocr  # noqa: F401
        import paddlex  # noqa: F401
        from passport_auto_renamer.ocr import PaddleOcrEngine

        PaddleOcrEngine()
        _write_self_test_log("OK\n")
        return 0
    except Exception:
        _write_self_test_log(traceback.format_exc())
        return 2


if __name__ == "__main__":
    if "--self-test" in sys.argv[1:]:
        raise SystemExit(_self_test())
    raise SystemExit(main())
