from __future__ import annotations

from pathlib import Path
from typing import Any

from .extract import OcrItem

SUPPORTED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}


class PaddleOcrEngine:
    def __init__(self) -> None:
        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "未安装 PaddleOCR。请先安装 PaddlePaddle CPU 版和 requirements.txt。"
            ) from exc

        # 中文模型同时可识别中文与拉丁字母；打开页面方向分类，关闭不必要的去畸变以降低 CPU 开销。
        self._ocr = PaddleOCR(
            lang="ch",
            device="cpu",
            use_doc_orientation_classify=True,
            use_doc_unwarping=False,
            use_textline_orientation=False,
        )

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
