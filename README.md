# Passport Auto Renamer / 护照扫描件自动命名

一个面向 Windows 的本地工具：将一个或多个护照扫描件（PDF/JPG/PNG/TIFF）拖到程序上，使用 PaddleOCR 在本机识别护照姓名，并按姓名重命名后输出到指定目录。

> 设计目标：护照图片默认不上传云端；中文姓名优先，识别不到中文时回退到 MRZ（机读区）英文姓名。

## 当前状态

这是 v0.1 原型，重点验证“拖入文件 -> OCR -> 姓名提取 -> 安全重命名”的闭环。

- [x] 多文件拖放（Windows 将拖到 EXE 的路径作为命令行参数传入）
- [x] PDF / JPG / JPEG / PNG / TIFF
- [x] PaddleOCR 本地 OCR
- [x] 中国护照中文姓名启发式提取
- [x] MRZ 英文姓名解析兜底
- [x] 中文设置界面
- [x] 输出目录、复制/移动模式、文件名模板
- [x] 重名自动追加 `(2)`、`(3)`
- [x] 识别失败保留原文件，并写入失败目录
- [ ] 针对不同版本中国护照做更多样本校准
- [ ] Windows 安装包 / 自动构建 Release
- [ ] 可选：监控柯美 bizhub C368 的 SMB 扫描目录

## 安装环境

建议：Windows 10/11 64 位、Python 3.10/3.11、8 GB 以上内存、SSD。CPU 即可，不要求独立显卡。

PaddlePaddle 官方当前 Windows CPU 安装示例使用 3.3.0：

```powershell
python -m pip install paddlepaddle==3.3.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
python -m pip install -r requirements.txt
```

## 使用

### 1. Python 直接运行

双击/运行设置界面：

```powershell
python -m passport_auto_renamer
```

处理一个或多个文件：

```powershell
python -m passport_auto_renamer "D:\scan\001.pdf" "D:\scan\002.pdf"
```

### 2. Windows 拖放

打包成 EXE 后，直接把一个或多个扫描件拖到 `PassportAutoRenamer.exe` 上即可。

双击 EXE 时不传文件参数，因此会打开设置窗口。

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

该项目按“本地 OCR”设计，不需要调用云 OCR API。PaddleOCR 模型首次使用时可能需要联网下载；下载完成后可离线识别。护照属于敏感证件，建议只在受控电脑和受控目录中处理，并设置合适的 Windows 文件权限。

## 已知限制

护照版式、扫描角度、反光、分辨率、遮挡会影响 OCR。中文姓名提取目前使用启发式规则，因此在正式批量使用前，应使用你们实际的护照扫描样本做脱敏测试和规则校准。程序在低置信度或无法可靠提取姓名时应进入失败目录，而不是猜测并覆盖文件。

## 开发

```powershell
python -m pip install -r requirements-dev.txt
pytest
```

## License

MIT
