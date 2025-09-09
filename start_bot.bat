@echo off
echo ========================================
echo           POPAYS BOT STARTING
echo ========================================
echo.
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo ========================================
echo Dependencies installed successfully!
echo ========================================
echo.
echo Starting POPAYS Bot...
echo Bot will send orders to channel: -1002958129439
echo.
python main.py
pause
