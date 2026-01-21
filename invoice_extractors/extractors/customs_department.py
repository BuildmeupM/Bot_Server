"""
Customs Department Invoice Extractor
====================================
Extractor สำหรับดึงข้อมูลจาก กรมศุลกากร

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class CustomsDepartmentExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก กรมศุลกากร"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "กรมศุลกากร",
        "Customs Department"
    ]
    
    def __init__(self):
        """Initialize Customs Department Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของกรมศุลกากรหรือไม่
        
        เงื่อนไขที่ 1: ไม่มีภาษีมูลค่าเพิ่ม
        - ต้องมี "กรมศุลกากร" และ "ค่าธรรมเนียมการผ่านพิธีการศุลกากร"
        
        เงื่อนไขที่ 2: มีภาษีมูลค่าเพิ่ม
        - ต้องมี "กรมศุลกากร" และ "ภาษีมูลค่าเพิ่ม"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสารกรมศุลกากร
        """
        if not text:
            return False
        
        # ต้องมีชื่อบริษัท
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        if not has_company:
            return False
        
        # เงื่อนไขที่ 1: ไม่มีภาษีมูลค่าเพิ่ม
        condition1 = "ค่าธรรมเนียมการผ่านพิธีการศุลกากร" in text
        
        # เงื่อนไขที่ 2: มีภาษีมูลค่าเพิ่ม
        condition2 = "ภาษีมูลค่าเพิ่ม" in text
        
        # ต้องมีอย่างน้อย 1 เงื่อนไข
        return condition1 or condition2
    
    def extract_company_name(self, text: str) -> str:
        """ดึงชื่อบริษัท"""
        return "กรมศุลกากร"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # กรมศุลกากร: ใช้เลขประจำตัวผู้เสียภาษีเป็น 0000000000000
        # ลองหาดูก่อนว่ามี Tax ID ในเอกสารหรือไม่
        pattern1 = r'TaxID\s*[:.]?\s*(\d{13})'
        match = re.search(pattern1, text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        pattern2 = r'Tax\s+ID\s+No[.:]?\s*(\d{13})'
        match = re.search(pattern2, text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # ถ้าไม่พบ ให้ใช้ค่า default สำหรับกรมศุลกากร
        return "0000000000000"
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่และแปลงเป็น dd/mm/yyyy"""
        # Pattern: 03/11/2025 หรือ Date: 03/11/2025
        pattern = r'(?:Date\s*[:.]?\s*)?(\d{1,2})[/-](\d{1,2})[/-](\d{4})'
        match = re.search(pattern, text)
        
        if match:
            day = match.group(1).zfill(2)
            month = match.group(2).zfill(2)
            year = match.group(3)
            return f"{day}/{month}/{year}"
        
        return None
    
    def extract_address(self, text: str) -> Optional[str]:
        """
        ดึงข้อมูลที่อยู่บริษัท
        
        ที่อยู่: เลขที่ 1 ถ.สุนทรโกษา เขตคลองเตย แขวงคลองเตย กทม. 10110
        
        Returns:
            ที่อยู่รวม (string) - ระบบจะแยกเป็นส่วนๆ อัตโนมัติใน parse_address()
        """
        return "เลขที่ 1 ถ.สุนทรโกษา เขตคลองเตย แขวงคลองเตย กทม. 10110"
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """
        ดึงข้อมูลบัญชี (Account Name / Account Code)
        
        สำหรับกรณีมีภาษีมูลค่าเพิ่ม บรรทัดที่ 1 จะเป็น "บัญชีพัก"
        """
        # ตรวจสอบว่ามีภาษีมูลค่าเพิ่มหรือไม่ (ใช้ฟังก์ชัน has_vat() ที่ตรวจสอบจากรายการจริง)
        has_vat = self.has_vat(text)
        
        if has_vat:
            return {
                'account_name': 'บัญชีพัก',
                'account_code': None
            }
        
        return {
            'account_name': None,
            'account_code': None
        }
    
    def extract_withholding_tax(self, text: str) -> Dict[str, Optional[float]]:
        """ดึงข้อมูลหัก ณ ที่จ่าย"""
        return {
            'withholding_tax_percent': 0.0,
            'withholding_tax_amount': 0.0
        }
    
    def has_vat(self, text: str) -> bool:
        """
        ตรวจสอบว่าเอกสารมีภาษีมูลค่าเพิ่มหรือไม่
        
        เงื่อนไขที่ 1 (ไม่มีภาษี): 
        - ต้องมี "ค่าธรรมเนียมการผ่านพิธีการศุลกากร"
        - และไม่มี "ค่าภาษีมูลค่าเพิ่ม" หรือ "ค่าอากรขาเข้า" ในส่วนรายการ
        
        เงื่อนไขที่ 2 (มีภาษี):
        - ต้องมี "ค่าภาษีมูลค่าเพิ่ม" หรือ "ค่าอากรขาเข้า" ในส่วนรายการ
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้ามีภาษีมูลค่าเพิ่ม (มี "ค่าภาษีมูลค่าเพิ่ม" หรือ "ค่าอากรขาเข้า" ในส่วนรายการ)
            False ถ้าไม่มีภาษีมูลค่าเพิ่ม (มีแค่ "ค่าธรรมเนียมการผ่านพิธีการศุลกากร")
        """
        # ตรวจสอบว่ามี "ค่าธรรมเนียมการผ่านพิธีการศุลกากร" หรือไม่
        has_fee = "ค่าธรรมเนียมการผ่านพิธีการศุลกากร" in text
        
        # ตรวจสอบว่ามี "ค่าภาษีมูลค่าเพิ่ม" หรือ "ค่าอากรขาเข้า" ในส่วนรายการหรือไม่
        # หาตำแหน่งของ "ได้รับเงินตามรายการข้างล่างนี้ไว้แล้ว" เพื่อจำกัดขอบเขต
        has_vat_in_items = False
        
        # หาตำแหน่งของ "ได้รับเงินตามรายการข้างล่างนี้ไว้แล้ว"
        items_start = text.find("ได้รับเงินตามรายการข้างล่างนี้ไว้แล้ว")
        if items_start != -1:
            # หาตำแหน่งของ "รวมเงินทั้งสิ้น" เพื่อจำกัดขอบเขตของรายการ
            total_start = text.find("รวมเงินทั้งสิ้น", items_start)
            if total_start != -1:
                # ตรวจสอบในส่วนรายการ (ระหว่าง "ได้รับเงิน..." ถึง "รวมเงินทั้งสิ้น")
                items_section = text[items_start:total_start]
                # ตรวจสอบว่ามี "ค่าภาษีมูลค่าเพิ่ม" หรือ "ค่าอากรขาเข้า" ในส่วนรายการ
                has_vat_in_items = ("ค่าภาษีมูลค่าเพิ่ม" in items_section) or ("ค่าอากรขาเข้า" in items_section)
            else:
                # ถ้าไม่พบ "รวมเงินทั้งสิ้น" ให้ตรวจสอบในส่วนหลัง "ได้รับเงิน..."
                items_section = text[items_start:items_start+500]  # ตรวจสอบ 500 ตัวอักษรแรก
                has_vat_in_items = ("ค่าภาษีมูลค่าเพิ่ม" in items_section) or ("ค่าอากรขาเข้า" in items_section)
        else:
            # ถ้าไม่พบ "ได้รับเงิน..." ให้ตรวจสอบทั้ง text (fallback)
            has_vat_in_items = ("ค่าภาษีมูลค่าเพิ่ม" in text) or ("ค่าอากรขาเข้า" in text)
        
        # ถ้ามี "ค่าธรรมเนียมการผ่านพิธีการศุลกากร" และไม่มี "ค่าภาษีมูลค่าเพิ่ม" หรือ "ค่าอากรขาเข้า" ในส่วนรายการ = ไม่มีภาษี
        if has_fee and not has_vat_in_items:
            return False
        
        # ถ้ามี "ค่าภาษีมูลค่าเพิ่ม" หรือ "ค่าอากรขาเข้า" ในส่วนรายการ = มีภาษี
        return has_vat_in_items
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงยอดเงินทั้งหมด
        
        เงื่อนไขที่ 1: ไม่มีภาษีมูลค่าเพิ่ม
        - ยอดก่อนภาษี: ดึงจาก "รวมเงินทั้งสิ้น (บาท) | 200.00"
        - ยอดภาษี: 0
        - ยอดรวม: เท่ากับยอดก่อนภาษี
        
        เงื่อนไขที่ 2: มีภาษีมูลค่าเพิ่ม
        - บรรทัดที่ 1:
          - ยอดก่อนภาษี: คำนวณจาก ยอดภาษี / 0.07
          - ยอดภาษี: ดึงจาก "ค่าภาษีมูลค่าเพิ่ม | | 13,961.00"
          - ยอดรวม: ยอดก่อนภาษี + ยอดภาษี
        - บรรทัดที่ 2:
          - ยอดก่อนภาษี: ดึงจาก "ค่าอากรขาเข้า | 18,131.00 |"
          - ยอดภาษี: 0
          - ยอดรวม: เท่ากับยอดก่อนภาษี
        
        Returns:
            {
                'amount_before_vat': float,  # ยอดก่อนภาษี (บรรทัดที่ 1 หรือยอดรวม)
                'amount_before_vat_2': float, # ยอดก่อนภาษี (บรรทัดที่ 2 - ถ้ามี)
                'vat_amount': float,          # ยอดภาษี
                'total_amount': float         # ยอดรวม
            }
        """
        result = {
            'amount_before_vat': None,
            'amount_before_vat_2': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        has_vat = self.has_vat(text)
        
        # Log สำหรับ debug
        logger.debug(f"🔍 กรมศุลกากร extract_amounts - has_vat: {has_vat}")
        logger.debug(f"🔍 กรมศุลกากร extract_amounts - Text length: {len(text)}")
        if 'รวมเงินทั้งสิ้น' in text:
            total_pos = text.find('รวมเงินทั้งสิ้น')
            logger.debug(f"🔍 กรมศุลกากร - พบ 'รวมเงินทั้งสิ้น' ที่ตำแหน่ง {total_pos}")
            logger.debug(f"🔍 กรมศุลกากร - ข้อความรอบๆ: '{text[max(0, total_pos-50):total_pos+100]}'")
        
        if not has_vat:
            # เงื่อนไขที่ 1: ไม่มีภาษีมูลค่าเพิ่ม
            # ไม่ต้องคำนวณอะไร เพียงแค่อ่านยอดเงินจาก "รวมเงินทั้งสิ้น (บาท) | 200.00"
            # รองรับหลายรูปแบบ: มี/ไม่มี space, มี/ไม่มี pipe, มี/ไม่มีวงเล็บ, มี/ไม่มี newline
            logger.info(f"🔍 กรมศุลกากร (ไม่มีภาษี) - เริ่มอ่านข้อมูล...")
            
            # ทำความสะอาด text สำหรับการค้นหา (รวม newline เป็น space)
            text_clean = re.sub(r'\s+', ' ', text)
            
            # Pattern: รวมเงินทั้งสิ้น (บาท) | 200.00
            # รองรับหลายรูปแบบ
            patterns = [
                # รูปแบบที่มี pipe และ space
                r'รวมเงินทั้งสิ้น\s*\(บาท\)\s*\|\s*([\d,]+\.?\d{2})',  # รวมเงินทั้งสิ้น (บาท) | 200.00
                r'รวมเงินทั้งสิ้น\s*\(บาท\)\s*\|\s*([\d,]+\.?\d*)',  # รวมเงินทั้งสิ้น (บาท) | 200
                # รูปแบบที่มี pipe แต่ไม่มี space
                r'รวมเงินทั้งสิ้น\s*\(บาท\)\s*\|\s*([\d,]+\.?\d{2})',  # รวมเงินทั้งสิ้น (บาท)|200.00
                # รูปแบบที่ไม่มี pipe
                r'รวมเงินทั้งสิ้น\s*\(บาท\)\s+([\d,]+\.?\d{2})',  # รวมเงินทั้งสิ้น (บาท) 200.00
                r'รวมเงินทั้งสิ้น\s*\(บาท\)\s*[:.]?\s*([\d,]+\.?\d{2})',  # รวมเงินทั้งสิ้น (บาท): 200.00
                # รูปแบบที่ไม่มีวงเล็บ
                r'รวมเงินทั้งสิ้น\s*\|\s*([\d,]+\.?\d{2})',  # รวมเงินทั้งสิ้น | 200.00
                r'รวมเงินทั้งสิ้น\s+([\d,]+\.?\d{2})',  # รวมเงินทั้งสิ้น 200.00
                # รูปแบบยืดหยุ่น (fallback)
                r'รวมเงินทั้งสิ้น[^0-9]*([\d,]+\.?\d{2})',  # รวมเงินทั้งสิ้น...200.00
            ]
            
            # ลองหาใน text เดิมก่อน
            logger.debug(f"🔍 กรมศุลกากร (ไม่มีภาษี) - ลองหาใน text เดิม...")
            for idx, pattern in enumerate(patterns):
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    amount_str = match.group(1).replace(',', '').replace(' ', '')
                    logger.debug(f"🔍 Pattern {idx+1} matched (text เดิม): '{pattern}' -> matched: '{match.group(0)}' -> amount_str: '{amount_str}'")
                    try:
                        amount = float(amount_str)
                        if amount > 0:
                            result['amount_before_vat'] = amount
                            result['vat_amount'] = 0.0
                            result['total_amount'] = amount
                            logger.info(f"✅ กรมศุลกากร (ไม่มีภาษี): ยอดก่อนภาษี = {amount} (pattern {idx+1} ใน text เดิม)")
                            break
                    except ValueError as e:
                        logger.warning(f"⚠️ ไม่สามารถแปลงเป็นตัวเลข: '{amount_str}', Error: {e}")
                        continue
                else:
                    logger.debug(f"🔍 Pattern {idx+1} ไม่ match (text เดิม): '{pattern}'")
            
            # ถ้ายังไม่พบ ให้ลองหาใน text_clean
            if not result['amount_before_vat']:
                logger.debug(f"🔍 กรมศุลกากร (ไม่มีภาษี) - ลองหาใน text_clean...")
                for idx, pattern in enumerate(patterns):
                    match = re.search(pattern, text_clean, re.IGNORECASE)
                    if match:
                        amount_str = match.group(1).replace(',', '').replace(' ', '')
                        logger.debug(f"🔍 Pattern {idx+1} matched (text_clean): '{pattern}' -> matched: '{match.group(0)}' -> amount_str: '{amount_str}'")
                        try:
                            amount = float(amount_str)
                            if amount > 0:
                                result['amount_before_vat'] = amount
                                result['vat_amount'] = 0.0
                                result['total_amount'] = amount
                                logger.info(f"✅ กรมศุลกากร (ไม่มีภาษี): ยอดก่อนภาษี = {amount} (pattern {idx+1} ใน text_clean)")
                                break
                        except ValueError as e:
                            logger.warning(f"⚠️ ไม่สามารถแปลงเป็นตัวเลข: '{amount_str}', Error: {e}")
                            continue
            
            # ถ้ายังไม่พบ ให้ลองหาด้วยวิธีอื่น: หาคำว่า "รวมเงินทั้งสิ้น" แล้วหาตัวเลขที่อยู่ใกล้ๆ
            if not result['amount_before_vat']:
                logger.warning(f"⚠️ กรมศุลกากร (ไม่มีภาษี) - ไม่พบยอดเงินจาก patterns, ลองหาด้วยวิธีอื่น...")
                # หาคำว่า "รวมเงินทั้งสิ้น" ใน text เดิม
                total_pos = text.find('รวมเงินทั้งสิ้น')
                if total_pos != -1:
                    # หาตัวเลขที่อยู่หลัง "รวมเงินทั้งสิ้น" (ภายใน 150 ตัวอักษร)
                    search_text = text[total_pos:total_pos+150]
                    logger.info(f"🔍 ข้อความรอบๆ 'รวมเงินทั้งสิ้น' (ตำแหน่ง {total_pos}): '{search_text}'")
                    # หาตัวเลขที่มีรูปแบบ 200.00 หรือ 200,00 หรือ 200
                    numbers = re.findall(r'([\d,]+\.?\d{2})', search_text)
                    if not numbers:
                        # ลองหาแบบไม่มี .00
                        numbers = re.findall(r'([\d,]+\.?\d*)', search_text)
                    if numbers:
                        logger.info(f"🔍 พบตัวเลข {len(numbers)} ตัว: {numbers}")
                        for num_str in numbers:
                            try:
                                amount = float(num_str.replace(',', '').replace(' ', ''))
                                if amount > 0:
                                    result['amount_before_vat'] = amount
                                    result['vat_amount'] = 0.0
                                    result['total_amount'] = amount
                                    logger.info(f"✅ กรมศุลกากร (ไม่มีภาษี): ยอดก่อนภาษี = {amount} (หาใกล้ๆ 'รวมเงินทั้งสิ้น')")
                                    break
                            except ValueError as e:
                                logger.debug(f"🔍 ข้ามตัวเลข '{num_str}': {e}")
                                continue
        else:
            # เงื่อนไขที่ 2: มีภาษีมูลค่าเพิ่ม
            logger.debug(f"🔍 กรมศุลกากร (มีภาษี) - ลองหาข้อมูล...")
            
            # บรรทัดที่ 1: ดึงยอดภาษีมูลค่าเพิ่ม
            # Pattern: ค่าภาษีมูลค่าเพิ่ม | | 13,961.00
            # รองรับหลายรูปแบบ: มี/ไม่มี space, มี/ไม่มี pipe
            vat_patterns = [
                r'ค่าภาษีมูลค่าเพิ่ม\s*\|\s*\|\s*([\d,]+\.?\d{2})',  # ค่าภาษีมูลค่าเพิ่ม | | 13,961.00
                r'ค่าภาษีมูลค่าเพิ่ม\s*\|\s+([\d,]+\.?\d{2})',  # ค่าภาษีมูลค่าเพิ่ม | 13,961.00 (space หลัง |)
                r'ค่าภาษีมูลค่าเพิ่ม\s*\|\s*([\d,]+\.?\d{2})',  # ค่าภาษีมูลค่าเพิ่ม | 13,961.00
                r'ค่าภาษีมูลค่าเพิ่ม\s+([\d,]+\.?\d{2})',  # ค่าภาษีมูลค่าเพิ่ม 13,961.00
                r'ค่าภาษีมูลค่าเพิ่ม[^0-9]*([\d,]+\.?\d{2})',  # ค่าภาษีมูลค่าเพิ่ม...13,961.00 (flexible)
                r'ภาษีมูลค่าเพิ่ม\s*\|\s*\|\s*([\d,]+\.?\d{2})',  # ภาษีมูลค่าเพิ่ม | | 13,961.00
                r'ภาษีมูลค่าเพิ่ม\s*\|\s+([\d,]+\.?\d{2})',  # ภาษีมูลค่าเพิ่ม | 13,961.00
                r'ภาษีมูลค่าเพิ่ม\s*\|\s*([\d,]+\.?\d{2})',  # ภาษีมูลค่าเพิ่ม | 13,961.00
            ]
            
            vat_amount = None
            logger.debug(f"🔍 กรมศุลกากร (มีภาษี) - ลองหา 'ค่าภาษีมูลค่าเพิ่ม'...")
            if 'ค่าภาษีมูลค่าเพิ่ม' in text:
                vat_pos = text.find('ค่าภาษีมูลค่าเพิ่ม')
                logger.debug(f"🔍 พบ 'ค่าภาษีมูลค่าเพิ่ม' ที่ตำแหน่ง {vat_pos}")
                logger.debug(f"🔍 ข้อความรอบๆ: '{text[max(0, vat_pos-30):vat_pos+100]}'")
            
            for idx, pattern in enumerate(vat_patterns):
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    vat_str = match.group(1).replace(',', '').replace(' ', '')
                    logger.debug(f"🔍 VAT Pattern {idx+1} matched: '{pattern}' -> matched: '{match.group(0)}' -> vat_str: '{vat_str}'")
                    try:
                        vat_amount = float(vat_str)
                        if vat_amount > 0:
                            result['vat_amount'] = vat_amount
                            logger.info(f"✅ กรมศุลกากร (มีภาษี): ยอดภาษี = {vat_amount} (pattern {idx+1})")
                            break
                    except ValueError as e:
                        logger.warning(f"⚠️ ไม่สามารถแปลงเป็นตัวเลข: '{vat_str}', Error: {e}")
                        continue
                else:
                    logger.debug(f"🔍 VAT Pattern {idx+1} ไม่ match: '{pattern}'")
            
            # ถ้ายังไม่พบ ให้ลองหาด้วยวิธีอื่น
            if not vat_amount:
                logger.warning(f"⚠️ กรมศุลกากร (มีภาษี) - ไม่พบยอดภาษีจาก patterns, ลองหาด้วยวิธีอื่น...")
                vat_pos = text.find('ค่าภาษีมูลค่าเพิ่ม')
                if vat_pos != -1:
                    # หาตัวเลขที่อยู่หลัง "ค่าภาษีมูลค่าเพิ่ม" (ภายใน 100 ตัวอักษร)
                    search_text = text[vat_pos:vat_pos+100]
                    logger.debug(f"🔍 ข้อความรอบๆ 'ค่าภาษีมูลค่าเพิ่ม': '{search_text}'")
                    # หาตัวเลขที่มีรูปแบบ 13,961.00
                    numbers = re.findall(r'([\d,]+\.?\d{2})', search_text)
                    if numbers:
                        # เลือกตัวเลขแรกที่มากกว่า 0
                        for num_str in numbers:
                            try:
                                amount = float(num_str.replace(',', '').replace(' ', ''))
                                if amount > 0:
                                    vat_amount = amount
                                    result['vat_amount'] = vat_amount
                                    logger.info(f"✅ กรมศุลกากร (มีภาษี): ยอดภาษี = {vat_amount} (หาใกล้ๆ)")
                                    break
                            except ValueError:
                                continue
            
            # คำนวณยอดก่อนภาษี (บรรทัดที่ 1) จากยอดภาษี / 0.07
            if vat_amount and vat_amount > 0:
                result['amount_before_vat'] = vat_amount / 0.07
                logger.info(f"✅ กรมศุลกากร (มีภาษี): ยอดก่อนภาษี (บรรทัด 1) = {result['amount_before_vat']:.2f} (คำนวณจาก {vat_amount} / 0.07)")
            
            # บรรทัดที่ 2: ดึงค่าอากรขาเข้า
            # Pattern: ค่าอากรขาเข้า | 18,131.00 |
            # รองรับหลายรูปแบบ: มี/ไม่มี space, มี/ไม่มี pipe
            import_patterns = [
                r'ค่าอากรขาเข้า\s*\|\s*([\d,]+\.?\d{2})\s*\|',  # ค่าอากรขาเข้า | 18,131.00 |
                r'ค่าอากรขาเข้า\s*\|\s+([\d,]+\.?\d{2})\s*\|',  # ค่าอากรขาเข้า | 18,131.00 | (space หลัง |)
                r'ค่าอากรขาเข้า\s*\|\s*([\d,]+\.?\d{2})',  # ค่าอากรขาเข้า | 18,131.00
                r'ค่าอากรขาเข้า\s+([\d,]+\.?\d{2})',  # ค่าอากรขาเข้า 18,131.00
                r'ค่าอากรขาเข้า[^0-9]*([\d,]+\.?\d{2})',  # ค่าอากรขาเข้า...18,131.00 (flexible)
                r'อากรขาเข้า\s*\|\s*([\d,]+\.?\d{2})\s*\|',  # อากรขาเข้า | 18,131.00 |
                r'อากรขาเข้า\s*\|\s*([\d,]+\.?\d{2})',  # อากรขาเข้า | 18,131.00
            ]
            
            logger.debug(f"🔍 กรมศุลกากร (มีภาษี) - ลองหา 'ค่าอากรขาเข้า'...")
            if 'ค่าอากรขาเข้า' in text:
                import_pos = text.find('ค่าอากรขาเข้า')
                logger.debug(f"🔍 พบ 'ค่าอากรขาเข้า' ที่ตำแหน่ง {import_pos}")
                logger.debug(f"🔍 ข้อความรอบๆ: '{text[max(0, import_pos-30):import_pos+100]}'")
            
            for idx, pattern in enumerate(import_patterns):
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    amount_str = match.group(1).replace(',', '').replace(' ', '')
                    logger.debug(f"🔍 Import Pattern {idx+1} matched: '{pattern}' -> matched: '{match.group(0)}' -> amount_str: '{amount_str}'")
                    try:
                        amount = float(amount_str)
                        if amount > 0:
                            result['amount_before_vat_2'] = amount
                            logger.info(f"✅ กรมศุลกากร (มีภาษี): ยอดก่อนภาษี (บรรทัด 2) = {amount} (pattern {idx+1})")
                            break
                    except ValueError as e:
                        logger.warning(f"⚠️ ไม่สามารถแปลงเป็นตัวเลข: '{amount_str}', Error: {e}")
                        continue
                else:
                    logger.debug(f"🔍 Import Pattern {idx+1} ไม่ match: '{pattern}'")
            
            # ถ้ายังไม่พบ ให้ลองหาด้วยวิธีอื่น
            if not result['amount_before_vat_2']:
                logger.warning(f"⚠️ กรมศุลกากร (มีภาษี) - ไม่พบค่าอากรขาเข้าจาก patterns, ลองหาด้วยวิธีอื่น...")
                import_pos = text.find('ค่าอากรขาเข้า')
                if import_pos != -1:
                    # หาตัวเลขที่อยู่หลัง "ค่าอากรขาเข้า" (ภายใน 100 ตัวอักษร)
                    search_text = text[import_pos:import_pos+100]
                    logger.debug(f"🔍 ข้อความรอบๆ 'ค่าอากรขาเข้า': '{search_text}'")
                    # หาตัวเลขที่มีรูปแบบ 18,131.00
                    numbers = re.findall(r'([\d,]+\.?\d{2})', search_text)
                    if numbers:
                        # เลือกตัวเลขแรกที่มากกว่า 0
                        for num_str in numbers:
                            try:
                                amount = float(num_str.replace(',', '').replace(' ', ''))
                                if amount > 0:
                                    result['amount_before_vat_2'] = amount
                                    logger.info(f"✅ กรมศุลกากร (มีภาษี): ยอดก่อนภาษี (บรรทัด 2) = {amount} (หาใกล้ๆ)")
                                    break
                            except ValueError:
                                continue
            
            # คำนวณยอดรวม
            line1_before_vat = result.get('amount_before_vat') or 0
            line1_vat = result.get('vat_amount') or 0
            line1_total = line1_before_vat + line1_vat
            
            line2_before_vat = result.get('amount_before_vat_2') or 0
            line2_total = line2_before_vat
            
            result['total_amount'] = line1_total + line2_total
            logger.info(f"✅ กรมศุลกากร (มีภาษี): ยอดรวม = {result['total_amount']:.2f} (บรรทัด 1: {line1_total:.2f} + บรรทัด 2: {line2_total:.2f})")
        
        return result
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """
        ดึงหมายเหตุ (ชื่อไฟล์เก่า)
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF (optional)
        
        Returns:
            หมายเหตุ (ชื่อไฟล์เก่า)
        """
        if filename:
            # ตัด VAT_, WHT_, None_vat_ และ .pdf
            filename_clean = re.sub(r'(VAT_|None_vat_|WHT_)', '', filename, flags=re.IGNORECASE)
            filename_clean = re.sub(r'\.pdf$', '', filename_clean, flags=re.IGNORECASE)
            return filename_clean.strip()
        
        return None
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """
        ดึงเลขที่ชำระอากร (สำหรับกรณีมีภาษีมูลค่าเพิ่ม)
        
        รูปแบบ: เลขที่ชำระอากร/วันเดือนปี 2801-090986/04-11-68
        ข้อมูลที่ต้องการ: 2801-090986
        """
        # Pattern: เลขที่ชำระอากร/วันเดือนปี 2801-090986/04-11-68
        patterns = [
            r'เลขที่ชำระอากร\s*/?\s*วันเดือนปี\s+(\d{4}-\d{6})',  # เลขที่ชำระอากร/วันเดือนปี 2801-090986/04-11-68
            r'เลขที่ชำระอากร\s*[:.]?\s*[^0-9]*(\d{4}-\d{6})',  # เลขที่ชำระอากร: ... 2801-090986
            r'เลขที่ชำระอากร[^0-9]*(\d{4}-\d{6})',  # เลขที่ชำระอากร... 2801-090986
            r'(\d{4}-\d{6})\s*/?\s*\d{2}-\d{2}-\d{2}',  # 2801-090986/04-11-68 (fallback)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                doc_num = match.group(1).strip()
                # ตรวจสอบรูปแบบที่ถูกต้อง (ต้องมีรูปแบบ XXXX-XXXXXX)
                if re.match(r'^\d{4}-\d{6}$', doc_num):
                    return doc_num
        
        return None
    
    def detect_document_type(self, text: str, amounts: Dict[str, Optional[float]], withholding: Dict[str, Optional[float]]) -> int:
        """
        ตรวจจับประเภทเอกสาร
        
        Returns:
            1 = เอกสารมีภาษีมูลค่าเพิ่ม (VAT)
            2 = เอกสารไม่มีภาษีมูลค่าเพิ่ม (NoneVat)
        """
        if self.has_vat(text):
            return 1  # มีภาษีมูลค่าเพิ่ม
        else:
            return 2  # ไม่มีภาษีมูลค่าเพิ่ม
    
    def extract_all_data(self, text: str, filename: str, filepath: str = None) -> Dict[str, Any]:
        """
        ดึงข้อมูลทั้งหมดจากเอกสารกรมศุลกากร
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
            filepath: Path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # ตรวจสอบว่าเป็นเอกสารกรมศุลกากรหรือไม่
        is_company = self.is_company_document(text)
        
        if not is_company:
            return {
                'success': False,
                'company': None,
                'error': 'ไม่ใช่เอกสารกรมศุลกากร'
            }
        
        # หาส่วนต้นฉบับของใบกำกับภาษีก่อน
        original_section = self.extract_original_invoice_section(text)
        if original_section:
            # ใช้เฉพาะส่วนต้นฉบับในการดึงข้อมูล
            text = original_section
            logger.info("✅ ใช้เฉพาะส่วนต้นฉบับของใบกำกับภาษีในการดึงข้อมูล")
        
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
        
        # สร้างชื่อไฟล์ใหม่ (ตัด VAT_, WHT_, None_vat_)
        new_filename = filename
        if new_filename:
            new_filename = re.sub(r'(VAT_|None_vat_|WHT_)', '', new_filename, flags=re.IGNORECASE)
        
        has_vat = self.has_vat(text)
        
        # สำหรับกรณีมีภาษีมูลค่าเพิ่ม: คำนวณยอดรวม
        if has_vat:
            line1_before_vat = amounts.get('amount_before_vat') or 0
            line1_vat = amounts.get('vat_amount') or 0
            line2_before_vat = amounts.get('amount_before_vat_2') or 0
            
            # ยอดรวมทั้งหมด
            total_before_vat = line1_before_vat + line2_before_vat
            total_vat = line1_vat
            total_amount = amounts.get('total_amount') or (total_before_vat + total_vat)
            
            return {
                'success': True,
                'company': 'CUSTOMS_DEPARTMENT',
                'company_name': company_name,
                'tax_id': tax_id,
                'date': date,
                'document_number': document_number,  # เลขที่ชำระอากร
                'address': address,
                'account_name': account_info['account_name'],
                'account_code': account_info['account_code'],
                'withholding_tax_percent': withholding['withholding_tax_percent'],
                'withholding_tax_amount': withholding['withholding_tax_amount'],
                'amount_before_vat': total_before_vat,  # รวมทั้ง 2 บรรทัด
                'vat_amount': total_vat,
                'total_amount': total_amount,
                'remark': remark,
                'new_filename': new_filename,
                'old_filename': filename,
                'filepath': filepath,
                'document_type': document_type,
                # ข้อมูลเพิ่มเติมสำหรับกรณีมีภาษี (สำหรับสร้าง 2 แถว)
                'amount_before_vat_line1': line1_before_vat,  # บรรทัดที่ 1
                'amount_before_vat_line2': line2_before_vat,  # บรรทัดที่ 2
                'vat_amount_line1': line1_vat,  # ภาษีบรรทัดที่ 1
                'vat_amount_line2': 0.0,  # ภาษีบรรทัดที่ 2 (ไม่มี)
            }
        else:
            # กรณีไม่มีภาษีมูลค่าเพิ่ม
            return {
                'success': True,
                'company': 'CUSTOMS_DEPARTMENT',
                'company_name': company_name,
                'tax_id': tax_id,
                'date': date,
                'document_number': document_number,  # เลขที่ชำระอากร
                'address': address,
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
                'document_type': document_type,  # 2 = ไม่มีภาษีมูลค่าเพิ่ม
            }
