import os
from pathlib import Path

class Config:
    # โครงสร้างโฟลเดอร์หลัก
    BASE_FOLDER = "V"  # หรือ "Synology"
    TEST_SYSTEM_FOLDER = "000 ทดสอบระบบ"
    
    # โฟลเดอร์หลักที่ต้องสแกน
    MAIN_FOLDERS = ["A.โฟร์เดอร์หลัก", "AA.โฟรเดอร์หลัก", "AAA.โฟรเดอร์หลัก"]
    
    # โฟลเดอร์ที่ต้องข้าม
    SKIP_FOLDERS = ["#recycle", "#snapshot", "A.BMUT", "A.Buildmeup", "A.งานนอก"]

    # โฟลเดอร์ที่ต้องเข้า
    CUSTOMER_FOLDER = "ลูกค้า"
    AUTOMATION_FOLDER = "ระบบอัตโนมัติ"
    
    # การตั้งค่าการประมวลผล
    MAX_PROCESSING_ITEMS = 60  # จำกัดจำนวนการประมวลผลสูงสุด
    
    COMPANY_VAT_STATUS = {
        "Shopee (Thailand) Co., Ltd.": "VAT",
        "Lazada Limited (Head Office)": "VAT",
        "SPX Express (Thailand) Co., Ltd.": "NoneVat",
        "Lazada Limited (Head Office)": "VAT",
        "gf.th.ar@grab.com" : "VAT",
        "K-BIZ Contact" : "VAT",
        "Delivery Hero (Thailand) Co., Ltd." : "VAT",
        "Purple Ventures Company Limited" : "VAT",
        "บริษัท ทรู มันนี่ จำกัด" : "VAT",
        "บริษัท ไลน์แมน (ประเทศไทย) จำกัด (สำนักงานใหญ่)": "VAT",
        "บริษัท กาแฟพันธุ์ไทย จำกัด": "VAT",
        "บริษัท แมกซ์ การ์ด จำกัด": "VAT",
        "Ksher Payment Co., Ltd.": "VAT",
        "Lazada Express Limited": "NoneVat",
        "Thai Happy Logistics Ltd. (Head Office)": "NoneVat",
        "LINE Company (THAILAND) LIMITED": "VAT",
        "บริษัท เคอีเอ็กซ์ เอ็กซ์เพรส (ประเทศไทย) จำกัด (มหาชน)": "NoneVat",
        "TikTok Shop (Thailand) Ltd. (Head Office)": "VAT",
        "บริษัท แอดวานซ์ ไวร์เลส เน็ทเวอร์ค จํากัด": "VAT",
        "Shippop Co., Ltd. (Headquarter)": "VAT",
        "บริษัท ชิปป๊อป จำกัด (สำนักงานใหญ่)": "VAT",
        "ttbbank.com": "VAT",
    }
    # การตั้งค่ากลุ่มบริษัท
    GROUP1_COMPANY_MAPPING = {
        "Shopee (Thailand) Co., Ltd.": "ค่าบริการ Shopee VAT",
        "Lazada Limited (Head Office)": "ค่าบริการ Lazada VAT",
        "SPX Express (Thailand) Co., Ltd.": "ค่าขนส่ง SPX",
        "Lazada Limited (Head Office)": "ค่าบริการ Lazada VAT",
        "gf.th.ar@grab.com": "ค่าบริการ Grab VAT",
        "K-BIZ Contact": "ค่าธรรมเนียมกสิกร VAT",
        "Delivery Hero (Thailand) Co., Ltd.": "ค่าบริการ Foodpanda VAT",
        "Purple Ventures Company Limited": "ค่าบริการ Robinhood VAT",
        "บริษัท ทรู มันนี่ จำกัด": "ค่าบริการ TrueMoney VAT",
        "บริษัท ไลน์แมน (ประเทศไทย) จำกัด (สำนักงานใหญ่)": "ค่าบริการ LINE MAN VAT",
        "บริษัท กาแฟพันธุ์ไทย จำกัด": "ค่าบริการ กาแฟพันธุ์ไทย VAT",
        "บริษัท แมกซ์ การ์ด จำกัด": "ค่าบริการ Maxcard VAT",
        "Ksher Payment Co., Ltd.": "ค่าบริการ Ksher VAT",
        "Lazada Express Limited": "ค่าขนส่ง Lazada",
        "Thai Happy Logistics Ltd. (Head Office)": "ค่าขนส่ง TikTok",
        "LINE Company (THAILAND) LIMITED": "ค่าบริการ LINE VAT",
        "บริษัท เคอีเอ็กซ์ เอ็กซ์เพรส (ประเทศไทย) จำกัด (มหาชน)": "ค่าขนส่ง Kerry",
        "TikTok Shop (Thailand) Ltd. (Head Office)": "ค่าบริการ TikTok VAT",
        "บริษัท แอดวานซ์ ไวร์เลส เน็ทเวอร์ค จํากัด": "ค่าบริการ AIS VAT",
        "Shippop Co., Ltd. (Headquarter)": "ค่าบริการ Shippop VAT",
        "บริษัท ชิปป๊อป จำกัด (สำนักงานใหญ่)": "ค่าบริการ Shippop VAT",
        "ttbbank.com": "ค่าบริการ ttbbank.com VAT",
    }
    
    GROUP3_COMPANY_MAPPING = {
        "Shopee (Thailand) Co., Ltd.": "ค่าบริการ Shopee ",
        "Lazada Limited (Head Office)": "ค่าบริการ Lazada ",
        "SPX Express (Thailand) Co., Ltd.": "ค่าขนส่ง SPX",
        "Lazada Limited (Head Office)": "ค่าบริการ Lazada",
        "gf.th.ar@grab.com": "ค่าบริการ Grab",
        "K-BIZ Contact": "ค่าธรรมเนียมกสิกร",
        "Delivery Hero (Thailand) Co., Ltd.": "ค่าบริการ Foodpanda",
        "Purple Ventures Company Limited": "ค่าบริการ Robinhood",
        "บริษัท ทรู มันนี่ จำกัด": "ค่าบริการ TrueMoney",
        "บริษัท ไลน์แมน (ประเทศไทย) จำกัด (สำนักงานใหญ่)": "ค่าบริการ LINE MAN",
        "บริษัท กาแฟพันธุ์ไทย จำกัด": "ค่าบริการ กาแฟพันธุ์ไทย",
        "บริษัท แมกซ์ การ์ด จำกัด": "ค่าบริการ Maxcard",
        "Ksher Payment Co., Ltd.": "ค่าบริการ Ksher",
        "Lazada Express Limited": "ค่าขนส่ง Lazada",
        "Thai Happy Logistics Ltd. (Head Office)": "ค่าขนส่ง TikTok",
        "LINE Company (THAILAND) LIMITED": "ค่าบริการ LINE",
        "บริษัท เคอีเอ็กซ์ เอ็กซ์เพรส (ประเทศไทย) จำกัด (มหาชน)": "ค่าขนส่ง Kerry",
        "TikTok Shop (Thailand) Ltd. (Head Office)": "ค่าบริการ TikTok",
        "บริษัท แอดวานซ์ ไวร์เลส เน็ทเวอร์ค จํากัด": "ค่าบริการ AIS",
        "Shippop Co., Ltd. (Headquarter)": "ค่าบริการ Shippop",
        "บริษัท ชิปป๊อป จำกัด (สำนักงานใหญ่)": "ค่าบริการ Shippop",
        "ttbbank.com": "ค่าบริการ ttbbank.com",
    }
    
    # URL เป้าหมาย
    PEAK_ENGINE_URL = "https://secure.peakengine.com/Home/Login"
    
    # การตั้งค่า Selenium
    SELENIUM_TIMEOUT = 30
    SELENIUM_IMPLICIT_WAIT = 10
    
    # การตั้งค่าไฟล์
    LOG_FILE = "bot_log.txt"
    REPORT_FILE = "bot_report.txt"
    EXCEL_LOG_FILE = "bot_log.xlsx"
    
    # การตั้งค่า LINE
    # LINE Notify (ส่งข้อความแบบง่าย - ตัวผู้ใช้จะกรอกเอง)
    LINE_NOTIFY_TOKEN = ""
    LINE_NOTIFY_ENABLED = True  # เปิด/ปิดการแจ้งเตือน LINE
    
    # LINE OA (Messaging API) - ตัวผู้ใช้จะกรอก token/secret เอง
    LINE_OA_CHANNEL_ACCESS_TOKEN = "YJs3V2sic1yX02ypBBY69ZIUXsObpJ2G9AONB3t7TvMKQJ8EJvOMzCMKAHjjj75SNvqR+KSwZ2/wBMOCvaiMXHptwTZeVMuBmT3mAtmFrcvu5lMJSJyaWLYW2+t+FQezLSxYBkQ5z9dQGlKar02cYgdB04t89/1O/w1cDnyilFU="
    LINE_OA_CHANNEL_SECRET = ""        # ใช้ตรวจสอบลายเซ็นตอนรับ Webhook
    LINE_OA_DEFAULT_TO = "C389a6ce3fd337a5f41666d3c39fcd4fb"            # userId/groupId/roomId ปลายทางสำหรับ push
    
    # Google Drive Settings
    GOOGLE_DRIVE_FOLDER_ID = "1ldTibIilFzBKoQZztMVhj1bLIzlLCg1W"
    
    # Mistral OCR Settings (ใช้ mistralai library)
    MISTRAL_OCR_API_KEY = "No8VPMGw64iIk7X85ZvuItI2IBRThTiX"  # ใส่ API key สำหรับ Mistral OCR ที่นี่
    MISTRAL_OCR_ENABLED = True  # เปิด/ปิดการใช้งาน Mistral OCR
    # หมายเหตุ: ต้องติดตั้ง mistralai library: pip install mistralai
    
    # AKSON OCR Settings (Primary OCR Service)
    AKSON_API_KEY = "ak_3541afc2d10848edbae590d71ab2b4e4"  # ใส่ API key สำหรับ AksonOCR ที่นี่
    AKSON_API_URL = "https://backend.aksonocr.com/api/v2/upload"  # ใส่ API endpoint URL
    AKSON_ENABLED = True  # เปิด/ปิดการใช้งาน AksonOCR
    
    # TYPHOON OCR Settings (Fallback - ใช้เมื่อ AksonOCR ไม่สามารถเชื่อมต่อได้)
    TYPHOON_API_KEY = "sk-fvOVV7K2bHQ39bBfvFoT5TwoxPpReDLKEDjMwXHZwxUzpf3J"  # ใส่ API key สำหรับ TYPHOON OCR ที่นี่
    TYPHOON_API_URL = "https://api.opentyphoon.ai/v1/ocr"  # ใส่ API endpoint URL (ถ้ามี) เช่น "https://api.typhoon.com/v1/ocr"
    TYPHOON_ENABLED = True  # เปิด/ปิดการใช้งาน TYPHOON OCR (เปิดเป็น fallback เมื่อ AksonOCR ไม่สามารถเชื่อมต่อได้)
    GOOGLE_DRIVE_CREDENTIALS_FILE = "credentials.json"  # Path ไปยัง credentials.json (ถ้ามี)
    GOOGLE_DRIVE_TOKEN_FILE = "token.pickle"  # Path ไปยัง token.pickle (ถ้ามี)
    
    # Ngrok Settings (สำหรับสร้าง HTTPS URL สำหรับ localhost)
    NGROK_ENABLED = True  # เปิด/ปิดการใช้ ngrok
    NGROK_URL = "https://980b9fc405de.ngrok-free.app"  # URL จาก ngrok (เช่น https://xxxx-xxxx-xxxx.ngrok-free.app) - ปล่อยว่างไว้ระบบจะดึงอัตโนมัติ
    NGROK_API_URL = "http://localhost:4040/api/tunnels"  # Ngrok API endpoint สำหรับดึง URL อัตโนมัติ
    
    # การตั้งค่าอีเมลล์ (SMTP)
    # ✅ ตั้งค่าเริ่มต้นสำหรับ SMTP
    SMTP_SERVER = "smtppro.zoho.com"  # เช่น smtp.gmail.com, smtp.outlook.com
    SMTP_PORT = 587            # Port สำหรับ TLS (587) หรือ SSL (465)
    SMTP_USE_TLS = True        # ใช้ TLS (True) หรือ SSL (False)
    SMTP_USERNAME = ""         # อีเมลล์ผู้ส่ง
    SMTP_PASSWORD = ""         # รหัสผ่านหรือ App Password
    EMAIL_FROM = ""            # อีเมลล์ผู้ส่ง (ถ้าไม่ระบุจะใช้ SMTP_USERNAME)
    EMAIL_ENABLED = False      # เปิด/ปิดการส่งอีเมลล์
    
    # การตั้งค่า Email Patterns และ Default Recipients
    # กำหนดเมลล์ผู้รับเริ่มต้น (ใช้เมื่อไม่ระบุในแต่ละครั้ง)
    EMAIL_DEFAULT_TO = []      # รายการอีเมลล์ผู้รับเริ่มต้น เช่น ["admin@example.com", "manager@example.com"]
    EMAIL_DEFAULT_CC = []      # รายการอีเมลล์ CC เริ่มต้น เช่น ["cc@example.com"]
    EMAIL_DEFAULT_BCC = []     # รายการอีเมลล์ BCC เริ่มต้น
    
    # ไฟล์สำหรับเก็บ Email Patterns (อยู่ใน email_system folder)
    EMAIL_PATTERNS_FILE = "email_system/email_patterns.json"  # ไฟล์ JSON สำหรับเก็บ email patterns
    EMAIL_SIGNATURES_FILE = "email_system/email_signatures.json"  # ไฟล์ JSON สำหรับเก็บ email signatures
    
    # การตั้งค่าโฟลเดอร์ผลลัพธ์
    OUTPUT_FOLDERS = {
        "original": "เอกสารต้นฉบับ",
        "processed": "เอกสารบันทึกแล้ว",
        "none_vat": "เอกสาร NoneVat",
        "vat": "เอกสาร Vat",
        "duplicate": "เอกสารซ้ำรอตรวจ",
        "processing_result": "ผลการประมวลผล",
        "database_error": "1. ฐานข้อมูลไม่เรียบร้อย",
        "pending_action": "2. เอกสารรอดำเนินการ",
        "unreadable": "3. เอกสารอ่านข้อมูลไม่ได้",
        "unreadable_image": "3.1 เอกสาร PDF ภาพ",
        "unreadable_not_implemented": "3.2 ยังไม่ได้นำเข้าระบบ"
    }
