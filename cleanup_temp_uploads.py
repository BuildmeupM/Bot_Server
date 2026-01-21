#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
สคริปต์สำหรับลบไฟล์ทั้งหมดใน temp_uploads
"""
from pathlib import Path

def cleanup_all_temp_files():
    """ลบไฟล์ทั้งหมดใน temp_uploads"""
    temp_dir = Path('temp_uploads')
    
    if not temp_dir.exists():
        print("❌ ไม่พบโฟลเดอร์ temp_uploads")
        return
    
    files = [f for f in temp_dir.glob('*') if f.is_file()]
    
    if not files:
        print("✅ ไม่มีไฟล์ให้ลบ")
        return
    
    deleted_count = 0
    failed_files = []
    
    print(f"📋 พบไฟล์ {len(files)} ไฟล์")
    print("=" * 50)
    
    for file_path in files:
        try:
            file_path.unlink()
            deleted_count += 1
            print(f"🗑️  ลบ: {file_path.name}")
        except Exception as e:
            failed_files.append((file_path.name, str(e)))
            print(f"⚠️  ไม่สามารถลบ {file_path.name}: {e}")
    
    print("=" * 50)
    print(f"✅ ลบไฟล์ {deleted_count} ไฟล์สำเร็จ")
    
    if failed_files:
        print(f"⚠️  ไม่สามารถลบ {len(failed_files)} ไฟล์:")
        for filename, error in failed_files:
            print(f"   - {filename}: {error}")

if __name__ == '__main__':
    cleanup_all_temp_files()

