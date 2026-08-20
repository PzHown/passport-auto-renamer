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

REM Use onedir for Paddle/PaddleOCR reliability. The installer wraps this folder,
REM so end users still get a normal Windows setup experience.
pyinstaller --noconfirm --clean --windowed --onedir ^
  --name PassportAutoRenamer ^
  --paths src ^
  --add-data "bundled_models;models" ^
  --collect-all paddleocr ^
  --collect-all paddlex ^
  src\passport_auto_renamer\__main__.py

if errorlevel 1 exit /b 1

echo.
echo Build complete: dist\PassportAutoRenamer\PassportAutoRenamer.exe
endlocal
