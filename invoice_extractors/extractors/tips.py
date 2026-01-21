"""
TIPS Invoice Extractor
=======================
Extractor สำหรับดึงข้อมูลจาก บริษัท ที ไอ พี เอส จำกัด

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class TIPSExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก บริษัท ที ไอ พี เอส จำกัด"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "ที ไอ พี เอส",
        "TIPS",
        "T I P S"
    ]
    
    def __init__(self):
        """Initialize TIPS Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ TIPS หรือไม่
        ตรวจสอบจากชื่อบริษัทและรูปแบบเอกสารเฉพาะ
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร TIPS
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท "ที ไอ พี เอส" หรือ "TIPS"
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมีรูปแบบเอกสารเฉพาะ เช่น "TIPS CO . LTD." หรือ "Receipt /Tax Invoice No."
        has_specific_format = (
            "TIPS CO" in text or 
            "Receipt /Tax Invoice No" in text or
            "LAEM CHABANG PORT" in text
        )
        
        # ต้องมีทั้งชื่อบริษัทและรูปแบบเอกสารเฉพาะถึงจะผ่าน
        return has_company and has_specific_format
    
    def extract_company_name(self, text: str) -> str:
        """ดึงชื่อบริษัท"""
        return "บริษัท ที ไอ พี เอส จำกัด"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี (กำหนดให้ระบบกรอกให้เองอัตโนมัติ)"""
        return "0105532051576"
    
    def extract_branch(self, text: str) -> Optional[str]:
        """ดึงสาขา (กำหนดให้ระบบกรอกให้เองอัตโนมัติ)"""
        return "00001"
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่จาก 'วันที่ Date 13.11.2025' และแปลงเป็น dd/mm/yyyy (เช่น 13/11/2025)"""
        # Pattern: วันที่ Date 13.11.2025
        patterns = [
            r'วันที่\s+Date\s*[:.]?\s*(\d{1,2})\.(\d{1,2})\.(\d{4})',  # วันที่ Date 13.11.2025
            r'วันที่\s*[:.]?\s*(\d{1,2})\.(\d{1,2})\.(\d{4})',  # วันที่ 13.11.2025
            r'Date\s*[:.]?\s*(\d{1,2})\.(\d{1,2})\.(\d{4})',  # Date 13.11.2025
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                day = match.group(1).zfill(2)
                month = match.group(2).zfill(2)
                year = match.group(3)
                return f"{day}/{month}/{year}"
        
        return None
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """ดึงเลขที่เอกสารจาก 'Receipt /Tax Invoice No .: CS14251106005'"""
        # Pattern: Receipt /Tax Invoice No .: CS14251106005
        # ต้องระวังไม่ให้จับคำว่า "Cheque" หรือคำอื่นๆ ที่ไม่ใช่เลขที่เอกสาร
        patterns = [
            # รูปแบบหลัก: Receipt /Tax Invoice No .: CS14251106005 (มีช่องว่างหลัง No)
            r'Receipt\s*/?\s*Tax\s+Invoice\s+No\s*\.?\s*[:.]?\s*([A-Z]{2}\d{11})',  # CS14251106005 (2 ตัวอักษร + 11 ตัวเลข)
            r'Receipt\s*/?\s*Tax\s+Invoice\s+No\s*\.?\s*[:.]?\s*([A-Z]{2}\d+)',  # CS14251106005 (2 ตัวอักษร + ตัวเลข)
            r'Receipt\s*/?\s*Tax\s+Invoice\s+No\.\s*[:.]?\s*([A-Z]{2}\d{11})',  # Receipt /Tax Invoice No.: CS14251106005
            r'Receipt\s*/?\s*Tax\s+Invoice\s+No\.\s*[:.]?\s*([A-Z]{2}\d+)',  # Receipt /Tax Invoice No.: CS14251106005
            # รูปแบบอื่นๆ
            r'Receipt\s+No\s*\.?\s*[:.]?\s*([A-Z]{2}\d{11})',  # Receipt No .: CS14251106005
            r'Receipt\s+No\s*\.?\s*[:.]?\s*([A-Z]{2}\d+)',  # Receipt No .: CS14251106005
            r'Invoice\s+No\s*\.?\s*[:.]?\s*([A-Z]{2}\d{11})',  # Invoice No .: CS14251106005
            r'Invoice\s+No\s*\.?\s*[:.]?\s*([A-Z]{2}\d+)',  # Invoice No .: CS14251106005
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doc_no = match.group(1).strip()
                # ตรวจสอบว่าไม่ใช่คำที่ไม่ใช่เลขที่เอกสาร
                if doc_no and doc_no.upper() not in ['CHEQUE', 'CHEQUE NO', 'NO']:
                    # ตรวจสอบว่าเป็นรูปแบบที่ถูกต้อง (เริ่มต้นด้วยตัวอักษร ตามด้วยตัวเลข)
                    if re.match(r'^[A-Z]{2,}\d+', doc_no, re.IGNORECASE):
                        logger.info(f"✅ พบเลขที่เอกสาร: {doc_no}")
                    return doc_no
        
        return None
    
    def extract_address(self, text: str) -> Optional[str]:
        """
        ดึงข้อมูลที่อยู่บริษัท (กำหนดให้ระบบกรอกให้เองอัตโนมัติ)
        
        ที่อยู่: ซอยท่าบี 4 ท่าเรือแหลมฉบัง ตำบลทุ่งสุขลา อำเภอศรีราชา จ.ชลบุรี 20230
        
        Returns:
            ที่อยู่รวม (string)
        """
        return "ซอยท่าบี 4 ท่าเรือแหลมฉบัง ตำบลทุ่งสุขลา อำเภอศรีราชา จ.ชลบุรี 20230"
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """ดึงข้อมูลบัญชี (Account Name / Account Code)"""
        return {
            'account_name': 'ค่าใช้จ่ายอื่นๆในการซื้อสินค้า',
            'account_code': None
        }
    
    def extract_withholding_tax(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงข้อมูลหัก ณ ที่จ่าย
        
        ถ้าเจอคำว่า "ภาษีหัก ณ ที่จ่าย Baht VAT 30.00 บาท" (หรือรูปแบบคล้ายๆ กัน)
        และยอดไม่ใช่ 0 ให้กรอกข้อมูล 3 ในคอลลัม เปอร์เซ็นต์หัก ณ ที่จ่าย
        """
        # Pattern: ภาษีหัก ณ ที่จ่าย Baht VAT 30.00 บาท
        # หรือรูปแบบอื่นๆ เช่น:
        # - ภาษีหัก ณ ที่จ่าย Baht VAT 30.00 บาท
        # - ภาษีหัก ณ ที่จ่าย 30.00 บาท
        # - ภาษีหัก ณ ที่จ่าย VAT 30.00
        patterns = [
            r'ภาษีหัก\s*ณ\s*ที่จ่าย\s+Baht\s+VAT\s+([\d,]+\.?\d*)\s*บาท',  # ภาษีหัก ณ ที่จ่าย Baht VAT 30.00 บาท
            r'ภาษีหัก\s*ณ\s*ที่จ่าย\s+VAT\s+([\d,]+\.?\d*)\s*บาท',  # ภาษีหัก ณ ที่จ่าย VAT 30.00 บาท
            r'ภาษีหัก\s*ณ\s*ที่จ่าย\s+([\d,]+\.?\d*)\s*บาท',  # ภาษีหัก ณ ที่จ่าย 30.00 บาท
            r'ภาษีหัก\s*ณ\s*ที่จ่าย\s+Baht\s+([\d,]+\.?\d*)',  # ภาษีหัก ณ ที่จ่าย Baht 30.00
            r'ภาษีหัก\s*ณ\s*ที่จ่าย\s+VAT\s+([\d,]+\.?\d*)',  # ภาษีหัก ณ ที่จ่าย VAT 30.00
            r'ภาษีหัก\s*ณ\s*ที่จ่าย\s*[:.]?\s*([\d,]+\.?\d*)',  # ภาษีหัก ณ ที่จ่าย: 30.00
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '').strip()
                try:
                    amount_val = float(amount_str)
                    # ตรวจสอบว่ายอดไม่ใช่ 0
                    if amount_val > 0:
                        logger.info(f"✅ พบภาษีหัก ณ ที่จ่าย: {amount_val} บาท - กำหนดเปอร์เซ็นต์หัก ณ ที่จ่ายเป็น 3%")
                        return {
                            'withholding_tax_percent': 3.0,  # กำหนดเป็น 3%
                            'withholding_tax_amount': amount_val
                        }
                except ValueError:
                    pass
        
        # ถ้าไม่เจอหรือยอดเป็น 0 ไม่ต้องกรอกข้อมูล
        logger.info("⚠️ ไม่พบภาษีหัก ณ ที่จ่ายหรือยอดเป็น 0 - ไม่กรอกข้อมูลเปอร์เซ็นต์หัก ณ ที่จ่าย")
        return {
            'withholding_tax_percent': None,
            'withholding_tax_amount': None
        }
    
    def _extract_from_html_table(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงข้อมูลจากตาราง HTML โดยค้นหา Total After Disc, VAT, และ Grand Total
        
        Args:
            text: ข้อความที่อ่านจาก OCR (อาจมี HTML table)
        
        Returns:
            Dictionary ที่มีข้อมูลที่ดึงได้
        """
        result = {
            'amount_before_vat': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        try:
            # หาตาราง HTML ทั้งหมด
            table_pattern = r'<table[^>]*>(.*?)</table>'
            tables = re.findall(table_pattern, text, re.DOTALL | re.IGNORECASE)
            
            if not tables:
                return result
            
            # วนลูปทุกตาราง
            for table_html in tables:
                # แยก rows
                rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL | re.IGNORECASE)
                
                # วนลูปทุกแถวเพื่อหาข้อมูล
                for row in rows:
                    # แยก cells
                    cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL | re.IGNORECASE)
                    
                    if not cells:
                        continue
                    
                    # ทำความสะอาด cell content
                    cleaned_cells = []
                    for cell in cells:
                        # ลบ HTML tags
                        cell_text = re.sub(r'<[^>]+>', '', cell)
                        # ลบช่องว่างส่วนเกิน
                        cell_text = re.sub(r'\s+', ' ', cell_text).strip()
                        cleaned_cells.append(cell_text)
                    
                    if len(cleaned_cells) < 2:
                        continue
                    
                    # ตรวจสอบว่าเป็นแถวที่ต้องการ
                    row_text = ' '.join(cleaned_cells)
                    row_upper = row_text.upper()
                    
                    # หา Total After Disc
                    if 'TOTAL' in row_upper and 'AFTER' in row_upper and 'DISC' in row_upper and not result['amount_before_vat']:
                        # หาตัวเลขใน cell สุดท้าย
                        last_cell = cleaned_cells[-1].strip()
                        amount_match = re.search(r'(\d{1,3}(?:,\d{3})*\.?\d{2})', last_cell)
                        if amount_match:
                            try:
                                result['amount_before_vat'] = float(amount_match.group(1).replace(',', ''))
                            except ValueError:
                                pass
                    
                    # หา VAT
                    if 'VAT' in row_upper and not result['vat_amount']:
                        # หาตัวเลขใน cell สุดท้าย
                        last_cell = cleaned_cells[-1].strip()
                        vat_match = re.search(r'(\d{1,3}(?:,\d{3})*\.?\d{2})', last_cell)
                        if vat_match:
                            try:
                                result['vat_amount'] = float(vat_match.group(1).replace(',', ''))
                            except ValueError:
                                pass
                    
                    # หา Grand Total
                    if 'GRAND' in row_upper and 'TOTAL' in row_upper and not result['total_amount']:
                        # หาตัวเลขใน cell สุดท้าย
                        last_cell = cleaned_cells[-1].strip()
                        total_match = re.search(r'(\d{1,3}(?:,\d{3})*\.?\d{2})', last_cell)
                        if total_match:
                            try:
                                result['total_amount'] = float(total_match.group(1).replace(',', ''))
                            except ValueError:
                                pass
                
                # ถ้าได้ข้อมูลครบแล้ว ให้ return
                if result['amount_before_vat'] and result['vat_amount'] and result['total_amount']:
                    logger.info(f"✅ ดึงยอดเงินจากตาราง HTML สำเร็จ: amount_before_vat={result['amount_before_vat']}, vat_amount={result['vat_amount']}, total_amount={result['total_amount']}")
                    return result
            
        except Exception as e:
            logger.warning(f"⚠️ เกิดข้อผิดพลาดในการดึงข้อมูลจากตาราง HTML: {e}")
        
        return result
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงข้อมูลยอดเงิน
        
        - ยอดก่อนภาษีมูลค่าเพิ่ม: Total After Disc 1,000.00
        - ภาษีมูลค่าเพิ่ม: VAT 70.00
        - ยอดหลังบวกภาษีมูลค่าเพิ่ม: Grand Total 1,070.00
        """
        amounts = {
            'amount_before_vat': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        # วิธีที่ 0: ลองดึงจาก HTML table ก่อน (ถ้าหน้าเว็บอ่านได้)
        html_table_result = self._extract_from_html_table(text)
        if html_table_result.get('amount_before_vat') or html_table_result.get('vat_amount') or html_table_result.get('total_amount'):
            amounts.update(html_table_result)
            # ถ้าได้ข้อมูลครบแล้ว ให้ return
            if amounts['amount_before_vat'] and amounts['vat_amount'] and amounts['total_amount']:
                return amounts
        
        # ยอดก่อนภาษีมูลค่าเพิ่ม: Total After Disc 1,000.00
        amount_patterns = [
            r'Total\s+After\s+Disc\s+([\d,]+\.?\d*)',
            r'Total\s+After\s+Discount\s+([\d,]+\.?\d*)',
            r'Total\s+([\d,]+\.?\d*)',
        ]
        for pattern in amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '').strip()
                try:
                    amount_val = float(amount_str)
                    if amount_val > 0:
                        amounts['amount_before_vat'] = amount_val
                        break
                except ValueError:
                    pass
        
        # ภาษีมูลค่าเพิ่ม: VAT 70.00
        vat_patterns = [
            r'VAT\s+([\d,]+\.?\d*)',
            r'ภาษีมูลค่าเพิ่ม\s+([\d,]+\.?\d*)',
            r'VAT\s+7%\s+([\d,]+\.?\d*)',
        ]
        for pattern in vat_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                vat_str = match.group(1).replace(',', '').strip()
                try:
                    vat_val = float(vat_str)
                    if vat_val > 0:
                        amounts['vat_amount'] = vat_val
                        break
                except ValueError:
                    pass
        
        # ยอดหลังบวกภาษีมูลค่าเพิ่ม: Grand Total 1,070.00
        total_patterns = [
            r'Grand\s+Total\s+([\d,]+\.?\d*)',
            r'GRAND\s+TOTAL\s+([\d,]+\.?\d*)',
            r'Total\s+Amount\s+([\d,]+\.?\d*)',
        ]
        for pattern in total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                total_str = match.group(1).replace(',', '').strip()
                try:
                    total_val = float(total_str)
                    if total_val > 0:
                        amounts['total_amount'] = total_val
                        break
                except ValueError:
                    pass
        
        return amounts
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงหมายเหตุ (ถ้ามี)"""
        remark_parts = []
        
        # เพิ่มชื่อไฟล์ (ตัด WHT_, VAT_, None_vat_ ออก)
        if filename:
            filename_clean = filename
            filename_clean = re.sub(r'(WHT_|VAT_|None_vat_)', '', filename_clean, flags=re.IGNORECASE)
            filename_clean = re.sub(r'\.pdf$', '', filename_clean, flags=re.IGNORECASE)
            if filename_clean:
                remark_parts.append(filename_clean)
        
        if remark_parts:
            return ' '.join(remark_parts)
        
        return None
    
    def detect_document_type(self, text: str, amounts: Dict[str, Optional[float]], withholding: Dict[str, Optional[float]]) -> int:
        """ตรวจสอบประเภทเอกสาร (1 = มีภาษีมูลค่าเพิ่ม)"""
        return 1  # มีภาษีมูลค่าเพิ่ม
    
    def extract_all_data(self, text: str, filename: str = None, filepath: str = None) -> Dict[str, Any]:
        """
        ดึงข้อมูลทั้งหมดจากเอกสาร
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ (optional)
            filepath: path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # หาส่วนต้นฉบับของใบกำกับภาษีก่อน
        original_section = self.extract_original_invoice_section(text)
        if original_section:
            # ใช้เฉพาะส่วนต้นฉบับในการดึงข้อมูล
            text = original_section
            logger.info("✅ ใช้เฉพาะส่วนต้นฉบับของใบกำกับภาษีในการดึงข้อมูล")
        
        # ดึงข้อมูล
        company_name = self.extract_company_name(text)
        tax_id = self.extract_tax_id(text)
        branch = self.extract_branch(text)
        date = self.extract_date(text)
        document_number = self.extract_document_number(text)
        address = self.extract_address(text)
        account_info = self.extract_account_info(text)
        amounts = self.extract_amounts(text)
        withholding = self.extract_withholding_tax(text)
        remark = self.extract_remark(text, filename)
        document_type = self.detect_document_type(text, amounts, withholding)
        
        # สร้างชื่อไฟล์ใหม่ (ตัด VAT_, None_vat_, WHT_)
        new_filename = filename
        if new_filename:
            new_filename = re.sub(r'(VAT_|None_vat_|WHT_)', '', new_filename, flags=re.IGNORECASE)
        
        # แยกที่อยู่เป็นส่วนๆ
        # ที่อยู่: ซอยท่าบี 4 ท่าเรือแหลมฉบัง ตำบลทุ่งสุขลา อำเภอศรีราชา จ.ชลบุรี 20230
        address_full = address or ''
        building_number = ''  # (ว่าง)
        other_info = ''  # ซอยท่าบี 4 ท่าเรือแหลมฉบัง
        soi = ''  # ซอย/ตรอก
        road = ''  # (ว่าง)
        subdistrict = ''  # ตำบลทุ่งสุขลา
        district = ''  # อำเภอศรีราชา
        province = ''  # จังหวัดชลบุรี
        postal_code = ''  # รหัสไปรษณีย์ 20230
        
        if address:
            # ดึงอื่นๆ จาก "ซอยท่าบี 4 ท่าเรือแหลมฉบัง" (ก่อนตำบล)
            other_match = re.search(r'^(.+?)(?=\s+ตำบล)', address)
            if other_match:
                other_info = other_match.group(1).strip()
            
            # ดึงตำบลจาก "ตำบลทุ่งสุขลา"
            subdistrict_match = re.search(r'ตำบล\s*([ก-๙A-Za-z]+)', address)
            if subdistrict_match:
                subdistrict = subdistrict_match.group(1).strip()
            
            # ดึงอำเภอจาก "อำเภอศรีราชา"
            district_match = re.search(r'อำเภอ\s*([ก-๙A-Za-z]+)', address)
            if district_match:
                district = district_match.group(1).strip()
            
            # ดึงจังหวัดจาก "จ.ชลบุรี" หรือ "ชลบุรี"
            province_match = re.search(r'จ\.?\s*(ชลบุรี)', address)
            if province_match:
                province = province_match.group(1).strip()
            elif 'ชลบุรี' in address:
                province = 'ชลบุรี'
            
            # ดึงรหัสไปรษณีย์ (5 หลัก)
            postal_match = re.search(r'(\d{5})\s*$', address)
            if postal_match:
                postal_code = postal_match.group(1).strip()
        
        return {
            'success': True,
            'company': 'TIPS',
            'company_name': company_name,
            'tax_id': tax_id,
            'branch': branch,
            'date': date,
            'document_number': document_number,
            'address': address,  # ที่อยู่รวม
            'address_full': address_full,  # ที่อยู่รวม (สำหรับ parse_address)
            'building_number': building_number or '',  # เลขที่ (ว่าง)
            'other_info': other_info or '',  # อื่นๆ (ซอยท่าบี 4 ท่าเรือแหลมฉบัง)
            'soi': soi or '',  # ซอย/ตรอก
            'road': road or '',  # ถนน (ว่าง)
            'subdistrict': subdistrict or '',  # ตำบล (ทุ่งสุขลา)
            'district': district or '',  # อำเภอ (ศรีราชา)
            'province': province or '',  # จังหวัด (ชลบุรี)
            'postal_code': postal_code or '',  # รหัสไปรษณีย์ (20230)
            'account_name': account_info['account_name'],
            'account_code': account_info['account_code'],
            'withholding_tax_percent': withholding['withholding_tax_percent'],
            'withholding_tax_amount': withholding['withholding_tax_amount'],
            'amount_before_vat': amounts['amount_before_vat'],
            'vat_amount': amounts['vat_amount'],
            'total_amount': amounts['total_amount'],
            'remark': remark,
            'new_filename': new_filename,
            'old_filename': filename,
            'filepath': filepath,
            'document_type': document_type,  # 1 = มีภาษีมูลค่าเพิ่ม
        }
