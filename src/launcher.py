from __future__ import annotations

import sys

from passport_auto_renamer.app import main


def _self_test() -> int:
    """Smoke-test the frozen application without opening the UI."""
    try:
        from passport_auto_renamer.ocr import PaddleOcrEngine

        PaddleOcrEngine()
        return 0
    except Exception:
        return 2


if __name__ == "__main__":
    if "--self-test" in sys.argv[1:]:
        raise SystemExit(_self_test())
    raise SystemExit(main())
