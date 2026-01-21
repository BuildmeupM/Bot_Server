"""
Invoice Extractors Utilities
============================
Helper functions สำหรับดึงข้อมูลที่ขาดไป

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


def extract_due_date(text: str) -> Optional[str]:
    """
    ดึงวันที่ครบกำหนดชำระจากข้อความ
    
    รูปแบบที่รองรับ:
    - Due Date: 03/11/2025
    - Due Date : 03-Nov-25
    - ครบกำหนดชำระ: 03/11/2025
    - Payment Due: 03/11/2025
    - Due: 03/11/2025
    
    Args:
        text: ข้อความที่อ่านจาก OCR
    
    Returns:
        วันที่ในรูปแบบ dd/mm/yyyy หรือ None
    """
    if not text:
        return None
    
    # รูปแบบวันที่ที่รองรับ
    patterns = [
        # Due Date: 03/11/2025
        (r'Due\s+Date\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})', 'dd/mm/yyyy'),
        # Due Date : 03-Nov-25
        (r'Due\s+Date\s*[:.]?\s*(\d{1,2})-([A-Za-z]{3})-(\d{2,4})', 'dd-mon-yy'),
        # ครบกำหนดชำระ: 03/11/2025
        (r'ครบกำหนดชำระ\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})', 'dd/mm/yyyy'),
        # Payment Due: 03/11/2025
        (r'Payment\s+Due\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})', 'dd/mm/yyyy'),
        # Due: 03/11/2025
        (r'Due\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})', 'dd/mm/yyyy'),
        # กำหนดชำระ: 03/11/2025
        (r'กำหนดชำระ\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})', 'dd/mm/yyyy'),
        # Due Date: 03-Nov-2025
        (r'Due\s+Date\s*[:.]?\s*(\d{1,2})-([A-Za-z]{3})-(\d{4})', 'dd-mon-yyyy'),
    ]
    
    month_map = {
        'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04',
        'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
        'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
    }
    
    for pattern, date_format in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if date_format == 'dd/mm/yyyy':
                day = match.group(1).zfill(2)
                month = match.group(2).zfill(2)
                year = match.group(3)
                return f"{day}/{month}/{year}"
            elif date_format in ['dd-mon-yy', 'dd-mon-yyyy']:
                day = match.group(1).zfill(2)
                month_abbr = match.group(2).upper()
                year_str = match.group(3)
                
                month = month_map.get(month_abbr, '01')
                
                # แปลงปี
                if len(year_str) == 2:
                    year = '20' + year_str
                else:
                    year = year_str
                
                return f"{day}/{month}/{year}"
    
    return None


def extract_account_info(text: str) -> Dict[str, Optional[str]]:
    """
    ดึงข้อมูลบัญชี (Account Name / Account Code) จากข้อความ
    
    รูปแบบที่รองรับ:
    - Account Name: ABC Company / Account Code: 12345
    - ชื่อบัญชี: ABC Company / โค้ดบัญชี: 12345
    - Account: ABC Company (Code: 12345)
    - A/C Name: ABC Company
    - A/C Code: 12345
    
    Args:
        text: ข้อความที่อ่านจาก OCR
    
    Returns:
        Dictionary ที่มี account_name และ account_code
    """
    result = {
        'account_name': None,
        'account_code': None
    }
    
    if not text:
        return result
    
    # รูปแบบการค้นหาชื่อบัญชี
    account_name_patterns = [
        r'Account\s+Name\s*[:.]?\s*([^\n\r/]+)',
        r'ชื่อบัญชี\s*[:.]?\s*([^\n\r/]+)',
        r'A/C\s+Name\s*[:.]?\s*([^\n\r/]+)',
        r'Account\s*[:.]?\s*([^\n\r/]+)',
        r'Customer\s+Name\s*[:.]?\s*([^\n\r/]+)',
        r'ชื่อลูกค้า\s*[:.]?\s*([^\n\r/]+)',
    ]
    
    # รูปแบบการค้นหาโค้ดบัญชี
    account_code_patterns = [
        r'Account\s+Code\s*[:.]?\s*([A-Z0-9\-]+)',
        r'โค้ดบัญชี\s*[:.]?\s*([A-Z0-9\-]+)',
        r'A/C\s+Code\s*[:.]?\s*([A-Z0-9\-]+)',
        r'Code\s*[:.]?\s*([A-Z0-9\-]+)',
        r'Account\s+No[.:]?\s*[:.]?\s*([A-Z0-9\-]+)',
        r'เลขที่บัญชี\s*[:.]?\s*([A-Z0-9\-]+)',
    ]
    
    # ค้นหาชื่อบัญชี
    for pattern in account_name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            account_name = match.group(1).strip()
            # ทำความสะอาด: ลบ space หลายตัว, ลบเครื่องหมายพิเศษ
            account_name = re.sub(r'\s+', ' ', account_name)
            account_name = account_name.strip('.,:;')
            if len(account_name) > 2:  # ต้องมีความยาวอย่างน้อย 3 ตัวอักษร
                result['account_name'] = account_name
                logger.debug(f"✅ พบชื่อบัญชี: {account_name}")
                break
    
    # ค้นหาโค้ดบัญชี
    for pattern in account_code_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            account_code = match.group(1).strip()
            # ทำความสะอาด: ลบ space, เครื่องหมายพิเศษ
            account_code = re.sub(r'[\s,.:;]+', '', account_code)
            if len(account_code) > 0:
                result['account_code'] = account_code
                logger.debug(f"✅ พบโค้ดบัญชี: {account_code}")
                break
    
    # ลองหาจากรูปแบบรวม: Account Name: XXX / Code: YYY
    combined_pattern = r'Account\s+Name\s*[:.]?\s*([^/\n]+)\s*[/|]\s*Code\s*[:.]?\s*([A-Z0-9\-]+)'
    match = re.search(combined_pattern, text, re.IGNORECASE)
    if match:
        account_name = match.group(1).strip()
        account_code = match.group(2).strip()
        if not result['account_name'] and len(account_name) > 2:
            result['account_name'] = account_name
        if not result['account_code'] and len(account_code) > 0:
            result['account_code'] = account_code
    
    return result


def extract_branch(text: str) -> Optional[str]:
    """
    ดึงสาขาจากข้อความ
    
    รูปแบบที่รองรับ:
    - Branch: 00001
    - สาขา: 00001
    - Branch No.: 00001
    - Branch Code: 00001
    
    Args:
        text: ข้อความที่อ่านจาก OCR
    
    Returns:
        สาขา (string) หรือ None
    """
    if not text:
        return None
    
    # รูปแบบการค้นหาสาขา
    patterns = [
        r'Branch\s*[:.]?\s*(\d{5})',  # Branch: 00001
        r'สาขา\s*[:.]?\s*(\d{5})',  # สาขา: 00001
        r'Branch\s+No[.:]?\s*[:.]?\s*(\d{5})',  # Branch No.: 00001
        r'Branch\s+Code\s*[:.]?\s*(\d{5})',  # Branch Code: 00001
        r'สาขา\s*เลขที่\s*[:.]?\s*(\d{5})',  # สาขาเลขที่: 00001
        r'Branch\s*[:.]?\s*(\d{1,5})',  # Branch: 1 (รองรับสาขาที่ไม่ใช่ 5 หลัก)
        r'สาขา\s*[:.]?\s*(\d{1,5})',  # สาขา: 1
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            branch = match.group(1).strip()
            # ถ้าเป็นสาขา 5 หลัก ให้เติม 0 นำหน้า
            if len(branch) < 5:
                branch = branch.zfill(5)
            logger.debug(f"✅ พบสาขา: {branch}")
            return branch
    
    return None


def extract_withholding_tax_enhanced(text: str) -> Dict[str, Optional[float]]:
    """
    ดึงข้อมูลหัก ณ ที่จ่ายแบบเพิ่มเติม (รองรับรูปแบบเพิ่มเติม)
    
    รูปแบบที่รองรับ:
    - หัก ณ ที่จ่าย 3%
    - Withholding Tax 3%
    - WHT 3%
    - หักภาษี ณ ที่จ่าย 3%
    
    Args:
        text: ข้อความที่อ่านจาก OCR
    
    Returns:
        Dictionary ที่มี withholding_tax_percent และ withholding_tax_amount
    """
    result = {
        'withholding_tax_percent': None,
        'withholding_tax_amount': None
    }
    
    if not text:
        return result
    
    # รูปแบบการค้นหาเปอร์เซ็นต์หัก ณ ที่จ่าย
    percent_patterns = [
        r'หัก\s*ณ\s*ที่จ่าย\s*(\d+(?:\.\d+)?)\s*%',
        r'หัก\s*ภาษี\s*ณ\s*ที่จ่าย\s*(\d+(?:\.\d+)?)\s*%',
        r'Withholding\s+Tax\s*(\d+(?:\.\d+)?)\s*%',
        r'WHT\s*(\d+(?:\.\d+)?)\s*%',
        r'หัก\s*(\d+(?:\.\d+)?)\s*%',
        r'เปอร์เซ็นต์หัก\s*ณ\s*ที่จ่าย\s*[:.]?\s*(\d+(?:\.\d+)?)\s*%',
    ]
    
    # รูปแบบการค้นหายอดหัก ณ ที่จ่าย
    amount_patterns = [
        r'หัก\s*ณ\s*ที่จ่าย\s*[:.]?\s*([\d,]+\.?\d{0,2})',
        r'หัก\s*ภาษี\s*ณ\s*ที่จ่าย\s*[:.]?\s*([\d,]+\.?\d{0,2})',
        r'Withholding\s+Tax\s+Amount\s*[:.]?\s*([\d,]+\.?\d{0,2})',
        r'WHT\s+Amount\s*[:.]?\s*([\d,]+\.?\d{0,2})',
        r'ยอดหัก\s*ณ\s*ที่จ่าย\s*[:.]?\s*([\d,]+\.?\d{0,2})',
    ]
    
    # ค้นหาเปอร์เซ็นต์
    for pattern in percent_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                percent = float(match.group(1))
                result['withholding_tax_percent'] = percent
                logger.debug(f"✅ พบเปอร์เซ็นต์หัก ณ ที่จ่าย: {percent}%")
                break
            except ValueError:
                continue
    
    # ค้นหายอดเงิน
    for pattern in amount_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                amount_str = match.group(1).replace(',', '').strip()
                amount = float(amount_str)
                if amount > 0:
                    result['withholding_tax_amount'] = amount
                    logger.debug(f"✅ พบยอดหัก ณ ที่จ่าย: {amount}")
                    break
            except ValueError:
                continue
    
    return result

