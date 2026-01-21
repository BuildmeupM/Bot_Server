"""
BotV3 GUI Application - Streamlit Version
Web Application แบบ Streamlit - หน้าประมวลผล PDF
"""

import streamlit as st
from pathlib import Path
from datetime import datetime
import json
import time
import threading
import uuid
from typing import Optional, Dict, List, Tuple
import pandas as pd
import sys
import os
import asyncio

# เพิ่ม current directory เข้า sys.path เพื่อให้สามารถ import โมดูลได้
# โดยเฉพาะเมื่อรันผ่าน Streamlit บน network drive
# สำหรับไฟล์ใน pages/ ต้องใช้ parent.parent เพื่อไปที่ root directory
try:
    script_path = Path(__file__)
    if script_path.exists():
        # ไฟล์อยู่ใน pages/ ดังนั้นต้องไปที่ parent.parent (root)
        current_dir = script_path.parent.parent.resolve()
    else:
        current_dir = Path(os.path.abspath(__file__)).parent.parent
except Exception:
    try:
        current_dir = Path(os.getcwd())
    except Exception:
        current_dir = Path.cwd()

# เพิ่ม path เข้า sys.path
if current_dir and str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# ตรวจสอบว่าไฟล์โมดูลที่จำเป็นมีอยู่หรือไม่
required_modules = ['config.py', 'main_system.py', 'report_manager.py']
missing_modules = []
for module in required_modules:
    module_path = current_dir / module
    if not module_path.exists():
        missing_modules.append(module)

if missing_modules:
    print(f"⚠️ ไม่พบไฟล์โมดูล: {', '.join(missing_modules)}")
    print(f"📂 กำลังค้นหาใน: {current_dir}")

# บังคับใช้ Proactor event loop สำหรับ Windows (ต้องทำก่อน import อื่นๆ)
if sys.platform == 'win32':
    try:
        try:
            loop = asyncio.get_event_loop()
            if not isinstance(loop, asyncio.ProactorEventLoop):
                loop.close()
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                print("✅ ตั้งค่า Proactor event loop สำเร็จ")
        except RuntimeError:
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            asyncio.set_event_loop(asyncio.new_event_loop())
            print("✅ สร้าง Proactor event loop ใหม่สำเร็จ")
    except Exception as e:
        print(f"⚠️ ไม่สามารถตั้งค่า Proactor event loop: {e}")

# Import modules with error handling
try:
    from config import Config
    from main_system import MainSystemOrchestrator
    from report_manager import get_global_report_manager, set_line_notifications_enabled
except ImportError as e:
    import traceback
    error_msg = f"""
    ❌ ไม่สามารถ import โมดูลได้: {e}
    
    ตรวจสอบว่า:
    1. ไฟล์ config.py, main_system.py, report_manager.py อยู่ในโฟลเดอร์เดียวกัน
    2. Python path ถูกต้อง
    3. โมดูลที่จำเป็นถูกติดตั้งแล้ว
    
    Current directory: {Path.cwd()}
    Script directory: {Path(__file__).parent.parent.resolve()}
    Python path: {sys.path[:3]}
    """
    print(error_msg)
    traceback.print_exc()
    class Config:
        BASE_FOLDER = "V"
        MAIN_FOLDERS = []
        SKIP_FOLDERS = []
        CUSTOMER_FOLDER = "ลูกค้า"
        AUTOMATION_FOLDER = "ระบบอัตโนมัติ"
    
    class MainSystemOrchestrator:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("ไม่สามารถโหลด MainSystemOrchestrator ได้ กรุณาตรวจสอบการติดตั้ง")
    
    def get_global_report_manager():
        return None
    
    def set_line_notifications_enabled(*args, **kwargs):
        pass

# ตั้งค่า page config
st.set_page_config(
    page_title="BotV3 - ระบบประมวลผล PDF อัตโนมัติ",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #2c3e50 0%, #34495e 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
    }
    .status-success {
        color: #27ae60;
        font-weight: bold;
    }
    .status-warning {
        color: #f39c12;
        font-weight: bold;
    }
    .status-error {
        color: #e74c3c;
        font-weight: bold;
    }
    .folder-card {
        background: white;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .log-container {
        background: #1e1e1e;
        color: #00ff00;
        padding: 15px;
        border-radius: 8px;
        font-family: 'Consolas', monospace;
        max-height: 600px;
        overflow-y: auto;
    }
    </style>
""", unsafe_allow_html=True)

JOB_LOG_LIMIT = 200
job_store_lock = threading.Lock()
job_store: Dict[str, Dict] = {}
folder_locks: Dict[str, str] = {}

# ---------- Job management helpers ----------

def _normalize_folder_path(folder_path: str) -> str:
    """Normalize folder path เพื่อเปรียบเทียบโฟลเดอร์เดียวกันแม้ path จะต่างกัน"""
    try:
        folder = Path(folder_path)
        normalized = str(folder.resolve())
        normalized = normalized.replace('\\', '/')
        return normalized.lower()
    except Exception:
        return str(Path(folder_path)).replace('\\', '/').lower()

def _is_folder_locked(folder_path: str) -> Tuple[bool, Optional[str]]:
    """ตรวจสอบว่าโฟลเดอร์กำลังถูกประมวลผลอยู่หรือไม่"""
    normalized_path = _normalize_folder_path(folder_path)
    with job_store_lock:
        if normalized_path in folder_locks:
            job_id = folder_locks[normalized_path]
            job = job_store.get(job_id)
            if job and job.get('status') in ('pending', 'running'):
                return True, job_id
            else:
                folder_locks.pop(normalized_path, None)
        return False, None

def _lock_folder(folder_path: str, job_id: str) -> bool:
    """Lock โฟลเดอร์เพื่อป้องกันการรันพร้อมกัน"""
    normalized_path = _normalize_folder_path(folder_path)
    with job_store_lock:
        if normalized_path in folder_locks:
            existing_job_id = folder_locks[normalized_path]
            existing_job = job_store.get(existing_job_id)
            if existing_job and existing_job.get('status') in ('pending', 'running'):
                return False
            else:
                folder_locks.pop(normalized_path, None)
        
        folder_locks[normalized_path] = job_id
        return True

def _unlock_folder(folder_path: str, job_id: str):
    """Unlock โฟลเดอร์เมื่องานเสร็จสิ้น"""
    normalized_path = _normalize_folder_path(folder_path)
    with job_store_lock:
        if normalized_path in folder_locks and folder_locks[normalized_path] == job_id:
            folder_locks.pop(normalized_path, None)

def _job_add_log(job_id: str, message: str, level: str = "info"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    with job_store_lock:
        job = job_store.get(job_id)
        if not job:
            return
        job.setdefault('log', []).append({"time": timestamp, "message": message, "level": level})
        if len(job['log']) > JOB_LOG_LIMIT:
            job['log'] = job['log'][-JOB_LOG_LIMIT:]


def _job_update_progress(job_id: str, *, total_delta=0, success_delta=0, failure_delta=0, duplicate_delta=0, reset=False):
    with job_store_lock:
        job = job_store.get(job_id)
        if not job:
            return
        if reset or 'progress' not in job:
            job['progress'] = {'total': 0, 'success': 0, 'failed': 0, 'duplicates': 0}
        progress = job['progress']
        if reset:
            progress.update({'total': 0, 'success': 0, 'failed': 0, 'duplicates': 0})
        progress['total'] = max(0, progress.get('total', 0) + total_delta)
        progress['success'] = max(0, progress.get('success', 0) + success_delta)
        progress['failed'] = max(0, progress.get('failed', 0) + failure_delta)
        progress['duplicates'] = max(0, progress.get('duplicates', 0) + duplicate_delta)


def _job_update_status(job_id: str, *, folder: Optional[str] = None, file: Optional[str] = None, step: Optional[str] = None):
    with job_store_lock:
        job = job_store.get(job_id)
        if not job:
            return
        if folder is not None:
            job['current_folder'] = folder
        if file is not None:
            job['current_file'] = file
        if step is not None:
            job['current_step'] = step


def _job_set_state(job_id: str, status: str):
    with job_store_lock:
        job = job_store.get(job_id)
        if not job:
            return
        job['status'] = status
        if status in ('success', 'partial_success', 'error'):
            job['end_time'] = datetime.now()


def _summarize_results(results: List[Dict]) -> Optional[Dict]:
    if not results:
        return None

    total_folders = len(results)
    total_pdfs = sum(r.get('pdf_count', 0) or 0 for r in results)
    success_folders = sum(1 for r in results if r.get('status') == 'success')
    partial_folders = sum(1 for r in results if r.get('status') == 'partial_success')
    failed_folders = sum(1 for r in results if r.get('status') == 'error')
    no_files_folders = sum(1 for r in results if r.get('status') == 'no_files')
    success_files = sum(r.get('success_count', 0) or 0 for r in results)
    total_duration = sum(r.get('duration', 0.0) or 0.0 for r in results)

    status_map = {
        "success": "✅ สำเร็จ",
        "partial_success": "⚠️ บางส่วน",
        "error": "❌ ล้มเหลว",
        "no_files": "📂 ไม่มีไฟล์",
        "read_failed": "⚠️ อ่านไม่ได้",
        "pending": "⏳ รอดำเนินการ"
    }

    folder_rows: List[Dict[str, str | int]] = []
    for res in results:
        automation_name = "-"
        automation_folder = res.get('automation_folder')
        if automation_folder:
            automation_name = Path(automation_folder).name or automation_folder
        folder_rows.append({
            "โฟลเดอร์หลัก": res.get('main_folder', '-'),
            "ระบบอัตโนมัติ": automation_name,
            "PDF": res.get('pdf_count', 0),
            "สถานะ": status_map.get(res.get('status'), res.get('status', '-')),
            "เวลา (s)": f"{(res.get('duration', 0.0) or 0.0):.1f}",
            "ข้อผิดพลาด": res.get('error') or "-"
        })

    return {
        "overall": {
            "total_folders": total_folders,
            "total_pdfs": total_pdfs,
            "success_folders": success_folders,
            "partial_folders": partial_folders,
            "failed_folders": failed_folders,
            "no_files_folders": no_files_folders,
            "success_files": success_files,
            "total_duration": total_duration,
            "total_duration_minutes": total_duration / 60 if total_duration else 0.0
        },
        "folders": folder_rows
    }


def _snapshot_jobs() -> List[Dict]:
    with job_store_lock:
        snapshot = []
        for job in job_store.values():
            copy_job = {
                k: (v.copy() if isinstance(v, dict) else list(v) if isinstance(v, list) else v)
                for k, v in job.items()
                if k != 'thread'
            }
            if 'progress' not in copy_job:
                copy_job['progress'] = {'total': 0, 'success': 0, 'failed': 0, 'duplicates': 0}
            snapshot.append(copy_job)
        return snapshot


def _start_job(folder_path: str) -> str:
    folder = Path(folder_path)
    if not folder.exists():
        raise FileNotFoundError(f"ไม่พบโฟลเดอร์: {folder_path}")

    is_locked, existing_job_id = _is_folder_locked(folder_path)
    if is_locked:
        existing_job = job_store.get(existing_job_id, {})
        folder_name = existing_job.get('folder', folder_path)
        status = existing_job.get('status', 'unknown')
        raise ValueError(
            f"⚠️ โฟลเดอร์นี้กำลังถูกประมวลผลอยู่แล้ว!\n"
            f"📂 โฟลเดอร์: {folder_name}\n"
            f"🆔 Job ID: {existing_job_id}\n"
            f"📊 สถานะ: {status}\n"
            f"กรุณารอให้งานเสร็จสิ้นก่อนเริ่มงานใหม่"
        )

    job_id = str(uuid.uuid4())[:8]
    job_data = {
        'id': job_id,
        'folder': str(folder),
        'status': 'pending',
        'progress': {'total': 0, 'success': 0, 'failed': 0, 'duplicates': 0},
        'current_folder': str(folder),
        'current_file': '-',
        'current_step': 'รอเริ่มงาน',
        'log': [],
        'start_time': None,
        'end_time': None
    }
    
    if not _lock_folder(folder_path, job_id):
        raise ValueError(f"⚠️ ไม่สามารถ lock โฟลเดอร์ได้: {folder_path}")
    
    with job_store_lock:
        job_store[job_id] = job_data

    worker = threading.Thread(target=_job_worker, args=(job_id,), daemon=True)
    worker.start()

    with job_store_lock:
        job_store[job_id]['thread'] = worker

    return job_id


def _job_worker(job_id: str):
    with job_store_lock:
        job = job_store.get(job_id)
        if not job:
            return
        folder = job['folder']
        job['start_time'] = datetime.now()
        job['status'] = 'running'

    _job_add_log(job_id, f"🚀 เริ่มประมวลผลโฟลเดอร์: {folder}", "info")
    _job_update_progress(job_id, reset=True)
    _job_update_status(job_id, folder=folder, step="กำลังเตรียมระบบ")

    orchestrator = MainSystemOrchestrator(
        str(folder),
        progress_callback=lambda **kwargs: _job_update_progress(job_id, **kwargs),
        status_callback=lambda **kwargs: _job_update_status(job_id, **kwargs),
        log_callback=lambda message, level="info": _job_add_log(job_id, message, level)
    )

    try:
        orchestrator.run_single_folder(folder)
        summary = _summarize_results(orchestrator.results)
        if summary is not None:
            with job_store_lock:
                job_data = job_store.get(job_id)
                if job_data is not None:
                    job_data['results'] = orchestrator.results
                    job_data['summary'] = summary
        final_status = 'success'
        if orchestrator.results:
            final_status = orchestrator.results[-1].get('status', 'unknown')
        _job_set_state(job_id, final_status)
        if final_status == 'success':
            _job_add_log(job_id, "✅ งานเสร็จสมบูรณ์", "success")
        elif final_status == 'partial_success':
            _job_add_log(job_id, "⚠️ งานเสร็จบางส่วน", "warning")
        else:
            _job_add_log(job_id, f"⚠️ งานจบด้วยสถานะ {final_status}", "warning")
    except Exception as e:
        _job_set_state(job_id, 'error')
        _job_add_log(job_id, f"❌ เกิดข้อผิดพลาด: {e}", "error")
    finally:
        _job_update_status(job_id, step="เสร็จสิ้น", file='-')
        _unlock_folder(folder, job_id)


def _aggregate_overview(jobs: List[Dict]) -> Dict:
    summary = {
        'total_jobs': len(jobs),
        'running': sum(1 for j in jobs if j.get('status') == 'running'),
        'completed': sum(1 for j in jobs if j.get('status') == 'success'),
        'failed': sum(1 for j in jobs if j.get('status') in ('error', 'partial_success', 'unknown')),
        'progress': {'total': 0, 'success': 0, 'failed': 0, 'duplicates': 0}
    }
    for job in jobs:
        progress = job.get('progress', {})
        summary['progress']['total'] += progress.get('total', 0)
        summary['progress']['success'] += progress.get('success', 0)
        summary['progress']['failed'] += progress.get('failed', 0)
        summary['progress']['duplicates'] += progress.get('duplicates', 0)
    return summary


def _clear_finished_jobs() -> int:
    with job_store_lock:
        finished_ids = [
            job_id for job_id, data in job_store.items()
            if data.get('status') in ('success', 'partial_success', 'error', 'unknown')
        ]
        for job_id in finished_ids:
            job_store.pop(job_id, None)
    return len(finished_ids)


def _render_job_card(job: Dict):
    folder_path = job.get('folder', '-')
    job_id = job.get('id', '-')
    progress = job.get('progress', {'total': 0, 'success': 0, 'failed': 0, 'duplicates': 0})
    total = max(progress.get('total', 0), 0)
    processed = progress.get('success', 0) + progress.get('failed', 0)
    ratio = processed / total if total else 0.0

    st.markdown(f"#### 📂 {Path(folder_path).name} (`{job_id}`)")
    st.progress(ratio)

    meta_cols = st.columns(3)
    meta_cols[0].metric("ไฟล์ทั้งหมด", total)
    meta_cols[1].metric("สำเร็จ", progress.get('success', 0))
    meta_cols[2].metric("ผิดพลาด", progress.get('failed', 0))

    st.caption(
        f"สถานะ: {job.get('status', 'pending')} • ขั้นตอน: {job.get('current_step', '-')}"
        f" • ไฟล์ล่าสุด: {job.get('current_file', '-')}"
    )

    summary = job.get('summary')
    if summary and isinstance(summary, dict):
        overall = summary.get('overall', {})
        if overall:
            st.markdown("**📊 สรุปผลการประมวลผล**")
            summary_cols = st.columns(4)
            summary_cols[0].metric("โฟลเดอร์ทั้งหมด", overall.get('total_folders', 0))
            summary_cols[1].metric("สำเร็จ", overall.get('success_folders', 0))
            summary_cols[2].metric("บางส่วน", overall.get('partial_folders', 0))
            summary_cols[3].metric("ล้มเหลว", overall.get('failed_folders', 0))
            st.caption(
                f"PDF ทั้งหมด {overall.get('total_pdfs', 0)} • ไฟล์สำเร็จ {overall.get('success_files', 0)} "
                f"• ใช้เวลา {overall.get('total_duration', 0.0):.1f}s "
                f"({overall.get('total_duration_minutes', 0.0):.1f} นาที)"
            )
        folder_rows = summary.get('folders') or []
        if folder_rows:
            with st.expander("📁 รายละเอียดแต่ละโฟลเดอร์", expanded=False):
                try:
                    folder_df = pd.DataFrame(folder_rows)
                    st.dataframe(folder_df, use_container_width=True)
                except Exception:
                    for row in folder_rows:
                        st.write(row)

    start_time = job.get('start_time')
    end_time = job.get('end_time')
    timeline = []
    if start_time:
        timeline.append(f"เริ่ม: {start_time.strftime('%H:%M:%S')}")
    if end_time:
        timeline.append(f"จบ: {end_time.strftime('%H:%M:%S')}")
    if timeline:
        st.caption(" | ".join(timeline))

    if job.get('log'):
        with st.expander("📝 รายการบันทึก", expanded=False):
            for entry in job['log'][-50:]:
                level = entry.get('level', 'info')
                color = "#00aaff"
                if level == "success":
                    color = "#27ae60"
                elif level == "error":
                    color = "#e74c3c"
                elif level == "warning":
                    color = "#f39c12"
                st.markdown(
                    f"<span style='color:{color}'>[{entry.get('time', '--')}] {entry.get('message', '')}</span>",
                    unsafe_allow_html=True
                )

    if job.get('status') in ('success', 'partial_success', 'error', 'unknown'):
        if st.button("🗑️ ลบงานนี้", key=f"delete_job_{job_id}", use_container_width=True):
            with job_store_lock:
                job_store.pop(job_id, None)
            st.rerun()


# Initialize session state
def init_session_state():
    """Initialize session state variables"""
    if 'admin_unlocked' not in st.session_state:
        st.session_state.admin_unlocked = False
    if 'line_notify_enabled' not in st.session_state:
        st.session_state.line_notify_enabled = getattr(Config, 'LINE_NOTIFY_ENABLED', True)
    if 'mode' not in st.session_state:
        st.session_state.mode = "custom"
    if 'custom_folder' not in st.session_state:
        st.session_state.custom_folder = ""
    if 'selected_folders' not in st.session_state:
        st.session_state.selected_folders = []
    if 'logs' not in st.session_state:
        st.session_state.logs = []
    if 'folder_list' not in st.session_state:
        st.session_state.folder_list = []
    if 'current_file' not in st.session_state:
        st.session_state.current_file = "-"
    if 'current_folder' not in st.session_state:
        st.session_state.current_folder = "-"
    if 'current_step' not in st.session_state:
        st.session_state.current_step = "-"
    if 'progress_stats' not in st.session_state:
        st.session_state.progress_stats = {
            'total': 0,
            'processed': 0,
            'success': 0,
            'failed': 0,
            'duplicates': 0
        }
    if 'show_json_editor' not in st.session_state:
        st.session_state.show_json_editor = False
    if 'json_editor_folder_code' not in st.session_state:
        st.session_state.json_editor_folder_code = None
    if 'show_txt_editor' not in st.session_state:
        st.session_state.show_txt_editor = False
    if 'txt_editor_folder_code' not in st.session_state:
        st.session_state.txt_editor_folder_code = None
    if 'show_tax_editor' not in st.session_state:
        st.session_state.show_tax_editor = False
    if 'tax_editor_folder_code' not in st.session_state:
        st.session_state.tax_editor_folder_code = None

def scan_folders():
    """สแกนโฟลเดอร์ทั้งหมด"""
    try:
        base_folder = getattr(Config, 'BASE_FOLDER', 'V')
        base_path = Path(f"{base_folder}:/")
        
        if not base_path.exists():
            add_log("❌ ไม่พบ drive", "error")
            return []
        
        folders_found = []
        main_folders = getattr(Config, 'MAIN_FOLDERS', ["A.โฟร์เดอร์หลัก", "AA.โฟรเดอร์หลัก", "AAA.โฟรเดอร์หลัก"])
        skip_folders = getattr(Config, 'SKIP_FOLDERS', ["#recycle", "#snapshot"])
        customer_folder = getattr(Config, 'CUSTOMER_FOLDER', 'ลูกค้า')
        automation_folder = getattr(Config, 'AUTOMATION_FOLDER', 'ระบบอัตโนมัติ')
        
        for main_folder_name in main_folders:
            main_folder = base_path / main_folder_name
            if main_folder.exists():
                has_build_folders = False
                for build_folder in main_folder.glob("Build*"):
                    if build_folder.is_dir() and not any(skip in build_folder.name for skip in skip_folders):
                        auto_folder = build_folder / customer_folder / automation_folder
                        if auto_folder.exists():
                            has_build_folders = True
                            break
                
                if has_build_folders:
                    folders_found.append({
                        'name': main_folder_name,
                        'path': str(main_folder),
                        'main_folder': main_folder_name
                    })
        
        add_log(f"✅ พบโฟลเดอร์ทั้งหมด: {len(folders_found)} โฟลเดอร์", "success")
        return folders_found
        
    except Exception as e:
        add_log(f"❌ เกิดข้อผิดพลาด: {e}", "error")
        return []

def add_log(message: str, level: str = "info"):
    """เพิ่ม log message"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = {
        'timestamp': timestamp,
        'message': message,
        'level': level
    }
    st.session_state.logs.append(log_entry)
    if len(st.session_state.logs) > 1000:
        st.session_state.logs = st.session_state.logs[-1000:]

def display_logs():
    """แสดง logs"""
    log_html = "<div class='log-container'>"
    for log in st.session_state.logs[-100:]:
        color = "#00ff00" if log['level'] == "success" else \
                "#ff0000" if log['level'] == "error" else \
                "#ffaa00" if log['level'] == "warning" else "#00aaff"
        log_html += f"<div style='color: {color}'>[{log['timestamp']}] {log['message']}</div>"
    log_html += "</div>"
    st.markdown(log_html, unsafe_allow_html=True)


def reset_progress_stats():
    st.session_state.progress_stats = {
        'total': 0,
        'processed': 0,
        'success': 0,
        'failed': 0,
        'duplicates': 0
    }


def _render_progress_summary(stats):
    processed = stats.get('success', 0) + stats.get('failed', 0)
    total = stats.get('total', 0)
    progress_ratio = min(1.0, processed / total) if total else 0.0

    st.markdown("### 📊 สรุปสถานะการประมวลผล")
    stats_cols = st.columns(3)
    stats_cols[0].metric("ไฟล์ทั้งหมด", total)
    stats_cols[1].metric("สำเร็จ", stats.get('success', 0))
    stats_cols[2].metric("ผิดพลาด", stats.get('failed', 0))

    st.progress(progress_ratio)
    st.caption(
        f"ดำเนินการแล้ว {processed}/{total or '?'} ไฟล์ • เอกสารซ้ำ {stats.get('duplicates', 0)}"
    )


def update_progress_stats(*, total_delta=0, success_delta=0, failure_delta=0, duplicate_delta=0, reset=False):
    if reset or 'progress_stats' not in st.session_state:
        reset_progress_stats()
    stats = st.session_state.progress_stats
    if reset:
        reset_progress_stats()
        stats = st.session_state.progress_stats
    stats['total'] = max(0, stats['total'] + total_delta)
    stats['success'] = max(0, stats['success'] + success_delta)
    stats['failed'] = max(0, stats['failed'] + failure_delta)
    stats['duplicates'] = max(0, stats['duplicates'] + duplicate_delta)
    stats['processed'] = max(0, stats['success'] + stats['failed'])
    st.session_state.progress_stats = stats

def extract_folder_code(folder_path: Path) -> Optional[str]:
    """แยกรหัสโฟลเดอร์จาก path"""
    try:
        for part in folder_path.parts:
            part_str = str(part)
            if part_str.startswith('Build') and ' ' in part_str:
                build_part = part_str.split(' ')[0]
                if len(build_part) >= 7:
                    code_part = build_part[5:]
                    if code_part.isdigit():
                        return f"Build{code_part}"
            elif part_str.startswith('Build') and len(part_str) >= 7:
                code_part = part_str[5:]
                if code_part.isdigit():
                    return f"Build{code_part}"
            elif len(part_str) == 3 and part_str.isdigit():
                return part_str
        return None
    except Exception:
        return None

def display_folder_info(folder_path: str):
    """แสดงข้อมูลโฟลเดอร์"""
    try:
        folder_path_obj = Path(folder_path)
        folder_code = extract_folder_code(folder_path_obj)
        
        if folder_code:
            st.info(f"🏷️ รหัสโฟลเดอร์: {folder_code}")
            
            folder_settings_path = Path("V:/A.โฟร์เดอร์หลัก/Build000 ทดสอบระบบ/folder_settings/folder_settings.json")
            if folder_settings_path.exists():
                with open(folder_settings_path, 'r', encoding='utf-8') as f:
                    folder_settings = json.load(f)
                
                if folder_code in folder_settings:
                    folder_info = folder_settings[folder_code]
                    group = folder_info.get('group', 'unknown')
                    
                    if group == 'special':
                        st.warning("📊 ประเภทภาษีมูลค่าเพิ่ม: ยังไม่ได้จดภาษีมูลค่าเพิ่ม (NoneVat)")
                    elif group == 'regular':
                        st.success("📊 ประเภทภาษีมูลค่าเพิ่ม: จดภาษีมูลค่าเพิ่ม (VAT)")
                    else:
                        st.warning(f"📊 ประเภทภาษีมูลค่าเพิ่ม: ไม่ทราบประเภท (group: {group})")
            
            json_path = Path(f"V:/A.โฟร์เดอร์หลัก/Build000 ทดสอบระบบ/รหัส/{folder_code}.json")
            if json_path.exists():
                with open(json_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                if json_data:
                    st.info(f"📄 พบข้อมูลจากไฟล์ JSON ({folder_code}.json) - ทั้งหมด {len(json_data)} บริษัท")
                    
                    companies_data = []
                    for company_key, data in json_data.items():
                        companies_data.append({
                            'ชื่อบริษัท': data.get("company_name", "ไม่ทราบชื่อ"),
                            'รหัสผู้ติดต่อ': data.get("customer_id", "ไม่พบ"),
                            'โค้ดบัญชี': data.get("account_code", "ไม่พบ")
                        })
                    
                    if companies_data:
                        df = pd.DataFrame(companies_data)
                        st.dataframe(df, use_container_width=True)
            else:
                st.warning(f"⚠️ ไม่พบไฟล์ JSON: {folder_code}.json")
        else:
            st.warning("⚠️ ไม่สามารถระบุรหัสโฟลเดอร์ได้")
            
    except Exception as e:
        st.error(f"⚠️ ไม่สามารถแสดงข้อมูลโฟลเดอร์: {e}")

def show_json_editor(folder_code: str):
    """แสดงหน้าต่างแก้ไข JSON"""
    st.subheader(f"✏️ แก้ไขผังบัญชี - {folder_code}")
    
    json_path = Path(f"V:/A.โฟร์เดอร์หลัก/Build000 ทดสอบระบบ/รหัส/{folder_code}.json")
    
    if not json_path.exists():
        st.error(f"❌ ไม่พบไฟล์ JSON: {json_path}")
        if st.button("📝 สร้างไฟล์ JSON ใหม่"):
            create_new_json_file(folder_code)
            st.rerun()
        return
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        st.warning("⚠️ สามารถแก้ไขได้เฉพาะรหัสผู้ติดต่อและโค้ดบัญชีเท่านั้น")
        
        with st.form(f"json_editor_form_{folder_code}", clear_on_submit=False):
            for company_key, company_data in json_data.items():
                with st.expander(f"🏢 {company_key}", expanded=False):
                    st.text_input(
                        "Company Name",
                        value=company_data.get("company_name", company_key),
                        disabled=True,
                        key=f"company_name_{company_key}_{folder_code}"
                    )
                    
                    st.text_input(
                        "รหัสผู้ติดต่อ",
                        value=company_data.get("customer_id", ""),
                        key=f"customer_id_{company_key}_{folder_code}"
                    )
                    
                    st.text_input(
                        "โค้ดบัญชี",
                        value=company_data.get("account_code", ""),
                        key=f"account_code_{company_key}_{folder_code}"
                    )
                    
                    st.text_input(
                        "Account Code 2",
                        value=company_data.get("account_code2", ""),
                        disabled=True,
                        key=f"account_code2_{company_key}_{folder_code}"
                    )
            
            col1, col2 = st.columns(2)
            with col1:
                save_btn = st.form_submit_button("💾 บันทึก", use_container_width=True, type="primary")
            with col2:
                cancel_btn = st.form_submit_button("❌ ยกเลิก", use_container_width=True)
            
            if save_btn:
                try:
                    edited_data = json_data.copy()
                    for company_key in json_data.keys():
                        customer_id_key = f"customer_id_{company_key}_{folder_code}"
                        account_code_key = f"account_code_{company_key}_{folder_code}"
                        
                        if customer_id_key in st.session_state:
                            edited_data[company_key]["customer_id"] = st.session_state[customer_id_key]
                        if account_code_key in st.session_state:
                            edited_data[company_key]["account_code"] = st.session_state[account_code_key]
                    
                    json_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(edited_data, f, ensure_ascii=False, indent=2)
                    st.success("✅ บันทึกไฟล์ JSON สำเร็จ")
                    add_log(f"💾 บันทึกไฟล์ JSON สำเร็จ: {folder_code}.json", "success")
                    st.session_state.show_json_editor = False
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ ไม่สามารถบันทึกไฟล์: {e}")
                    add_log(f"❌ ไม่สามารถบันทึกไฟล์ JSON: {e}", "error")
            
            if cancel_btn:
                st.session_state.show_json_editor = False
                st.rerun()
        
        if st.button("← กลับ", use_container_width=True):
            st.session_state.show_json_editor = False
            st.rerun()
                
    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาด: {e}")
        add_log(f"❌ เกิดข้อผิดพลาดในการแก้ไข JSON: {e}", "error")

def show_txt_editor(folder_code: str):
    """แสดงหน้าต่างแก้ไข TXT"""
    st.subheader(f"📄 แก้ไขข้อมูล login - {folder_code}")
    
    folder_path = Path(f"V:/A.โฟร์เดอร์หลัก/Build000 ทดสอบระบบ/รหัส/")
    
    if not folder_path.exists():
        st.error(f"❌ ไม่พบโฟลเดอร์รหัส: {folder_path}")
        return
    
    txt_files = [f for f in folder_path.glob("*.txt") if f.name.startswith(folder_code)]
    
    if not txt_files:
        st.error(f"❌ ไม่พบไฟล์ .txt ที่ตรงกับรหัส '{folder_code}'")
        if st.button("📝 สร้างไฟล์ TXT ใหม่"):
            create_new_txt_file(folder_code)
            st.rerun()
        return
    
    if len(txt_files) > 1:
        selected_file_name = st.selectbox(
            "เลือกไฟล์ TXT ที่ต้องการแก้ไข",
            [f.name for f in txt_files],
            key=f"txt_file_select_{folder_code}"
        )
        selected_file = next(f for f in txt_files if f.name == selected_file_name)
    else:
        selected_file = txt_files[0]
    
    try:
        try:
            with open(selected_file, 'r', encoding='utf-8') as f:
                file_content = f.read()
        except UnicodeDecodeError:
            with open(selected_file, 'r', encoding='cp1252') as f:
                file_content = f.read()
        
        with st.form(f"txt_editor_form_{folder_code}", clear_on_submit=False):
            edited_content = st.text_area(
                "แก้ไขเนื้อหา",
                value=file_content,
                height=300,
                key=f"txt_editor_{folder_code}"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                save_btn = st.form_submit_button("💾 บันทึก", use_container_width=True, type="primary")
            with col2:
                cancel_btn = st.form_submit_button("❌ ยกเลิก", use_container_width=True)
            
            if save_btn:
                try:
                    with open(selected_file, 'w', encoding='utf-8') as f:
                        f.write(edited_content)
                    st.success("✅ บันทึกไฟล์ TXT สำเร็จ")
                    add_log(f"💾 บันทึกไฟล์ TXT สำเร็จ: {selected_file.name}", "success")
                    st.session_state.show_txt_editor = False
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ ไม่สามารถบันทึกไฟล์: {e}")
                    add_log(f"❌ ไม่สามารถบันทึกไฟล์ TXT: {e}", "error")
            
            if cancel_btn:
                st.session_state.show_txt_editor = False
                st.rerun()
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 รีเฟรช", use_container_width=True, key=f"refresh_txt_{folder_code}"):
                st.rerun()
        with col2:
            if st.button("← กลับ", use_container_width=True, key=f"back_txt_{folder_code}"):
                st.session_state.show_txt_editor = False
                st.rerun()
            
    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาด: {e}")
        add_log(f"❌ เกิดข้อผิดพลาดในการแก้ไข TXT: {e}", "error")

def show_tax_editor(folder_code: str):
    """แสดงหน้าต่างจัดการข้อมูลภาษี"""
    st.subheader(f"📊 จัดการข้อมูลภาษี - {folder_code}")
    
    tax_settings_path = Path("V:/A.โฟร์เดอร์หลัก/Build000 ทดสอบระบบ/folder_settings/folder_settings.json")
    
    current_data = {}
    current_group = 'unknown'
    if tax_settings_path.exists():
        with open(tax_settings_path, 'r', encoding='utf-8') as f:
            current_data = json.load(f)
        
        if folder_code in current_data:
            current_info = current_data[folder_code]
            current_group = current_info.get('group', 'unknown')
    
    if current_group != 'unknown':
        status_text = f"สถานะปัจจุบัน: {current_group} ({'VAT' if current_group == 'regular' else 'NoneVat' if current_group == 'special' else 'ไม่ทราบ'})"
        st.info(status_text)
    else:
        st.warning("⚠️ ยังไม่มีการตั้งค่าประเภทภาษี")
    
    with st.form(f"tax_editor_form_{folder_code}", clear_on_submit=False):
        st.markdown("**ประเภทภาษีมูลค่าเพิ่ม:**")
        
        tax_type = st.radio(
            "เลือกประเภท",
            ["regular", "special"],
            index=0 if current_group == "regular" else 1 if current_group == "special" else 0,
            format_func=lambda x: "🟢 จดภาษีมูลค่าเพิ่ม (VAT)" if x == "regular" else "🟡 ยังไม่ได้จดภาษีมูลค่าเพิ่ม (NoneVat)",
            key=f"tax_type_{folder_code}"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            save_btn = st.form_submit_button("💾 บันทึก", use_container_width=True, type="primary")
        with col2:
            cancel_btn = st.form_submit_button("❌ ยกเลิก", use_container_width=True)
        
        if save_btn:
            try:
                if folder_code not in current_data:
                    current_data[folder_code] = {}
                
                current_data[folder_code]['group'] = tax_type
                
                tax_settings_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(tax_settings_path, 'w', encoding='utf-8') as f:
                    json.dump(current_data, f, ensure_ascii=False, indent=2)
                
                type_text = "จดภาษีมูลค่าเพิ่ม (VAT)" if tax_type == "regular" else "ยังไม่ได้จดภาษีมูลค่าเพิ่ม (NoneVat)"
                st.success(f"✅ บันทึกการตั้งค่าประเภทภาษีสำเร็จ: {type_text}")
                add_log(f"✅ บันทึกการตั้งค่าประเภทภาษีสำเร็จ: {folder_code} -> {tax_type}", "success")
                st.session_state.show_tax_editor = False
                st.rerun()
            except Exception as e:
                st.error(f"❌ ไม่สามารถบันทึกการตั้งค่า: {e}")
                add_log(f"❌ ไม่สามารถบันทึกการตั้งค่าประเภทภาษี: {e}", "error")
        
        if cancel_btn:
            st.session_state.show_tax_editor = False
            st.rerun()
    
    if st.button("← กลับ", use_container_width=True, key=f"back_tax_{folder_code}"):
        st.session_state.show_tax_editor = False
        st.rerun()

def create_new_json_file(folder_code: str):
    """สร้างไฟล์ JSON ใหม่"""
    try:
        new_json_path = Path(f"V:/A.โฟร์เดอร์หลัก/Build000 ทดสอบระบบ/รหัส/{folder_code}.json")
        template_json_path = Path(f"V:/A.โฟร์เดอร์หลัก/Build000 ทดสอบระบบ/รหัส/Build000.json")
        
        if not template_json_path.exists():
            st.error(f"❌ ไม่พบไฟล์ต้นแบบ: {template_json_path}")
            return
        
        with open(template_json_path, 'r', encoding='utf-8') as f:
            template_data = json.load(f)
        
        new_data = {}
        for company_key, company_data in template_data.items():
            new_data[company_key] = {
                "company_name": company_data.get("company_name", company_key),
                "customer_id": "",
                "account_code": "",
                "account_code2": company_data.get("account_code2", "")
            }
        
        new_json_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(new_json_path, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)
        
        st.success(f"✅ สร้างไฟล์ JSON ใหม่สำเร็จ: {folder_code}.json")
        add_log(f"✅ สร้างไฟล์ JSON ใหม่สำเร็จ: {folder_code}.json", "success")
        
    except Exception as e:
        st.error(f"❌ ไม่สามารถสร้างไฟล์ JSON: {e}")
        add_log(f"❌ ไม่สามารถสร้างไฟล์ JSON: {e}", "error")

def create_new_txt_file(folder_code: str):
    """สร้างไฟล์ TXT ใหม่"""
    try:
        new_txt_path = Path(f"V:/A.โฟร์เดอร์หลัก/Build000 ทดสอบระบบ/รหัส/{folder_code}.txt")
        
        txt_content = """Username : 
Password : 
Link company : 
Link Express : 
"""
        
        new_txt_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(new_txt_path, 'w', encoding='utf-8') as f:
            f.write(txt_content)
        
        st.success(f"✅ สร้างไฟล์ TXT ใหม่สำเร็จ: {folder_code}.txt")
        add_log(f"✅ สร้างไฟล์ TXT ใหม่สำเร็จ: {folder_code}.txt", "success")
        
    except Exception as e:
        st.error(f"❌ ไม่สามารถสร้างไฟล์ TXT: {e}")
        add_log(f"❌ ไม่สามารถสร้างไฟล์ TXT: {e}", "error")

def admin_login():
    """เข้าสู่โหมดแอดมิน"""
    admin_password = "adminit"
    
    if st.session_state.admin_unlocked:
        if st.button("🔒 ออกจากโหมดแอดมิน", use_container_width=True):
            st.session_state.admin_unlocked = False
            st.rerun()
    else:
        password = st.text_input("รหัสผ่านแอดมิน", type="password", key="admin_password_input")
        if st.button("🔓 เข้าสู่โหมดแอดมิน", use_container_width=True):
            if password == admin_password:
                st.session_state.admin_unlocked = True
                st.success("เข้าสู่โหมดแอดมินสำเร็จ")
                st.rerun()
            elif password:
                st.error("รหัสผ่านไม่ถูกต้อง")

def main():
    """Main Streamlit App"""
    init_session_state()

    st.markdown("""
        <div class='main-header'>
            <h1>🤖 BotV3 - ระบบประมวลผล PDF อัตโนมัติ</h1>
        </div>
    """, unsafe_allow_html=True)

    jobs_snapshot = _snapshot_jobs()
    summary = _aggregate_overview(jobs_snapshot)

    refresh_placeholder = st.empty()
    has_active_jobs = any(job.get('status') in ('pending', 'running') for job in jobs_snapshot)
    if has_active_jobs:
        refresh_placeholder.markdown(
            """
            <script>
                setTimeout(function() { window.location.reload(); }, 3000);
            </script>
            """,
            unsafe_allow_html=True
        )
    else:
        refresh_placeholder.empty()

    with st.sidebar:
        st.header("⚙️ ควบคุมระบบ")
        st.subheader("🔐 โหมดแอดมิน")
        admin_login()

        if st.session_state.admin_unlocked:
            st.success("✅ อยู่ในโหมดแอดมิน")
            st.subheader("📱 การแจ้งเตือน LINE")
            line_notify = st.toggle(
                "เปิดการแจ้งเตือน LINE",
                value=st.session_state.line_notify_enabled
            )
            if line_notify != st.session_state.line_notify_enabled:
                st.session_state.line_notify_enabled = line_notify
                try:
                    set_line_notifications_enabled(line_notify)
                    add_log("✅ อัพเดตการตั้งค่าการแจ้งเตือน LINE", "success")
                except Exception:
                    pass

        st.divider()
        st.subheader("📊 ภาพรวมงาน")
        overview_cols = st.columns(4)
        overview_cols[0].metric("ทั้งหมด", summary['total_jobs'])
        overview_cols[1].metric("กำลังทำงาน", summary['running'])
        overview_cols[2].metric("สำเร็จ", summary['completed'])
        overview_cols[3].metric("ล้มเหลว", summary['failed'])

        if st.button("🧹 ล้างงานที่เสร็จแล้ว", use_container_width=True):
            removed = _clear_finished_jobs()
            if removed:
                st.success(f"ลบงานที่เสร็จแล้ว {removed} งาน")
            else:
                st.info("ไม่มีงานที่เสร็จแล้วให้ลบ")
            st.rerun()

    col1, col2 = st.columns([1, 1])

    with col1:
        st.header("📁 เพิ่มงานใหม่")
        folder_input = st.text_input(
            "โฟลเดอร์",
            value=st.session_state.get('custom_folder', ''),
            placeholder="พิมพ์หรือวาง path โฟลเดอร์"
        ).strip()

        add_job_cols = st.columns([3, 1])
        add_job_clicked = add_job_cols[0].button("➕ เพิ่มงาน", use_container_width=True, type="primary")
        if add_job_cols[1].button("🔄 รีเฟรช", use_container_width=True):
            st.rerun()

        if add_job_clicked:
            if not folder_input:
                st.error("กรุณาระบุโฟลเดอร์ที่จะประมวลผล")
            else:
                try:
                    job_id = _start_job(folder_input)
                    st.session_state.custom_folder = folder_input
                    st.success(f"เริ่มงานใหม่เรียบร้อย (ID: {job_id})")
                except FileNotFoundError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"❌ ไม่สามารถเริ่มงานได้: {e}")

        if folder_input:
            display_folder_info(folder_input)
            folder_path = Path(folder_input)
            if folder_path.exists():
                folder_code = extract_folder_code(folder_path)
                if folder_code:
                    st.divider()
                    st.subheader("🔧 จัดการข้อมูลเพิ่มเติม")
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button("✏️ แก้ไขผังบัญชี", use_container_width=True, type="primary"):
                            st.session_state.show_json_editor = True
                            st.session_state.json_editor_folder_code = folder_code
                            st.rerun()
                        if st.button("📄 แก้ไขข้อมูล login", use_container_width=True):
                            st.session_state.show_txt_editor = True
                            st.session_state.txt_editor_folder_code = folder_code
                            st.rerun()
                    with btn_col2:
                        if st.button("📊 จัดการข้อมูลภาษี", use_container_width=True):
                            st.session_state.show_tax_editor = True
                            st.session_state.tax_editor_folder_code = folder_code
                            st.rerun()

        if st.session_state.show_json_editor and st.session_state.json_editor_folder_code:
            st.divider()
            show_json_editor(st.session_state.json_editor_folder_code)
        if st.session_state.show_txt_editor and st.session_state.txt_editor_folder_code:
            st.divider()
            show_txt_editor(st.session_state.txt_editor_folder_code)
        if st.session_state.show_tax_editor and st.session_state.tax_editor_folder_code:
            st.divider()
            show_tax_editor(st.session_state.tax_editor_folder_code)

        with st.expander("🔰 ขั้นตอนแนะนำการใช้งาน", expanded=False):
            st.markdown(
                """
                1. คัดลอกที่อยู่ของโฟลเดอร์บอท แล้วนำมาวางในช่อง `โฟลเดอร์`
                2. ตรวจสอบสถานะโฟลเดอร์และกด `เพิ่มงาน`
                3. ระบบจะเริ่มประมวลผลอัตโนมัติ สามารถติดตามผลได้จากคอลัมน์ขวามือ
                4. เมื่องานเสร็จสมบูรณ์ สามารถลบงานออกจากรายการได้
                """
            )

    with col2:
        st.header("📊 งานทั้งหมด")
        _render_progress_summary(summary['progress'])

        jobs_cols = st.columns(3)
        jobs_cols[0].metric("งานทั้งหมด", summary['total_jobs'])
        jobs_cols[1].metric("กำลังทำงาน", summary['running'])
        jobs_cols[2].metric("สำเร็จ", summary['completed'])

        if not jobs_snapshot:
            st.info("ยังไม่มีงานที่กำลังประมวลผล")
        else:
            sorted_jobs = sorted(
                jobs_snapshot,
                key=lambda j: j.get('start_time') or datetime.min,
                reverse=True
            )
            for job in sorted_jobs:
                _render_job_card(job)
                st.divider()

        st.header("📝 บันทึกทั่วไป")
        if st.session_state.logs:
            display_logs()
        else:
            st.info("ยังไม่มีบันทึก")

# Main App
if __name__ == "__main__":
    main()

