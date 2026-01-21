"""
OCR Processor สำหรับแบบภาษี ภ.ง.ด.1 โดยเฉพาะ
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


def get_ppnd1_custom_fields() -> list:
    """
    สร้าง custom fields สำหรับ AksonOCR key-extract API สำหรับแบบภาษี ภ.ง.ด.1
    
    Returns:
        List of custom field dictionaries
    """
    return [
        {
            "key": "ภ.ง.ด.1",
            "description": "ค้นหาคำว่า ภ.ง.ด.1 หรือ ภ.ง.ด. 1 ว่ามีไหม",
            "example": "ภ.ง.ด.1"
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
            "key": "เลขที่ใบเสร็จ",
            "description": "",
            "example": ""
        },
        {
            "key": "วันที่:",
            "description": "",
            "example": ""
        },
        {
            "key": "(1) ยื่นปกติ",
            "description": "",
            "example": "ยื่นแแบบปกติ"
        },
        {
            "key": "(2) ยื่นเพิ่มเติมครั้งที่",
            "description": "ดูว่ายื่นเพิ่มเติมครั้งที่เท่าไหร่",
            "example": "ยื่นเพิ่มเติมครั้งที่ 1"
        },
        {
            "key": "พ.ศ.",
            "description": "",
            "example": ""
        },
        {
            "key": "เดือนภาษี",
            "description": "",
            "example": "ธันวาคม"
        },
        {
            "key": "1. เงินได้ตามมาตรา 40 (1) เงินเดือน ค่าจ้าง ฯลฯ กรณีทั่วไป",
            "description": "ดึงข้อมูลในส่วนของ ภาษีที่นำส่งทั้งสิ้น",
            "example": "0.00"
        },
        {
            "key": "2. เงินได้ตามมาตรา 40 (1)เงินเดือน ค่าจ้าง ฯลฯ กรณีได้รับ อนุมัติจากกรมสรรพากรให้หักอัตรา ร้อยละ 3",
            "description": "ดึงข้อมูลในส่วนของ ภาษีที่นำส่งทั้งสิ้น",
            "example": "0.00"
        },
        {
            "key": "3. เงินได้ตาม มาตรา 40 (1) (2) กรณีนายจ้างจ่ายให้ครั้งเดียว เพราะเหตุออกจากงาน",
            "description": "ดึงข้อมูลในส่วนของ ภาษีที่นำส่งทั้งสิ้น",
            "example": "0.00"
        },
        {
            "key": "4. เงินได้ตามมาตรา 40 (2)กรณีผู้รับเงินได้เป็นผู้อยู่ในประเทศไทย",
            "description": "ดึงข้อมูลในส่วนของ ภาษีที่นำส่งทั้งสิ้น",
            "example": "0.00"
        },
        {
            "key": "5. เงินได้ตามมาตรา 40 (2)กรณีผู้รับเงินได้มิได้เป็นผู้อยู่ในประเทศไทย",
            "description": "ดึงข้อมูลในส่วนของ ภาษีที่นำส่งทั้งสิ้น",
            "example": "0.00"
        },
        {
            "key": "6. รวม",
            "description": "ดึงข้อมูลในส่วนของ ภาษีที่นำส่งทั้งสิ้น",
            "example": "0.00"
        },
        {
            "key": "7. เงินเพิ่ม (ถ้ามี)",
            "description": "ดึงข้อมูลในส่วนของ ภาษีที่นำส่งทั้งสิ้น",
            "example": "0.00"
        },
        {
            "key": "8. รวมยอดภาษีที่นำส่งทั้งสิ้น และเงินเพิ่ม (6.+7.)",
            "description": "ดึงข้อมูลในส่วนของ ภาษีที่นำส่งทั้งสิ้น",
            "example": "0.00"
        }
    ]


def process_ppnd1_ocr(file_path: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    ประมวลผล OCR สำหรับแบบภาษี ภ.ง.ด.1 โดยใช้ AksonOCR API
    
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
    custom_fields = get_ppnd1_custom_fields()
    
    # 3. Prepare payload
    payload = {
        'customFields': json.dumps(custom_fields),
        'model': 'aksonocr-1.0',
        'additionalInstructions': 'ดึงข้อมูลจากแบบภาษี ภ.ง.ด.1 โดยเน้นความถูกต้องของตัวเลขและวันที่'
    }
    
    # 4. Make the request
    headers = {'X-API-Key': api_key}
    
    try:
        logger.info(f"📤 [PPND1 OCR] กำลังส่งไฟล์ไปยัง AksonOCR API: {file_path_obj.name}")
        
        with open(file_path_obj, 'rb') as file:
            files = {'file': (file_path_obj.name, file, 'application/pdf')}
            
            response = requests.post(
                API_URL, 
                headers=headers, 
                data=payload, 
                files=files, 
                timeout=120  # เพิ่ม timeout เป็น 120 วินาที
            )
            
            logger.info(f"📥 [PPND1 OCR] Status Code: {response.status_code}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info("✅ [PPND1 OCR] สำเร็จ!")
                
                # Extract data from response
                if 'success' in result and result.get('success'):
                    data = result.get('data', {})
                    
                    # Extract fields - API ส่งมาเป็น dict ของ key-value โดยตรง
                    # เช่น { "ชื่อบริษัท": "บริษัท...", ... }
                    fields_data = {}
                    if isinstance(data, dict):
                        # ถ้า data เป็น dict โดยตรง (กรณีที่ API ส่งมาเป็น key-value)
                        if any(key.startswith('1.') or key.startswith('2.') or 'ชื่อบริษัท' in key for key in data.keys()):
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
                
                logger.error(f"❌ [PPND1 OCR] Error: {error_msg}")
                
                return {
                    'success': False,
                    'data': {},
                    'raw_response': {},
                    'error': error_msg
                }
                
    except requests.exceptions.Timeout:
        error_msg = 'Request timeout (เกิน 120 วินาที)'
        logger.error(f"❌ [PPND1 OCR] {error_msg}")
        return {
            'success': False,
            'data': {},
            'raw_response': {},
            'error': error_msg
        }
    except requests.exceptions.RequestException as e:
        error_msg = f'Network Error: {str(e)}'
        logger.error(f"❌ [PPND1 OCR] {error_msg}")
        return {
            'success': False,
            'data': {},
            'raw_response': {},
            'error': error_msg
        }
    except Exception as e:
        error_msg = f'Unexpected Error: {str(e)}'
        logger.error(f"❌ [PPND1 OCR] {error_msg}", exc_info=True)
        return {
            'success': False,
            'data': {},
            'raw_response': {},
            'error': error_msg
        }


def parse_ppnd1_data(ocr_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse ข้อมูลจาก OCR result ให้เป็นรูปแบบที่ใช้งานได้
    
    Args:
        ocr_result: ผลลัพธ์จาก process_ppnd1_ocr()
    
    Returns:
        Dictionary containing parsed data:
        {
            'amounts': dict,  # ข้อมูล 8 ข้อ
            'company_name': str,
            'tax_id': str,
            'address': str,
            'receipt_number': str,
            'date': str,
            'filing_type': str,  # 'normal' or 'additional'
            'filing_additional_number': str or None,
            'year': int,  # พ.ศ.
            'month': int,  # 1-12
            'tax_form_type': 'ภ.ง.ด.1',
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
            'receipt_number': '',
            'date': '',
            'filing_type': '',
            'filing_additional_number': None,
            'year': None,
            'month': None,
            'tax_form_type': 'ภ.ง.ด.1',
            'success': False,
            'error': ocr_result.get('error', 'Unknown error')
        }
    
    # Extract fields - ข้อมูลอยู่ใน ocr_result['data'] โดยตรง
    # process_ppnd1_ocr จะส่ง fields_data โดยตรง (ไม่ wrap อีกชั้น)
    fields = ocr_result.get('data', {})
    
    # ตรวจสอบว่า fields เป็น dict หรือไม่
    if not isinstance(fields, dict):
        fields = {}
    
    # Parse amounts (8 items)
    amounts = {}
    
    # Mapping keys สำหรับยอดเงิน
    key_mapping = {
        '1. เงินได้ตามมาตรา 40 (1) เงินเดือน ค่าจ้าง ฯลฯ กรณีทั่วไป': 'เงินได้ตามมาตรา 40 (1) กรณีทั่วไป (ภ.ง.ด.1)',
        '2. เงินได้ตามมาตรา 40 (1)เงินเดือน ค่าจ้าง ฯลฯ กรณีได้รับ อนุมัติจากกรมสรรพากรให้หักอัตรา ร้อยละ 3': 'เงินได้ตามมาตรา 40 (1) หักอัตราร้อยละ 3 (ภ.ง.ด.1)',
        '3. เงินได้ตาม มาตรา 40 (1) (2) กรณีนายจ้างจ่ายให้ครั้งเดียว เพราะเหตุออกจากงาน': 'เงินได้ตามมาตรา 40 (1) (2) ออกจากงาน (ภ.ง.ด.1)',
        '4. เงินได้ตามมาตรา 40 (2)กรณีผู้รับเงินได้เป็นผู้อยู่ในประเทศไทย': 'เงินได้ตามมาตรา 40 (2) อยู่ในประเทศไทย (ภ.ง.ด.1)',
        '5. เงินได้ตามมาตรา 40 (2)กรณีผู้รับเงินได้มิได้เป็นผู้อยู่ในประเทศไทย': 'เงินได้ตามมาตรา 40 (2) ไม่ได้อยู่ในประเทศไทย (ภ.ง.ด.1)',
        '6. รวม': 'รวม (ภ.ง.ด.1)',
        '7. เงินเพิ่ม (ถ้ามี)': 'เงินเพิ่ม (ภ.ง.ด.1)',
        '8. รวมยอดภาษีที่นำส่งทั้งสิ้น และเงินเพิ่ม (6.+7.)': 'รวมยอดภาษีที่นำส่งทั้งสิ้น และเงินเพิ่ม (ภ.ง.ด.1)',
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
    address = fields.get('ที่อยู่', '').strip() if fields.get('ที่อยู่') else ''
    receipt_number = fields.get('เลขที่ใบเสร็จ', '').strip() if fields.get('เลขที่ใบเสร็จ') else ''
    date = fields.get('วันที่:', '').strip() if fields.get('วันที่:') else ''
    
    # Parse การยื่นแบบ
    filing_type = ''
    filing_additional_number = None
    
    # ตรวจสอบว่ายื่นปกติหรือยื่นเพิ่มเติม
    filing_normal = fields.get('(1) ยื่นปกติ', '')
    filing_additional = fields.get('(2) ยื่นเพิ่มเติมครั้งที่', '')
    
    if filing_normal and (filing_normal.strip().lower() in ['x', '✓', '✔', 'checked', 'true', '1'] or 'ยื่นปกติ' in str(filing_normal)):
        filing_type = 'normal'
    elif filing_additional:
        filing_type = 'additional'
        # หาเลขครั้งที่
        additional_match = re.search(r'(\d+)', str(filing_additional))
        if additional_match:
            filing_additional_number = additional_match.group(1)
    
    # Parse ปี (พ.ศ.)
    year = None
    year_str = fields.get('พ.ศ.', '')
    if year_str:
        year_match = re.search(r'(\d{4})', str(year_str))
        if year_match:
            try:
                year = int(year_match.group(1))
            except ValueError:
                pass
    
    # Parse เดือน
    month = None
    month_str = fields.get('เดือนภาษี', '')
    if month_str:
        # หาเลขเดือน (1-12)
        month_match = re.search(r'(\d{1,2})', str(month_str))
        if month_match:
            try:
                month_num = int(month_match.group(1))
                if 1 <= month_num <= 12:
                    month = month_num
            except ValueError:
                pass
        
        # ถ้ายังหาไม่เจอ ให้ลองหาเดือนจากชื่อเดือน
        if month is None:
            month_names = {
                'มกราคม': 1, 'กุมภาพันธ์': 2, 'มีนาคม': 3, 'เมษายน': 4,
                'พฤษภาคม': 5, 'มิถุนายน': 6, 'กรกฎาคม': 7, 'สิงหาคม': 8,
                'กันยายน': 9, 'ตุลาคม': 10, 'พฤศจิกายน': 11, 'ธันวาคม': 12
            }
            for month_name, month_num in month_names.items():
                if month_name in str(month_str):
                    month = month_num
                    break
    
    return {
        'amounts': amounts,
        'company_name': company_name,
        'tax_id': tax_id,
        'address': address,
        'receipt_number': receipt_number,
        'date': date,
        'filing_type': filing_type,
        'filing_additional_number': filing_additional_number,
        'year': year,
        'month': month,
        'tax_form_type': 'ภ.ง.ด.1',
        'success': True,
        'error': None,
        'raw_fields': fields  # เก็บข้อมูลดิบไว้ด้วย
    }


if __name__ == "__main__":
    # Test function
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python ppnd1_ocr_processor.py <pdf_file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    print("=" * 70)
    print("🧪 ทดสอบ PPND1 OCR Processor")
    print("=" * 70)
    print(f"📄 ไฟล์: {file_path}")
    print("-" * 70)
    
    # Process OCR
    result = process_ppnd1_ocr(file_path)
    
    if result['success']:
        print("✅ OCR สำเร็จ!")
        print("-" * 70)
        
        # Parse data
        parsed = parse_ppnd1_data(result)
        
        print("\n📋 ข้อมูลที่ Extract ได้:")
        print("-" * 70)
        
        # แสดงข้อมูลบริษัท
        if parsed.get('company_name'):
            print(f"  🏢 ชื่อบริษัท: {parsed['company_name']}")
        if parsed.get('tax_id'):
            print(f"  🆔 เลขประจำตัวผู้เสียภาษีอากร: {parsed['tax_id']}")
        if parsed.get('address'):
            print(f"  📍 ที่อยู่: {parsed['address']}")
        if parsed.get('receipt_number'):
            print(f"  📄 เลขที่ใบเสร็จ: {parsed['receipt_number']}")
        if parsed.get('date'):
            print(f"  📅 วันที่: {parsed['date']}")
        
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
        
        # แสดงเดือนและปี
        month = parsed.get('month')
        year = parsed.get('year')
        if month:
            month_names = ['', 'มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 
                          'พฤษภาคม', 'มิถุนายน', 'กรกฎาคม', 'สิงหาคม', 
                          'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม']
            print(f"  📅 เดือน: {month_names[month]} ({month})")
        if year:
            print(f"  📅 ปี: พ.ศ. {year} (ค.ศ. {year - 543})")
        
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
