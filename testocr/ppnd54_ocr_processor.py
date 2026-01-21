"""
OCR Processor สำหรับแบบภาษี ภ.ง.ด.54 โดยเฉพาะ
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


def get_ppnd54_custom_fields() -> list:
    """
    สร้าง custom fields สำหรับ AksonOCR key-extract API สำหรับแบบภาษี ภ.ง.ด.54
    
    Returns:
        List of custom field dictionaries
    """
    return [
        {
            "key": "ภ.ง.ด.54",
            "description": "ค้นหาคำว่า ภ.ง.ด.54 หรือ ภ.ง.ด. 54 ว่ามีไหม",
            "example": "ภ.ง.ด.54"
        },
        {
            "key": "ชื่อบริษัท",
            "description": "",
            "example": ""
        },
        {
            "key": "เลขประจำตัวผู้เสียภาษีอากร",
            "description": "",
            "example": "0105564065416"
        },
        {
            "key": "ที่อยู่",
            "description": "",
            "example": ""
        },
        {
            "key": "(1) ยื่นปกติ",
            "description": "",
            "example": "ยื่นปกติ"
        },
        {
            "key": "(2) ยื่นเพิ่มเติมครั้งที่",
            "description": "ดูว่ายื่นเพิ่มเติมครั้งที่เท่าไหร่",
            "example": "ยื่นเพิ่มเติมครั้งที่ 1"
        },
        {
            "key": "1. ประเภทเงินได้ที่จ่าย",
            "description": "(ทำเครื่องหมาย \"      \" ลงในช่อง \"      \" ตามประเภทเงินได้ที่จ่าย)",
            "example": "(2) ค่าสิทธิในงานวรรณกรรม ศิลปะ และวิทยาศาสตร์ ตามมาตรา 40(3)"
        },
        {
            "key": "3. วันเดือนปีที่จ่ายเงินได้ซึ่งต้องหักภาษีจากเงินได้ที่จ่ายตามมาตรา 70",
            "description": "ดึงข้อมูลให้ออกมาเป็นรูปแบบวันที่ dd/mm/yyyy",
            "example": "14/11/2025"
        },
        {
            "key": "(1) เงินได้พึงประเมิน",
            "description": "",
            "example": "0.00"
        },
        {
            "key": "(2) เงินภาษีที่นำส่งในอัตรา",
            "description": "ให้ดึงข้อมูลในจำนวนเงิน",
            "example": "0.00"
        },
        {
            "key": "(3) เงินเพิ่ม (ถ้ามี)",
            "description": "",
            "example": "0.00"
        },
        {
            "key": "(4) รวมเป็นเงินทั้งสิ้น",
            "description": "",
            "example": ""
        }
    ]


def process_ppnd54_ocr(file_path: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    ประมวลผล OCR สำหรับแบบภาษี ภ.ง.ด.54 โดยใช้ AksonOCR API
    
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
    custom_fields = get_ppnd54_custom_fields()
    
    # 3. Prepare payload
    payload = {
        'customFields': json.dumps(custom_fields),
        'model': 'aksonocr-1.0',
        'additionalInstructions': 'ดึงข้อมูลจากแบบภาษี ภ.ง.ด.54 โดยเน้นความถูกต้องของตัวเลขและวันที่'
    }
    
    # 4. Make the request
    headers = {'X-API-Key': api_key}
    
    try:
        logger.info(f"📤 [PPND54 OCR] กำลังส่งไฟล์ไปยัง AksonOCR API: {file_path_obj.name}")
        
        with open(file_path_obj, 'rb') as file:
            files = {'file': (file_path_obj.name, file, 'application/pdf')}
            
            response = requests.post(
                API_URL, 
                headers=headers, 
                data=payload, 
                files=files, 
                timeout=120  # เพิ่ม timeout เป็น 120 วินาที
            )
            
            logger.info(f"📥 [PPND54 OCR] Status Code: {response.status_code}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info("✅ [PPND54 OCR] สำเร็จ!")
                
                # Extract data from response
                if 'success' in result and result.get('success'):
                    data = result.get('data', {})
                    
                    # Extract fields - API ส่งมาเป็น dict ของ key-value โดยตรง
                    # เช่น { "ชื่อบริษัท": "บริษัท...", ... }
                    fields_data = {}
                    if isinstance(data, dict):
                        # ถ้า data เป็น dict โดยตรง (กรณีที่ API ส่งมาเป็น key-value)
                        if any(key.startswith('(1)') or key.startswith('(2)') or 'ชื่อบริษัท' in key or 'ภ.ง.ด.54' in key for key in data.keys()):
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
                
                logger.error(f"❌ [PPND54 OCR] Error: {error_msg}")
                
                return {
                    'success': False,
                    'data': {},
                    'raw_response': {},
                    'error': error_msg
                }
                
    except requests.exceptions.Timeout:
        error_msg = 'Request timeout (เกิน 120 วินาที)'
        logger.error(f"❌ [PPND54 OCR] {error_msg}")
        return {
            'success': False,
            'data': {},
            'raw_response': {},
            'error': error_msg
        }
    except requests.exceptions.RequestException as e:
        error_msg = f'Network Error: {str(e)}'
        logger.error(f"❌ [PPND54 OCR] {error_msg}")
        return {
            'success': False,
            'data': {},
            'raw_response': {},
            'error': error_msg
        }
    except Exception as e:
        error_msg = f'Unexpected Error: {str(e)}'
        logger.error(f"❌ [PPND54 OCR] {error_msg}", exc_info=True)
        return {
            'success': False,
            'data': {},
            'raw_response': {},
            'error': error_msg
        }


def parse_ppnd54_data(ocr_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse ข้อมูลจาก OCR result ให้เป็นรูปแบบที่ใช้งานได้
    
    Args:
        ocr_result: ผลลัพธ์จาก process_ppnd54_ocr()
    
    Returns:
        Dictionary containing parsed data:
        {
            'amounts': dict,  # ข้อมูล 4 ข้อ
            'company_name': str,
            'tax_id': str,
            'address': str,
            'filing_type': str,  # 'normal' or 'additional'
            'filing_additional_number': str or None,
            'income_type': str,  # ประเภทเงินได้ที่จ่าย
            'payment_date': str,  # วันเดือนปีที่จ่ายเงินได้ (dd/mm/yyyy)
            'tax_form_type': 'ภ.ง.ด.54',
            'success': bool,
            'error': str or None
        }
    """
    if not ocr_result.get('success'):
        return {
            'amounts': {},
            'company_name': '',
            'tax_id': '',
            'address': '',
            'filing_type': '',
            'filing_additional_number': None,
            'income_type': '',
            'payment_date': '',
            'tax_form_type': 'ภ.ง.ด.54',
            'success': False,
            'error': ocr_result.get('error', 'Unknown error')
        }
    
    # Extract fields - ข้อมูลอยู่ใน ocr_result['data'] โดยตรง
    # process_ppnd54_ocr จะส่ง fields_data โดยตรง (ไม่ wrap อีกชั้น)
    fields = ocr_result.get('data', {})
    
    # ตรวจสอบว่า fields เป็น dict หรือไม่
    if not isinstance(fields, dict):
        fields = {}
    
    # Parse amounts (4 items)
    amounts = {}
    
    # Mapping keys สำหรับยอดเงิน
    key_mapping = {
        '(1) เงินได้พึงประเมิน': 'เงินได้พึงประเมิน (ภ.ง.ด.54)',
        '(2) เงินภาษีที่นำส่งในอัตรา': 'เงินภาษีที่นำส่งในอัตรา (ภ.ง.ด.54)',
        '(3) เงินเพิ่ม (ถ้ามี)': 'เงินเพิ่ม (ภ.ง.ด.54)',
        '(4) รวมเป็นเงินทั้งสิ้น': 'รวมเป็นเงินทั้งสิ้น (ภ.ง.ด.54)',
    }
    
    # Parse และแปลงค่า
    for original_key, mapped_key in key_mapping.items():
        value = fields.get(original_key, '')
        
        # ถ้า value เป็น None ให้แปลงเป็น empty string
        if value is None:
            value = ''
        
        if not value or value == '-' or value == '':
            amounts[mapped_key] = 0.00
        else:
            # ลบ comma และ whitespace
            clean_value = str(value).replace(',', '').replace(' ', '').strip()
            
            # หาตัวเลข (รองรับทศนิยม)
            match = re.search(r'(\d+\.?\d*)', clean_value)
            if match:
                try:
                    amounts[mapped_key] = float(match.group(1))
                except ValueError:
                    amounts[mapped_key] = 0.00
            else:
                amounts[mapped_key] = 0.00
    
    # Parse ข้อมูลบริษัท
    company_name = fields.get('ชื่อบริษัท', '').strip() if fields.get('ชื่อบริษัท') else ''
    tax_id = fields.get('เลขประจำตัวผู้เสียภาษีอากร', '').strip() if fields.get('เลขประจำตัวผู้เสียภาษีอากร') else ''
    # สำหรับ ภ.ง.ด.54: ใช้ค่าตามที่อ่านได้จาก JSON (ไม่ format)
    # ไม่ต้องลบ dash หรือช่องว่าง เพราะต้องการใช้ค่าตามที่อ่านได้
    address = fields.get('ที่อยู่', '').strip() if fields.get('ที่อยู่') else ''
    
    # Parse การยื่นแบบ
    # สำหรับ ภ.ง.ด.54: ใช้ค่าตามที่อ่านได้จาก JSON (เช่น "ยื่นปกติ" หรือ "1", "2", ...)
    filing_type = ''
    filing_additional_number = None
    
    # ตรวจสอบว่าอันไหนมีข้อมูล (ไม่เป็น null) แล้วดึงข้อมูลนั้นมาใช้
    filing_normal = fields.get('(1) ยื่นปกติ', '')
    filing_additional = fields.get('(2) ยื่นเพิ่มเติมครั้งที่', '')
    
    if filing_normal and filing_normal is not None and filing_normal != 'null' and str(filing_normal).strip():
        # ถ้า "(1) ยื่นปกติ" มีข้อมูล (ไม่เป็น null) ให้ใช้ค่าจาก JSON โดยตรง
        filing_type = str(filing_normal).strip()  # เช่น "ยื่นปกติ"
    elif filing_additional and filing_additional is not None and filing_additional != 'null' and str(filing_additional).strip():
        # ถ้า "(2) ยื่นเพิ่มเติมครั้งที่" มีข้อมูล (ไม่เป็น null) ให้ใช้ค่าจาก JSON โดยตรง
        filing_type = str(filing_additional).strip()  # เช่น "1", "2", หรือข้อความอื่นๆ
        # หาเลขครั้งที่ (ถ้ามี)
        additional_match = re.search(r'(\d+)', str(filing_additional))
        if additional_match:
            filing_additional_number = additional_match.group(1)
    
    # Parse ประเภทเงินได้ที่จ่าย
    income_type = fields.get('1. ประเภทเงินได้ที่จ่าย', '').strip() if fields.get('1. ประเภทเงินได้ที่จ่าย') else ''
    
    # Parse วันเดือนปีที่จ่ายเงินได้
    payment_date = ''
    payment_date_str = fields.get('3. วันเดือนปีที่จ่ายเงินได้ซึ่งต้องหักภาษีจากเงินได้ที่จ่ายตามมาตรา 70', '')
    if payment_date_str:
        # ลองหา pattern วันที่ dd/mm/yyyy หรือ dd-mm-yyyy หรือรูปแบบอื่นๆ
        date_patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # dd/mm/yyyy หรือ dd-mm-yyyy
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # yyyy/mm/dd หรือ yyyy-mm-dd
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, str(payment_date_str))
            if match:
                if len(match.groups()) == 3:
                    # ถ้าเป็นรูปแบบ yyyy/mm/dd ให้แปลงเป็น dd/mm/yyyy
                    if len(match.group(1)) == 4:
                        year, month, day = match.groups()
                        payment_date = f"{day.zfill(2)}/{month.zfill(2)}/{year}"
                    else:
                        day, month, year = match.groups()
                        payment_date = f"{day.zfill(2)}/{month.zfill(2)}/{year}"
                    break
        
        # ถ้ายังหาไม่เจอ ให้เก็บค่าเดิม
        if not payment_date:
            payment_date = str(payment_date_str).strip()
    
    # สร้าง ppnd54_json structure สำหรับส่งไป frontend
    ppnd54_json = {
        'data': fields  # ส่งข้อมูลดิบทั้งหมดไปให้ frontend
    }
    
    return {
        'amounts': amounts,
        'company_name': company_name,
        'tax_id': tax_id,  # ใช้ค่าตามที่อ่านได้ (ไม่ format)
        'address': address,
        'filing_type': filing_type,  # ใช้ค่าตามที่อ่านได้ (เช่น "ยื่นปกติ")
        'filing_additional_number': filing_additional_number,
        'income_type': income_type,
        'payment_date': payment_date,
        'tax_form_type': 'ภ.ง.ด.54',
        'success': True,
        'error': None,
        'raw_fields': fields,  # เก็บข้อมูลดิบไว้ด้วย
        'ppnd54_json': ppnd54_json  # ส่ง JSON structure ใหม่ไปให้ frontend
    }


if __name__ == "__main__":
    # Test function
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python ppnd54_ocr_processor.py <pdf_file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    print("=" * 70)
    print("🧪 ทดสอบ PPND54 OCR Processor")
    print("=" * 70)
    print(f"📄 ไฟล์: {file_path}")
    print("-" * 70)
    
    # Process OCR
    result = process_ppnd54_ocr(file_path)
    
    if result['success']:
        print("✅ OCR สำเร็จ!")
        print("-" * 70)
        
        # Parse data
        parsed = parse_ppnd54_data(result)
        
        print("\n📋 ข้อมูลที่ Extract ได้:")
        print("-" * 70)
        
        # แสดงข้อมูลบริษัท
        if parsed.get('company_name'):
            print(f"  🏢 ชื่อบริษัท: {parsed['company_name']}")
        if parsed.get('tax_id'):
            print(f"  🆔 เลขประจำตัวผู้เสียภาษีอากร: {parsed['tax_id']}")
        if parsed.get('address'):
            print(f"  📍 ที่อยู่: {parsed['address']}")
        
        # แสดงข้อมูลการยื่นแบบ
        filing_type = parsed.get('filing_type')
        if filing_type:
            if filing_type == 'normal':
                print(f"  📝 การยื่นแบบ: ยื่นปกติ")
            elif filing_type == 'additional':
                additional_num = parsed.get('filing_additional_number')
                if additional_num:
                    print(f"  📝 การยื่นแบบ: ยื่นเพิ่มเติม ครั้งที่ {additional_num}")
                else:
                    print(f"  📝 การยื่นแบบ: ยื่นเพิ่มเติม")
        
        # แสดงประเภทเงินได้ที่จ่าย
        if parsed.get('income_type'):
            print(f"  💼 ประเภทเงินได้ที่จ่าย: {parsed['income_type']}")
        
        # แสดงวันเดือนปีที่จ่ายเงินได้
        if parsed.get('payment_date'):
            print(f"  📅 วันเดือนปีที่จ่ายเงินได้: {parsed['payment_date']}")
        
        # แสดงข้อมูลยอดเงิน
        print("\n💰 ยอดเงิน:")
        print("-" * 70)
        for key, value in parsed['amounts'].items():
            print(f"  • {key}: {value:,.2f}")
        
        print("\n📄 Raw Fields:")
        print("-" * 70)
        for key, value in parsed.get('raw_fields', {}).items():
            if value:
                print(f"  • {key}: {value}")
    else:
        print(f"❌ OCR ไม่สำเร็จ: {result.get('error', 'Unknown error')}")
    
    print("=" * 70)
