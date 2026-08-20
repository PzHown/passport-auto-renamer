from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

APP_NAME = "PassportAutoRenamer"


def config_path() -> Path:
    base = Path(os.environ.get("APPDATA", Path.home()))
    return base / APP_NAME / "config.json"


@dataclass
class AppConfig:
    output_dir: str = str(Path.home() / "PassportScan" / "Finished")
    failed_dir: str = str(Path.home() / "PassportScan" / "Failed")
    mode: str = "copy"
    filename_template: str = "{name}"
    prefer_chinese: bool = True
    min_confidence: float = 0.55

    def validate(self) -> None:
        if self.mode not in {"copy", "move"}:
            raise ValueError("mode 必须是 copy 或 move")
        if "{name}" not in self.filename_template:
            raise ValueError("filename_template 必须包含 {name}")
        if not 0 <= float(self.min_confidence) <= 1:
            raise ValueError("min_confidence 必须在 0~1 之间")


def load_config() -> AppConfig:
    path = config_path()
    if not path.exists():
        cfg = AppConfig()
        save_config(cfg)
        return cfg
    data = json.loads(path.read_text(encoding="utf-8"))
    cfg = AppConfig(**{**asdict(AppConfig()), **data})
    cfg.validate()
    return cfg


def save_config(cfg: AppConfig) -> None:
    cfg.validate()
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(asdict(cfg), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
