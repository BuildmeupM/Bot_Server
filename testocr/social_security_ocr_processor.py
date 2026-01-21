"""
OCR Processor สำหรับแบบประกันสังคม โดยเฉพาะ
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


def get_social_security_custom_fields() -> list:
    """
    สร้าง custom fields สำหรับ AksonOCR key-extract API สำหรับแบบประกันสังคม
    
    Returns:
        List of custom field dictionaries
    """
    return [
        {
            "key": "สำนักงานประกันสังคม",
            "description": "ให้แสดงผลออกมาเป็น แบบประกันสังคม",
            "example": "แบบประกันสังคม"
        },
        {
            "key": "ชื่อสถานะประกอบการ",
            "description": "",
            "example": "บริษัท ไอสาม เกทเวย์ จำกัด"
        },
        {
            "key": "ที่ตั้งสำนักงานใหญ่/สาขา",
            "description": "",
            "example": ""
        },
        {
            "key": "เลขที่บัญชี",
            "description": "ดึงข้อมูลให้รวมกันไม่ต้องวรรค",
            "example": "1002732158"
        },
        {
            "key": "การนำส่งเงินสมทบสำหรับค่าจ้างเดือน",
            "description": "ให้ระบบดูว่าเป็นนำส่งเงินสมทบของเดือนไหน",
            "example": "ธันวาคม"
        },
        {
            "key": "พ.ศ.",
            "description": "ให้ระบบดูว่าเป็นนำส่งของปีไหน",
            "example": "2568"
        },
        {
            "key": "จำนวนผู้ประกันตนที่ส่งเงินสมทบ",
            "description": "",
            "example": "27"
        },
        {
            "key": "เงินค่าจ้างทั้งสิ้น",
            "description": "",
            "example": "0.00"
        },
        {
            "key": "เงินสมทบผู้ประกันตน",
            "description": "",
            "example": "0.00"
        },
        {
            "key": "เงินสมทบนายจ้าง",
            "description": "",
            "example": "0.00"
        },
        {
            "key": "รวมเงินสมทบที่นำส่งทั้งสิ้น",
            "description": "",
            "example": "0.00"
        }
    ]


def process_social_security_ocr(file_path: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    ประมวลผล OCR สำหรับแบบประกันสังคม โดยใช้ AksonOCR API
    
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
    custom_fields = get_social_security_custom_fields()
    
    # 3. Prepare payload
    payload = {
        'customFields': json.dumps(custom_fields),
        'model': 'aksonocr-1.0',
        'additionalInstructions': 'ดึงข้อมูลให้ถูกต้องตามที่กำหนด โดยเน้นที่ชื่อสถานะประกอบการและเลขที่บัญชี จะต้องถูกต้องครบตัวอักษร'
    }
    
    # 4. Make the request
    headers = {'X-API-Key': api_key}
    
    try:
        logger.info(f"📤 [Social Security OCR] กำลังส่งไฟล์ไปยัง AksonOCR API: {file_path_obj.name}")
        
        with open(file_path_obj, 'rb') as file:
            files = {'file': (file_path_obj.name, file, 'application/pdf')}
            
            response = requests.post(
                API_URL, 
                headers=headers, 
                data=payload, 
                files=files, 
                timeout=120  # เพิ่ม timeout เป็น 120 วินาที
            )
            
            logger.info(f"📥 [Social Security OCR] Status Code: {response.status_code}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info("✅ [Social Security OCR] สำเร็จ!")
                
                # Extract data from response
                if 'success' in result and result.get('success'):
                    data = result.get('data', {})
                    
                    # Extract fields - API ส่งมาเป็น dict ของ key-value โดยตรง
                    # เช่น { "ชื่อสถานะประกอบการ": "บริษัท...", ... }
                    fields_data = {}
                    if isinstance(data, dict):
                        # ถ้า data เป็น dict โดยตรง (กรณีที่ API ส่งมาเป็น key-value)
                        if any('ชื่อสถานะประกอบการ' in key or 'เลขที่บัญชี' in key or 'ประกันสังคม' in key or 'เงินสมทบ' in key for key in data.keys()):
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
                
                logger.error(f"❌ [Social Security OCR] Error: {error_msg}")
                
                return {
                    'success': False,
                    'data': {},
                    'raw_response': {},
                    'error': error_msg
                }
                
    except requests.exceptions.Timeout:
        error_msg = 'Request timeout (เกิน 120 วินาที)'
        logger.error(f"❌ [Social Security OCR] {error_msg}")
        return {
            'success': False,
            'data': {},
            'raw_response': {},
            'error': error_msg
        }
    except requests.exceptions.RequestException as e:
        error_msg = f'Network Error: {str(e)}'
        logger.error(f"❌ [Social Security OCR] {error_msg}")
        return {
            'success': False,
            'data': {},
            'raw_response': {},
            'error': error_msg
        }
    except Exception as e:
        error_msg = f'Unexpected Error: {str(e)}'
        logger.error(f"❌ [Social Security OCR] {error_msg}", exc_info=True)
        return {
            'success': False,
            'data': {},
            'raw_response': {},
            'error': error_msg
        }


def parse_social_security_data(ocr_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse ข้อมูลจาก OCR result ให้เป็นรูปแบบที่ใช้งานได้
    
    Args:
        ocr_result: ผลลัพธ์จาก process_social_security_ocr()
    
    Returns:
        Dictionary containing parsed data:
        {
            'company_name': str,  # ชื่อสถานะประกอบการ
            'address': str,  # ที่ตั้งสำนักงานใหญ่/สาขา
            'account_number': str,  # เลขที่บัญชี (ไม่เว้นวรรค)
            'month': str,  # เดือน (เช่น "ธันวาคม", "12")
            'year': int,  # พ.ศ.
            'number_of_insured': int,  # จำนวนผู้ประกันตนที่ส่งเงินสมทบ
            'total_wages': float,  # เงินค่าจ้างทั้งสิ้น
            'employee_contribution': float,  # เงินสมทบผู้ประกันตน
            'employer_contribution': float,  # เงินสมทบนายจ้าง
            'total_contribution': float,  # รวมเงินสมทบที่นำส่งทั้งสิ้น
            'tax_form_type': 'แบบประกันสังคม',
            'success': bool,
            'error': str or None
        }
    """
    if not ocr_result.get('success'):
        return {
            'company_name': '',
            'address': '',
            'account_number': '',
            'month': '',
            'year': 0,
            'number_of_insured': 0,
            'total_wages': 0.00,
            'employee_contribution': 0.00,
            'employer_contribution': 0.00,
            'total_contribution': 0.00,
            'tax_form_type': 'แบบประกันสังคม',
            'success': False,
            'error': ocr_result.get('error', 'Unknown error')
        }
    
    # Extract fields - ข้อมูลอยู่ใน ocr_result['data'] โดยตรง
    # process_social_security_ocr จะส่ง fields_data โดยตรง (ไม่ wrap อีกชั้น)
    fields = ocr_result.get('data', {})
    
    # ตรวจสอบว่า fields เป็น dict หรือไม่
    if not isinstance(fields, dict):
        fields = {}
    
    # Parse ชื่อสถานะประกอบการ
    company_name = fields.get('ชื่อสถานะประกอบการ', '').strip() if fields.get('ชื่อสถานะประกอบการ') else ''
    
    # Parse ที่ตั้งสำนักงานใหญ่/สาขา
    address = fields.get('ที่ตั้งสำนักงานใหญ่/สาขา', '').strip() if fields.get('ที่ตั้งสำนักงานใหญ่/สาขา') else ''
    
    # Parse เลขที่บัญชี (ลบเว้นวรรคและ dash)
    account_number = fields.get('เลขที่บัญชี', '').strip() if fields.get('เลขที่บัญชี') else ''
    if account_number:
        account_number = account_number.replace(' ', '').replace('-', '')
    
    # Parse เดือน
    month = ''
    month_str = fields.get('การนำส่งเงินสมทบสำหรับค่าจ้างเดือน', '')
    if month_str:
        month = str(month_str).strip()
        
        # แปลงชื่อเดือนไทยเป็นตัวเลข (ถ้าเป็นชื่อเดือน)
        thai_months = {
            'มกราคม': '01', 'กุมภาพันธ์': '02', 'มีนาคม': '03', 'เมษายน': '04',
            'พฤษภาคม': '05', 'มิถุนายน': '06', 'กรกฎาคม': '07', 'สิงหาคม': '08',
            'กันยายน': '09', 'ตุลาคม': '10', 'พฤศจิกายน': '11', 'ธันวาคม': '12'
        }
        
        # ถ้าเป็นชื่อเดือนไทย ให้แปลงเป็นตัวเลข
        for thai_month, month_num in thai_months.items():
            if thai_month in month:
                month = month_num
                break
        
        # ถ้ายังเป็นตัวเลขอยู่แล้ว ให้ตรวจสอบว่าเป็นรูปแบบที่ถูกต้อง
        if month.isdigit():
            month = month.zfill(2)
    
    # Parse พ.ศ.
    year = 0
    year_str = fields.get('พ.ศ.', '')
    if year_str:
        # หาตัวเลขใน year_str
        match = re.search(r'(\d{4})', str(year_str))
        if match:
            try:
                year = int(match.group(1))
            except ValueError:
                year = 0
    
    # Parse จำนวนผู้ประกันตนที่ส่งเงินสมทบ
    number_of_insured = 0
    number_of_insured_str = fields.get('จำนวนผู้ประกันตนที่ส่งเงินสมทบ', '')
    if number_of_insured_str:
        # หาตัวเลข
        match = re.search(r'(\d+)', str(number_of_insured_str).replace(',', ''))
        if match:
            try:
                number_of_insured = int(match.group(1))
            except ValueError:
                number_of_insured = 0
    
    # Parse เงินค่าจ้างทั้งสิ้น
    total_wages = 0.00
    total_wages_str = fields.get('เงินค่าจ้างทั้งสิ้น', '')
    if total_wages_str:
        # ลบ comma และ whitespace
        clean_value = str(total_wages_str).replace(',', '').replace(' ', '').strip()
        
        # หาตัวเลข (รองรับทศนิยม)
        match = re.search(r'(\d+\.?\d*)', clean_value)
        if match:
            try:
                total_wages = float(match.group(1))
            except ValueError:
                total_wages = 0.00
    
    # Parse เงินสมทบผู้ประกันตน
    employee_contribution = 0.00
    employee_contribution_str = fields.get('เงินสมทบผู้ประกันตน', '')
    if employee_contribution_str:
        # ลบ comma และ whitespace
        clean_value = str(employee_contribution_str).replace(',', '').replace(' ', '').strip()
        
        # หาตัวเลข (รองรับทศนิยม)
        match = re.search(r'(\d+\.?\d*)', clean_value)
        if match:
            try:
                employee_contribution = float(match.group(1))
            except ValueError:
                employee_contribution = 0.00
    
    # Parse เงินสมทบนายจ้าง
    employer_contribution = 0.00
    employer_contribution_str = fields.get('เงินสมทบนายจ้าง', '')
    if employer_contribution_str:
        # ลบ comma และ whitespace
        clean_value = str(employer_contribution_str).replace(',', '').replace(' ', '').strip()
        
        # หาตัวเลข (รองรับทศนิยม)
        match = re.search(r'(\d+\.?\d*)', clean_value)
        if match:
            try:
                employer_contribution = float(match.group(1))
            except ValueError:
                employer_contribution = 0.00
    
    # Parse รวมเงินสมทบที่นำส่งทั้งสิ้น
    total_contribution = 0.00
    total_contribution_str = fields.get('รวมเงินสมทบที่นำส่งทั้งสิ้น', '')
    if total_contribution_str:
        # ลบ comma และ whitespace
        clean_value = str(total_contribution_str).replace(',', '').replace(' ', '').strip()
        
        # หาตัวเลข (รองรับทศนิยม)
        match = re.search(r'(\d+\.?\d*)', clean_value)
        if match:
            try:
                total_contribution = float(match.group(1))
            except ValueError:
                total_contribution = 0.00
    
    # สร้าง amounts dictionary สำหรับส่งไป frontend
    amounts = {
        'รวมเงินสมทบที่นำส่งทั้งสิ้น (ประกันสังคม)': total_contribution
    }
    
    # สร้าง social_security_json structure สำหรับส่งไป frontend
    social_security_json = {
        'data': fields  # ส่งข้อมูลดิบทั้งหมดไปให้ frontend
    }
    
    return {
        'company_name': company_name,
        'address': address,
        'account_number': account_number,
        'month': month,
        'year': year,
        'number_of_insured': number_of_insured,
        'total_wages': total_wages,
        'employee_contribution': employee_contribution,
        'employer_contribution': employer_contribution,
        'total_contribution': total_contribution,
        'tax_form_type': 'แบบประกันสังคม',
        'success': True,
        'error': None,
        'raw_fields': fields,  # เก็บข้อมูลดิบไว้ด้วย
        'amounts': amounts,  # เพิ่ม amounts dictionary สำหรับส่งไป frontend
        'social_security_json': social_security_json  # ส่ง JSON structure ใหม่ไปให้ frontend
    }


if __name__ == "__main__":
    # Test function
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python social_security_ocr_processor.py <pdf_file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    print("=" * 70)
    print("🧪 ทดสอบ Social Security OCR Processor")
    print("=" * 70)
    print(f"📄 ไฟล์: {file_path}")
    print("-" * 70)
    
    # Process OCR
    result = process_social_security_ocr(file_path)
    
    if result['success']:
        print("✅ OCR สำเร็จ!")
        print("-" * 70)
        
        # Parse data
        parsed = parse_social_security_data(result)
        
        print("\n📋 ข้อมูลที่ Extract ได้:")
        print("-" * 70)
        
        # แสดงข้อมูลสถานะประกอบการ
        if parsed.get('company_name'):
            print(f"  🏢 ชื่อสถานะประกอบการ: {parsed['company_name']}")
        if parsed.get('address'):
            print(f"  📍 ที่ตั้งสำนักงานใหญ่/สาขา: {parsed['address']}")
        if parsed.get('account_number'):
            print(f"  🆔 เลขที่บัญชี: {parsed['account_number']}")
        if parsed.get('month'):
            print(f"  📅 เดือน: {parsed['month']}")
        if parsed.get('year'):
            print(f"  📅 พ.ศ.: {parsed['year']}")
        if parsed.get('number_of_insured'):
            print(f"  👥 จำนวนผู้ประกันตนที่ส่งเงินสมทบ: {parsed['number_of_insured']}")
        if parsed.get('total_wages'):
            print(f"  💰 เงินค่าจ้างทั้งสิ้น: {parsed['total_wages']:,.2f} บาท")
        if parsed.get('employee_contribution'):
            print(f"  💰 เงินสมทบผู้ประกันตน: {parsed['employee_contribution']:,.2f} บาท")
        if parsed.get('employer_contribution'):
            print(f"  💰 เงินสมทบนายจ้าง: {parsed['employer_contribution']:,.2f} บาท")
        if parsed.get('total_contribution'):
            print(f"  💰 รวมเงินสมทบที่นำส่งทั้งสิ้น: {parsed['total_contribution']:,.2f} บาท")
        
        print("\n📄 Raw Fields:")
        print("-" * 70)
        for key, value in parsed.get('raw_fields', {}).items():
            if value:
                print(f"  • {key}: {value}")
    else:
        print(f"❌ OCR ไม่สำเร็จ: {result.get('error', 'Unknown error')}")
    
    print("=" * 70)
