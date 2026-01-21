"""
Excel State Manager - ระบบจัดการสถานะการทำงาน Excel
เพื่อรองรับการ Resume และป้องกันความผิดพลาด
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime
import hashlib


class ExcelStateManager:
    """จัดการสถานะการทำงาน Excel เพื่อรองรับการ Resume"""
    
    def __init__(self, excel_path: str):
        """
        Args:
            excel_path: Path ของไฟล์ Excel
        """
        self.excel_path = excel_path
        self.excel_dir = os.path.dirname(excel_path) if os.path.exists(excel_path) else None
        
        # สร้าง state file path (อยู่ในโฟลเดอร์เดียวกับ Excel)
        excel_filename = os.path.basename(excel_path)
        state_filename = f".{excel_filename}.state.json"
        self.state_file_path = os.path.join(self.excel_dir, state_filename) if self.excel_dir else None
        
        # เก็บสถานะใน memory
        self.state: Dict = {
            'excel_path': excel_path,
            'excel_hash': self._calculate_file_hash(excel_path),
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'completed_sequences': [],  # List of sequence numbers ที่เสร็จแล้ว
            'failed_sequences': [],  # List of sequence numbers ที่ล้มเหลว
            'skipped_sequences': [],  # List of sequence numbers ที่ข้าม (เช่น ไฟล์ไม่พบ)
            'file_validation': {},  # เก็บผลการตรวจสอบไฟล์ PDF สำหรับแต่ละ sequence
            'total_sequences': 0,
            'processed_count': 0,
            'version': '1.0'
        }
        
        # โหลด state จากไฟล์ (ถ้ามี)
        self.load_state()
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """คำนวณ hash ของไฟล์ Excel เพื่อตรวจสอบว่าไฟล์เปลี่ยนหรือไม่"""
        try:
            if not os.path.exists(file_path):
                return ""
            
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                # อ่านเฉพาะส่วนแรกของไฟล์ (1024 bytes) เพื่อความเร็ว
                chunk = f.read(1024)
                hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
    
    def load_state(self) -> bool:
        """โหลด state จากไฟล์"""
        if not self.state_file_path or not os.path.exists(self.state_file_path):
            return False
        
        try:
            with open(self.state_file_path, 'r', encoding='utf-8') as f:
                loaded_state = json.load(f)
                
                # ตรวจสอบว่าเป็นไฟล์ Excel เดียวกันหรือไม่ (ตรวจสอบ hash)
                if loaded_state.get('excel_hash') == self.state['excel_hash']:
                    self.state.update(loaded_state)
                    self.state['last_updated'] = datetime.now().isoformat()
                    return True
                else:
                    # ไฟล์ Excel เปลี่ยน → reset state
                    self._log(f"⚠️ ไฟล์ Excel เปลี่ยน → รีเซ็ต state")
                    return False
        except Exception as e:
            print(f"⚠️ ไม่สามารถโหลด state file: {e}")
            return False
    
    def save_state(self) -> bool:
        """บันทึก state ลงไฟล์ (ต้องบันทึกที่โฟลเดอร์เดียวกับไฟล์ Excel เท่านั้น)"""
        if not self.state_file_path:
            return False
        
        try:
            self.state['last_updated'] = datetime.now().isoformat()
            with open(self.state_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
            return True
        except PermissionError as e:
            # ถ้าไม่มี permission ให้ log warning แต่ไม่บันทึกใน temp directory
            print(f"⚠️ ไม่สามารถบันทึก state file ที่ตำแหน่งเดิม (Permission denied): {self.state_file_path}")
            print(f"   ระบบจะไม่สามารถ Resume ได้ แต่จะทำงานต่อได้ปกติ")
            return False
        except Exception as e:
            print(f"⚠️ ไม่สามารถบันทึก state file: {e}")
            return False
    
    def is_sequence_completed(self, sequence: str) -> bool:
        """ตรวจสอบว่า sequence นี้เสร็จแล้วหรือยัง"""
        return sequence in self.state['completed_sequences']
    
    def is_sequence_failed(self, sequence: str) -> bool:
        """ตรวจสอบว่า sequence นี้ล้มเหลวหรือยัง"""
        return sequence in self.state['failed_sequences']
    
    def is_sequence_skipped(self, sequence: str) -> bool:
        """ตรวจสอบว่า sequence นี้ถูกข้ามหรือยัง"""
        return sequence in self.state['skipped_sequences']
    
    def mark_sequence_completed(self, sequence: str) -> bool:
        """ทำเครื่องหมายว่า sequence นี้เสร็จแล้ว"""
        if sequence not in self.state['completed_sequences']:
            self.state['completed_sequences'].append(sequence)
            # ลบออกจาก failed_sequences และ skipped_sequences (ถ้ามี)
            if sequence in self.state['failed_sequences']:
                self.state['failed_sequences'].remove(sequence)
            if sequence in self.state['skipped_sequences']:
                self.state['skipped_sequences'].remove(sequence)
            self.state['processed_count'] = len(self.state['completed_sequences'])
            return self.save_state()
        return True
    
    def mark_sequence_failed(self, sequence: str, reason: str = "") -> bool:
        """ทำเครื่องหมายว่า sequence นี้ล้มเหลว"""
        if sequence not in self.state['failed_sequences']:
            self.state['failed_sequences'].append(sequence)
            # ลบออกจาก completed_sequences (ถ้ามี)
            if sequence in self.state['completed_sequences']:
                self.state['completed_sequences'].remove(sequence)
            return self.save_state()
        return True
    
    def mark_sequence_skipped(self, sequence: str, reason: str = "") -> bool:
        """ทำเครื่องหมายว่า sequence นี้ถูกข้าม"""
        if sequence not in self.state['skipped_sequences']:
            self.state['skipped_sequences'].append(sequence)
            # บันทึก reason
            if 'skip_reasons' not in self.state:
                self.state['skip_reasons'] = {}
            self.state['skip_reasons'][sequence] = reason
            return self.save_state()
        return True
    
    def validate_files_for_sequence(self, sequence: str, rows: List[Dict]) -> Dict:
        """
        ตรวจสอบว่าไฟล์ PDF สำหรับ sequence นี้มีครบหรือไม่
        
        Returns:
            Dict with keys:
                - valid: bool
                - missing_files: List[str] - รายชื่อไฟล์ที่หาไม่เจอ
                - found_files: List[str] - รายชื่อไฟล์ที่พบ
        """
        result = {
            'valid': True,
            'missing_files': [],
            'found_files': []
        }
        
        if not self.excel_dir:
            result['valid'] = False
            result['missing_files'] = ['ไม่พบโฟลเดอร์ Excel']
            return result
        
        for row in rows:
            old_filename = row.get('ชื่อไฟล์เก่า', '').strip()
            if not old_filename:
                continue
            
            file_path = os.path.join(self.excel_dir, old_filename)
            if os.path.exists(file_path):
                result['found_files'].append(old_filename)
            else:
                result['missing_files'].append(old_filename)
                result['valid'] = False
        
        # บันทึกผลการตรวจสอบ
        if 'file_validation' not in self.state:
            self.state['file_validation'] = {}
        self.state['file_validation'][sequence] = result
        self.save_state()
        
        return result
    
    def get_completed_sequences(self) -> Set[str]:
        """คืนค่า set ของ sequence ที่เสร็จแล้ว"""
        return set(self.state['completed_sequences'])
    
    def get_failed_sequences(self) -> Set[str]:
        """คืนค่า set ของ sequence ที่ล้มเหลว"""
        return set(self.state['failed_sequences'])
    
    def get_skipped_sequences(self) -> Set[str]:
        """คืนค่า set ของ sequence ที่ถูกข้าม"""
        return set(self.state['skipped_sequences'])
    
    def get_progress_summary(self) -> Dict:
        """คืนค่าสรุปความคืบหน้า"""
        total = self.state.get('total_sequences', 0)
        completed = len(self.state['completed_sequences'])
        failed = len(self.state['failed_sequences'])
        skipped = len(self.state['skipped_sequences'])
        remaining = total - completed - failed - skipped
        
        return {
            'total': total,
            'completed': completed,
            'failed': failed,
            'skipped': skipped,
            'remaining': remaining,
            'progress_percent': (completed / total * 100) if total > 0 else 0
        }
    
    def reset_state(self) -> bool:
        """รีเซ็ต state ทั้งหมด"""
        self.state = {
            'excel_path': self.excel_path,
            'excel_hash': self._calculate_file_hash(self.excel_path),
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'completed_sequences': [],
            'failed_sequences': [],
            'skipped_sequences': [],
            'file_validation': {},
            'total_sequences': 0,
            'processed_count': 0,
            'version': '1.0'
        }
        return self.save_state()
    
    def delete_state_file(self) -> bool:
        """ลบ state file"""
        if self.state_file_path and os.path.exists(self.state_file_path):
            try:
                os.remove(self.state_file_path)
                return True
            except Exception as e:
                print(f"⚠️ ไม่สามารถลบ state file: {e}")
                return False
        return False
    
    def _log(self, message: str, level: str = "info"):
        """Helper method สำหรับ log (จะถูก override โดย WebAutomationPlaywright)"""
        print(f"[{level.upper()}] {message}")

