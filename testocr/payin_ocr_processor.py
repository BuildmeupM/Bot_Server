"""
OCR Processor สำหรับ Pay-in ชำระภาษี โดยเฉพาะ
ใช้ AksonOCR API - Key Extract Model
"""
import requests
import json
from pathlib import Path
from typing import Dict, Any, Optional
import sys
import logging
import re

# เพิ่ม path เพื่อ import config
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from config import Config
except ImportError:
    Config = None

logger = logging.getLogger(__name__)


def get_payin_custom_fields() -> list:
    """
    สร้าง custom fields สำหรับ AksonOCR key-extract API สำหรับ Pay-in ชำระภาษี
    
    Returns:
        List of custom field dictionaries
    """
    return [
        {
            "key": "ชุดชำระเงิน/Pay-In Slip",
            "description": "ให้แสดงผลออกมาเป็น Pay-in ชำระภาษี",
            "example": "Pay-in ชำระภาษี"
        },
        {
            "key": "ชื่อ",
            "description": "ให้แสดงผลออกมาเป็นชื่อของกิจการ",
            "example": "บริษัท ไอสาม เกทเวย์ จำกัด"
        },
        {
            "key": "เลขประจำตัวผู้เสียภาษีอากร [REF1]",
            "description": "",
            "example": ""
        },
        {
            "key": "ยอดชำระ (บาท)",
            "description": "",
            "example": "0.00"
        },
        {
            "key": "ภายในวันที่",
            "description": "ให้ระบบเช็คว่าครบกำหนดชำระภายในวันที่เท่าไหร่ แปลงข้อมูลออกมาเป็น dd/mm/yyyy ในรูปแบบของปี ค.ศ.",
            "example": "15/1/2026"
        }
    ]


def process_payin_ocr(file_path: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    ประมวลผล OCR สำหรับ Pay-in ชำระภาษี โดยใช้ AksonOCR API
    
    Args:
        file_path: Path to PDF file
        api_key: AksonOCR API key (ถ้าไม่ระบุจะใช้จาก Config)
    
    Returns:
        Dictionary containing OCR results with structure:
        {
            'success': bool,
            'data': dict,  # ข้อมูลที่ extract ได้จาก API
            'raw_response': dict,  # Response ทั้งหมดจาก API
            'error': str or None
        }
    """
    # 1. API Configuration
    API_URL = "https://backend.aksonocr.com/api/v1/key-extract"
    
    # ใช้ API key จาก parameter หรือจาก Config
    if api_key is None:
        if Config and hasattr(Config, 'AKSON_API_KEY'):
            api_key = Config.AKSON_API_KEY
        else:
            return {
                'success': False,
                'data': {},
                'raw_response': {},
                'error': 'ไม่พบ API Key'
            }
    
    # ตรวจสอบว่าไฟล์มีอยู่จริง
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        return {
            'success': False,
            'data': {},
            'raw_response': {},
            'error': f'ไม่พบไฟล์: {file_path}'
        }
    
    # 2. Define custom fields
    custom_fields = get_payin_custom_fields()
    
    # 3. Prepare payload
    payload = {
        'customFields': json.dumps(custom_fields),
        'model': 'aksonocr-1.0',
        'additionalInstructions': 'ดึงข้อมูลให้ถูกต้องตามที่กำหนด โดยเน้นที่ชื่อหน่วยงานและเลขประจำตัวผู้เสียภาษีอากร จะต้องถูกต้องครบตัวอักษร'
    }
    
    # 4. Make the request
    headers = {'X-API-Key': api_key}
    
    try:
        logger.info(f"📤 [Pay-in OCR] กำลังส่งไฟล์ไปยัง AksonOCR API: {file_path_obj.name}")
        
        with open(file_path_obj, 'rb') as file:
            files = {'file': (file_path_obj.name, file, 'application/pdf')}
            
            response = requests.post(
                API_URL, 
                headers=headers, 
                data=payload, 
                files=files, 
                timeout=120  # เพิ่ม timeout เป็น 120 วินาที
            )
            
            logger.info(f"📥 [Pay-in OCR] Status Code: {response.status_code}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info("✅ [Pay-in OCR] สำเร็จ!")
                
                # Extract data from response
                if 'success' in result and result.get('success'):
                    data = result.get('data', {})
                    
                    # Extract fields - API ส่งมาเป็น dict ของ key-value โดยตรง
                    # เช่น { "ชื่อ": "บริษัท...", ... }
                    fields_data = {}
                    if isinstance(data, dict):
                        # ถ้า data เป็น dict โดยตรง (กรณีที่ API ส่งมาเป็น key-value)
                        if any('ชื่อ' in key or 'เลขประจำตัวผู้เสียภาษีอากร' in key or 'Pay-in' in key or 'Pay-In' in key or 'ยอดชำระ' in key or 'ภายในวันที่' in key for key in data.keys()):
                            fields_data = data
                        # ถ้า data มี 'fields' หรือ 'customFields' อยู่ข้างใน
                        elif 'fields' in data:
                            fields_data = data['fields']
                        elif 'customFields' in data:
                            fields_data = data['customFields']
                    
                    return {
                        'success': True,
                        'data': fields_data,  # ส่ง fields_data โดยตรง (ไม่ wrap อีกชั้น)
                        'raw_response': result,
                        'error': None
                    }
                else:
                    return {
                        'success': False,
                        'data': {},
                        'raw_response': result,
                        'error': 'API returned success=False'
                    }
            else:
                # Error response
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', {}).get('message', f'HTTP {response.status_code}')
                except:
                    error_msg = f'HTTP {response.status_code}: {response.text[:200]}'
                
                logger.error(f"❌ [Pay-in OCR] Error: {error_msg}")
                
                return {
                    'success': False,
                    'data': {},
                    'raw_response': {},
                    'error': error_msg
                }
                
    except requests.exceptions.Timeout:
        error_msg = 'Request timeout (เกิน 120 วินาที)'
        logger.error(f"❌ [Pay-in OCR] {error_msg}")
        return {
            'success': False,
            'data': {},
            'raw_response': {},
            'error': error_msg
        }
    except requests.exceptions.RequestException as e:
        error_msg = f'Network Error: {str(e)}'
        logger.error(f"❌ [Pay-in OCR] {error_msg}")
        return {
            'success': False,
            'data': {},
            'raw_response': {},
            'error': error_msg
        }
    except Exception as e:
        error_msg = f'Unexpected Error: {str(e)}'
        logger.error(f"❌ [Pay-in OCR] {error_msg}", exc_info=True)
        return {
            'success': False,
            'data': {},
            'raw_response': {},
            'error': error_msg
        }


def parse_payin_data(ocr_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse ข้อมูลจาก OCR result ให้เป็นรูปแบบที่ใช้งานได้
    
    Args:
        ocr_result: ผลลัพธ์จาก process_payin_ocr()
    
    Returns:
        Dictionary containing parsed data:
        {
            'company_name': str,  # ชื่อของกิจการ
            'tax_id': str,  # เลขประจำตัวผู้เสียภาษีอากร (ไม่เว้นวรรค)
            'payment_amount': float,  # ยอดชำระ (บาท)
            'due_date': str,  # ภายในวันที่ (dd/mm/yyyy ในรูปแบบปี ค.ศ.)
            'tax_form_type': 'Pay-in ชำระภาษี',
            'success': bool,
            'error': str or None
        }
    """
    if not ocr_result.get('success'):
        return {
            'company_name': '',
            'tax_id': '',
            'payment_amount': 0.00,
            'due_date': '',
            'tax_form_type': 'Pay-in ชำระภาษี',
            'success': False,
            'error': ocr_result.get('error', 'Unknown error')
        }
    
    # Extract fields - ข้อมูลอยู่ใน ocr_result['data'] โดยตรง
    # process_payin_ocr จะส่ง fields_data โดยตรง (ไม่ wrap อีกชั้น)
    fields = ocr_result.get('data', {})
    
    # ตรวจสอบว่า fields เป็น dict หรือไม่
    if not isinstance(fields, dict):
        fields = {}
    
    # Parse ชื่อของกิจการ
    company_name = fields.get('ชื่อ', '').strip() if fields.get('ชื่อ') else ''
    
    # Parse เลขประจำตัวผู้เสียภาษีอากร
    # สำหรับ Pay-in: ใช้ค่าตามที่อ่านได้จาก JSON (ไม่ format)
    tax_id = ''
    # ลองหาในหลายๆ key ที่อาจจะใช้
    tax_id_keys = [
        'เลขประจำตัวผู้เสียภาษีอากร [REF1]',
        'เลขประจำตัวผู้เสียภาษีอากร',
        'REF1'
    ]
    
    for key in tax_id_keys:
        if key in fields and fields[key]:
            tax_id = str(fields[key]).strip()
            break
    
    # ไม่ต้องลบ dash หรือช่องว่าง เพราะต้องการใช้ค่าตามที่อ่านได้
    
    # Parse ยอดชำระ (บาท)
    payment_amount = 0.00
    payment_amount_str = fields.get('ยอดชำระ (บาท)', '')
    if payment_amount_str:
        # ลบ comma และ whitespace
        clean_value = str(payment_amount_str).replace(',', '').replace(' ', '').strip()
        
        # หาตัวเลข (รองรับทศนิยม)
        match = re.search(r'(\d+\.?\d*)', clean_value)
        if match:
            try:
                payment_amount = float(match.group(1))
            except ValueError:
                payment_amount = 0.00
    
    # Parse ภายในวันที่ (dd/mm/yyyy ในรูปแบบปี ค.ศ.)
    due_date = ''
    due_date_str = fields.get('ภายในวันที่', '')
    if due_date_str:
        # ลองหา pattern วันที่ dd/mm/yyyy หรือ dd-mm-yyyy หรือรูปแบบอื่นๆ
        # รองรับทั้งปี พ.ศ. และ ค.ศ.
        date_patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # dd/mm/yyyy หรือ dd-mm-yyyy
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # yyyy/mm/dd หรือ yyyy-mm-dd
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, str(due_date_str))
            if match:
                if len(match.groups()) == 3:
                    # ถ้าเป็นรูปแบบ yyyy/mm/dd ให้แปลงเป็น dd/mm/yyyy
                    if len(match.group(1)) == 4:
                        year, month, day = match.groups()
                        # ถ้าเป็นปี พ.ศ. (มากกว่า 2500) ให้แปลงเป็น ค.ศ.
                        year_int = int(year)
                        if year_int > 2500:
                            year_int = year_int - 543
                        due_date = f"{day.zfill(2)}/{month.zfill(2)}/{year_int}"
                    else:
                        day, month, year = match.groups()
                        # ถ้าเป็นปี พ.ศ. (มากกว่า 2500) ให้แปลงเป็น ค.ศ.
                        year_int = int(year)
                        if year_int > 2500:
                            year_int = year_int - 543
                        due_date = f"{day.zfill(2)}/{month.zfill(2)}/{year_int}"
                    break
        
        # ถ้ายังหาไม่เจอ ให้ลองหาแบบอื่น (เช่น "15 มกราคม 2569")
        if not due_date:
            # Pattern สำหรับวันที่แบบไทย เช่น "15 มกราคม 2569"
            thai_months = {
                'มกราคม': '01', 'กุมภาพันธ์': '02', 'มีนาคม': '03', 'เมษายน': '04',
                'พฤษภาคม': '05', 'มิถุนายน': '06', 'กรกฎาคม': '07', 'สิงหาคม': '08',
                'กันยายน': '09', 'ตุลาคม': '10', 'พฤศจิกายน': '11', 'ธันวาคม': '12'
            }
            
            thai_date_pattern = r'(\d{1,2})\s+([ก-๙]+)\s+(\d{4})'
            match = re.search(thai_date_pattern, str(due_date_str))
            if match:
                day, month_name, year = match.groups()
                if month_name in thai_months:
                    month_num = thai_months[month_name]
                    # ถ้าเป็นปี พ.ศ. (มากกว่า 2500) ให้แปลงเป็น ค.ศ.
                    year_int = int(year)
                    if year_int > 2500:
                        year_int = year_int - 543
                    due_date = f"{day.zfill(2)}/{month_num}/{year_int}"
        
        # ถ้ายังหาไม่เจอ ให้เก็บค่าเดิม
        if not due_date:
            due_date = str(due_date_str).strip()
    
    # สร้าง amounts dictionary สำหรับส่งไป frontend
    amounts = {
        'ยอดชำระ (บาท)': payment_amount
    }
    
    return {
        'company_name': company_name,
        'tax_id': tax_id,  # ใช้ค่าตามที่อ่านได้ (ไม่ format)
        'payment_amount': payment_amount,
        'due_date': due_date,
        'tax_form_type': 'Pay-in ชำระภาษี',
        'success': True,
        'error': None,
        'raw_fields': fields,  # เก็บข้อมูลดิบไว้ด้วย
        'amounts': amounts  # เพิ่ม amounts dictionary สำหรับส่งไป frontend
    }


if __name__ == "__main__":
    # Test function
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python payin_ocr_processor.py <pdf_file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    print("=" * 70)
    print("🧪 ทดสอบ Pay-in OCR Processor")
    print("=" * 70)
    print(f"📄 ไฟล์: {file_path}")
    print("-" * 70)
    
    # Process OCR
    result = process_payin_ocr(file_path)
    
    if result['success']:
        print("✅ OCR สำเร็จ!")
        print("-" * 70)
        
        # Parse data
        parsed = parse_payin_data(result)
        
        print("\n📋 ข้อมูลที่ Extract ได้:")
        print("-" * 70)
        
        # แสดงข้อมูลกิจการ
        if parsed.get('company_name'):
            print(f"  🏢 ชื่อกิจการ: {parsed['company_name']}")
        if parsed.get('tax_id'):
            print(f"  🆔 เลขประจำตัวผู้เสียภาษีอากร: {parsed['tax_id']}")
        if parsed.get('payment_amount'):
            print(f"  💰 ยอดชำระ: {parsed['payment_amount']:,.2f} บาท")
        if parsed.get('due_date'):
            print(f"  📅 ภายในวันที่: {parsed['due_date']}")
        
        print("\n📄 Raw Fields:")
        print("-" * 70)
        for key, value in parsed.get('raw_fields', {}).items():
            if value:
                print(f"  • {key}: {value}")
    else:
        print(f"❌ OCR ไม่สำเร็จ: {result.get('error', 'Unknown error')}")
    
    print("=" * 70)
