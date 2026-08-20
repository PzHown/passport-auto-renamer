from __future__ import annotations

import shutil
from pathlib import Path

from paddleocr import PaddleOCR

DET_MODEL = "PP-OCRv5_mobile_det"
REC_MODEL = "PP-OCRv5_mobile_rec"
TARGET_ROOT = Path("bundled_models")


def find_model_dir(model_name: str) -> Path:
    home = Path.home()
    preferred = home / ".paddlex" / "official_models" / model_name
    if preferred.is_dir():
        return preferred

    matches = [p for p in home.rglob(model_name) if p.is_dir()]
    if not matches:
        raise FileNotFoundError(f"Downloaded model directory not found: {model_name}")
    return matches[0]


def main() -> None:
    TARGET_ROOT.mkdir(parents=True, exist_ok=True)

    # Initializing PaddleOCR on the clean Actions runner downloads the selected
    # official inference models once. They are then copied into the build tree.
    PaddleOCR(
        lang="ch",
        device="cpu",
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        text_detection_model_name=DET_MODEL,
        text_recognition_model_name=REC_MODEL,
    )

    for name in (DET_MODEL, REC_MODEL):
        source = find_model_dir(name)
        target = TARGET_ROOT / name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target)
        print(f"Bundled {name}: {source} -> {target}")


if __name__ == "__main__":
    main()
