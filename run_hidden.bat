@echo off
cd /d "%~dp0"
:: Activate venv and run server.py (this is called by the VBS script)
call venv\Scripts\activate.bat
python server.py
