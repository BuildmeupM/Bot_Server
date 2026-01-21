#!/usr/bin/env python3
"""
สคริปต์เพื่อดีบัก environment และเปรียบเทียบผลลัพธ์
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

def debug_environment():
    """ตรวจสอบ environment ปัจจุบัน"""
    print("=== Debug Environment Information ===")
    print(f"Python Version: {sys.version}")
    print(f"Current Working Directory: {os.getcwd()}")
    print(f"Python Path: {sys.executable}")
    print(f"Script Path: {__file__}")
    print(f"Platform: {sys.platform}")
    print()
    
    print("=== Environment Variables ===")
    important_vars = ['PATH', 'PYTHONPATH', 'VIRTUAL_ENV']
    for var in important_vars:
        value = os.environ.get(var, 'Not Set')
        print(f"{var}: {value[:100]}..." if len(str(value)) > 100 else f"{var}: {value}")
    print()
    
    print("=== Current Directory Contents ===")
    current_dir = Path('.')
    try:
        files = list(current_dir.iterdir())
        print(f"Found {len(files)} items:")
        for file in files[:10]:  # แสดงแค่ 10 ไฟล์แรก
            print(f"  - {file.name}")
        if len(files) > 10:
            print(f"  ... และอีก {len(files) - 10} ไฟล์")
    except Exception as e:
        print(f"Error listing directory: {e}")
    print()
    
    print("=== Python Modules (Important) ===")
    important_modules = ['selenium', 'pathlib', 'requests']
    for module in important_modules:
        try:
            imported = __import__(module)
            if hasattr(imported, '__version__'):
                print(f"{module}: {imported.__version__}")
            else:
                print(f"{module}: Available (no version info)")
        except ImportError as e:
            print(f"{module}: NOT AVAILABLE - {e}")
    print()
    
    print("=== File System Check ===")
    # ตรวจสอบ V: drive
    v_drive = Path("V:/")
    if v_drive.exists():
        print("✅ V: drive available")
        test_folder = Path("V:/A.โฟร์เดอร์หลัก/Build000 ทดสอบระบบ")
        if test_folder.exists():
            print("✅ Test folder available")
            # นับไฟล์ในโฟลเดอร์รหัส
            code_folder = test_folder / "รหัส"
            if code_folder.exists():
                try:
                    files = list(code_folder.iterdir())
                    json_files = len([f for f in files if f.suffix.lower() == '.json'])
                    txt_files = len([f for f in files if f.suffix.lower() == '.txt'])
                    print(f"✅ Code folder: {json_files} JSON, {txt_files} TXT files")
                except Exception as e:
                    print(f"❌ Error counting files: {e}")
            else:
                print("❌ Code folder not found")
        else:
            print("❌ Test folder not found")
    else:
        print("❌ V: drive not available")
    print()
    
    return {
        'timestamp': datetime.now().isoformat(),
        'python_version': sys.version,
        'cwd': os.getcwd(),
        'python_path': sys.executable,
        'platform': sys.platform,
        'v_drive_available': v_drive.exists() if 'v_drive' in locals() else False
    }

if __name__ == "__main__":
    result = debug_environment()
    
    # บันทึกผลลัพธ์
    output_file = f"debug_env_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"Results saved to: {output_file}")
