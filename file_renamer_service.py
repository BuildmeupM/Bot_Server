"""
File Renamer Service
===================
Service สำหรับเปลี่ยนชื่อไฟล์ PDF อัตโนมัติ

Author: BotV3
Version: 1.0.0
"""

import logging
from pathlib import Path
from typing import Optional, Tuple
import shutil

logger = logging.getLogger(__name__)


class FileRenamerService:
    """Service สำหรับเปลี่ยนชื่อไฟล์"""
    
    def __init__(self):
        """Initialize File Renamer Service"""
        pass
    
    def rename_file(
        self, 
        original_path: str, 
        new_filename: str,
        backup: bool = True
    ) -> Tuple[bool, str, Optional[str]]:
        """
        เปลี่ยนชื่อไฟล์
        
        Args:
            original_path: Path ของไฟล์เดิม
            new_filename: ชื่อไฟล์ใหม่ (รวม extension)
            backup: สำรองไฟล์เดิมหรือไม่
        
        Returns:
            (success, message, new_path)
        """
        try:
            original_file = Path(original_path)
            
            # ตรวจสอบว่าไฟล์เดิมมีอยู่จริง
            if not original_file.exists():
                return False, f"ไม่พบไฟล์: {original_path}", None
            
            # สร้าง path ใหม่
            new_path = original_file.parent / new_filename
            
            # ตรวจสอบว่าไฟล์ใหม่มีอยู่แล้วหรือไม่
            if new_path.exists():
                logger.warning(f"⚠️ ไฟล์ {new_filename} มีอยู่แล้ว")
                return False, f"ไฟล์ {new_filename} มีอยู่แล้ว", None
            
            # สำรองไฟล์เดิม (ถ้าต้องการ)
            backup_path = None
            if backup:
                backup_folder = original_file.parent / "_backup"
                backup_folder.mkdir(exist_ok=True)
                backup_path = backup_folder / original_file.name
                
                try:
                    shutil.copy2(original_file, backup_path)
                    logger.info(f"📦 สำรองไฟล์: {backup_path}")
                except Exception as e:
                    logger.warning(f"⚠️ ไม่สามารถสำรองไฟล์: {e}")
            
            # เปลี่ยนชื่อไฟล์
            original_file.rename(new_path)
            
            logger.info(f"✅ เปลี่ยนชื่อไฟล์สำเร็จ: {original_file.name} → {new_filename}")
            
            message = f"เปลี่ยนชื่อไฟล์สำเร็จ: {original_file.name} → {new_filename}"
            if backup_path:
                message += f"\n📦 สำรองไฟล์ไว้ที่: {backup_path}"
            
            return True, message, str(new_path)
        
        except Exception as e:
            logger.error(f"❌ เกิดข้อผิดพลาดในการเปลี่ยนชื่อไฟล์: {e}", exc_info=True)
            return False, f"เกิดข้อผิดพลาด: {e}", None
    
    def batch_rename(
        self, 
        files_mapping: dict,
        backup: bool = True
    ) -> Tuple[int, int, list]:
        """
        เปลี่ยนชื่อไฟล์หลายไฟล์พร้อมกัน
        
        Args:
            files_mapping: Dictionary {original_path: new_filename}
            backup: สำรองไฟล์เดิมหรือไม่
        
        Returns:
            (success_count, fail_count, results)
        """
        success_count = 0
        fail_count = 0
        results = []
        
        for original_path, new_filename in files_mapping.items():
            success, message, new_path = self.rename_file(
                original_path, 
                new_filename, 
                backup=backup
            )
            
            if success:
                success_count += 1
            else:
                fail_count += 1
            
            results.append({
                'original_path': original_path,
                'new_filename': new_filename,
                'new_path': new_path,
                'success': success,
                'message': message
            })
        
        return success_count, fail_count, results


# ===== Helper Functions =====

def rename_pdf_file(
    original_path: str, 
    new_filename: str,
    backup: bool = True
) -> Tuple[bool, str]:
    """
    Helper function สำหรับเปลี่ยนชื่อไฟล์ PDF
    
    Args:
        original_path: Path ของไฟล์เดิม
        new_filename: ชื่อไฟล์ใหม่ (ถ้าไม่มี .pdf จะเพิ่มให้อัตโนมัติ)
        backup: สำรองไฟล์เดิมหรือไม่
    
    Returns:
        (success, message)
    """
    # เพิ่ม .pdf ถ้าไม่มี
    if not new_filename.lower().endswith('.pdf'):
        new_filename += '.pdf'
    
    renamer = FileRenamerService()
    success, message, _ = renamer.rename_file(original_path, new_filename, backup)
    
    return success, message


# ===== Usage Example =====
if __name__ == "__main__":
    # ตัวอย่างการใช้งาน
    original_path = "EXC-2511-008_007.pdf"
    new_filename = "2511200301.pdf"
    
    success, message = rename_pdf_file(original_path, new_filename, backup=True)
    
    print("=" * 80)
    print("🔄 File Renamer Result")
    print("=" * 80)
    print(f"Success: {success}")
    print(f"Message: {message}")
    print("=" * 80)

