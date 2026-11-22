@echo off
title iNiKKi laptop run
cd /d "%~dp0"
echo.
echo  iNiKKi laptop run: keep this window open and the laptop plugged in until it says Finished.
echo.
where py >/dev/null 2>NUL || (echo Python is not installed. Install it from python.org/downloads ^(tick "Add python.exe to PATH"^), then double-click this file again. & pause & exit /b)
echo Getting the newest helper...
curl -s -L -o clip_helper.py https://raw.githubusercontent.com/haridhyaragav77-bit/inikki-reels/main/tools/clip_helper.py
py clip_helper.py
echo.
echo  Finished. Now press Done on the Manual work tab of the Control Room.
echo  Press any key to close this window.
pause >nul
