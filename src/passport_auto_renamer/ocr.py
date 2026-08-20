from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from .extract import OcrItem

SUPPORTED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}
DET_MODEL_NAME = "PP-OCRv5_mobile_det"
REC_MODEL_NAME = "PP-OCRv5_mobile_rec"


def _resource_root() -> Path:
    """Return the PyInstaller resource directory, or the project root in dev mode."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parents[2]


def _bundled_model_dir(model_name: str) -> Path | None:
    path = _resource_root() / "models" / model_name
    return path if path.is_dir() else None


class PaddleOcrEngine:
    def __init__(self) -> None:
        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "未安装 PaddleOCR。请使用完整安装包，或先安装 PaddlePaddle CPU 版和 requirements.txt。"
            ) from exc

        det_dir = _bundled_model_dir(DET_MODEL_NAME)
        rec_dir = _bundled_model_dir(REC_MODEL_NAME)

        kwargs: dict[str, Any] = {
            "lang": "ch",
            "device": "cpu",
            "use_doc_orientation_classify": False,
            "use_doc_unwarping": False,
            "use_textline_orientation": False,
            "text_detection_model_name": DET_MODEL_NAME,
            "text_recognition_model_name": REC_MODEL_NAME,
        }

        # 正式安装包把模型放在 models/ 下，并显式传给 PaddleOCR，因此首次启动也不需要联网下载模型。
        if det_dir and rec_dir:
            kwargs["text_detection_model_dir"] = str(det_dir)
            kwargs["text_recognition_model_dir"] = str(rec_dir)
        elif getattr(sys, "frozen", False):
            raise RuntimeError("安装包缺少 OCR 模型，请重新下载安装完整版本。")

        self._ocr = PaddleOCR(**kwargs)

    @staticmethod
    def _to_box(raw: Any) -> tuple[float, float, float, float] | None:
        if raw is None:
            return None
        try:
            vals = list(raw)
            if len(vals) == 4 and not isinstance(vals[0], (list, tuple)):
                return tuple(float(v) for v in vals)  # type: ignore[return-value]
        except Exception:
            return None
        return None

    def recognize(self, file_path: Path) -> list[OcrItem]:
        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise ValueError(f"不支持的文件类型：{file_path.suffix}")

        results = self._ocr.predict(str(file_path))
        items: list[OcrItem] = []

        # 护照扫描件通常一页即可。若 PDF 含多页，也只取首个有效页，避免误读后续附件。
        for result in results:
            payload = getattr(result, "json", None)
            if callable(payload):
                payload = payload()
            if not isinstance(payload, dict):
                continue
            res = payload.get("res", payload)
            texts = list(res.get("rec_texts") or [])
            scores = list(res.get("rec_scores") or [])
            boxes = list(res.get("rec_boxes") or [])

            for idx, text in enumerate(texts):
                score = float(scores[idx]) if idx < len(scores) else 0.0
                box = self._to_box(boxes[idx]) if idx < len(boxes) else None
                items.append(OcrItem(text=str(text), score=score, box=box))

            if items:
                break

        return items
