#!/bin/bash

echo "================================================"
echo "🤖 BotV3 Setup - การติดตั้งระบบ"
echo "   ระบบประมวลผล PDF อัตโนมัติ"
echo "================================================"
echo ""

echo "📋 กำลังตรวจสอบ Python..."
if command -v python3 &> /dev/null; then
    python3 --version
elif command -v python &> /dev/null; then
    python --version
else
    echo "❌ ไม่พบ Python กรุณาติดตั้ง Python 3.8 หรือสูงกว่า"
    echo "   Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "   CentOS/RHEL: sudo yum install python3 python3-pip"
    echo "   macOS: brew install python3"
    exit 1
fi

echo ""
echo "🚀 เริ่มการติดตั้ง..."
echo ""

# ตรวจสอบว่าใช้ python3 หรือ python
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
else
    PYTHON_CMD="python"
    PIP_CMD="pip"
fi

$PYTHON_CMD install_botv3.py

echo ""
echo "📋 การติดตั้งเสร็จสิ้น!"
echo ""
echo "ขั้นตอนต่อไป:"
echo "1. แก้ไขไฟล์ config.py"
echo "2. ตั้งค่าไฟล์ข้อมูลในโฟลเดอร์ 'รหัส/'"
echo "3. เริ่มระบบด้วย ./start_botv3.sh"
echo ""
read -p "กด Enter เพื่อปิด..."
