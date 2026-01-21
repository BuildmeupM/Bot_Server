@echo off
title BotV3 EXE Installer
echo ================================================
echo 🤖 BotV3 EXE Installer
echo    ระบบประมวลผล PDF อัตโนมัติ
echo ================================================
echo.

echo 📋 กำลังติดตั้ง BotV3...
echo.

REM สร้างโฟลเดอร์หลัก
if not exist "BotV3" mkdir BotV3
cd BotV3

REM สร้างโฟลเดอร์ที่จำเป็น
if not exist "รหัส" mkdir รหัส
if not exist "folder_settings" mkdir folder_settings
if not exist "temp_uploads" mkdir temp_uploads
if not exist "เอกสารต้นฉบับ" mkdir เอกสารต้นฉบับ
if not exist "เอกสารบันทึกแล้ว" mkdir เอกสารบันทึกแล้ว
if not exist "เอกสารบันทึกแล้ว\เอกสาร Vat" mkdir "เอกสารบันทึกแล้ว\เอกสาร Vat"
if not exist "เอกสารบันทึกแล้ว\เอกสาร NoneVat" mkdir "เอกสารบันทึกแล้ว\เอกสาร NoneVat"
if not exist "เอกสารซ้ำรอตรวจ" mkdir เอกสารซ้ำรอตรวจ
if not exist "เอกสารฐานข้อมูลไม่เรียบร้อย" mkdir เอกสารฐานข้อมูลไม่เรียบร้อย
if not exist "เอกสารรอดำเนินการ" mkdir เอกสารรอดำเนินการ
if not exist "เอกสารอ่านข้อมูลไม่ได้" mkdir เอกสารอ่านข้อมูลไม่ได้
if not exist "เอกสารอ่านข้อมูลไม่ได้\เอกสาร PDF ภาพ" mkdir "เอกสารอ่านข้อมูลไม่ได้\เอกสาร PDF ภาพ"
if not exist "เอกสารอ่านข้อมูลไม่ได้\ยังไม่ได้นำเข้าระบบ" mkdir "เอกสารอ่านข้อมูลไม่ได้\ยังไม่ได้นำเข้าระบบ"

echo ✅ สร้างโฟลเดอร์เสร็จสิ้น

REM คัดลอกไฟล์ .exe
if exist "..\BotV3_GUI.exe" copy "..\BotV3_GUI.exe" "BotV3_GUI.exe"

echo ✅ คัดลอกไฟล์ .exe เสร็จสิ้น

REM สร้างไฟล์ config template
echo # -*- coding: utf-8 -*- > config_template.py
echo """BotV3 Configuration Template""" >> config_template.py
echo class Config: >> config_template.py
echo     BASE_FOLDER = "V" >> config_template.py
echo     MAIN_FOLDERS = ["A.โฟร์เดอร์หลัก", "AA.โฟรเดอร์หลัก"] >> config_template.py
echo     LINE_NOTIFY_TOKEN = "" >> config_template.py
echo     LINE_OA_CHANNEL_ACCESS_TOKEN = "" >> config_template.py

echo ✅ สร้างไฟล์ config template เสร็จสิ้น

REM สร้างไฟล์ข้อมูลตัวอย่าง
echo { > "รหัส\Build000.json"
echo   "companies": { >> "รหัส\Build000.json"
echo     "Shopee (Thailand) Co., Ltd.": { >> "รหัส\Build000.json"
echo       "customer_id": "C00001", >> "รหัส\Build000.json"
echo       "account_code": "520101" >> "รหัส\Build000.json"
echo     } >> "รหัส\Build000.json"
echo   } >> "รหัส\Build000.json"
echo } >> "รหัส\Build000.json"

echo Username : your_username_here > "รหัส\Build000.txt"
echo Password : your_password_here >> "รหัส\Build000.txt"
echo Link company : https://secure.peakengine.com/your_company_link >> "รหัส\Build000.txt"
echo Link Express : https://secure.peakengine.com/your_express_link >> "รหัส\Build000.txt"

echo ✅ สร้างไฟล์ข้อมูลตัวอย่างเสร็จสิ้น

REM สร้างไฟล์ folder_settings
echo { > "folder_settings\folder_settings.json"
echo   "Build000": { >> "folder_settings\folder_settings.json"
echo     "group": "regular", >> "folder_settings\folder_settings.json"
echo     "description": "โฟลเดอร์ทดสอบระบบ" >> "folder_settings\folder_settings.json"
echo   } >> "folder_settings\folder_settings.json"
echo } >> "folder_settings\folder_settings.json"

echo ✅ สร้างไฟล์ folder_settings เสร็จสิ้น

echo.
echo 🎉 การติดตั้งเสร็จสิ้น!
echo.
echo ขั้นตอนต่อไป:
echo 1. แก้ไขไฟล์ config.py
echo 2. ตั้งค่าไฟล์ข้อมูลในโฟลเดอร์ 'รหัส/'
echo 3. เริ่มระบบด้วย BotV3_GUI.exe
echo.
echo 📁 ไฟล์ .exe ที่พร้อมใช้งาน:
if exist "BotV3_GUI.exe" echo   - BotV3_GUI.exe (GUI หลัก)
echo.
pause
