"""
Invoice Extractor Manager
=========================
ตัวจัดการ Extractor ทั้งหมด

Author: BotV3
Version: 3.0.0
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class InvoiceExtractorManager:
    """ตัวจัดการ Extractor ทั้งหมด"""
    
    def __init__(self):
        """Initialize Manager"""
        # Import extractors (จะ import จาก extractors/__init__.py)
        from .extractors import EXTRACTORS
        
        # ใช้ extractors จาก extractors/__init__.py
        # ลำดับมีความสำคัญ: extractor ที่เฉพาะเจาะจงต้องอยู่ก่อน
        self.extractors = EXTRACTORS
    
    def validate_and_adjust_amounts(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        ตรวจสอบและปรับยอดเงินให้สอดคล้องกัน
        
        เงื่อนไข: ยอดก่อนภาษี + ยอดภาษี = ยอดรวม
        
        Args:
            data: Dictionary ที่มีข้อมูลที่ดึงได้ (ต้องมี amount_before_vat, vat_amount, total_amount)
        
        Returns:
            Dictionary ที่มีการปรับยอดเงินแล้ว (ถ้าจำเป็น)
        """
        # ตรวจสอบว่ามีข้อมูลที่จำเป็นหรือไม่
        if not data.get('success'):
            return data
        
        # ตรวจสอบ flag skip_amount_adjustment (สำหรับเอกสารไม่มีภาษีมูลค่าเพิ่ม - ใช้ค่าที่อ่านได้เท่านั้น)
        if data.get('skip_amount_adjustment', False):
            logger.info("ℹ️ ข้ามการปรับยอดเงิน (ใช้ค่าที่อ่านได้จากเอกสารเท่านั้น)")
            return data
        
        amount_before_vat = data.get('amount_before_vat')
        vat_amount = data.get('vat_amount')
        total_amount = data.get('total_amount')
        
        # ถ้าไม่มีข้อมูลยอดเงินเลย ไม่ต้องตรวจสอบ
        if amount_before_vat is None and vat_amount is None and total_amount is None:
            return data
        
        # แปลง None เป็น 0 สำหรับการคำนวณ
        pre_tax = amount_before_vat if amount_before_vat is not None else 0.0
        tax = vat_amount if vat_amount is not None else 0.0
        total = total_amount if total_amount is not None else 0.0
        
        # คำนวณยอดรวมที่ควรจะเป็น
        calculated_total = pre_tax + tax
        
        # ใช้ tolerance เล็กน้อยสำหรับ floating point comparison (0.01 บาท)
        tolerance = 0.01
        difference = abs(calculated_total - total)
        
        # ถ้ายอดรวมตรงกัน (ภายใน tolerance) ไม่ต้องปรับ
        if difference <= tolerance:
            logger.info(f"✅ ยอดเงินสอดคล้องกัน: {pre_tax} + {tax} = {total}")
            return data
        
        # ถ้ายอดรวมไม่ตรงกัน ต้องปรับค่า
        logger.warning(f"⚠️ ยอดเงินไม่สอดคล้องกัน: {pre_tax} + {tax} = {calculated_total} แต่ยอดรวมที่อ่านได้ = {total}")
        logger.info(f"🔧 กำลังปรับยอดเงินให้สอดคล้องกัน...")
        
        # กลยุทธ์การปรับค่า: ใช้ยอดรวมเป็นหลัก (ถ้ามี) เพราะมักจะอ่านได้ถูกต้องกว่า
        # 1. ถ้ามียอดรวม ให้ใช้ยอดรวมเป็นหลักและคำนวณยอดก่อนภาษีและยอดภาษีใหม่
        # 2. ถ้าไม่มียอดรวม แต่มียอดก่อนภาษีและยอดภาษี ให้คำนวณยอดรวมใหม่
        # 3. ถ้ามีแค่บางส่วน ให้คำนวณส่วนที่ขาด
        
        # กรณีพิเศษ: มียอดครบทั้ง 3 ส่วนแต่ไม่สอดคล้องกัน
        # ตรวจสอบว่ายอดรวมที่อ่านได้ใกล้เคียงกับยอดรวมที่คำนวณได้หรือไม่
        has_all_three = (pre_tax > 0 and tax > 0 and total > 0)
        
        if has_all_three:
            # มียอดครบทั้ง 3 ส่วน แต่ไม่สอดคล้องกัน
            # เปรียบเทียบความแตกต่างระหว่างยอดรวมที่อ่านได้กับยอดรวมที่คำนวณได้
            percent_diff = abs(difference / calculated_total * 100) if calculated_total > 0 else 100
            
            logger.info(f"📊 มียอดครบทั้ง 3 ส่วน แต่ไม่สอดคล้องกัน (ความแตกต่าง: {percent_diff:.2f}%)")
            
            # ถ้าความแตกต่างมากกว่า 10% อาจจะยอดรวมที่อ่านได้ผิด
            # แต่เราจะใช้ยอดรวมเป็นหลักเสมอ (เพราะมักจะอ่านได้ถูกต้องกว่า)
            # คำนวณยอดก่อนภาษีและยอดภาษีใหม่จากยอดรวม
            calculated_pre_tax = total / 1.07
            calculated_tax = total - calculated_pre_tax
            
            if calculated_pre_tax > 0 and calculated_tax >= 0:
                # บันทึกค่าก่อนปรับ
                old_pre_tax = pre_tax
                old_tax = tax
                
                # ใช้ค่าที่คำนวณได้จากยอดรวม
                data['amount_before_vat'] = round(calculated_pre_tax, 2)
                data['vat_amount'] = round(calculated_tax, 2)
                data['total_amount'] = round(total, 2)
                
                logger.info(f"✅ ปรับยอดเงินจากยอดรวม (มียอดครบแต่ไม่สอดคล้อง):")
                logger.info(f"   ยอดก่อนภาษี: {old_pre_tax} -> {data['amount_before_vat']}")
                logger.info(f"   ยอดภาษี: {old_tax} -> {data['vat_amount']}")
                logger.info(f"   ยอดรวม: {total} (ใช้ค่าที่อ่านได้)")
            else:
                # ถ้าค่าที่คำนวณได้ไม่สมเหตุสมผล ให้ใช้ยอดรวมที่คำนวณได้จาก pre_tax + tax
                calculated_total_new = pre_tax + tax
                data['total_amount'] = round(calculated_total_new, 2)
                logger.warning(f"⚠️ ค่าที่คำนวณจากยอดรวมไม่สมเหตุสมผล ใช้ยอดรวมที่คำนวณได้แทน: {data['total_amount']} = {pre_tax} + {tax}")
        
        elif total > 0:
            # กรณี: มียอดรวม -> ใช้ยอดรวมเป็นหลักและคำนวณยอดก่อนภาษีและยอดภาษีใหม่
            # สมมติว่ายอดภาษี = 7% ของยอดก่อนภาษี
            # total = pre_tax + (pre_tax * 0.07) = pre_tax * 1.07
            # ดังนั้น: pre_tax = total / 1.07
            calculated_pre_tax = total / 1.07
            calculated_tax = total - calculated_pre_tax
            
            # ตรวจสอบว่าค่าที่คำนวณได้สมเหตุสมผลหรือไม่
            if calculated_pre_tax > 0 and calculated_tax >= 0:
                # ใช้ค่าที่คำนวณได้
                data['amount_before_vat'] = round(calculated_pre_tax, 2)
                data['vat_amount'] = round(calculated_tax, 2)
                data['total_amount'] = round(total, 2)
                
                # แสดงข้อมูลการปรับค่า
                if pre_tax > 0 or tax > 0:
                    logger.info(f"✅ ปรับยอดเงินจากยอดรวม: ยอดก่อนภาษี = {pre_tax} -> {data['amount_before_vat']}, ยอดภาษี = {tax} -> {data['vat_amount']}, ยอดรวม = {total}")
                else:
                    logger.info(f"✅ คำนวณยอดเงินจากยอดรวม: ยอดก่อนภาษี = {data['amount_before_vat']}, ยอดภาษี = {data['vat_amount']}, ยอดรวม = {total}")
            else:
                # ถ้าค่าที่คำนวณได้ไม่สมเหตุสมผล ให้ลองใช้วิธีอื่น
                if pre_tax > 0:
                    # ถ้ามียอดก่อนภาษี ให้คำนวณยอดภาษีจากยอดรวม
                    adjusted_tax = total - pre_tax
                    if adjusted_tax >= 0:
                        data['vat_amount'] = round(adjusted_tax, 2)
                        data['total_amount'] = round(total, 2)
                        logger.info(f"✅ ปรับยอดภาษี: {tax} -> {data['vat_amount']} (ยอดรวม: {total}, ยอดก่อนภาษี: {pre_tax})")
                    else:
                        # ถ้ายอดภาษีติดลบ ให้ใช้ยอดรวมเป็นหลัก
                        data['amount_before_vat'] = round(calculated_pre_tax, 2)
                        data['vat_amount'] = round(calculated_tax, 2)
                        data['total_amount'] = round(total, 2)
                        logger.info(f"✅ ปรับยอดก่อนภาษีและยอดภาษี: ยอดก่อนภาษี = {pre_tax} -> {data['amount_before_vat']}, ยอดภาษี = {tax} -> {data['vat_amount']}, ยอดรวม = {total}")
                elif tax > 0:
                    # ถ้ามียอดภาษี ให้คำนวณยอดก่อนภาษีจากยอดรวม
                    adjusted_pre_tax = total - tax
                    if adjusted_pre_tax >= 0:
                        data['amount_before_vat'] = round(adjusted_pre_tax, 2)
                        data['total_amount'] = round(total, 2)
                        logger.info(f"✅ ปรับยอดก่อนภาษี: {pre_tax} -> {data['amount_before_vat']} (ยอดรวม: {total}, ยอดภาษี: {tax})")
                    else:
                        # ถ้ายอดก่อนภาษีติดลบ ให้ใช้ยอดรวมเป็นหลัก
                        data['amount_before_vat'] = round(calculated_pre_tax, 2)
                        data['vat_amount'] = round(calculated_tax, 2)
                        data['total_amount'] = round(total, 2)
                        logger.info(f"✅ ปรับยอดก่อนภาษีและยอดภาษี: ยอดก่อนภาษี = {pre_tax} -> {data['amount_before_vat']}, ยอดภาษี = {tax} -> {data['vat_amount']}, ยอดรวม = {total}")
                else:
                    # ไม่มียอดก่อนภาษีหรือยอดภาษีเลย ให้ใช้ค่าที่คำนวณได้
                    data['amount_before_vat'] = round(calculated_pre_tax, 2)
                    data['vat_amount'] = round(calculated_tax, 2)
                    data['total_amount'] = round(total, 2)
                    logger.info(f"✅ คำนวณยอดก่อนภาษีและยอดภาษี: ยอดก่อนภาษี = {data['amount_before_vat']}, ยอดภาษี = {data['vat_amount']}, ยอดรวม = {total}")
        
        elif pre_tax > 0 and tax > 0:
            # กรณี: มียอดก่อนภาษีและยอดภาษี แต่ไม่มียอดรวม -> คำนวณยอดรวมใหม่
            calculated_total_new = pre_tax + tax
            data['total_amount'] = round(calculated_total_new, 2)
            logger.info(f"✅ คำนวณยอดรวมใหม่: {data['total_amount']} = {pre_tax} + {tax}")
        
        elif pre_tax > 0:
            # กรณี: มีแค่อยอดก่อนภาษี -> คำนวณยอดภาษีและยอดรวมใหม่
            # สมมติว่ายอดภาษี = 7% ของยอดก่อนภาษี
            calculated_tax = pre_tax * 0.07
            calculated_total_new = pre_tax + calculated_tax
            data['vat_amount'] = round(calculated_tax, 2)
            data['total_amount'] = round(calculated_total_new, 2)
            logger.info(f"✅ คำนวณยอดภาษีและยอดรวม: ยอดภาษี = {data['vat_amount']} (7% ของ {pre_tax}), ยอดรวม = {data['total_amount']}")
        
        elif tax > 0:
            # กรณี: มีแค่อยอดภาษี -> คำนวณยอดก่อนภาษีและยอดรวมใหม่
            # ถ้ายอดภาษี = 7% ของยอดก่อนภาษี
            # tax = pre_tax * 0.07
            # ดังนั้น: pre_tax = tax / 0.07
            calculated_pre_tax = tax / 0.07
            calculated_total_new = calculated_pre_tax + tax
            data['amount_before_vat'] = round(calculated_pre_tax, 2)
            data['total_amount'] = round(calculated_total_new, 2)
            logger.info(f"✅ คำนวณยอดก่อนภาษีและยอดรวม: ยอดก่อนภาษี = {data['amount_before_vat']} (จากยอดภาษี {tax}), ยอดรวม = {data['total_amount']}")
        
        # ตรวจสอบอีกครั้งว่าตรงกันแล้ว
        final_pre_tax = data.get('amount_before_vat', 0) or 0
        final_tax = data.get('vat_amount', 0) or 0
        final_total = data.get('total_amount', 0) or 0
        final_calculated = final_pre_tax + final_tax
        
        if abs(final_calculated - final_total) <= tolerance:
            logger.info(f"✅ ยอดเงินสอดคล้องกันแล้ว: {final_pre_tax} + {final_tax} = {final_total}")
        else:
            logger.warning(f"⚠️ ยังไม่สอดคล้องกัน: {final_pre_tax} + {final_tax} = {final_calculated} แต่ยอดรวม = {final_total}")
        
        return data
    
    def check_data_completeness(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        ตรวจสอบความครบถ้วนของข้อมูลที่ดึงได้
        
        Args:
            data: Dictionary ที่มีข้อมูลที่ดึงได้
        
        Returns:
            Dictionary ที่มีข้อมูลเพิ่มเติมเกี่ยวกับความครบถ้วน:
            - missing_fields: List ของฟิลด์ที่ขาด
            - completeness_score: คะแนนความครบถ้วน (0-100)
            - is_complete: True ถ้าข้อมูลครบถ้วน
        """
        if not data.get('success'):
            return {
                'missing_fields': ['ไม่สามารถดึงข้อมูลได้'],
                'completeness_score': 0,
                'is_complete': False
            }
        
        # ฟิลด์ที่จำเป็น (required fields) - เรียงตามลำดับความสำคัญ
        # ลำดับ: 1. ชื่อบริษัท, 2. เลขประจำตัวผู้เสียภาษี, 3. วันที่, 4. เลขที่เอกสาร, 5. ยอดก่อนภาษี, 6. ยอดรวม
        required_fields = [
            ('company_name', 'ชื่อบริษัท'),
            ('tax_id', 'เลขประจำตัวผู้เสียภาษี'),
            ('date', 'วันที่'),
            ('document_number', 'เลขที่เอกสาร'),
            ('amount_before_vat', 'ยอดก่อนภาษี'),
            ('total_amount', 'ยอดรวม')
        ]
        
        # ฟิลด์ที่ควรมี (recommended fields) - สำหรับคำนวณคะแนน
        recommended_fields_for_score = {
            'branch': 'สาขา',
            'account_name': 'ชื่อบัญชี',
            'account_code': 'โค้ดบัญชี',
            'vat_amount': 'ยอดภาษี',
            'withholding_tax_percent': 'เปอร์เซ็นต์หัก ณ ที่จ่าย',
            'address': 'ที่อยู่'
        }
        
        # ฟิลด์ที่ควรมี (recommended fields) - สำหรับแสดงแจ้งเตือน (ไม่รวมสาขา, ชื่อบัญชี, โค้ดบัญชี)
        recommended_fields_for_warning = {
            'vat_amount': 'ยอดภาษี',
            'withholding_tax_percent': 'เปอร์เซ็นต์หัก ณ ที่จ่าย',
            'address': 'ที่อยู่'
        }
        
        missing_required = []
        missing_recommended = []
        missing_recommended_for_warning = []
        
        # ตรวจสอบฟิลด์ที่จำเป็น (เรียงตามลำดับความสำคัญ)
        for field, field_name in required_fields:
            value = data.get(field)
            if value is None or (isinstance(value, str) and value.strip() == '') or (isinstance(value, (int, float)) and value == 0 and field not in ['withholding_tax_percent']):
                missing_required.append(field_name)
        
        # ตรวจสอบฟิลด์ที่ควรมี (สำหรับคำนวณคะแนน)
        for field, field_name in recommended_fields_for_score.items():
            value = data.get(field)
            if value is None or (isinstance(value, str) and value.strip() == '') or (isinstance(value, (int, float)) and value == 0 and field not in ['withholding_tax_percent', 'withholding_tax_amount']):
                missing_recommended.append(field_name)
        
        # ตรวจสอบฟิลด์ที่ควรมี (สำหรับแสดงแจ้งเตือน - ไม่รวมสาขา, ชื่อบัญชี, โค้ดบัญชี)
        for field, field_name in recommended_fields_for_warning.items():
            value = data.get(field)
            if value is None or (isinstance(value, str) and value.strip() == '') or (isinstance(value, (int, float)) and value == 0 and field not in ['withholding_tax_percent', 'withholding_tax_amount']):
                missing_recommended_for_warning.append(field_name)
        
        # คำนวณคะแนนความครบถ้วน (ใช้ recommended_fields_for_score)
        total_fields = len(required_fields) + len(recommended_fields_for_score)
        missing_count = len(missing_required) + len(missing_recommended)
        completeness_score = max(0, int((total_fields - missing_count) / total_fields * 100))
        
        # ถ้ามีฟิลด์ที่จำเป็นขาด แสดงว่าไม่ครบถ้วน
        is_complete = len(missing_required) == 0
        
        # รวมฟิลด์ที่ขาดทั้งหมด (สำหรับแสดงแจ้งเตือน - ไม่รวมสาขา, ชื่อบัญชี, โค้ดบัญชี)
        all_missing = missing_required + missing_recommended_for_warning
        
        result = {
            'missing_fields': all_missing,
            'missing_required_fields': missing_required,
            'missing_recommended_fields': missing_recommended,
            'completeness_score': completeness_score,
            'is_complete': is_complete,
            'has_warnings': len(missing_required) > 0 or len(missing_recommended) > 0
        }
        
        if all_missing:
            logger.warning(f"⚠️ ข้อมูลไม่ครบถ้วน: ขาด {', '.join(all_missing)} (คะแนน: {completeness_score}%)")
        else:
            logger.info(f"✅ ข้อมูลครบถ้วน (คะแนน: {completeness_score}%)")
        
        return result
    
    def extract_data(self, text: str, filename: str, filepath: str = None) -> Dict[str, Any]:
        """
        ดึงข้อมูลจากเอกสารโดยอัตโนมัติ
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
            filepath: Path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด (มีการตรวจสอบและปรับยอดเงินให้สอดคล้องกันแล้ว)
        """
        # ลองแต่ละ Extractor
        for idx, extractor in enumerate(self.extractors):
            extractor_name = extractor.__class__.__name__
            logger.debug(f"🔍 [Manager] กำลังตรวจสอบ extractor {idx+1}/{len(self.extractors)}: {extractor_name}")
            
            if extractor.is_company_document(text):
                logger.info(f"🔍 ตรวจพบเอกสารของ: {extractor_name}")
                extracted_data = extractor.extract_all_data(text, filename, filepath)
                
                # ตรวจสอบและปรับยอดเงินให้สอดคล้องกัน
                validated_data = self.validate_and_adjust_amounts(extracted_data)
                
                # เพิ่ม old_filename ถ้ายังไม่มี (ใช้ชื่อไฟล์ปัจจุบัน)
                if 'old_filename' not in validated_data or not validated_data.get('old_filename'):
                    validated_data['old_filename'] = filename
                
                # ตรวจสอบความครบถ้วนของข้อมูล
                completeness_info = self.check_data_completeness(validated_data)
                
                # เพิ่มข้อมูลความครบถ้วนเข้าไปในผลลัพธ์
                validated_data['completeness'] = completeness_info
                validated_data['missing_fields'] = completeness_info['missing_fields']
                validated_data['completeness_score'] = completeness_info['completeness_score']
                validated_data['is_complete'] = completeness_info['is_complete']
                validated_data['has_warnings'] = completeness_info['has_warnings']
                
                return validated_data
        
        # ไม่พบ Extractor ที่เหมาะสม
        return {
            'success': False,
            'company': None,
            'error': 'ไม่สามารถระบุประเภทเอกสารได้ (ยังไม่รองรับบริษัทนี้)'
        }
    
    def get_supported_companies(self) -> List[Dict[str, Any]]:
        """
        ดึงรายชื่อบริษัทที่ระบบรองรับ
        
        Returns:
            List of dictionaries containing company information
        """
        companies = []
        for extractor in self.extractors:
            try:
                # เรียก extract_company_name เพื่อดึงชื่อบริษัท (ใช้ข้อความตัวอย่าง)
                # สำหรับ extractor บางตัวที่ต้องการ parse text ใช้ข้อความตัวอย่าง
                sample_text = "Sample text for company name extraction"
                company_name = extractor.extract_company_name(sample_text)
                extractor_name = extractor.__class__.__name__
                
                # ถ้าได้ None หรือ empty ให้ลองด้วยข้อความว่าง
                if not company_name:
                    company_name = extractor.extract_company_name("")
                
                companies.append({
                    'extractor_name': extractor_name,
                    'company_name': company_name or 'ไม่ระบุชื่อ',
                    'identifiers': getattr(extractor, 'COMPANY_IDENTIFIERS', [])
                })
            except Exception as e:
                logger.warning(f"ไม่สามารถดึงข้อมูลบริษัทจาก {extractor.__class__.__name__}: {e}")
                # ถ้ามีปัญหา ให้ใช้ชื่อ extractor แทน
                companies.append({
                    'extractor_name': extractor.__class__.__name__,
                    'company_name': extractor.__class__.__name__.replace('Extractor', ''),
                    'identifiers': getattr(extractor, 'COMPANY_IDENTIFIERS', [])
                })
                continue
        
        return companies
