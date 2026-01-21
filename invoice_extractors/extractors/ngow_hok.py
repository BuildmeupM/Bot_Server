"""
Ngow Hok Invoice Extractor
===========================
Extractor สำหรับดึงข้อมูลจาก บริษัท โงวฮก จำกัด

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class NgowHokExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก บริษัท โงวฮก จำกัด"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "โงวฮก",
        "Ngow Hok",
        "NGOW HOCK CO., LTD.",
        "NGOW HOCK"
    ]
    
    def __init__(self):
        """Initialize Ngow Hok Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ Ngow Hok หรือไม่
        ต้องมีทั้ง 2 เงื่อนไข:
        1. ชื่อบริษัท "บริษัท โงวฮก จำกัด" หรือ "NGOW HOCK CO., LTD."
        2. Tax ID "0105472000024" หรือ "0105567200024"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร Ngow Hok (มีทั้ง 2 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0105472000024" หรือ "0105567200024"
        has_tax_id = "0105472000024" in text or "0105567200024" in text
        
        # ต้องมีทั้ง 2 เงื่อนไขถึงจะผ่าน
        return has_company and has_tax_id
    
    def extract_company_name(self, text: str) -> str:
        """ดึงชื่อบริษัท"""
        return "บริษัท โงวฮก จำกัด"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษีจาก 'เลขประจำตัวผู้เสียภาษี 0105472000024' หรือ '0105567200024'"""
        # Pattern: เลขประจำตัวผู้เสียภาษี 0105472000024 หรือ 0105567200024
        patterns = [
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*(\d{13})',
            r'Tax\s+ID\s*[:.]?\s*(\d{13})',
            r'เลขประจำตัวผู้เสียภาษีอากร\s*[:.]?\s*(\d{13})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                tax_id = match.group(1).strip()
                # ตรวจสอบว่าเป็น Tax ID ที่รองรับ
                if tax_id in ["0105472000024", "0105567200024"]:
                    return tax_id
        
        # ถ้าไม่พบ pattern ให้ตรวจสอบว่า Tax ID อยู่ใน text หรือไม่
        if "0105567200024" in text:
            return "0105567200024"
        if "0105472000024" in text:
            return "0105472000024"
        
        return None
    
    def extract_branch(self, text: str) -> Optional[str]:
        """ดึงสาขาจาก 'สาขา 00004'"""
        # Pattern: สาขา 00004
        patterns = [
            r'สาขา\s*[:.]?\s*(\d{5})',
            r'Branch\s*[:.]?\s*(\d{5})',
            r'สำนักงานสาขา\s*[:.]?\s*(\d{5})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่จาก 'วันที่ DATE 31/10/2025' และแปลงเป็น dd/mm/yyyy"""
        # Pattern: วันที่ DATE 31/10/2025
        patterns = [
            r'วันที่\s+DATE\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
            r'DATE\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
            r'วันที่\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
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
        """ดึงเลขที่เอกสารจาก 'เลขที่ NO. N-B25103946'"""
        # Pattern: เลขที่ NO. N-B25103946
        patterns = [
            r'เลขที่\s+NO[.:]?\s*[:.]?\s*([A-Z0-9\-]+)',
            r'NO[.:]?\s*[:.]?\s*([A-Z0-9\-]+)',
            r'Document\s+No[.:]?\s*[:.]?\s*([A-Z0-9\-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def extract_address(self, text: str) -> Optional[str]:
        """
        ดึงข้อมูลที่อยู่บริษัท
        
        ที่อยู่: 127/1 ถนนรัชดาภิเษก แขวงอ่อนนุช เขตยานนาวา กรุงเทพฯ 10120
        
        Returns:
            ที่อยู่รวม (string)
        """
        # ลองหาที่อยู่จาก text ก่อน (มักจะอยู่ในส่วนสาขา)
        lines = text.split('\n')
        address_lines = []
        collecting = False
        
        # หาตำแหน่งที่เริ่มต้นที่อยู่ (มักจะอยู่หลังสาขา)
        for i, line in enumerate(lines):
            line_clean = line.strip()
            
            # หา "สาขา" หรือ "โงวฮก" แล้วเก็บบรรทัดถัดไปที่เป็นที่อยู่
            if ('โงวฮก' in line_clean and 'บริษัท' in line_clean) or ('สาขา' in line_clean and 'อาคาร' in line_clean):
                collecting = True
                continue
            
            # ถ้ากำลังเก็บข้อมูลที่อยู่
            if collecting:
                # หยุดเมื่อเจอ TaxID, Tax ID, เลขประจำตัวผู้เสียภาษี, หรือ header อื่นๆ
                if any(keyword in line_clean for keyword in ['TaxID', 'Tax ID', 'เลขประจำตัวผู้เสียภาษี', 'ใบเสร็จ', 'ใบกำกับ', 'DATE', 'NO.']):
                    break
                
                # เก็บบรรทัดที่มีข้อมูล (ไม่ใช่บรรทัดว่าง และมีความยาวมากกว่า 15 ตัวอักษร)
                if line_clean and len(line_clean) > 15:
                    # ตรวจสอบว่ามีรูปแบบที่อยู่ (มี "ถนน", "แขวง", "เขต", "กรุงเทพ", หรือรหัสไปรษณีย์ 5 หลัก)
                    if any(keyword in line_clean for keyword in ['ถนน', 'แขวง', 'เขต', 'กรุงเทพ', '10120', '127/1']):
                        # ลบส่วนที่ไม่ใช่ที่อยู่ (เช่น โทร., แฟกซ์)
                        line_clean = re.sub(r'\s*(โทร\.|แฟกซ์\.|Fax\.|Tel\.).*$', '', line_clean, flags=re.IGNORECASE)
                        address_lines.append(line_clean.strip())
                        break  # หาได้แล้ว ให้หยุด
        
        # รวมที่อยู่ทั้งหมด
        if address_lines:
            address = ' '.join(address_lines).strip()
            # ทำความสะอาด: ลบ space หลายตัว
            address = re.sub(r'\s+', ' ', address)
            if len(address) > 15:
                return address
        
        # Fallback: ใช้ที่อยู่ default
        return "127/1 ถนนรัชดาภิเษก แขวงอ่อนนุช เขตยานนาวา กรุงเทพฯ 10120"
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """ดึงข้อมูลบัญชี (Account Name / Account Code)"""
        return {
            'account_name': None,
            'account_code': None
        }
    
    def extract_withholding_tax(self, text: str) -> Dict[str, Optional[float]]:
        """ดึงข้อมูลหัก ณ ที่จ่าย"""
        return {
            'withholding_tax_percent': None,
            'withholding_tax_amount': None
        }
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงข้อมูลยอดเงิน
        
        - Net Total: 600.00 -> amount_before_vat
        - ภาษีมูลค่าเพิ่ม 7%: 42.00 -> vat_amount
        - Grand Total: 642.00 -> total_amount
        """
        amounts = {
            'amount_before_vat': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        # ดึง Net Total (ยอดก่อนภาษี)
        net_total_patterns = [
            r'Net\s+Total\s*[:.]?\s*([\d,]+\.?\d*)',
            r'รวมราคา\s+Net\s+Total\s*[:.]?\s*([\d,]+\.?\d*)',
            r'รวมราคา\s*[:.]?\s*([\d,]+\.?\d*)',
        ]
        for pattern in net_total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    amounts['amount_before_vat'] = float(amount_str)
                    break
                except ValueError:
                    pass
        
        # ดึงภาษีมูลค่าเพิ่ม 7% (ยอดภาษี)
        vat_patterns = [
            r'ภาษีมูลค่าเพิ่ม\s+7%\s*[:.]?\s*([\d,]+\.?\d*)',
            r'VAT\s+7%\s*[:.]?\s*([\d,]+\.?\d*)',
            r'ภาษีมูลค่าเพิ่ม\s*[:.]?\s*([\d,]+\.?\d*)',
        ]
        for pattern in vat_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    amounts['vat_amount'] = float(amount_str)
                    break
                except ValueError:
                    pass
        
        # ดึง Grand Total (ยอดรวม)
        grand_total_patterns = [
            r'Grand\s+Total\s*[:.]?\s*([\d,]+\.?\d*)',
            r'จำนวนเงินรวมทั้งสิ้น\s+Grand\s+Total\s*[:.]?\s*([\d,]+\.?\d*)',
            r'จำนวนเงินรวมทั้งสิ้น\s*[:.]?\s*([\d,]+\.?\d*)',
        ]
        for pattern in grand_total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    amounts['total_amount'] = float(amount_str)
                    break
                except ValueError:
                    pass
        
        # ถ้าไม่มี total_amount แต่มี amount_before_vat และ vat_amount ให้คำนวณ
        if amounts['total_amount'] is None and amounts['amount_before_vat'] is not None and amounts['vat_amount'] is not None:
            amounts['total_amount'] = amounts['amount_before_vat'] + amounts['vat_amount']
        
        return amounts
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """
        ดึงหมายเหตุ: B/L SZXGC25090716 {ชื่อไฟล์เก่า}
        อ่านข้อมูลจากบรรทัดที่มี "เลขที่เอกสาร / REF. No. | รายการ / Description | จำนวนเงิน / Amount"
        แล้วตามด้วย "ICN25103563 SZXGC25090716 | CLEANING SERVICES | 600.00"
        """
        remark_parts = []
        
        # หาบรรทัดที่มี "เลขที่เอกสาร / REF. No." หรือ "REF. No."
        lines = text.split('\n')
        bl_no = None
        
        for i, line in enumerate(lines):
            line_clean = line.strip()
            
            # หาบรรทัดที่มี header "เลขที่เอกสาร / REF. No." หรือ "REF. No."
            if 'เลขที่เอกสาร' in line_clean and 'REF. No.' in line_clean:
                # ดูบรรทัดถัดไป
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    # ตัวอย่าง: "ICN25103563 SZXGC25090716 | CLEANING SERVICES | 600.00"
                    # ดึงส่วนก่อน | (ส่วนแรก)
                    if '|' in next_line:
                        first_part = next_line.split('|')[0].strip()
                        # แยกด้วย space และหา B/L No. (ตัวที่ 2 หลังเลขที่เอกสาร)
                        parts = first_part.split()
                        if len(parts) >= 2:
                            # ตัวที่ 2 น่าจะเป็น B/L No. (เช่น SZXGC25090716)
                            candidate = parts[1]
                            # ตรวจสอบว่าเป็นรูปแบบ B/L No. (ตัวอักษร + ตัวเลข)
                            if re.match(r'^[A-Z]{2,}[0-9]{6,}$', candidate):
                                bl_no = candidate
                                break
                    
                    # ถ้ายังไม่เจอ ลองหาจาก pattern ทั่วไปในบรรทัดถัดไป
                    if not bl_no:
                        # หา B/L No. ที่เป็นตัวอักษรและตัวเลข (เช่น SZXGC25090716)
                        # หาทุกตัวที่ match pattern แล้วเลือกตัวที่ยาวที่สุด (เพราะ B/L No. มักจะยาว)
                        all_matches = re.findall(r'\b([A-Z]{3,}[0-9]{8,})\b', next_line)
                        if all_matches:
                            bl_no = max(all_matches, key=len)
                            break
            
            # หรือหาจากบรรทัดที่มี | และมีรูปแบบ "ICN25103563 SZXGC25090716 |"
            if not bl_no and '|' in line_clean and 'เลขที่เอกสาร' not in line_clean:
                # หา pattern ที่มีตัวอักษรและตัวเลขคั่นด้วย space ก่อน |
                parts = line_clean.split('|')
                if len(parts) > 0:
                    first_part = parts[0].strip()
                    # แยกด้วย space และหา B/L No. (ตัวที่ 2)
                    words = first_part.split()
                    if len(words) >= 2:
                        candidate = words[1]
                        if re.match(r'^[A-Z]{2,}[0-9]{6,}$', candidate):
                            bl_no = candidate
                            break
        
        # ถ้ายังไม่เจอ ลองหาจาก pattern ทั่วไปใน text ทั้งหมด
        if not bl_no:
            # หา pattern ที่เป็น B/L No. format (ตัวอักษร 3-10 ตัว + ตัวเลข 8-12 ตัว)
            bl_patterns = [
                r'\b([A-Z]{3,}[0-9]{8,})\b',  # SZXGC25090716
                r'B/L\s*No[.:]?\s*[:.]?\s*([A-Z0-9]+)',  # B/L No: SZXGC25090716
            ]
            for pattern in bl_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    # เลือกตัวที่ยาวที่สุด (เพราะ B/L No. มักจะยาวกว่า)
                    bl_no = max(matches, key=len)
                    break
        
        # เพิ่ม B/L No. ใน remark
        if bl_no:
            remark_parts.append(f"B/L {bl_no}")
        
        # เพิ่มชื่อไฟล์ (ตัด WHT_, VAT_, None_vat_ ออก)
        if filename:
            filename_clean = filename
            # ตัด WHT_, VAT_, None_vat_ ออก
            filename_clean = re.sub(r'(WHT_|VAT_|None_vat_)', '', filename_clean, flags=re.IGNORECASE)
            # ตัด .pdf ออก
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
        # ที่อยู่: 127/1 ถนนรัชดาภิเษก แขวงอ่อนนุช เขตยานนาวา กรุงเทพฯ 10120
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
            # ดึงเลขที่จาก "127/1" (อยู่ต้นที่อยู่)
            building_match = re.search(r'^(\d+(?:/\d+)?)', address.strip())
            if building_match:
                building_number = building_match.group(1).strip()
            
            # ดึงถนนจาก "ถนนรัชดาภิเษก"
            road_match = re.search(r'ถนน\s*([ก-๙A-Za-z]+)', address)
            if road_match:
                road = f"ถนน{road_match.group(1)}"
            
            # ดึงแขวงจาก "แขวงอ่อนนุช"
            subdistrict_match = re.search(r'แขวง\s*([ก-๙A-Za-z]+)', address)
            if subdistrict_match:
                subdistrict = subdistrict_match.group(1).strip()
            
            # ดึงเขตจาก "เขตยานนาวา"
            district_match = re.search(r'เขต\s*([ก-๙A-Za-z]+)', address)
            if district_match:
                district = district_match.group(1).strip()
            
            # ดึงจังหวัดจาก "กรุงเทพฯ" หรือ "กรุงเทพมหานคร"
            if 'กรุงเทพ' in address:
                province = 'กรุงเทพมหานคร'
            
            # ดึงรหัสไปรษณีย์
            postal_match = re.search(r'(\d{5})\s*$', address)
            if postal_match:
                postal_code = postal_match.group(1).strip()
        
        return {
            'success': True,
            'company': 'NGOW_HOK',
            'company_name': company_name,
            'tax_id': tax_id,
            'branch': branch,
            'date': date,
            'document_number': document_number,
            'address': address,  # ที่อยู่รวม
            'address_full': address_full,  # ที่อยู่รวม (สำหรับ parse_address)
            'building_number': building_number,  # เลขที่ (127/1)
            'other_info': other_info,  # อื่นๆ (ว่าง)
            'soi': soi,  # ซอย/ตรอก
            'road': road,  # ถนน (ถนนรัชดาภิเษก)
            'subdistrict': subdistrict,  # แขวง (อ่อนนุช)
            'district': district,  # เขต (ยานนาวา)
            'province': province,  # จังหวัด (กรุงเทพมหานคร)
            'postal_code': postal_code,  # รหัสไปรษณีย์ (10120)
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
