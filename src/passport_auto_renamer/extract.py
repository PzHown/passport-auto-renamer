from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Sequence


CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
CJK_NAME_RE = re.compile(r"^[\u3400-\u4dbf\u4e00-\u9fff·]{2,8}$")

# 常见字段/国家文字，避免被误判为姓名。
CJK_STOPWORDS = {
    "姓名", "性别", "国籍", "出生日期", "出生地点", "签发日期", "有效期至",
    "签发机关", "中华人民共和国", "中华人民共和国护照", "护照", "中国",
    "持照人签名", "签名", "类型", "国家码", "护照号码",
}


@dataclass(frozen=True)
class OcrItem:
    text: str
    score: float
    box: tuple[float, float, float, float] | None = None

    @property
    def cx(self) -> float | None:
        if not self.box:
            return None
        x1, _, x2, _ = self.box
        return (x1 + x2) / 2

    @property
    def cy(self) -> float | None:
        if not self.box:
            return None
        _, y1, _, y2 = self.box
        return (y1 + y2) / 2


@dataclass(frozen=True)
class NameResult:
    name: str
    confidence: float
    source: str  # chinese | mrz


def clean_text(text: str) -> str:
    return re.sub(r"\s+", "", text or "").strip()


def normalize_chinese_candidate(text: str) -> str:
    text = clean_text(text)
    text = re.sub(r"^(姓名|姓名NAME|NAME姓名|NAME)[:：]?", "", text, flags=re.I)
    text = re.sub(r"[^\u3400-\u4dbf\u4e00-\u9fff·]", "", text)
    return text


def is_plausible_chinese_name(text: str) -> bool:
    if not CJK_NAME_RE.fullmatch(text):
        return False
    if text in CJK_STOPWORDS:
        return False
    # 绝大多数中文姓名 2~4 字；少数复姓/少数民族姓名更长，因此上限放宽。
    return 2 <= len(text.replace("·", "")) <= 6


def _find_name_labels(items: Sequence[OcrItem]) -> list[OcrItem]:
    labels = []
    for item in items:
        t = clean_text(item.text).upper()
        if t in {"姓名", "NAME", "姓名NAME", "NAME姓名"} or "姓名" in t:
            labels.append(item)
    return labels


def extract_chinese_name(items: Sequence[OcrItem], min_confidence: float = 0.55) -> NameResult | None:
    labels = _find_name_labels(items)
    candidates: list[tuple[float, OcrItem, str]] = []

    for item in items:
        if item.score < min_confidence:
            continue
        name = normalize_chinese_candidate(item.text)
        if not is_plausible_chinese_name(name):
            continue

        rank = float(item.score)

        # 中文姓名常为 2~4 字；过长候选略降权。
        if 2 <= len(name.replace("·", "")) <= 4:
            rank += 0.12

        # 若 OCR 框可用，则优先“姓名/Name”标签右侧或下方附近的候选。
        if item.box and labels:
            best_proximity = 0.0
            for label in labels:
                if not label.box or item.cx is None or item.cy is None or label.cx is None or label.cy is None:
                    continue
                dx = item.cx - label.cx
                dy = item.cy - label.cy
                # 右侧同一行，或下方一小段距离，都给予加分。
                if dx >= -20 and abs(dy) <= 120:
                    best_proximity = max(best_proximity, 0.35)
                elif dy >= -20 and dy <= 180 and abs(dx) <= 500:
                    best_proximity = max(best_proximity, 0.25)
            rank += best_proximity

        candidates.append((rank, item, name))

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0], reverse=True)
    rank, item, name = candidates[0]
    confidence = min(0.99, max(item.score, rank - 0.12))
    return NameResult(name=name, confidence=confidence, source="chinese")


def parse_mrz_name_line(line: str) -> str | None:
    """Parse TD3 passport MRZ line 1 and return 'SURNAME GIVEN NAMES'."""
    raw = re.sub(r"\s+", "", (line or "").upper())
    # OCR 可能把 '<' 周围插入空格；这里只接受 P< 开头的护照 MRZ。
    if not raw.startswith("P<") or len(raw) < 10:
        return None

    # TD3: 位置 6 开始为姓名；宽松处理非完整 44 字符行。
    payload = raw[5:] if len(raw) >= 6 else raw[2:]
    if "<<" not in payload:
        return None

    surname_raw, given_raw = payload.split("<<", 1)
    surname = re.sub(r"[^A-Z<]", "", surname_raw).replace("<", " ").strip()
    given = re.sub(r"[^A-Z<]", "", given_raw).replace("<", " ").strip()
    surname = re.sub(r"\s+", " ", surname)
    given = re.sub(r"\s+", " ", given)
    if not surname:
        return None

    full = " ".join(part for part in (surname, given) if part).strip()
    # 排除明显 OCR 噪声。
    if len(full.replace(" ", "")) < 3:
        return None
    return full


def extract_mrz_name(items: Iterable[OcrItem], min_confidence: float = 0.45) -> NameResult | None:
    best: NameResult | None = None
    for item in items:
        if item.score < min_confidence:
            continue
        name = parse_mrz_name_line(item.text)
        if name:
            result = NameResult(name=name, confidence=float(item.score), source="mrz")
            if best is None or result.confidence > best.confidence:
                best = result
    return best


def extract_best_name(
    items: Sequence[OcrItem],
    *,
    prefer_chinese: bool = True,
    min_confidence: float = 0.55,
) -> NameResult | None:
    chinese = extract_chinese_name(items, min_confidence=min_confidence)
    mrz = extract_mrz_name(items, min_confidence=max(0.40, min_confidence - 0.10))

    if prefer_chinese and chinese:
        return chinese
    if mrz:
        return mrz
    return chinese
