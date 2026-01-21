"""
ทดสอบ AksonOCR API - Key Extract Model
ใช้โครงสร้างตามตัวอย่างจากเอกสาร API
"""
import requests
import json
from pathlib import Path
import sys

# เพิ่ม path เพื่อ import config
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config

def test_aksonocr_api():
    """ทดสอบ AksonOCR API ด้วยไฟล์ PDF - Key Extract Model"""
    
    # 1. API Configuration
    API_URL = "https://backend.aksonocr.com/api/v1/key-extract"
    API_KEY = Config.AKSON_API_KEY
    
    # 2. ไฟล์ที่ต้องการทดสอบ
    test_file = Path(__file__).parent / "Wht_vat_BL-HLCUSZX2511CPIR9 EXC2512-224_006.pdf"
    
    if not test_file.exists():
        print(f"❌ ไม่พบไฟล์: {test_file}")
        return
    
    print(f"📄 ไฟล์ที่ทดสอบ: {test_file.name}")
    print(f"📏 ขนาดไฟล์: {test_file.stat().st_size} bytes")
    print(f"🔑 API Key: {API_KEY[:10]}...")
    
    # ตรวจสอบ magic bytes เพื่อยืนยันว่าเป็น PDF จริงๆ
    try:
        with open(test_file, "rb") as check_file:
            magic_bytes = check_file.read(4)
            is_pdf = magic_bytes.startswith(b'%PDF')
            print(f"🔍 Magic Bytes: {magic_bytes.hex()} ({magic_bytes})")
            print(f"🔍 Is PDF: {is_pdf}")
            if not is_pdf:
                print("⚠️ ไฟล์ไม่ใช่ PDF จริงๆ (magic bytes ไม่ตรงกับ %PDF)")
    except Exception as e:
        print(f"⚠️ ไม่สามารถตรวจสอบ magic bytes ได้: {e}")
    
    print("-" * 70)
    
    # 2. Define your extraction fields
    custom_fields = [
        {
            "key": "ประเภทเอกสาร",
            "description": "ประเภทเอกสาร เช่น Receipt/Tax Invoice, Receipt, Tax Invoice, Invoice, ใบเสร็จรับเงิน/ใบกำกับภาษี, ใบเสร็จรับเงิน, ใบกำกับภาษี, ใบแจ้งหนี้",
            "example": "Receipt / Tax Invoice"
        },
        {
            "key": "สถานะเอกสาร",
            "description": "สถานะเอกสารว่าเป็น ต้นฉบับ (Original) หรือ สำเนา (Copy/Duplicate)",
            "example": "ต้นฉบับ หรือ ORIGINAL"
        },
        {
            "key": "เลขที่ใบกำกับภาษี",
            "description": "เลขที่ใบกำกับภาษีหรือใบเสร็จ",
            "example": "IV2024001"
        },
        {
            "key": "วันที่",
            "description": "วันที่ออกใบกำกับภาษี",
            "example": "15/01/2567"
        },
        {
            "key": "ชื่อผู้ขาย",
            "description": "ชื่อบริษัทหรือร้านค้าผู้ขาย",
            "example": "บริษัท เอบีซี จำกัด"
        },
        {
            "key": "เลขประจำตัวผู้เสียภาษี - ผู้ขาย",
            "description": "เลขประจำตัวผู้เสียภาษีของบริษัทผู้ขาย (Tax ID)",
            "example": "0105518012712"
        },
        {
            "key": "ที่อยู่ผู้ขาย",
            "description": "ที่อยู่เต็มของผู้ขาย (บริษัทผู้ขาย) รวมเลขที่ ถนน แขวง/ตำบล เขต/อำเภอ จังหวัด รหัสไปรษณีย์",
            "example": "123 ถนนสุขุมวิท แขวงคลองตัน เขตคลองตัน กรุงเทพมหานคร 10110"
        },
        {
            "key": "สาขา - ผู้ขาย",
            "description": "สาขาของบริษัทผู้ขาย เช็คข้อมูลให้ครบถ้วนและถูกต้อง",
            "example": "00000"
        },
        {
            "key": "ชื่อผู้นำส่งภาษีมูลค่าเพิ่ม",
            "description": "ชื่อบริษัทหรือบุคคลที่นำส่งภาษีมูลค่าเพิ่ม (สำหรับแบบ ภ.พ.36) เช่น ชื่อที่แสดงในช่อง 'ชื่อผู้นำส่งภาษีมูลค่าเพิ่ม'",
            "example": "บริษัท ไอสาม เกทเวย์ จำกัด"
        },
        {
            "key": "เลขประจำตัวผู้เสียภาษี - ผู้นำส่งภาษีมูลค่าเพิ่ม",
            "description": "เลขประจำตัวผู้เสียภาษีของผู้นำส่งภาษีมูลค่าเพิ่ม (สำหรับแบบ ภ.พ.36) เช่น เลขที่แสดงในช่อง 'เลขประจำตัวผู้เสียภาษีอากร'",
            "example": "0105553114437"
        },
        {
            "key": "ที่อยู่ - ผู้นำส่งภาษีมูลค่าเพิ่ม",
            "description": "ที่อยู่ของผู้นำส่งภาษีมูลค่าเพิ่ม (สำหรับแบบ ภ.พ.36) รวมเลขที่ ถนน แขวง/ตำบล เขต/อำเภอ จังหวัด รหัสไปรษณีย์",
            "example": "อาคาร ไอทีเอฟ-ทาวเวอร์ ห้องเลขที่ - ชั้นที่ 25 เลขที่ 140/61 ถนน สีลม แขวง สุริยวงศ์ เขต บางรัก จังหวัด กรุงเทพมหานคร 10500"
        },
        {
            "key": "สาขา - ผู้นำส่งภาษีมูลค่าเพิ่ม",
            "description": "สาขาของผู้นำส่งภาษีมูลค่าเพิ่ม (สำหรับแบบ ภ.พ.36) เช่น เลขที่แสดงในช่อง 'สาขาที่'",
            "example": "00000"
        },
        {
            "key": "ชื่อผู้ซื้อ",
            "description": "ชื่อบริษัทหรือลูกค้าผู้ซื้อ",
            "example": "บริษัท ลูกค้า จำกัด"
        },
        {
            "key": "เลขประจำตัวผู้เสียภาษี - ผู้ซื้อ",
            "description": "เลขประจำตัวผู้เสียภาษีของลูกค้าผู้ซื้อ (Tax ID)",
            "example": "0105568010721"
        },
        {
            "key": "ที่อยู่ผู้ซื้อ",
            "description": "ที่อยู่เต็มของผู้ซื้อ (ลูกค้า) รวมเลขที่ ถนน แขวง/ตำบล เขต/อำเภอ จังหวัด รหัสไปรษณีย์",
            "example": "456 ถนนพหลโยธิน แขวงจตุจักร เขตจตุจักร กรุงเทพมหานคร 10900"
        },
        {
            "key": "สาขา - ผู้ซื้อ",
            "description": "สาขาของบริษัทผู้ซื้อ เช็คข้อมูลให้ครบถ้วนและถูกต้อง",
            "example": "00000"
        },
        {
            "key": "ค่าธรรมเนียม",
            "description": "ค่าธรรมเนียมหรือค่าบริการ (Commission) สำหรับเอกสารบางประเภท เช่น เอกสารของบริษัท เคเชอร์ เพย์เมนท์ จำกัด",
            "example": "16.54"
        },
        {
            "key": "ยอดรวมก่อนภาษี",
            "description": "ยอดรวมก่อนภาษีมูลค่าเพิ่ม",
            "example": "1,000.00"
        },
        {
            "key": "ภาษีมูลค่าเพิ่ม",
            "description": "จำนวนเงินภาษีมูลค่าเพิ่ม (VAT)",
            "example": "70.00"
        },
        {
            "key": "ส่วนลด",
            "description": "ส่วนลดที่รับได้ (ถ้ามี)",
            "example": "100.00"
        },
        {
            "key": "ยอดเงินที่ได้รับยกเว้นภาษี",
            "description": "ยอดเงินที่ได้รับยกเว้นภาษีมูลค่าเพิ่ม (Non-Taxable Amount) เช่น ยอดขายที่ได้รับยกเว้น ยอดที่ได้รับยกเว้นภาษี ยอดยกเว้นภาษี",
            "example": "500.00"
        },
        {
            "key": "ยอดรวมสุทธิ",
            "description": "ยอดรวมทั้งสิ้นที่ต้องชำระ",
            "example": "1,070.00"
        },
        {
            "key": "มีการหัก ณ ที่จ่าย",
            "description": "ตรวจสอบว่าเอกสารมีการหัก ณ ที่จ่ายหรือไม่ (Withholding Tax) เช่น มีข้อความ 'หัก ณ ที่จ่าย', 'WHT', 'Withholding Tax', 'หักภาษี ณ ที่จ่าย'",
            "example": "ใช่ หรือ ไม่ใช่ หรือ มี หรือ ไม่มี"
        },
        {
            "key": "จำนวนเงินหัก ณ ที่จ่าย",
            "description": "จำนวนเงินที่หัก ณ ที่จ่าย (ถ้ามี)",
            "example": "100.00"
        },
        {
            "key": "อัตราหัก ณ ที่จ่าย",
            "description": "อัตราการหัก ณ ที่จ่าย (ถ้ามี) เช่น 3%, 5%",
            "example": "3%"
        },
        {
            "key": "การหัก ณ ที่จ่ายเป็นการกระทำการแทน",
            "description": "ตรวจสอบว่าการหัก ณ ที่จ่ายเป็นการกระทำการแทนหรือไม่ เช่น มีข้อความ 'กระทำการแทน', 'Acting on behalf', 'ผู้รับมอบอำนาจ'",
            "example": "ใช่ หรือ ไม่ใช่ หรือ มี หรือ ไม่มี"
        },
        {
            "key": "ชื่อผู้รับมอบอำนาจ",
            "description": "ชื่อบริษัทหรือบุคคลที่รับมอบอำนาจ (ถ้ามีการกระทำการแทน)",
            "example": "บริษัท รับมอบอำนาจ จำกัด"
        },
        {
            "key": "เลขประจำตัวผู้เสียภาษี - ผู้รับมอบอำนาจ",
            "description": "เลขประจำตัวผู้เสียภาษีของผู้รับมอบอำนาจ (ถ้ามีการกระทำการแทน)",
            "example": "0105518012712"
        },
    ]
    
    # 3. Prepare the file and data
    payload = {
        'customFields': json.dumps(custom_fields),
        'model': 'aksonocr-1.0',
        'additionalInstructions': 'ดึงข้อมูลจากใบกำกับภาษี โดยเน้นความถูกต้องของตัวเลขและวันที่'
    }
    
    print("📋 Payload Configuration:")
    print(f"  - Model: {payload['model']}")
    print(f"  - Custom Fields: {len(custom_fields)} fields")
    print("-" * 70)
    
    # 5. Make the request
    headers = {'X-API-Key': API_KEY}
    
    # ใช้รูปแบบที่ใช้งานได้ (ระบุ filename และ content-type)
    try:
        print("📤 กำลังส่งไฟล์ไปยัง AksonOCR API...")
        with open(test_file, 'rb') as file:
            files = {'file': (test_file.name, file, 'application/pdf')}
            
            response = requests.post(API_URL, headers=headers, data=payload, files=files, timeout=60)
            
            print(f"📥 Status Code: {response.status_code}")
            print("-" * 70)
            
            if response.status_code in [200, 201]:
                result = response.json()
                print("✅ สำเร็จ!")
                print(f"📋 Response Structure: {list(result.keys())}")
                print("-" * 70)
                
                # แสดงผลลัพธ์ที่ได้จากไฟล์ PDF จริงๆ
                print("📄 ผลลัพธ์ที่ได้จากไฟล์ PDF:")
                print("=" * 70)
                
                # ตรวจสอบโครงสร้าง response
                if 'success' in result and result.get('success'):
                    if 'data' in result:
                        data = result['data']
                        
                        # แสดงข้อมูลที่ extract ได้
                        print("\n📋 ข้อมูลที่ Extract ได้:")
                        print("-" * 70)
                        
                        # แสดง custom fields ที่ extract ได้
                        # รองรับทั้งโครงสร้าง fields, customFields หรือ data เป็น dictionary โดยตรง
                        fields_data = {}
                        if isinstance(data, dict):
                            if 'fields' in data:
                                fields_data = data.get('fields', {})
                            elif 'customFields' in data:
                                fields_data = data.get('customFields', {})
                            else:
                                # ถ้า data เป็น dictionary โดยตรง ให้ใช้ data ทั้งหมด
                                fields_data = data
                        
                        # แสดงทุกฟิลด์ที่กำหนดไว้ใน custom_fields
                        print("\n📋 ข้อมูลที่ Extract ได้ (แสดงทุกฟิลด์):")
                        print("-" * 70)
                        for field in custom_fields:
                            field_key = field['key']
                            field_value = fields_data.get(field_key, None)
                            
                            # แสดงค่าหรือ "ไม่มีข้อมูล"
                            if field_value:
                                print(f"  ✅ {field_key}: {field_value}")
                            else:
                                print(f"  ⚠️  {field_key}: ไม่มีข้อมูล")
                        
                        # แสดงข้อมูลอื่นๆ ที่อาจมีใน response แต่ไม่ได้กำหนดใน custom_fields
                        other_fields = {}
                        if isinstance(fields_data, dict):
                            for key in fields_data:
                                if key not in [f['key'] for f in custom_fields]:
                                    other_fields[key] = fields_data[key]
                        
                        if other_fields:
                            print("\n📋 ข้อมูลเพิ่มเติม (ไม่ได้กำหนดใน custom_fields):")
                            print("-" * 70)
                            for key, value in other_fields.items():
                                if value:
                                    print(f"  • {key}: {value}")
                        
                        # แสดงข้อมูลทั้งหมด (Full Response)
                        print(f"\n📄 ข้อมูลทั้งหมด (Full Response):")
                        print("-" * 70)
                        print(json.dumps(result, indent=2, ensure_ascii=False))
                    else:
                        # ถ้าไม่มี 'data' ให้แสดงทั้งหมด
                        print(json.dumps(result, indent=2, ensure_ascii=False))
                else:
                    # แสดงผลลัพธ์ทั้งหมด
                    print(json.dumps(result, indent=2, ensure_ascii=False))
                
            else:
                print("❌ ไม่สำเร็จ!")
                try:
                    error_data = response.json()
                    # แสดง error ทั้งหมดเพื่อ debug
                    print(f"📋 Full Error Response:")
                    print(json.dumps(error_data, indent=2, ensure_ascii=False))
                    
                    # แสดง error code และ message ถ้ามี
                    if 'error' in error_data:
                        if isinstance(error_data['error'], dict):
                            error_code = error_data['error'].get('code', 'UNKNOWN')
                            error_msg = error_data['error'].get('message', 'Unknown error')
                            print(f"📋 Error: [{error_code}] {error_msg}")
                        else:
                            print(f"📋 Error: {error_data['error']}")
                    elif 'code' in error_data:
                        print(f"📋 Error Code: {error_data['code']}")
                except Exception as e:
                    print(f"📋 Error Text: {response.text[:500]}")
                    print(f"📋 Parse Error: {e}")
                    
    except requests.exceptions.RequestException as e:
        print(f"❌ Network Error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 70)
    print("🧪 ทดสอบ AksonOCR API - Key Extract Model")
    print("=" * 70)
    test_aksonocr_api()
    print("=" * 70)
