"""
Tax Form Parser - สำหรับอ่านข้อมูลจากแบบภาษีแต่ละประเภท
"""
import re
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class TaxFormParser:
    """คลาสสำหรับ parse ข้อมูลจากแบบภาษีแต่ละประเภท"""
    
    def __init__(self):
        pass
    
    def parse_tax_form(self, text: str, raw_content: str = None) -> Dict[str, Any]:
        """
        Parse ข้อมูลจากข้อความที่อ่านได้จาก OCR
        
        Args:
            text: ข้อความที่ format แล้ว (formatted_text)
            raw_content: ข้อความดิบจาก OCR (ใช้สำหรับ parse ตัวเลขที่ถูกต้อง)
            
        Returns:
            Dictionary ที่มีข้อมูลแบบภาษี
        """
        # ใช้ raw_content ถ้ามี (เพื่อความแม่นยำในการ parse ตัวเลข)
        parse_text = raw_content if raw_content else text
        
        # ตรวจสอบประเภทแบบภาษี
        tax_form_type = self._detect_tax_form_type(parse_text)
        
        # Parse ข้อมูลตามประเภทแบบภาษี
        if 'ภ.พ.30' in tax_form_type or 'ภพ.30' in tax_form_type or 'ภพ30' in tax_form_type:
            return self._parse_pp30(parse_text, text)
        elif 'ภ.พ.36' in tax_form_type or 'ภพ.36' in tax_form_type or 'ภพ36' in tax_form_type:
            return self._parse_pp36(parse_text, text)
        elif 'ภ.ง.ด.54' in tax_form_type or 'ภงด.54' in tax_form_type or 'ภงด54' in tax_form_type:
            return self._parse_pnd54(parse_text, text)
        elif 'ภ.ง.ด.53' in tax_form_type or 'ภงด.53' in tax_form_type or 'ภงด53' in tax_form_type:
            return self._parse_pnd53(parse_text, text)
        elif 'ภ.ง.ด.1' in tax_form_type or 'ภงด.1' in tax_form_type or 'ภงด1' in tax_form_type:
            return self._parse_pnd1(parse_text, text)
        elif 'ภ.ง.ด.3' in tax_form_type or 'ภงด.3' in tax_form_type or 'ภงด3' in tax_form_type:
            return self._parse_pnd3(parse_text, text)
        elif 'Pay-in' in tax_form_type or 'Pay-In' in tax_form_type:
            return self._parse_payin(parse_text, text)
        elif 'กองทุน กยศ.' in tax_form_type or 'กยศ.' in tax_form_type:
            return self._parse_student_loan(parse_text, text)
        elif 'ประกันสังคม' in tax_form_type:
            return self._parse_social_security(parse_text, text)
        else:
            # Parse ข้อมูลพื้นฐาน
            return self._parse_basic_info(parse_text, text)
    
    def _detect_tax_form_type(self, text: str) -> str:
        """ตรวจสอบประเภทแบบภาษี"""
        tax_form_patterns = [
            (r'ภ\.ง\.ด\.53|ภงด\.53|ภงด53', 'ภ.ง.ด.53'),
            (r'ภ\.ง\.ด\.1|ภงด\.1|ภงด1', 'ภ.ง.ด.1'),
            (r'ภ\.ง\.ด\.3|ภงด\.3|ภงด3', 'ภ.ง.ด.3'),
            (r'ภ\.ง\.ด\.54|ภงด\.54|ภงด54', 'ภ.ง.ด.54'),
            (r'ภ\.ธ\.40|ภธ\.40|ภธ40', 'ภ.ธ.40'),
            (r'ภ\.พ\.30|ภพ\.30|ภพ30', 'ภ.พ.30'),
            (r'ภ\.พ\.36|ภพ\.36|ภพ36', 'ภ.พ.36'),
        ]
        
        for pattern, form_type in tax_form_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return form_type
        
        # ตรวจสอบ Pay-in
        if re.search(r'Pay-in|Pay-In|ชุดชำระเงิน', text, re.IGNORECASE):
            # ตรวจสอบว่าเป็น กองทุน กยศ. หรือไม่
            if re.search(r'กยศ|กองทุนเงินให้กู้ยืมเพื่อการศึกษา|Student\s*Loan\s*Fund', text, re.IGNORECASE):
                return 'กองทุน กยศ.'  # ✅ เปลี่ยนกลับเป็นชื่อเดิม
            return 'Pay-in ชำระภาษี'
        
        # ตรวจสอบประกันสังคม
        if re.search(r'ประกันสังคม', text, re.IGNORECASE):
            return 'ประกันสังคม'
        
        # ตรวจสอบกองทุน กยศ. (สำหรับกรณีที่ไม่มี Pay-in ในชื่อไฟล์)
        if re.search(r'กองทุน\s*กยศ\.?|กยศ\.|กองทุนเงินให้กู้ยืมเพื่อการศึกษา', text, re.IGNORECASE):
            return 'กองทุน กยศ.'  # ✅ เปลี่ยนกลับเป็นชื่อเดิม
        
        return 'ไม่ทราบประเภท'
    
    def _parse_basic_info(self, text: str, formatted_text: str) -> Dict[str, Any]:
        """Parse ข้อมูลพื้นฐาน (ชื่อบริษัท, เลขประจำตัวผู้เสียภาษี, ฯลฯ)"""
        data = {
            'tax_form_type': None,
            'company_name': None,
            'tax_id': None,
            'filing_type': None,
            'filing_period': {'month': None, 'year': None},
            'payment_date': None,
            'due_date': None,
            'amounts': {}
        }
        
        # 1. หาชื่อบริษัท
        company_patterns = [
            # Pattern 1: หาจาก "ชื่อผู้มีหน้าที่หักภาษี ณ ที่จ่าย" → สาขาที่ X → บรรทัดถัดไป (ภ.ง.ด.3)
            r'ชื่อผู้มีหน้าที่หัก\s*ภาษี\s*ณ\s*ที่จ่าย[^\n]*\n\s*สาขาที่[^\n]*\n\s*(บริษัท\s+[^\n]+?จำกัด(?:\s+(?:มหาชน|\(มหาชน\)))?)',
            # Pattern 2: หาจาก "ชื่อผู้นำส่งภาษี สาขาที่ X บริษัท..." (ภ.ง.ด.54)
            r'ชื่อผู้นำส่งภาษี[^\n]*?สาขาที่\s*\d+\s*\n\s*(บริษัท\s+[^\n]+?จำกัด(?:\s+(?:มหาชน|\(มหาชน\)))?)',
            r'ชื่อผู้นำส่งภาษี[^\n]*?สาขาที่\s*\d+\s*\n[^\n]*\n\s*(บริษัท\s+[^\n]+?จำกัด(?:\s+(?:มหาชน|\(มหาชน\)))?)',
            # Pattern 3: หาจาก "ชื่อผู้ประกอบการ บริษัท..."
            r'ชื่อผู้ประกอบการ\s+(บริษัท\s+[^\n]+?จำกัด(?:\s+(?:มหาชน|\(มหาชน\)))?)',
            # Pattern 4: หาชื่อบริษัทโดยตรง (รูปแบบทั่วไป)
            r'(บริษัท\s+[ก-ฮa-zA-Z0-9\s\.\(\)]+?จำกัด(?:\s+(?:มหาชน|\(มหาชน\)))?)',
        ]
        for pattern in company_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                company_name = match.group(1).strip()
                # ทำความสะอาดชื่อบริษัท
                company_name = re.sub(r'\s+', ' ', company_name)  # ลบช่องว่างซ้ำ
                company_name = re.sub(r'\*+', '', company_name)  # ลบ *
                
                if 'บริษัท' in company_name or 'ห้างหุ้นส่วน' in company_name:
                    data['company_name'] = company_name
                    logger.info(f"✅ พบชื่อบริษัท: {company_name}")
                    break
        
        # 2. หาเลขประจำตัวผู้เสียภาษี
        tax_id_patterns = [
            r'เลขประจำตัวผู้เสียภาษีอากร\s+([0-9\s\-]{13,30})',
            r'เลขประจำตัวผู้เสียภาษีอากร[^\n]*\n([^\n]+)',
            r'\(ของผู้มีหน้าที่หัก\s*ภาษี\s*ณ\s*ที่จ่าย\)[^\n]*\n([^\n]+)',
            # รูปแบบที่ 1: หาเลขประจำตัวผู้เสียภาษีอากรที่อยู่หลัง "(ของผู้มีหน้าที่หักภาษี ณ ที่จ่าย)" และอาจมีช่องว่างหลายบรรทัด
            # รองรับ: 0 1 0 5 5 - 5 3 1 1 4 - 4 3 - 7
            r'\(ของผู้มีหน้าที่หัก\s*ภาษี\s*ณ\s*ที่จ่าย\)\s*\n\s*([0-9\s\-]{15,35})',
            # รูปแบบที่ 2: หาเลขประจำตัวผู้เสียภาษีอากรที่มีช่องว่างระหว่างตัวเลขและ dash
            # รองรับ: 0 1 0 5 5 - 5 3 1 1 4 - 4 3 - 7 หรือ 0 1 0 5 5-5 3 1 1 4-4 3-7
            r'เลขประจำตัวผู้เสียภาษีอากร[^\n]*(?:ของผู้มีหน้าที่หัก\s*ภาษี\s*ณ\s*ที่จ่าย\))?\s*\n\s*([0-9\s\-]{15,35})',
            # รูปแบบที่ 3: หาเลขประจำตัวผู้เสียภาษีอากรที่อยู่ในบรรทัดเดียวกับ "(ของผู้มีหน้าที่หักภาษี ณ ที่จ่าย)" หรือบรรทัดถัดไป
            # รองรับทั้งกรณีที่มีช่องว่างหลายบรรทัด
            r'\(ของผู้มีหน้าที่หัก\s*ภาษี\s*ณ\s*ที่จ่าย\)(?:\s*\n\s*)+([0-9\s\-]{15,35})',
        ]
        for pattern in tax_id_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                tax_id_raw = match.group(1).strip()
                # ลบช่องว่างและ dash
                tax_id_clean = re.sub(r'[\s\-]+', '', tax_id_raw)
                # ตรวจสอบว่าเป็นตัวเลข 13 หลัก
                if tax_id_clean.isdigit() and len(tax_id_clean) == 13:
                    # Format เป็น x-xxxx-xxxxx-xx-x
                    tax_id_formatted = f"{tax_id_clean[0]}-{tax_id_clean[1:5]}-{tax_id_clean[5:10]}-{tax_id_clean[10:12]}-{tax_id_clean[12]}"
                    data['tax_id'] = tax_id_formatted
                    logger.info(f"✅ พบเลขประจำตัวผู้เสียภาษี: {tax_id_formatted}")
                    break
        
        # 3. หาประเภทการยื่น
        if re.search(r'ยื่นปกติ', text, re.IGNORECASE):
            data['filing_type'] = 'ยื่นปกติ'
        elif re.search(r'ยื่นเพิ่มเติม', text, re.IGNORECASE):
            data['filing_type'] = 'ยื่นเพิ่มเติม'
        
        # 4. หาเดือนและปี
        month_patterns = [
            r'สำหรับเดือนภาษี[^\n]*?([มกกุมภาพันธ์มีนาคมเมษายนพฤษภาคมมิถุนายนกรกฎาคมสิงหาคมกันยายนตุลาคมพฤศจิกายนธันวาคม]+)',
            r'ประจำเดือน\s+([มกกุมภาพันธ์มีนาคมเมษายนพฤษภาคมมิถุนายนกรกฎาคมสิงหาคมกันยายนตุลาคมพฤศจิกายนธันวาคม]+)',
        ]
        year_patterns = [
            r'พ\.ศ\.\s*([0-9,]+)',
            r'พ\.ศ\s*([0-9,]+)',
            r'ปี\s+([0-9,]{4})',
        ]
        
        for pattern in month_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                month = match.group(1).strip()
                data['filing_period']['month'] = month
                break
        
        for pattern in year_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                year_str = match.group(1).replace(',', '').strip()
                try:
                    data['filing_period']['year'] = int(year_str)
                except ValueError:
                    pass
                break
        
        return data
    
    def _parse_pp30(self, text: str, formatted_text: str) -> Dict[str, Any]:
        """Parse ข้อมูล ภ.พ.30"""
        data = self._parse_basic_info(text, formatted_text)
        data['tax_form_type'] = 'ภ.พ.30'
        
        # Parse ข้อมูลเฉพาะ ภ.พ.30
        amounts = self._parse_pp30_amounts(text)
        data['amounts'] = amounts
        
        return data
    
    def _parse_pp30_amounts(self, text: str) -> Dict[str, float]:
        """Parse ยอดเงินจาก ภ.พ.30"""
        amounts = {}
        skip_old_method = False  # Flag เพื่อข้ามการ parse แบบเดิมถ้ามีข้อมูลจาก formatted text
        
        # ตรวจสอบว่ามีข้อความ "☑ ขอนำภาษีไปชำระในเดือนถัดไป" หรือไม่
        # ต้องมี checkbox ☑ เท่านั้น (ไม่ใช่ ☐ หรือไม่มี checkbox)
        # ถ้ามี ให้ตั้งยอดต้องชำระเป็น 0.00 (ไม่มียอดชำระ)
        # รองรับกรณีที่ OCR อาจอ่านผิด (มีช่องว่างแปลกๆ)
        carry_forward_patterns = [
            r'☑\s*ขอ\s*นำ\s*ภาษี\s*ไป\s*ชำระ\s*ใน\s*เดือน\s*ถัดไป',
            r'☑\s*ขอนำภาษีไปชำระในเดือนถัดไป',
            r'\[x\]\s*ขอนำภาษีไปชำระในเดือนถัดไป',
        ]
        
        for pattern in carry_forward_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                logger.info("✅ พบข้อความ '☑ ขอนำภาษีไปชำระในเดือนถัดไป' - ตั้งยอดต้องชำระเป็น 0.00 (ไม่มียอดชำระ)")
                # เพิ่ม flag พิเศษเพื่อบอก OCR processor ว่านี่เป็นกรณีพิเศษ (ไม่ใช่อ่านไม่ได้)
                # ใช้ค่า 0.01 บาทสำหรับ "ชำระเกิน" เพื่อให้ OCR processor รู้ว่ามีข้อมูล
                # (จะถูกแปลงกลับเป็น 0.00 ในภายหลัง)
                return {
                    'ต้องชำระ (ภ.พ.30)': 0.00,
                    'ชำระเกิน (ภ.พ.30)': 0.00,
                    'เงินเพิ่ม (ภ.พ.30)': 0.00,
                    'เบี้ยปรับ (ภ.พ.30)': 0.00,
                    '__carry_forward__': True  # Flag พิเศษเพื่อบอกว่าเป็นกรณีขอนำภาษีไปชำระเดือนถัดไป
                }
        
        # ตรวจสอบว่ามีรูปแบบ formatted text หรือไม่ (รูปแบบ: "  1. คำอธิบาย\n     จำนวนเงิน: 0.00")
        # รองรับทั้งแบบมีและไม่มี checkbox [x] หรือ [ ]
        # Pattern 1: แบบมี checkbox "  [x] 12. คำอธิบาย\n     จำนวนเงิน: -"
        # Pattern 2: แบบไม่มี checkbox "  1. คำอธิบาย\n     จำนวนเงิน: 0.00"
        formatted_patterns = [
            (r'\[\s*([x\s]*)\s*\]\s*(\d{1,2})\.\s+([^\n]+?)\n\s+จำนวนเงิน:\s+([^\n]+)', True),  # แบบมี checkbox
            (r'(\d{1,2})\.\s+([^\n]+?)\n\s+จำนวนเงิน:\s+([^\n]+)', False),  # แบบไม่มี checkbox
        ]
        
        formatted_matches = []
        checkbox_info = {}  # เก็บข้อมูล checkbox สำหรับข้อ 11 และ 12
        processed_items = set()  # เก็บ item numbers ที่ process แล้ว (เพื่อไม่ให้ซ้ำ)
        
        # หาแบบมี checkbox ก่อน (เพื่อให้ได้ข้อมูล checkbox)
        for pattern, has_checkbox in formatted_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            for match in matches:
                if has_checkbox:
                    checkbox_part = match[0] if len(match) > 0 else ''
                    item_num_str = match[1] if len(match) > 1 else match[0]
                    description = match[2] if len(match) > 2 else match[1]
                    amount_str = match[3] if len(match) > 3 else match[2]
                    checkbox_val = 'x' in checkbox_part.lower() if checkbox_part else False
                else:
                    item_num_str = match[0]
                    description = match[1]
                    amount_str = match[2]
                    checkbox_val = None
                
                try:
                    item_num = int(item_num_str)
                    # ข้ามถ้า process แล้ว (เพื่อไม่ให้ซ้ำ)
                    if item_num in processed_items:
                        continue
                    
                    formatted_matches.append((item_num_str, description, amount_str, checkbox_val))
                    processed_items.add(item_num)
                    
                    # เก็บข้อมูล checkbox สำหรับข้อ 11 และ 12
                    if item_num in [11, 12] and checkbox_val is not None:
                        checkbox_info[item_num] = checkbox_val
                except ValueError:
                    continue
        
        if formatted_matches:
            logger.info(f"✅ พบรูปแบบ formatted text: {len(formatted_matches)} รายการ")
            # Mapping ระหว่าง item number และ key ใน amounts
            item_mapping = {
                1: 'ยอดขายในเดือนนี้ (ภ.พ.30)',
                2: 'ยอดขายที่เสียภาษีในอัตราร้อยละ 0 (ภ.พ.30)',
                3: 'ยอดขายที่ได้รับยกเว้น (ภ.พ.30)',
                4: 'ยอดขายที่ต้องเสียภาษี (ภ.พ.30)',
                5: 'ภาษีขายเดือนนี้ (ภ.พ.30)',
                6: 'ยอดซื้อที่มีสิทธินำภาษีซื้อ (ภ.พ.30)',
                7: 'ภาษีซื้อเดือนนี้ (ภ.พ.30)',
                8: 'ภาษีที่ต้องชำระเดือนนี้ (ภ.พ.30)',
                9: 'ภาษีที่ชำระเกินเดือนนี้ (ภ.พ.30)',
                10: 'ภาษีที่ชำระเกินยกมา (ภ.พ.30)',
                11: 'ต้องชำระ (ภ.พ.30)',
                12: 'ชำระเกิน (ภ.พ.30)',
                13: 'เงินเพิ่ม (ภ.พ.30)',
                14: 'เบี้ยปรับ (ภ.พ.30)',
                15: 'รวมภาษี เงินเพิ่ม และเบี้ยปรับที่ต้องชำระ (ภ.พ.30)',
                16: 'รวมภาษีที่ชำระเกิน หลังคำนวณเงินเพิ่มและเบี้ยปรับแล้ว (ภ.พ.30)',
            }
            
            for item_num_str, description, amount_str, checkbox_val in formatted_matches:
                try:
                    item_num = int(item_num_str)
                    if item_num in item_mapping:
                        key = item_mapping[item_num]
                        
                        # เก็บข้อมูล checkbox สำหรับข้อ 11 และ 12
                        if item_num in [11, 12] and checkbox_val is not None:
                            checkbox_info[item_num] = checkbox_val
                        
                        # Parse จำนวนเงิน
                        amount_str_clean = amount_str.strip()
                        if amount_str_clean == '-' or amount_str_clean == '' or '[ไม่พบข้อมูล]' in amount_str_clean:
                            amount_value = 0.00
                        else:
                            # ลบ comma และ whitespace
                            amount_str_clean = amount_str_clean.replace(',', '').replace(' ', '').strip()
                            # ลบข้อความที่ติดมา (เช่น "245.0000" -> "245.00")
                            # รองรับรูปแบบ "245.0000" หรือ "245.00" หรือ "3,500.00"
                            amount_match = re.search(r'(\d{1,3}(?:,\d{3})*\.?\d*|\d+\.?\d*)', amount_str_clean)
                            if amount_match:
                                amount_str_clean = amount_match.group(1).replace(',', '')
                                try:
                                    amount_value = float(amount_str_clean)
                                except ValueError:
                                    amount_value = 0.00
                            else:
                                amount_value = 0.00
                        
                        amounts[key] = amount_value
                        logger.info(f"✅ [Formatted Text] พบข้อ {item_num}: {key} = {amount_value:,.2f}")
                except (ValueError, IndexError) as e:
                    logger.warning(f"⚠️ [Formatted Text] ไม่สามารถ parse ข้อ {item_num_str}: {e}")
                    continue
            
            # ตรวจสอบ checkbox สำหรับข้อ 11 และ 12 และคำนวณถ้าจำเป็น
            if 12 in checkbox_info and checkbox_info[12] is True:
                # ถ้ามี checkbox [x] ที่ข้อ 12 แต่ไม่มีจำนวนเงิน หรือจำนวนเงินเป็น 0 ให้คำนวณจากข้อ 9 + 10
                item12_value = amounts.get('ชำระเกิน (ภ.พ.30)', 0.00)
                if item12_value == 0.00:
                    item9 = amounts.get('ภาษีที่ชำระเกินเดือนนี้ (ภ.พ.30)', 0.00)
                    item10 = amounts.get('ภาษีที่ชำระเกินยกมา (ภ.พ.30)', 0.00)
                    if item9 > 0 or item10 > 0:
                        amounts['ชำระเกิน (ภ.พ.30)'] = item9 + item10
                        logger.info(f"✅ [Formatted Text] คำนวณข้อ 12 จาก ข้อ 9 ({item9:,.2f}) + 10 ({item10:,.2f}) = {amounts['ชำระเกิน (ภ.พ.30)']:,.2f}")
            
            if 11 in checkbox_info and checkbox_info[11] is True:
                # ถ้ามี checkbox [x] ที่ข้อ 11 แต่ไม่มีจำนวนเงิน ให้คำนวณจากข้อ 8 - 10
                item11_value = amounts.get('ต้องชำระ (ภ.พ.30)', 0.00)
                if item11_value == 0.00:
                    item8 = amounts.get('ภาษีที่ต้องชำระเดือนนี้ (ภ.พ.30)', 0.00)
                    item10 = amounts.get('ภาษีที่ชำระเกินยกมา (ภ.พ.30)', 0.00)
                    if item8 > 0:
                        item11_calc = item8 - item10
                        if item11_calc > 0:
                            amounts['ต้องชำระ (ภ.พ.30)'] = item11_calc
                            logger.info(f"✅ [Formatted Text] คำนวณข้อ 11 จาก ข้อ 8 ({item8:,.2f}) - 10 ({item10:,.2f}) = {amounts['ต้องชำระ (ภ.พ.30)']:,.2f}")
            
            # ถ้ามีข้อมูลจาก formatted text แล้ว ให้ไปยังส่วนการคำนวณต่อ
            if amounts:
                logger.info(f"✅ [Formatted Text] ดึงข้อมูลได้ {len(amounts)} รายการ จาก formatted text")
                # ไปยังส่วนการคำนวณต่อไป (ไม่ต้องใช้วิธีเดิม)
                # ข้ามไปยังส่วนการสร้าง result_amounts และการคำนวณ
                skip_old_method = True
            else:
                logger.warning("⚠️ [Formatted Text] ไม่พบข้อมูลจาก formatted text ให้ใช้วิธีเดิม")
                skip_old_method = False
        
        # อ่านจากทั้งข้อความ (ไม่จำกัดเฉพาะส่วน "การคำนวณภาษี")
        # ข้ามส่วนนี้ถ้ามีข้อมูลจาก formatted text แล้ว
        if not skip_old_method:
            # เพราะ OCR อาจอ่านได้หลายรูปแบบ และข้อมูลอาจอยู่ที่ไหนก็ได้
            # แยกแถวทั้งหมดจากข้อความ
            all_rows = [row.strip() for row in text.split('\n') if row.strip()]
            
            # หาแถวที่มี "ต้องชำระ" หรือ "11." หรือ "ชำระเกิน" หรือ "12." หรือ "เงินเพิ่ม" หรือ "เบี้ยปรับ"
            # ไม่จำเป็นต้องมี | ในแถว (เพราะบางแถวอาจไม่มี)
            target_keywords = ['11.', '12.', 'ต้องชำระ', 'ชำระเกิน', 'เงินเพิ่ม', 'เบี้ยปรับ']
            rows = []
            for row in all_rows:
                if any(keyword in row for keyword in target_keywords):
                    rows.append(row)
            
            # ถ้ายังไม่พบแถว ให้ลองหาจากส่วน "การคำนวณภาษี" (fallback)
            if len(rows) == 0:
                tax_calc_section = re.search(r'การคำนวณภาษี(.*?)(?=กรณียื่นแบบแสดงรายการ|การขอคืนภาษี|คำรับรอง|$)', text, re.DOTALL)
            if tax_calc_section:
                table_text = tax_calc_section.group(1)
                rows = [row.strip() for row in table_text.split('\n') if row.strip() and '|' in row]
            
            if rows:
                found_keys = set()
            
            # ฟังก์ชันช่วยในการหาค่าจากคอลัมน์ที่ถูกต้อง
            def find_amount_in_columns(columns, row_text, min_value=0, last_col_is_number=False):
                """
                หาค่าจากคอลัมน์ที่ถูกต้อง โดยตรวจสอบทั้งรูปแบบตาราง
                
                Args:
                    columns: รายการคอลัมน์
                    row_text: ข้อความทั้งแถว
                    min_value: ค่าต่ำสุดที่ยอมรับ
                    last_col_is_number: ถ้า True ให้หาตัวเลขจากคอลัมน์ก่อนสุดท้าย (กรณีคอลัมน์สุดท้ายเป็น "11" หรือ "12")
                """
                # ฟังก์ชันช่วยในการทำความสะอาดตัวเลข (รวมตัวเลขที่ถูกแบ่ง)
                def clean_number(text):
                    """ทำความสะอาดตัวเลขที่ถูกแบ่ง เช่น '21,7               774.57' -> '21774.57'"""
                    if not text:
                        return None
                    # ลบช่องว่างทั้งหมด
                    cleaned = re.sub(r'\s+', '', text)
                    # ลบ comma
                    cleaned = cleaned.replace(',', '')
                    # ลบตัวอักษรที่ไม่ใช่ตัวเลขและจุดทศนิยม
                    cleaned = re.sub(r'[^\d.]', '', cleaned)
                    return cleaned if cleaned else None
                
                # ฟังก์ชันตรวจสอบว่าเป็นตัวเลขเงินจริงหรือไม่ (ไม่ใช่ตัวเลขลำดับ)
                def is_valid_amount(value, original_text=""):
                    """
                    ตรวจสอบว่าเป็นตัวเลขเงินจริงหรือไม่
                    - ต้องมากกว่าหรือเท่ากับ 100 (เพราะตัวเลขเงินมักจะมากกว่า 100)
                    - หรือถ้ามี comma หรือจุดทศนิยมในข้อความเดิม แสดงว่าเป็นตัวเลขเงิน
                    """
                    if value < 100:
                        # ตรวจสอบว่ามี comma หรือจุดทศนิยมในข้อความเดิมหรือไม่
                        if ',' in original_text or '.' in original_text:
                            # ถ้ามี comma หรือจุดทศนิยม แสดงว่าเป็นตัวเลขเงิน (แม้จะน้อยกว่า 100)
                            return True
                        return False
                    return True
                
                # ตรวจสอบว่าคอลัมน์สุดท้ายเป็นตัวเลข (เช่น "11" หรือ "12")
                last_col_is_digit = False
                if len(columns) >= 2:
                    last_col = columns[-1].strip()
                    last_col_is_digit = last_col.isdigit()
                
                # ถ้า last_col_is_number = True และคอลัมน์สุดท้ายเป็นตัวเลข (เช่น "11" หรือ "12")
                # ให้หาตัวเลขจากคอลัมน์ก่อนสุดท้ายก่อน
                if last_col_is_number and last_col_is_digit and len(columns) >= 2:
                    second_last_col = columns[-2].strip()
                    cleaned = clean_number(second_last_col)
                    if cleaned and re.match(r'^\d+\.?\d*$', cleaned):
                        try:
                            amount_value = float(cleaned)
                            # ตรวจสอบว่าเป็นตัวเลขเงินจริงหรือไม่
                            if amount_value >= min_value and is_valid_amount(amount_value, second_last_col):
                                return amount_value, len(columns) - 2
                        except ValueError:
                            pass
                
                # กรณีพิเศษ: หาตัวเลขที่อยู่ก่อนคอลัมน์สุดท้ายที่เป็นตัวเลข (เช่น | | | 16,943.64 | 11)
                # ให้หาจากคอลัมน์ก่อนสุดท้ายโดยตรง (ข้ามคอลัมน์ว่าง)
                if last_col_is_digit and len(columns) >= 2:
                    # หาจากคอลัมน์ก่อนสุดท้ายไปจนถึงคอลัมน์แรก (ย้อนกลับ)
                    for col_idx in range(len(columns) - 2, -1, -1):
                        col = columns[col_idx].strip()
                        # ข้ามคอลัมน์ว่าง
                        if not col:
                            continue
                        # ข้ามถ้าเป็นตัวเลขเดียวหลักเดียว (เช่น "11", "12") ที่ไม่ใช่ตัวเลขเงิน
                        if col.isdigit() and len(col) <= 2:
                            continue
                        cleaned = clean_number(col)
                        if cleaned and re.match(r'^\d+\.?\d*$', cleaned):
                            try:
                                amount_value = float(cleaned)
                                # ตรวจสอบว่าเป็นตัวเลขเงินจริงหรือไม่
                                if amount_value >= min_value and is_valid_amount(amount_value, col):
                                    return amount_value, col_idx
                            except ValueError:
                                continue
                
                # หาจากทุกคอลัมน์ (ยกเว้นคอลัมน์สุดท้ายถ้าเป็นตัวเลข)
                # แต่ให้ลองหาจากคอลัมน์ที่ 3, 4, 5 ก่อน (เพราะตัวเลขมักอยู่ในคอลัมน์เหล่านี้)
                priority_indices = []
                if len(columns) >= 5:
                    priority_indices = [3, 4, 2, 5, 1, 0]  # ลำดับความสำคัญ: คอลัมน์ 4, 5, 3, 6, 2, 1
                elif len(columns) >= 4:
                    priority_indices = [3, 2, 1, 0]
                elif len(columns) >= 3:
                    priority_indices = [2, 1, 0]
                else:
                    priority_indices = list(range(len(columns)))
                
                # ลบ index ที่เกินจำนวนคอลัมน์
                priority_indices = [idx for idx in priority_indices if idx < len(columns)]
                
                # หาจากคอลัมน์ที่มีลำดับความสำคัญก่อน
                for col_idx in priority_indices:
                    # ข้ามคอลัมน์สุดท้ายถ้าเป็นตัวเลข
                    if last_col_is_digit and col_idx == len(columns) - 1:
                        continue
                    col = columns[col_idx].strip()
                    # ข้ามคอลัมน์ว่าง
                    if not col:
                        continue
                    # ข้ามถ้าเป็นตัวเลขลำดับ (11, 12, 13, 14) ที่อยู่ในข้อความ "11.", "12.", "13.", "14."
                    if col.isdigit() and len(col) <= 2 and int(col) in [11, 12, 13, 14]:
                        # ตรวจสอบว่าอยู่ในข้อความ "11.", "12.", "13.", "14." หรือไม่
                        if re.search(rf'\b{col}\.', row_text):
                            continue
                    cleaned = clean_number(col)
                    if cleaned and re.match(r'^\d+\.?\d*$', cleaned):
                        try:
                            amount_value = float(cleaned)
                            # ตรวจสอบว่าเป็นตัวเลขเงินจริงหรือไม่
                            if amount_value >= min_value and is_valid_amount(amount_value, col):
                                return amount_value, col_idx
                        except ValueError:
                            continue
                
                # ถ้ายังไม่พบ ให้ลองหาจากทุกคอลัมน์ (ย้อนกลับจากท้าย)
                end_idx = len(columns) - 1 if last_col_is_digit else len(columns)
                for col_idx in range(end_idx - 1, -1, -1):
                    if col_idx in priority_indices:
                        continue  # ข้ามเพราะลองไปแล้ว
                    col = columns[col_idx].strip()
                    # ข้ามคอลัมน์ว่าง
                    if not col:
                        continue
                    # ข้ามถ้าเป็นตัวเลขลำดับ (11, 12, 13, 14) ที่อยู่ในข้อความ "11.", "12.", "13.", "14."
                    if col.isdigit() and len(col) <= 2 and int(col) in [11, 12, 13, 14]:
                        # ตรวจสอบว่าอยู่ในข้อความ "11.", "12.", "13.", "14." หรือไม่
                        if re.search(rf'\b{col}\.', row_text):
                            continue
                    cleaned = clean_number(col)
                    if cleaned and re.match(r'^\d+\.?\d*$', cleaned):
                        try:
                            amount_value = float(cleaned)
                            # ตรวจสอบว่าเป็นตัวเลขเงินจริงหรือไม่
                            if amount_value >= min_value and is_valid_amount(amount_value, col):
                                return amount_value, col_idx
                        except ValueError:
                            continue
                return None, None
            
            # อ่านข้อมูลจากแต่ละแถว
            for row_idx, row in enumerate(rows, 1):
                # Split ด้วย | และเก็บคอลัมน์ทั้งหมด (รวมคอลัมน์ว่างด้วย)
                # ถ้าไม่มี | ในแถว ให้ใช้แถวทั้งหมดเป็นคอลัมน์เดียว
                if '|' in row:
                    all_cols = re.split(r'\s*\|\s*', row)
                    # เก็บคอลัมน์ทั้งหมด (รวมคอลัมน์ว่าง) เพื่อตรวจสอบคอลัมน์สุดท้าย
                    all_cols_stripped = [col.strip() for col in all_cols]
                    # กรองคอลัมน์ว่างออก (สำหรับการหาตัวเลข)
                    columns = [col.strip() for col in all_cols if col.strip()]
                else:
                    # ถ้าไม่มี | ให้ใช้แถวทั้งหมดเป็นคอลัมน์เดียว
                    all_cols_stripped = [row]
                    columns = [row]
                
                # ต้องมีอย่างน้อย 1 คอลัมน์ (ไม่จำเป็นต้องมี 2 คอลัมน์แล้ว เพราะอาจไม่มี |)
                if len(columns) < 1:
                    continue
                
                # ตรวจสอบ ☑ 11. ต้องชำระ หรือ 11. ต้องชำระ (รองรับทั้งกรณีที่มีและไม่มี ☑)
                has_checkbox_11 = re.search(r'☑\s*11\.|☑\s*11\s*\.', row)
                has_11_without_checkbox = ('11.' in row and 'ต้องชำระ' in row) or bool(re.search(r'(?:^|\s|\|)11\.(?:$|\s|\||[^\d])', row))
                has_must_pay = 'ต้องชำระ' in row
                
                # ตรวจสอบว่าคอลัมน์สุดท้าย (รวมคอลัมน์ว่าง) เป็น "11" หรือไม่
                last_col_is_11 = len(all_cols_stripped) >= 1 and all_cols_stripped[-1].strip() == '11'
                # หรือตรวจสอบจากคอลัมน์ที่กรองแล้ว
                if not last_col_is_11 and len(columns) >= 1:
                    last_col_is_11 = columns[-1].strip() == '11'
                
                if (has_checkbox_11 or has_11_without_checkbox) and has_must_pay and 'ต้องชำระ (ภ.พ.30)' not in found_keys:
                    
                    # ถ้าไม่มี | ในแถว ให้หาตัวเลขจากแถวโดยตรง
                    if '|' not in row:
                        # หาตัวเลขจากแถวโดยตรง (ใช้ regex หาตัวเลขที่มี comma และจุดทศนิยม)
                        # รองรับทั้งรูปแบบ: 16,943.64 หรือ 16943.64 หรือ 16943
                        amount_pattern = r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d{4,}(?:\.\d{2})?)'
                        matches = re.findall(amount_pattern, row)
                        if matches:
                            # ใช้ตัวเลขตัวสุดท้าย (เพราะมักจะเป็นยอดเงิน)
                            for match in reversed(matches):
                                try:
                                    amount_value = float(match.replace(',', ''))
                                    # กรองตัวเลขลำดับ (11, 12, 13, 14) ออก
                                    if amount_value in [11, 12, 13, 14]:
                                        # ตรวจสอบว่าอยู่ในข้อความ "11.", "12.", "13.", "14." หรือไม่
                                        if re.search(rf'\b{int(amount_value)}\.', row):
                                            continue
                                    # ตรวจสอบว่าเป็นตัวเลขเงินจริงหรือไม่ (มากกว่า 100 หรือมี comma/จุดทศนิยม)
                                    if amount_value >= 100 or (',' in match or '.' in match):
                                        amounts['ต้องชำระ (ภ.พ.30)'] = amount_value
                                        found_keys.add('ต้องชำระ (ภ.พ.30)')
                                        source = "☑ 11." if has_checkbox_11 else "11."
                                        logger.info(f"✅ พบต้องชำระ (ภ.พ.30) จาก {source}: {amount_value:,.2f}")
                                        break
                                except ValueError:
                                    continue
                        if 'ต้องชำระ (ภ.พ.30)' in amounts:
                            continue
                    
                    amount_value, col_idx = find_amount_in_columns(columns, row, min_value=0, last_col_is_number=last_col_is_11)
                    if amount_value is not None:
                        amounts['ต้องชำระ (ภ.พ.30)'] = amount_value
                        found_keys.add('ต้องชำระ (ภ.พ.30)')
                        source = "☑ 11." if has_checkbox_11 else "11."
                        logger.info(f"✅ พบต้องชำระ (ภ.พ.30) จาก {source}: {amount_value:,.2f}")
                        # ถ้าพบต้องชำระแล้ว ให้ข้ามการตรวจสอบชำระเกิน (เพราะจะไม่เกิดขึ้นพร้อมกัน)
                        continue
                    else:
                        logger.warning(f"⚠️ พบ 11. ต้องชำระ แต่ไม่พบตัวเลข: {row[:100]}")
                
                # ตรวจสอบ ☑ 12. ชำระเกิน หรือ 12. ชำระเกิน (รองรับทั้งกรณีที่มีและไม่มี ☑)
                has_checkbox_12 = re.search(r'☑\s*12\.|☑\s*12\s*\.', row)
                has_12_without_checkbox = ('12.' in row and 'ชำระเกิน' in row) or bool(re.search(r'(?:^|\s|\|)12\.(?:$|\s|\||[^\d])', row))
                has_over_pay = 'ชำระเกิน' in row
                
                # ตรวจสอบว่าคอลัมน์สุดท้าย (รวมคอลัมน์ว่าง) เป็น "12" หรือไม่
                # แต่ต้องมี "12." ในแถวด้วย (ไม่ใช่แค่ตัวเลข "12" เปล่าๆ)
                last_col_is_12 = False
                if (has_checkbox_12 or has_12_without_checkbox):
                    # ตรวจสอบว่าคอลัมน์สุดท้ายเป็น "12" และมี "12." ในแถว
                    if len(all_cols_stripped) >= 1 and all_cols_stripped[-1].strip() == '12':
                        last_col_is_12 = True
                    # หรือตรวจสอบจากคอลัมน์ที่กรองแล้ว
                    elif len(columns) >= 1 and columns[-1].strip() == '12':
                        last_col_is_12 = True
                
                if (has_checkbox_12 or has_12_without_checkbox) and has_over_pay and 'ชำระเกิน (ภ.พ.30)' not in found_keys:
                    
                    # ถ้าไม่มี | ในแถว ให้หาตัวเลขจากแถวโดยตรง
                    if '|' not in row:
                        # หาตัวเลขจากแถวโดยตรง (ใช้ regex หาตัวเลขที่มี comma และจุดทศนิยม)
                        # รองรับทั้งรูปแบบ: 16,943.64 หรือ 16943.64 หรือ 16943
                        amount_pattern = r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d{4,}(?:\.\d{2})?)'
                        matches = re.findall(amount_pattern, row)
                        if matches:
                            # ใช้ตัวเลขตัวสุดท้าย (เพราะมักจะเป็นยอดเงิน)
                            for match in reversed(matches):
                                try:
                                    amount_value = float(match.replace(',', ''))
                                    # กรองตัวเลขลำดับ (11, 12, 13, 14) ออก
                                    if amount_value in [11, 12, 13, 14]:
                                        # ตรวจสอบว่าอยู่ในข้อความ "11.", "12.", "13.", "14." หรือไม่
                                        if re.search(rf'\b{int(amount_value)}\.', row):
                                            continue
                                    # ตรวจสอบว่าเป็นตัวเลขเงินจริงหรือไม่ (มากกว่า 100 หรือมี comma/จุดทศนิยม)
                                    if amount_value >= 100 or (',' in match or '.' in match):
                                        amounts['ชำระเกิน (ภ.พ.30)'] = amount_value
                                        found_keys.add('ชำระเกิน (ภ.พ.30)')
                                        source = "☑ 12." if has_checkbox_12 else "12."
                                        logger.info(f"✅ พบชำระเกิน (ภ.พ.30) จาก {source}: {amount_value:,.2f}")
                                        break
                                except ValueError:
                                    continue
                        if 'ชำระเกิน (ภ.พ.30)' in amounts:
                            continue
                    
                    amount_value, col_idx = find_amount_in_columns(columns, row, min_value=0, last_col_is_number=last_col_is_12)
                    if amount_value is not None:
                        amounts['ชำระเกิน (ภ.พ.30)'] = amount_value
                        found_keys.add('ชำระเกิน (ภ.พ.30)')
                        source = "☑ 12." if has_checkbox_12 else "12."
                        logger.info(f"✅ พบชำระเกิน (ภ.พ.30) จาก {source}: {amount_value:,.2f}")
                        # ถ้ามี checkbox ☑ 12. ชำระเกิน ให้ตั้งต้องชำระเป็น 0
                        if has_checkbox_12:
                            amounts['ต้องชำระ (ภ.พ.30)'] = 0.00
                            found_keys.add('ต้องชำระ (ภ.พ.30)')
                            logger.info(f"✅ ตั้งต้องชำระ (ภ.พ.30) เป็น 0.00 เพราะพบ ☑ 12. ชำระเกิน")
                        # ถ้าพบชำระเกินแล้ว ให้ข้ามการตรวจสอบต้องชำระ (เพราะจะไม่เกิดขึ้นพร้อมกัน)
                        continue
                    else:
                        logger.warning(f"⚠️ พบ 12. ชำระเกิน แต่ไม่พบตัวเลข: {row[:100]}")
                
                # 1. ยอดขายในเดือนนี้ - อ่านจาก 1. ยอดขายในเดือนนี้ หรือ (1.1) ยอดขายแจ้งไว้ขาด
                if (re.search(r'^1\.|1\.\s|\|\s*1\.', row) and 'ยอดขายในเดือนนี้' in row) or \
                   ('(1.1)' in row and 'ยอดขายแจ้งไว้ขาด' in row):
                    if 'ยอดขายในเดือนนี้ (ภ.พ.30)' not in found_keys:
                        amount_value, col_idx = find_amount_in_columns(columns, row, min_value=0)
                        if amount_value is not None:
                            amounts['ยอดขายในเดือนนี้ (ภ.พ.30)'] = amount_value
                            found_keys.add('ยอดขายในเดือนนี้ (ภ.พ.30)')
                            logger.info(f"✅ พบยอดขายในเดือนนี้ (ภ.พ.30): {amount_value:,.2f} (คอลัมน์ {col_idx+1})")
                        else:
                            logger.warning(f"⚠️ พบข้อ 1. แต่ไม่พบตัวเลขที่ถูกต้อง: {columns}")
                
                # 4. ยอดขายที่ต้องเสียภาษี - อ่านจาก 4. ยอดขายที่ต้องเสียภาษี
                if re.search(r'^4\.|4\.\s|\|\s*4\.', row) and 'ยอดขายที่ต้องเสียภาษี' in row and 'ยอดขายที่ต้องเสียภาษี (ภ.พ.30)' not in found_keys:
                    amount_value, col_idx = find_amount_in_columns(columns, row, min_value=0)
                    if amount_value is not None:
                        amounts['ยอดขายที่ต้องเสียภาษี (ภ.พ.30)'] = amount_value
                        found_keys.add('ยอดขายที่ต้องเสียภาษี (ภ.พ.30)')
                        logger.info(f"✅ พบยอดขายที่ต้องเสียภาษี (ภ.พ.30): {amount_value:,.2f} (คอลัมน์ {col_idx+1})")
                    else:
                        logger.warning(f"⚠️ พบข้อ 4. แต่ไม่พบตัวเลขที่ถูกต้อง: {columns}")
                
                # 6. ยอดซื้อที่มีสิทธินำภาษีซื้อ - อ่านจาก 6. ยอดซื้อที่มีสิทธินำภาษีซื้อ หรือ (6.1) ยอดซื้อแจ้งไว้ขาด
                if (re.search(r'^6\.|6\.\s|\|\s*6\.', row) and 'ยอดซื้อที่มีสิทธินำภาษีซื้อ' in row) or \
                   ('(6.1)' in row and 'ยอดซื้อแจ้งไว้ขาด' in row):
                    if 'ยอดซื้อที่มีสิทธินำภาษีซื้อ (ภ.พ.30)' not in found_keys:
                        amount_value, col_idx = find_amount_in_columns(columns, row, min_value=0)
                        if amount_value is not None:
                            amounts['ยอดซื้อที่มีสิทธินำภาษีซื้อ (ภ.พ.30)'] = amount_value
                            found_keys.add('ยอดซื้อที่มีสิทธินำภาษีซื้อ (ภ.พ.30)')
                            logger.info(f"✅ พบยอดซื้อที่มีสิทธินำภาษีซื้อ (ภ.พ.30): {amount_value:,.2f} (คอลัมน์ {col_idx+1})")
                        else:
                            logger.warning(f"⚠️ พบข้อ 6. แต่ไม่พบตัวเลขที่ถูกต้อง: {columns}")
                
                # 5. ภาษีขายเดือนนี้ - อ่านจาก 5. ภาษีขายเดือนนี้
                if re.search(r'^5\.|5\.\s|\|\s*5\.', row) and 'ภาษีขายเดือนนี้' in row and 'ภาษีขายเดือนนี้ (ภ.พ.30)' not in found_keys:
                    amount_value, col_idx = find_amount_in_columns(columns, row, min_value=0)
                    if amount_value is not None:
                        amounts['ภาษีขายเดือนนี้ (ภ.พ.30)'] = amount_value
                        found_keys.add('ภาษีขายเดือนนี้ (ภ.พ.30)')
                        logger.info(f"✅ พบภาษีขายเดือนนี้ (ภ.พ.30): {amount_value:,.2f} (คอลัมน์ {col_idx+1})")
                
                # 7. ภาษีซื้อเดือนนี้ - อ่านจาก 7. ภาษีซื้อเดือนนี้ (ตามหลักฐาน)
                if re.search(r'^7\.|7\.\s|\|\s*7\.', row) and 'ภาษีซื้อเดือนนี้' in row and 'ภาษีซื้อเดือนนี้ (ภ.พ.30)' not in found_keys:
                    amount_value, col_idx = find_amount_in_columns(columns, row, min_value=0)
                    if amount_value is not None:
                        amounts['ภาษีซื้อเดือนนี้ (ภ.พ.30)'] = amount_value
                        found_keys.add('ภาษีซื้อเดือนนี้ (ภ.พ.30)')
                        logger.info(f"✅ พบภาษีซื้อเดือนนี้ (ภ.พ.30): {amount_value:,.2f} (คอลัมน์ {col_idx+1})")
                    else:
                        logger.warning(f"⚠️ พบข้อ 7. ภาษีซื้อเดือนนี้ แต่ไม่พบตัวเลขที่ถูกต้อง: {columns}")
                
                # 8. ภาษีที่ต้องชำระเดือนนี้ - อ่านจาก 8. ภาษีที่ต้องชำระเดือนนี้
                if re.search(r'^8\.|8\.\s|\|\s*8\.', row) and 'ภาษีที่ต้องชำระเดือนนี้' in row and 'ภาษีที่ต้องชำระเดือนนี้ (ภ.พ.30)' not in found_keys:
                    amount_value, col_idx = find_amount_in_columns(columns, row, min_value=0)
                    if amount_value is not None:
                        amounts['ภาษีที่ต้องชำระเดือนนี้ (ภ.พ.30)'] = amount_value
                        found_keys.add('ภาษีที่ต้องชำระเดือนนี้ (ภ.พ.30)')
                        logger.info(f"✅ พบภาษีที่ต้องชำระเดือนนี้ (ภ.พ.30): {amount_value:,.2f} (คอลัมน์ {col_idx+1})")
                    else:
                        logger.warning(f"⚠️ พบข้อ 8. แต่ไม่พบตัวเลขที่ถูกต้อง: {columns}")
                
                # 6.1. ภาษีที่ชำระเกินเดือนนี้ - อ่านจาก 9. ภาษีที่ชำระเกินเดือนนี้
                if re.search(r'^9\.|9\.\s|\|\s*9\.', row) and 'ภาษีที่ชำระเกินเดือนนี้' in row and 'ภาษีที่ชำระเกินเดือนนี้ (ภ.พ.30)' not in found_keys:
                    amount_value, col_idx = find_amount_in_columns(columns, row, min_value=0)
                    if amount_value is not None:
                        amounts['ภาษีที่ชำระเกินเดือนนี้ (ภ.พ.30)'] = amount_value
                        found_keys.add('ภาษีที่ชำระเกินเดือนนี้ (ภ.พ.30)')
                        logger.info(f"✅ พบภาษีที่ชำระเกินเดือนนี้ (ภ.พ.30): {amount_value:,.2f} (คอลัมน์ {col_idx+1})")
                    else:
                        logger.warning(f"⚠️ พบข้อ 9. แต่ไม่พบตัวเลขที่ถูกต้อง: {columns}")
                
                # 10. ภาษีที่ชำระเกินยกมา - อ่านจาก 10. ภาษีที่ชำระเกินยกมา
                if re.search(r'^10\.|10\.\s|\|\s*10\.', row) and 'ภาษีที่ชำระเกินยกมา' in row and 'ภาษีที่ชำระเกินยกมา (ภ.พ.30)' not in found_keys:
                    amount_value, col_idx = find_amount_in_columns(columns, row, min_value=0)
                    if amount_value is not None:
                        amounts['ภาษีที่ชำระเกินยกมา (ภ.พ.30)'] = amount_value
                        found_keys.add('ภาษีที่ชำระเกินยกมา (ภ.พ.30)')
                        logger.info(f"✅ พบภาษีที่ชำระเกินยกมา (ภ.พ.30): {amount_value:,.2f} (คอลัมน์ {col_idx+1})")
                    else:
                        logger.warning(f"⚠️ พบข้อ 10. แต่ไม่พบตัวเลขที่ถูกต้อง: {columns}")
                
                # 2. ยอดขายที่เสียภาษีในอัตราร้อยละ 0 - อ่านจาก 2. ลบ ยอดขายที่เสียภาษีในอัตราร้อยละ 0
                if re.search(r'^2\.|2\.\s|\|\s*2\.', row) and 'ยอดขายที่เสียภาษีในอัตราร้อยละ 0' in row and 'ยอดขายที่เสียภาษีในอัตราร้อยละ 0 (ภ.พ.30)' not in found_keys:
                    amount_value, col_idx = find_amount_in_columns(columns, row, min_value=0)
                    if amount_value is not None:
                        amounts['ยอดขายที่เสียภาษีในอัตราร้อยละ 0 (ภ.พ.30)'] = amount_value
                        found_keys.add('ยอดขายที่เสียภาษีในอัตราร้อยละ 0 (ภ.พ.30)')
                        logger.info(f"✅ พบยอดขายที่เสียภาษีในอัตราร้อยละ 0 (ภ.พ.30): {amount_value:,.2f} (คอลัมน์ {col_idx+1})")
                
                # 3. ยอดขายที่ได้รับยกเว้น - อ่านจาก 3. ลบ ยอดขายที่ได้รับยกเว้น
                if re.search(r'^3\.|3\.\s|\|\s*3\.', row) and 'ยอดขายที่ได้รับยกเว้น' in row and 'ยอดขายที่ได้รับยกเว้น (ภ.พ.30)' not in found_keys:
                    amount_value, col_idx = find_amount_in_columns(columns, row, min_value=0)
                    if amount_value is not None:
                        amounts['ยอดขายที่ได้รับยกเว้น (ภ.พ.30)'] = amount_value
                        found_keys.add('ยอดขายที่ได้รับยกเว้น (ภ.พ.30)')
                        logger.info(f"✅ พบยอดขายที่ได้รับยกเว้น (ภ.พ.30): {amount_value:,.2f} (คอลัมน์ {col_idx+1})")
                
                # 7. เงินเพิ่ม - อ่านจาก "เงินเพิ่ม" หรือ "เงินเพิ่ม (ภ.พ.30)"
                if ('เงินเพิ่ม' in row or 'เงินเพิ่ม (ภ.พ.30)' in row) and 'เงินเพิ่ม (ภ.พ.30)' not in found_keys:
                    # ข้ามถ้าเป็นส่วนของ "รวมภาษี เงินเพิ่ม และเบี้ยปรับ"
                    if 'รวมภาษี เงินเพิ่ม และเบี้ยปรับ' not in row:
                        # ถ้าไม่มี | ในแถว ให้หาตัวเลขจากแถวโดยตรง
                        if '|' not in row:
                            amount_pattern = r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d{4,}(?:\.\d{2})?)'
                            matches = re.findall(amount_pattern, row)
                            if matches:
                                for match in reversed(matches):
                                    try:
                                        amount_value = float(match.replace(',', ''))
                                        # กรองตัวเลขลำดับ (11, 12, 13, 14) ออก
                                        if amount_value in [11, 12, 13, 14]:
                                            if re.search(rf'\b{int(amount_value)}\.', row):
                                                continue
                                        # ตรวจสอบว่าเป็นตัวเลขเงินจริงหรือไม่
                                        if amount_value >= 100 or (',' in match or '.' in match):
                                            amounts['เงินเพิ่ม (ภ.พ.30)'] = amount_value
                                            found_keys.add('เงินเพิ่ม (ภ.พ.30)')
                                            logger.info(f"✅ พบเงินเพิ่ม (ภ.พ.30): {amount_value:,.2f}")
                                            break
                                    except ValueError:
                                        continue
                        else:
                            amount_value, col_idx = find_amount_in_columns(columns, row, min_value=0)
                            if amount_value is not None:
                                amounts['เงินเพิ่ม (ภ.พ.30)'] = amount_value
                                found_keys.add('เงินเพิ่ม (ภ.พ.30)')
                                logger.info(f"✅ พบเงินเพิ่ม (ภ.พ.30): {amount_value:,.2f}")
                
                # 8. เบี้ยปรับ - อ่านจาก "เบี้ยปรับ" หรือ "เบี้ยปรับ (ภ.พ.30)"
                if ('เบี้ยปรับ' in row or 'เบี้ยปรับ (ภ.พ.30)' in row) and 'เบี้ยปรับ (ภ.พ.30)' not in found_keys:
                    # ข้ามถ้าเป็นส่วนของ "รวมภาษี เงินเพิ่ม และเบี้ยปรับ"
                    if 'รวมภาษี เงินเพิ่ม และเบี้ยปรับ' not in row:
                        # ถ้าไม่มี | ในแถว ให้หาตัวเลขจากแถวโดยตรง
                        if '|' not in row:
                            amount_pattern = r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d{4,}(?:\.\d{2})?)'
                            matches = re.findall(amount_pattern, row)
                            if matches:
                                for match in reversed(matches):
                                    try:
                                        amount_value = float(match.replace(',', ''))
                                        # กรองตัวเลขลำดับ (11, 12, 13, 14) ออก
                                        if amount_value in [11, 12, 13, 14]:
                                            if re.search(rf'\b{int(amount_value)}\.', row):
                                                continue
                                        # ตรวจสอบว่าเป็นตัวเลขเงินจริงหรือไม่
                                        if amount_value >= 100 or (',' in match or '.' in match):
                                            amounts['เบี้ยปรับ (ภ.พ.30)'] = amount_value
                                            found_keys.add('เบี้ยปรับ (ภ.พ.30)')
                                            logger.info(f"✅ พบเบี้ยปรับ (ภ.พ.30): {amount_value:,.2f}")
                                            break
                                    except ValueError:
                                        continue
                        else:
                            amount_value, col_idx = find_amount_in_columns(columns, row, min_value=0)
                            if amount_value is not None:
                                amounts['เบี้ยปรับ (ภ.พ.30)'] = amount_value
                                found_keys.add('เบี้ยปรับ (ภ.พ.30)')
                                logger.info(f"✅ พบเบี้ยปรับ (ภ.พ.30): {amount_value:,.2f}")
        
        # สร้าง dictionary ที่มีข้อมูลทั้งหมด 16 ข้อ
        # (ส่วนนี้จะทำงานไม่ว่าจะมีข้อมูลจาก formatted text หรือไม่)
        result_amounts = {}
        
        # ข้อ 1-16: เก็บข้อมูลทั้งหมด
        item_keys = [
            ('1', 'ยอดขายในเดือนนี้ (ภ.พ.30)', 'ยอดขายในเดือนนี้'),
            ('2', 'ยอดขายที่เสียภาษีในอัตราร้อยละ 0 (ภ.พ.30)', 'ยอดขายที่เสียภาษีในอัตราร้อยละ 0'),
            ('3', 'ยอดขายที่ได้รับยกเว้น (ภ.พ.30)', 'ยอดขายที่ได้รับยกเว้น'),
            ('4', 'ยอดขายที่ต้องเสียภาษี (ภ.พ.30)', 'ยอดขายที่ต้องเสียภาษี'),
            ('5', 'ภาษีขายเดือนนี้ (ภ.พ.30)', 'ภาษีขายเดือนนี้'),
            ('6', 'ยอดซื้อที่มีสิทธินำภาษีซื้อ (ภ.พ.30)', 'ยอดซื้อที่มีสิทธินำภาษีซื้อ'),
            ('7', 'ภาษีซื้อเดือนนี้ (ภ.พ.30)', 'ภาษีซื้อเดือนนี้'),
            ('8', 'ภาษีที่ต้องชำระเดือนนี้ (ภ.พ.30)', 'ภาษีที่ต้องชำระเดือนนี้'),
            ('9', 'ภาษีที่ชำระเกินเดือนนี้ (ภ.พ.30)', 'ภาษีที่ชำระเกินเดือนนี้'),
            ('10', 'ภาษีที่ชำระเกินยกมา (ภ.พ.30)', 'ภาษีที่ชำระเกินยกมา'),
            ('11', 'ต้องชำระ (ภ.พ.30)', 'ต้องชำระ'),
            ('12', 'ชำระเกิน (ภ.พ.30)', 'ชำระเกิน'),
            ('13', 'เงินเพิ่ม (ภ.พ.30)', 'เงินเพิ่ม'),
            ('14', 'เบี้ยปรับ (ภ.พ.30)', 'เบี้ยปรับ'),
            ('15', 'รวมภาษี เงินเพิ่ม และเบี้ยปรับที่ต้องชำระ (ภ.พ.30)', 'รวมภาษี เงินเพิ่ม และเบี้ยปรับที่ต้องชำระ'),
            ('16', 'รวมภาษีที่ชำระเกิน หลังคำนวณเงินเพิ่มและเบี้ยปรับแล้ว (ภ.พ.30)', 'รวมภาษีที่ชำระเกิน หลังคำนวณเงินเพิ่มและเบี้ยปรับแล้ว'),
        ]
        
        # เก็บข้อมูลที่ extract ได้
        for item_num, full_key, short_key in item_keys:
            # หาค่าจาก amounts dictionary
            value = None
            for key in amounts.keys():
                if short_key in key or item_num in key:
                    value = amounts.get(key)
                    break
            
            if value is None:
                value = 0.00
            
            result_amounts[full_key] = value
        
        # การคำนวณตามสูตร (คำนวณเฉพาะเมื่อยังไม่มีค่าจาก OCR)
        item1 = result_amounts.get('ยอดขายในเดือนนี้ (ภ.พ.30)', 0.00)
        item2 = result_amounts.get('ยอดขายที่เสียภาษีในอัตราร้อยละ 0 (ภ.พ.30)', 0.00)
        item3 = result_amounts.get('ยอดขายที่ได้รับยกเว้น (ภ.พ.30)', 0.00)
        item4 = result_amounts.get('ยอดขายที่ต้องเสียภาษี (ภ.พ.30)', 0.00)
        item5 = result_amounts.get('ภาษีขายเดือนนี้ (ภ.พ.30)', 0.00)
        item6 = result_amounts.get('ยอดซื้อที่มีสิทธินำภาษีซื้อ (ภ.พ.30)', 0.00)
        item7 = result_amounts.get('ภาษีซื้อเดือนนี้ (ภ.พ.30)', 0.00)
        item8 = result_amounts.get('ภาษีที่ต้องชำระเดือนนี้ (ภ.พ.30)', 0.00)
        item9 = result_amounts.get('ภาษีที่ชำระเกินเดือนนี้ (ภ.พ.30)', 0.00)
        item10 = result_amounts.get('ภาษีที่ชำระเกินยกมา (ภ.พ.30)', 0.00)
        item11 = result_amounts.get('ต้องชำระ (ภ.พ.30)', 0.00)
        item12 = result_amounts.get('ชำระเกิน (ภ.พ.30)', 0.00)
        item13 = result_amounts.get('เงินเพิ่ม (ภ.พ.30)', 0.00)
        item14 = result_amounts.get('เบี้ยปรับ (ภ.พ.30)', 0.00)
        
        # ข้อ 4 = ข้อ 1 - ข้อ 2 - ข้อ 3 (ถ้ายังไม่มีค่าจาก OCR)
        if item4 == 0.00 and (item1 > 0 or item2 > 0 or item3 > 0):
            item4_calc = item1 - item2 - item3
            if item4_calc >= 0:
                result_amounts['ยอดขายที่ต้องเสียภาษี (ภ.พ.30)'] = item4_calc
                item4 = item4_calc
        
        # ข้อ 5 = ข้อ 4 * 7% (ถ้ายังไม่มีค่าจาก OCR)
        if item5 == 0.00 and item4 > 0:
            item5_calc = round(item4 * 0.07, 2)
            result_amounts['ภาษีขายเดือนนี้ (ภ.พ.30)'] = item5_calc
            item5 = item5_calc
        
        # ข้อ 7 = ข้อ 6 * 7% (ถ้ายังไม่มีค่าจาก OCR)
        if item7 == 0.00 and item6 > 0:
            item7_calc = round(item6 * 0.07, 2)
            result_amounts['ภาษีซื้อเดือนนี้ (ภ.พ.30)'] = item7_calc
            item7 = item7_calc
        
        # ข้อ 8 หรือ 9 = ข้อ 5 - ข้อ 7 (คำนวณใหม่เสมอ)
        diff_5_7 = item5 - item7
        
        if diff_5_7 > 0:
            # ข้อ 5 มากกว่า 7 = ข้อ 8
            result_amounts['ภาษีที่ต้องชำระเดือนนี้ (ภ.พ.30)'] = diff_5_7
            result_amounts['ภาษีที่ชำระเกินเดือนนี้ (ภ.พ.30)'] = 0.00
            item8 = diff_5_7
            item9 = 0.00
        elif diff_5_7 < 0:
            # ข้อ 7 มากกว่า 5 = ข้อ 9
            result_amounts['ภาษีที่ต้องชำระเดือนนี้ (ภ.พ.30)'] = 0.00
            result_amounts['ภาษีที่ชำระเกินเดือนนี้ (ภ.พ.30)'] = abs(diff_5_7)
            item8 = 0.00
            item9 = abs(diff_5_7)
        else:
            result_amounts['ภาษีที่ต้องชำระเดือนนี้ (ภ.พ.30)'] = 0.00
            result_amounts['ภาษีที่ชำระเกินเดือนนี้ (ภ.พ.30)'] = 0.00
            item8 = 0.00
            item9 = 0.00
        
        # ข้อ 11 หรือ 12 (คำนวณใหม่เสมอ)
        if item8 > 0:
            # ถ้ามีข้อ 8: ข้อ 8 - ข้อ 10 = ข้อ 11
            item11_calc = item8 - item10
            if item11_calc > 0:
                result_amounts['ต้องชำระ (ภ.พ.30)'] = item11_calc
                result_amounts['ชำระเกิน (ภ.พ.30)'] = 0.00
                item11 = item11_calc
                item12 = 0.00
            else:
                result_amounts['ต้องชำระ (ภ.พ.30)'] = 0.00
                result_amounts['ชำระเกิน (ภ.พ.30)'] = abs(item11_calc)
                item11 = 0.00
                item12 = abs(item11_calc)
        elif item9 > 0:
            # ถ้ามีข้อ 9: ข้อ 9 + ข้อ 10 = ข้อ 12
            item12_calc = item9 + item10
            result_amounts['ต้องชำระ (ภ.พ.30)'] = 0.00
            result_amounts['ชำระเกิน (ภ.พ.30)'] = item12_calc
            item11 = 0.00
            item12 = item12_calc
        else:
            result_amounts['ต้องชำระ (ภ.พ.30)'] = 0.00
            result_amounts['ชำระเกิน (ภ.พ.30)'] = 0.00
            item11 = 0.00
            item12 = 0.00
        
        # ข้อ 15 และ 16 (คำนวณใหม่เสมอ)
        if item11 > 0:
            # ถ้ามีข้อ 11: ข้อ 15 = ข้อ 11 + 13 + 14
            item15_calc = item11 + item13 + item14
            result_amounts['รวมภาษี เงินเพิ่ม และเบี้ยปรับที่ต้องชำระ (ภ.พ.30)'] = item15_calc
            result_amounts['รวมภาษีที่ชำระเกิน หลังคำนวณเงินเพิ่มและเบี้ยปรับแล้ว (ภ.พ.30)'] = 0.00
        elif item12 > 0:
            # ถ้ามีข้อ 12: ข้อ 15 = 13 + 14 - 12, ข้อ 16 = 12 - 13 - 14
            item15_calc = item13 + item14 - item12
            item16_calc = item12 - item13 - item14
            
            if item15_calc > 0:
                result_amounts['รวมภาษี เงินเพิ่ม และเบี้ยปรับที่ต้องชำระ (ภ.พ.30)'] = item15_calc
                result_amounts['รวมภาษีที่ชำระเกิน หลังคำนวณเงินเพิ่มและเบี้ยปรับแล้ว (ภ.พ.30)'] = 0.00
            else:
                result_amounts['รวมภาษี เงินเพิ่ม และเบี้ยปรับที่ต้องชำระ (ภ.พ.30)'] = 0.00
                result_amounts['รวมภาษีที่ชำระเกิน หลังคำนวณเงินเพิ่มและเบี้ยปรับแล้ว (ภ.พ.30)'] = abs(item16_calc) if item16_calc < 0 else item16_calc
        else:
            result_amounts['รวมภาษี เงินเพิ่ม และเบี้ยปรับที่ต้องชำระ (ภ.พ.30)'] = 0.00
            result_amounts['รวมภาษีที่ชำระเกิน หลังคำนวณเงินเพิ่มและเบี้ยปรับแล้ว (ภ.พ.30)'] = 0.00
        
        # Log สรุปผลลัพธ์
        logger.info(f"✅ สรุปผลการ parse ภ.พ.30:")
        logger.info(f"   ต้องชำระ={result_amounts.get('ต้องชำระ (ภ.พ.30)', 0.00):,.2f}, ชำระเกิน={result_amounts.get('ชำระเกิน (ภ.พ.30)', 0.00):,.2f}")
        logger.info(f"   เงินเพิ่ม={result_amounts.get('เงินเพิ่ม (ภ.พ.30)', 0.00):,.2f}, เบี้ยปรับ={result_amounts.get('เบี้ยปรับ (ภ.พ.30)', 0.00):,.2f}")
        
        return result_amounts
    
    def _parse_pp36(self, text: str, formatted_text: str) -> Dict[str, Any]:
        """Parse ข้อมูล ภ.พ.36"""
        data = self._parse_basic_info(text, formatted_text)
        data['tax_form_type'] = 'ภ.พ.36'
        
        # Parse ข้อมูลเฉพาะ ภ.พ.36 (ชื่อบริษัท, เลขประจำตัวผู้เสียภาษีอากร)
        # ใช้ทั้ง text (raw) และ formatted_text เพื่อให้ครอบคลุมทุกรูปแบบ
        
        # 1. หาชื่อบริษัท (สำหรับ ภ.พ.36)
        if not data.get('company_name'):
            pp36_company_patterns = [
                # รูปแบบ: **ชื่อผู้นำส่งภาษีมูลค่าเพิ่ม:** บริษัท... (รองรับ **)
                r'(?:[*]+\s*)?ชื่อผู้นำส่งภาษีมูลค่าเพิ่ม[^\n]*?[:：]\s*(?:=+\s*)?(?:[*]+\s*)?(บริษัท\s+[^\n]+?จำกัด(?:\s+(?:มหาชน|\(มหาชน\)))?)',
                # รูปแบบ: ชื่อผู้นำส่งภาษีมูลค่าเพิ่ม: บริษัท...
                r'ชื่อผู้นำส่งภาษีมูลค่าเพิ่ม[^\n]*?[:：]\s*(?:=+\s*)?(?:[*]+\s*)?(บริษัท\s+[^\n]+?จำกัด(?:\s+(?:มหาชน|\(มหาชน\)))?)',
                # รูปแบบ: ชื่อผู้นำส่งภาษีมูลค่าเพิ่ม\nบริษัท...
                r'ชื่อผู้นำส่งภาษีมูลค่าเพิ่ม[^\n]*?\n\s*(?:=+\s*)?(?:[*]+\s*)?(บริษัท\s+[^\n]+?จำกัด(?:\s+(?:มหาชน|\(มหาชน\)))?)',
                # รูปแบบ: === ชื่อผู้นำส่งภาษีมูลค่าเพิ่ม: === บริษัท... ===
                r'=+\s*ชื่อผู้นำส่งภาษีมูลค่าเพิ่ม[^\n]*?[:：]\s*=+\s*(บริษัท\s+[^\n]+?จำกัด(?:\s+(?:มหาชน|\(มหาชน\)))?)\s*=+',
                # รูปแบบ: ชื่อผู้ประกอบการ บริษัท...
                r'ชื่อผู้ประกอบการ[^\n]*?[:：]\s*(?:=+\s*)?(?:[*]+\s*)?(บริษัท\s+[^\n]+?จำกัด(?:\s+(?:มหาชน|\(มหาชน\)))?)',
                # รูปแบบ: ชื่อผู้ประกอบการ\nบริษัท...
                r'ชื่อผู้ประกอบการ[^\n]*?\n\s*(?:=+\s*)?(?:[*]+\s*)?(บริษัท\s+[^\n]+?จำกัด(?:\s+(?:มหาชน|\(มหาชน\)))?)',
                # รูปแบบ: ชื่อผู้ประกอบการ (สำหรับผู้ประกอบการจดทะเบียนภาษีมูลค่าเพิ่ม)
                r'ชื่อผู้ประกอบการ[^\n]*?\([^\n]*?\)[^\n]*?[:：]\s*(?:=+\s*)?(?:[*]+\s*)?(บริษัท\s+[^\n]+?จำกัด(?:\s+(?:มหาชน|\(มหาชน\)))?)',
                # รูปแบบ: หาชื่อบริษัทโดยตรง (รูปแบบทั่วไป)
                r'(บริษัท\s+[ก-ฮa-zA-Z0-9\s\.\(\)]+?จำกัด(?:\s+(?:มหาชน|\(มหาชน\)))?)',
            ]
            # ลองหาใน raw text ก่อน
            for pattern in pp36_company_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    company_name = match.group(1).strip()
                    # ทำความสะอาดชื่อบริษัท
                    company_name = re.sub(r'\s+', ' ', company_name)  # ลบช่องว่างซ้ำ
                    company_name = re.sub(r'[=*]+', '', company_name)  # ลบ = และ *
                    company_name = company_name.strip()
                    if company_name and 'บริษัท' in company_name:
                        data['company_name'] = company_name
                        logger.info(f"✅ [ภ.พ.36] พบชื่อบริษัท: {company_name}")
                        break
            
            # ถ้ายังไม่พบ ลองหาใน formatted_text
            if not data.get('company_name'):
                for pattern in pp36_company_patterns:
                    match = re.search(pattern, formatted_text, re.IGNORECASE | re.MULTILINE)
                    if match:
                        company_name = match.group(1).strip()
                        company_name = re.sub(r'\s+', ' ', company_name)
                        company_name = re.sub(r'[=*]+', '', company_name)
                        company_name = company_name.strip()
                        if company_name and 'บริษัท' in company_name:
                            data['company_name'] = company_name
                            logger.info(f"✅ [ภ.พ.36] พบชื่อบริษัท (จาก formatted_text): {company_name}")
                            break
        
        # 2. หาเลขประจำตัวผู้เสียภาษีอากร (สำหรับ ภ.พ.36)
        if not data.get('tax_id'):
            pp36_tax_id_patterns = [
                # รูปแบบ: เลขประจำตัวผู้เสียภาษีอากร (สำหรับผู้ประกอบการจดทะเบียนภาษีมูลค่าเพิ่ม)
                r'เลขประจำตัวผู้เสียภาษีอากร[^\n]*?\([^\n]*?\)[^\n]*?[:：]\s*(?:=+\s*)?(?:[*]+\s*)?([0-9\s]{13,30})',
                # รูปแบบ: เลขประจำตัวผู้เสียภาษีอากร: 0 1 0 5 5 5 3 1 1 4 4 3 7
                r'เลขประจำตัวผู้เสียภาษีอากร[^\n]*?[:：]\s*(?:=+\s*)?(?:[*]+\s*)?([0-9\s]{13,30})',
                # รูปแบบ: เลขประจำตัวผู้เสียภาษีอากร\n0 1 0 5 5 5 3 1 1 4 4 3 7
                r'เลขประจำตัวผู้เสียภาษีอากร[^\n]*?\n\s*(?:=+\s*)?(?:[*]+\s*)?([0-9\s]{13,30})',
                # รูปแบบ: เลขประจำตัวผู้เสียภาษีอากร (สำหรับผู้ประกอบการจดทะเบียนภาษีมูลค่าเพิ่ม)\n0 1 0 5 5 5 3 1 1 4 4 3 7
                r'เลขประจำตัวผู้เสียภาษีอากร[^\n]*?\([^\n]*?\)[^\n]*?\n\s*(?:=+\s*)?(?:[*]+\s*)?([0-9\s]{13,30})',
            ]
            # ลองหาใน raw text ก่อน
            for pattern in pp36_tax_id_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    tax_id_raw = match.group(1).strip()
                    # ลบช่องว่างและ dash และ = และ *
                    tax_id_clean = re.sub(r'[\s\-=*]+', '', tax_id_raw)
                    # ตรวจสอบว่าเป็นตัวเลข 13 หลัก
                    if tax_id_clean.isdigit() and len(tax_id_clean) == 13:
                        # Format เป็น x-xxxx-xxxxx-xx-x
                        tax_id_formatted = f"{tax_id_clean[0]}-{tax_id_clean[1:5]}-{tax_id_clean[5:10]}-{tax_id_clean[10:12]}-{tax_id_clean[12]}"
                        data['tax_id'] = tax_id_formatted
                        logger.info(f"✅ [ภ.พ.36] พบเลขประจำตัวผู้เสียภาษีอากร: {tax_id_formatted}")
                        break
            
            # ถ้ายังไม่พบ ลองหาใน formatted_text
            if not data.get('tax_id'):
                for pattern in pp36_tax_id_patterns:
                    match = re.search(pattern, formatted_text, re.IGNORECASE | re.MULTILINE)
                    if match:
                        tax_id_raw = match.group(1).strip()
                        tax_id_clean = re.sub(r'[\s\-=*]+', '', tax_id_raw)
                        if tax_id_clean.isdigit() and len(tax_id_clean) == 13:
                            tax_id_formatted = f"{tax_id_clean[0]}-{tax_id_clean[1:5]}-{tax_id_clean[5:10]}-{tax_id_clean[10:12]}-{tax_id_clean[12]}"
                            data['tax_id'] = tax_id_formatted
                            logger.info(f"✅ [ภ.พ.36] พบเลขประจำตัวผู้เสียภาษีอากร (จาก formatted_text): {tax_id_formatted}")
                            break
        
        # 3. หาเดือนและปี (สำหรับ ภ.พ.36)
        # รูปแบบ: วัน เดือน ปี ที่จ่ายเงิน === วันที่ 01 เดือน ตุลาคม พ.ศ. 2568 ===
        if not data.get('filing_period', {}).get('month'):
            pp36_month_patterns = [
                # รูปแบบ: วันที่ XX เดือน ตุลาคม พ.ศ. XXXX
                r'วันที่\s+\d+\s+เดือน\s+([มกกุมภาพันธ์มีนาคมเมษายนพฤษภาคมมิถุนายนกรกฎาคมสิงหาคมกันยายนตุลาคมพฤศจิกายนธันวาคม]+)',
                # รูปแบบ: เดือน ตุลาคม พ.ศ. XXXX
                r'เดือน\s+([มกกุมภาพันธ์มีนาคมเมษายนพฤษภาคมมิถุนายนกรกฎาคมสิงหาคมกันยายนตุลาคมพฤศจิกายนธันวาคม]+)',
                # รูปแบบ: === วันที่ XX เดือน ตุลาคม พ.ศ. XXXX ===
                r'=+\s*วันที่\s+\d+\s+เดือน\s+([มกกุมภาพันธ์มีนาคมเมษายนพฤษภาคมมิถุนายนกรกฎาคมสิงหาคมกันยายนตุลาคมพฤศจิกายนธันวาคม]+)',
            ]
            # ลองหาใน raw text ก่อน
            for pattern in pp36_month_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    month = match.group(1).strip()
                    if month:
                        if not data.get('filing_period'):
                            data['filing_period'] = {'month': None, 'year': None}
                        data['filing_period']['month'] = month
                        logger.info(f"✅ [ภ.พ.36] พบเดือน: {month}")
                        break
            
            # ถ้ายังไม่พบ ลองหาใน formatted_text
            if not data.get('filing_period', {}).get('month'):
                for pattern in pp36_month_patterns:
                    match = re.search(pattern, formatted_text, re.IGNORECASE | re.MULTILINE)
                    if match:
                        month = match.group(1).strip()
                        if month:
                            if not data.get('filing_period'):
                                data['filing_period'] = {'month': None, 'year': None}
                            data['filing_period']['month'] = month
                            logger.info(f"✅ [ภ.พ.36] พบเดือน (จาก formatted_text): {month}")
                            break
        
        # Parse ข้อมูลเฉพาะ ภ.พ.36 (ใช้ formatted_text แทน text เพื่อให้ได้ข้อมูลที่ถูก format แล้ว)
        amounts = self._parse_pp36_amounts(formatted_text if formatted_text else text)
        data['amounts'] = amounts
        
        return data
    
    def _parse_pp36_amounts(self, text: str) -> Dict[str, float]:
        """Parse ยอดเงินจาก ภ.พ.36"""
        amounts = {}
        
        logger.info(f"🔍 [DEBUG] เริ่ม parse ยอดเงิน ภ.พ.36")
        logger.info(f"🔍 [DEBUG] ข้อความที่ค้นหา (500 ตัวอักษรแรก): {text[:500]}")
        
        # รูปแบบที่พบในข้อมูลจริง:
        # 1. "2. จำนวนเงินภาษีมูลค่าเพิ่มที่ต้องนำส่ง 49 67" (ไม่มี "(ตัวอักษร)", ไม่มีเลข 2 ต่อท้าย)
        # 2. "2. จำนวนเงินภาษีมูลค่าเพิ่มที่ต้องนำส่ง (ตัวอักษร) 1,967 59 2" (มี "(ตัวอักษร)", มีเลข 2 ต่อท้าย)
        # 3. "2. จำนวนเงินภาษีมูลค่าเพิ่มที่ต้องนำส่ง 49.67" (มีจุดทศนิยม)
        
        # Pattern หลัก: รองรับรูปแบบ "2. จำนวนเงินภาษีมูลค่าเพิ่มที่ต้องนำส่ง 49 67" (ไม่มี "(ตัวอักษร)", ไม่มีเลข 2 ต่อท้าย)
        patterns = [
            # Pattern 1: "2. จำนวนเงินภาษีมูลค่าเพิ่มที่ต้องนำส่ง 49 67" (มีช่องว่างระหว่างตัวเลข)
            r'2\.\s*จำนวนเงินภาษีมูลค่าเพิ่มที่ต้องนำส่ง[^\d]*([\d,]+)\s+(\d{2})(?:\s|$)',
            r'2\s*\.\s*จำนวนเงินภาษีมูลค่าเพิ่มที่ต้องนำส่ง[^\d]*([\d,]+)\s+(\d{2})(?:\s|$)',
            # Pattern 2: "2. จำนวนเงินภาษีมูลค่าเพิ่มที่ต้องนำส่ง 49.67" (มีจุดทศนิยม)
            r'2\.\s*จำนวนเงินภาษีมูลค่าเพิ่มที่ต้องนำส่ง[^\d]*([\d,]+\.\d{2})(?:\s|$)',
            r'2\s*\.\s*จำนวนเงินภาษีมูลค่าเพิ่มที่ต้องนำส่ง[^\d]*([\d,]+\.\d{2})(?:\s|$)',
            # Pattern 3: "2. จำนวนเงินภาษีมูลค่าเพิ่มที่ต้องนำส่ง (ตัวอักษร) 1,967 59 2" (มี "(ตัวอักษร)", มีเลข 2 ต่อท้าย)
            r'2\.\s*จำนวนเงินภาษีมูลค่าเพิ่มที่ต้องนำส่ง\s*\(ตัวอักษร\)\s*([\d,\s]+)\s*(\d)\s*$',
            r'2\.\s*จำนวนเงินภาษีมูลค่าเพิ่มที่ต้องนำส่ง\s*\(ตัวอักษร\)\s*([\d,\s]+)\s*(\d)',
            # Pattern 4: ไม่มี "2." ข้างหน้า
            r'จำนวนเงินภาษีมูลค่าเพิ่มที่ต้องนำส่ง[^\d]*([\d,]+)\s+(\d{2})(?:\s|$)',
            r'จำนวนเงินภาษีมูลค่าเพิ่มที่ต้องนำส่ง[^\d]*([\d,]+\.\d{2})(?:\s|$)',
        ]
        
        for pattern_idx, pattern in enumerate(patterns):
            logger.info(f"🔍 [DEBUG] ลองใช้ pattern {pattern_idx+1}: {pattern[:80]}...")
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if match:
                logger.info(f"🔍 [DEBUG] Pattern {pattern_idx+1} match ได้: {match.groups()}")
                
                # กรณีที่มี 2 groups (main_part และ decimal_part)
                if len(match.groups()) == 2:
                    amount_part = match.group(1).strip()
                    decimal_part = match.group(2).strip()
                    
                    logger.info(f"🔍 [DEBUG] พบ pattern: amount_part='{amount_part}', decimal_part='{decimal_part}'")
                    
                    # ลบช่องว่างและ comma จากส่วนหลัก
                    amount_clean = re.sub(r'\s+', '', amount_part)
                    amount_clean = amount_clean.replace(',', '')
                    
                    # ตรวจสอบว่า decimal_part เป็นเลข 2 หลักหรือไม่ (ถ้าเป็น 1 หลักอาจเป็นเลขท้ายที่ต้องลบ)
                    if decimal_part.isdigit():
                        if len(decimal_part) == 2:
                            # decimal_part เป็น 2 หลัก (เช่น "67") -> ใช้เป็นทศนิยม
                            amount_str = f"{amount_clean}.{decimal_part}"
                        elif len(decimal_part) == 1 and decimal_part == '2':
                            # decimal_part เป็น "2" (เลขท้ายที่ต้องลบ) -> แยก 2 หลักท้ายของ amount_clean เป็นทศนิยม
                            if len(amount_clean) >= 2:
                                main_part = amount_clean[:-2]
                                decimal_part_final = amount_clean[-2:]
                                amount_str = f"{main_part}.{decimal_part_final}"
                            else:
                                logger.info(f"🔍 [DEBUG] amount_clean สั้นเกินไป: '{amount_clean}' ข้าม")
                                continue
                        else:
                            logger.info(f"🔍 [DEBUG] decimal_part ไม่ถูกต้อง: '{decimal_part}' ข้าม")
                            continue
                        
                        try:
                            amount_value = float(amount_str)
                            if amount_value >= 0:  # อนุญาตให้เป็น 0 ได้
                                amounts['จำนวนเงินภาษีมูลค่าเพิ่มที่ต้องนำส่ง (ภ.พ.36)'] = amount_value
                                logger.info(f"✅ [Pattern {pattern_idx+1}] พบจำนวนเงินภาษีมูลค่าเพิ่มที่ต้องนำส่ง (ภ.พ.36): {amount_value:,.2f}")
                                return amounts
                        except ValueError as e:
                            logger.warning(f"⚠️ ไม่สามารถแปลง '{amount_str}' เป็นตัวเลขได้: {e}")
                            continue
                
                # กรณีที่มี 1 group (มีจุดทศนิยมอยู่แล้ว)
                elif len(match.groups()) == 1:
                    amount_str = match.group(1).strip()
                    logger.info(f"🔍 [DEBUG] พบ pattern (มีจุดทศนิยม): amount_str='{amount_str}'")
                    
                    # ลบ comma
                    amount_clean = amount_str.replace(',', '')
                    
                    try:
                        amount_value = float(amount_clean)
                        if amount_value >= 0:  # อนุญาตให้เป็น 0 ได้
                            amounts['จำนวนเงินภาษีมูลค่าเพิ่มที่ต้องนำส่ง (ภ.พ.36)'] = amount_value
                            logger.info(f"✅ [Pattern {pattern_idx+1}] พบจำนวนเงินภาษีมูลค่าเพิ่มที่ต้องนำส่ง (ภ.พ.36): {amount_value:,.2f}")
                            return amounts
                    except ValueError as e:
                        logger.warning(f"⚠️ ไม่สามารถแปลง '{amount_clean}' เป็นตัวเลขได้: {e}")
                        continue
        
        # Fallback: ลองหาจากรูปแบบอื่นๆ (ไม่ต้องมี "2." หรือ "(ตัวอักษร)")
        logger.info(f"🔍 [DEBUG] ลองหาแบบ fallback...")
        
        # Pattern fallback: หา "จำนวนเงินภาษีมูลค่าเพิ่มที่ต้องนำส่ง" ตามด้วยตัวเลข
        fallback_patterns = [
            # รูปแบบ: "จำนวนเงินภาษีมูลค่าเพิ่มที่ต้องนำส่ง 49 67"
            r'จำนวนเงินภาษีมูลค่าเพิ่มที่ต้องนำส่ง[^\d]*([\d,]+)\s+(\d{2})(?:\s|$)',
            # รูปแบบ: "จำนวนเงินภาษีมูลค่าเพิ่มที่ต้องนำส่ง 49.67"
            r'จำนวนเงินภาษีมูลค่าเพิ่มที่ต้องนำส่ง[^\d]*([\d,]+\.\d{2})(?:\s|$)',
            # รูปแบบ: "2. จำนวนเงิน..." (ไม่มี "(ตัวอักษร)")
            r'2\.\s*จำนวนเงิน[^\d]*([\d,]+)\s+(\d{2})(?:\s|$)',
            r'2\.\s*จำนวนเงิน[^\d]*([\d,]+\.\d{2})(?:\s|$)',
        ]
        
        for pattern_idx, pattern in enumerate(fallback_patterns):
            logger.info(f"🔍 [DEBUG] [Fallback] ลองใช้ pattern {pattern_idx+1}: {pattern[:80]}...")
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if match:
                logger.info(f"🔍 [DEBUG] [Fallback] Pattern {pattern_idx+1} match ได้: {match.groups()}")
                
                if len(match.groups()) == 2:
                    amount_part = match.group(1).strip()
                    decimal_part = match.group(2).strip()
                    
                    logger.info(f"🔍 [DEBUG] [Fallback] พบ pattern: amount_part='{amount_part}', decimal_part='{decimal_part}'")
                    
                    # ลบช่องว่างและ comma
                    amount_clean = re.sub(r'\s+', '', amount_part)
                    amount_clean = amount_clean.replace(',', '')
                    
                    if decimal_part.isdigit() and len(decimal_part) == 2:
                        amount_str = f"{amount_clean}.{decimal_part}"
                        try:
                            amount_value = float(amount_str)
                            if amount_value >= 0:
                                amounts['จำนวนเงินภาษีมูลค่าเพิ่มที่ต้องนำส่ง (ภ.พ.36)'] = amount_value
                                logger.info(f"✅ [Fallback Pattern {pattern_idx+1}] พบจำนวนเงินภาษีมูลค่าเพิ่มที่ต้องนำส่ง (ภ.พ.36): {amount_value:,.2f}")
                                return amounts
                        except ValueError:
                            continue
                
                elif len(match.groups()) == 1:
                    amount_str = match.group(1).strip()
                    logger.info(f"🔍 [DEBUG] [Fallback] พบ pattern (มีจุดทศนิยม): amount_str='{amount_str}'")
                    
                    amount_clean = amount_str.replace(',', '')
                    try:
                        amount_value = float(amount_clean)
                        if amount_value >= 0:
                            amounts['จำนวนเงินภาษีมูลค่าเพิ่มที่ต้องนำส่ง (ภ.พ.36)'] = amount_value
                            logger.info(f"✅ [Fallback Pattern {pattern_idx+1}] พบจำนวนเงินภาษีมูลค่าเพิ่มที่ต้องนำส่ง (ภ.พ.36): {amount_value:,.2f}")
                            return amounts
                    except ValueError:
                        continue
        
        logger.warning(f"⚠️ [DEBUG] ไม่พบยอดเงิน 'จำนวนเงินภาษีมูลค่าเพิ่มที่ต้องนำส่ง' ใน ภ.พ.36")
        logger.info(f"🔍 [DEBUG] ข้อความที่ค้นหา (500 ตัวอักษรสุดท้าย): ...{text[-500:]}")
        return amounts
    
    def _parse_pnd54(self, text: str, formatted_text: str) -> Dict[str, Any]:
        """Parse ข้อมูล ภ.ง.ด.54"""
        data = self._parse_basic_info(text, formatted_text)
        data['tax_form_type'] = 'ภ.ง.ด.54'
        
        # Parse ข้อมูลเฉพาะ ภ.ง.ด.54 (ชื่อบริษัท, เลขประจำตัวผู้เสียภาษีอากร, ที่ตั้งสำนักงาน)
        # ใช้ทั้ง text (raw) และ formatted_text เพื่อให้ครอบคลุมทุกรูปแบบ
        
        # 1. หาชื่อบริษัท (สำหรับ ภ.ง.ด.54)
        if not data.get('company_name'):
            pnd54_company_patterns = [
                # รูปแบบ raw text: **ชื่อผู้นำส่งภาษี:** บริษัท ไอสาม เกทเวย์ จำกัด
                r'ชื่อผู้นำส่งภาษี[^\n]*?[:：]\s*(?:[*]+\s*)?(บริษัท\s+[^\n]+?จำกัด(?:\s+(?:มหาชน|\(มหาชน\)))?)',
                # รูปแบบ formatted: === ชื่อผู้นำส่งภาษี: === = บริษัท ไอสาม เกทเวย์ จำกัด ===
                r'ชื่อผู้นำส่งภาษี[^\n]*?[:：]\s*(?:=+\s*)?(?:=\s*)?(บริษัท\s+[^\n]+?จำกัด(?:\s+(?:มหาชน|\(มหาชน\)))?)',
                # รูปแบบ: ชื่อผู้นำส่งภาษี: === = บริษัท ไอสาม เกทเวย์ จำกัด
                r'ชื่อผู้นำส่งภาษี[^\n]*?[:：]\s*=+\s*=\s*(บริษัท\s+[^\n]+?จำกัด(?:\s+(?:มหาชน|\(มหาชน\)))?)',
                # รูปแบบ: ชื่อผู้นำส่งภาษี สาขาที่ X บริษัท...
                r'ชื่อผู้นำส่งภาษี[^\n]*?สาขาที่[^\n]*?[:：]\s*(?:=+\s*)?(?:[*]+\s*)?(บริษัท\s+[^\n]+?จำกัด(?:\s+(?:มหาชน|\(มหาชน\)))?)',
            ]
            # ลองหาใน raw text ก่อน
            for pattern in pnd54_company_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    company_name = match.group(1).strip()
                    # ทำความสะอาดชื่อบริษัท
                    company_name = re.sub(r'\s+', ' ', company_name)  # ลบช่องว่างซ้ำ
                    company_name = re.sub(r'[=*]+', '', company_name)  # ลบ = และ *
                    company_name = company_name.strip()
                    if company_name and 'บริษัท' in company_name:
                        data['company_name'] = company_name
                        logger.info(f"✅ [ภ.ง.ด.54] พบชื่อบริษัท: {company_name}")
                        break
            
            # ถ้ายังไม่พบ ลองหาใน formatted_text
            if not data.get('company_name'):
                for pattern in pnd54_company_patterns:
                    match = re.search(pattern, formatted_text, re.IGNORECASE | re.MULTILINE)
                    if match:
                        company_name = match.group(1).strip()
                        company_name = re.sub(r'\s+', ' ', company_name)
                        company_name = re.sub(r'[=*]+', '', company_name)
                        company_name = company_name.strip()
                        if company_name and 'บริษัท' in company_name:
                            data['company_name'] = company_name
                            logger.info(f"✅ [ภ.ง.ด.54] พบชื่อบริษัท (จาก formatted_text): {company_name}")
                            break
        
        # 2. หาเลขประจำตัวผู้เสียภาษีอากร (สำหรับ ภ.ง.ด.54)
        if not data.get('tax_id'):
            pnd54_tax_id_patterns = [
                # รูปแบบ raw text: **เลขประจำตัวผู้เสียภาษีอากร:** 0 1 0 5 5 5 3 1 1 4 4 3 7
                r'เลขประจำตัวผู้เสียภาษีอากร[^\n]*?[:：]\s*(?:[*]+\s*)?([0-9\s]{13,30})',
                # รูปแบบ formatted: === เลขประจำตัวผู้เสียภาษีอากร: === 0 1 0 5 5 5 3 1 1 4 4 3 7 ===
                r'เลขประจำตัวผู้เสียภาษีอากร[^\n]*?[:：]\s*(?:=+\s*)?([0-9\s]{13,30})',
                # รูปแบบ: เลขประจำตัวผู้เสียภาษีอากร: === = 0 1 0 5 5 5 3 1 1 4 4 3 7
                r'เลขประจำตัวผู้เสียภาษีอากร[^\n]*?[:：]\s*=+\s*=\s*([0-9\s]{13,30})',
                # รูปแบบ: เลขประจำตัวผู้เสียภาษีอากร (ของผู้มีหน้าที่หักภาษี ณ ที่จ่าย): 0 1 0 5 5 5 3 1 1 4 4 3 7
                r'เลขประจำตัวผู้เสียภาษีอากร[^\n]*?[:：]\s*(?:=+\s*)?(?:[*]+\s*)?([0-9\s\-]{13,30})',
            ]
            # ลองหาใน raw text ก่อน
            for pattern in pnd54_tax_id_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    tax_id_raw = match.group(1).strip()
                    # ลบช่องว่างและ dash และ = และ *
                    tax_id_clean = re.sub(r'[\s\-=*]+', '', tax_id_raw)
                    # ตรวจสอบว่าเป็นตัวเลข 13 หลัก
                    if tax_id_clean.isdigit() and len(tax_id_clean) == 13:
                        data['tax_id'] = tax_id_clean
                        logger.info(f"✅ [ภ.ง.ด.54] พบเลขประจำตัวผู้เสียภาษีอากร: {tax_id_clean}")
                        break
            
            # ถ้ายังไม่พบ ลองหาใน formatted_text
            if not data.get('tax_id'):
                for pattern in pnd54_tax_id_patterns:
                    match = re.search(pattern, formatted_text, re.IGNORECASE | re.MULTILINE)
                    if match:
                        tax_id_raw = match.group(1).strip()
                        tax_id_clean = re.sub(r'[\s\-=*]+', '', tax_id_raw)
                        if tax_id_clean.isdigit() and len(tax_id_clean) == 13:
                            data['tax_id'] = tax_id_clean
                            logger.info(f"✅ [ภ.ง.ด.54] พบเลขประจำตัวผู้เสียภาษีอากร (จาก formatted_text): {tax_id_clean}")
                            break
        
        # 3. หาที่ตั้งสำนักงาน (สำหรับ ภ.ง.ด.54)
        pnd54_address_patterns = [
            # รูปแบบ raw text: **ที่ตั้งสำนักงาน : อาคาร** ไอทีเอฟ-ทาวเวอร์ ... **รหัสไปรษณีย์** 1 0 5 0 0
            r'ที่ตั้งสำนักงาน[^\n]*?[:：]\s*(?:[*]+\s*)?(?:อาคาร[^\n]+?รหัสไปรษณีย์[^\n]+?[0-9\s]{5})',
            # รูปแบบ formatted: ที่ตั้งสำนักงาน : อาคาร === ไอทีเอฟ-ทาวเวอร์ === ... รหัสไปรษณีย์ === 1 0 5 0 0
            r'ที่ตั้งสำนักงาน[^\n]*?[:：]\s*(?:=+\s*)?(อาคาร[^\n]+?รหัสไปรษณีย์[^\n]+?[0-9\s]{5})',
            # รูปแบบ: ที่ตั้งสำนักงาน : อาคาร === ... === รหัสไปรษณีย์ === 1 0 5 0 0
            r'ที่ตั้งสำนักงาน[^\n]*?[:：]\s*(?:=+\s*)?(อาคาร[^\n]+?รหัสไปรษณีย์\s+[0-9\s]{5})',
        ]
        for pattern in pnd54_address_patterns:
            # ลองหาใน raw text ก่อน
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if match:
                address_raw = match.group(1).strip() if match.lastindex else match.group(0).strip()
                # ทำความสะอาดที่อยู่
                address_clean = re.sub(r'\s+', ' ', address_raw)  # ลบช่องว่างซ้ำ
                address_clean = re.sub(r'[=*]+', '', address_clean)  # ลบ = และ *
                address_clean = re.sub(r'\s*[:：]\s*', ' ', address_clean)  # ลบ : และช่องว่างรอบๆ
                address_clean = address_clean.strip()
                if address_clean:
                    data['office_address'] = address_clean
                    logger.info(f"✅ [ภ.ง.ด.54] พบที่ตั้งสำนักงาน: {address_clean[:50]}...")
                    break
            
            # ถ้ายังไม่พบ ลองหาใน formatted_text
            if not data.get('office_address'):
                match = re.search(pattern, formatted_text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                if match:
                    address_raw = match.group(1).strip() if match.lastindex else match.group(0).strip()
                    address_clean = re.sub(r'\s+', ' ', address_raw)
                    address_clean = re.sub(r'[=*]+', '', address_clean)
                    address_clean = re.sub(r'\s*[:：]\s*', ' ', address_clean)
                    address_clean = address_clean.strip()
                    if address_clean:
                        data['office_address'] = address_clean
                        logger.info(f"✅ [ภ.ง.ด.54] พบที่ตั้งสำนักงาน (จาก formatted_text): {address_clean[:50]}...")
                        break
        
        # Parse ข้อมูลเฉพาะ ภ.ง.ด.54 (ใช้ formatted_text แทน text เพื่อให้ได้ข้อมูลที่ถูก format แล้ว)
        amounts = self._parse_pnd54_amounts(formatted_text if formatted_text else text)
        data['amounts'] = amounts
        
        return data
    
    def _parse_pnd54_amounts(self, text: str) -> Dict[str, float]:
        """Parse ยอดเงินจาก ภ.ง.ด.54"""
        amounts = {}
        
        logger.info(f"🔍 [DEBUG] เริ่ม parse ยอดเงิน ภ.ง.ด.54")
        logger.info(f"🔍 [DEBUG] ข้อความที่ค้นหา (500 ตัวอักษรแรก): {text[:500]}")
        
        # รูปแบบที่พบในข้อมูลจริง:
        # 1. "(2) เงินภาษีที่นำส่งในอัตรา ร้อยละ 5 34.21"
        # 2. "(4) รวมเป็นเงินทั้งสิ้น 34.21"
        # 3. "รวมเป็นเงินทั้งสิ้น 34.21"
        # 4. รูปแบบที่มีช่องว่างระหว่างตัวเลข: "34 21" -> "34.21"
        
        # Pattern หลัก - หาจาก "(2) เงินภาษีที่นำส่งในอัตรา ร้อยละ 5"
        patterns = [
            # Pattern 1: "(2) เงินภาษีที่นำส่งในอัตรา ร้อยละ 5 34.21" (มีจุดทศนิยม)
            r'\(2\)\s*เงินภาษีที่นำส่งในอัตรา\s*ร้อยละ\s*5[^\d]*([\d,]+\.\d{2})(?:\s|$)',
            r'\(2\)\s*เงินภาษีที่นำส่งในอัตรา\s*ร้อยละ\s*5[^\d]*([\d,]+\.\d{1,2})(?:\s|$)',
            # Pattern 2: "(2) เงินภาษีที่นำส่งในอัตรา ร้อยละ 5 34 21" (มีช่องว่างระหว่างตัวเลข)
            r'\(2\)\s*เงินภาษีที่นำส่งในอัตรา\s*ร้อยละ\s*5[^\d]*([\d,]+)\s+(\d{2})(?:\s|$)',
            r'\(2\)\s*เงินภาษีที่นำส่งในอัตรา\s*ร้อยละ\s*5[^\d]*([\d,]+)\s+(\d{1,2})(?:\s|$)',
            # Pattern 3: ไม่มีวงเล็บ "(2)"
            r'2\)\s*เงินภาษีที่นำส่งในอัตรา\s*ร้อยละ\s*5[^\d]*([\d,]+\.\d{2})(?:\s|$)',
            r'2\)\s*เงินภาษีที่นำส่งในอัตรา\s*ร้อยละ\s*5[^\d]*([\d,]+)\s+(\d{2})(?:\s|$)',
            # Pattern 4: ไม่มี "(2)" และ "ร้อยละ 5"
            r'\(2\)[^\d]*เงินภาษี[^\d]*ร้อยละ\s*5[^\d]*([\d,]+\.\d{2})(?:\s|$)',
            r'เงินภาษีที่นำส่งในอัตรา\s*ร้อยละ\s*5[^\d]*([\d,]+\.\d{2})(?:\s|$)',
            r'เงินภาษีที่นำส่งในอัตรา\s*ร้อยละ\s*5[^\d]*([\d,]+)\s+(\d{2})(?:\s|$)',
        ]
        
        for pattern_idx, pattern in enumerate(patterns):
            logger.info(f"🔍 [DEBUG] ลองใช้ pattern {pattern_idx+1}: {pattern[:80]}...")
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if match:
                logger.info(f"🔍 [DEBUG] Pattern {pattern_idx+1} match ได้: {match.groups()}")
                
                # กรณีที่มี 2 groups (main_part และ decimal_part)
                if len(match.groups()) == 2:
                    amount_part = match.group(1).strip()
                    decimal_part = match.group(2).strip()
                    
                    logger.info(f"🔍 [DEBUG] พบ pattern: amount_part='{amount_part}', decimal_part='{decimal_part}'")
                    
                    # ลบช่องว่างและ comma จากส่วนหลัก
                    amount_clean = re.sub(r'\s+', '', amount_part)
                    amount_clean = amount_clean.replace(',', '')
                    
                    if decimal_part.isdigit():
                        amount_str = f"{amount_clean}.{decimal_part.zfill(2)}"
                    else:
                        logger.info(f"🔍 [DEBUG] decimal_part ไม่ถูกต้อง: '{decimal_part}' ข้าม")
                        continue
                else:
                    # กรณีที่มี 1 group (มีจุดทศนิยมอยู่แล้ว)
                    amount_str = match.group(1).strip()
                    logger.info(f"🔍 [DEBUG] พบ pattern (มีจุดทศนิยม): amount_str='{amount_str}'")
                    amount_clean = amount_str.replace(',', '')
                    amount_str = amount_clean
                
                try:
                    amount_value = float(amount_str)
                    if amount_value >= 0:  # รับค่าตั้งแต่ 0 ขึ้นไป
                        amounts['รวมเป็นเงินทั้งสิ้น (ภ.ง.ด.54)'] = amount_value
                        logger.info(f"✅ [Pattern {pattern_idx+1}] พบรวมเป็นเงินทั้งสิ้น (ภ.ง.ด.54): {amount_value:,.2f}")
                        return amounts
                except ValueError as e:
                    logger.warning(f"⚠️ ไม่สามารถแปลง '{amount_str}' เป็นตัวเลขได้: {e}")
                    continue
        
        # Fallback 1: หาจาก "(4) รวมเป็นเงินทั้งสิ้น"
        logger.info(f"🔍 [DEBUG] ไม่พบ 'เงินภาษีที่นำส่งในอัตรา ร้อยละ 5' → ลองหาจาก '(4) รวมเป็นเงินทั้งสิ้น'...")
        
        fallback_patterns_1 = [
            # Pattern 1: "(4) รวมเป็นเงินทั้งสิ้น 34.21" (มีจุดทศนิยม)
            r'\(4\)\s*รวมเป็นเงินทั้งสิ้น[^\d]*([\d,]+\.\d{2})(?:\s|$)',
            r'\(4\)\s*รวมเป็นเงินทั้งสิ้น[^\d]*([\d,]+\.\d{1,2})(?:\s|$)',
            # Pattern 2: "(4) รวมเป็นเงินทั้งสิ้น 34 21" (มีช่องว่างระหว่างตัวเลข)
            r'\(4\)\s*รวมเป็นเงินทั้งสิ้น[^\d]*([\d,]+)\s+(\d{2})(?:\s|$)',
            r'\(4\)\s*รวมเป็นเงินทั้งสิ้น[^\d]*([\d,]+)\s+(\d{1,2})(?:\s|$)',
            # Pattern 3: ไม่มีวงเล็บ "(4)"
            r'4\)\s*รวมเป็นเงินทั้งสิ้น[^\d]*([\d,]+\.\d{2})(?:\s|$)',
            r'4\)\s*รวมเป็นเงินทั้งสิ้น[^\d]*([\d,]+)\s+(\d{2})(?:\s|$)',
            # Pattern 4: มี "คือ" คั่น
            r'\(4\)\s*รวมเป็นเงินทั้งสิ้น\s*(?:คือ\s*)?([\d,]+\.\d{2})(?:\s|$)',
            r'\(4\)\s*รวมเป็นเงินทั้งสิ้น\s*(?:คือ\s*)?([\d,]+)\s+(\d{2})(?:\s|$)',
        ]
        
        for pattern_idx, pattern in enumerate(fallback_patterns_1):
            logger.info(f"🔍 [DEBUG] [Fallback 1] ลองใช้ pattern {pattern_idx+1}: {pattern[:80]}...")
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if match:
                logger.info(f"🔍 [DEBUG] [Fallback 1] Pattern {pattern_idx+1} match ได้: {match.groups()}")
                
                if len(match.groups()) == 2:
                    amount_part = match.group(1).strip()
                    decimal_part = match.group(2).strip()
                    
                    logger.info(f"🔍 [DEBUG] [Fallback 1] พบ pattern: amount_part='{amount_part}', decimal_part='{decimal_part}'")
                    
                    amount_clean = re.sub(r'\s+', '', amount_part)
                    amount_clean = amount_clean.replace(',', '')
                    
                    if decimal_part.isdigit():
                        amount_str = f"{amount_clean}.{decimal_part.zfill(2)}"
                    else:
                        continue
                else:
                    amount_str = match.group(1).strip()
                    logger.info(f"🔍 [DEBUG] [Fallback 1] พบ pattern (มีจุดทศนิยม): amount_str='{amount_str}'")
                    amount_clean = amount_str.replace(',', '')
                    amount_str = amount_clean
                
                try:
                    amount_value = float(amount_str)
                    if amount_value >= 0:
                        amounts['รวมเป็นเงินทั้งสิ้น (ภ.ง.ด.54)'] = amount_value
                        logger.info(f"✅ [Fallback 1 Pattern {pattern_idx+1}] พบรวมเป็นเงินทั้งสิ้น (ภ.ง.ด.54): {amount_value:,.2f}")
                        return amounts
                except ValueError as e:
                    logger.warning(f"⚠️ ไม่สามารถแปลง '{amount_str}' เป็นตัวเลขได้: {e}")
                    continue
        
        # Fallback 2: ลองหาจากรูปแบบอื่นๆ (ไม่ต้องมี "(4)")
        logger.info(f"🔍 [DEBUG] ลองหาแบบ fallback 2...")
        
        fallback_patterns_2 = [
            # Pattern 1: "รวมเป็นเงินทั้งสิ้น 34.21" (มีจุดทศนิยม)
            r'รวมเป็นเงินทั้งสิ้น[^\d]*([\d,]+\.\d{2})(?:\s|$)',
            # Pattern 2: "รวมเป็นเงินทั้งสิ้น 34 21" (มีช่องว่างระหว่างตัวเลข)
            r'รวมเป็นเงินทั้งสิ้น[^\d]*([\d,]+)\s+(\d{2})(?:\s|$)',
            # Pattern 3: มี "คือ" คั่น
            r'รวมเป็นเงินทั้งสิ้น\s*(?:คือ\s*)?([\d,]+\.\d{2})(?:\s|$)',
            r'รวมเป็นเงินทั้งสิ้น\s*(?:คือ\s*)?([\d,]+)\s+(\d{2})(?:\s|$)',
            # Pattern 4: "(4)" เท่านั้น
            r'\(4\)[^\d]*([\d,]+\.\d{2})(?:\s|$)',
            r'\(4\)[^\d]*([\d,]+)\s+(\d{2})(?:\s|$)',
        ]
        
        for pattern_idx, pattern in enumerate(fallback_patterns_2):
            logger.info(f"🔍 [DEBUG] [Fallback 2] ลองใช้ pattern {pattern_idx+1}: {pattern[:80]}...")
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if match:
                logger.info(f"🔍 [DEBUG] [Fallback 2] Pattern {pattern_idx+1} match ได้: {match.groups()}")
                
                if len(match.groups()) == 2:
                    amount_part = match.group(1).strip()
                    decimal_part = match.group(2).strip()
                    
                    logger.info(f"🔍 [DEBUG] [Fallback 2] พบ pattern: amount_part='{amount_part}', decimal_part='{decimal_part}'")
                    
                    amount_clean = re.sub(r'\s+', '', amount_part)
                    amount_clean = amount_clean.replace(',', '')
                    
                    if decimal_part.isdigit():
                        amount_str = f"{amount_clean}.{decimal_part.zfill(2)}"
                    else:
                        continue
                else:
                    amount_str = match.group(1).strip()
                    logger.info(f"🔍 [DEBUG] [Fallback 2] พบ pattern (มีจุดทศนิยม): amount_str='{amount_str}'")
                    amount_clean = amount_str.replace(',', '')
                    amount_str = amount_clean
                
                try:
                    amount_value = float(amount_str)
                    if amount_value >= 0:
                        amounts['รวมเป็นเงินทั้งสิ้น (ภ.ง.ด.54)'] = amount_value
                        logger.info(f"✅ [Fallback 2 Pattern {pattern_idx+1}] พบรวมเป็นเงินทั้งสิ้น (ภ.ง.ด.54): {amount_value:,.2f}")
                        return amounts
                except ValueError as e:
                    logger.warning(f"⚠️ ไม่สามารถแปลง '{amount_str}' เป็นตัวเลขได้: {e}")
                    continue
        
        logger.warning(f"⚠️ [DEBUG] ไม่พบยอดเงิน 'รวมเป็นเงินทั้งสิ้น' ใน ภ.ง.ด.54")
        logger.info(f"🔍 [DEBUG] ข้อความที่ค้นหา (500 ตัวอักษรสุดท้าย): ...{text[-500:]}")
        return amounts
    
    def _parse_pnd53(self, text: str, formatted_text: str) -> Dict[str, Any]:
        """Parse ข้อมูล ภ.ง.ด.53"""
        data = self._parse_basic_info(text, formatted_text)
        data['tax_form_type'] = 'ภ.ง.ด.53'
        
        # 1. หาชื่อบริษัท (สำหรับ ภ.ง.ด.53)
        if not data.get('company_name'):
            pnd53_company_patterns = [
                # รูปแบบ: ชื่อผู้มีหน้าที่หักภาษี ณ ที่จ่าย (หน่วยงาน): บริษัท...
                r'ชื่อผู้มีหน้าที่หัก\s*ภาษี\s*ณ\s*ที่จ่าย\s*\([^)]*\)[^\n]*?[:：]\s*(?:=+\s*)?(?:[*]+\s*)?(บริษัท\s+[^\n]+?จำกัด(?:\s+(?:มหาชน|\(มหาชน\)))?)',
                # รูปแบบ: ชื่อผู้มีหน้าที่หักภาษี ณ ที่จ่าย (หน่วยงาน)\nบริษัท...
                r'ชื่อผู้มีหน้าที่หัก\s*ภาษี\s*ณ\s*ที่จ่าย\s*\([^)]*\)[^\n]*?\n\s*(?:=+\s*)?(?:[*]+\s*)?(บริษัท\s+[^\n]+?จำกัด(?:\s+(?:มหาชน|\(มหาชน\)))?)',
            ]
            # ลองหาใน raw text ก่อน
            for pattern in pnd53_company_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    company_name = match.group(1).strip()
                    company_name = re.sub(r'\s+', ' ', company_name)
                    company_name = re.sub(r'[=*]+', '', company_name)
                    company_name = company_name.strip()
                    if company_name and 'บริษัท' in company_name:
                        data['company_name'] = company_name
                        logger.info(f"✅ [ภ.ง.ด.53] พบชื่อบริษัท: {company_name}")
                        break
            
            # ถ้ายังไม่พบ ลองหาใน formatted_text
            if not data.get('company_name'):
                for pattern in pnd53_company_patterns:
                    match = re.search(pattern, formatted_text, re.IGNORECASE | re.MULTILINE)
                    if match:
                        company_name = match.group(1).strip()
                        company_name = re.sub(r'\s+', ' ', company_name)
                        company_name = re.sub(r'[=*]+', '', company_name)
                        company_name = company_name.strip()
                        if company_name and 'บริษัท' in company_name:
                            data['company_name'] = company_name
                            logger.info(f"✅ [ภ.ง.ด.53] พบชื่อบริษัท (จาก formatted_text): {company_name}")
                            break
        
        # 2. หาเลขประจำตัวผู้เสียภาษีอากร (สำหรับ ภ.ง.ด.53)
        if not data.get('tax_id'):
            pnd53_tax_id_patterns = [
                # รูปแบบ: เลขประจำตัวผู้เสียภาษีอากร (ของผู้มีหน้าที่หักภาษี ณ ที่จ่าย): 0 1 0 5 5 5 3 1 1 4 4 3 7
                r'เลขประจำตัวผู้เสียภาษีอากร\s*\([^)]*\)[^\n]*?[:：]\s*(?:=+\s*)?(?:[*]+\s*)?([0-9\s]{13,30})',
                # รูปแบบ: เลขประจำตัวผู้เสียภาษีอากร: 0 1 0 5 5 5 3 1 1 4 4 3 7
                r'เลขประจำตัวผู้เสียภาษีอากร[^\n]*?[:：]\s*(?:=+\s*)?(?:[*]+\s*)?([0-9\s]{13,30})',
            ]
            # ลองหาใน raw text ก่อน
            for pattern in pnd53_tax_id_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    tax_id_raw = match.group(1).strip()
                    tax_id_clean = re.sub(r'[\s\-=*]+', '', tax_id_raw)
                    if tax_id_clean.isdigit() and len(tax_id_clean) == 13:
                        tax_id_formatted = f"{tax_id_clean[0]}-{tax_id_clean[1:5]}-{tax_id_clean[5:10]}-{tax_id_clean[10:12]}-{tax_id_clean[12]}"
                        data['tax_id'] = tax_id_formatted
                        logger.info(f"✅ [ภ.ง.ด.53] พบเลขประจำตัวผู้เสียภาษีอากร: {tax_id_formatted}")
                        break
            
            # ถ้ายังไม่พบ ลองหาใน formatted_text
            if not data.get('tax_id'):
                for pattern in pnd53_tax_id_patterns:
                    match = re.search(pattern, formatted_text, re.IGNORECASE | re.MULTILINE)
                    if match:
                        tax_id_raw = match.group(1).strip()
                        tax_id_clean = re.sub(r'[\s\-=*]+', '', tax_id_raw)
                        if tax_id_clean.isdigit() and len(tax_id_clean) == 13:
                            tax_id_formatted = f"{tax_id_clean[0]}-{tax_id_clean[1:5]}-{tax_id_clean[5:10]}-{tax_id_clean[10:12]}-{tax_id_clean[12]}"
                            data['tax_id'] = tax_id_formatted
                            logger.info(f"✅ [ภ.ง.ด.53] พบเลขประจำตัวผู้เสียภาษีอากร (จาก formatted_text): {tax_id_formatted}")
                            break
        
        # Parse เดือนจากรูปแบบ ☑ (10) ตุลาคม สำหรับ ภ.ง.ด.53
        # หา checkbox ที่ถูกติ๊ก (☑) ตามด้วยหมายเลขเดือนและชื่อเดือน
        if not data['filing_period']['month']:
            month_mapping = {
                '1': 'มกราคม',
                '2': 'กุมภาพันธ์',
                '3': 'มีนาคม',
                '4': 'เมษายน',
                '5': 'พฤษภาคม',
                '6': 'มิถุนายน',
                '7': 'กรกฎาคม',
                '8': 'สิงหาคม',
                '9': 'กันยายน',
                '10': 'ตุลาคม',
                '11': 'พฤศจิกายน',
                '12': 'ธันวาคม',
            }
            
            # Pattern ที่รองรับ: ☑ (10) ตุลาคม หรือ ☑ (10) ตุลาคม (มีช่องว่างแปลกๆ)
            # หา checkbox ☑ ที่ตามด้วยวงเล็บและตัวเลขเดือน
            checkbox_month_pattern = r'☑\s*[^\n]*?\(\s*(\d{1,2})\s*\)\s*([มกกุมภาพันธ์มีนาคมเมษายนพฤษภาคมมิถุนายนกรกฎาคมสิงหาคมกันยายนตุลาคมพฤศจิกายนธันวาคม]+)'
            
            match = re.search(checkbox_month_pattern, text, re.IGNORECASE)
            if match:
                month_num = match.group(1).strip()
                month_name_in_text = match.group(2).strip()
                
                # ตรวจสอบว่า month_num ตรงกับชื่อเดือนหรือไม่
                if month_num in month_mapping:
                    month_name = month_mapping[month_num]
                    # ตรวจสอบว่าชื่อเดือนในข้อความตรงกับเดือนที่ map หรือไม่
                    if month_name in month_name_in_text:
                        data['filing_period']['month'] = month_name
                        logger.info(f"✅ พบเดือนจาก checkbox: {month_name} (☑ ({month_num}) {month_name})")
                    else:
                        # ถ้าไม่ตรงกัน แต่ยังมี checkbox ให้ใช้ชื่อเดือนจากข้อความ
                        for known_month in month_mapping.values():
                            if known_month in month_name_in_text:
                                data['filing_period']['month'] = known_month
                                logger.info(f"✅ พบเดือนจาก checkbox: {known_month} (จากข้อความ: {month_name_in_text})")
                                break
        
        # Parse ข้อมูลเฉพาะ ภ.ง.ด.53
        # ใช้ formatted_text แทน text เพื่อให้ได้ข้อมูลที่ถูก format แล้ว
        amounts = self._parse_pnd53_amounts(formatted_text if formatted_text else text)
        data['amounts'] = amounts
        
        return data
    
    def _parse_pnd53_amounts(self, text: str) -> Dict[str, float]:
        """Parse ยอดเงินจาก ภ.ง.ด.53"""
        amounts = {}
        
        # อ่านยอดเงินจาก "2. รวมยอดภาษีที่นำส่งทั้งสิ้น" หรือ "4. รวมยอดภาษีที่นำส่งทั้งสิ้น และเงินเพิ่ม"
        # รองรับทั้งรูปแบบข้อความธรรมดาและรูปแบบตาราง (มี pipe |)
        # ค่าอยู่ในคอลัมน์สุดท้าย: | | | 34,003.60
        
        logger.info(f"🔍 [DEBUG] เริ่ม parse ยอดเงิน ภ.ง.ด.53")
        
        # แยกแถวทั้งหมด
        all_rows = [row.strip() for row in text.split('\n') if row.strip()]
        logger.info(f"🔍 [DEBUG] จำนวนแถวทั้งหมด: {len(all_rows)}")
        
        # หาแถวที่มี "2. รวมยอดภาษีที่นำส่งทั้งสิ้น" หรือ "4. รวมยอดภาษีที่นำส่งทั้งสิ้น และเงินเพิ่ม"
        # ตรวจสอบทั้งกรณีที่มีช่องว่างก่อน "2." หรือ "4." หรือไม่
        target_rows = []
        
        # Log แถวที่เกี่ยวข้องเพื่อ debug
        logger.info(f"🔍 [DEBUG] กำลังตรวจสอบแถวทั้งหมด...")
        for idx, row in enumerate(all_rows):
            # ตรวจสอบว่าแถวมี "2." หรือ "4." และ "รวมยอดภาษีที่นำส่งทั้งสิ้น"
            # ใช้ pattern ที่ยืดหยุ่นมากขึ้น
            if re.search(r'(?:2|4)\s*\.\s*รวมยอดภาษีที่(?:นำ|น่า)ส่งทั้งสิ้น', row, re.IGNORECASE):
                target_rows.append(row)
                logger.info(f"🔍 [DEBUG] ✅ พบแถว {idx+1} (ตรง pattern): {row[:150]}")
            # Log แถวที่เกี่ยวข้องเพื่อ debug
            elif 'รวมยอด' in row or 'รวม' in row[:10]:
                logger.info(f"🔍 [DEBUG] แถว {idx+1} (เกี่ยวข้อง): {row[:150]}")
        
        if not target_rows:
            logger.info(f"🔍 [DEBUG] ไม่พบแถวที่ตรงกับ pattern '2. หรือ 4. รวมยอดภาษีที่นำส่งทั้งสิ้น' - จะใช้ fallback pattern แทน")
            logger.info(f"🔍 [DEBUG] ลองหาแถวที่มี 'รวมยอดภาษีที่นำส่งทั้งสิ้น' หรือ 'รวมยอดภาษีที่น่าส่งทั้งสิ้น'...")
            # ลองหาแบบยืดหยุ่นมากขึ้น (ไม่ต้องมี 2. หรือ 4. ข้างหน้า)
            for idx, row in enumerate(all_rows):
                if 'รวมยอดภาษีที่' in row and ('นำส่งทั้งสิ้น' in row or 'น่าส่งทั้งสิ้น' in row):
                    # ตรวจสอบว่าเป็นแถวสุดท้ายที่มีคำนี้
                    target_rows.append(row)
                    logger.info(f"🔍 [DEBUG] ✅ พบแถว {idx+1} (แบบยืดหยุ่น): {row[:150]}")
        
        if target_rows:
            # ใช้แถวสุดท้ายที่เจอ (กรณีมีหลายแถว)
            row = target_rows[-1]
            logger.info(f"🔍 พบแถว: {row[:100]}")
            
            # ถ้ามี pipe (|) แสดงว่าเป็นรูปแบบตาราง ให้อ่านจากคอลัมน์สุดท้าย
            if '|' in row:
                columns = [col.strip() for col in re.split(r'\s*\|\s*', row)]
                logger.info(f"🔍 [DEBUG] คอลัมน์ทั้งหมด ({len(columns)} คอลัมน์): {columns}")
                
                # หาค่าจากคอลัมน์สุดท้ายไปจนถึงคอลัมน์แรก (ย้อนกลับ)
                for col_idx in range(len(columns) - 1, -1, -1):
                    col = columns[col_idx].strip()
                    logger.info(f"🔍 [DEBUG] ตรวจสอบคอลัมน์ {col_idx+1}: '{col}'")
                    
                    if not col or col == '':
                        continue
                    
                    # ข้ามคอลัมน์ที่มีข้อความ "2." หรือ "4." หรือ "รวมยอด..." เพราะนั่นคือคอลัมน์แรก
                    if re.search(r'[24]\s*\.', col) or 'รวมยอด' in col or 'รวมยอดภาษี' in col:
                        logger.info(f"🔍 [DEBUG] ข้ามคอลัมน์ {col_idx+1} เพราะมีข้อความ '2./4.' หรือ 'รวมยอด'")
                        continue
                    
                    # หาตัวเลขที่มี comma หรือจุดทศนิยม (รูปแบบจำนวนเงิน)
                    # รูปแบบ: 34,003.60 หรือ 34003.60
                    amount_match = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d{4,}(?:\.\d{2})?)', col)
                    if amount_match:
                        amount_str = amount_match.group(1).strip()
                        amount_clean = amount_str.replace(',', '')
                        logger.info(f"🔍 [DEBUG] พบตัวเลข: '{amount_str}' -> {amount_clean}")
                        try:
                            amount_value = float(amount_clean)
                            logger.info(f"🔍 [DEBUG] แปลงเป็นตัวเลขได้: {amount_value}")
                            # ตรวจสอบว่าเป็นตัวเลขเงินจริง (>= 10 เพื่อหลีกเลี่ยงเลข 1-9)
                            if amount_value >= 10:
                                amounts['รวมยอดภาษีที่นำส่งทั้งสิ้น (ภ.ง.ด.53)'] = amount_value
                                logger.info(f"✅ พบรวมยอดภาษีที่นำส่งทั้งสิ้น (ภ.ง.ด.53): {amount_value:,.2f}")
                                return amounts
                            else:
                                logger.info(f"🔍 [DEBUG] ค่า {amount_value} น้อยกว่า 10 ข้าม")
                        except ValueError as e:
                            logger.info(f"🔍 [DEBUG] ไม่สามารถแปลง '{amount_clean}' เป็นตัวเลขได้: {e}")
                            continue
                
                logger.warning(f"⚠️ [DEBUG] ไม่พบค่าที่ถูกต้องในคอลัมน์ใดๆ ของแถว")
            else:
                # ถ้าไม่มี pipe ให้อ่านจากรูปแบบข้อความธรรมดา
                # รูปแบบ: "2. รวมยอดภาษีที่นำส่งทั้งสิ้น 34,003.60" หรือ "4. รวมยอดภาษีที่นำส่งทั้งสิ้น และเงินเพิ่ม (2. + 3.) 34,003.60"
                amount_patterns = [
                    r'[24]\.\s*รวมยอดภาษีที่(?:นำ|น่า)ส่งทั้งสิ้น\s*(?:คือ|:)\s*([\d,]+\.?\d*)',
                    r'รวมยอดภาษีที่(?:นำ|น่า)ส่งทั้งสิ้น\s*(?:คือ|:)\s*([\d,]+\.?\d*)',
                ]
                
                for pattern in amount_patterns:
                    match = re.search(pattern, row, re.IGNORECASE)
                    if match:
                        amount_str = match.group(1).strip()
                        amount_clean = amount_str.replace(',', '')
                        try:
                            amount_value = float(amount_clean)
                            if amount_value >= 10:
                                amounts['รวมยอดภาษีที่นำส่งทั้งสิ้น (ภ.ง.ด.53)'] = amount_value
                                logger.info(f"✅ พบรวมยอดภาษีที่นำส่งทั้งสิ้น (ภ.ง.ด.53): {amount_value:,.2f}")
                                return amounts
                        except ValueError:
                            continue
        
        # Fallback: ลองหาจากรูปแบบอื่นๆ (ถ้ายังไม่เจอ)
        logger.info(f"🔍 [DEBUG] ลองหาแบบ fallback จากข้อความทั้งหมด...")
        
        # ลองหาจากทั้งข้อความโดยตรง (ไม่จำกัดเฉพาะแถว)
        # Pattern ที่เฉพาะเจาะจง: หา "8. รวมยอดภาษีที่นำส่งทั้งสิ้น" ตามด้วย pipe และตัวเลข
        # รูปแบบ: 8. รวมยอดภาษีที่นำส่งทั้งสิ้น  | | | 57,086.53
        
        # ลองหาโดยตรงจากข้อความทั้งหมด (ไม่ต้องแยกเป็นแถว)
        # Pattern 1: หาจากรูปแบบที่เฉพาะเจาะจง: 8. รวมยอด... | | | 57,086.53
        direct_pattern = r'8\.\s*รวมยอดภาษีที่(?:นำ|น่า)ส่งทั้งสิ้น\s*\|\s*\|\s*\|\s*([\d,]+\.\d{2})'
        match = re.search(direct_pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            amount_str = match.group(1).strip()
            amount_clean = amount_str.replace(',', '')
            logger.info(f"🔍 [DEBUG] [Fallback Direct] พบตัวเลข: '{amount_str}' -> {amount_clean}")
            try:
                amount_value = float(amount_clean)
                if amount_value >= 10:
                    amounts['รวมยอดภาษีที่นำส่งทั้งสิ้น (ภ.ง.ด.53)'] = amount_value
                    logger.info(f"✅ [Fallback Direct] พบรวมยอดภาษีที่นำส่งทั้งสิ้น (ภ.ง.ด.53): {amount_value:,.2f}")
                    return amounts
            except ValueError:
                pass
        
        # Pattern 2: ลองหาจากข้อความที่อาจมีการแบ่งบรรทัด
        fallback_patterns = [
            # Pattern สำหรับตารางที่มี pipe: 8. รวมยอด... | | | 57,086.53
            r'8\.\s*รวมยอดภาษีที่(?:นำ|น่า)ส่งทั้งสิ้น[^|]*\|\s*\|\s*\|\s*([\d,]+\.\d{2})',
            r'8\s*\.\s*รวมยอดภาษีที่(?:นำ|น่า)ส่งทั้งสิ้น[^|]*\|\s*\|\s*\|\s*([\d,]+\.\d{2})',
            # Pattern ที่ไม่ต้องมี 8. ข้างหน้า
            r'รวมยอดภาษีที่(?:นำ|น่า)ส่งทั้งสิ้น[^|]*\|\s*\|\s*\|\s*([\d,]+\.\d{2})',
            # Pattern สำหรับจำนวนเงินที่มี comma และจุดทศนิยม 2 ตำแหน่ง
            r'8\.\s*รวมยอดภาษีที่(?:นำ|น่า)ส่งทั้งสิ้น[^0-9]*([\d,]+\.\d{2})',
        ]
        
        for pattern_idx, pattern in enumerate(fallback_patterns):
            logger.info(f"🔍 [DEBUG] [Fallback] ลองใช้ pattern {pattern_idx+1}: {pattern[:80]}...")
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                amount_str = match.group(1).strip()
                logger.info(f"🔍 [DEBUG] [Fallback] Pattern {pattern_idx+1} match ได้: '{amount_str}'")
                
                # ตรวจสอบว่าไม่ใช่แค่ตัวเลขลำดับ (เช่น "6.", "8.")
                if amount_str.endswith('.') and len(amount_str) <= 3:
                    logger.info(f"🔍 [DEBUG] [Fallback] ข้ามค่า '{amount_str}' เพราะเป็นเลขลำดับ")
                    continue
                
                # ตรวจสอบว่ามีจุดทศนิยม 2 ตำแหน่ง (เพื่อให้แน่ใจว่าเป็นจำนวนเงิน)
                if '.' in amount_str and len(amount_str.split('.')[-1]) == 2:
                    amount_clean = amount_str.replace(',', '')
                    logger.info(f"🔍 [DEBUG] [Fallback] พบตัวเลข: '{amount_str}' -> {amount_clean}")
                    try:
                        amount_value = float(amount_clean)
                        if amount_value >= 10:
                            amounts['รวมยอดภาษีที่นำส่งทั้งสิ้น (ภ.ง.ด.53)'] = amount_value
                            logger.info(f"✅ [Fallback] พบรวมยอดภาษีที่นำส่งทั้งสิ้น (ภ.ง.ด.53): {amount_value:,.2f}")
                            return amounts
                    except ValueError as e:
                        logger.info(f"🔍 [DEBUG] [Fallback] ไม่สามารถแปลง '{amount_clean}' เป็นตัวเลขได้: {e}")
                        continue
        
        # Pattern สำหรับ ภ.ง.ด.53: "4. รวมยอดภาษีที่นำส่งทั้งสิ้น และเงินเพิ่ม (2. + 3.) 34,003.60"
        # หรือ "2. รวมยอดภาษีที่นำส่งทั้งสิ้น 34,003.60"
        pnd53_fallback_patterns = [
            r'4\.\s*รวมยอดภาษีที่(?:นำ|น่า)ส่งทั้งสิ้น\s+และเงินเพิ่ม[^0-9]*([\d,]+\.\d{2})',
            r'4\s*\.\s*รวมยอดภาษีที่(?:นำ|น่า)ส่งทั้งสิ้น\s+และเงินเพิ่ม[^0-9]*([\d,]+\.\d{2})',
            r'2\.\s*รวมยอดภาษีที่(?:นำ|น่า)ส่งทั้งสิ้น[^0-9]*([\d,]+\.\d{2})',
            r'2\s*\.\s*รวมยอดภาษีที่(?:นำ|น่า)ส่งทั้งสิ้น[^0-9]*([\d,]+\.\d{2})',
        ]
        
        for pattern in pnd53_fallback_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                amount_str = match.group(1).strip()
                amount_clean = amount_str.replace(',', '')
                try:
                    amount_value = float(amount_clean)
                    if amount_value >= 10:
                        amounts['รวมยอดภาษีที่นำส่งทั้งสิ้น (ภ.ง.ด.53)'] = amount_value
                        logger.info(f"✅ [Fallback PND53] พบรวมยอดภาษีที่นำส่งทั้งสิ้น (ภ.ง.ด.53): {amount_value:,.2f}")
                        return amounts
                except ValueError:
                    continue
        
        logger.warning(f"⚠️ [DEBUG] ไม่พบยอดเงิน 'รวมยอดภาษีที่นำส่งทั้งสิ้น' ใน ภ.ง.ด.53")
        logger.info(f"🔍 [DEBUG] ข้อความที่ค้นหา (200 ตัวอักษรสุดท้าย): ...{text[-200:]}")
        return amounts
    
    def _parse_pnd1(self, text: str, formatted_text: str) -> Dict[str, Any]:
        """Parse ข้อมูล ภ.ง.ด.1"""
        data = self._parse_basic_info(text, formatted_text)
        data['tax_form_type'] = 'ภ.ง.ด.1'
        
        # 1. หาชื่อบริษัท (สำหรับ ภ.ง.ด.1)
        if not data.get('company_name'):
            pnd1_company_patterns = [
                # รูปแบบ: ชื่อผู้มีหน้าที่หักภาษี ณ ที่จ่าย (หน่วยงาน): บริษัท...
                r'ชื่อผู้มีหน้าที่หัก\s*ภาษี\s*ณ\s*ที่จ่าย\s*\([^)]*\)[^\n]*?[:：]\s*(?:=+\s*)?(?:[*]+\s*)?(บริษัท\s+[^\n]+?จำกัด(?:\s+(?:มหาชน|\(มหาชน\)))?)',
                # รูปแบบ: ชื่อผู้มีหน้าที่หักภาษี ณ ที่จ่าย (หน่วยงาน)\nบริษัท...
                r'ชื่อผู้มีหน้าที่หัก\s*ภาษี\s*ณ\s*ที่จ่าย\s*\([^)]*\)[^\n]*?\n\s*(?:=+\s*)?(?:[*]+\s*)?(บริษัท\s+[^\n]+?จำกัด(?:\s+(?:มหาชน|\(มหาชน\)))?)',
            ]
            # ลองหาใน raw text ก่อน
            for pattern in pnd1_company_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    company_name = match.group(1).strip()
                    company_name = re.sub(r'\s+', ' ', company_name)
                    company_name = re.sub(r'[=*]+', '', company_name)
                    company_name = company_name.strip()
                    if company_name and 'บริษัท' in company_name:
                        data['company_name'] = company_name
                        logger.info(f"✅ [ภ.ง.ด.1] พบชื่อบริษัท: {company_name}")
                        break
            
            # ถ้ายังไม่พบ ลองหาใน formatted_text
            if not data.get('company_name'):
                for pattern in pnd1_company_patterns:
                    match = re.search(pattern, formatted_text, re.IGNORECASE | re.MULTILINE)
                    if match:
                        company_name = match.group(1).strip()
                        company_name = re.sub(r'\s+', ' ', company_name)
                        company_name = re.sub(r'[=*]+', '', company_name)
                        company_name = company_name.strip()
                        if company_name and 'บริษัท' in company_name:
                            data['company_name'] = company_name
                            logger.info(f"✅ [ภ.ง.ด.1] พบชื่อบริษัท (จาก formatted_text): {company_name}")
                            break
        
        # 2. หาเลขประจำตัวผู้เสียภาษีอากร (สำหรับ ภ.ง.ด.1)
        if not data.get('tax_id'):
            pnd1_tax_id_patterns = [
                # รูปแบบ: เลขประจำตัวผู้เสียภาษีอากร: 0 1 0 5 5 5 3 1 1 4 4 3 7
                r'เลขประจำตัวผู้เสียภาษีอากร[^\n]*?[:：]\s*(?:=+\s*)?(?:[*]+\s*)?([0-9\s]{13,30})',
            ]
            # ลองหาใน raw text ก่อน
            for pattern in pnd1_tax_id_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    tax_id_raw = match.group(1).strip()
                    tax_id_clean = re.sub(r'[\s\-=*]+', '', tax_id_raw)
                    if tax_id_clean.isdigit() and len(tax_id_clean) == 13:
                        tax_id_formatted = f"{tax_id_clean[0]}-{tax_id_clean[1:5]}-{tax_id_clean[5:10]}-{tax_id_clean[10:12]}-{tax_id_clean[12]}"
                        data['tax_id'] = tax_id_formatted
                        logger.info(f"✅ [ภ.ง.ด.1] พบเลขประจำตัวผู้เสียภาษีอากร: {tax_id_formatted}")
                        break
            
            # ถ้ายังไม่พบ ลองหาใน formatted_text
            if not data.get('tax_id'):
                for pattern in pnd1_tax_id_patterns:
                    match = re.search(pattern, formatted_text, re.IGNORECASE | re.MULTILINE)
                    if match:
                        tax_id_raw = match.group(1).strip()
                        tax_id_clean = re.sub(r'[\s\-=*]+', '', tax_id_raw)
                        if tax_id_clean.isdigit() and len(tax_id_clean) == 13:
                            tax_id_formatted = f"{tax_id_clean[0]}-{tax_id_clean[1:5]}-{tax_id_clean[5:10]}-{tax_id_clean[10:12]}-{tax_id_clean[12]}"
                            data['tax_id'] = tax_id_formatted
                            logger.info(f"✅ [ภ.ง.ด.1] พบเลขประจำตัวผู้เสียภาษีอากร (จาก formatted_text): {tax_id_formatted}")
                            break
        
        # Parse เดือนจากรูปแบบ ☑ (10) ตุลาคม สำหรับ ภ.ง.ด.1
        # หา checkbox ที่ถูกติ๊ก (☑) ตามด้วยหมายเลขเดือนและชื่อเดือน
        if not data['filing_period']['month']:
            month_mapping = {
                '1': 'มกราคม',
                '2': 'กุมภาพันธ์',
                '3': 'มีนาคม',
                '4': 'เมษายน',
                '5': 'พฤษภาคม',
                '6': 'มิถุนายน',
                '7': 'กรกฎาคม',
                '8': 'สิงหาคม',
                '9': 'กันยายน',
                '10': 'ตุลาคม',
                '11': 'พฤศจิกายน',
                '12': 'ธันวาคม',
            }
            
            # Pattern ที่รองรับ: ☑ (10) ตุลาคม หรือ ☑ (10) ตุลาคม (มีช่องว่างแปลกๆ)
            # หา checkbox ☑ ที่ตามด้วยวงเล็บและตัวเลขเดือน
            checkbox_month_pattern = r'☑\s*[^\n]*?\(\s*(\d{1,2})\s*\)\s*([มกกุมภาพันธ์มีนาคมเมษายนพฤษภาคมมิถุนายนกรกฎาคมสิงหาคมกันยายนตุลาคมพฤศจิกายนธันวาคม]+)'
            
            match = re.search(checkbox_month_pattern, text, re.IGNORECASE)
            if match:
                month_num = match.group(1).strip()
                month_name_in_text = match.group(2).strip()
                
                # ตรวจสอบว่า month_num ตรงกับชื่อเดือนหรือไม่
                if month_num in month_mapping:
                    month_name = month_mapping[month_num]
                    # ตรวจสอบว่าชื่อเดือนในข้อความตรงกับเดือนที่ map หรือไม่
                    if month_name in month_name_in_text:
                        data['filing_period']['month'] = month_name
                        logger.info(f"✅ พบเดือนจาก checkbox: {month_name} (☑ ({month_num}) {month_name})")
                    else:
                        # ถ้าไม่ตรงกัน แต่ยังมี checkbox ให้ใช้ชื่อเดือนจากข้อความ
                        for known_month in month_mapping.values():
                            if known_month in month_name_in_text:
                                data['filing_period']['month'] = known_month
                                logger.info(f"✅ พบเดือนจาก checkbox: {known_month} (จากข้อความ: {month_name_in_text})")
                                break
        
        # Parse ข้อมูลเฉพาะ ภ.ง.ด.1
        # ใช้ formatted_text แทน text เพื่อให้ได้ข้อมูลที่ถูก format แล้ว
        amounts = self._parse_pnd1_amounts(formatted_text if formatted_text else text)
        data['amounts'] = amounts
        
        return data
    
    def _parse_pnd1_amounts(self, text: str) -> Dict[str, float]:
        """Parse ยอดเงินจาก ภ.ง.ด.1"""
        amounts = {}
        
        # ตรวจสอบว่ามีคำว่า "สำหรับใบเสร็จรับเงิน" หรือไม่
        # ถ้ามี ให้อนุญาตให้อ่านยอดเงินเป็น 0 ได้
        has_receipt_section = 'สำหรับใบเสร็จรับเงิน' in text
        if has_receipt_section:
            logger.info(f"🔍 [DEBUG] พบคำว่า 'สำหรับใบเสร็จรับเงิน' - อนุญาตให้อ่านยอดเงินเป็น 0 ได้")
        
        # อ่านยอดเงินจาก "8. รวมยอดภาษีที่นำส่งทั้งสิ้น" หรือ "8. รวมยอดภาษีที่น่าส่งทั้งสิ้น"
        # รองรับทั้งรูปแบบข้อความธรรมดาและรูปแบบตาราง (มี pipe |)
        # ค่าอยู่ในคอลัมน์สุดท้าย: | | | 57,086.53
        
        logger.info(f"🔍 [DEBUG] เริ่ม parse ยอดเงิน ภ.ง.ด.1")
        
        # แยกแถวทั้งหมด
        all_rows = [row.strip() for row in text.split('\n') if row.strip()]
        logger.info(f"🔍 [DEBUG] จำนวนแถวทั้งหมด: {len(all_rows)}")
        
        # หาแถวที่มี "8. รวมยอดภาษีที่นำส่งทั้งสิ้น" หรือ "8. รวมยอดภาษีที่น่าส่งทั้งสิ้น"
        # ตรวจสอบทั้งกรณีที่มีช่องว่างก่อน "8." หรือไม่
        target_rows = []
        
        # Log แถวที่เกี่ยวข้องเพื่อ debug
        logger.info(f"🔍 [DEBUG] กำลังตรวจสอบแถวทั้งหมด...")
        for idx, row in enumerate(all_rows):
            # ตรวจสอบว่าแถวมี "8." และ "รวมยอดภาษีที่นำส่งทั้งสิ้น" หรือ "รวมยอดภาษีที่น่าส่งทั้งสิ้น"
            # ใช้ pattern ที่ยืดหยุ่นมากขึ้น
            if re.search(r'8\s*\.\s*รวมยอดภาษีที่(?:นำ|น่า)ส่งทั้งสิ้น', row, re.IGNORECASE):
                target_rows.append(row)
                logger.info(f"🔍 [DEBUG] ✅ พบแถว {idx+1} (ตรง pattern): {row[:150]}")
            # Log แถวที่เกี่ยวข้องเพื่อ debug
            elif 'รวมยอด' in row or 'รวม' in row[:10]:
                logger.info(f"🔍 [DEBUG] แถว {idx+1} (เกี่ยวข้อง): {row[:150]}")
        
        if not target_rows:
            logger.warning(f"⚠️ [DEBUG] ไม่พบแถวที่ตรงกับ pattern '8. รวมยอดภาษีที่นำส่งทั้งสิ้น'")
            logger.info(f"🔍 [DEBUG] ลองหาแถวที่มี 'รวมยอดภาษีที่นำส่งทั้งสิ้น' หรือ 'รวมยอดภาษีที่น่าส่งทั้งสิ้น'...")
            # ลองหาแบบยืดหยุ่นมากขึ้น (ไม่ต้องมี 8. ข้างหน้า)
            for idx, row in enumerate(all_rows):
                if 'รวมยอดภาษีที่' in row and ('นำส่งทั้งสิ้น' in row or 'น่าส่งทั้งสิ้น' in row):
                    # ตรวจสอบว่าเป็นแถวสุดท้ายที่มีคำนี้ (น่าจะเป็นแถวที่ 8)
                    target_rows.append(row)
                    logger.info(f"🔍 [DEBUG] ✅ พบแถว {idx+1} (แบบยืดหยุ่น): {row[:150]}")
        
        if target_rows:
            # ใช้แถวสุดท้ายที่เจอ (กรณีมีหลายแถว)
            row = target_rows[-1]
            logger.info(f"🔍 พบแถว: {row[:100]}")
            
            # ถ้ามี pipe (|) แสดงว่าเป็นรูปแบบตาราง ให้อ่านจากคอลัมน์สุดท้าย
            if '|' in row:
                columns = [col.strip() for col in re.split(r'\s*\|\s*', row)]
                logger.info(f"🔍 [DEBUG] คอลัมน์ทั้งหมด ({len(columns)} คอลัมน์): {columns}")
                
                # หาค่าจากคอลัมน์สุดท้ายไปจนถึงคอลัมน์แรก (ย้อนกลับ)
                for col_idx in range(len(columns) - 1, -1, -1):
                    col = columns[col_idx].strip()
                    logger.info(f"🔍 [DEBUG] ตรวจสอบคอลัมน์ {col_idx+1}: '{col}'")
                    
                    if not col or col == '':
                        continue
                    
                    # ข้ามคอลัมน์ที่มีข้อความ "8." หรือ "รวมยอด..." เพราะนั่นคือคอลัมน์แรก
                    if '8.' in col or 'รวมยอด' in col or 'รวมยอดภาษี' in col:
                        logger.info(f"🔍 [DEBUG] ข้ามคอลัมน์ {col_idx+1} เพราะมีข้อความ '8.' หรือ 'รวมยอด'")
                        continue
                    
                    # หาตัวเลขที่มี comma หรือจุดทศนิยม (รูปแบบจำนวนเงิน)
                    # รูปแบบ: 57,086.53 หรือ 57086.53
                    amount_match = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d{4,}(?:\.\d{2})?)', col)
                    if amount_match:
                        amount_str = amount_match.group(1).strip()
                        amount_clean = amount_str.replace(',', '')
                        logger.info(f"🔍 [DEBUG] พบตัวเลข: '{amount_str}' -> {amount_clean}")
                        try:
                            amount_value = float(amount_clean)
                            logger.info(f"🔍 [DEBUG] แปลงเป็นตัวเลขได้: {amount_value}")
                            # ตรวจสอบว่าเป็นตัวเลขเงินจริง
                            # ถ้ามีคำว่า "สำหรับใบเสร็จรับเงิน" ให้อนุญาตให้เป็น 0 ได้
                            # ถ้าไม่มี ต้อง >= 10 เพื่อหลีกเลี่ยงเลข 1-9
                            if has_receipt_section:
                                # ถ้ามี "สำหรับใบเสร็จรับเงิน" อนุญาตให้เป็น 0 หรือค่าอื่นๆ
                                amounts['รวมยอดภาษีที่นำส่งทั้งสิ้น (ภ.ง.ด.1)'] = amount_value
                                logger.info(f"✅ พบรวมยอดภาษีที่นำส่งทั้งสิ้น (ภ.ง.ด.1): {amount_value:,.2f} (มีใบเสร็จรับเงิน)")
                                return amounts
                            elif amount_value >= 10:
                                amounts['รวมยอดภาษีที่นำส่งทั้งสิ้น (ภ.ง.ด.1)'] = amount_value
                                logger.info(f"✅ พบรวมยอดภาษีที่นำส่งทั้งสิ้น (ภ.ง.ด.1): {amount_value:,.2f}")
                                return amounts
                            else:
                                logger.info(f"🔍 [DEBUG] ค่า {amount_value} น้อยกว่า 10 ข้าม")
                        except ValueError as e:
                            logger.info(f"🔍 [DEBUG] ไม่สามารถแปลง '{amount_clean}' เป็นตัวเลขได้: {e}")
                            continue
                
                logger.warning(f"⚠️ [DEBUG] ไม่พบค่าที่ถูกต้องในคอลัมน์ใดๆ ของแถว")
            else:
                # ถ้าไม่มี pipe ให้อ่านจากรูปแบบข้อความธรรมดา
                # รูปแบบ: "8. รวมยอดภาษีที่นำส่งทั้งสิ้น คือ 57,086.53"
                amount_patterns = [
                    r'8\.\s*รวมยอดภาษีที่(?:นำ|น่า)ส่งทั้งสิ้น\s*(?:คือ|:)\s*([\d,]+\.?\d*)',
                    r'รวมยอดภาษีที่(?:นำ|น่า)ส่งทั้งสิ้น\s*(?:คือ|:)\s*([\d,]+\.?\d*)',
                ]
                
                for pattern in amount_patterns:
                    match = re.search(pattern, row, re.IGNORECASE)
                    if match:
                        amount_str = match.group(1).strip()
                        amount_clean = amount_str.replace(',', '')
                        try:
                            amount_value = float(amount_clean)
                            # ถ้ามีคำว่า "สำหรับใบเสร็จรับเงิน" ให้อนุญาตให้เป็น 0 ได้
                            if has_receipt_section:
                                amounts['รวมยอดภาษีที่นำส่งทั้งสิ้น (ภ.ง.ด.1)'] = amount_value
                                logger.info(f"✅ พบรวมยอดภาษีที่นำส่งทั้งสิ้น (ภ.ง.ด.1): {amount_value:,.2f} (มีใบเสร็จรับเงิน)")
                                return amounts
                            elif amount_value >= 10:
                                amounts['รวมยอดภาษีที่นำส่งทั้งสิ้น (ภ.ง.ด.1)'] = amount_value
                                logger.info(f"✅ พบรวมยอดภาษีที่นำส่งทั้งสิ้น (ภ.ง.ด.1): {amount_value:,.2f}")
                                return amounts
                        except ValueError:
                            continue
        
        # Fallback: ลองหาจากรูปแบบอื่นๆ (ถ้ายังไม่เจอ)
        logger.info(f"🔍 [DEBUG] ลองหาแบบ fallback จากข้อความทั้งหมด...")
        
        # ลองหาจากทั้งข้อความโดยตรง (ไม่จำกัดเฉพาะแถว)
        # Pattern ที่เฉพาะเจาะจง: หา "8. รวมยอดภาษีที่นำส่งทั้งสิ้น" ตามด้วย pipe และตัวเลข
        # รูปแบบ: 8. รวมยอดภาษีที่นำส่งทั้งสิ้น  | | | 57,086.53
        
        # ลองหาโดยตรงจากข้อความทั้งหมด (ไม่ต้องแยกเป็นแถว)
        # Pattern 1: หาจากรูปแบบที่เฉพาะเจาะจง: 8. รวมยอด... | | | 57,086.53
        direct_pattern = r'8\.\s*รวมยอดภาษีที่(?:นำ|น่า)ส่งทั้งสิ้น\s*\|\s*\|\s*\|\s*([\d,]+\.\d{2})'
        match = re.search(direct_pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            amount_str = match.group(1).strip()
            amount_clean = amount_str.replace(',', '')
            logger.info(f"🔍 [DEBUG] [Fallback Direct] พบตัวเลข: '{amount_str}' -> {amount_clean}")
            try:
                amount_value = float(amount_clean)
                # ถ้ามีคำว่า "สำหรับใบเสร็จรับเงิน" ให้อนุญาตให้เป็น 0 ได้
                if has_receipt_section:
                    amounts['รวมยอดภาษีที่นำส่งทั้งสิ้น (ภ.ง.ด.1)'] = amount_value
                    logger.info(f"✅ [Fallback Direct] พบรวมยอดภาษีที่นำส่งทั้งสิ้น (ภ.ง.ด.1): {amount_value:,.2f} (มีใบเสร็จรับเงิน)")
                    return amounts
                elif amount_value >= 10:
                    amounts['รวมยอดภาษีที่นำส่งทั้งสิ้น (ภ.ง.ด.1)'] = amount_value
                    logger.info(f"✅ [Fallback Direct] พบรวมยอดภาษีที่นำส่งทั้งสิ้น (ภ.ง.ด.1): {amount_value:,.2f}")
                    return amounts
            except ValueError:
                pass
        
        # Pattern 2: ลองหาจากข้อความที่อาจมีการแบ่งบรรทัด
        fallback_patterns = [
            # Pattern สำหรับตารางที่มี pipe: 8. รวมยอด... | | | 57,086.53
            r'8\.\s*รวมยอดภาษีที่(?:นำ|น่า)ส่งทั้งสิ้น[^|]*\|\s*\|\s*\|\s*([\d,]+\.\d{2})',
            r'8\s*\.\s*รวมยอดภาษีที่(?:นำ|น่า)ส่งทั้งสิ้น[^|]*\|\s*\|\s*\|\s*([\d,]+\.\d{2})',
            # Pattern ที่ไม่ต้องมี 8. ข้างหน้า
            r'รวมยอดภาษีที่(?:นำ|น่า)ส่งทั้งสิ้น[^|]*\|\s*\|\s*\|\s*([\d,]+\.\d{2})',
            # Pattern สำหรับจำนวนเงินที่มี comma และจุดทศนิยม 2 ตำแหน่ง
            r'8\.\s*รวมยอดภาษีที่(?:นำ|น่า)ส่งทั้งสิ้น[^0-9]*([\d,]+\.\d{2})',
        ]
        
        for pattern_idx, pattern in enumerate(fallback_patterns):
            logger.info(f"🔍 [DEBUG] [Fallback] ลองใช้ pattern {pattern_idx+1}: {pattern[:80]}...")
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                amount_str = match.group(1).strip()
                logger.info(f"🔍 [DEBUG] [Fallback] Pattern {pattern_idx+1} match ได้: '{amount_str}'")
                
                # ตรวจสอบว่าไม่ใช่แค่ตัวเลขลำดับ (เช่น "6.", "8.")
                if amount_str.endswith('.') and len(amount_str) <= 3:
                    logger.info(f"🔍 [DEBUG] [Fallback] ข้ามค่า '{amount_str}' เพราะเป็นเลขลำดับ")
                    continue
                
                # ตรวจสอบว่ามีจุดทศนิยม 2 ตำแหน่ง (เพื่อให้แน่ใจว่าเป็นจำนวนเงิน)
                if '.' in amount_str and len(amount_str.split('.')[-1]) == 2:
                    amount_clean = amount_str.replace(',', '')
                    logger.info(f"🔍 [DEBUG] [Fallback] พบตัวเลข: '{amount_str}' -> {amount_clean}")
                    try:
                        amount_value = float(amount_clean)
                        # ถ้ามีคำว่า "สำหรับใบเสร็จรับเงิน" ให้อนุญาตให้เป็น 0 ได้
                        if has_receipt_section:
                            amounts['รวมยอดภาษีที่นำส่งทั้งสิ้น (ภ.ง.ด.1)'] = amount_value
                            logger.info(f"✅ [Fallback] พบรวมยอดภาษีที่นำส่งทั้งสิ้น (ภ.ง.ด.1): {amount_value:,.2f} (มีใบเสร็จรับเงิน)")
                            return amounts
                        elif amount_value >= 10:
                            amounts['รวมยอดภาษีที่นำส่งทั้งสิ้น (ภ.ง.ด.1)'] = amount_value
                            logger.info(f"✅ [Fallback] พบรวมยอดภาษีที่นำส่งทั้งสิ้น (ภ.ง.ด.1): {amount_value:,.2f}")
                            return amounts
                    except ValueError as e:
                        logger.info(f"🔍 [DEBUG] [Fallback] ไม่สามารถแปลง '{amount_clean}' เป็นตัวเลขได้: {e}")
                        continue
        
        # Pattern สำหรับ ภ.ง.ด.1: "8. รวมยอดภาษีที่นำส่งทั้งสิ้น 57,086.53" หรือ "8. รวมยอดภาษีที่นำส่งทั้งสิ้น และเงินเพิ่ม (6.+7.) 57,086.53"
        pnd1_fallback_patterns = [
            r'8\.\s*รวมยอดภาษีที่(?:นำ|น่า)ส่งทั้งสิ้น\s+และเงินเพิ่ม[^0-9]*([\d,]+\.\d{2})',
            r'8\s*\.\s*รวมยอดภาษีที่(?:นำ|น่า)ส่งทั้งสิ้น\s+และเงินเพิ่ม[^0-9]*([\d,]+\.\d{2})',
            r'8\.\s*รวมยอดภาษีที่(?:นำ|น่า)ส่งทั้งสิ้น[^0-9]*([\d,]+\.\d{2})',
            r'8\s*\.\s*รวมยอดภาษีที่(?:นำ|น่า)ส่งทั้งสิ้น[^0-9]*([\d,]+\.\d{2})',
        ]
        
        logger.info(f"🔍 [DEBUG] [Fallback PND1] กำลังค้นหา pattern สำหรับ ภ.ง.ด.1...")
        for pattern_idx, pattern in enumerate(pnd1_fallback_patterns):
            logger.info(f"🔍 [DEBUG] [Fallback PND1] ลองใช้ pattern {pattern_idx+1}: {pattern[:80]}...")
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                amount_str = match.group(1).strip()
                logger.info(f"🔍 [DEBUG] [Fallback PND1] Pattern {pattern_idx+1} match ได้: '{amount_str}'")
                amount_clean = amount_str.replace(',', '')
                try:
                    amount_value = float(amount_clean)
                    if has_receipt_section or amount_value >= 10:
                        amounts['รวมยอดภาษีที่นำส่งทั้งสิ้น (ภ.ง.ด.1)'] = amount_value
                        logger.info(f"✅ [Fallback PND1] พบรวมยอดภาษีที่นำส่งทั้งสิ้น (ภ.ง.ด.1): {amount_value:,.2f}")
                        return amounts
                except ValueError as e:
                    logger.info(f"🔍 [DEBUG] [Fallback PND1] ไม่สามารถแปลง '{amount_clean}' เป็นตัวเลขได้: {e}")
                    continue
        
        logger.warning(f"⚠️ [DEBUG] ไม่พบยอดเงิน 'รวมยอดภาษีที่นำส่งทั้งสิ้น' ใน ภ.ง.ด.1")
        logger.info(f"🔍 [DEBUG] ข้อความที่ค้นหา (200 ตัวอักษรสุดท้าย): ...{text[-200:]}")
        return amounts
    
    def _parse_pnd3(self, text: str, formatted_text: str) -> Dict[str, Any]:
        """Parse ข้อมูล ภ.ง.ด.3"""
        data = self._parse_basic_info(text, formatted_text)
        data['tax_form_type'] = 'ภ.ง.ด.3'
        
        # 1. หาชื่อบริษัท (สำหรับ ภ.ง.ด.3)
        if not data.get('company_name'):
            pnd3_company_patterns = [
                # รูปแบบ: ชื่อผู้มีหน้าที่หักภาษี ณ ที่จ่าย (หน่วยงาน): บริษัท...
                r'ชื่อผู้มีหน้าที่หัก\s*ภาษี\s*ณ\s*ที่จ่าย\s*\([^)]*\)[^\n]*?[:：]\s*(?:=+\s*)?(?:[*]+\s*)?(บริษัท\s+[^\n]+?จำกัด(?:\s+(?:มหาชน|\(มหาชน\)))?)',
                # รูปแบบ: ชื่อผู้มีหน้าที่หักภาษี ณ ที่จ่าย (หน่วยงาน)\nบริษัท...
                r'ชื่อผู้มีหน้าที่หัก\s*ภาษี\s*ณ\s*ที่จ่าย\s*\([^)]*\)[^\n]*?\n\s*(?:=+\s*)?(?:[*]+\s*)?(บริษัท\s+[^\n]+?จำกัด(?:\s+(?:มหาชน|\(มหาชน\)))?)',
            ]
            # ลองหาใน raw text ก่อน
            for pattern in pnd3_company_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    company_name = match.group(1).strip()
                    company_name = re.sub(r'\s+', ' ', company_name)
                    company_name = re.sub(r'[=*]+', '', company_name)
                    company_name = company_name.strip()
                    if company_name and 'บริษัท' in company_name:
                        data['company_name'] = company_name
                        logger.info(f"✅ [ภ.ง.ด.3] พบชื่อบริษัท: {company_name}")
                        break
            
            # ถ้ายังไม่พบ ลองหาใน formatted_text
            if not data.get('company_name'):
                for pattern in pnd3_company_patterns:
                    match = re.search(pattern, formatted_text, re.IGNORECASE | re.MULTILINE)
                    if match:
                        company_name = match.group(1).strip()
                        company_name = re.sub(r'\s+', ' ', company_name)
                        company_name = re.sub(r'[=*]+', '', company_name)
                        company_name = company_name.strip()
                        if company_name and 'บริษัท' in company_name:
                            data['company_name'] = company_name
                            logger.info(f"✅ [ภ.ง.ด.3] พบชื่อบริษัท (จาก formatted_text): {company_name}")
                            break
        
        # 2. หาเลขประจำตัวผู้เสียภาษีอากร (สำหรับ ภ.ง.ด.3)
        if not data.get('tax_id'):
            pnd3_tax_id_patterns = [
                # รูปแบบ: เลขประจำตัวผู้เสียภาษีอากร (ของผู้มีหน้าที่หักภาษี ณ ที่จ่าย): 0 1 0 5 5 5 3 1 1 4 4 3 7
                r'เลขประจำตัวผู้เสียภาษีอากร\s*\([^)]*\)[^\n]*?[:：]\s*(?:=+\s*)?(?:[*]+\s*)?([0-9\s]{13,30})',
                # รูปแบบ: เลขประจำตัวผู้เสียภาษีอากร: 0 1 0 5 5 5 3 1 1 4 4 3 7
                r'เลขประจำตัวผู้เสียภาษีอากร[^\n]*?[:：]\s*(?:=+\s*)?(?:[*]+\s*)?([0-9\s]{13,30})',
            ]
            # ลองหาใน raw text ก่อน
            for pattern in pnd3_tax_id_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    tax_id_raw = match.group(1).strip()
                    tax_id_clean = re.sub(r'[\s\-=*]+', '', tax_id_raw)
                    if tax_id_clean.isdigit() and len(tax_id_clean) == 13:
                        tax_id_formatted = f"{tax_id_clean[0]}-{tax_id_clean[1:5]}-{tax_id_clean[5:10]}-{tax_id_clean[10:12]}-{tax_id_clean[12]}"
                        data['tax_id'] = tax_id_formatted
                        logger.info(f"✅ [ภ.ง.ด.3] พบเลขประจำตัวผู้เสียภาษีอากร: {tax_id_formatted}")
                        break
            
            # ถ้ายังไม่พบ ลองหาใน formatted_text
            if not data.get('tax_id'):
                for pattern in pnd3_tax_id_patterns:
                    match = re.search(pattern, formatted_text, re.IGNORECASE | re.MULTILINE)
                    if match:
                        tax_id_raw = match.group(1).strip()
                        tax_id_clean = re.sub(r'[\s\-=*]+', '', tax_id_raw)
                        if tax_id_clean.isdigit() and len(tax_id_clean) == 13:
                            tax_id_formatted = f"{tax_id_clean[0]}-{tax_id_clean[1:5]}-{tax_id_clean[5:10]}-{tax_id_clean[10:12]}-{tax_id_clean[12]}"
                            data['tax_id'] = tax_id_formatted
                            logger.info(f"✅ [ภ.ง.ด.3] พบเลขประจำตัวผู้เสียภาษีอากร (จาก formatted_text): {tax_id_formatted}")
                            break
        
        # Parse เดือนจากรูปแบบ ☑ (10) ตุลาคม สำหรับ ภ.ง.ด.3
        # หา checkbox ที่ถูกติ๊ก (☑) ตามด้วยหมายเลขเดือนและชื่อเดือน
        if not data['filing_period']['month']:
            month_mapping = {
                '1': 'มกราคม',
                '2': 'กุมภาพันธ์',
                '3': 'มีนาคม',
                '4': 'เมษายน',
                '5': 'พฤษภาคม',
                '6': 'มิถุนายน',
                '7': 'กรกฎาคม',
                '8': 'สิงหาคม',
                '9': 'กันยายน',
                '10': 'ตุลาคม',
                '11': 'พฤศจิกายน',
                '12': 'ธันวาคม',
            }
            
            # Pattern ที่รองรับ: ☑ (10) ตุลาคม หรือ ☑ (10) ตุลาคม (มีช่องว่างแปลกๆ)
            # หา checkbox ☑ ที่ตามด้วยวงเล็บและตัวเลขเดือน
            checkbox_month_pattern = r'☑\s*[^\n]*?\(\s*(\d{1,2})\s*\)\s*([มกกุมภาพันธ์มีนาคมเมษายนพฤษภาคมมิถุนายนกรกฎาคมสิงหาคมกันยายนตุลาคมพฤศจิกายนธันวาคม]+)'
            
            match = re.search(checkbox_month_pattern, text, re.IGNORECASE)
            if match:
                month_num = match.group(1).strip()
                month_name_in_text = match.group(2).strip()
                
                # ตรวจสอบว่า month_num ตรงกับชื่อเดือนหรือไม่
                if month_num in month_mapping:
                    month_name = month_mapping[month_num]
                    # ตรวจสอบว่าชื่อเดือนในข้อความตรงกับเดือนที่ map หรือไม่
                    if month_name in month_name_in_text:
                        data['filing_period']['month'] = month_name
                        logger.info(f"✅ พบเดือนจาก checkbox: {month_name} (☑ ({month_num}) {month_name})")
                    else:
                        # ถ้าไม่ตรงกัน แต่ยังมี checkbox ให้ใช้ชื่อเดือนจากข้อความ
                        for known_month in month_mapping.values():
                            if known_month in month_name_in_text:
                                data['filing_period']['month'] = known_month
                                logger.info(f"✅ พบเดือนจาก checkbox: {known_month} (จากข้อความ: {month_name_in_text})")
                                break
        
        # Parse ข้อมูลเฉพาะ ภ.ง.ด.3
        # ใช้ formatted_text แทน text เพื่อให้ได้ข้อมูลที่ถูก format แล้ว
        amounts = self._parse_pnd3_amounts(formatted_text if formatted_text else text)
        data['amounts'] = amounts
        
        return data
    
    def _parse_pnd3_amounts(self, text: str) -> Dict[str, float]:
        """Parse ยอดเงินจาก ภ.ง.ด.3"""
        amounts = {}
        
        # อ่านยอดเงินจาก "8. รวมยอดภาษีที่นำส่งทั้งสิ้น" หรือ "8. รวมยอดภาษีที่น่าส่งทั้งสิ้น"
        # รองรับทั้งรูปแบบข้อความธรรมดาและรูปแบบตาราง (มี pipe |)
        # ค่าอยู่ในคอลัมน์สุดท้าย: | | | 57,086.53
        
        logger.info(f"🔍 [DEBUG] เริ่ม parse ยอดเงิน ภ.ง.ด.3")
        
        # แยกแถวทั้งหมด
        all_rows = [row.strip() for row in text.split('\n') if row.strip()]
        logger.info(f"🔍 [DEBUG] จำนวนแถวทั้งหมด: {len(all_rows)}")
        
        # หาแถวที่มี "8. รวมยอดภาษีที่นำส่งทั้งสิ้น" หรือ "8. รวมยอดภาษีที่น่าส่งทั้งสิ้น"
        # ตรวจสอบทั้งกรณีที่มีช่องว่างก่อน "8." หรือไม่
        target_rows = []
        
        # Log แถวที่เกี่ยวข้องเพื่อ debug
        logger.info(f"🔍 [DEBUG] กำลังตรวจสอบแถวทั้งหมด...")
        for idx, row in enumerate(all_rows):
            # ตรวจสอบว่าแถวมี "8." และ "รวมยอดภาษีที่นำส่งทั้งสิ้น" หรือ "รวมยอดภาษีที่น่าส่งทั้งสิ้น"
            # ใช้ pattern ที่ยืดหยุ่นมากขึ้น
            if re.search(r'8\s*\.\s*รวมยอดภาษีที่(?:นำ|น่า)ส่งทั้งสิ้น', row, re.IGNORECASE):
                target_rows.append(row)
                logger.info(f"🔍 [DEBUG] ✅ พบแถว {idx+1} (ตรง pattern): {row[:150]}")
            # Log แถวที่เกี่ยวข้องเพื่อ debug
            elif 'รวมยอด' in row or 'รวม' in row[:10]:
                logger.info(f"🔍 [DEBUG] แถว {idx+1} (เกี่ยวข้อง): {row[:150]}")
        
        if not target_rows:
            logger.warning(f"⚠️ [DEBUG] ไม่พบแถวที่ตรงกับ pattern '8. รวมยอดภาษีที่นำส่งทั้งสิ้น'")
            logger.info(f"🔍 [DEBUG] ลองหาแถวที่มี 'รวมยอดภาษีที่นำส่งทั้งสิ้น' หรือ 'รวมยอดภาษีที่น่าส่งทั้งสิ้น'...")
            # ลองหาแบบยืดหยุ่นมากขึ้น (ไม่ต้องมี 8. ข้างหน้า)
            for idx, row in enumerate(all_rows):
                if 'รวมยอดภาษีที่' in row and ('นำส่งทั้งสิ้น' in row or 'น่าส่งทั้งสิ้น' in row):
                    # ตรวจสอบว่าเป็นแถวสุดท้ายที่มีคำนี้ (น่าจะเป็นแถวที่ 8)
                    target_rows.append(row)
                    logger.info(f"🔍 [DEBUG] ✅ พบแถว {idx+1} (แบบยืดหยุ่น): {row[:150]}")
        
        if target_rows:
            # ใช้แถวสุดท้ายที่เจอ (กรณีมีหลายแถว)
            row = target_rows[-1]
            logger.info(f"🔍 พบแถว: {row[:100]}")
            
            # ถ้ามี pipe (|) แสดงว่าเป็นรูปแบบตาราง ให้อ่านจากคอลัมน์สุดท้าย
            if '|' in row:
                columns = [col.strip() for col in re.split(r'\s*\|\s*', row)]
                logger.info(f"🔍 [DEBUG] คอลัมน์ทั้งหมด ({len(columns)} คอลัมน์): {columns}")
                
                # หาค่าจากคอลัมน์สุดท้ายไปจนถึงคอลัมน์แรก (ย้อนกลับ)
                for col_idx in range(len(columns) - 1, -1, -1):
                    col = columns[col_idx].strip()
                    logger.info(f"🔍 [DEBUG] ตรวจสอบคอลัมน์ {col_idx+1}: '{col}'")
                    
                    if not col or col == '':
                        continue
                    
                    # ข้ามคอลัมน์ที่มีข้อความ "8." หรือ "รวมยอด..." เพราะนั่นคือคอลัมน์แรก
                    if '8.' in col or 'รวมยอด' in col or 'รวมยอดภาษี' in col:
                        logger.info(f"🔍 [DEBUG] ข้ามคอลัมน์ {col_idx+1} เพราะมีข้อความ '8.' หรือ 'รวมยอด'")
                        continue
                    
                    # หาตัวเลขที่มี comma หรือจุดทศนิยม (รูปแบบจำนวนเงิน)
                    # รูปแบบ: 57,086.53 หรือ 57086.53
                    amount_match = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d{4,}(?:\.\d{2})?)', col)
                    if amount_match:
                        amount_str = amount_match.group(1).strip()
                        amount_clean = amount_str.replace(',', '')
                        logger.info(f"🔍 [DEBUG] พบตัวเลข: '{amount_str}' -> {amount_clean}")
                        try:
                            amount_value = float(amount_clean)
                            logger.info(f"🔍 [DEBUG] แปลงเป็นตัวเลขได้: {amount_value}")
                            # ตรวจสอบว่าเป็นตัวเลขเงินจริง (>= 10 เพื่อหลีกเลี่ยงเลข 1-9)
                            if amount_value >= 10:
                                amounts['รวมยอดภาษีที่นำส่งทั้งสิ้น (ภ.ง.ด.3)'] = amount_value
                                logger.info(f"✅ พบรวมยอดภาษีที่นำส่งทั้งสิ้น (ภ.ง.ด.3): {amount_value:,.2f}")
                                return amounts
                            else:
                                logger.info(f"🔍 [DEBUG] ค่า {amount_value} น้อยกว่า 10 ข้าม")
                        except ValueError as e:
                            logger.info(f"🔍 [DEBUG] ไม่สามารถแปลง '{amount_clean}' เป็นตัวเลขได้: {e}")
                            continue
                
                logger.warning(f"⚠️ [DEBUG] ไม่พบค่าที่ถูกต้องในคอลัมน์ใดๆ ของแถว")
            else:
                # ถ้าไม่มี pipe ให้อ่านจากรูปแบบข้อความธรรมดา
                # รูปแบบ: "8. รวมยอดภาษีที่นำส่งทั้งสิ้น คือ 57,086.53"
                amount_patterns = [
                    r'8\.\s*รวมยอดภาษีที่(?:นำ|น่า)ส่งทั้งสิ้น\s*(?:คือ|:)\s*([\d,]+\.?\d*)',
                    r'รวมยอดภาษีที่(?:นำ|น่า)ส่งทั้งสิ้น\s*(?:คือ|:)\s*([\d,]+\.?\d*)',
                ]
                
                for pattern in amount_patterns:
                    match = re.search(pattern, row, re.IGNORECASE)
                    if match:
                        amount_str = match.group(1).strip()
                        amount_clean = amount_str.replace(',', '')
                        try:
                            amount_value = float(amount_clean)
                            if amount_value >= 10:
                                amounts['รวมยอดภาษีที่นำส่งทั้งสิ้น (ภ.ง.ด.3)'] = amount_value
                                logger.info(f"✅ พบรวมยอดภาษีที่นำส่งทั้งสิ้น (ภ.ง.ด.3): {amount_value:,.2f}")
                                return amounts
                        except ValueError:
                            continue
        
        # Fallback: ลองหาจากรูปแบบอื่นๆ (ถ้ายังไม่เจอ)
        logger.info(f"🔍 [DEBUG] ลองหาแบบ fallback จากข้อความทั้งหมด...")
        
        # ลองหาจากทั้งข้อความโดยตรง (ไม่จำกัดเฉพาะแถว)
        # Pattern ที่เฉพาะเจาะจง: หา "8. รวมยอดภาษีที่นำส่งทั้งสิ้น" ตามด้วย pipe และตัวเลข
        # รูปแบบ: 8. รวมยอดภาษีที่นำส่งทั้งสิ้น  | | | 57,086.53
        
        # ลองหาโดยตรงจากข้อความทั้งหมด (ไม่ต้องแยกเป็นแถว)
        # Pattern 1: หาจากรูปแบบที่เฉพาะเจาะจง: 8. รวมยอด... | | | 57,086.53
        direct_pattern = r'8\.\s*รวมยอดภาษีที่(?:นำ|น่า)ส่งทั้งสิ้น\s*\|\s*\|\s*\|\s*([\d,]+\.\d{2})'
        match = re.search(direct_pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            amount_str = match.group(1).strip()
            amount_clean = amount_str.replace(',', '')
            logger.info(f"🔍 [DEBUG] [Fallback Direct] พบตัวเลข: '{amount_str}' -> {amount_clean}")
            try:
                amount_value = float(amount_clean)
                if amount_value >= 10:
                    amounts['รวมยอดภาษีที่นำส่งทั้งสิ้น (ภ.ง.ด.3)'] = amount_value
                    logger.info(f"✅ [Fallback Direct] พบรวมยอดภาษีที่นำส่งทั้งสิ้น (ภ.ง.ด.3): {amount_value:,.2f}")
                    return amounts
            except ValueError:
                pass
        
        # Pattern 2: ลองหาจากข้อความที่อาจมีการแบ่งบรรทัด
        fallback_patterns = [
            # Pattern สำหรับตารางที่มี pipe: 8. รวมยอด... | | | 57,086.53
            r'8\.\s*รวมยอดภาษีที่(?:นำ|น่า)ส่งทั้งสิ้น[^|]*\|\s*\|\s*\|\s*([\d,]+\.\d{2})',
            r'8\s*\.\s*รวมยอดภาษีที่(?:นำ|น่า)ส่งทั้งสิ้น[^|]*\|\s*\|\s*\|\s*([\d,]+\.\d{2})',
            # Pattern ที่ไม่ต้องมี 8. ข้างหน้า
            r'รวมยอดภาษีที่(?:นำ|น่า)ส่งทั้งสิ้น[^|]*\|\s*\|\s*\|\s*([\d,]+\.\d{2})',
            # Pattern สำหรับจำนวนเงินที่มี comma และจุดทศนิยม 2 ตำแหน่ง
            r'8\.\s*รวมยอดภาษีที่(?:นำ|น่า)ส่งทั้งสิ้น[^0-9]*([\d,]+\.\d{2})',
        ]
        
        for pattern_idx, pattern in enumerate(fallback_patterns):
            logger.info(f"🔍 [DEBUG] [Fallback] ลองใช้ pattern {pattern_idx+1}: {pattern[:80]}...")
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                amount_str = match.group(1).strip()
                logger.info(f"🔍 [DEBUG] [Fallback] Pattern {pattern_idx+1} match ได้: '{amount_str}'")
                
                # ตรวจสอบว่าไม่ใช่แค่ตัวเลขลำดับ (เช่น "6.", "8.")
                if amount_str.endswith('.') and len(amount_str) <= 3:
                    logger.info(f"🔍 [DEBUG] [Fallback] ข้ามค่า '{amount_str}' เพราะเป็นเลขลำดับ")
                    continue
                
                # ตรวจสอบว่ามีจุดทศนิยม 2 ตำแหน่ง (เพื่อให้แน่ใจว่าเป็นจำนวนเงิน)
                if '.' in amount_str and len(amount_str.split('.')[-1]) == 2:
                    amount_clean = amount_str.replace(',', '')
                    logger.info(f"🔍 [DEBUG] [Fallback] พบตัวเลข: '{amount_str}' -> {amount_clean}")
                    try:
                        amount_value = float(amount_clean)
                        if amount_value >= 10:
                            amounts['รวมยอดภาษีที่นำส่งทั้งสิ้น (ภ.ง.ด.3)'] = amount_value
                            logger.info(f"✅ [Fallback] พบรวมยอดภาษีที่นำส่งทั้งสิ้น (ภ.ง.ด.3): {amount_value:,.2f}")
                            return amounts
                    except ValueError as e:
                        logger.info(f"🔍 [DEBUG] [Fallback] ไม่สามารถแปลง '{amount_clean}' เป็นตัวเลขได้: {e}")
                        continue
        
        # Pattern สำหรับ ภ.ง.ด.3: "4. รวมยอดภาษีที่นำส่งทั้งสิ้น และเงินเพิ่ม (2. + 3.) 59,570.36"
        # หรือ "2. รวมยอดภาษีที่นำส่งทั้งสิ้น 59,570.36"
        pnd3_fallback_patterns = [
            r'4\.\s*รวมยอดภาษีที่(?:นำ|น่า)ส่งทั้งสิ้น\s+และเงินเพิ่ม[^0-9]*([\d,]+\.\d{2})',
            r'4\s*\.\s*รวมยอดภาษีที่(?:นำ|น่า)ส่งทั้งสิ้น\s+และเงินเพิ่ม[^0-9]*([\d,]+\.\d{2})',
            r'2\.\s*รวมยอดภาษีที่(?:นำ|น่า)ส่งทั้งสิ้น[^0-9]*([\d,]+\.\d{2})',
            r'2\s*\.\s*รวมยอดภาษีที่(?:นำ|น่า)ส่งทั้งสิ้น[^0-9]*([\d,]+\.\d{2})',
            # Pattern ที่รองรับกรณีที่มี --- หรือช่องว่างมาก
            r'4\.\s*รวมยอดภาษีที่(?:นำ|น่า)ส่งทั้งสิ้น\s+และเงินเพิ่ม.*?([\d,]+\.\d{2})',
            r'2\.\s*รวมยอดภาษีที่(?:นำ|น่า)ส่งทั้งสิ้น.*?([\d,]+\.\d{2})',
        ]
        
        logger.info(f"🔍 [DEBUG] [Fallback PND3] กำลังค้นหา pattern สำหรับ ภ.ง.ด.3...")
        for pattern_idx, pattern in enumerate(pnd3_fallback_patterns):
            logger.info(f"🔍 [DEBUG] [Fallback PND3] ลองใช้ pattern {pattern_idx+1}: {pattern[:80]}...")
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                amount_str = match.group(1).strip()
                logger.info(f"🔍 [DEBUG] [Fallback PND3] Pattern {pattern_idx+1} match ได้: '{amount_str}'")
                amount_clean = amount_str.replace(',', '')
                try:
                    amount_value = float(amount_clean)
                    if amount_value >= 10:
                        amounts['รวมยอดภาษีที่นำส่งทั้งสิ้น (ภ.ง.ด.3)'] = amount_value
                        logger.info(f"✅ [Fallback PND3] พบรวมยอดภาษีที่นำส่งทั้งสิ้น (ภ.ง.ด.3): {amount_value:,.2f}")
                        return amounts
                except ValueError as e:
                    logger.info(f"🔍 [DEBUG] [Fallback PND3] ไม่สามารถแปลง '{amount_clean}' เป็นตัวเลขได้: {e}")
                    continue
        
        logger.warning(f"⚠️ [DEBUG] ไม่พบยอดเงิน 'รวมยอดภาษีที่นำส่งทั้งสิ้น' ใน ภ.ง.ด.3")
        logger.info(f"🔍 [DEBUG] ข้อความที่ค้นหา (200 ตัวอักษรสุดท้าย): ...{text[-200:]}")
        return amounts
    
    def _parse_payin(self, text: str, formatted_text: str) -> Dict[str, Any]:
        """Parse ข้อมูล Pay-in ชำระภาษี"""
        data = self._parse_basic_info(text, formatted_text)
        data['tax_form_type'] = 'Pay-in ชำระภาษี'
        
        # ✅ Parse Tax ID จาก Pay-in (รูปแบบ: เลขประจำตัวผู้เสียภาษีอากร [REF1] Customer No. 0105553114437)
        if not data.get('tax_id'):
            tax_id_patterns = [
                r'เลขประจำตัวผู้เสียภาษีอากร[^\d]*Customer\s*No\.\s*(\d{13})',  # รูปแบบ: เลขประจำตัวผู้เสียภาษีอากร [REF1] Customer No. 0105553114437
                r'เลขประจำตัวผู้เสียภาษีอากร[^\|]*\|\s*(\d{13})',  # มี | คั่น
                r'เลขประจำตัวผู้เสียภาษีอากร[^\d]*(\d{13})',  # ไม่มี |
                r'Tax\s*ID[^\|]*\|\s*(\d{13})',  # มี | คั่น (อังกฤษ)
                r'Tax\s*ID[^\d]*(\d{13})',  # ไม่มี | (อังกฤษ)
                r'Customer\s*No\.\s*(\d{13})',  # Customer No. 0105553114437
                r'^(\d{13})\s*\|',  # เลขขึ้นต้นบรรทัดตามด้วย |
                r'\|\s*(\d{13})\s*\|',  # เลขอยู่ระหว่าง | สองอัน
            ]
            
            # ใช้ formatted_text แทน text เพื่อให้ได้ข้อมูลที่ถูก format แล้ว
            search_text = formatted_text if formatted_text else text
            for pattern in tax_id_patterns:
                match = re.search(pattern, search_text, re.MULTILINE)
                if match:
                    tax_id_raw = match.group(1).strip()
                    if len(tax_id_raw) == 13:
                        # จัดรูปแบบเป็น X-XXXX-XXXXX-XX-X
                        tax_id_formatted = f"{tax_id_raw[0]}-{tax_id_raw[1:5]}-{tax_id_raw[5:10]}-{tax_id_raw[10:12]}-{tax_id_raw[12]}"
                        data['tax_id'] = tax_id_formatted
                        logger.info(f"✅ [Pay-in] พบ Tax ID: {tax_id_formatted}")
                        break
        
        # ✅ Parse Company Name จาก Pay-in (รูปแบบ: === ชื่อ Name === บริษัท ... จำกัด)
        if not data.get('company_name'):
            company_patterns = [
                # Pattern 1: === ชื่อ Name === บริษัท ... จำกัด (สำหรับ Pay-in ภาษี)
                r'===\s*ชื่อ\s*Name\s*===\s*(บริษัท\s+[^\n]+?จำกัด(?:\s+(?:มหาชน|\(มหาชน\)))?)',
                r'ชื่อ\s*Name\s*===\s*(บริษัท\s+[^\n]+?จำกัด(?:\s+(?:มหาชน|\(มหาชน\)))?)',
                # Pattern 2: ชื่อหน่วยงาน บริษัท... (สำหรับ Pay-in กองทุน กยศ.)
                r'ชื่อหน่วยงาน\s+(บริษัท[^\n\r]+?จำกัด(?:\s+(?:มหาชน|\(มหาชน\)))?)',
                # Pattern 3: ชื่อหน่วยงาน | บริษัท... (มี | คั่น)
                r'ชื่อหน่วยงาน[^\|]*\|\s*(บริษัท[^\n\r]+?จำกัด(?:\s+(?:มหาชน|\(มหาชน\)))?)',
                # Pattern 4: ชื่อ Name | บริษัท... (สำหรับ Pay-in ภาษี)
                r'ชื่อ\s*Name[^\|]*\|\s*(บริษัท\s+[^\|]+?จำกัด(?:\s+(?:มหาชน|\(มหาชน\)))?)',
                r'ชื่อ[^\|]*\|\s*(บริษัท\s+[^\|]+?จำกัด(?:\s+(?:มหาชน|\(มหาชน\)))?)',
                r'Name[^\|]*\|\s*(บริษัท\s+[^\|]+?จำกัด(?:\s+(?:มหาชน|\(มหาชน\)))?)',
            ]
            
            # ใช้ formatted_text แทน text เพื่อให้ได้ข้อมูลที่ถูก format แล้ว
            search_text = formatted_text if formatted_text else text
            for pattern in company_patterns:
                match = re.search(pattern, search_text, re.IGNORECASE | re.MULTILINE)
                if match:
                    company_name = match.group(1).strip()
                    # ทำความสะอาด
                    company_name = re.sub(r'\s+', ' ', company_name)
                    company_name = re.sub(r'[=*]+', '', company_name)
                    company_name = company_name.replace('|', '').strip()
                    
                    if 'บริษัท' in company_name:
                        data['company_name'] = company_name
                        logger.info(f"✅ [Pay-in] พบชื่อบริษัท: {company_name}")
                        break
        
        # Parse วันที่ครบกำหนดชำระจาก "=== 17 พฤศจิกายน 2,568 ==="
        if 'due_date' not in data or not data['due_date']:
            due_date_patterns = [
                r'===\s*(\d{1,2})\s+([มกกุมภาพันธ์มีนาคมเมษายนพฤษภาคมมิถุนายนกรกฎาคมสิงหาคมกันยายนตุลาคมพฤศจิกายนธันวาคม]+)\s+([\d,]+)\s*===',
                r'===\s*(\d{1,2})\s+([มกกุมภาพันธ์มีนาคมเมษายนพฤษภาคมมิถุนายนกรกฎาคมสิงหาคมกันยายนตุลาคมพฤศจิกายนธันวาคม]+)\s+([\d,]+)',
                r'(\d{1,2})\s+([มกกุมภาพันธ์มีนาคมเมษายนพฤษภาคมมิถุนายนกรกฎาคมสิงหาคมกันยายนตุลาคมพฤศจิกายนธันวาคม]+)\s+([\d,]+)',
            ]
            
            # Map ชื่อเดือนเป็นตัวเลข
            month_mapping = {
                'มกราคม': '01', 'กุมภาพันธ์': '02', 'มีนาคม': '03', 'เมษายน': '04',
                'พฤษภาคม': '05', 'มิถุนายน': '06', 'กรกฎาคม': '07', 'สิงหาคม': '08',
                'กันยายน': '09', 'ตุลาคม': '10', 'พฤศจิกายน': '11', 'ธันวาคม': '12',
            }
            
            for pattern in due_date_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    day = match.group(1).strip()
                    month_name = match.group(2).strip()
                    year_str = match.group(3).strip().replace(',', '')
                    
                    # หาเลขเดือนจากชื่อเดือน
                    month_num = None
                    for thai_month, num in month_mapping.items():
                        if thai_month in month_name:
                            month_num = num
                            break
                    
                    if month_num:
                        try:
                            year_value = int(year_str)
                            # ถ้าปีน้อยกว่า 2500 ให้บวก 2500 (เช่น 68 -> 2568)
                            if year_value < 2500:
                                year_value = 2500 + year_value
                            
                            # Format เป็น DD/MM/YYYY
                            due_date = f"{day.zfill(2)}/{month_num}/{year_value}"
                            data['due_date'] = due_date
                            logger.info(f"✅ พบวันที่ครบกำหนดชำระ (Pay-in): {due_date}")
                            
                            # แปลงเป็น filing_period โดยย้อนหลัง 1 เดือน
                            # Map ชื่อเดือนไทยเป็นชื่อเดือนสำหรับ filing_period
                            month_name_mapping = {
                                'มกราคม': 'มกราคม', 'กุมภาพันธ์': 'กุมภาพันธ์', 
                                'มีนาคม': 'มีนาคม', 'เมษายน': 'เมษายน',
                                'พฤษภาคม': 'พฤษภาคม', 'มิถุนายน': 'มิถุนายน', 
                                'กรกฎาคม': 'กรกฎาคม', 'สิงหาคม': 'สิงหาคม',
                                'กันยายน': 'กันยายน', 'ตุลาคม': 'ตุลาคม', 
                                'พฤศจิกายน': 'พฤศจิกายน', 'ธันวาคม': 'ธันวาคม',
                            }
                            
                            # Map ตัวเลขเดือนเป็นชื่อเดือน (ย้อนหลัง 1 เดือน)
                            filing_month_mapping = {
                                '01': 'ธันวาคม', '02': 'มกราคม', '03': 'กุมภาพันธ์', '04': 'มีนาคม',
                                '05': 'เมษายน', '06': 'พฤษภาคม', '07': 'มิถุนายน', '08': 'กรกฎาคม',
                                '09': 'สิงหาคม', '10': 'กันยายน', '11': 'ตุลาคม', '12': 'พฤศจิกายน',
                            }
                            
                            # Map ตัวเลขเดือนเป็นชื่อเดือน (ย้อนหลัง 1 เดือน) และปรับปีถ้าจำเป็น
                            filing_month = filing_month_mapping.get(month_num)
                            filing_year = year_value
                            
                            # ถ้าเดือนเป็นมกราคม (01) ให้ย้อนปีกลับ 1 ปี
                            if month_num == '01':
                                filing_year = year_value - 1
                            
                            if filing_month:
                                data['filing_period']['month'] = filing_month
                                data['filing_period']['year'] = filing_year
                                logger.info(f"✅ พบ filing_period (Pay-in): {filing_month} {filing_year} (ย้อนหลัง 1 เดือนจาก {month_name})")
                            
                            break
                        except ValueError:
                            continue
        
        # Parse ข้อมูลเฉพาะ Pay-in
        amounts = self._parse_payin_amounts(text)
        data['amounts'] = amounts
        
        return data
    
    def _parse_payin_amounts(self, text: str) -> Dict[str, float]:
        """Parse ยอดเงินจาก Pay-in"""
        amounts = {}
        
        logger.info(f"🔍 [DEBUG] เริ่ม parse ยอดเงิน Pay-in")
        
        # หา "ยอดชำระ (บาท) Paid Amount (baht)" จากตาราง
        # รูปแบบ: 105,553,114,437 | 105,553,114,437 | 154,500.61 |
        # ต้องการคอลัมน์สุดท้ายที่มีตัวเลขทศนิยม (154,500.61)
        
        # หาแถวที่มี header "ยอดชำระ (บาท)" หรือ "Paid Amount"
        header_patterns = [
            r'ยอดชำระ\s*\(บาท\)\s*Paid\s*Amount',
            r'ยอดชำระ\s*\(บาท\)',
            r'Paid\s*Amount',
        ]
        
        header_row_idx = None
        all_rows = [row.strip() for row in text.split('\n') if row.strip()]
        
        for idx, row in enumerate(all_rows):
            for pattern in header_patterns:
                if re.search(pattern, row, re.IGNORECASE):
                    header_row_idx = idx
                    logger.info(f"🔍 [DEBUG] พบ header ที่แถว {idx+1}: {row[:100]}")
                    break
            if header_row_idx is not None:
                break
        
        if header_row_idx is not None:
            # หาแถวข้อมูลที่อยู่ถัดจาก header (ข้าม separator line ถ้ามี)
            data_start_idx = header_row_idx + 1
            
            # ข้าม separator line (เช่น ----- หรือ ===)
            while data_start_idx < len(all_rows):
                row = all_rows[data_start_idx]
                if re.search(r'^[-=]+$', row):
                    data_start_idx += 1
                    continue
                break
            
            # อ่านแถวข้อมูล (อาจมีหลายแถว)
            for idx in range(data_start_idx, min(data_start_idx + 5, len(all_rows))):
                row = all_rows[idx]
                
                # ตรวจสอบว่ามี pipe (|) แสดงว่าเป็นแถวตาราง
                if '|' in row:
                    columns = [col.strip() for col in re.split(r'\s*\|\s*', row)]
                    logger.info(f"🔍 [DEBUG] พบแถวข้อมูล {idx+1}: {len(columns)} คอลัมน์")
                    logger.info(f"🔍 [DEBUG] คอลัมน์ทั้งหมด: {columns}")
                    
                    # หาคอลัมน์สุดท้ายที่มีตัวเลขทศนิยม (ยอดชำระ)
                    # เริ่มจากคอลัมน์สุดท้ายย้อนกลับ
                    for col_idx in range(len(columns) - 1, -1, -1):
                        col = columns[col_idx].strip()
                        
                        if not col:
                            continue
                        
                        # หาตัวเลขทศนิยม (รูปแบบ: 154,500.61 หรือ 154500.61)
                        amount_match = re.search(r'([\d,]+\.\d{2})', col)
                        if amount_match:
                            amount_str = amount_match.group(1).strip()
                            amount_clean = amount_str.replace(',', '')
                            
                            logger.info(f"🔍 [DEBUG] พบตัวเลขในคอลัมน์ {col_idx+1}: '{amount_str}' -> {amount_clean}")
                            
                            try:
                                amount_value = float(amount_clean)
                                # ตรวจสอบว่าเป็นตัวเลขเงินจริง (>= 10)
                                if amount_value >= 10:
                                    amounts['ยอดชำระ (บาท)'] = amount_value
                                    logger.info(f"✅ พบยอดชำระ (บาท) (Pay-in): {amount_value:,.2f}")
                                    return amounts
                            except ValueError as e:
                                logger.info(f"🔍 [DEBUG] ไม่สามารถแปลง '{amount_clean}' เป็นตัวเลขได้: {e}")
                                continue
        
        # Fallback: ลองหาจากรูปแบบอื่นๆ (ไม่ต้องมี header)
        logger.info(f"🔍 [DEBUG] ลองหาแบบ fallback...")
        
        # Pattern fallback: หาตัวเลขทศนิยมที่อยู่หลัง pipe หลายตัว (น่าจะเป็นคอลัมน์สุดท้าย)
        fallback_patterns = [
            r'[\d,]+\s*\|\s*[\d,]+\s*\|\s*([\d,]+\.\d{2})',
            r'[\d,]+\s*\|\s*([\d,]+\.\d{2})',
            r'ยอดชำระ[^\d]*([\d,]+\.\d{2})',
        ]
        
        for pattern in fallback_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                amount_str = match.group(1).strip()
                amount_clean = amount_str.replace(',', '')
                
                logger.info(f"🔍 [DEBUG] [Fallback] พบ pattern: amount_str='{amount_str}', amount_clean='{amount_clean}'")
                
                try:
                    amount_value = float(amount_clean)
                    if amount_value >= 10:
                        amounts['ยอดชำระ (บาท)'] = amount_value
                        logger.info(f"✅ [Fallback] พบยอดชำระ (บาท) (Pay-in): {amount_value:,.2f}")
                        return amounts
                except ValueError:
                    continue
        
        logger.warning(f"⚠️ [DEBUG] ไม่พบยอดเงิน 'ยอดชำระ (บาท)' ใน Pay-in")
        return amounts
    
    def _parse_student_loan(self, text: str, formatted_text: str) -> Dict[str, Any]:
        """Parse ข้อมูลกองทุน กยศ."""
        data = self._parse_basic_info(text, formatted_text)
        data['tax_form_type'] = 'กองทุน กยศ.'
        
        # Parse เดือนและปีจาก "ชำระเงินของเดือน 10/2,568"
        if not data['filing_period']['month'] or not data['filing_period']['year']:
            # Pattern: ชำระเงินของเดือน 10/2,568 (รองรับ comma ในปี)
            month_year_pattern = r'ชำระเงินของเดือน\s+(\d{1,2})/([\d,]+)'
            match = re.search(month_year_pattern, text, re.IGNORECASE)
            if match:
                month_num = match.group(1).strip()
                year_str = match.group(2).strip().replace(',', '')
                
                # Map ตัวเลขเดือนเป็นชื่อเดือน
                month_mapping = {
                    '1': 'มกราคม', '2': 'กุมภาพันธ์', '3': 'มีนาคม', '4': 'เมษายน',
                    '5': 'พฤษภาคม', '6': 'มิถุนายน', '7': 'กรกฎาคม', '8': 'สิงหาคม',
                    '9': 'กันยายน', '10': 'ตุลาคม', '11': 'พฤศจิกายน', '12': 'ธันวาคม',
                }
                
                if month_num in month_mapping:
                    data['filing_period']['month'] = month_mapping[month_num]
                    logger.info(f"✅ พบเดือนจาก 'ชำระเงินของเดือน': {data['filing_period']['month']}")
                
                try:
                    year_value = int(year_str)
                    # ถ้าปีน้อยกว่า 2500 ให้บวก 2500 (เช่น 68 -> 2568)
                    if year_value < 2500:
                        year_value = 2500 + year_value
                    data['filing_period']['year'] = year_value
                    logger.info(f"✅ พบปีจาก 'ชำระเงินของเดือน': {year_value}")
                except ValueError:
                    pass
        
        # Parse วันที่ครบกำหนดชำระเงินจาก "* วันที่ครบกำหนดชำระเงิน | 17/11/2,568"
        if 'due_date' not in data or not data['due_date']:
            due_date_patterns = [
                r'\*\s*วันที่ครบกำหนดชำระเงิน\s*\|\s*(\d{1,2})/(\d{1,2})/([\d,]+)',
                r'วันที่ครบกำหนดชำระเงิน\s*\|\s*(\d{1,2})/(\d{1,2})/([\d,]+)',
                r'วันที่ครบกำหนดชำระเงิน[^\d]*(\d{1,2})/(\d{1,2})/([\d,]+)',
            ]
            
            for pattern in due_date_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    day = match.group(1).strip()
                    month = match.group(2).strip()
                    year_str = match.group(3).strip().replace(',', '')
                    
                    try:
                        year_value = int(year_str)
                        # ถ้าปีน้อยกว่า 2500 ให้บวก 2500 (เช่น 68 -> 2568)
                        if year_value < 2500:
                            year_value = 2500 + year_value
                        
                        # Format เป็น DD/MM/YYYY
                        due_date = f"{day.zfill(2)}/{month.zfill(2)}/{year_value}"
                        data['due_date'] = due_date
                        logger.info(f"✅ พบวันที่ครบกำหนดชำระเงิน: {due_date}")
                        break
                    except ValueError:
                        continue
        
        # Parse ข้อมูลเฉพาะกองทุน กยศ.
        amounts = self._parse_student_loan_amounts(text)
        data['amounts'] = amounts
        
        return data
    
    def _parse_student_loan_amounts(self, text: str) -> Dict[str, float]:
        """Parse ยอดเงินจากกองทุน กยศ."""
        amounts = {}
        
        logger.info(f"🔍 [DEBUG] เริ่ม parse ยอดเงิน กองทุน กยศ.")
        
        # หา "ยอดชำระ (บาท) 4,024.00"
        patterns = [
            r'ยอดชำระ\s*\(บาท\)\s*([\d,]+\.\d{2})',
            r'ยอดชำระ\s*\(บาท\)[^\d]*([\d,]+\.\d{2})',
            r'ยอดชำระ\s*\(บาท\)\s*([\d,]+\.\d{1,2})',
            r'ยอดชำระ\s*\(บาท\)[^\d]*([\d,]+\.\d{1,2})',
            r'ยอดชำระ[^\d]*([\d,]+\.\d{2})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                amount_str = match.group(1).strip()
                # ลบ comma
                amount_clean = amount_str.replace(',', '')
                
                logger.info(f"🔍 [DEBUG] พบ pattern: amount_str='{amount_str}', amount_clean='{amount_clean}'")
                
                try:
                    amount_value = float(amount_clean)
                    if amount_value >= 0:
                        amounts['ยอดชำระ (บาท)'] = amount_value
                        logger.info(f"✅ พบยอดชำระ (บาท): {amount_value:,.2f}")
                        return amounts
                except ValueError as e:
                    logger.warning(f"⚠️ ไม่สามารถแปลง '{amount_clean}' เป็นตัวเลขได้: {e}")
                    continue
        
        # Fallback: ลองหาจากรูปแบบอื่นๆ
        logger.info(f"🔍 [DEBUG] ลองหาแบบ fallback...")
        
        fallback_patterns = [
            r'ยอดชำระ[^\d]*([\d,]+\.\d{2})',
            r'ชำระ[^\d]*([\d,]+\.\d{2})',
        ]
        
        for pattern in fallback_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                amount_str = match.group(1).strip()
                amount_clean = amount_str.replace(',', '')
                
                logger.info(f"🔍 [DEBUG] [Fallback] พบ pattern: amount_str='{amount_str}', amount_clean='{amount_clean}'")
                
                try:
                    amount_value = float(amount_clean)
                    if amount_value >= 0:
                        amounts['ยอดชำระ (บาท)'] = amount_value
                        logger.info(f"✅ [Fallback] พบยอดชำระ (บาท): {amount_value:,.2f}")
                        return amounts
                except ValueError:
                    continue
        
        logger.warning(f"⚠️ [DEBUG] ไม่พบยอดเงิน 'ยอดชำระ (บาท)' ใน กองทุน กยศ.")
        return amounts
    
    def _parse_social_security(self, text: str, formatted_text: str) -> Dict[str, Any]:
        """Parse ข้อมูลประกันสังคม"""
        data = self._parse_basic_info(text, formatted_text)
        data['tax_form_type'] = 'ประกันสังคม'
        
        # ดึง company_name จาก "ชื่อสถานประกอบการ: === บริษัท ไอสาม เกทเวย์ จำกัด"
        if not data.get('company_name'):
            company_patterns = [
                r'ชื่อสถานประกอบการ[^\n]*?[:：]\s*===\s*(บริษัท\s+[^\n]+?จำกัด(?:\s+(?:มหาชน|\(มหาชน\)))?)',
                r'ชื่อสถานประกอบการ[^\n]*?[:：]\s*(?:=+\s*)?(?:[*]+\s*)?(บริษัท\s+[^\n]+?จำกัด(?:\s+(?:มหาชน|\(มหาชน\)))?)',
            ]
            
            # ลองหาใน formatted_text ก่อน
            for pattern in company_patterns:
                match = re.search(pattern, formatted_text if formatted_text else text, re.IGNORECASE | re.MULTILINE)
                if match:
                    company_name = match.group(1).strip()
                    company_name = re.sub(r'\s+', ' ', company_name)
                    company_name = re.sub(r'[=*]+', '', company_name)
                    company_name = company_name.strip()
                    if company_name and 'บริษัท' in company_name:
                        data['company_name'] = company_name
                        logger.info(f"✅ [ประกันสังคม] พบชื่อบริษัท: {company_name}")
                        break
        
        # ดึง month จาก "การนำส่งเงินสมทบสำหรับค่าจ้างเดือน: === ตุลาคม"
        if not data['filing_period']['month']:
            month_patterns = [
                r'การนำส่งเงินสมทบสำหรับค่าจ้างเดือน[^\n]*?[:：]\s*===\s*([มกกุมภาพันธ์มีนาคมเมษายนพฤษภาคมมิถุนายนกรกฎาคมสิงหาคมกันยายนตุลาคมพฤศจิกายนธันวาคม]+)',
                r'การนำส่งเงินสมทบสำหรับค่าจ้างเดือน[^\n]*?[:：]\s*(?:=+\s*)?(?:[*]+\s*)?([มกกุมภาพันธ์มีนาคมเมษายนพฤษภาคมมิถุนายนกรกฎาคมสิงหาคมกันยายนตุลาคมพฤศจิกายนธันวาคม]+)',
            ]
            
            # ลองหาใน formatted_text ก่อน
            for pattern in month_patterns:
                match = re.search(pattern, formatted_text if formatted_text else text, re.IGNORECASE | re.MULTILINE)
                if match:
                    month_name = match.group(1).strip()
                    month_name = re.sub(r'[=*\s]+', '', month_name)
                    if month_name:
                        data['filing_period']['month'] = month_name
                        logger.info(f"✅ [ประกันสังคม] พบเดือน: {month_name}")
                        break
        
        # Parse ข้อมูลเฉพาะประกันสังคม (ใช้ formatted_text แทน text)
        amounts = self._parse_social_security_amounts(formatted_text if formatted_text else text)
        data['amounts'] = amounts
        
        return data
    
    def _parse_social_security_amounts(self, text: str) -> Dict[str, float]:
        """Parse ยอดเงินจากประกันสังคม"""
        amounts = {}
        
        logger.info(f"🔍 [DEBUG] เริ่ม parse ยอดเงิน ประกันสังคม")
        
        # หา "4. รวมเงินสมทบที่นำส่งทั้งสิ้น | 37,334 | 00"
        # 37,334 คือส่วนหลัก, 00 คือจุดทศนิยม (เศษสตางค์)
        # ผลลัพธ์: 37,334.00
        
        # Pattern หลัก: หา "4. รวมเงินสมทบที่นำส่งทั้งสิ้น" ตามด้วย pipe และตัวเลข
        patterns = [
            r'4\.\s*รวมเงินสมทบที่นำส่งทั้งสิ้น\s*\|\s*([\d,]+)\s*\|\s*(\d{2})',
            r'4\.\s*รวมเงินสมทบที่นำส่งทั้งสิ้น[^\|]*\|\s*([\d,]+)\s*\|\s*(\d{2})',
            r'รวมเงินสมทบที่นำส่งทั้งสิ้น\s*\|\s*([\d,]+)\s*\|\s*(\d{2})',
            r'รวมเงินสมทบที่นำส่งทั้งสิ้น[^\|]*\|\s*([\d,]+)\s*\|\s*(\d{2})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                main_part = match.group(1).strip()
                decimal_part = match.group(2).strip()
                
                logger.info(f"🔍 [DEBUG] พบ pattern: main_part='{main_part}', decimal_part='{decimal_part}'")
                
                # ลบ comma จากส่วนหลัก
                main_clean = main_part.replace(',', '')
                
                # รวมเป็นตัวเลขทศนิยม
                amount_str = f"{main_clean}.{decimal_part}"
                
                try:
                    amount_value = float(amount_str)
                    if amount_value >= 0:
                        amounts['รวมเงินสมทบที่นำส่งทั้งสิ้น (ประกันสังคม)'] = amount_value
                        logger.info(f"✅ พบรวมเงินสมทบที่นำส่งทั้งสิ้น (ประกันสังคม): {amount_value:,.2f}")
                        return amounts
                except ValueError as e:
                    logger.warning(f"⚠️ ไม่สามารถแปลง '{amount_str}' เป็นตัวเลขได้: {e}")
                    continue
        
        # Fallback: ลองหาจากรูปแบบอื่นๆ (กรณีที่ไม่มี pipe หรือรูปแบบต่างออกไป)
        logger.info(f"🔍 [DEBUG] ลองหาแบบ fallback...")
        
        # Pattern fallback 1: หาจากรูปแบบที่มี pipe แต่ไม่มีเลข 4. ข้างหน้า
        # Pattern fallback 2: หาจากรูปแบบที่ไม่มี pipe (อาจเป็นข้อความธรรมดา)
        # Pattern fallback 3: หาจากรูปแบบ "4. รวมเงินสมทบที่นำส่งทั้งสิ้น 37,334 00" (ไม่มี pipe, มีช่องว่างระหว่างตัวเลข)
        fallback_patterns = [
            r'รวมเงินสมทบที่นำส่งทั้งสิ้น[^\d]*([\d,]+)\s*\|\s*(\d{2})',
            r'รวมเงินสมทบ[^\d]*([\d,]+)\s*\|\s*(\d{2})',
            r'4\.\s*รวมเงินสมทบที่นำส่งทั้งสิ้น[^\d]*([\d,]+)\.(\d{2})',
            r'รวมเงินสมทบที่นำส่งทั้งสิ้น[^\d]*([\d,]+)\.(\d{2})',
            r'4\.\s*รวมเงินสมทบที่นำส่งทั้งสิ้น[^\d]*([\d,]+)\s+(\d{2})',
            r'รวมเงินสมทบที่นำส่งทั้งสิ้น[^\d]*([\d,]+)\s+(\d{2})',
        ]
        
        for pattern in fallback_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                main_part = match.group(1).strip()
                decimal_part = match.group(2).strip()
                
                logger.info(f"🔍 [DEBUG] [Fallback] พบ pattern: main_part='{main_part}', decimal_part='{decimal_part}'")
                
                # ลบ comma จากส่วนหลัก
                main_clean = main_part.replace(',', '')
                
                # รวมเป็นตัวเลขทศนิยม
                amount_str = f"{main_clean}.{decimal_part}"
                
                try:
                    amount_value = float(amount_str)
                    if amount_value >= 0:
                        amounts['รวมเงินสมทบที่นำส่งทั้งสิ้น (ประกันสังคม)'] = amount_value
                        logger.info(f"✅ [Fallback] พบรวมเงินสมทบที่นำส่งทั้งสิ้น (ประกันสังคม): {amount_value:,.2f}")
                        return amounts
                except ValueError:
                    continue
        
        logger.warning(f"⚠️ [DEBUG] ไม่พบยอดเงิน 'รวมเงินสมทบที่นำส่งทั้งสิ้น' ใน ประกันสังคม")
        return amounts


