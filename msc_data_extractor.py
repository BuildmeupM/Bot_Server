"""
MSC Data Extractor
==================
ดึงข้อมูลจาก MSC Mediterranean Shipping Company invoices
และจัดรูปแบบสำหรับส่งไปยัง Excel

Author: BotV3
Version: 1.0.0
"""

import re
from datetime import datetime
from typing import Dict, Optional, Any
from pathlib import Path


class MSCDataExtractor:
    """Extractor สำหรับดึงข้อมูลจาก MSC invoices"""
    
    # Company identifiers
    MSC_IDENTIFIERS = [
        "MSC Mediterranean Shipping Company",
        "Mediterranean Shipping (Thailand)",
        "MSC Building"
    ]
    
    def __init__(self):
        """Initialize MSC Data Extractor"""
        pass
    
    def is_msc_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ MSC หรือไม่
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร MSC
        """
        if not text:
            return False
        
        text_upper = text.upper()
        for identifier in self.MSC_IDENTIFIERS:
            if identifier.upper() in text_upper:
                return True
        return False
    
    def extract_company_name(self, text: str) -> str:
        """
        ดึงชื่อบริษัท MSC
        
        Returns:
            "MSC Mediterranean Shipping Company S.A."
        """
        # หาบรรทัดที่มี MSC Mediterranean Shipping Company
        lines = text.split('\n')
        for line in lines:
            if 'MSC Mediterranean Shipping Company' in line:
                # Clean up
                company_name = line.strip()
                # ถ้าไม่มี S.A. ให้เพิ่ม
                if 'S.A.' not in company_name:
                    company_name = 'MSC Mediterranean Shipping Company S.A.'
                return company_name
        
        return 'MSC Mediterranean Shipping Company S.A.'
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """
        ดึงเลขประจำตัวผู้เสียภาษี
        
        Pattern: TaxID 9930000036677 → 0993000003667
        
        Returns:
            เลขประจำตัวผู้เสียภาษี 13 หลัก (เติม 0 ข้างหน้าถ้าต้องการ)
        """
        # Pattern 1: TaxID 9930000036677
        pattern1 = r'TaxID\s*[:.]?\s*(\d{13})'
        match = re.search(pattern1, text, re.IGNORECASE)
        if match:
            tax_id = match.group(1)
            # ถ้าขึ้นต้นด้วย 99 ให้เปลี่ยนเป็น 09
            if tax_id.startswith('99'):
                tax_id = '0' + tax_id[1:]
            return tax_id
        
        # Pattern 2: Tax ID No. 9930000036677
        pattern2 = r'Tax\s+ID\s+No[.:]?\s*(\d{13})'
        match = re.search(pattern2, text, re.IGNORECASE)
        if match:
            tax_id = match.group(1)
            if tax_id.startswith('99'):
                tax_id = '0' + tax_id[1:]
            return tax_id
        
        # Pattern 3: เลขที่มีจุลภาค 993,000,003,667
        pattern3 = r'TaxID\s*[:.]?\s*([\d,]{15,})'
        match = re.search(pattern3, text, re.IGNORECASE)
        if match:
            tax_id = match.group(1).replace(',', '')
            if len(tax_id) == 13:
                if tax_id.startswith('99'):
                    tax_id = '0' + tax_id[1:]
                return tax_id
        
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        """
        ดึงวันที่และแปลงเป็น dd/mm/yyyy
        
        Pattern: Date / วันที่ 03-NOV-2025 Branch No : 0
        
        Returns:
            วันที่ในรูปแบบ dd/mm/yyyy (เช่น 03/11/2025)
        """
        # Pattern: Date / วันที่ 03-NOV-2025
        pattern = r'Date\s*[/:]?\s*วันที่\s*[:.]?\s*(\d{1,2})-([A-Z]{3})-(\d{4})'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            day = match.group(1).zfill(2)  # เติม 0 ถ้าวันเป็นเลขหลักเดียว
            month_abbr = match.group(2).upper()
            year = match.group(3)
            
            # แปลงเดือนจากตัวย่อเป็นเลข
            month_map = {
                'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04',
                'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
                'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
            }
            
            month = month_map.get(month_abbr, '01')
            
            return f"{day}/{month}/{year}"
        
        return None
    
    def extract_non_taxable_amount(self, text: str) -> Optional[float]:
        """
        ดึงยอดก่อนภาษีมูลค่าเพิ่ม (Non-Taxable Amount)
        
        Pattern: Non-Taxable Amount / ไม่มีภาษีมูลค่าเพิ่ม 6,000.00
        
        Returns:
            จำนวนเงิน (float)
        """
        # Pattern 1: Non-Taxable Amount / ไม่มีภาษีมูลค่าเพิ่ม 6,000.00
        pattern1 = r'Non-Taxable Amount\s*[/:]?\s*ไม่มีภาษีมูลค่าเพิ่ม\s*([\d,]+\.?\d*)'
        match = re.search(pattern1, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '')
            try:
                return float(amount_str)
            except ValueError:
                pass
        
        # Pattern 2: ถ้าไม่เจอ ให้หาแค่ Non-Taxable Amount ตามด้วยตัวเลข
        pattern2 = r'Non-Taxable Amount[^\d]+([\d,]+\.?\d*)'
        match = re.search(pattern2, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '')
            try:
                return float(amount_str)
            except ValueError:
                pass
        
        return None
    
    def extract_total_amount(self, text: str) -> Optional[float]:
        """
        ดึงยอดรวม (Total)
        
        Pattern: Total / รวม 6,000.00
        
        Returns:
            จำนวนเงิน (float)
        """
        # Pattern 1: Total / รวม 6,000.00
        pattern1 = r'Total\s*[/:]?\s*รวม\s*([\d,]+\.?\d*)'
        match = re.search(pattern1, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '')
            try:
                return float(amount_str)
            except ValueError:
                pass
        
        # Pattern 2: ถ้าไม่เจอ ให้หาแค่ Total ตามด้วยตัวเลข (แต่ไม่ใช่ Taxable)
        pattern2 = r'(?<!Taxable )(?<!Non-Taxable )Total[^\d]+([\d,]+\.?\d*)'
        match = re.search(pattern2, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '')
            try:
                return float(amount_str)
            except ValueError:
                pass
        
        return None
    
    def extract_document_number_from_filename(self, filename: str) -> Optional[str]:
        """
        ดึงเลขที่เอกสารจากชื่อไฟล์
        
        Pattern: EXC-2511-008_007.pdf → EXC-2511-008
        
        Returns:
            เลขที่เอกสาร (เช่น EXC-2511-008)
        """
        # ลบ .pdf ออกก่อน
        name_without_ext = filename.replace('.pdf', '').replace('.PDF', '')
        
        # Pattern: EXC-2511-008_007 → เอาแค่ EXC-2511-008
        # หรือ EXC-2511-008 → เอาทั้งหมด
        parts = name_without_ext.split('_')
        if parts:
            return parts[0]
        
        return name_without_ext
    
    def extract_invoice_number_from_text(self, text: str) -> Optional[str]:
        """
        ดึงเลขที่ใบแจ้งหนี้จากข้อความ (สำหรับเปลี่ยนชื่อไฟล์)
        
        Pattern: No. 2511200301
        
        Returns:
            เลขที่ใบแจ้งหนี้
        """
        # Pattern: No. 2511200301
        pattern = r'No\.\s*(\d{10,})'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        return None
    
    def extract_all_data(self, text: str, filename: str) -> Dict[str, Any]:
        """
        ดึงข้อมูลทั้งหมดจากเอกสาร MSC
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด:
            {
                'is_msc': bool,
                'company_name': str,
                'tax_id': str,
                'date': str,  # dd/mm/yyyy
                'non_taxable_amount': float,
                'total_amount': float,
                'remark': str,  # เลขที่เอกสารจากชื่อไฟล์
                'new_filename': str,  # ชื่อไฟล์ใหม่
                'old_filename': str  # ชื่อไฟล์เก่า
            }
        """
        result = {
            'is_msc': self.is_msc_document(text),
            'company_name': None,
            'tax_id': None,
            'date': None,
            'non_taxable_amount': None,
            'total_amount': None,
            'remark': None,
            'new_filename': None,
            'old_filename': filename
        }
        
        if not result['is_msc']:
            return result
        
        # ดึงข้อมูลทีละฟิลด์
        result['company_name'] = self.extract_company_name(text)
        result['tax_id'] = self.extract_tax_id(text)
        result['date'] = self.extract_date(text)
        result['non_taxable_amount'] = self.extract_non_taxable_amount(text)
        result['total_amount'] = self.extract_total_amount(text)
        
        # หมายเหตุ: เลขที่เอกสารจากชื่อไฟล์
        result['remark'] = self.extract_document_number_from_filename(filename)
        
        # ชื่อไฟล์ใหม่: ใช้เลขที่ใบแจ้งหนี้จากเอกสาร
        invoice_number = self.extract_invoice_number_from_text(text)
        if invoice_number:
            result['new_filename'] = f"{invoice_number}.pdf"
        
        return result


# ===== Helper Functions =====

def extract_msc_data(text: str, filename: str) -> Dict[str, Any]:
    """
    Helper function สำหรับดึงข้อมูล MSC
    
    Args:
        text: ข้อความที่อ่านจาก OCR
        filename: ชื่อไฟล์ PDF
    
    Returns:
        Dictionary ที่มีข้อมูลทั้งหมด
    """
    extractor = MSCDataExtractor()
    return extractor.extract_all_data(text, filename)


# ===== Usage Example =====
if __name__ == "__main__":
    # ตัวอย่างการใช้งาน
    sample_text = """
    MSC Mediterranean Shipping Company S.A.
    C/O Mediterranean Shipping (Thailand) Co., Ltd.
    Head Office: MSC Building, 571 Sukhumvit 71 Rd., Klongton-Nua, Vadhana,
    Bangkok 10,110 Tel: +66(0)2,460-6,400
    
    TaxID 9930000036677
    
    TAX INVOICE/RECEIPT
    ต้นฉบับใบกำกับภาษี / ต้นฉบับใบเสร็จรับเงิน
    
    No. 2511200301
    
    Date / วันที่ 03-NOV-2025 Branch No : 0
    
    Non-Taxable Amount / ไม่มีภาษีมูลค่าเพิ่ม 6,000.00
    Total / รวม 6,000.00
    """
    
    filename = "EXC-2511-008_007.pdf"
    
    result = extract_msc_data(sample_text, filename)
    
    print("=" * 80)
    print("🔍 MSC Data Extraction Result")
    print("=" * 80)
    print(f"Is MSC Document: {result['is_msc']}")
    print(f"Company Name: {result['company_name']}")
    print(f"Tax ID: {result['tax_id']}")
    print(f"Date: {result['date']}")
    print(f"Non-Taxable Amount: {result['non_taxable_amount']}")
    print(f"Total Amount: {result['total_amount']}")
    print(f"Remark: {result['remark']}")
    print(f"New Filename: {result['new_filename']}")
    print(f"Old Filename: {result['old_filename']}")
    print("=" * 80)

