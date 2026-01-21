@echo off
title BotV3 Desktop Application
color 0A

echo.
echo ============================================================
echo                BotV3 Desktop Application
echo ============================================================
echo.

REM ตรวจสอบ Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ไม่พบ Python กรุณาติดตั้ง Python 3.8+ ก่อน
    pause
    exit /b 1
)

REM ตรวจสอบไฟล์ที่จำเป็น
if not exist "bot_gui_tkinter.py" (
    echo ❌ ไม่พบไฟล์ bot_gui_tkinter.py
    pause
    exit /b 1
)

if not exist "config.py" (
    echo ❌ ไม่พบไฟล์ config.py
    pause
    exit /b 1
)

echo ✅ ตรวจสอบไฟล์เสร็จสิ้น
echo.

REM รันโปรแกรม
echo 🚀 กำลังเปิด Desktop Application...
echo.
python run_desktop_app.py

REM ถ้าโปรแกรมปิด ให้แสดงข้อความ
echo.
echo ============================================================
echo                    โปรแกรมปิดแล้ว
echo ============================================================
pause

