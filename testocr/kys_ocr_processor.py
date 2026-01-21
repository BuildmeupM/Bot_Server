"""
OCR Processor สำหรับแบบ กยศ. โดยเฉพาะ
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


def get_kys_custom_fields() -> list:
    """
    สร้าง custom fields สำหรับ AksonOCR key-extract API สำหรับแบบ กยศ.
    
    Returns:
        List of custom field dictionaries
    """
    return [
        {
            "key": "สำหรับหน่วยงานรับชำระเงินกู้ยืมคืน กยศ.",
            "description": "",
            "example": "กองทุน กยศ."
        },
        {
            "key": "ชื่อหน่วยงาน",
            "description": "",
            "example": "บริษัท ไอสาม เกทเวย์ จำกัด"
        },
        {
            "key": "เลขประจำตัวผู้เสียภาษีอากร",
            "description": "ดึงข้อมูลแบบที่ไม่ต้องมีเว้นวรรค",
            "example": "0105564065416"
        },
        {
            "key": "ชำระเงินของเดือน ",
            "description": "ให้ระบบดูว่าชำระเงินของเดือนไหน",
            "example": "12/2568"
        },
        {
            "key": "วันที่ครบกำหนดชำระเงิน",
            "description": "ให้แสดงผลลัพธ์ออกมาในรูปแบบของ dd/mm/yyyy",
            "example": "01/11/2568"
        },
        {
            "key": "ยอดชำระ (บาท)",
            "description": "",
            "example": "0.00"
        }
    ]


def process_kys_ocr(file_path: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    ประมวลผล OCR สำหรับแบบ กยศ. โดยใช้ AksonOCR API
    
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
    custom_fields = get_kys_custom_fields()
    
    # 3. Prepare payload
    payload = {
        'customFields': json.dumps(custom_fields),
        'model': 'aksonocr-1.0',
        'additionalInstructions': 'ดึงข้อมูลให้ถูกต้องตามที่กำหนด โดยเน้นที่ชื่อหน่วยงานและเลขประจำตัวผู้เสียภาษีอากร จะต้องถูกต้องครบตัวอักษร'
    }
    
    # 4. Make the request
    headers = {'X-API-Key': api_key}
    
    try:
        logger.info(f"📤 [KYS OCR] กำลังส่งไฟล์ไปยัง AksonOCR API: {file_path_obj.name}")
        
        with open(file_path_obj, 'rb') as file:
            files = {'file': (file_path_obj.name, file, 'application/pdf')}
            
            response = requests.post(
                API_URL, 
                headers=headers, 
                data=payload, 
                files=files, 
                timeout=120  # เพิ่ม timeout เป็น 120 วินาที
            )
            
            logger.info(f"📥 [KYS OCR] Status Code: {response.status_code}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info("✅ [KYS OCR] สำเร็จ!")
                
                # Extract data from response
                if 'success' in result and result.get('success'):
                    data = result.get('data', {})
                    
                    # Extract fields - API ส่งมาเป็น dict ของ key-value โดยตรง
                    # เช่น { "ชื่อหน่วยงาน": "บริษัท...", ... }
                    fields_data = {}
                    if isinstance(data, dict):
                        # ถ้า data เป็น dict โดยตรง (กรณีที่ API ส่งมาเป็น key-value)
                        if any('ชื่อหน่วยงาน' in key or 'เลขประจำตัวผู้เสียภาษีอากร' in key or 'กยศ.' in key or 'ยอดชำระ' in key for key in data.keys()):
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
                
                logger.error(f"❌ [KYS OCR] Error: {error_msg}")
                
                return {
                    'success': False,
                    'data': {},
                    'raw_response': {},
                    'error': error_msg
                }
                
    except requests.exceptions.Timeout:
        error_msg = 'Request timeout (เกิน 120 วินาที)'
        logger.error(f"❌ [KYS OCR] {error_msg}")
        return {
            'success': False,
            'data': {},
            'raw_response': {},
            'error': error_msg
        }
    except requests.exceptions.RequestException as e:
        error_msg = f'Network Error: {str(e)}'
        logger.error(f"❌ [KYS OCR] {error_msg}")
        return {
            'success': False,
            'data': {},
            'raw_response': {},
            'error': error_msg
        }
    except Exception as e:
        error_msg = f'Unexpected Error: {str(e)}'
        logger.error(f"❌ [KYS OCR] {error_msg}", exc_info=True)
        return {
            'success': False,
            'data': {},
            'raw_response': {},
            'error': error_msg
        }


def parse_kys_data(ocr_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse ข้อมูลจาก OCR result ให้เป็นรูปแบบที่ใช้งานได้
    
    Args:
        ocr_result: ผลลัพธ์จาก process_kys_ocr()
    
    Returns:
        Dictionary containing parsed data:
        {
            'company_name': str,  # ชื่อหน่วยงาน
            'tax_id': str,  # เลขประจำตัวผู้เสียภาษีอากร (ไม่เว้นวรรค)
            'payment_month': str,  # ชำระเงินของเดือน (mm/yyyy)
            'due_date': str,  # วันที่ครบกำหนดชำระเงิน (dd/mm/yyyy)
            'payment_amount': float,  # ยอดชำระ (บาท)
            'tax_form_type': 'กยศ.',
            'success': bool,
            'error': str or None
        }
    """
    if not ocr_result.get('success'):
        return {
            'company_name': '',
            'tax_id': '',
            'payment_month': '',
            'due_date': '',
            'payment_amount': 0.00,
            'tax_form_type': 'กยศ.',
            'success': False,
            'error': ocr_result.get('error', 'Unknown error')
        }
    
    # Extract fields - ข้อมูลอยู่ใน ocr_result['data'] โดยตรง
    # process_kys_ocr จะส่ง fields_data โดยตรง (ไม่ wrap อีกชั้น)
    fields = ocr_result.get('data', {})
    
    # ตรวจสอบว่า fields เป็น dict หรือไม่
    if not isinstance(fields, dict):
        fields = {}
    
    # Parse ข้อมูลหน่วยงาน
    company_name = fields.get('ชื่อหน่วยงาน', '').strip() if fields.get('ชื่อหน่วยงาน') else ''
    
    # Parse เลขประจำตัวผู้เสียภาษีอากร
    # สำหรับ กยศ.: ใช้ค่าตามที่อ่านได้จาก JSON (ไม่ format)
    tax_id = fields.get('เลขประจำตัวผู้เสียภาษีอากร', '').strip() if fields.get('เลขประจำตัวผู้เสียภาษีอากร') else ''
    # ไม่ต้องลบ dash หรือช่องว่าง เพราะต้องการใช้ค่าตามที่อ่านได้
    
    # Parse ชำระเงินของเดือน (mm/yyyy)
    payment_month = ''
    payment_month_str = fields.get('ชำระเงินของเดือน ', '')
    if payment_month_str:
        # ลองหา pattern mm/yyyy หรือ mm-yyyy
        month_patterns = [
            r'(\d{1,2})[/-](\d{4})',  # mm/yyyy หรือ mm-yyyy
        ]
        
        for pattern in month_patterns:
            match = re.search(pattern, str(payment_month_str))
            if match:
                if len(match.groups()) == 2:
                    month, year = match.groups()
                    payment_month = f"{month.zfill(2)}/{year}"
                    break
        
        # ถ้ายังหาไม่เจอ ให้เก็บค่าเดิม
        if not payment_month:
            payment_month = str(payment_month_str).strip()
    
    # Parse วันที่ครบกำหนดชำระเงิน (dd/mm/yyyy)
    due_date = ''
    due_date_str = fields.get('วันที่ครบกำหนดชำระเงิน', '')
    if due_date_str:
        # ลองหา pattern วันที่ dd/mm/yyyy หรือ dd-mm-yyyy หรือรูปแบบอื่นๆ
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
                        due_date = f"{day.zfill(2)}/{month.zfill(2)}/{year}"
                    else:
                        day, month, year = match.groups()
                        due_date = f"{day.zfill(2)}/{month.zfill(2)}/{year}"
                    break
        
        # ถ้ายังหาไม่เจอ ให้เก็บค่าเดิม
        if not due_date:
            due_date = str(due_date_str).strip()
    
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
    
    # สร้าง amounts dictionary สำหรับส่งไป frontend
    amounts = {
        'ยอดชำระ (บาท)': payment_amount
    }
    
    return {
        'company_name': company_name,
        'tax_id': tax_id,  # ใช้ค่าตามที่อ่านได้ (ไม่ format)
        'payment_month': payment_month,
        'due_date': due_date,
        'payment_amount': payment_amount,
        'tax_form_type': 'กยศ.',
        'success': True,
        'error': None,
        'raw_fields': fields,  # เก็บข้อมูลดิบไว้ด้วย
        'amounts': amounts  # เพิ่ม amounts dictionary สำหรับส่งไป frontend
    }


if __name__ == "__main__":
    # Test function
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python kys_ocr_processor.py <pdf_file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    print("=" * 70)
    print("🧪 ทดสอบ KYS OCR Processor")
    print("=" * 70)
    print(f"📄 ไฟล์: {file_path}")
    print("-" * 70)
    
    # Process OCR
    result = process_kys_ocr(file_path)
    
    if result['success']:
        print("✅ OCR สำเร็จ!")
        print("-" * 70)
        
        # Parse data
        parsed = parse_kys_data(result)
        
        print("\n📋 ข้อมูลที่ Extract ได้:")
        print("-" * 70)
        
        # แสดงข้อมูลหน่วยงาน
        if parsed.get('company_name'):
            print(f"  🏢 ชื่อหน่วยงาน: {parsed['company_name']}")
        if parsed.get('tax_id'):
            print(f"  🆔 เลขประจำตัวผู้เสียภาษีอากร: {parsed['tax_id']}")
        if parsed.get('payment_month'):
            print(f"  📅 ชำระเงินของเดือน: {parsed['payment_month']}")
        if parsed.get('due_date'):
            print(f"  📅 วันที่ครบกำหนดชำระเงิน: {parsed['due_date']}")
        if parsed.get('payment_amount'):
            print(f"  💰 ยอดชำระ: {parsed['payment_amount']:,.2f} บาท")
        
        print("\n📄 Raw Fields:")
        print("-" * 70)
        for key, value in parsed.get('raw_fields', {}).items():
            if value:
                print(f"  • {key}: {value}")
    else:
        print(f"❌ OCR ไม่สำเร็จ: {result.get('error', 'Unknown error')}")
    
    print("=" * 70)
