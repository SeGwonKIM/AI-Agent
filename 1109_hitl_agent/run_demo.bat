@echo off
chcp 65001 > nul
title TikTok HITL Publishing Dashboard
cd /d %~dp0

echo ======================================================================
echo    🛡️ 틱톡 숏폼 자동발행 HITL 승인 관제센터 데모 실행기
echo    모두의연구소 AI 에이전트 2기 | 사람이 승인하는 에이전트 만들기
echo ======================================================================
echo.
echo 웹 브라우저를 열고 http://localhost:8501 에 접속합니다...
echo.

start http://localhost:8501
python standalone_demo.py

pause
