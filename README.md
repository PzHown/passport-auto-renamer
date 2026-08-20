# Passport Auto Renamer / 护照扫描件自动命名

一个面向 Windows 的本地工具：将一个或多个护照扫描件（PDF/JPG/PNG/TIFF）拖到程序上，使用 PaddleOCR 在本机识别护照姓名，并按姓名重命名后输出到指定目录。

> 设计目标：护照图片不上传云端；中文姓名优先，识别不到中文时回退到 MRZ（机读区）英文姓名。

## 下载即用

GitHub Actions 会构建一个包含 Python 运行时、Paddle/PaddleOCR 依赖和 OCR 模型的完整 Windows 包。

在仓库的 **Actions -> Build Windows Installer** 中下载构建产物 `PassportAutoRenamer-ready-to-use`，其中包含：

- `PassportAutoRenamer-Setup.exe`：推荐，双击安装后即可使用。
- `PassportAutoRenamer-Portable.zip`：免安装版，解压后直接运行。

正式安装包已经内置 `PP-OCRv5_mobile_det` 和 `PP-OCRv5_mobile_rec`，首次启动不需要再下载 OCR 模型，也不要求用户安装 Python。

安装后：

- 双击 `Passport Auto Renamer`：打开中文设置界面。
- 将一个或多个护照扫描件拖到程序快捷方式或 `PassportAutoRenamer.exe`：自动识别并重命名。

## 当前功能

- [x] 多文件拖放
- [x] PDF / JPG / JPEG / PNG / TIFF / BMP
- [x] PaddleOCR 本地 OCR
- [x] 中国护照中文姓名启发式提取
- [x] MRZ 英文姓名解析兜底
- [x] 中文设置界面
- [x] 输出目录、复制/移动模式、文件名模板
- [x] 重名自动追加 `(2)`、`(3)`
- [x] 识别失败保留原文件，并写入失败目录
- [x] GitHub Actions 自动构建 Windows 安装包
- [x] OCR 模型随安装包内置，可离线首次运行
- [ ] 针对不同版本中国护照做更多样本校准
- [ ] 可选：监控柯美 bizhub C368 的 SMB 扫描目录

## 默认命名逻辑

1. PaddleOCR 对扫描件执行本地 OCR。
2. 优先寻找 2~6 个汉字组成的姓名候选，并参考“姓名 / Name”字段的位置与 OCR 置信度打分。
3. 若没有可靠中文姓名，则在 OCR 文本中寻找 MRZ 第一行，例如：

```text
P<CHNZHANG<<SAN<<<<<<<<<<<<<<<<<<<<<<<<
```

解析为：

```text
ZHANG SAN
```

4. 文件名默认使用 `{name}`。例如识别到 `张三`，则输出为 `张三.pdf`。
5. 若 `张三.pdf` 已存在，则输出 `张三 (2).pdf`。

## 配置

首次运行会在用户配置目录生成：

```text
%APPDATA%\PassportAutoRenamer\config.json
```

示例：

```json
{
  "output_dir": "D:\\PassportScan\\Finished",
  "failed_dir": "D:\\PassportScan\\Failed",
  "mode": "copy",
  "filename_template": "{name}",
  "prefer_chinese": true,
  "min_confidence": 0.55
}
```

`mode` 支持：

- `copy`：保留原扫描件，复制到输出目录并改名（默认，更安全）
- `move`：移动原扫描件到输出目录并改名

## 隐私说明

正式安装包按完全本地 OCR 设计。模型在 GitHub Actions 构建时下载并打进安装包，终端用户处理护照时不需要将图片上传到第三方 OCR 服务，也不依赖首次联网下载模型。

护照属于敏感证件，建议只在受控电脑和受控目录中处理，并设置合适的 Windows 文件权限。

## 已知限制

护照版式、扫描角度、反光、分辨率、遮挡会影响 OCR。当前离线安装包为了降低体积和 CPU 负担，使用 PP-OCRv5 mobile 检测/识别模型，并关闭额外的文档方向分类模型，因此建议从柯美等扫描设备输出方向正常的页面。

中文姓名提取目前使用启发式规则，因此在正式批量使用前，应使用实际的脱敏护照扫描样本做校准。程序在低置信度或无法可靠提取姓名时应进入失败目录，而不是猜测并覆盖文件。

## 开发

建议 Windows 10/11 64 位、Python 3.11、8 GB 以上内存、SSD。CPU 即可，不要求独立显卡。

```powershell
python -m pip install paddlepaddle==3.3.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
python -m pip install -r requirements-dev.txt
pytest
python scripts/prepare_models.py
scripts\build_windows.bat
```

## License

MIT
