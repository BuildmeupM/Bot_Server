"""
Tax OCR Processor - ระบบ OCR สำหรับอ่านข้อมูลจากไฟล์แบบยื่นภาษี
ใช้ TYPHOON OCR model
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import re

logger = logging.getLogger(__name__)

# ===== ตรวจสอบ TYPHOON OCR =====
TYPHOON_AVAILABLE = False
try:
    # ตรวจสอบว่ามี TYPHOON OCR library หรือไม่
    # อาจเป็น library ภายนอกที่ต้องติดตั้ง
    try:
        from typhoon_ocr import TYPHOONOCR  # type: ignore
        TYPHOON_AVAILABLE = True
        logger.info("✅ TYPHOON OCR พร้อมใช้งาน")
    except ImportError:
        # ลองใช้ API หรือ library อื่นๆ
        try:
            import requests
            # ตรวจสอบว่ามี TYPHOON API endpoint หรือไม่
            TYPHOON_AVAILABLE = True
            logger.info("✅ TYPHOON OCR (API) พร้อมใช้งาน")
        except ImportError:
            TYPHOON_AVAILABLE = False
            logger.warning("⚠️ TYPHOON OCR ไม่พร้อมใช้งาน - ต้องติดตั้ง library หรือตั้งค่า API")
except Exception as e:
    TYPHOON_AVAILABLE = False
    logger.warning(f"⚠️ TYPHOON OCR ไม่พร้อมใช้งาน: {e}")

# ===== Fallback: ใช้ PyPDF2 หรือ pdf2image + pytesseract =====
FALLBACK_OCR_AVAILABLE = False
try:
    from pdf2image import convert_from_path
    try:
        import pytesseract
        FALLBACK_OCR_AVAILABLE = True
        logger.info("✅ Fallback OCR (pytesseract) พร้อมใช้งาน")
    except ImportError:
        logger.warning("⚠️ pytesseract ไม่ได้ติดตั้ง - ใช้ PyPDF2 แทน")
        FALLBACK_OCR_AVAILABLE = False
except ImportError:
    logger.warning("⚠️ pdf2image ไม่ได้ติดตั้ง")
    FALLBACK_OCR_AVAILABLE = False

class TaxOCRProcessor:
    """คลาสสำหรับประมวลผล OCR จากไฟล์แบบยื่นภาษี"""
    
    def __init__(self):
        self.typhoon_available = TYPHOON_AVAILABLE
        self.fallback_available = FALLBACK_OCR_AVAILABLE
        
    def extract_tax_amounts(self, pdf_path: Path) -> Dict[str, Any]:
        """
        อ่านข้อมูลยอดเงินจากไฟล์แบบยื่นภาษี
        
        Args:
            pdf_path: Path ของไฟล์ PDF แบบยื่นภาษี
            
        Returns:
            Dictionary ที่มีข้อมูลยอดเงินที่อ่านได้ เช่น:
            {
                'success': True,
                'amounts': {
                    'ภงด.1': 1000.00,
                    'ภงด.3': 2000.00,
                    'ประกันสังคม': 4500.00,
                    'กองทุน กยศ.': 2000.00
                },
                'raw_text': '...',
                'method': 'typhoon' or 'fallback'
            }
        """
        if not pdf_path.exists():
            return {
                'success': False,
                'error': f'ไม่พบไฟล์: {pdf_path}'
            }
        
        try:
            # ลองใช้ TYPHOON OCR ก่อน
            if self.typhoon_available:
                result = self._extract_with_typhoon(pdf_path)
                if result.get('success'):
                    return result
            
            # ถ้า TYPHOON ไม่สำเร็จหรือไม่มี ให้ใช้ fallback
            if self.fallback_available:
                result = self._extract_with_fallback(pdf_path)
                if result.get('success'):
                    return result
            
            # ถ้าไม่มี OCR ใดๆ ใช้ PyPDF2 แบบพื้นฐาน
            return self._extract_with_pypdf2(pdf_path)
            
        except Exception as e:
            logger.error(f"❌ เกิดข้อผิดพลาดในการอ่าน OCR: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'เกิดข้อผิดพลาด: {e}'
            }
    
    def _extract_with_typhoon(self, pdf_path: Path) -> Dict[str, Any]:
        """ใช้ TYPHOON OCR ในการอ่าน"""
        try:
            # TODO: เรียกใช้ TYPHOON OCR API หรือ library
            # ตัวอย่างโครงสร้าง:
            # typhoon_ocr = TYPHOONOCR()
            # result = typhoon_ocr.process(pdf_path)
            # text = result.get('text', '')
            
            # สำหรับตอนนี้ ใช้ placeholder
            logger.info(f"🔄 กำลังใช้ TYPHOON OCR อ่านไฟล์: {pdf_path.name}")
            
            # เรียกใช้ TYPHOON API (ถ้ามี)
            # result = self._call_typhoon_api(pdf_path)
            
            return {
                'success': False,
                'error': 'TYPHOON OCR ยังไม่ได้ตั้งค่า - ใช้ fallback แทน'
            }
            
        except Exception as e:
            logger.error(f"❌ TYPHOON OCR error: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'TYPHOON OCR error: {e}'
            }
    
    def _extract_with_fallback(self, pdf_path: Path) -> Dict[str, Any]:
        """ใช้ pytesseract + pdf2image เป็น fallback"""
        try:
            from pdf2image import convert_from_path
            import pytesseract
            
            logger.info(f"🔄 กำลังใช้ Fallback OCR (pytesseract) อ่านไฟล์: {pdf_path.name}")
            
            # แปลง PDF เป็นรูปภาพ
            images = convert_from_path(str(pdf_path), dpi=300)
            
            if not images:
                return {
                    'success': False,
                    'error': 'ไม่สามารถแปลง PDF เป็นรูปภาพได้'
                }
            
            # อ่านข้อความจากรูปภาพทั้งหมด
            all_text = []
            for img in images:
                text = pytesseract.image_to_string(img, lang='tha+eng')
                all_text.append(text)
            
            raw_text = '\n'.join(all_text)
            
            # แยกยอดเงินจากข้อความ
            amounts = self._parse_tax_amounts(raw_text)
            
            return {
                'success': True,
                'amounts': amounts,
                'raw_text': raw_text,
                'method': 'fallback'
            }
            
        except Exception as e:
            logger.error(f"❌ Fallback OCR error: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Fallback OCR error: {e}'
            }
    
    def _extract_with_pypdf2(self, pdf_path: Path) -> Dict[str, Any]:
        """ใช้ PyPDF2 อ่านข้อความพื้นฐาน (ไม่มี OCR)"""
        try:
            import PyPDF2
            
            logger.info(f"🔄 กำลังใช้ PyPDF2 อ่านไฟล์: {pdf_path.name}")
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                all_text = []
                
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    all_text.append(text)
            
            raw_text = '\n'.join(all_text)
            
            # แยกยอดเงินจากข้อความ
            amounts = self._parse_tax_amounts(raw_text)
            
            return {
                'success': True,
                'amounts': amounts,
                'raw_text': raw_text,
                'method': 'pypdf2'
            }
            
        except Exception as e:
            logger.error(f"❌ PyPDF2 error: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'PyPDF2 error: {e}'
            }
    
    def _parse_tax_amounts(self, text: str) -> Dict[str, float]:
        """
        แยกยอดเงินจากข้อความที่อ่านได้
        
        Args:
            text: ข้อความที่อ่านได้จาก OCR
            
        Returns:
            Dictionary ของยอดเงิน เช่น:
            {
                'ภงด.1': 1000.00,
                'ภงด.3': 2000.00,
                'ประกันสังคม': 4500.00,
                'กองทุน กยศ.': 2000.00
            }
        """
        amounts = {}
        
        # รูปแบบการค้นหายอดเงิน
        patterns = {
            'ภงด.1': [
                r'ภงด\.1[^\d]*([\d,]+\.?\d*)',
                r'P\.N\.D\.1[^\d]*([\d,]+\.?\d*)',
                r'แบบ\s*ภงด\.1[^\d]*([\d,]+\.?\d*)'
            ],
            'ภงด.3': [
                r'ภงด\.3[^\d]*([\d,]+\.?\d*)',
                r'P\.N\.D\.3[^\d]*([\d,]+\.?\d*)',
                r'แบบ\s*ภงด\.3[^\d]*([\d,]+\.?\d*)'
            ],
            'ประกันสังคม': [
                r'ประกันสังคม[^\d]*([\d,]+\.?\d*)',
                r'Social\s*Security[^\d]*([\d,]+\.?\d*)',
                r'ส\.ส\.ส\.\s*[^\d]*([\d,]+\.?\d*)'
            ],
            'กองทุน กยศ.': [
                r'กองทุน\s*กยศ\.?[^\d]*([\d,]+\.?\d*)',
                r'กยศ\.?[^\d]*([\d,]+\.?\d*)',
                r'Student\s*Loan[^\d]*([\d,]+\.?\d*)'
            ]
        }
        
        for tax_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    # ใช้ค่าที่พบครั้งแรก
                    try:
                        # แปลง string เป็น float (ลบ comma ออก)
                        amount_str = matches[0].replace(',', '')
                        amount = float(amount_str)
                        amounts[tax_type] = amount
                        logger.info(f"✅ พบยอดเงิน {tax_type}: {amount:,.2f}")
                        break
                    except ValueError:
                        continue
        
        return amounts
    
    def process_tax_filing_file(self, pdf_path: Path) -> Dict[str, Any]:
        """
        ประมวลผลไฟล์แบบยื่นภาษีและส่งคืนข้อมูลยอดเงิน
        
        Args:
            pdf_path: Path ของไฟล์ PDF แบบยื่นภาษี
            
        Returns:
            Dictionary ที่มีข้อมูลยอดเงินที่อ่านได้
        """
        return self.extract_tax_amounts(pdf_path)


# ===== Helper Functions =====
def extract_tax_amounts_from_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Helper function สำหรับเรียกใช้ OCR จากไฟล์ PDF
    
    Args:
        pdf_path: Path ของไฟล์ PDF
        
    Returns:
        Dictionary ที่มีข้อมูลยอดเงิน
    """
    processor = TaxOCRProcessor()
    return processor.extract_tax_amounts(Path(pdf_path))

