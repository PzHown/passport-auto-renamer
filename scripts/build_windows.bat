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

REM Keep onedir for Paddle/PaddleOCR reliability; the Inno Setup installer wraps
REM the complete directory. The Python packaging helper follows PaddleOCR's
REM official PyInstaller guidance for Paddle binaries, PaddleX data and metadata.
python scripts\package_windows.py
if errorlevel 1 exit /b 1

echo.
echo Build complete: dist\PassportAutoRenamer\PassportAutoRenamer.exe
endlocal
