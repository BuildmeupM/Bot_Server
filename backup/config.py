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
    LINE_OA_DEFAULT_TO = "C28e6b9cfcfec3c419ec6cb8eb52f294b"            # userId/groupId/roomId ปลายทางสำหรับ push
    
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
