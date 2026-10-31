@echo off
cd /d "%~dp0"
where pythonw.exe >nul 2>nul
if errorlevel 1 (
    start "" python.exe main.py
) else (
    start "" pythonw.exe main.py
)
