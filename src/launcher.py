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


def _load_font(size: int, *, mono: bool = False):
    from PIL import ImageFont

    candidates = (
        [r"C:\Windows\Fonts\consola.ttf", r"C:\Windows\Fonts\cour.ttf"]
        if mono
        else [
            r"C:\Windows\Fonts\msyh.ttc",
            r"C:\Windows\Fonts\msyhbd.ttc",
            r"C:\Windows\Fonts\simsun.ttc",
            r"C:\Windows\Fonts\arial.ttf",
        ]
    )
    for font_path in candidates:
        try:
            return ImageFont.truetype(font_path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _draw_security_pattern(draw, box: tuple[int, int, int, int], *, step: int = 34) -> None:
    """Draw light synthetic security-style lines without reproducing a real passport design."""
    x1, y1, x2, y2 = box
    for offset in range(-400, (x2 - x1) + 400, step):
        draw.line(
            [(x1 + offset, y1), (x1 + offset + 360, y2)],
            fill=(238, 218, 222),
            width=1,
        )
    for y in range(y1 + 20, y2, 42):
        draw.arc((x1 + 40, y - 22, x2 - 40, y + 22), 0, 180, fill=(221, 231, 215), width=1)


def _draw_placeholder_portrait(draw, box: tuple[int, int, int, int]) -> None:
    """Draw an obviously synthetic portrait placeholder for the CI mock."""
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius=16, fill=(174, 210, 230), outline=(125, 165, 185), width=2)
    cx = (x1 + x2) // 2
    head_r = max(24, (x2 - x1) // 7)
    head_y = y1 + (y2 - y1) // 3
    draw.ellipse((cx - head_r, head_y - head_r, cx + head_r, head_y + head_r), fill=(238, 208, 184))
    draw.pieslice((x1 + 34, y1 + (y2 - y1) // 2, x2 - 34, y2 + 90), 180, 360, fill=(105, 125, 150))
    draw.text((x1 + 24, y2 - 52), "MOCK", fill=(60, 80, 100), font=_load_font(24))


def _create_mock_image(path: Path) -> None:
    """Create a synthetic scan shaped like an open passport booklet for CI OCR testing."""
    from PIL import Image, ImageDraw

    # A scanner-like white canvas with the booklet centered and a lot of white margin,
    # matching the shape of typical office MFP scans without copying any real document.
    image = Image.new("RGB", (1800, 2400), (252, 253, 252))
    draw = ImageDraw.Draw(image)

    for y in range(120, 2280, 190):
        draw.line((40, y, 1760, y), fill=(245, 247, 246), width=2)

    px, py, pw = 310, 350, 1180
    top_h, data_h = 650, 900
    top_box = (px, py, px + pw, py + top_h)
    data_box = (px, py + top_h, px + pw, py + top_h + data_h)

    draw.rounded_rectangle(top_box, radius=24, fill=(250, 245, 244), outline=(196, 176, 176), width=3)
    _draw_security_pattern(draw, top_box)
    draw.rectangle(data_box, fill=(248, 247, 231), outline=(188, 180, 150), width=3)
    _draw_security_pattern(draw, data_box, step=40)
    draw.line((px, py + top_h, px + pw, py + top_h), fill=(165, 150, 145), width=5)

    top_cn = _load_font(25)
    top_en = _load_font(22)
    draw.text((705, 555), "中华人民共和国有关机关请为持照人提供必要协助", fill=(137, 91, 91), font=top_cn)
    draw.text((690, 615), "THIS IS A SYNTHETIC CI TEST DOCUMENT - NOT A REAL PASSPORT", fill=(145, 105, 105), font=top_en)
    draw.text((755, 700), "MOCK / TEST ONLY", fill=(180, 130, 130), font=_load_font(42))

    header_font = _load_font(30)
    small_font = _load_font(22)
    label_font = _load_font(21)
    value_font = _load_font(31)
    name_font = _load_font(46)
    english_name_font = _load_font(34)
    mrz_font = _load_font(31, mono=True)

    data_y = py + top_h
    draw.text((px + 40, data_y + 32), "中华人民共和国  PEOPLE'S REPUBLIC OF CHINA", fill=(132, 86, 79), font=header_font)
    draw.text((px + 55, data_y + 92), "护照 / PASSPORT     MOCK TEST ONLY", fill=(148, 100, 82), font=small_font)

    photo_box = (px + 55, data_y + 170, px + 325, data_y + 520)
    _draw_placeholder_portrait(draw, photo_box)

    tx = px + 370
    ty = data_y + 155
    draw.text((tx, ty), "姓名 / Name", fill=(128, 104, 88), font=label_font)
    draw.text((tx, ty + 42), "张三", fill=(45, 45, 42), font=name_font)
    draw.text((tx, ty + 102), "ZHANG, SAN", fill=(45, 45, 42), font=english_name_font)

    right_x = px + 800
    draw.text((right_x, ty), "护照号码 / Passport No.", fill=(128, 104, 88), font=label_font)
    draw.text((right_x, ty + 42), "E12345678", fill=(65, 55, 50), font=value_font)

    row2 = ty + 180
    draw.text((tx, row2), "性别 / Sex", fill=(128, 104, 88), font=label_font)
    draw.text((tx, row2 + 36), "男 / M", fill=(55, 55, 50), font=value_font)
    draw.text((tx + 250, row2), "国籍 / Nationality", fill=(128, 104, 88), font=label_font)
    draw.text((tx + 250, row2 + 36), "中国 / CHINESE", fill=(55, 55, 50), font=value_font)
    draw.text((right_x, row2), "出生日期 / Date of birth", fill=(128, 104, 88), font=label_font)
    draw.text((right_x, row2 + 36), "01 JAN 1990", fill=(55, 55, 50), font=value_font)

    row3 = row2 + 125
    draw.text((tx, row3), "出生地点 / Place of birth", fill=(128, 104, 88), font=label_font)
    draw.text((tx, row3 + 36), "北京 / BEIJING", fill=(55, 55, 50), font=value_font)
    draw.text((right_x, row3), "有效期至 / Date of expiry", fill=(128, 104, 88), font=label_font)
    draw.text((right_x, row3 + 36), "01 JAN 2035", fill=(55, 55, 50), font=value_font)

    row4 = row3 + 125
    draw.text((tx, row4), "签发机关 / Authority", fill=(128, 104, 88), font=label_font)
    draw.text((tx, row4 + 36), "MOCK AUTHORITY", fill=(55, 55, 50), font=value_font)
    draw.text((right_x, row4), "持照人签名 / Bearer's signature", fill=(128, 104, 88), font=label_font)
    draw.text((right_x + 70, row4 + 38), "张三", fill=(94, 77, 70), font=_load_font(38))

    mrz_y = data_y + 725
    draw.rectangle((px + 35, mrz_y - 18, px + pw - 35, mrz_y + 135), fill=(246, 245, 225))
    draw.text((px + 55, mrz_y), "P<CHNZHANG<<SAN<<<<<<<<<<<<<<<<<<<<<<<<<<<", fill=(35, 35, 34), font=mrz_font)
    draw.text((px + 55, mrz_y + 58), "E12345678CHN9001011M3501012<<<<<<<<<<<<<<04", fill=(35, 35, 34), font=mrz_font)

    # Keep an unmistakable watermark so this fixture cannot be confused with a real identity document.
    draw.text((560, 2040), "SYNTHETIC MOCK - CI ONLY", fill=(225, 225, 225), font=_load_font(54))
    image.save(path, format="PNG")


def _self_test() -> int:
    """Exercise packaged imports, local models, and a realistic synthetic OCR inference."""
    try:
        import paddle  # noqa: F401
        import paddleocr  # noqa: F401
        import paddlex  # noqa: F401
        from passport_auto_renamer.extract import extract_best_name
        from passport_auto_renamer.ocr import PaddleOcrEngine

        engine = PaddleOcrEngine()
        with tempfile.TemporaryDirectory(prefix="passport-auto-renamer-") as tmp_dir:
            mock_path = Path(tmp_dir) / "mock-passport-scan.png"
            _create_mock_image(mock_path)
            items = engine.recognize(mock_path)

        if not items:
            raise RuntimeError("Mock OCR inference returned no recognized text.")

        recognized = " | ".join(item.text for item in items)
        compact = recognized.replace(" ", "")
        if "ZHANG" not in recognized.upper():
            raise RuntimeError(f"Mock OCR did not recognize expected English name: {recognized}")
        if "张三" not in compact:
            raise RuntimeError(f"Mock OCR did not recognize expected Chinese name: {recognized}")

        extracted = extract_best_name(items, prefer_chinese=True, min_confidence=0.55)
        if extracted is None or extracted.name != "张三":
            raise RuntimeError(f"Name extraction did not return 张三: extracted={extracted}; OCR={recognized}")

        _write_self_test_log(
            f"OK - realistic synthetic passport OCR completed, items={len(items)}\n"
            f"extracted={extracted.name} source={extracted.source} confidence={extracted.confidence:.3f}\n"
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
