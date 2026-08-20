from passport_auto_renamer.extract import (
    OcrItem,
    extract_best_name,
    extract_chinese_name,
    parse_mrz_name_line,
)


def test_parse_mrz_name():
    line = "P<CHNZHANG<<SAN<<<<<<<<<<<<<<<<<<<<<<<<<<<<"
    assert parse_mrz_name_line(line) == "ZHANG SAN"


def test_extract_chinese_name_near_label():
    items = [
        OcrItem("中华人民共和国", 0.99, (10, 10, 200, 40)),
        OcrItem("姓名", 0.98, (100, 120, 180, 160)),
        OcrItem("张三", 0.93, (240, 118, 330, 162)),
        OcrItem("中国", 0.99, (100, 220, 170, 250)),
    ]
    result = extract_chinese_name(items)
    assert result is not None
    assert result.name == "张三"
    assert result.source == "chinese"


def test_best_name_prefers_chinese():
    items = [
        OcrItem("姓名", 0.98, (100, 100, 180, 140)),
        OcrItem("李小明", 0.91, (220, 100, 350, 140)),
        OcrItem("P<CHNLI<<XIAOMING<<<<<<<<<<<<<<<<<<<<<<<<<", 0.96, (0, 700, 800, 740)),
    ]
    result = extract_best_name(items, prefer_chinese=True)
    assert result is not None
    assert result.name == "李小明"


def test_best_name_falls_back_to_mrz():
    items = [OcrItem("P<CHNWANG<<WU<<<<<<<<<<<<<<<<<<<<<<<<<<<<", 0.95, None)]
    result = extract_best_name(items, prefer_chinese=True)
    assert result is not None
    assert result.name == "WANG WU"
