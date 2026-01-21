@echo off
title BotV3 Setup - การติดตั้งระบบ
echo ================================================
echo 🤖 BotV3 Setup - การติดตั้งระบบ
echo    ระบบประมวลผล PDF อัตโนมัติ
echo ================================================
echo.

echo 📋 กำลังตรวจสอบ Python...
python --version
if errorlevel 1 (
    echo ❌ ไม่พบ Python กรุณาติดตั้ง Python 3.8 หรือสูงกว่า
    echo    ดาวน์โหลดได้ที่: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo.
echo 🚀 เริ่มการติดตั้ง...
echo.

python install_botv3.py

echo.
echo 📋 การติดตั้งเสร็จสิ้น!
echo.
echo ขั้นตอนต่อไป:
echo 1. แก้ไขไฟล์ config.py
echo 2. ตั้งค่าไฟล์ข้อมูลในโฟลเดอร์ 'รหัส/'
echo 3. เริ่มระบบด้วย start_botv3.bat
echo.
pause
