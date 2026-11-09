@echo off
title TikTok HITL Publishing Dashboard
cd /d "%~dp0"

start "" "%~dp0web_demo.html"

if exist "C:\AI-Agent\.venv\Scripts\python.exe" (
    "C:\AI-Agent\.venv\Scripts\python.exe" standalone_demo.py
) else if exist "C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe" (
    "C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe" standalone_demo.py
) else (
    python standalone_demo.py
)
pause
