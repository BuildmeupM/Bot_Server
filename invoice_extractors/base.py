"""
Base Invoice Extractor
======================
Base class สำหรับ Extractor ทั้งหมด

Author: BotV3
Version: 3.0.0
"""

from typing import Dict, Any, Optional
import logging
import re

logger = logging.getLogger(__name__)


class BaseInvoiceExtractor:
    """Base class สำหรับ Extractor ทั้งหมด"""
    
    def __init__(self):
        """Initialize Base Extractor"""
        self.company_identifiers = []
    
    def is_company_document(self, text: str) -> bool:
        """ตรวจสอบว่าเป็นเอกสารของบริษัทนี้หรือไม่"""
        raise NotImplementedError
    
    def extract_all_data(self, text: str, filename: str, filepath: str = None) -> Dict[str, Any]:
        """ดึงข้อมูลทั้งหมดจากเอกสาร"""
        raise NotImplementedError
    
    def extract_due_date(self, text: str) -> Optional[str]:
        """
        ดึงวันที่ครบกำหนดชำระ (สามารถ override ได้)
        
        Default implementation ใช้ utility function
        """
        from .utils import extract_due_date
        return extract_due_date(text)
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """
        ดึงข้อมูลบัญชี (Account Name / Account Code) (สามารถ override ได้)
        
        Default implementation ใช้ utility function
        """
        from .utils import extract_account_info
        return extract_account_info(text)
    
    def extract_branch(self, text: str) -> Optional[str]:
        """
        ดึงสาขา (สามารถ override ได้)
        
        Default implementation ใช้ utility function
        """
        from .utils import extract_branch
        return extract_branch(text)
    
    def extract_withholding_tax(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงข้อมูลหัก ณ ที่จ่าย (สามารถ override ได้)
        
        Default implementation ใช้ utility function
        """
        from .utils import extract_withholding_tax_enhanced
        return extract_withholding_tax_enhanced(text)
    
    def extract_original_invoice_section(self, text: str) -> Optional[str]:
        """
        หาส่วนต้นฉบับของใบกำกับภาษีจากข้อความ
        
        หาข้อความ:
        - ใบเสร็จรับเงิน/ใบกำกับภาษี
        - ใบแจ้งหนี้/ใบกำกับภาษี
        - ใบกำกับภาษี
        - Receipt/tax invoice
        - Tax Invoice
        - Invoice
        
        และดึงเฉพาะส่วนต้นฉบับ (original) เท่านั้น
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            ส่วนต้นฉบับของใบกำกับภาษี หรือ None ถ้าไม่พบ
        """
        if not text:
            return None
        
        # รูปแบบที่ต้องการหา (ทั้งภาษาไทยและอังกฤษ)
        invoice_patterns = [
            r'ใบเสร็จรับเงิน\s*/?\s*ใบกำกับภาษี',
            r'ใบแจ้งหนี้\s*/?\s*ใบกำกับภาษี',
            r'ใบกำกับภาษี',
            r'Receipt\s*/?\s*Tax\s+Invoice',
            r'Receipt\s*/?\s*tax\s+invoice',
            r'Tax\s+Invoice',
            r'tax\s+invoice',
            r'Invoice',
        ]
        
        # หาตำแหน่งของคำว่า "ต้นฉบับ" หรือ "Original" หรือ "ORIGINAL"
        original_keywords = [
            r'ต้นฉบับ',
            r'Original',
            r'ORIGINAL',
            r'COPY',
            r'สำเนา',
        ]
        
        # หาตำแหน่งของคำว่า "สำเนา" หรือ "COPY" (ถ้ามี)
        copy_keywords = [
            r'สำเนา',
            r'COPY',
            r'Copy',
        ]
        
        best_match = None
        best_start = len(text)
        best_end = len(text)
        
        # หาทุกตำแหน่งที่มีคำว่าใบกำกับภาษี
        for pattern in invoice_patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            for match in matches:
                start_pos = match.start()
                
                # หาว่ามีคำว่า "ต้นฉบับ" หรือ "Original" อยู่ใกล้ๆ หรือไม่
                # ตรวจสอบ 200 ตัวอักษรก่อนและหลัง
                context_start = max(0, start_pos - 200)
                context_end = min(len(text), start_pos + 500)
                context = text[context_start:context_end]
                
                # ตรวจสอบว่ามีคำว่า "สำเนา" หรือ "COPY" ในบริบทนี้หรือไม่
                has_copy = False
                for copy_keyword in copy_keywords:
                    if re.search(copy_keyword, context, re.IGNORECASE):
                        has_copy = True
                        break
                
                # ถ้ามี "สำเนา" หรือ "COPY" ให้ข้าม (ไม่ใช่ต้นฉบับ)
                if has_copy:
                    continue
                
                # หาว่ามีคำว่า "ต้นฉบับ" หรือ "Original" หรือไม่
                has_original = False
                for original_keyword in original_keywords:
                    if re.search(original_keyword, context, re.IGNORECASE):
                        has_original = True
                        break
                
                # ถ้าไม่มีคำว่า "ต้นฉบับ" หรือ "Original" แต่ก็ไม่มี "สำเนา" หรือ "COPY"
                # ให้ถือว่าเป็นต้นฉบับ (เพราะเอกสารส่วนใหญ่จะเป็นต้นฉบับ)
                # แต่ถ้ามีคำว่า "ต้นฉบับ" หรือ "Original" ให้ความสำคัญมากกว่า
                
                # หาจุดสิ้นสุดของส่วนนี้ (หาจนถึงส่วนที่อาจจะเป็นสำเนา หรือส่วนท้ายของเอกสาร)
                # หา "สำเนา" หรือ "COPY" หลังจากตำแหน่งนี้
                end_pos = len(text)
                search_start = start_pos + 100
                for copy_keyword in copy_keywords:
                    copy_match = re.search(copy_keyword, text[search_start:], re.IGNORECASE)
                    if copy_match:
                        end_pos = min(end_pos, search_start + copy_match.start())
                        break
                
                # ถ้าไม่มี "สำเนา" ให้หาจนถึงส่วนท้ายของเอกสาร หรือจนถึงส่วนที่อาจจะเป็นส่วนอื่น
                # หา pattern ที่อาจจะเป็นส่วนอื่น เช่น "เอกสารนี้ได้จัดทำ" หรือ "This document"
                other_section_patterns = [
                    r'เอกสารนี้ได้จัดทำ',
                    r'This\s+document',
                    r'กรุณาติดต่อ',
                    r'Please\s+contact',
                ]
                
                for other_pattern in other_section_patterns:
                    other_match = re.search(other_pattern, text[search_start:], re.IGNORECASE)
                    if other_match:
                        # ถ้าเป็นส่วนท้ายของเอกสาร ให้ใช้ตำแหน่งนี้
                        if 'จัดทำ' in other_pattern or 'document' in other_pattern.lower():
                            end_pos = min(end_pos, search_start + other_match.start())
                            break
                
                # ถ้าไม่มีคำว่า "ต้นฉบับ" หรือ "Original" แต่ก็ไม่มี "สำเนา"
                # ให้ถือว่าเป็นต้นฉบับ (เพราะเอกสารส่วนใหญ่จะเป็นต้นฉบับ)
                # แต่ถ้ามีคำว่า "ต้นฉบับ" หรือ "Original" ให้ความสำคัญมากกว่า
                if has_original or not has_copy:
                    # ถ้ามีคำว่า "ต้นฉบับ" หรือ "Original" ให้ความสำคัญมากกว่า
                    if has_original and (best_match is None or not re.search(r'ต้นฉบับ|Original|ORIGINAL', best_match, re.IGNORECASE)):
                        best_match = text[start_pos:end_pos]
                        best_start = start_pos
                        best_end = end_pos
                    elif not has_copy and best_match is None:
                        # ถ้าไม่มี "สำเนา" และยังไม่เจอส่วนที่ดีกว่า ให้ใช้ส่วนนี้
                        best_match = text[start_pos:end_pos]
                        best_start = start_pos
                        best_end = end_pos
        
        if best_match:
            logger.info(f"✅ พบส่วนต้นฉบับของใบกำกับภาษี (ความยาว: {len(best_match)} ตัวอักษร)")
            return best_match
        
        # ถ้าไม่พบส่วนที่ชัดเจน ให้ใช้ทั้งเอกสาร (แต่ log warning)
        logger.warning("⚠️ ไม่พบส่วนต้นฉบับของใบกำกับภาษีที่ชัดเจน ใช้ทั้งเอกสาร")
        return text