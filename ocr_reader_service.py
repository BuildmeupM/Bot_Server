"""
OCR Reader Service
==================
บริการสำหรับอ่านข้อมูล OCR จากไฟล์ PDF
- รองรับการอ่านจากโฟลเดอร์และไฟล์เดียว
- ใช้ cache เพื่อหลีกเลี่ยงการอ่านซ้ำ
- รองรับ progress callback
- ใช้ TaxOCRProcessor เพื่อ extract ข้อมูลบริษัทและข้อมูลอื่นๆ
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from ocr_cache_manager import OCRCacheManager

logger = logging.getLogger(__name__)


class OCRReaderService:
    """บริการสำหรับอ่านข้อมูล OCR จากไฟล์ PDF"""
    
    def __init__(self, max_files: Optional[int] = None):
        """
        Initialize OCR Reader Service
        
        Args:
            max_files: จำนวนไฟล์สูงสุดที่จะอ่าน (None = ไม่จำกัด)
        """
        self.max_files = max_files
        self.cache_manager = OCRCacheManager(cache_ttl_hours=720)
        
        # Import TaxOCRProcessor
        try:
            from email_system.tax_ocr_processor import TaxOCRProcessor
            self.ocr_processor = TaxOCRProcessor()
        except ImportError:
            logger.warning("⚠️ ไม่สามารถ import TaxOCRProcessor ได้ - จะใช้ PyPDF2 แทน")
            self.ocr_processor = None
    
    def _extract_text_from_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """
        อ่านข้อความและ extract ข้อมูลจากไฟล์ PDF โดยใช้ TaxOCRProcessor
        
        Args:
            pdf_path: path ของไฟล์ PDF
            
        Returns:
            dictionary ประกอบด้วย:
            - success: bool
            - text: str (ข้อความที่อ่านได้)
            - raw_content: str (JSON response จาก key-extract API)
            - error: str (ถ้ามีข้อผิดพลาด)
        """
        try:
            # ใช้ TaxOCRProcessor เพื่อ extract ข้อมูล
            if self.ocr_processor:
                ocr_result = self.ocr_processor.get_ocr_raw_data(pdf_path)
                
                if ocr_result.get('success'):
                    # สำหรับ key-extract API: raw_content จะเป็น JSON format
                    raw_content = ocr_result.get('raw_content', '')
                    text = ocr_result.get('text', '')
                    
                    # ถ้า raw_content เป็น JSON (key-extract response) ให้ใช้ raw_content เป็นหลัก
                    if raw_content and ('"success"' in raw_content or '"data"' in raw_content):
                        # raw_content เป็น JSON format แล้ว
                        return {
                            'success': True,
                            'text': text or raw_content,
                            'raw_content': raw_content,
                            'error': None
                        }
                    else:
                        # ถ้าไม่ใช่ JSON ให้ใช้ text
                        return {
                            'success': True,
                            'text': text or raw_content,
                            'raw_content': text or raw_content,
                            'error': None
                        }
                else:
                    return {
                        'success': False,
                        'text': '',
                        'raw_content': '',
                        'error': ocr_result.get('error', 'ไม่สามารถอ่านข้อมูลได้')
                    }
            else:
                # Fallback: ใช้ PyPDF2 ถ้าไม่มี TaxOCRProcessor
                import PyPDF2
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text_parts = []
                    
                    # อ่านข้อความจากทุกหน้า
                    for page in pdf_reader.pages:
                        try:
                            text = page.extract_text() or ""
                            if text:
                                text_parts.append(text)
                        except Exception as e:
                            logger.warning(f"⚠️ ไม่สามารถอ่านหน้า PDF ได้: {e}")
                            continue
                    
                    raw_text = "\n".join(text_parts)
                    
                    if not raw_text.strip():
                        return {
                            'success': False,
                            'text': '',
                            'raw_content': '',
                            'error': 'ไม่พบข้อความในไฟล์ PDF (อาจเป็นไฟล์ภาพ)'
                        }
                    
                    return {
                        'success': True,
                        'text': raw_text,
                        'raw_content': raw_text,
                        'error': None
                    }
                
        except Exception as e:
            logger.error(f"❌ เกิดข้อผิดพลาดในการอ่าน PDF {pdf_path}: {e}", exc_info=True)
            return {
                'success': False,
                'text': '',
                'raw_content': '',
                'error': str(e)
            }
    
    def _read_single_file(self, file_path: Path) -> Dict[str, Any]:
        """
        อ่านไฟล์เดียว (ใช้ cache ถ้ามี)
        
        Args:
            file_path: path ของไฟล์
            
        Returns:
            dictionary ประกอบด้วย:
            - filename: str
            - filepath: str
            - status: str ('success' หรือ 'error')
            - raw_text: str (JSON format จาก key-extract API)
            - basic_info: dict
            - error: str (ถ้ามี)
        """
        filename = file_path.name
        filepath_str = str(file_path)
        
        # ตรวจสอบ cache ก่อน
        cached_data = self.cache_manager.get(filename, filepath_str)
        if cached_data:
            logger.debug(f"✅ พบ cache สำหรับ {filename}")
            return {
                'filename': filename,
                'filepath': filepath_str,
                'status': 'success',
                'raw_text': cached_data.get('raw_text', cached_data.get('text', '')),
                'basic_info': cached_data.get('basic_info', {}),
                'error': None
            }
        
        # อ่านไฟล์
        result = self._extract_text_from_pdf(file_path)
        
        if result['success']:
            # ใช้ raw_content เป็นหลัก (สำหรับ key-extract API จะเป็น JSON format)
            raw_content = result.get('raw_content', result.get('text', ''))
            text = result.get('text', raw_content)
            
            # สร้าง basic_info จากข้อความ
            lines = text.split('\n') if text else []
            
            # ถ้า raw_content เป็น JSON (key-extract response) ให้ parse และดึงข้อมูล
            basic_info = {
                'line_count': len(lines),
                'char_count': len(text),
                'first_lines': lines[:5] if len(lines) > 5 else lines,
                'has_company_name': False,
                'has_tax_id': False,
                'has_numbers': False,
                'form_type_detected': None,
                'keywords_found': []
            }
            
            # ถ้า raw_content เป็น JSON (key-extract response) ให้ parse และดึงข้อมูล
            if raw_content and ('"success"' in raw_content or '"data"' in raw_content):
                try:
                    parsed_json = json.loads(raw_content)
                    if isinstance(parsed_json, dict) and 'data' in parsed_json:
                        data = parsed_json.get('data', {})
                        
                        # ตรวจสอบว่ามีข้อมูลบริษัทหรือไม่
                        basic_info['has_company_name'] = bool(data.get('ชื่อผู้ขาย') or data.get('ชื่อบริษัท'))
                        basic_info['has_tax_id'] = bool(data.get('เลขประจำตัวผู้เสียภาษี - ผู้ขาย'))
                        basic_info['has_numbers'] = bool(data.get('ยอดรวมก่อนภาษี') or data.get('ยอดรวมสุทธิ'))
                        basic_info['form_type_detected'] = data.get('ประเภทเอกสาร', '')
                        
                        # ดึง keywords
                        keywords = []
                        if data.get('ชื่อผู้ขาย'):
                            keywords.append('ชื่อผู้ขาย')
                        if data.get('เลขประจำตัวผู้เสียภาษี - ผู้ขาย'):
                            keywords.append('เลขประจำตัวผู้เสียภาษี')
                        if data.get('ยอดรวมสุทธิ'):
                            keywords.append('ยอดรวม')
                        basic_info['keywords_found'] = keywords
                except Exception as e:
                    logger.debug(f"⚠️ ไม่สามารถ parse JSON ได้: {e}")
            
            # เก็บลง cache (ใช้ raw_content เป็นหลัก)
            cache_data = {
                'text': text,
                'raw_text': raw_content,  # เก็บ JSON format สำหรับ key-extract API
                'basic_info': basic_info
            }
            self.cache_manager.set(filename, filepath_str, cache_data)
            
            return {
                'filename': filename,
                'filepath': filepath_str,
                'status': 'success',
                'raw_text': raw_content,  # ใช้ raw_content (JSON format) แทน text
                'basic_info': basic_info,
                'error': None
            }
        else:
            return {
                'filename': filename,
                'filepath': filepath_str,
                'status': 'error',
                'raw_text': '',
                'basic_info': {},
                'error': result.get('error', 'ไม่ทราบสาเหตุ')
            }
    
    def read_folder_raw(
        self,
        folder_path: str,
        include_subfolders: bool = False,
        progress_callback: Optional[Callable[[int, int, float, str], None]] = None
    ) -> Dict[str, Any]:
        """
        อ่านข้อมูล OCR จากโฟลเดอร์
        
        Args:
            folder_path: path ของโฟลเดอร์
            include_subfolders: ต้องการอ่านไฟล์ในโฟลเดอร์ย่อยหรือไม่
            progress_callback: callback function(current, total, percent, filename)
            
        Returns:
            dictionary ประกอบด้วย:
            - files: List[Dict] (รายการไฟล์ที่อ่าน)
            - stats: Dict (สถิติ: total, success, error)
        """
        folder = Path(folder_path)
        
        if not folder.exists():
            return {
                'files': [],
                'stats': {
                    'total': 0,
                    'success': 0,
                    'error': 0
                },
                'error': f'โฟลเดอร์ไม่พบ: {folder_path}'
            }
        
        # หาไฟล์ PDF ทั้งหมด
        if include_subfolders:
            pdf_files = list(folder.rglob('*.pdf'))
        else:
            pdf_files = list(folder.glob('*.pdf'))
        
        # จำกัดจำนวนไฟล์ถ้ามีการกำหนด
        if self.max_files and len(pdf_files) > self.max_files:
            pdf_files = pdf_files[:self.max_files]
        
        total_files = len(pdf_files)
        files_result = []
        stats = {
            'total': total_files,
            'success': 0,
            'error': 0
        }
        
        # อ่านไฟล์ทีละไฟล์
        for idx, pdf_file in enumerate(pdf_files, 1):
            try:
                # อัปเดต progress
                percent = (idx / total_files * 100) if total_files > 0 else 0
                if progress_callback:
                    try:
                        progress_callback(idx, total_files, percent, pdf_file.name)
                    except Exception as e:
                        logger.warning(f"⚠️ เกิดข้อผิดพลาดใน progress_callback: {e}")
                
                # อ่านไฟล์
                file_result = self._read_single_file(pdf_file)
                files_result.append(file_result)
                
                # อัปเดตสถิติ
                if file_result['status'] == 'success':
                    stats['success'] += 1
                else:
                    stats['error'] += 1
                    
            except Exception as e:
                logger.error(f"❌ เกิดข้อผิดพลาดในการอ่านไฟล์ {pdf_file}: {e}", exc_info=True)
                files_result.append({
                    'filename': pdf_file.name,
                    'filepath': str(pdf_file),
                    'status': 'error',
                    'raw_text': '',
                    'basic_info': {},
                    'error': str(e)
                })
                stats['error'] += 1
        
        return {
            'files': files_result,
            'stats': stats
        }
    
    def read_single_file_raw(self, file_path: str) -> Dict[str, Any]:
        """
        อ่านข้อมูล OCR จากไฟล์เดียว
        
        Args:
            file_path: path ของไฟล์
            
        Returns:
            dictionary ประกอบด้วย:
            - success: bool
            - file: Dict (ข้อมูลไฟล์)
            - error: str (ถ้ามี)
        """
        file = Path(file_path)
        
        if not file.exists():
            return {
                'success': False,
                'file': None,
                'error': f'ไฟล์ไม่พบ: {file_path}'
            }
        
        if not file.suffix.lower() == '.pdf':
            return {
                'success': False,
                'file': None,
                'error': 'รองรับเฉพาะไฟล์ PDF'
            }
        
        try:
            file_result = self._read_single_file(file)
            
            if file_result['status'] == 'success':
                return {
                    'success': True,
                    'file': file_result,
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'file': file_result,
                    'error': file_result.get('error', 'ไม่ทราบสาเหตุ')
                }
                
        except Exception as e:
            logger.error(f"❌ เกิดข้อผิดพลาดในการอ่านไฟล์ {file_path}: {e}", exc_info=True)
            return {
                'success': False,
                'file': None,
                'error': str(e)
            }
