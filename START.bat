@echo off
cd /d "%~dp0"
py -3.13 -c "import pandas" >nul 2>&1
if errorlevel 1 (
    py -3.13 -m pip install -r python_files\requirements.txt
    if errorlevel 1 pause & exit /b 1
)
py -3.13 python_files\main.py
if errorlevel 1 pause
