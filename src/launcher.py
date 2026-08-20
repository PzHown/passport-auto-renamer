from __future__ import annotations

import os
import sys
import tempfile
import traceback
from pathlib import Path

# Set this before importing the application/Paddle stack so oneDNN/MKLDNN is
# disabled consistently in the packaged Windows executable.
os.environ.setdefault("PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT", "0")

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


def _create_mock_image(path: Path) -> None:
    """Create a local synthetic image so CI exercises real OCR inference."""
    from PIL import Image, ImageDraw, ImageFont

    image = Image.new("RGB", (1200, 700), "white")
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("arial.ttf", 64)
    except OSError:
        font = ImageFont.load_default()

    draw.text((80, 120), "PASSPORT MOCK TEST", fill="black", font=font)
    draw.text((80, 260), "NAME: ZHANG SAN", fill="black", font=font)
    draw.text((80, 400), "P<CHNZHANG<<SAN<<<<<<<<<<<<<<<<<<<<", fill="black", font=font)
    image.save(path, format="PNG")


def _self_test() -> int:
    """Smoke-test packaged imports, OCR initialization, and one real mock-image inference."""
    try:
        import paddle  # noqa: F401
        import paddleocr  # noqa: F401
        import paddlex  # noqa: F401
        from passport_auto_renamer.ocr import PaddleOcrEngine

        engine = PaddleOcrEngine()
        with tempfile.TemporaryDirectory(prefix="passport-auto-renamer-") as tmp_dir:
            mock_path = Path(tmp_dir) / "mock-passport.png"
            _create_mock_image(mock_path)
            items = engine.recognize(mock_path)

        _write_self_test_log(f"OK - mock OCR inference completed, items={len(items)}\n")
        return 0
    except Exception:
        _write_self_test_log(traceback.format_exc())
        return 2


if __name__ == "__main__":
    if "--self-test" in sys.argv[1:]:
        raise SystemExit(_self_test())
    raise SystemExit(main())
