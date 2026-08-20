@echo off
setlocal

python -m pip install -r requirements-dev.txt
if errorlevel 1 exit /b 1

REM PaddlePaddle/PaddleOCR 的 PyInstaller 打包兼容性会随版本变化。
REM 第一版使用 onedir，通常比 onefile 更稳定，也便于放置模型文件。
pyinstaller --noconfirm --clean --windowed --onedir ^
  --name PassportAutoRenamer ^
  --paths src ^
  src\passport_auto_renamer\__main__.py

if errorlevel 1 exit /b 1

echo.
echo Build complete: dist\PassportAutoRenamer\PassportAutoRenamer.exe
endlocal
