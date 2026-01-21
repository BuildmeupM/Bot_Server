"""
Hutchison Laemchabang Terminal Invoice Extractor
=================================================
Extractor สำหรับดึงข้อมูลจาก Hutchison Laemchabang Terminal Limited

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class HutchisonLaemchabangTerminalExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก Hutchison Laemchabang Terminal Limited"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "Hutchison Laemchabang Terminal",
        "Hutchison Laemchabang Terminal Limited",
        "HUTCHISONPORTS THAILAND",
        "Hutchison Laemchabang",
        "Thai Laemchabang Terminal",  # รองรับ Thai Laemchabang Terminal Co., Ltd.
        "Thai Laemchabang Terminal Co., Ltd."
    ]
    
    def __init__(self):
        """Initialize Hutchison Laemchabang Terminal Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ Hutchison Laemchabang Terminal หรือไม่
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร Hutchison Laemchabang Terminal
        """
        if not text:
            return False
        
        # ตรวจสอบชื่อบริษัท
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # ตรวจสอบ Tax ID (รองรับหลาย Tax ID ที่เป็นไปได้)
        # "0105 5471 35401" หรือ "0105547135401" (เดิม)
        # "0105 5473 5401" หรือ "010554735401" (รูปแบบใหม่)
        # "0205539005838" (Thai Laemchabang Terminal)
        has_tax_id = (
            "0105 5471 35401" in text or "0105547135401" in text or
            "0105 5473 5401" in text or "010554735401" in text or
            "0205539005838" in text or
            ("TAX ID" in text.upper() and ("0105547" in text.replace(' ', '').replace('-', '') or "0205539" in text.replace(' ', '').replace('-', '')))
        )
        
        # ต้องมีทั้งชื่อบริษัทและ Tax ID
        return has_company and has_tax_id
    
    def extract_company_name(self, text: str) -> str:
        """ดึงชื่อบริษัท"""
        # ตรวจสอบว่าเป็น Thai Laemchabang Terminal หรือไม่
        if "Thai Laemchabang Terminal" in text:
            return "Thai Laemchabang Terminal Co., Ltd."
        return "Hutchison Laemchabang Terminal Limited"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern: TAX ID. 0105 5471 35401 หรือ TAX ID. 0105547135401
        patterns = [
            r'TAX\s+ID[.:]?\s*(\d{4}\s+\d{4}\s+\d{5})',  # TAX ID. 0105 5471 35401
            r'TAX\s+ID[.:]?\s*(\d{13})',  # TAX ID. 0105547135401
            r'Tax\s+ID[.:]?\s*(\d{4}\s+\d{4}\s+\d{5})',  # Tax ID. 0105 5471 35401
            r'Tax\s+ID[.:]?\s*(\d{13})',  # Tax ID. 0105547135401
            r'TaxID\s*[:.]?\s*(\d{13})',  # TaxID: 0105547135401
            r'TAXID\s*[:.]?\s*(\d{13})',  # TAXID: 0105547135401
            r'Tax\s+ID\s+No[.:]?\s*(\d{13})',  # Tax ID No.: 0105547135401
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษี: 0105547135401
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*(\d{4}\s+\d{4}\s+\d{5})',  # เลขประจำตัวผู้เสียภาษี: 0105 5471 35401
            r'(\d{4}\s+\d{4}\s+\d{5})',  # 0105 5471 35401 (รูปแบบทั่วไป)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                tax_id = match.group(1).replace(' ', '')  # ลบช่องว่าง
                if len(tax_id) == 13:
                    # รองรับทั้ง Tax ID เดิมและใหม่ รวมถึง Thai Laemchabang Terminal
                    if tax_id in ["0105547135401", "010554735401", "0205539005838"]:
                        return tax_id
        
        # Fallback: ตรวจสอบว่า Tax ID อยู่ใน text หรือไม่ (รองรับช่องว่างและขีด)
        text_clean = text.replace(' ', '').replace('-', '')
        if "0105547135401" in text_clean:
            return "0105547135401"
        if "010554735401" in text_clean:
            return "010554735401"
        if "0205539005838" in text_clean:
            return "0205539005838"
        
        # ลองหาจากรูปแบบทั่วไป: ตัวเลข 13 หลักที่อยู่ใกล้กับคำว่า Tax, ID, หรือเลขประจำตัว
        general_patterns = [
            r'(?:Tax|TAX|เลขประจำตัวผู้เสียภาษี)[^0-9]*(\d{13})',
            r'(\d{4}\s*\d{4}\s*\d{5})',  # รูปแบบที่มีช่องว่าง: 0105 5471 35401
        ]
        
        for pattern in general_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                tax_id = match.group(1).replace(' ', '').replace('-', '')
                if len(tax_id) == 13:
                    # รองรับทั้ง Tax ID เดิมและใหม่ รวมถึง Thai Laemchabang Terminal
                    if tax_id in ["0105547135401", "010554735401", "0205539005838"]:
                        return tax_id
        
        # Fallback: ถ้าระบบอ่าน Tax ID ไม่ได้ ให้ใช้ค่า default
        logger.info("⚠️ ไม่พบเลขประจำตัวผู้เสียภาษีในเอกสาร - ใช้ค่า default: 0105547135401")
        return "0105547135401"
    
    def extract_branch(self, text: str) -> Optional[str]:
        """ดึงสาขา"""
        # Pattern: Branch No. 3 หรือ Branch No.3 หรือ Branch: 3
        patterns = [
            r'Branch\s+No[.:]?\s*(\d+)',  # Branch No. 3 หรือ Branch No: 3
            r'Branch\s+No[.:]?\s*[.:]?\s*(\d+)',  # Branch No.: 3
            r'สาขา\s*[:.]?\s*(\d+)',  # สาขา: 3
            r'Branch\s*[:.]?\s*(\d+)',  # Branch: 3
            r'Branch\s*(\d+)',  # Branch 3
            # รูปแบบที่มีช่องว่างหรือตัวอักษรอื่นๆ
            r'Branch[^\d]*(\d+)',  # Branch ... 3
            r'สาขา[^\d]*(\d+)',  # สาขา ... 3
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                branch = match.group(1).strip()
                if branch:
                    branch_formatted = branch.zfill(5)  # เติม 0 นำหน้าให้ครบ 5 หลัก
                    logger.info(f"✅ พบสาขา: {branch_formatted} (จาก: {branch})")
                    return branch_formatted
        
        # Fallback: ลองหาจากรูปแบบทั่วไป (ตัวเลขที่อยู่ใกล้กับคำว่า Branch)
        fallback_patterns = [
            r'Branch[^\n]*?(\d{1,5})',  # Branch ... 3
            r'สาขา[^\n]*?(\d{1,5})',  # สาขา ... 3
        ]
        
        for pattern in fallback_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                branch = match.group(1).strip()
                if branch and len(branch) <= 5:  # ตรวจสอบว่าไม่เกิน 5 หลัก
                    branch_formatted = branch.zfill(5)
                    logger.info(f"✅ พบสาขา (fallback): {branch_formatted} (จาก: {branch})")
                    return branch_formatted
        
        logger.warning("⚠️ ไม่พบสาขาในเอกสาร")
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่และแปลงเป็น dd/mm/yyyy"""
        # Pattern: วันที่ / Date 20-Nov-2025 หรือ Date 20-Nov-2025
        patterns = [
            r'วันที่\s*/?\s*Date\s*(\d{1,2})-([A-Za-z]{3})-(\d{4})',
            r'Date\s*(\d{1,2})-([A-Za-z]{3})-(\d{4})',
            r'วันที่\s*[:.]?\s*(\d{1,2})-([A-Za-z]{3})-(\d{4})',
        ]
        
        month_map = {
            'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04',
            'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
            'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
        }
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                day = match.group(1).zfill(2)
                month_abbr = match.group(2).upper()
                year = match.group(3)
                
                month = month_map.get(month_abbr, '01')
                
                return f"{day}/{month}/{year}"
        
        return None
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """ดึงเลขที่เอกสาร"""
        # Pattern: เลขที่ / No. C1C2 CA2511-4466325 หรือ CA2511-4466325
        patterns = [
            r'เลขที่\s*/?\s*No[.:]?\s*[A-Z0-9]+\s+([A-Z0-9\-]+)',  # เลขที่ / No. C1C2 CA2511-4466325
            r'No[.:]?\s*[A-Z0-9]+\s+([A-Z0-9\-]+)',  # No. C1C2 CA2511-4466325
            r'([A-Z]{2}\d{4}-\d{7})',  # CA2511-4466325
            r'เลขที่\s*[:.]?\s*([A-Z0-9\-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doc_no = match.group(1).strip()
                if doc_no and len(doc_no) > 5:  # ตรวจสอบว่ามีความยาวพอสมควร
                    return doc_no
        
        return None
    
    def extract_address(self, text: str) -> Optional[str]:
        """
        ดึงข้อมูลที่อยู่บริษัท
        
        ที่อยู่: 88/4 Moo 3 Tungsukhla, Sriracha, Chonburi 20230
        """
        # Pattern: หาที่อยู่หลังชื่อบริษัท
        # 88/4 Moo 3 Tungsukhla, Sriracha, Chonburi 20230
        patterns = [
            r'88/4\s+Moo\s+3[^.]*Chonburi\s+20230',
            r'88/4[^.]*Chonburi\s+20230',
            r'Tungsukhla[^.]*Chonburi\s+20230',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                address = match.group(0).strip()
                return address
        
        # Fallback: ใช้ที่อยู่ default
        return "88/4 Moo 3 Tungsukhla, Sriracha, Chonburi 20230"
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """ดึงข้อมูลบัญชี (Account Name / Account Code)"""
        # กำหนดชื่อบัญชีเป็น "ค่าใช้จ่ายอื่นๆในการซื้อสินค้า" (ค่าคงที่)
        return {
            'account_name': 'ค่าใช้จ่ายอื่นๆในการซื้อสินค้า',
            'account_code': None
        }
    
    def extract_withholding_tax(self, text: str) -> Dict[str, Optional[float]]:
        """ดึงข้อมูลหัก ณ ที่จ่าย"""
        result = {
            'withholding_tax_percent': None,
            'withholding_tax_amount': None
        }
        
        # Pattern: หักภาษี ณ. ที่จ่าย / WHT 3.00% 0.00 บาท /Baht
        # หรือ หักภาษี ณ. ที่จ่าย / WHT 3.00% 30.00 บาท /Baht
        patterns = [
            r'หักภาษี\s*ณ[.]?\s*ที่จ่าย\s*/?\s*WHT\s*(\d+\.?\d*)%\s+([\d,]+\.?\d*)\s*บาท',  # หักภาษี ณ. ที่จ่าย / WHT 3.00% 0.00 บาท
            r'WHT\s*(\d+\.?\d*)%\s+([\d,]+\.?\d*)\s*บาท',  # WHT 3.00% 0.00 บาท
            r'หัก\s*ภาษี\s*ณ[.]?\s*ที่จ่าย\s*(\d+\.?\d*)%\s+([\d,]+\.?\d*)\s*บาท',  # หักภาษี ณ ที่จ่าย 3% 0.00 บาท
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    percent = float(match.group(1))
                    amount_str = match.group(2).replace(',', '').strip()
                    amount = float(amount_str)
                    
                    # เงื่อนไข: ถ้า amount เป็น 0.00 บาท → ไม่ต้องกรอกเปอร์เซ็นต์หัก ณ ที่จ่าย
                    # ถ้า amount ไม่ใช่ 0.00 บาท → กรอกเปอร์เซ็นต์หัก ณ ที่จ่ายเป็น 3%
                    if amount == 0.00:
                        result['withholding_tax_percent'] = None
                        result['withholding_tax_amount'] = 0.0
                        logger.info(f"✅ พบ WHT {percent}% แต่ยอดเป็น 0.00 บาท - ไม่กรอกเปอร์เซ็นต์หัก ณ ที่จ่าย")
                    else:
                        result['withholding_tax_percent'] = 3.0  # กำหนดเป็น 3% ตามที่ระบุ
                        result['withholding_tax_amount'] = amount
                        logger.info(f"✅ พบ WHT {percent}% ยอด {amount} บาท - กรอกเปอร์เซ็นต์หัก ณ ที่จ่ายเป็น 3%")
                    
                    break
                except (ValueError, IndexError):
                    continue
        
        # ถ้ายังไม่พบ ให้ลองหาแค่เปอร์เซ็นต์ (fallback)
        if result['withholding_tax_percent'] is None and result['withholding_tax_amount'] is None:
            percent_patterns = [
                r'หักภาษี\s*ณ[.]?\s*ที่จ่าย\s*/?\s*WHT\s*(\d+\.?\d*)%',
                r'WHT\s*(\d+\.?\d*)%',
                r'หัก\s*ภาษี\s*ณ[.]?\s*ที่จ่าย\s*(\d+\.?\d*)%',
            ]
            
            for pattern in percent_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        percent = float(match.group(1))
                        # หายอดเงินหัก ณ ที่จ่าย
                        amount_pattern = rf'WHT\s*{re.escape(match.group(1))}%\s*([\d,]+\.?\d*)'
                        amount_match = re.search(amount_pattern, text, re.IGNORECASE)
                        if amount_match:
                            amount_str = amount_match.group(1).replace(',', '').strip()
                            amount = float(amount_str)
                            
                            # เงื่อนไข: ถ้า amount เป็น 0.00 บาท → ไม่ต้องกรอกเปอร์เซ็นต์หัก ณ ที่จ่าย
                            if amount == 0.00:
                                result['withholding_tax_percent'] = None
                                result['withholding_tax_amount'] = 0.0
                                logger.info(f"✅ พบ WHT {percent}% แต่ยอดเป็น 0.00 บาท - ไม่กรอกเปอร์เซ็นต์หัก ณ ที่จ่าย")
                            else:
                                result['withholding_tax_percent'] = 3.0  # กำหนดเป็น 3% ตามที่ระบุ
                                result['withholding_tax_amount'] = amount
                                logger.info(f"✅ พบ WHT {percent}% ยอด {amount} บาท - กรอกเปอร์เซ็นต์หัก ณ ที่จ่ายเป็น 3%")
                        break
                    except (ValueError, IndexError):
                        continue
        
        return result
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงข้อมูลยอดเงิน
        
        - ค่าสินค้าและบริการ / Tariff charges 1,000.00 บาท /Baht
        - ภาษีมูลค่าเพิ่ม / VAT 7.00% 70.00 บาท /Baht
        - จำนวนเงินรวมทั้งสิ้น / Grand total 1,070.00 บาท /Baht
        - ค่าสินค้าและบริการสุทธิ / Net total 1,040.00 บาท /Baht (หลังหัก WHT)
        """
        amounts = {
            'amount_before_vat': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        logger.info("🔍 [Hutchison] เริ่มดึงยอดเงิน...")
        
        # ทำความสะอาด text: ลบ emoji และ label "💰 ยอดชำระ:" ที่อาจรบกวนการอ่านข้อมูล
        text_clean = text
        # ลบ emoji 💰 และ label "ยอดชำระ:"
        text_clean = re.sub(r'💰\s*ยอดชำระ\s*[:.]?\s*', '', text_clean)
        text_clean = re.sub(r'ยอดชำระ\s*[:.]?\s*', '', text_clean)
        # ลบช่องว่างส่วนเกิน
        text_clean = re.sub(r'\s+', ' ', text_clean)
        
        logger.debug(f"📄 [Hutchison] Text length: {len(text_clean)} characters")
        
        # ยอดก่อนภาษี: ค่าสินค้าและบริการ / Tariff charges 1,000.00 บาท
        pre_tax_patterns = [
            r'ค่าสินค้าและบริการ\s*/?\s*Tariff\s+charges\s+([\d,]+\.?\d*)\s*บาท',  # ค่าสินค้าและบริการ / Tariff charges 1,000.00 บาท
            r'Tariff\s+charges\s+([\d,]+\.?\d*)\s*บาท',  # Tariff charges 1,000.00 บาท
            r'ค่าสินค้าและบริการ\s*[:.]?\s*([\d,]+\.?\d*)\s*บาท',  # ค่าสินค้าและบริการ: 1,000.00 บาท
            r'HUTCHISONPORTS\s+THAILAND\s+ค่าสินค้าและบริการ\s*[:.]?\s*([\d,]+\.?\d*)\s*บาท',  # HUTCHISONPORTS THAILAND ค่าสินค้าและบริการ: 1,000.00 บาท
        ]
        
        for pattern in pre_tax_patterns:
            match = re.search(pattern, text_clean, re.IGNORECASE)
            if match:
                try:
                    amount_str = match.group(1).replace(',', '').replace(' ', '').strip()
                    amount_val = float(amount_str)
                    if amount_val > 0:
                        amounts['amount_before_vat'] = amount_val
                        logger.info(f"✅ [Hutchison] พบยอดก่อนภาษี: {amount_val} (pattern: {pattern[:50]}...)")
                        break
                except ValueError as e:
                    logger.debug(f"⚠️ [Hutchison] ไม่สามารถแปลงเป็นตัวเลข: '{amount_str}', Error: {e}")
                    continue
        
        # ยอดภาษี: ภาษีมูลค่าเพิ่ม / VAT 7.00% 70.00 บาท /Baht
        vat_patterns = [
            r'ภาษีมูลค่าเพิ่ม\s*/?\s*VAT\s+\d+\.?\d*%\s+([\d,]+\.?\d*)\s*บาท',  # ภาษีมูลค่าเพิ่ม / VAT 7.00% 70.00 บาท
            r'VAT\s+\d+\.?\d*%\s+([\d,]+\.?\d*)\s*บาท',  # VAT 7.00% 70.00 บาท
            r'ภาษีมูลค่าเพิ่ม\s*[:.]?\s*([\d,]+\.?\d*)\s*บาท',  # ภาษีมูลค่าเพิ่ม: 70.00 บาท
            r'ภาษีมูลค่าเพิ่ม\s*/?\s*VAT\s+7\.00%\s+([\d,]+\.?\d*)\s*บาท',  # ภาษีมูลค่าเพิ่ม / VAT 7.00% 70.00 บาท
        ]
        
        for pattern in vat_patterns:
            match = re.search(pattern, text_clean, re.IGNORECASE)
            if match:
                try:
                    vat_str = match.group(1).replace(',', '').replace(' ', '').strip()
                    vat_val = float(vat_str)
                    if vat_val > 0:
                        amounts['vat_amount'] = vat_val
                        logger.info(f"✅ [Hutchison] พบยอดภาษี: {vat_val} (pattern: {pattern[:50]}...)")
                        break
                except ValueError as e:
                    logger.debug(f"⚠️ [Hutchison] ไม่สามารถแปลงเป็นตัวเลข: '{vat_str}', Error: {e}")
                    continue
        
        # ยอดรวม: จำนวนเงินรวมทั้งสิ้น / Grand total 1,070.00 บาท /Baht
        total_patterns = [
            r'จำนวนเงินรวมทั้งสิ้น\s*/?\s*Grand\s+total\s+([\d,]+\.?\d*)\s*บาท',  # จำนวนเงินรวมทั้งสิ้น / Grand total 1,070.00 บาท
            r'Grand\s+total\s+([\d,]+\.?\d*)\s*บาท',  # Grand total 1,070.00 บาท
            r'จำนวนเงินรวมทั้งสิ้น\s*[:.]?\s*([\d,]+\.?\d*)\s*บาท',  # จำนวนเงินรวมทั้งสิ้น: 1,070.00 บาท
        ]
        
        for pattern in total_patterns:
            match = re.search(pattern, text_clean, re.IGNORECASE)
            if match:
                try:
                    total_str = match.group(1).replace(',', '').replace(' ', '').strip()
                    total_val = float(total_str)
                    if total_val > 0:
                        amounts['total_amount'] = total_val
                        logger.info(f"✅ [Hutchison] พบยอดรวม: {total_val} (pattern: {pattern[:50]}...)")
                        break
                except ValueError as e:
                    logger.debug(f"⚠️ [Hutchison] ไม่สามารถแปลงเป็นตัวเลข: '{total_str}', Error: {e}")
                    continue
        
        # Fallback: ถ้ายังไม่มี total_amount แต่มี amount_before_vat และ vat_amount ให้คำนวณ
        if amounts['total_amount'] is None and amounts['amount_before_vat'] is not None and amounts['vat_amount'] is not None:
            amounts['total_amount'] = amounts['amount_before_vat'] + amounts['vat_amount']
            logger.info(f"✅ [Hutchison] คำนวณยอดรวม: {amounts['total_amount']} = {amounts['amount_before_vat']} + {amounts['vat_amount']}")
        
        # Fallback: ถ้ายังไม่มี amount_before_vat แต่มี total_amount และ vat_amount ให้คำนวณ
        if amounts['amount_before_vat'] is None and amounts['total_amount'] is not None and amounts['vat_amount'] is not None:
            amounts['amount_before_vat'] = amounts['total_amount'] - amounts['vat_amount']
            logger.info(f"✅ [Hutchison] คำนวณยอดก่อนภาษี: {amounts['amount_before_vat']} = {amounts['total_amount']} - {amounts['vat_amount']}")
        
        # Fallback: ถ้ายังไม่มี vat_amount แต่มี total_amount และ amount_before_vat ให้คำนวณ
        if amounts['vat_amount'] is None and amounts['total_amount'] is not None and amounts['amount_before_vat'] is not None:
            amounts['vat_amount'] = amounts['total_amount'] - amounts['amount_before_vat']
            logger.info(f"✅ [Hutchison] คำนวณยอดภาษี: {amounts['vat_amount']} = {amounts['total_amount']} - {amounts['amount_before_vat']}")
        
        logger.info(f"📊 [Hutchison] ผลลัพธ์: amount_before_vat={amounts['amount_before_vat']}, vat_amount={amounts['vat_amount']}, total_amount={amounts['total_amount']}")
        
        return amounts
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงหมายเหตุ - ใช้ชื่อไฟล์เดิม (ตัด VAT_, WHT_, None_vat_ ออก)"""
        if not filename:
            return None
        
        # ตัด VAT_, WHT_, None_vat_ ออก
        filename_clean = filename
        filename_clean = re.sub(r'(WHT_|VAT_|None_vat_)', '', filename_clean, flags=re.IGNORECASE)
        filename_clean = re.sub(r'\.pdf$', '', filename_clean, flags=re.IGNORECASE)
        
        if filename_clean:
            return filename_clean.strip()
        
        return None
    
    def detect_document_type(self, text: str, amounts: Dict[str, Optional[float]], withholding: Dict[str, Optional[float]]) -> int:
        """ตรวจสอบประเภทเอกสาร (1 = มีภาษีมูลค่าเพิ่ม, 2 = ไม่มีภาษีมูลค่าเพิ่ม)"""
        # ถ้ามียอดภาษี แสดงว่ามีภาษีมูลค่าเพิ่ม
        if amounts.get('vat_amount') and amounts['vat_amount'] > 0:
            return 1  # มีภาษีมูลค่าเพิ่ม
        
        # ถ้ามี WHT แสดงว่ามีภาษีมูลค่าเพิ่ม
        if withholding.get('withholding_tax_percent') and withholding['withholding_tax_percent'] > 0:
            return 1  # มีภาษีมูลค่าเพิ่ม
        
        return 2  # ไม่มีภาษีมูลค่าเพิ่ม
    
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
        # ดึงสาขาจาก text เดิมก่อน (เพราะอาจจะอยู่ในส่วนอื่นๆ ที่ไม่ใช่ original section)
        branch = self.extract_branch(text)
        
        # หาส่วนต้นฉบับของใบกำกับภาษีก่อน
        original_section = self.extract_original_invoice_section(text)
        if original_section:
            # ใช้เฉพาะส่วนต้นฉบับในการดึงข้อมูล
            text = original_section
            logger.info("✅ ใช้เฉพาะส่วนต้นฉบับของใบกำกับภาษีในการดึงข้อมูล")
            # ถ้ายังไม่พบสาขา ลองอ่านจาก original section อีกครั้ง
            if not branch:
                branch = self.extract_branch(text)
        
        # ดึงข้อมูล
        company_name = self.extract_company_name(text)
        tax_id = self.extract_tax_id(text)
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
        address_full = address or ''
        building_number = ''
        other_info = ''
        soi = ''
        road = ''
        subdistrict = ''
        district = ''
        province = ''
        postal_code = ''
        
        if address:
            # ดึงเลขที่: 88/4
            building_match = re.search(r'^(\d+/\d+)', address)
            if building_match:
                building_number = building_match.group(1)
            
            # ดึงตำบล: Tungsukhla
            subdistrict_match = re.search(r'Moo\s+\d+\s+([^,]+)', address, re.IGNORECASE)
            if subdistrict_match:
                subdistrict = subdistrict_match.group(1).strip()
            
            # ดึงอำเภอ: Sriracha
            district_match = re.search(r'Sriracha', address, re.IGNORECASE)
            if district_match:
                district = 'ศรีราชา'
            
            # ดึงจังหวัด: Chonburi
            province_match = re.search(r'Chonburi', address, re.IGNORECASE)
            if province_match:
                province = 'ชลบุรี'
            
            # ดึงรหัสไปรษณีย์: 20230
            postal_match = re.search(r'(\d{5})\s*$', address)
            if postal_match:
                postal_code = postal_match.group(1)
        
        return {
            'success': True,
            'company': 'HUTCHISON',
            'company_name': company_name,
            'tax_id': tax_id,
            'branch': branch,
            'date': date,
            'document_number': document_number,
            'address': address,
            'address_full': address_full,
            'building_number': building_number or '',
            'other_info': other_info or '',
            'soi': soi or '',
            'road': road or '',
            'subdistrict': subdistrict or '',
            'district': district or '',
            'province': province or '',
            'postal_code': postal_code or '',
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
            'document_type': document_type,
        }
