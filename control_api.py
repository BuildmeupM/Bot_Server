#!/usr/bin/env python3
"""
BotV3 Control API - Flask Backend for UI Control
API สำหรับควบคุมระบบผ่าน Web UI
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from pathlib import Path
import threading
import time
from typing import Dict, List, Optional
from main_system import MainSystemOrchestrator, set_system_state
from config import Config

app = Flask(__name__)
CORS(app)

# Global state
system_state = {
    'running': False,
    'current_folder': None,
    'current_file': '-',
    'current_step': '-',
    'processed': 0,
    'errors': 0,
    'total_folders': 0,
    'total_files': 0,
    'thread': None,
    'loop_enabled': False,  # เพิ่มตัวแปรสำหรับควบคุมการลูป
    'stop_requested': False,  # เพิ่มตัวแปรสำหรับหยุดทันที
    'line_notifications_enabled': True  # เพิ่มตัวแปรสำหรับควบคุมการแจ้งเตือน LINE
}


def run_system_thread(mode: str, folders: List[str]):
    """รันระบบในเธรดแยก พร้อมการลูปอัตโนมัติ"""
    global system_state
    
    try:
        system_state['running'] = True
        system_state['stop_requested'] = False
        
        # เริ่มการทำงาน (ไม่จำเป็นต้องเป็นลูป)
        print(f"\n🚀 เริ่มการทำงาน...")
        
        system_state['processed'] = 0
        system_state['errors'] = 0
        
        if mode == 'auto':
            # ตรวจสอบว่าเลือกโฟลเดอร์เฉพาะหรือทั้งหมด
            if folders and folders != ['all']:
                # รันเฉพาะโฟลเดอร์ที่เลือก
                base_paths = []
                for folder in folders:
                    if folder in ["A.โฟร์เดอร์หลัก", "AA.โฟรเดอร์หลัก", "AAA.โฟรเดอร์หลัก"]:
                        base_paths.append(f"V:/{folder}")
            else:
                # รันทุกโฟลเดอร์หลัก
                base_paths = [
                    "V:/A.โฟร์เดอร์หลัก",
                    "V:/AA.โฟรเดอร์หลัก", 
                    "V:/AAA.โฟรเดอร์หลัก"
                ]
            
            for base_path in base_paths:
                if not system_state['running'] or system_state['stop_requested']:
                    break
                
                print(f"\n🔍 กำลังสแกน: {base_path}")
                system_state['current_folder'] = base_path
                system_state['current_step'] = 'กำลังสแกนโฟลเดอร์'
                
                # Set system state reference for main_system
                set_system_state(system_state)
                
                orchestrator = MainSystemOrchestrator(base_path)
                orchestrator.run_all_main_folders()
                
                # Update stats
                for result in orchestrator.results:
                    if result['status'] == 'success':
                        system_state['processed'] += result.get('success_count', 0)
                    else:
                        system_state['errors'] += 1
        else:
            # รันเฉพาะโฟลเดอร์ที่เลือก
            for folder_path in folders:
                if not system_state['running'] or system_state['stop_requested']:
                    break
                
                system_state['current_folder'] = folder_path
                system_state['current_step'] = 'กำลังประมวลผลโฟลเดอร์'
                
                # Set system state reference for main_system
                set_system_state(system_state)
                
                # ใช้ run_all_main_folders เหมือนกับโหมด auto
                orchestrator = MainSystemOrchestrator(folder_path)
                orchestrator.run_all_main_folders()
                
                # Update stats
                for result in orchestrator.results:
                    if result['status'] == 'success':
                        system_state['processed'] += result.get('success_count', 0)
                    else:
                        system_state['errors'] += 1
    
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        system_state['errors'] += 1
    
    finally:
        system_state['running'] = False
        system_state['current_folder'] = None
        system_state['current_file'] = '-'
        system_state['current_step'] = '-'
        print("✅ ระบบทำงานเสร็จสิ้น")


def run_loop_thread(mode: str, folders: List[str]):
    """รันระบบแบบลูปต่อเนื่องในเธรดแยก"""
    global system_state
    
    try:
        system_state['running'] = True
        system_state['loop_enabled'] = True
        system_state['stop_requested'] = False
        
        # ลูปการทำงาน
        loop_count = 0
        while system_state['loop_enabled'] and not system_state['stop_requested']:
            loop_count += 1
            print(f"\n🔄 เริ่มรอบการทำงานที่ {loop_count}")
            
            system_state['processed'] = 0
            system_state['errors'] = 0
            
            if mode == 'auto':
                # ตรวจสอบว่าเลือกโฟลเดอร์เฉพาะหรือทั้งหมด
                if folders and folders != ['all']:
                    # รันเฉพาะโฟลเดอร์ที่เลือก
                    base_paths = []
                    for folder in folders:
                        if folder in ["A.โฟร์เดอร์หลัก", "AA.โฟรเดอร์หลัก", "AAA.โฟรเดอร์หลัก"]:
                            base_paths.append(f"V:/{folder}")
                else:
                    # รันทุกโฟลเดอร์หลัก
                    base_paths = [
                        "V:/A.โฟร์เดอร์หลัก",
                        "V:/AA.โฟรเดอร์หลัก", 
                        "V:/AAA.โฟรเดอร์หลัก"
                    ]
                
                for base_path in base_paths:
                    if not system_state['running'] or system_state['stop_requested']:
                        break
                    
                    print(f"\n🔍 กำลังสแกน: {base_path}")
                    system_state['current_folder'] = base_path
                    system_state['current_step'] = 'กำลังสแกนโฟลเดอร์'
                    
                    # Set system state reference for main_system
                    set_system_state(system_state)
                    
                    orchestrator = MainSystemOrchestrator(base_path)
                    orchestrator.run_all_main_folders()
                    
                    # Update stats
                    for result in orchestrator.results:
                        if result['status'] == 'success':
                            system_state['processed'] += result.get('success_count', 0)
                        else:
                            system_state['errors'] += 1
            else:
                # รันเฉพาะโฟลเดอร์ที่เลือก
                for folder_path in folders:
                    if not system_state['running'] or system_state['stop_requested']:
                        break
                    
                    system_state['current_folder'] = folder_path
                    system_state['current_step'] = 'กำลังประมวลผลโฟลเดอร์'
                    
                    # Set system state reference for main_system
                    set_system_state(system_state)
                    
                    # ใช้ run_all_main_folders เหมือนกับโหมด auto
                    orchestrator = MainSystemOrchestrator(folder_path)
                    orchestrator.run_all_main_folders()
                    
                    # Update stats
                    for result in orchestrator.results:
                        if result['status'] == 'success':
                            system_state['processed'] += result.get('success_count', 0)
                        else:
                            system_state['errors'] += 1
            
            # ตรวจสอบว่าต้องหยุดหรือไม่
            if system_state['stop_requested']:
                print("🛑 หยุดการทำงานตามคำขอ")
                break
            
            # รอ 15 วินาทีก่อนรอบถัดไป (ตรวจสอบหยุดทุกวินาที)
            print(f"⏳ รอ 15 วินาทีก่อนรอบถัดไป...")
            system_state['current_step'] = f'รอบที่ {loop_count} - รอ 15 วินาที'
            for i in range(15):
                if system_state['stop_requested']:
                    print("🛑 หยุดการทำงานระหว่างรอ")
                    break
                time.sleep(1)
                system_state['current_step'] = f'รอบที่ {loop_count} - รอ {i+1}/15 วินาที'
                print(f"   รอ... {i+1}/15 วินาที")
    
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        system_state['errors'] += 1
    
    finally:
        system_state['running'] = False
        system_state['loop_enabled'] = False
        system_state['current_folder'] = None
        system_state['current_file'] = '-'
        system_state['current_step'] = '-'
        print("✅ ระบบลูปทำงานเสร็จสิ้น")


@app.route('/')
def index():
    """หน้าหลัก"""
    return send_from_directory('.', 'main_control.html')


@app.route('/api/system/scan', methods=['GET'])
def scan_folders():
    """สแกนโฟลเดอร์ทั้งหมด"""
    try:
        base_paths = [
            Path("V:/A.โฟร์เดอร์หลัก"),
            Path("V:/AA.โฟรเดอร์หลัก"),
            Path("V:/AAA.โฟรเดอร์หลัก")
        ]
        
        total_folders = 0
        total_files = 0
        folder_info = []
        
        for base_path in base_paths:
            if not base_path.exists():
                continue
            
            # นับโฟลเดอร์ Build*
            build_folders = list(base_path.glob("Build*"))
            folder_count = len(build_folders)
            
            # นับไฟล์ PDF
            file_count = 0
            for build_folder in build_folders:
                # ค้นหาโฟลเดอร์ระบบอัตโนมัติ
                for automation_folder in build_folder.rglob("*ระบบอัตโนมัติ*"):
                    if automation_folder.is_dir():
                        pdf_files = list(automation_folder.rglob("*.pdf"))
                        file_count += len(pdf_files)
            
            total_folders += folder_count
            total_files += file_count
            
            folder_info.append({
                'name': base_path.name,
                'path': str(base_path),
                'exists': True,
                'subfolders': folder_count,
                'files': file_count
            })
        
        # Update global state
        system_state['total_folders'] = total_folders
        system_state['total_files'] = total_files
        
        return jsonify({
            'success': True,
            'total_folders': total_folders,
            'total_files': total_files,
            'folders': folder_info
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'เกิดข้อผิดพลาด: {str(e)}'
        }), 500


@app.route('/api/system/start', methods=['POST'])
def start_system():
    """เริ่มระบบ"""
    global system_state
    
    if system_state['running']:
        return jsonify({
            'success': False,
            'message': 'ระบบกำลังทำงานอยู่แล้ว'
        }), 400
    
    try:
        data = request.json
        mode = data.get('mode', 'auto')
        folders = data.get('folders', [])
        loop_enabled = data.get('loop', False)  # เพิ่มการรับค่า loop
        
        # Start system in background thread
        if loop_enabled:
            # ใช้ฟังก์ชันลูป
            thread = threading.Thread(
                target=run_loop_thread,
                args=(mode, folders),
                daemon=True
            )
            message = 'เริ่มระบบลูปสำเร็จ'
        else:
            # ใช้ฟังก์ชันปกติ
            thread = threading.Thread(
                target=run_system_thread,
                args=(mode, folders),
                daemon=True
            )
            message = 'เริ่มระบบสำเร็จ'
        
        thread.start()
        system_state['thread'] = thread
        
        return jsonify({
            'success': True,
            'message': message
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'เกิดข้อผิดพลาด: {str(e)}'
        }), 500


@app.route('/api/system/stop', methods=['POST'])
def stop_system():
    """หยุดระบบ"""
    global system_state
    
    if not system_state['running']:
        return jsonify({
            'success': False,
            'message': 'ระบบไม่ได้ทำงานอยู่'
        }), 400
    
    system_state['running'] = False
    system_state['loop_enabled'] = False
    system_state['stop_requested'] = True
    system_state['current_folder'] = None
    system_state['current_file'] = '-'
    system_state['current_step'] = '-'
    
    return jsonify({
        'success': True,
        'message': 'หยุดระบบทันที'
    })



@app.route('/api/system/status', methods=['GET'])
def get_status():
    """ดูสถานะระบบ"""
    return jsonify({
        'running': system_state['running'],
        'current_folder': system_state['current_folder'],
        'current_file': system_state.get('current_file', '-'),
        'current_step': system_state.get('current_step', '-'),
        'processed': system_state['processed'],
        'errors': system_state['errors'],
        'total_folders': system_state['total_folders'],
        'total_files': system_state['total_files'],
        'loop_enabled': system_state['loop_enabled'],
        'stop_requested': system_state['stop_requested'],
        'line_notifications_enabled': system_state['line_notifications_enabled']
    })


@app.route('/api/system/line-notifications/toggle', methods=['POST'])
def toggle_line_notifications():
    """เปิด/ปิดการแจ้งเตือน LINE"""
    global system_state
    
    try:
        data = request.json
        enabled = data.get('enabled', not system_state['line_notifications_enabled'])
        
        system_state['line_notifications_enabled'] = enabled
        
        # อัปเดตการตั้งค่าใน report_manager
        try:
            from report_manager import set_line_notifications_enabled
            set_line_notifications_enabled(enabled)
        except ImportError:
            pass
        
        status = "เปิด" if enabled else "ปิด"
        return jsonify({
            'success': True,
            'message': f'{status}การแจ้งเตือน LINE แล้ว',
            'enabled': enabled
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'เกิดข้อผิดพลาด: {str(e)}'
        }), 500


@app.route('/api/system/line-notifications/status', methods=['GET'])
def get_line_notifications_status():
    """ดูสถานะการแจ้งเตือน LINE"""
    return jsonify({
        'enabled': system_state['line_notifications_enabled']
    })



def test_system():
    """ทดสอบระบบ"""
    try:
        results = {}
        
        # Test 1: Check if folders exist
        base_paths = [
            Path("V:/A.โฟร์เดอร์หลัก"),
            Path("V:/AA.โฟรเดอร์หลัก"),
            Path("V:/AAA.โฟรเดอร์หลัก")
        ]
        
        folders_exist = []
        for base_path in base_paths:
            folders_exist.append(f"{base_path.name}: {'✓' if base_path.exists() else '✗'}")
        
        results['โฟลเดอร์'] = ', '.join(folders_exist)
        
        # Test 2: Check imports
        try:
            from pdf_reader import PDFReader
            from web_automation_playwright import WebAutomationPlaywright
            from file_manager import FileManager
            results['โมดูล'] = '✓ ทุกโมดูลพร้อมใช้งาน'
        except ImportError as e:
            results['โมดูล'] = f'✗ ขาดโมดูล: {str(e)}'
        
        # Test 3: Check Playwright
        try:
            from playwright.sync_api import sync_playwright
            results['Playwright'] = '✓ พร้อมใช้งาน'
        except ImportError:
            results['Playwright'] = '✗ ยังไม่ได้ติดตั้ง'
        
        # Test 4: Check LINE config
        if Config.LINE_OA_CHANNEL_ACCESS_TOKEN:
            results['LINE OA'] = '✓ ตั้งค่าแล้ว'
        elif Config.LINE_NOTIFY_TOKEN:
            results['LINE Notify'] = '✓ ตั้งค่าแล้ว'
        else:
            results['LINE'] = '⚠ ยังไม่ได้ตั้งค่า'
        
        return jsonify({
            'success': True,
            'message': 'ทดสอบระบบเสร็จสิ้น',
            'results': results
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'เกิดข้อผิดพลาด: {str(e)}'
        }), 500

@app.route('/api/system/test', methods=['POST'])
def test_system_endpoint():
    """ทดสอบระบบ"""
    return test_system()


@app.route('/api/system/test-run', methods=['POST'])
def test_run_system():
    """ทดสอบรันระบบในโฟลเดอร์เดียว"""
    global system_state
    
    if system_state['running']:
        return jsonify({
            'success': False,
            'message': 'ระบบกำลังทำงานอยู่แล้ว'
        }), 400
    
    try:
        # ตั้งค่าโฟลเดอร์ทดสอบ
        test_folder = "V:/A.โฟร์เดอร์หลัก/Build000 ทดสอบระบบ/ลูกค้า/ระบบอัตโนมัติ"
        
        print(f"\n🧪 เริ่มทดสอบระบบ...")
        print(f"📂 โฟลเดอร์ทดสอบ: {test_folder}")
        
        # เริ่มระบบทดสอบในเธรดแยก
        thread = threading.Thread(
            target=run_test_thread,
            args=(test_folder,),
            daemon=True
        )
        thread.start()
        system_state['thread'] = thread
        
        return jsonify({
            'success': True,
            'message': f'เริ่มทดสอบระบบในโฟลเดอร์: {test_folder}'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'เกิดข้อผิดพลาด: {str(e)}'
        }), 500


def run_test_thread(test_folder: str):
    """รันระบบทดสอบในเธรดแยก"""
    global system_state
    
    try:
        system_state['running'] = True
        system_state['stop_requested'] = False
        system_state['processed'] = 0
        system_state['errors'] = 0
        
        print(f"\n🧪 เริ่มทดสอบระบบ...")
        print(f"📂 โฟลเดอร์ทดสอบ: {test_folder}")
        
        # ปิดการแจ้งเตือน LINE สำหรับการทดสอบ
        original_line_status = system_state['line_notifications_enabled']
        system_state['line_notifications_enabled'] = False
        print("🔕 ปิดการแจ้งเตือน LINE สำหรับการทดสอบ")
        
        # ตั้งค่าสถานะ
        system_state['current_folder'] = test_folder
        system_state['current_step'] = 'กำลังทดสอบระบบ'
        
        # Set system state reference for main_system
        set_system_state(system_state)
        
        # สร้าง orchestrator และรันโฟลเดอร์เดียว
        orchestrator = MainSystemOrchestrator()
        orchestrator.run_single_folder(test_folder)
        
        # Update stats
        for result in orchestrator.results:
            if result['status'] == 'success':
                system_state['processed'] += result.get('success_count', 0)
            else:
                system_state['errors'] += 1
        
        print(f"\n✅ ทดสอบระบบเสร็จสิ้น")
        print(f"📊 ผลลัพธ์: ประมวลผลสำเร็จ {system_state['processed']} ไฟล์, ข้อผิดพลาด {system_state['errors']} ครั้ง")
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการทดสอบ: {e}")
        system_state['errors'] += 1
    
    finally:
        # คืนสถานะการแจ้งเตือน LINE กลับเป็นเดิม
        system_state['line_notifications_enabled'] = original_line_status
        print(f"🔔 คืนสถานะการแจ้งเตือน LINE: {'เปิด' if original_line_status else 'ปิด'}")
        
        system_state['running'] = False
        system_state['current_folder'] = None
        system_state['current_file'] = '-'
        system_state['current_step'] = '-'
        print("✅ ระบบทดสอบทำงานเสร็จสิ้น")


if __name__ == '__main__':
    print("🚀 Starting BotV3 Control API...")
    print("📡 API available at: http://localhost:5000")
    print("🌐 Web UI available at: http://localhost:5000")
    print("\n💡 Press Ctrl+C to stop\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

