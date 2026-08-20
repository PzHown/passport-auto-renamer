@echo off
setlocal

python -m pip install -r requirements-dev.txt
if errorlevel 1 exit /b 1

if not exist bundled_models\PP-OCRv5_mobile_det (
  echo Missing bundled detection model. Run: python scripts\prepare_models.py
  exit /b 1
)
if not exist bundled_models\PP-OCRv5_mobile_rec (
  echo Missing bundled recognition model. Run: python scripts\prepare_models.py
  exit /b 1
)

REM Use an absolute-import launcher as the PyInstaller entry point. Packaging the
REM package __main__.py directly breaks relative imports in frozen mode.
REM Keep onedir for Paddle/PaddleOCR reliability; the installer wraps this folder.
pyinstaller --noconfirm --clean --windowed --onedir ^
  --name PassportAutoRenamer ^
  --paths src ^
  --add-data "bundled_models;models" ^
  --collect-all paddleocr ^
  --collect-all paddlex ^
  src\launcher.py

if errorlevel 1 exit /b 1

echo.
echo Build complete: dist\PassportAutoRenamer\PassportAutoRenamer.exe
endlocal
