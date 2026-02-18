"""
OCR Cache Manager
=================
ระบบจัดการ cache สำหรับข้อมูล OCR ที่อ่านได้
- เก็บข้อมูลตามชื่อไฟล์ (filename)
- แยก cache ตามบริษัท (company) จาก path
- ลบข้อมูลที่เก่ากว่า 30 วันอัตโนมัติ
- ป้องกันการอ่าน OCR ซ้ำเมื่อเว็บเซิฟเวอร์หลุดกลางทาง

Author: BotV3
Version: 2.0.0
"""

import logging
import json
import time
import hashlib
import re
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# File locks สำหรับป้องกัน race condition เมื่อบันทึก cache
_cache_file_locks: Dict[str, threading.Lock] = {}
_cache_locks_lock = threading.Lock()


class OCRCacheManager:
    """จัดการ cache สำหรับข้อมูล OCR แยกตามบริษัท"""
    
    # ขนาดไฟล์สูงสุด (bytes) ก่อนที่จะแยกไฟล์ - 50MB
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
    # จำนวนรายการสูงสุดต่อไฟล์ - ถ้าเกินจะแยกไฟล์
    MAX_ENTRIES_PER_FILE = 1000
    
    def __init__(self, cache_dir: str = "cache", cache_ttl_hours: int = 720, company_name: Optional[str] = None):
        """
        Initialize OCR Cache Manager
        
        Args:
            cache_dir: โฟลเดอร์สำหรับเก็บ cache files
            cache_ttl_hours: ระยะเวลาที่เก็บ cache (ชั่วโมง) - default 720 ชั่วโมง (30 วัน)
            company_name: ชื่อบริษัทสำหรับแยก cache (ถ้าไม่ระบุจะใช้ "default")
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl_hours = cache_ttl_hours
        self.company_name = company_name or "default"
        
        # สร้างชื่อไฟล์ cache ตามบริษัท
        safe_company_name = self._sanitize_filename(self.company_name)
        self.cache_file_base = self.cache_dir / f"ocr_cache_{safe_company_name}"
        self.cache_file = self.cache_dir / f"ocr_cache_{safe_company_name}.json"
        
        self.cache_data = {}
        self._load_cache()
    
    def _sanitize_filename(self, name: str) -> str:
        """
        ทำความสะอาดชื่อไฟล์ให้ปลอดภัย (ลบอักขระที่ไม่ถูกต้อง)
        
        Args:
            name: ชื่อที่ต้องการทำความสะอาด
            
        Returns:
            ชื่อที่ปลอดภัยสำหรับใช้เป็นชื่อไฟล์
        """
        # ลบอักขระที่ไม่ถูกต้องสำหรับชื่อไฟล์ Windows/Linux
        invalid_chars = r'[<>:"/\\|?*]'
        safe_name = re.sub(invalid_chars, '_', name)
        # ลบช่องว่างที่หัวท้าย
        safe_name = safe_name.strip()
        # ถ้าเป็นค่าว่างให้ใช้ "default"
        if not safe_name:
            safe_name = "default"
        return safe_name
    
    @staticmethod
    def _extract_company_name_from_path(filepath: str) -> str:
        """
        ดึงชื่อบริษัทจาก filepath (หา folder ที่มี "Build" ในชื่อ)
        
        Args:
            filepath: path ของไฟล์
            
        Returns:
            ชื่อบริษัท (เช่น "Build000 ทดสอบระบบ") หรือ "default" ถ้าไม่พบ
        """
        try:
            path_obj = Path(filepath)
            # วนลูปหา folder ที่มี "Build" ในชื่อ
            for part in path_obj.parts:
                part_str = str(part)
                # หา folder ที่ขึ้นต้นด้วย "Build" (case-insensitive)
                if part_str.lower().startswith('build'):
                    return part_str
            
            # ถ้าไม่เจอ ให้ใช้ชื่อโฟลเดอร์หลัก (parent ของไฟล์)
            if path_obj.parent and path_obj.parent.name:
                return path_obj.parent.name
            
            return "default"
        except Exception as e:
            logger.warning(f"⚠️ ไม่สามารถดึงชื่อบริษัทจาก path: {e}")
            return "default"
    
    def _get_company_cache_manager(self, filepath: str) -> 'OCRCacheManager':
        """
        สร้าง OCRCacheManager ใหม่สำหรับบริษัทที่ระบุใน filepath
        
        Args:
            filepath: path ของไฟล์
            
        Returns:
            OCRCacheManager instance สำหรับบริษัทนั้น
        """
        company_name = OCRCacheManager._extract_company_name_from_path(filepath)
        return OCRCacheManager(
            cache_dir=str(self.cache_dir),
            cache_ttl_hours=self.cache_ttl_hours,
            company_name=company_name
        )
    
    def _load_cache(self):
        """โหลดข้อมูล cache จากไฟล์ (รองรับหลายไฟล์)"""
        try:
            self.cache_data = {}
            
            # หาไฟล์ cache ทั้งหมดที่เกี่ยวข้อง (อาจมีหลายไฟล์: part1, part2, ...)
            cache_files = []
            
            # ตรวจสอบไฟล์หลัก (ไม่มี part)
            if self.cache_file.exists():
                cache_files.append(self.cache_file)
            
            # หาไฟล์ part ทั้งหมด (part1, part2, ...)
            part_index = 1
            while True:
                part_file = self.cache_dir / f"{self.cache_file_base.name}_part{part_index}.json"
                if part_file.exists():
                    cache_files.append(part_file)
                    part_index += 1
                else:
                    break
            
            if not cache_files:
                logger.info("📝 สร้าง cache ใหม่")
                return
            
            # โหลดข้อมูลจากทุกไฟล์
            total_loaded = 0
            for cache_file in cache_files:
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # ลอง parse JSON
                    file_data = json.loads(content)
                    if isinstance(file_data, dict):
                        # รวมข้อมูลจากไฟล์นี้เข้ากับ cache_data
                        self.cache_data.update(file_data)
                        total_loaded += len(file_data)
                        logger.debug(f"✅ โหลด cache จาก {cache_file.name}: {len(file_data)} รายการ")
                    
                except json.JSONDecodeError as json_error:
                    logger.error(f"❌ JSON parse error ในไฟล์ cache: {json_error}")
                    logger.error(f"   ไฟล์: {cache_file}")
                    logger.error(f"   บรรทัด: {json_error.lineno}, คอลัมน์: {json_error.colno}")
                    
                    # สร้าง backup ของไฟล์ที่เสีย
                    backup_file = cache_file.with_suffix('.json.broken')
                    try:
                        import shutil
                        shutil.copy2(cache_file, backup_file)
                        logger.warning(f"💾 สร้าง backup ของไฟล์ที่เสียไว้ที่: {backup_file}")
                    except Exception as backup_error:
                        logger.error(f"❌ ไม่สามารถสร้าง backup ได้: {backup_error}")
                    
                except Exception as file_error:
                    logger.error(f"❌ ไม่สามารถโหลดไฟล์ cache {cache_file}: {file_error}")
            
            if total_loaded > 0:
                logger.info(f"✅ โหลด cache สำเร็จ: {total_loaded} รายการ จาก {len(cache_files)} ไฟล์")
            else:
                logger.info("📝 สร้าง cache ใหม่เนื่องจากไฟล์เดิมเสียหาย")
                self.cache_data = {}
                
        except Exception as e:
            logger.error(f"❌ ไม่สามารถโหลด cache: {e}", exc_info=True)
            self.cache_data = {}
    
    def _get_file_lock(self) -> threading.Lock:
        """Get or create a file lock for this cache file"""
        cache_file_str = str(self.cache_file)
        with _cache_locks_lock:
            if cache_file_str not in _cache_file_locks:
                _cache_file_locks[cache_file_str] = threading.Lock()
            return _cache_file_locks[cache_file_str]
    
    def _save_cache(self):
        """บันทึกข้อมูล cache ลงไฟล์ (แยกไฟล์ถ้าข้อมูลใหญ่เกินไป) - มี file locking เพื่อป้องกัน race condition"""
        file_lock = self._get_file_lock()
        
        with file_lock:
            try:
                # Reload cache ก่อนบันทึกเพื่อ merge ข้อมูลใหม่กับข้อมูลเก่า (ป้องกัน race condition)
                # แต่เก็บข้อมูลใหม่ที่เพิ่งเพิ่มไว้ก่อน
                new_cache_data = self.cache_data.copy()
                
                # โหลด cache ใหม่จากไฟล์ (อาจมีข้อมูลที่ถูกเพิ่มโดย thread อื่น)
                try:
                    # หาไฟล์ cache ทั้งหมดที่เกี่ยวข้อง
                    cache_files = []
                    if self.cache_file.exists():
                        cache_files.append(self.cache_file)
                    
                    part_index = 1
                    while True:
                        part_file = self.cache_dir / f"{self.cache_file_base.name}_part{part_index}.json"
                        if part_file.exists():
                            cache_files.append(part_file)
                            part_index += 1
                        else:
                            break
                    
                    # โหลดข้อมูลจากไฟล์ทั้งหมด
                    loaded_data = {}
                    for cache_file in cache_files:
                        try:
                            with open(cache_file, 'r', encoding='utf-8') as f:
                                file_data = json.load(f)
                                if isinstance(file_data, dict):
                                    loaded_data.update(file_data)
                        except (json.JSONDecodeError, Exception) as e:
                            logger.warning(f"⚠️ ไม่สามารถโหลด cache จาก {cache_file.name}: {e}")
                    
                    # Merge: ข้อมูลใหม่จะทับข้อมูลเก่า (ข้อมูลใหม่สำคัญกว่า)
                    merged_data = {**loaded_data, **new_cache_data}
                    self.cache_data = merged_data
                    
                except Exception as reload_error:
                    logger.warning(f"⚠️ ไม่สามารถ reload cache ก่อนบันทึก: {reload_error} - จะใช้ข้อมูลปัจจุบันแทน")
                    # ถ้า reload ไม่ได้ ให้ใช้ข้อมูลปัจจุบัน
                
                total_entries = len(self.cache_data)
                
                # ถ้าข้อมูลไม่มาก ให้บันทึกลงไฟล์เดียว
                if total_entries <= self.MAX_ENTRIES_PER_FILE:
                    # ตรวจสอบขนาดไฟล์ก่อนบันทึก
                    import io
                    test_buffer = io.StringIO()
                    json.dump(self.cache_data, test_buffer, ensure_ascii=False, indent=2)
                    test_size = len(test_buffer.getvalue().encode('utf-8'))
                    
                    if test_size <= self.MAX_FILE_SIZE:
                        # บันทึกลงไฟล์เดียว
                        with open(self.cache_file, 'w', encoding='utf-8') as f:
                            json.dump(self.cache_data, f, ensure_ascii=False, indent=2)
                        
                        # ลบไฟล์ part ทั้งหมด (ถ้ามี)
                        self._delete_part_files()
                        
                        logger.debug(f"💾 บันทึก cache สำเร็จ: {total_entries} รายการ (ไฟล์เดียว)")
                        return
                
                # ถ้าข้อมูลมากเกินไป ให้แยกไฟล์
                logger.info(f"📦 ข้อมูล cache มีขนาดใหญ่ ({total_entries} รายการ) - จะแยกเป็นหลายไฟล์")
                
                # แบ่งข้อมูลออกเป็น chunks
                entries_list = list(self.cache_data.items())
                num_parts = (total_entries + self.MAX_ENTRIES_PER_FILE - 1) // self.MAX_ENTRIES_PER_FILE
                
                # ลบไฟล์ part เก่าทั้งหมดก่อน
                self._delete_part_files()
                
                # บันทึกแต่ละ part
                for part_index in range(num_parts):
                    start_idx = part_index * self.MAX_ENTRIES_PER_FILE
                    end_idx = min(start_idx + self.MAX_ENTRIES_PER_FILE, total_entries)
                    part_data = dict(entries_list[start_idx:end_idx])
                    
                    if part_index == 0:
                        # Part แรกบันทึกลงไฟล์หลัก
                        with open(self.cache_file, 'w', encoding='utf-8') as f:
                            json.dump(part_data, f, ensure_ascii=False, indent=2)
                        logger.debug(f"💾 บันทึก cache part 1: {len(part_data)} รายการ (ไฟล์หลัก)")
                    else:
                        # Part ถัดไปบันทึกลงไฟล์ part
                        part_file = self.cache_dir / f"{self.cache_file_base.name}_part{part_index}.json"
                        with open(part_file, 'w', encoding='utf-8') as f:
                            json.dump(part_data, f, ensure_ascii=False, indent=2)
                        logger.debug(f"💾 บันทึก cache part {part_index + 1}: {len(part_data)} รายการ ({part_file.name})")
                
                logger.info(f"✅ บันทึก cache สำเร็จ: {total_entries} รายการ แยกเป็น {num_parts} ไฟล์")
            
            except Exception as e:
                logger.error(f"❌ ไม่สามารถบันทึก cache: {e}", exc_info=True)
    
    def _delete_part_files(self):
        """ลบไฟล์ part ทั้งหมด (part1, part2, ...)"""
        try:
            part_index = 1
            while True:
                part_file = self.cache_dir / f"{self.cache_file_base.name}_part{part_index}.json"
                if part_file.exists():
                    part_file.unlink()
                    logger.debug(f"🗑️ ลบไฟล์ part {part_index}: {part_file.name}")
                    part_index += 1
                else:
                    break
        except Exception as e:
            logger.warning(f"⚠️ ไม่สามารถลบไฟล์ part: {e}")
    
    def _get_cache_key(self, filename: str, filepath: str) -> str:
        """
        สร้าง cache key จาก filename และ filepath
        
        Args:
            filename: ชื่อไฟล์
            filepath: path ไฟล์
            
        Returns:
            cache key (hash)
        """
        # ใช้ filename + filepath เพื่อให้ unique
        key_string = f"{filename}|{filepath}"
        return hashlib.md5(key_string.encode('utf-8')).hexdigest()
    
    def get(self, filename: str, filepath: str) -> Optional[Dict[str, Any]]:
        """
        ดึงข้อมูลจาก cache (จะใช้ cache manager ของบริษัทที่ระบุใน filepath)
        ตรวจสอบทั้ง exact match (filename+path) และ filename เท่านั้น - ถ้าเคยอ่านชื่อไฟล์นี้แล้วไม่ต้องอ่านซ้ำ
        
        Args:
            filename: ชื่อไฟล์
            filepath: path ไฟล์
            
        Returns:
            ข้อมูล OCR หรือ None ถ้าไม่มีหรือหมดอายุ
        """
        # ถ้า company_name เป็น "default" ให้ดึงชื่อบริษัทจาก filepath
        if self.company_name == "default":
            company_manager = self._get_company_cache_manager(filepath)
            return company_manager.get(filename, filepath)
        
        # ขั้นตอน 1: ลอง exact match (filename + filepath) ก่อน
        cache_key = self._get_cache_key(filename, filepath)
        current_time = time.time()
        
        if cache_key in self.cache_data:
            cache_entry = self.cache_data[cache_key]
            cached_time = cache_entry.get('cached_at', 0)
            age_hours = (current_time - cached_time) / 3600
            
            if age_hours <= self.cache_ttl_hours:
                logger.debug(f"✅ พบ cache (exact match) สำหรับ {filename} (อายุ {age_hours:.2f} ชั่วโมง)")
                return cache_entry.get('data')
            else:
                del self.cache_data[cache_key]
                self._save_cache()
        
        # ขั้นตอน 2: ค้นหาจากชื่อไฟล์เท่านั้น - ถ้าเคยอ่านไฟล์ชื่อนี้แล้ว ไม่ต้องอ่านซ้ำ
        return self._get_by_filename(filename)
    
    def _get_by_filename(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        ค้นหา cache จากชื่อไฟล์เท่านั้น (ไม่สนใจ path)
        ใช้เมื่อ exact match ไม่เจอ - เช็คว่าเคยอ่านชื่อไฟล์นี้ไปแล้วหรือไม่
        
        Args:
            filename: ชื่อไฟล์
            
        Returns:
            ข้อมูล OCR หรือ None ถ้าไม่มีหรือหมดอายุ
        """
        current_time = time.time()
        found_key = None
        
        for cache_key, cache_entry in self.cache_data.items():
            if cache_entry.get('filename') == filename:
                cached_time = cache_entry.get('cached_at', 0)
                age_hours = (current_time - cached_time) / 3600
                if age_hours <= self.cache_ttl_hours:
                    logger.debug(f"✅ พบ cache (จากชื่อไฟล์) สำหรับ {filename} - ไม่ต้องอ่านซ้ำ (อายุ {age_hours:.2f} ชม.)")
                    return cache_entry.get('data')
                else:
                    found_key = cache_key
                    break
        
        if found_key:
            del self.cache_data[found_key]
            self._save_cache()
        return None
    
    def set(self, filename: str, filepath: str, ocr_data: Dict[str, Any]):
        """
        เก็บข้อมูล OCR ลง cache (จะใช้ cache manager ของบริษัทที่ระบุใน filepath)
        
        Args:
            filename: ชื่อไฟล์
            filepath: path ไฟล์
            ocr_data: ข้อมูล OCR ที่อ่านได้
        """
        # ถ้า company_name เป็น "default" ให้ดึงชื่อบริษัทจาก filepath
        if self.company_name == "default":
            company_manager = self._get_company_cache_manager(filepath)
            company_manager.set(filename, filepath, ocr_data)
            return
        
        # ใช้ cache manager ปัจจุบัน
        cache_key = self._get_cache_key(filename, filepath)
        
        self.cache_data[cache_key] = {
            'filename': filename,
            'filepath': filepath,
            'data': ocr_data,
            'cached_at': time.time()
        }
        
        self._save_cache()
        logger.debug(f"💾 เก็บ cache สำหรับ {filename} (บริษัท: {self.company_name})")
    
    def cleanup_expired(self) -> int:
        """
        ลบ cache ที่หมดอายุ (สำหรับบริษัทนี้เท่านั้น)
        
        Returns:
            จำนวน cache ที่ลบออก
        """
        current_time = time.time()
        expired_keys = []
        
        for cache_key, cache_entry in self.cache_data.items():
            cached_time = cache_entry.get('cached_at', 0)
            age_hours = (current_time - cached_time) / 3600
            
            if age_hours > self.cache_ttl_hours:
                expired_keys.append(cache_key)
        
        for key in expired_keys:
            filename = self.cache_data[key].get('filename', 'unknown')
            del self.cache_data[key]
            logger.debug(f"🗑️ ลบ cache ที่หมดอายุ: {filename}")
        
        if expired_keys:
            self._save_cache()
            logger.info(f"✅ ลบ cache ที่หมดอายุแล้ว: {len(expired_keys)} รายการ (บริษัท: {self.company_name})")
        
        return len(expired_keys)
    
    @staticmethod
    def cleanup_all_expired(cache_dir: str = "cache", cache_ttl_hours: int = 720) -> int:
        """
        ลบ cache ที่หมดอายุจากทุกบริษัท
        
        Args:
            cache_dir: โฟลเดอร์ cache
            cache_ttl_hours: ระยะเวลา TTL
            
        Returns:
            จำนวน cache ที่ลบออกทั้งหมด
        """
        cache_path = Path(cache_dir)
        total_deleted = 0
        
        # หาไฟล์ cache ทั้งหมด (ไม่รวม part files)
        cache_files = list(cache_path.glob("ocr_cache_*.json"))
        
        # กรองเฉพาะไฟล์หลัก (ไม่ใช่ part files)
        main_cache_files = [f for f in cache_files if '_part' not in f.stem]
        
        for cache_file in main_cache_files:
            try:
                # ดึงชื่อบริษัทจากชื่อไฟล์ (ลบ "ocr_cache_" ออก)
                company_name = cache_file.stem.replace("ocr_cache_", "")
                manager = OCRCacheManager(
                    cache_dir=str(cache_path),
                    cache_ttl_hours=cache_ttl_hours,
                    company_name=company_name
                )
                deleted = manager.cleanup_expired()
                total_deleted += deleted
            except Exception as e:
                logger.error(f"❌ Error cleaning cache file {cache_file}: {e}")
        
        return total_deleted
    
    def clear_all(self):
        """ลบ cache ทั้งหมด (สำหรับบริษัทนี้เท่านั้น)"""
        count = len(self.cache_data)
        self.cache_data = {}
        self._save_cache()
        logger.info(f"🗑️ ลบ cache ทั้งหมด: {count} รายการ (บริษัท: {self.company_name})")
    
    @staticmethod
    def clear_all_companies(cache_dir: str = "cache") -> int:
        """
        ลบ cache ทั้งหมดจากทุกบริษัท
        
        Args:
            cache_dir: โฟลเดอร์ cache
            
        Returns:
            จำนวน cache ที่ลบออกทั้งหมด
        """
        cache_path = Path(cache_dir)
        total_deleted = 0
        
        # หาไฟล์ cache ทั้งหมด (ไม่รวม part files)
        cache_files = list(cache_path.glob("ocr_cache_*.json"))
        
        # กรองเฉพาะไฟล์หลัก (ไม่ใช่ part files)
        main_cache_files = [f for f in cache_files if '_part' not in f.stem]
        
        for cache_file in main_cache_files:
            try:
                # ดึงชื่อบริษัทจากชื่อไฟล์ (ลบ "ocr_cache_" ออก)
                company_name = cache_file.stem.replace("ocr_cache_", "")
                manager = OCRCacheManager(
                    cache_dir=str(cache_path),
                    company_name=company_name
                )
                deleted = len(manager.cache_data)
                manager.clear_all()
                total_deleted += deleted
            except Exception as e:
                logger.error(f"❌ Error clearing cache file {cache_file}: {e}")
        
        return total_deleted
    
    def get_stats(self) -> Dict[str, Any]:
        """
        รับสถิติของ cache
        
        Returns:
            dictionary ประกอบด้วย total, expired_count, valid_count
        """
        current_time = time.time()
        expired_count = 0
        valid_count = 0
        
        for cache_entry in self.cache_data.values():
            cached_time = cache_entry.get('cached_at', 0)
            age_hours = (current_time - cached_time) / 3600
            
            if age_hours > self.cache_ttl_hours:
                expired_count += 1
            else:
                valid_count += 1
        
        return {
            'total': len(self.cache_data),
            'valid': valid_count,
            'expired': expired_count,
            'ttl_hours': self.cache_ttl_hours
        }
