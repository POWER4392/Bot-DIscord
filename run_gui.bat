@echo off
title Kich hoat va Chay Bot GUI
cd /d "%~dp0"
if not exist .venv (
    echo [ERROR] Thu muc .venv khong ton tai!
    echo Vui long tao virtual environment va cai dat cac dependencies truoc.
    pause
    exit /b
)
echo [STARTING] Dang chay Setting GUI qua virtual environment (.venv)...
.venv\Scripts\python.exe setting_gui.py
if %errorlevel% neq 0 pause

