@echo off
chcp 65001 > nul
title TikTok HITL Publishing Dashboard
cd /d "%~dp0"

echo ==============================================================================
echo   🛡️ 틱톡 숏폼 자동발행 HITL 승인 관제센터 웹 데모
echo   모두의연구소 AI 에이전트 2기 | 9. 사람이 승인하는 에이전트 만들기
echo ==============================================================================
echo.
echo 웹 브라우저를 실행합니다...
echo.

:: 1. 브라우저에서 HTML 관제 대시보드 즉시 실행
start "" "%~dp0web_demo.html"

:: 2. 파이썬 환경이 있으면 백엔드 서버도 함께 구동
if exist "C:\AI-Agent\.venv\Scripts\python.exe" (
    set "PY=C:\AI-Agent\.venv\Scripts\python.exe"
) else if exist "C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe" (
    set "PY=C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe"
) else (
    set "PY=python"
)

echo 백엔드 서버 구동 시도 (%PY%)...
%PY% standalone_demo.py

pause
