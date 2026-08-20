@echo off
set PYTHONPATH=%~dp0..\src
python -m passport_auto_renamer %*
