"""
OCR Processor สำหรับแบบภาษี ภ.พ.30 โดยเฉพาะ
ใช้ AksonOCR API - Key Extract Model
"""
import requests
import json
from pathlib import Path
from typing import Dict, Any, Optional
import sys
import logging

# เพิ่ม path เพื่อ import config
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from config import Config
except ImportError:
    Config = None

logger = logging.getLogger(__name__)


def get_pp30_custom_fields() -> list:
    """
    สร้าง custom fields สำหรับ AksonOCR key-extract API สำหรับแบบภาษี ภ.พ.30
    
    Returns:
        List of custom field dictionaries
    """
    return [
        # ข้อมูลบริษัทและที่อยู่
        {
            "key": "ภ.พ.30",
            "description": "ค้นหาคำว่า ภ.พ.30 หรือ ภ.พ. 30 ว่ามีไหม",
            "example": "ภ.พ.30"
        },
        {
            "key": "ชื่อบริษัท",
            "description": "ชื่อบริษัทหรือชื่อผู้ประกอบการที่ยื่นแบบภาษี",
            "example": "บริษัท ABC จำกัด"
        },
        {
            "key": "ที่อยู่",
            "description": "ที่อยู่ของบริษัทหรือผู้ประกอบการ",
            "example": "123 ถนนสุขุมวิท แขวงคลองตัน เขตคลองตัน กรุงเทพมหานคร 10110"
        },
        # ข้อมูลการยื่นแบบ
        {
            "key": "ยื่นปกติ",
            "description": "ตรวจสอบว่ามีการเลือก checkbox 'ยื่นปกติ' หรือไม่โดยให้เเสดงผลออกมาเป็น ยื่นปกติ หากอ่านข้อมูลได้แล้วไม่เป็น null",
            "example": "ยื่นปกติ"
        },
        {
            "key": "ยื่นเพิ่มเติม",
            "description": "ตรวจสอบว่ามีการเลือก checkbox 'ยื่นเพิ่มเติม' หรือไม่ และครั้งที่เท่าไหร่โดยให้เเสดงผลออกมาเป็น ยื่นเพิ่มเติมครั้งที่",
            "example": "ยื่นเพิ่มเติมครั้งที่ 1"
        },
        {
            "key": "เดือน",
            "description": "เดือนที่ยื่นแบบภาษี (1-12) เช่น มกราคม, กุมภาพันธ์, ... ธันวาคม",
            "example": "ธันวาคม หรือ 12"
        },
        {
            "key": "ปี",
            "description": "ปีที่ยื่นแบบภาษี (พ.ศ.)",
            "example": "พ.ศ. 2568 หรือ 2568"
        },
        # ข้อมูลการคำนวณภาษี (16 ข้อ)
        {
            "key": "1. ยอดขายในเดือนนี้",
            "description": "",
            "example": ""
        },
        {
            "key": "2. ลบ ยอดขายที่เสียภาษีในอัตราร้อยละ 0 (ถ้ามี)",
            "description": "",
            "example": ""
        },
        {
            "key": "3. ลบ ยอดขายที่ได้รับยกเว้น (ถ้ามี)",
            "description": "",
            "example": ""
        },
        {
            "key": "4. ยอดขายที่ต้องเสียภาษี (1. - 2. - 3.)",
            "description": "",
            "example": ""
        },
        {
            "key": "5. ภาษีขายเดือนนี้",
            "description": "",
            "example": ""
        },
        {
            "key": "6. ยอดซื้อที่มีสิทธินำภาษีซื้อ",
            "description": "",
            "example": ""
        },
        {
            "key": "7. ภาษีซื้อเดือนนี้(ตามหลักฐานใบกำกับภาษีของยอดซื้อตาม 6.)",
            "description": "",
            "example": ""
        },
        {
            "key": "8. ภาษีที่ต้องชำระเดือนนี้ (ถ้า 5. มากกว่า 7. )",
            "description": "",
            "example": ""
        },
        {
            "key": "9. ภาษีที่ชำระเกินเดือนนี้ (ถ้า 5. น้อยกว่า 7. )",
            "description": "",
            "example": ""
        },
        {
            "key": "10. ภาษีที่ชำระเกินยกมา",
            "description": "",
            "example": ""
        },
        {
            "key": "11. ต้องชำระ (ถ้า 8. มากกว่า 10.)",
            "description": "",
            "example": ""
        },
        {
            "key": "12. ชำระเกิน (ถ้า 10. มากกว่า 8.) หรือ (9. รวมกับ 10.)",
            "description": "",
            "example": ""
        },
        {
            "key": "13. เงินเพิ่ม",
            "description": "",
            "example": ""
        },
        {
            "key": "14. เบี้ยปรับ",
            "description": "",
            "example": ""
        },
        {
            "key": "15. รวมภาษี เงินเพิ่ม และเบี้ยปรับที่ต้องชำระ ( 11. + 13. + 14. ) หรือ ( 13. + 14. - 12. )",
            "description": "",
            "example": ""
        },
        {
            "key": "16. รวมภาษีที่ชำระเกิน หลังคำนวณเงินเพิ่มและเบี้ยปรับแล้ว( 12. - 13. - 14. )",
            "description": "",
            "example": ""
        }
    ]


def process_pp30_ocr(file_path: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    ประมวลผล OCR สำหรับแบบภาษี ภ.พ.30 โดยใช้ AksonOCR API
    
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
    custom_fields = get_pp30_custom_fields()
    
    # 3. Prepare payload
    payload = {
        'customFields': json.dumps(custom_fields),
        'model': 'aksonocr-1.0',
        'additionalInstructions': 'ดึงข้อมูลจากแบบภาษี ภ.พ.30 โดยเน้นความถูกต้องของตัวเลขและวันที่'
    }
    
    # 4. Make the request
    headers = {'X-API-Key': api_key}
    
    try:
        logger.info(f"📤 [PP30 OCR] กำลังส่งไฟล์ไปยัง AksonOCR API: {file_path_obj.name}")
        
        with open(file_path_obj, 'rb') as file:
            files = {'file': (file_path_obj.name, file, 'application/pdf')}
            
            response = requests.post(
                API_URL, 
                headers=headers, 
                data=payload, 
                files=files, 
                timeout=120  # เพิ่ม timeout เป็น 120 วินาที
            )
            
            logger.info(f"📥 [PP30 OCR] Status Code: {response.status_code}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info("✅ [PP30 OCR] สำเร็จ!")
                
                # Extract data from response
                if 'success' in result and result.get('success'):
                    data = result.get('data', {})
                    
                    # Extract fields - API ส่งมาเป็น dict ของ key-value โดยตรง
                    # เช่น { "1. ยอดขายในเดือนนี้": "0.00", ... }
                    fields_data = {}
                    if isinstance(data, dict):
                        # ถ้า data เป็น dict โดยตรง (กรณีที่ API ส่งมาเป็น key-value)
                        if any(key.startswith('1.') or key.startswith('2.') for key in data.keys()):
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
                
                logger.error(f"❌ [PP30 OCR] Error: {error_msg}")
                
                return {
                    'success': False,
                    'data': {},
                    'raw_response': {},
                    'error': error_msg
                }
                
    except requests.exceptions.Timeout:
        error_msg = 'Request timeout (เกิน 120 วินาที)'
        logger.error(f"❌ [PP30 OCR] {error_msg}")
        return {
            'success': False,
            'data': {},
            'raw_response': {},
            'error': error_msg
        }
    except requests.exceptions.RequestException as e:
        error_msg = f'Network Error: {str(e)}'
        logger.error(f"❌ [PP30 OCR] {error_msg}")
        return {
            'success': False,
            'data': {},
            'raw_response': {},
            'error': error_msg
        }
    except Exception as e:
        error_msg = f'Unexpected Error: {str(e)}'
        logger.error(f"❌ [PP30 OCR] {error_msg}", exc_info=True)
        return {
            'success': False,
            'data': {},
            'raw_response': {},
            'error': error_msg
        }


def parse_pp30_data(ocr_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse ข้อมูลจาก OCR result ให้เป็นรูปแบบที่ใช้งานได้
    
    Args:
        ocr_result: ผลลัพธ์จาก process_pp30_ocr()
    
    Returns:
        Dictionary containing parsed data:
        {
            'amounts': dict,  # ข้อมูล 16 ข้อ
            'tax_form_type': 'ภ.พ.30',
            'company_name': str,  # ชื่อบริษัท
            'address': str,  # ที่อยู่
            'filing_type': str,  # 'normal' หรือ 'additional'
            'filing_additional_number': int or None,  # ครั้งที่เท่าไหร่ (ถ้าเป็นยื่นเพิ่มเติม)
            'month': int or None,  # เดือน (1-12)
            'year': int or None,  # ปี (พ.ศ.)
            'success': bool,
            'error': str or None
        }
    """
    if not ocr_result.get('success'):
        return {
            'amounts': {},
            'tax_form_type': 'ภ.พ.30',
            'success': False,
            'error': ocr_result.get('error', 'Unknown error')
        }
    
    # Extract fields - ข้อมูลอยู่ใน ocr_result['data'] โดยตรง
    # จาก API response: { "success": true, "data": { "1. ยอดขายในเดือนนี้": "0.00", ... } }
    # process_pp30_ocr จะส่ง fields_data โดยตรง (ไม่ wrap อีกชั้น)
    fields = ocr_result.get('data', {})
    
    # ตรวจสอบว่า fields เป็น dict หรือไม่
    if not isinstance(fields, dict):
        fields = {}
    
    # Parse amounts (16 items)
    amounts = {}
    
    # Mapping keys
    key_mapping = {
        '1. ยอดขายในเดือนนี้': 'ยอดขายในเดือนนี้ (ภ.พ.30)',
        '2. ลบ ยอดขายที่เสียภาษีในอัตราร้อยละ 0 (ถ้ามี)': 'ยอดขายที่เสียภาษีในอัตราร้อยละ 0 (ภ.พ.30)',
        '3. ลบ ยอดขายที่ได้รับยกเว้น (ถ้ามี)': 'ยอดขายที่ได้รับยกเว้น (ภ.พ.30)',
        '4. ยอดขายที่ต้องเสียภาษี (1. - 2. - 3.)': 'ยอดขายที่ต้องเสียภาษี (ภ.พ.30)',
        '5. ภาษีขายเดือนนี้': 'ภาษีขายเดือนนี้ (ภ.พ.30)',
        '6. ยอดซื้อที่มีสิทธินำภาษีซื้อ': 'ยอดซื้อที่มีสิทธินำภาษีซื้อ (ภ.พ.30)',
        '7. ภาษีซื้อเดือนนี้(ตามหลักฐานใบกำกับภาษีของยอดซื้อตาม 6.)': 'ภาษีซื้อเดือนนี้ (ภ.พ.30)',
        '8. ภาษีที่ต้องชำระเดือนนี้ (ถ้า 5. มากกว่า 7. )': 'ภาษีที่ต้องชำระเดือนนี้ (ภ.พ.30)',
        '9. ภาษีที่ชำระเกินเดือนนี้ (ถ้า 5. น้อยกว่า 7. )': 'ภาษีที่ชำระเกินเดือนนี้ (ภ.พ.30)',
        '10. ภาษีที่ชำระเกินยกมา': 'ภาษีที่ชำระเกินยกมา (ภ.พ.30)',
        '11. ต้องชำระ (ถ้า 8. มากกว่า 10.)': 'ต้องชำระ (ภ.พ.30)',
        '12. ชำระเกิน (ถ้า 10. มากกว่า 8.) หรือ (9. รวมกับ 10.)': 'ชำระเกิน (ภ.พ.30)',
        '13. เงินเพิ่ม': 'เงินเพิ่ม (ภ.พ.30)',
        '14. เบี้ยปรับ': 'เบี้ยปรับ (ภ.พ.30)',
        '15. รวมภาษี เงินเพิ่ม และเบี้ยปรับที่ต้องชำระ ( 11. + 13. + 14. ) หรือ ( 13. + 14. - 12. )': 'รวมภาษี เงินเพิ่ม และเบี้ยปรับที่ต้องชำระ (ภ.พ.30)',
        '16. รวมภาษีที่ชำระเกิน หลังคำนวณเงินเพิ่มและเบี้ยปรับแล้ว( 12. - 13. - 14. )': 'รวมภาษีที่ชำระเกิน หลังคำนวณเงินเพิ่มและเบี้ยปรับแล้ว (ภ.พ.30)',
    }
    
    # Parse และแปลงค่า
    import re
    
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
    
    # Parse ข้อมูลเพิ่มเติม
    company_name = fields.get('ชื่อบริษัท', '').strip() if fields.get('ชื่อบริษัท') else ''
    address = fields.get('ที่อยู่', '').strip() if fields.get('ที่อยู่') else ''
    
    # Parse การยื่นแบบ
    filing_type = None  # 'normal' หรือ 'additional'
    filing_additional_number = None  # ครั้งที่เท่าไหร่ (ถ้าเป็นยื่นเพิ่มเติม)
    
    yien_normal = fields.get('ยื่นปกติ', '').strip() if fields.get('ยื่นปกติ') else ''
    yien_additional = fields.get('ยื่นเพิ่มเติม', '').strip() if fields.get('ยื่นเพิ่มเติม') else ''
    
    # ตรวจสอบว่ามีการเลือกยื่นปกติหรือยื่นเพิ่มเติม
    import re
    if yien_normal and (yien_normal.lower() in ['✓', '✔', '[x]', 'x', 'checked', 'true'] or 
                        'ยื่นปกติ' in yien_normal.lower()):
        filing_type = 'normal'
    elif yien_additional and (yien_additional.lower() in ['✓', '✔', '[x]', 'x', 'checked', 'true'] or 
                              'ยื่นเพิ่มเติม' in yien_additional.lower()):
        filing_type = 'additional'
        # หาเลขครั้งที่
        additional_match = re.search(r'ครั้งที่\s*(\d+)', yien_additional)
        if additional_match:
            try:
                filing_additional_number = int(additional_match.group(1))
            except ValueError:
                pass
    
    # Parse เดือนและปี
    month_raw = fields.get('เดือน', '').strip() if fields.get('เดือน') else ''
    year_raw = fields.get('ปี', '').strip() if fields.get('ปี') else ''
    
    month = None
    year = None
    
    # Parse เดือน (1-12)
    month_names = {
        'มกราคม': 1, 'กุมภาพันธ์': 2, 'มีนาคม': 3, 'เมษายน': 4,
        'พฤษภาคม': 5, 'มิถุนายน': 6, 'กรกฎาคม': 7, 'สิงหาคม': 8,
        'กันยายน': 9, 'ตุลาคม': 10, 'พฤศจิกายน': 11, 'ธันวาคม': 12
    }
    
    if month_raw:
        # ลองหาเลขเดือน (1-12)
        month_match = re.search(r'\(?(\d{1,2})\)?\s*', month_raw)
        if month_match:
            try:
                month = int(month_match.group(1))
            except ValueError:
                pass
        
        # ถ้ายังหาไม่เจอ ลองหาชื่อเดือน
        if month is None:
            for name, num in month_names.items():
                if name in month_raw:
                    month = num
                    break
    
    # Parse ปี (พ.ศ.)
    if year_raw:
        # หาเลขปี (พ.ศ.)
        year_match = re.search(r'พ\.ศ\.?\s*(\d{4})|(\d{4})', year_raw)
        if year_match:
            try:
                year = int(year_match.group(1) or year_match.group(2))
            except (ValueError, AttributeError):
                pass
    
    return {
        'amounts': amounts,
        'tax_form_type': 'ภ.พ.30',
        'company_name': company_name,
        'address': address,
        'filing_type': filing_type,  # 'normal' หรือ 'additional'
        'filing_additional_number': filing_additional_number,  # ครั้งที่เท่าไหร่ (ถ้ามี)
        'month': month,  # 1-12
        'year': year,  # พ.ศ.
        'success': True,
        'error': None,
        'raw_fields': fields  # เก็บข้อมูลดิบไว้ด้วย
    }


if __name__ == "__main__":
    # Test function
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python pp30_ocr_processor.py <pdf_file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    print("=" * 70)
    print("🧪 ทดสอบ PP30 OCR Processor")
    print("=" * 70)
    print(f"📄 ไฟล์: {file_path}")
    print("-" * 70)
    
    # Process OCR
    result = process_pp30_ocr(file_path)
    
    if result['success']:
        print("✅ OCR สำเร็จ!")
        print("-" * 70)
        
        # Parse data
        parsed = parse_pp30_data(result)
        
        print("\n📋 ข้อมูลที่ Extract ได้:")
        print("-" * 70)
        
        # แสดงข้อมูลบริษัท
        if parsed.get('company_name'):
            print(f"  🏢 ชื่อบริษัท: {parsed['company_name']}")
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
