"""
OCR Processor สำหรับแบบภาษี ภ.พ.36 โดยเฉพาะ
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


def get_pp36_custom_fields() -> list:
    """
    สร้าง custom fields สำหรับ AksonOCR key-extract API สำหรับแบบภาษี ภ.พ.36
    
    Returns:
        List of custom field dictionaries
    """
    return [
        {
            "key": "ภ.พ.36",
            "description": "ค้นหาคำว่า ภ.พ.36 หรือ ภ.พ. 36 ว่ามีไหม",
            "example": "ภ.พ.36"
        },
        {
            "key": "ชื่อบริษัท",
            "description": "",
            "example": ""
        },
        {
            "key": "เลขประจำตัวผู้เสียภาษีอากร",
            "description": "ดึงข้อมูลแบบที่ไม่ต้องมีเว้นวรรค",
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
            "key": "วัน เดือน ปีที่จ่ายเงิน",
            "description": "ให้แสดงผลลัพธ์ออกมาในรูปแบบของ dd/mm/yyyy",
            "example": "01/11/2568"
        },
        {
            "key": "1. จำนวนที่จ่ายเงิน",
            "description": "",
            "example": "0.00"
        },
        {
            "key": "2. จำนวนเงินภาษีมูลค่าเพิ่มที่ต้องนำส่ง",
            "description": "",
            "example": "0.00"
        },
        {
            "key": "3. เงินเพิ่ม",
            "description": "",
            "example": "0.00"
        },
        {
            "key": "4. เบี้ยปรับ (ถ้ามี (เฉพาะกรณีรับโอนสินค้าหรือรับโอนสิทธิในบริการที่ได้เสียภาษีในอัตราร้อยละ 0))",
            "description": "",
            "example": "0.00"
        },
        {
            "key": "5.  รวมภาษีมูลค่าเพิ่มที่ต้องนำส่ง เงินเพิ่ม และเบี้ยปรับ (2. + 3. + 4.)",
            "description": "",
            "example": "0.00"
        }
    ]


def process_pp36_ocr(file_path: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    ประมวลผล OCR สำหรับแบบภาษี ภ.พ.36 โดยใช้ AksonOCR API
    
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
    custom_fields = get_pp36_custom_fields()
    
    # 3. Prepare payload
    payload = {
        'customFields': json.dumps(custom_fields),
        'model': 'aksonocr-1.0',
        'additionalInstructions': 'ดึงข้อมูลจากแบบภาษี ภ.พ.36 โดยเน้นความถูกต้องของตัวเลขและวันที่'
    }
    
    # 4. Make the request
    headers = {'X-API-Key': api_key}
    
    try:
        logger.info(f"📤 [PP36 OCR] กำลังส่งไฟล์ไปยัง AksonOCR API: {file_path_obj.name}")
        
        with open(file_path_obj, 'rb') as file:
            files = {'file': (file_path_obj.name, file, 'application/pdf')}
            
            response = requests.post(
                API_URL, 
                headers=headers, 
                data=payload, 
                files=files, 
                timeout=120  # เพิ่ม timeout เป็น 120 วินาที
            )
            
            logger.info(f"📥 [PP36 OCR] Status Code: {response.status_code}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info("✅ [PP36 OCR] สำเร็จ!")
                
                # Extract data from response
                if 'success' in result and result.get('success'):
                    data = result.get('data', {})
                    
                    # Extract fields - API ส่งมาเป็น dict ของ key-value โดยตรง
                    # เช่น { "ชื่อบริษัท": "บริษัท...", ... }
                    fields_data = {}
                    if isinstance(data, dict):
                        # ถ้า data เป็น dict โดยตรง (กรณีที่ API ส่งมาเป็น key-value)
                        if any(key.startswith('1.') or key.startswith('2.') or 'ชื่อบริษัท' in key or 'ภ.พ.36' in key for key in data.keys()):
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
                
                logger.error(f"❌ [PP36 OCR] Error: {error_msg}")
                
                return {
                    'success': False,
                    'data': {},
                    'raw_response': {},
                    'error': error_msg
                }
                
    except requests.exceptions.Timeout:
        error_msg = 'Request timeout (เกิน 120 วินาที)'
        logger.error(f"❌ [PP36 OCR] {error_msg}")
        return {
            'success': False,
            'data': {},
            'raw_response': {},
            'error': error_msg
        }
    except requests.exceptions.RequestException as e:
        error_msg = f'Network Error: {str(e)}'
        logger.error(f"❌ [PP36 OCR] {error_msg}")
        return {
            'success': False,
            'data': {},
            'raw_response': {},
            'error': error_msg
        }
    except Exception as e:
        error_msg = f'Unexpected Error: {str(e)}'
        logger.error(f"❌ [PP36 OCR] {error_msg}", exc_info=True)
        return {
            'success': False,
            'data': {},
            'raw_response': {},
            'error': error_msg
        }


def parse_pp36_data(ocr_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse ข้อมูลจาก OCR result ให้เป็นรูปแบบที่ใช้งานได้
    
    Args:
        ocr_result: ผลลัพธ์จาก process_pp36_ocr()
    
    Returns:
        Dictionary containing parsed data:
        {
            'amounts': dict,  # ข้อมูล 5 ข้อ
            'company_name': str,
            'tax_id': str,
            'address': str,
            'filing_type': str,  # 'normal' or 'additional'
            'filing_additional_number': str or None,
            'payment_date': str,  # วันเดือนปีที่จ่ายเงิน (dd/mm/yyyy)
            'tax_form_type': 'ภ.พ.36',
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
            'payment_date': '',
            'tax_form_type': 'ภ.พ.36',
            'success': False,
            'error': ocr_result.get('error', 'Unknown error')
        }
    
    # Extract fields - ข้อมูลอยู่ใน ocr_result['data'] โดยตรง
    # process_pp36_ocr จะส่ง fields_data โดยตรง (ไม่ wrap อีกชั้น)
    fields = ocr_result.get('data', {})
    
    # ตรวจสอบว่า fields เป็น dict หรือไม่
    if not isinstance(fields, dict):
        fields = {}
    
    # Parse amounts (5 items)
    amounts = {}
    
    # Mapping keys สำหรับยอดเงิน
    key_mapping = {
        '1. จำนวนที่จ่ายเงิน': 'จำนวนที่จ่ายเงิน (ภ.พ.36)',
        '2. จำนวนเงินภาษีมูลค่าเพิ่มที่ต้องนำส่ง': 'จำนวนเงินภาษีมูลค่าเพิ่มที่ต้องนำส่ง (ภ.พ.36)',
        '3. เงินเพิ่ม': 'เงินเพิ่ม (ภ.พ.36)',
        '4. เบี้ยปรับ (ถ้ามี (เฉพาะกรณีรับโอนสินค้าหรือรับโอนสิทธิในบริการที่ได้เสียภาษีในอัตราร้อยละ 0))': 'เบี้ยปรับ (ภ.พ.36)',
        '5.  รวมภาษีมูลค่าเพิ่มที่ต้องนำส่ง เงินเพิ่ม และเบี้ยปรับ (2. + 3. + 4.)': 'รวมภาษีมูลค่าเพิ่มที่ต้องนำส่ง เงินเพิ่ม และเบี้ยปรับ (ภ.พ.36)',
    }
    
    # Parse และแปลงค่า
    # สำหรับ ภ.พ.36: 2 หลักสุดท้ายจะเป็นเศษสตางค์เสมอ
    for original_key, mapped_key in key_mapping.items():
        value = fields.get(original_key, '')
        
        # ถ้า value เป็น None ให้แปลงเป็น empty string
        if value is None:
            value = ''
        
        if not value or value == '-' or value == '':
            amounts[mapped_key] = 0.00
        else:
            # รูปแบบ: "28,108 38" -> แยกเป็น "28,108" (ส่วนหลัก) และ "38" (เศษสตางค์ 2 หลัก)
            # ผลลัพธ์: 28,108.38
            # รูปแบบ: "1,967 59" -> แยกเป็น "1,967" (ส่วนหลัก) และ "59" (เศษสตางค์ 2 หลัก)
            # ผลลัพธ์: 1,967.59
            
            value_str = str(value).strip()
            
            # แยกส่วนหลักและส่วนทศนิยม (2 หลักสุดท้าย)
            parts = value_str.split()
            
            if len(parts) >= 2:
                # มีช่องว่างแยกส่วนหลักและส่วนทศนิยม
                main_part = parts[-2].replace(',', '').replace(' ', '')  # ส่วนหลัก (ลบ comma และช่องว่าง)
                decimal_part = parts[-1]  # ส่วนทศนิยม (2 หลักสุดท้าย)
                
                # ตรวจสอบว่า decimal_part เป็นตัวเลข 2 หลักหรือไม่
                if decimal_part.isdigit() and len(decimal_part) == 2:
                    try:
                        amounts[mapped_key] = float(main_part + '.' + decimal_part)
                    except ValueError:
                        amounts[mapped_key] = 0.00
                else:
                    # ถ้าไม่ใช่ 2 หลัก ให้ลอง parse แบบเดิม
                    clean_value = value_str.replace(',', '').replace(' ', '').strip()
                    match = re.search(r'(\d+\.?\d*)', clean_value)
                    if match:
                        try:
                            amounts[mapped_key] = float(match.group(1))
                        except ValueError:
                            amounts[mapped_key] = 0.00
                    else:
                        amounts[mapped_key] = 0.00
            else:
                # ถ้าไม่มีช่องว่างแยก หรือรูปแบบไม่ถูกต้อง ให้ลอง parse แบบเดิม
                clean_value = value_str.replace(',', '').replace(' ', '').strip()
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
    # สำหรับ ภ.พ.36: ใช้ค่าตามที่อ่านได้จาก JSON (ไม่ format)
    # ไม่ต้องลบ dash หรือช่องว่าง เพราะต้องการใช้ค่าตามที่อ่านได้
    address = fields.get('ที่อยู่', '').strip() if fields.get('ที่อยู่') else ''
    
    # Parse การยื่นแบบ
    filing_type = ''
    filing_additional_number = None
    
    # ตรวจสอบว่ายื่นปกติหรือยื่นเพิ่มเติม
    # สำหรับ ภ.พ.36: ใช้ค่าตามที่อ่านได้จาก JSON (เช่น "ยื่นปกติ" หรือ "1", "2", ...)
    filing_normal = fields.get('(1) ยื่นปกติ', '')
    filing_additional = fields.get('(2) ยื่นเพิ่มเติมครั้งที่', '')
    
    # ตรวจสอบว่าอันไหนมีข้อมูล (ไม่เป็น null) แล้วดึงข้อมูลนั้นมาใช้
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
    
    # Parse วันเดือนปีที่จ่ายเงิน
    payment_date = ''
    payment_date_str = fields.get('วัน เดือน ปีที่จ่ายเงิน', '')
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
    
    # สร้าง pp36_json structure สำหรับส่งไป frontend
    pp36_json = {
        'data': fields  # ส่งข้อมูลดิบทั้งหมดไปให้ frontend
    }
    
    return {
        'amounts': amounts,
        'company_name': company_name,
        'tax_id': tax_id,  # ใช้ค่าตามที่อ่านได้ (ไม่ format)
        'address': address,
        'filing_type': filing_type,
        'filing_additional_number': filing_additional_number,
        'payment_date': payment_date,
        'tax_form_type': 'ภ.พ.36',
        'success': True,
        'error': None,
        'raw_fields': fields,  # เก็บข้อมูลดิบไว้ด้วย
        'pp36_json': pp36_json  # ส่ง JSON structure ใหม่ไปให้ frontend
    }


if __name__ == "__main__":
    # Test function
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python pp36_ocr_processor.py <pdf_file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    print("=" * 70)
    print("🧪 ทดสอบ PP36 OCR Processor")
    print("=" * 70)
    print(f"📄 ไฟล์: {file_path}")
    print("-" * 70)
    
    # Process OCR
    result = process_pp36_ocr(file_path)
    
    if result['success']:
        print("✅ OCR สำเร็จ!")
        print("-" * 70)
        
        # Parse data
        parsed = parse_pp36_data(result)
        
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
        
        # แสดงวันเดือนปีที่จ่ายเงิน
        if parsed.get('payment_date'):
            print(f"  📅 วันเดือนปีที่จ่ายเงิน: {parsed['payment_date']}")
        
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
