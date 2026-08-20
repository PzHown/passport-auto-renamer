from __future__ import annotations

import os
import sys
import tempfile
import traceback
from pathlib import Path

# Disable PaddleX/Paddle oneDNN (MKLDNN) before importing the application/Paddle
# stack. This avoids CPU runtime failures seen on some Windows systems.
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


def _load_font(size: int):
    from PIL import ImageFont

    candidates = [
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\msyhbd.ttc",
        r"C:\Windows\Fonts\simsun.ttc",
        r"C:\Windows\Fonts\arial.ttf",
    ]
    for font_path in candidates:
        try:
            return ImageFont.truetype(font_path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _create_mock_image(path: Path) -> None:
    """Create a synthetic Chinese/English passport-like image for CI OCR testing."""
    from PIL import Image, ImageDraw

    image = Image.new("RGB", (1400, 900), "white")
    draw = ImageDraw.Draw(image)
    title_font = _load_font(54)
    body_font = _load_font(64)
    mrz_font = _load_font(42)

    draw.text((80, 80), "护照 OCR MOCK 测试", fill="black", font=title_font)
    draw.text((80, 210), "姓名：张三", fill="black", font=body_font)
    draw.text((80, 340), "NAME: ZHANG SAN", fill="black", font=body_font)
    draw.text((80, 520), "P<CHNZHANG<<SAN<<<<<<<<<<<<<<<<<<<<", fill="black", font=mrz_font)
    draw.text((80, 610), "E123456789CHN9001011M3001012<<<<<<<<<<<<<<02", fill="black", font=mrz_font)
    image.save(path, format="PNG")


def _self_test() -> int:
    """Exercise packaged imports, local models, and one real OCR inference."""
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

        if not items:
            raise RuntimeError("Mock OCR inference returned no recognized text.")

        recognized = " | ".join(item.text for item in items)
        if "ZHANG" not in recognized.upper():
            raise RuntimeError(f"Mock OCR did not recognize expected English name: {recognized}")
        if "张三" not in recognized.replace(" ", ""):
            raise RuntimeError(f"Mock OCR did not recognize expected Chinese name: {recognized}")

        _write_self_test_log(
            f"OK - Chinese/English mock OCR inference completed, items={len(items)}\n"
            f"recognized={recognized}\n"
        )
        return 0
    except Exception:
        _write_self_test_log(traceback.format_exc())
        return 2


if __name__ == "__main__":
    if "--self-test" in sys.argv[1:]:
        raise SystemExit(_self_test())
    raise SystemExit(main())
