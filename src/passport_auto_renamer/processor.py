from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from .config import AppConfig
from .extract import NameResult, extract_best_name
from .files import sanitize_filename, transfer_file, unique_destination
from .ocr import PaddleOcrEngine, SUPPORTED_EXTENSIONS

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProcessResult:
    source: Path
    destination: Path | None
    name_result: NameResult | None
    success: bool
    message: str


class PassportProcessor:
    def __init__(self, config: AppConfig, engine: PaddleOcrEngine | None = None) -> None:
        self.config = config
        self.engine = engine or PaddleOcrEngine()

    def process(self, source: Path) -> ProcessResult:
        source = source.expanduser().resolve()
        if not source.exists() or not source.is_file():
            return ProcessResult(source, None, None, False, "文件不存在")
        if source.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return ProcessResult(source, None, None, False, "不支持的文件类型")

        try:
            items = self.engine.recognize(source)
            name_result = extract_best_name(
                items,
                prefer_chinese=self.config.prefer_chinese,
                min_confidence=float(self.config.min_confidence),
            )
            if not name_result:
                return self._send_to_failed(source, "未可靠识别到姓名")

            stem = self.config.filename_template.format(name=name_result.name)
            stem = sanitize_filename(stem)
            dest = unique_destination(Path(self.config.output_dir), stem, source.suffix.lower())
            transfer_file(source, dest, self.config.mode)
            return ProcessResult(
                source, dest, name_result, True,
                f"识别成功：{name_result.name} ({name_result.source}, {name_result.confidence:.2f})",
            )
        except Exception as exc:
            log.exception("处理失败: %s", source)
            return self._send_to_failed(source, f"处理异常：{exc}")

    def _send_to_failed(self, source: Path, reason: str) -> ProcessResult:
        failed_dir = Path(self.config.failed_dir)
        dest = unique_destination(failed_dir, source.stem, source.suffix.lower())
        # 失败文件始终复制，不移动原始文件，避免误操作导致原件丢失。
        transfer_file(source, dest, "copy")
        return ProcessResult(source, dest, None, False, reason)
