"""
Punthai Coffee Co., Ltd. Invoice Extractor
==========================================
Extractor สำหรับดึงข้อมูลจาก บริษัท กาแฟพันธุ์ไทย จำกัด (Punthai Coffee Co., Ltd.)

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class PunthaiCoffeeExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก บริษัท กาแฟพันธุ์ไทย จำกัด (Punthai Coffee Co., Ltd.)"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "Punthai Coffee Co., Ltd.",
        "กาแฟพันธุ์ไทย",
        "Punthai Coffee"
    ]
    
    # Tax ID
    TAX_ID = "0105555139534"
    
    def __init__(self):
        """Initialize Punthai Coffee Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ Punthai Coffee Co., Ltd. หรือไม่
        ต้องมีทั้ง 3 เงื่อนไข:
        1. ชื่อบริษัท "Punthai Coffee Co., Ltd." หรือ "กาแฟพันธุ์ไทย"
        2. Tax ID "0105555139534"
        3. เอกสาร "ใบกำกับภาษี" หรือ "TAX INVOICE"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร Punthai Coffee Co., Ltd. (มีทั้ง 3 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0105555139534"
        has_tax_id = self.TAX_ID in text
        
        # เงื่อนไข 3: ต้องมีเอกสาร "ใบกำกับภาษี" หรือ "TAX INVOICE"
        has_document_type = (
            "ใบกำกับภาษี" in text or 
            "TAX INVOICE" in text.upper() or
            "tax invoice" in text.lower()
        )
        
        # ต้องมีทั้ง 3 เงื่อนไขถึงจะผ่าน
        logger.info(f"🔍 [Punthai Coffee] ตรวจสอบเอกสาร:")
        logger.info(f"   - มีชื่อบริษัท: {has_company}")
        logger.info(f"   - มี Tax ID: {has_tax_id}")
        logger.info(f"   - มีเอกสาร: {has_document_type}")
        
        return has_company and has_tax_id and has_document_type
    
    def extract_company_name(self, text: str) -> str:
        """ดึงชื่อบริษัท"""
        # Pattern: บริษัท กาแฟพันธุ์ไทย จำกัด Punthai Coffee Co., Ltd.
        patterns = [
            r'บริษัท\s+กาแฟพันธุ์ไทย\s+จำกัด',
            r'กาแฟพันธุ์ไทย\s+จำกัด',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                company_name = match.group(0).strip()
                logger.info(f"✅ [Punthai Coffee] พบชื่อบริษัท: {company_name}")
                return company_name
        
        # Fallback
        logger.info(f"⚠️ [Punthai Coffee] ไม่พบชื่อบริษัท - ใช้ค่า default")
        return "บริษัท กาแฟพันธุ์ไทย จำกัด"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern: เลขประจำตัวผู้เสียภาษี 0105555139534
        patterns = [
            r'เลขประจำตัวผู้เสียภาษี\s+(\d{13})',
            r'Tax\s+ID\s*[:.]?\s*(\d{13})',
            r'TAX\s+ID\s*[:.]?\s*(\d{13})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                tax_id = match.group(1).strip()
                if tax_id == self.TAX_ID:
                    logger.info(f"✅ [Punthai Coffee] พบเลขประจำตัวผู้เสียภาษี: {tax_id}")
                    return tax_id
        
        # Fallback
        logger.info(f"⚠️ [Punthai Coffee] ไม่พบเลขประจำตัวผู้เสียภาษี - ใช้ค่า default: {self.TAX_ID}")
        return self.TAX_ID
    
    def extract_branch(self, text: str) -> Optional[str]:
        """ดึงสาขา"""
        # ไม่มีสาขา (ว่าง)
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่และแปลงเป็น dd/mm/yyyy"""
        # Pattern: วันที่ 31.10.2025 หรือ === วันที่ === 31.10.2025
        patterns = [
            r'===?\s*วันที่\s*===?\s*(\d{1,2})\.(\d{1,2})\.(\d{4})',
            r'วันที่\s*[:.]?\s*(\d{1,2})\.(\d{1,2})\.(\d{4})',
            r'(\d{1,2})\.(\d{1,2})\.(\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                day = match.group(1).zfill(2)
                month = match.group(2).zfill(2)
                year = match.group(3)
                
                date_str = f"{day}/{month}/{year}"
                logger.info(f"✅ [Punthai Coffee] พบวันที่: {date_str} (จาก: {match.group(0)})")
                return date_str
        
        logger.warning("⚠️ [Punthai Coffee] ไม่พบวันที่ในเอกสาร")
        return None
    
    def extract_document_number(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงเลขที่เอกสาร"""
        # อ่านจากชื่อไฟล์: 20251031_ETIV21202510005759_TIV_TH.pdf
        if filename:
            # Pattern: ETIV + ตัวเลข
            pattern = r'(ETIV\d+)'
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                doc_no = match.group(1)
                logger.info(f"✅ [Punthai Coffee] พบเลขที่เอกสารจากชื่อไฟล์: {doc_no}")
                return doc_no
        
        # Fallback: อ่านจาก text
        patterns = [
            r'===?\s*เลขที่\s*===?\s*([A-Z0-9]+)',
            r'เลขที่\s*[:.]?\s*([A-Z0-9]+)',
            r'(ETIV\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doc_no = match.group(1).strip()
                if doc_no and len(doc_no) > 5:
                    logger.info(f"✅ [Punthai Coffee] พบเลขที่เอกสารจาก text: {doc_no}")
                    return doc_no
        
        logger.warning("⚠️ [Punthai Coffee] ไม่พบเลขที่เอกสาร")
        return None
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงข้อมูลยอดเงิน
        
        จากตาราง:
        มูลค่ารวมก่อนภาษี | 20,670.26
        ภาษีมูลค่าเพิ่ม | 1,446.92
        มูลค่ารวมภาษี | 22,117.18
        """
        amounts = {
            'amount_before_vat': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        lines = text.split('\n')
        logger.info(f"📋 [Punthai Coffee] เริ่มอ่านยอดเงินจาก {len(lines)} บรรทัด")
        
        # Helper function: แปลง string เป็น float และตรวจสอบความถูกต้อง
        def safe_float(value_str: str) -> Optional[float]:
            """แปลง string เป็น float และตรวจสอบความถูกต้อง"""
            try:
                value_str_clean = value_str.replace(',', '').strip()
                if not re.match(r'^\d+\.?\d*$', value_str_clean):
                    return None
                value = float(value_str_clean)
                if value >= 0:
                    return value
            except (ValueError, AttributeError):
                pass
            return None
        
        # อ่านทีละบรรทัด
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            logger.debug(f"📄 [Punthai Coffee] บรรทัด {i}: {line}")
            
            # หา "มูลค่ารวมก่อนภาษี"
            if 'มูลค่ารวมก่อนภาษี' in line:
                logger.info(f"✅ [Punthai Coffee] พบบรรทัด 'มูลค่ารวมก่อนภาษี' ที่บรรทัด {i}: {line}")
                
                # ถ้ามี pipe separator ให้อ่านจากหลัง pipe
                if '|' in line:
                    parts = [p.strip() for p in line.split('|')]
                    logger.info(f"   แยกด้วย pipe: {parts}")
                    if len(parts) >= 2:
                        val = safe_float(parts[-1])  # ใช้ส่วนสุดท้ายหลัง pipe
                        if val is not None:
                            amounts['amount_before_vat'] = val
                            logger.info(f"   ✅ อ่านยอดก่อนภาษีได้: {amounts['amount_before_vat']}")
                else:
                    # หาตัวเลขในบรรทัด (รองรับ comma)
                    numbers = re.findall(r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d+\.?\d*', line)
                    logger.info(f"   พบตัวเลข: {numbers}")
                    if numbers:
                        val = safe_float(numbers[-1])  # ใช้ตัวเลขตัวสุดท้าย
                        if val is not None:
                            amounts['amount_before_vat'] = val
                            logger.info(f"   ✅ อ่านยอดก่อนภาษีได้: {amounts['amount_before_vat']}")
            
            # หา "ภาษีมูลค่าเพิ่ม"
            elif 'ภาษีมูลค่าเพิ่ม' in line and 'มูลค่ารวม' not in line:
                logger.info(f"✅ [Punthai Coffee] พบบรรทัด 'ภาษีมูลค่าเพิ่ม' ที่บรรทัด {i}: {line}")
                
                # ถ้ามี pipe separator ให้อ่านจากหลัง pipe
                if '|' in line:
                    parts = [p.strip() for p in line.split('|')]
                    logger.info(f"   แยกด้วย pipe: {parts}")
                    if len(parts) >= 2:
                        val = safe_float(parts[-1])  # ใช้ส่วนสุดท้ายหลัง pipe
                        if val is not None:
                            amounts['vat_amount'] = val
                            logger.info(f"   ✅ อ่านยอดภาษีได้: {amounts['vat_amount']}")
                else:
                    # หาตัวเลขในบรรทัด (รองรับ comma)
                    numbers = re.findall(r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d+\.?\d*', line)
                    logger.info(f"   พบตัวเลข: {numbers}")
                    if numbers:
                        val = safe_float(numbers[-1])  # ใช้ตัวเลขตัวสุดท้าย
                        if val is not None:
                            amounts['vat_amount'] = val
                            logger.info(f"   ✅ อ่านยอดภาษีได้: {amounts['vat_amount']}")
            
            # หา "มูลค่ารวมภาษี"
            elif 'มูลค่ารวมภาษี' in line:
                logger.info(f"✅ [Punthai Coffee] พบบรรทัด 'มูลค่ารวมภาษี' ที่บรรทัด {i}: {line}")
                
                # ถ้ามี pipe separator ให้อ่านจากหลัง pipe
                if '|' in line:
                    parts = [p.strip() for p in line.split('|')]
                    logger.info(f"   แยกด้วย pipe: {parts}")
                    if len(parts) >= 2:
                        val = safe_float(parts[-1])  # ใช้ส่วนสุดท้ายหลัง pipe
                        if val is not None:
                            amounts['total_amount'] = val
                            logger.info(f"   ✅ อ่านยอดรวมได้: {amounts['total_amount']}")
                else:
                    # หาตัวเลขในบรรทัด (รองรับ comma)
                    numbers = re.findall(r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d+\.?\d*', line)
                    logger.info(f"   พบตัวเลข: {numbers}")
                    if numbers:
                        val = safe_float(numbers[-1])  # ใช้ตัวเลขตัวสุดท้าย
                        if val is not None:
                            amounts['total_amount'] = val
                            logger.info(f"   ✅ อ่านยอดรวมได้: {amounts['total_amount']}")
        
        # สรุปผลการอ่านข้อมูล
        logger.info(f"📊 [Punthai Coffee] สรุปผลการอ่านยอดเงิน:")
        logger.info(f"   - ยอดก่อนภาษีมูลค่าเพิ่ม: {amounts['amount_before_vat']}")
        logger.info(f"   - ยอดภาษีมูลค่าเพิ่ม: {amounts['vat_amount']}")
        logger.info(f"   - ยอดหลังบวกภาษีมูลค่าเพิ่ม: {amounts['total_amount']}")
        
        return amounts
    
    def extract_withholding_tax(self, text: str) -> Dict[str, Optional[float]]:
        """ดึงข้อมูลหัก ณ ที่จ่าย"""
        result = {
            'withholding_tax_percent': None,
            'withholding_tax_amount': None
        }
        
        # ไม่มีข้อมูลหัก ณ ที่จ่าย (ว่าง)
        return result
    
    def extract_address(self, text: str) -> Dict[str, Optional[str]]:
        """
        ดึงข้อมูลที่อยู่
        
        ที่อยู่รวม: เลขที่ 90 อาคารซีดับเบิ้ลยู ทาวเวอร์ เอ ชั้นที่ 33 ถนนรัชดาภิเษก แขวงห้วยขวาง เขตห้วยขวาง กรุงเทพมหานคร 10310
        """
        address_data = {
            'address_full': '',
            'building_number': '',
            'other_info': '',
            'soi': '',
            'road': '',
            'district': '',
            'subdistrict': '',
            'province': '',
            'postal_code': ''
        }
        
        lines = text.split('\n')
        logger.info(f"📋 [Punthai Coffee] เริ่มอ่านที่อยู่จาก {len(lines)} บรรทัด")
        
        # หาที่อยู่จากบรรทัดที่มี "เลขที่ 90 อาคารซีดับเบิ้ลยู"
        address_full = None
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if 'เลขที่ 90' in line and 'อาคารซีดับเบิ้ลยู' in line:
                logger.info(f"✅ [Punthai Coffee] พบบรรทัดที่อยู่ที่บรรทัด {i}: {line}")
                address_full = line
                # ตัดข้อมูลที่อยู่หลังรหัสไปรษณีย์ออก
                address_full = re.sub(r'\s+10310.*$', ' 10310', address_full)
                break
        
        if address_full:
            address_data['address_full'] = address_full
            logger.info(f"   ที่อยู่รวม: {address_full}")
            
            # แยกส่วนต่างๆ ของที่อยู่
            # เลขที่: 90
            building_match = re.search(r'เลขที่\s+(\d+)', address_full)
            if building_match:
                address_data['building_number'] = building_match.group(1)
                logger.info(f"   เลขที่: {address_data['building_number']}")
            
            # อื่นๆ: อาคารซีดับเบิ้ลยู ทาวเวอร์ เอ ชั้นที่ 33
            other_match = re.search(r'อาคาร[^ถนน]+', address_full)
            if other_match:
                address_data['other_info'] = other_match.group(0).strip()
                logger.info(f"   อื่นๆ: {address_data['other_info']}")
            
            # ถนน: ถนนรัชดาภิเษก
            road_match = re.search(r'ถนน\s+([^\s]+)', address_full)
            if road_match:
                address_data['road'] = f"ถนน{road_match.group(1)}"
                logger.info(f"   ถนน: {address_data['road']}")
            
            # แขวง: ห้วยขวาง
            subdistrict_match = re.search(r'แขวง\s+([^\s]+)', address_full)
            if subdistrict_match:
                address_data['subdistrict'] = subdistrict_match.group(1)
                logger.info(f"   แขวง: {address_data['subdistrict']}")
            
            # เขต: ห้วยขวาง
            district_match = re.search(r'เขต\s+([^\s]+)', address_full)
            if district_match:
                address_data['district'] = district_match.group(1)
                logger.info(f"   เขต: {address_data['district']}")
            
            # จังหวัด: กรุงเทพมหานคร
            province_match = re.search(r'จังหวัด\s+([^\s]+)', address_full)
            if province_match:
                address_data['province'] = province_match.group(1)
                logger.info(f"   จังหวัด: {address_data['province']}")
            
            # เลขไปรษณีย์: 10310
            postal_match = re.search(r'(\d{5})\s*$', address_full)
            if postal_match:
                address_data['postal_code'] = postal_match.group(1)
                logger.info(f"   เลขไปรษณีย์: {address_data['postal_code']}")
        else:
            logger.warning("⚠️ [Punthai Coffee] ไม่พบที่อยู่ในเอกสาร")
        
        return address_data
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """ดึงข้อมูลบัญชี (Account Name / Account Code)"""
        # ไม่มีข้อมูลบัญชี (ว่าง)
        return {
            'account_name': None,
            'account_code': None
        }
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงหมายเหตุ"""
        # ไม่มีหมายเหตุ (ว่าง)
        return None
    
    def detect_document_type(self, text: str, amounts: Dict[str, Optional[float]], withholding: Dict[str, Optional[float]]) -> int:
        """ตรวจสอบประเภทเอกสาร (1 = มีภาษีมูลค่าเพิ่ม, 2 = ไม่มีภาษีมูลค่าเพิ่ม)"""
        # ถ้ามียอดภาษี แสดงว่ามีภาษีมูลค่าเพิ่ม
        if amounts.get('vat_amount') and amounts['vat_amount'] > 0:
            return 1  # มีภาษีมูลค่าเพิ่ม
        
        return 1  # มีภาษีมูลค่าเพิ่ม (ตามที่ระบุ)
    
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
        logger.info("=" * 80)
        logger.info("🚀 [Punthai Coffee] เริ่มดึงข้อมูลจากเอกสาร")
        logger.info("=" * 80)
        
        # ดึงข้อมูล
        company_name = self.extract_company_name(text)
        tax_id = self.extract_tax_id(text)
        branch = self.extract_branch(text)
        date = self.extract_date(text)
        document_number = self.extract_document_number(text, filename)
        address_data = self.extract_address(text)
        account_info = self.extract_account_info(text)
        amounts = self.extract_amounts(text)
        withholding = self.extract_withholding_tax(text)
        remark = self.extract_remark(text, filename)
        document_type = self.detect_document_type(text, amounts, withholding)
        
        # สร้างชื่อไฟล์ใหม่: ต้นทุนขายสินค้า_กาแฟพันธ์ไทย
        new_filename = "ต้นทุนขายสินค้า_กาแฟพันธ์ไทย"
        if filename:
            # เพิ่มนามสกุลไฟล์ถ้ามี
            if '.' in filename:
                ext = filename.split('.')[-1]
                new_filename = f"{new_filename}.{ext}"
        
        logger.info("=" * 80)
        logger.info("✅ [Punthai Coffee] ดึงข้อมูลเสร็จสิ้น")
        logger.info("=" * 80)
        
        return {
            'success': True,
            'company': 'PUNTHAI_COFFEE',
            'company_name': company_name,
            'tax_id': tax_id,
            'branch': branch,
            'date': date,
            'document_number': document_number,
            'address': address_data.get('address_full', ''),
            'address_full': address_data.get('address_full', ''),
            'building_number': address_data.get('building_number', ''),
            'other_info': address_data.get('other_info', ''),
            'soi': address_data.get('soi', ''),
            'road': address_data.get('road', ''),
            'subdistrict': address_data.get('subdistrict', ''),
            'district': address_data.get('district', ''),
            'province': address_data.get('province', ''),
            'postal_code': address_data.get('postal_code', ''),
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

