from __future__ import annotations

import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List


REGULAR_LABEL = "จดภาษีมูลค่าเพิ่ม"
SPECIAL_LABEL = "ยังไม่ได้จดภาษีมูลค่าเพิ่ม"

# Global variable to control LINE notifications
_line_notifications_enabled = True

def set_line_notifications_enabled(enabled: bool):
    """Set global LINE notifications enabled status"""
    global _line_notifications_enabled
    old_value = _line_notifications_enabled
    _line_notifications_enabled = enabled
    print(f"🔧 [LINE Notify] เปลี่ยนสถานะ: {old_value} -> {enabled}")

def get_line_notifications_enabled() -> bool:
    """Get global LINE notifications enabled status"""
    return _line_notifications_enabled


class ReportManager:
    """รวบรวมสถิติการทำงาน และสร้างรายงาน/ข้อความสำหรับแจ้งไลน์"""

    def __init__(self, main_folder: str):
        self.main_folder = main_folder  # เช่น V:/A.โฟร์เดอร์หลัก/Build000 ทดสอบระบบ
        self.folder_code: Optional[str] = None
        self.group: Optional[str] = None  # 'regular' | 'special' | None
        self.group_label: Optional[str] = None

        # สถิติ
        self.total_pdf_files: int = 0           # PDF ทั้งหมดในโฟลเดอร์ระบบอัตโนมัติ (ที่อ่านมาเข้า batch)
        self.readable_files: int = 0           # อ่านได้ (เข้า workflow)
        self.unreadable_files: int = 0         # อ่านไม่ได้/ไม่ครบ
        self.processed_success: int = 0        # อัปโหลดสำเร็จ
        self.duplicate_count: int = 0          # เอกสารซ้ำ
        self.database_error_count: int = 0     # ฐานข้อมูลไม่เรียบร้อย
        self.pending_action_count: int = 0     # เอกสารรอดำเนินการ
        self.unreadable_image_count: int = 0   # 3.1 เอกสาร PDF ภาพ
        self.unreadable_not_implemented_count: int = 0  # 3.2 ยังไม่ได้นำเข้าระบบ

        # รายละเอียดบริษัท: {company_name: count}
        self.company_to_count: Dict[str, int] = {}

        # สำหรับรายงานไฟล์
        self.automation_folder: Optional[Path] = None
        self._started: bool = False

    # ---------- Context ----------
    def set_group(self, folder_code: str, group: str):
        self.folder_code = folder_code
        self.group = group or 'unknown'
        self.group_label = REGULAR_LABEL if self.group == 'regular' else (SPECIAL_LABEL if self.group == 'special' else 'ไม่ทราบกลุ่ม')

    def set_automation_folder(self, automation_folder: str | Path):
        self.automation_folder = Path(automation_folder)

    # ---------- Batch preparation ----------
    def prepare_from_batch(self, batch_report: Dict, pdf_files: List[Path] | List[str], company_counts: Optional[Dict[str, int]] = None):
        self.total_pdf_files = int(batch_report.get('total', len(pdf_files) if pdf_files else 0))
        self.readable_files = int(batch_report.get('read_success', 0))
        self.unreadable_files = int(batch_report.get('read_failed', 0))
        if company_counts:
            self.company_to_count = dict(company_counts)

    # ---------- Lifecycle ----------
    def start(self) -> str:
        self._started = True
        title = f"{Path(self.main_folder).name} - {self.group_label or ''}".strip()
        unreadable_total = self.unreadable_image_count + self.unreadable_not_implemented_count
        return (
            "เริ่มต้นการทำงาน\n"
            f"{title}\n"
            "กำลังทำงาน :\n"
            f"เอกสารทั้งหมด {self.total_pdf_files} ไฟล์\n"
            f"เอกสารที่ทำงานได้ทั้งหมด {self.readable_files}/{self.total_pdf_files}\n"
            f"เอกสารรอดำเนินการทั้งหมด {self.pending_action_count}/{self.total_pdf_files}\n"
            f"เอกสารที่อ่านข้อมูลไม่ได้ทั้งหมด {unreadable_total}/{self.total_pdf_files}\n"
            f"ฐานข้อมูลไม่เรียบร้อยทั้งหมด {self.database_error_count}/{self.total_pdf_files}"
        )

    def add_processed_success(self, n: int = 1):
        self.processed_success += int(n)

    def add_duplicate(self, n: int = 1):
        self.duplicate_count += int(n)

    def add_database_error(self, n: int = 1):
        self.database_error_count += int(n)

    def add_pending_action(self, n: int = 1):
        self.pending_action_count += int(n)

    def add_unreadable_image(self, n: int = 1):
        self.unreadable_image_count += int(n)

    def add_unreadable_not_implemented(self, n: int = 1):
        self.unreadable_not_implemented_count += int(n)

    def end_success(self) -> str:
        title = f"{Path(self.main_folder).name} - {self.group_label or ''}".strip()
        return (
            "สิ้นสุดการทำงาน (ครบถ้วน)\n"
            f"{title}\n"
            f"ทำงานเสร็จแล้ว เอกสารที่ทำงานทั้งหมด {self.processed_success}/{self.total_pdf_files}\n"
            f"เอกสารที่ซ้ำกับในระบบทั้งหมด {self.duplicate_count}/{self.total_pdf_files}\n"
            f"เอกสารรอดำเนินการทั้งหมด {self.pending_action_count}/{self.total_pdf_files}\n"
            f"เอกสารที่อ่านข้อมูลไม่ได้ทั้งหมด {self.unreadable_image_count + self.unreadable_not_implemented_count}/{self.total_pdf_files}\n"
            f"ฐานข้อมูลไม่เรียบร้อยทั้งหมด {self.database_error_count}/{self.total_pdf_files}"
        )

    def end_partial(self) -> str:
        title = f"{Path(self.main_folder).name} - {self.group_label or ''}".strip()
        return (
            "สิ้นสุดการทำงาน (บางส่วน)\n"
            f"{title}\n"
            f"ทำงานเสร็จแล้ว เอกสารที่ทำงานทั้งหมด {self.processed_success}/{self.total_pdf_files}\n"
            f"เอกสารที่ซ้ำกับในระบบทั้งหมด {self.duplicate_count}/{self.total_pdf_files}\n"
            f"เอกสารรอดำเนินการทั้งหมด {self.pending_action_count}/{self.total_pdf_files}\n"
            f"เอกสารที่อ่านข้อมูลไม่ได้ทั้งหมด {self.unreadable_image_count + self.unreadable_not_implemented_count}/{self.total_pdf_files}\n"
            f"ฐานข้อมูลไม่เรียบร้อยทั้งหมด {self.database_error_count}/{self.total_pdf_files}\n"
            "ยังเหลือการทำงานบางส่วนที่ยังรอดำเนินการอยู่"
        )

    # ---------- Text report ----------
    def write_txt_report(self, filename: str | None = None) -> Optional[Path]:
        try:
            base = self.automation_folder or Path(self.main_folder) / "ลูกค้า" / "ระบบอัตโนมัติ"
            base.mkdir(parents=True, exist_ok=True)
            # ตั้งชื่อไฟล์ตาม timestamp หากไม่ได้ระบุชื่อมา
            if not filename:
                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"รายงานการทำงาน_{ts}.txt"
            report_path = base / filename
            lines: List[str] = []
            title = f"{Path(self.main_folder).name} - {self.group_label or ''}".strip()

            lines.append("เริ่มต้นการทำงาน :")
            lines.append(title)
            lines.append(f"เอกสารรวมทั้งหมด: {self.total_pdf_files}")
            lines.append(f"อ่านได้ (เข้า workflow): {self.readable_files}")
            lines.append(f"อ่านไม่ได้: {self.unreadable_files}")
            lines.append("")
            if self.company_to_count:
                lines.append("รายการบริษัทที่อ่านได้:")
                for comp, cnt in sorted(self.company_to_count.items(), key=lambda x: (-x[1], x[0])):
                    lines.append(f"- {comp}: {cnt} ไฟล์")
                lines.append("")

            lines.append("สิ้นสุดการทำงาน :")
            lines.append(f"อัปโหลดสำเร็จ: {self.processed_success}/{self.readable_files}")
            lines.append(f"เอกสารซ้ำ: {self.duplicate_count}")
            lines.append(f"เอกสารรอดำเนินการ: {self.pending_action_count}")
            lines.append(f"เอกสารอ่านข้อมูลไม่ได้ (รวม): {self.unreadable_image_count + self.unreadable_not_implemented_count}")
            lines.append(f"  - เอกสาร PDF ภาพ: {self.unreadable_image_count}")
            lines.append(f"  - ยังไม่ได้นำเข้าระบบ: {self.unreadable_not_implemented_count}")
            lines.append(f"ฐานข้อมูลไม่เรียบร้อย: {self.database_error_count}")
            lines.append(f"เวลารายงาน: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(lines))

            return report_path
        except Exception:
            return None


# ---------- LINE helpers ----------
import json, requests
from config import Config
from logger import BotLogger

_bot_logger: BotLogger | None = None
_global_report_manager: ReportManager | None = None

def _get_bot_logger() -> BotLogger:
    global _bot_logger
    if _bot_logger is None:
        _bot_logger = BotLogger()
    return _bot_logger

def set_global_report_manager(manager: ReportManager) -> None:
    global _global_report_manager
    _global_report_manager = manager

def get_global_report_manager() -> ReportManager | None:
    return _global_report_manager

def line_notify(message: str, image_path: Optional[str] = None) -> bool:
    """
    ส่งข้อความไปยัง LINE Notify (รองรับการส่งรูปภาพด้วย)
    
    Args:
        message: ข้อความที่จะส่ง (จำกัด 1000 ตัวอักษร)
        image_path: Path ของไฟล์รูปภาพที่จะแนบ (optional, รองรับ PNG, JPEG, GIF)
    
    Returns:
        True ถ้าสำเร็จ, False ถ้าล้มเหลว
    """
    # ตรวจสอบสถานะการแจ้งเตือน LINE
    enabled = get_line_notifications_enabled()
    if not enabled:
        print(f"🔕 [LINE Notify] ปิดการแจ้งเตือน LINE (สถานะ: {enabled}) - ข้ามการส่ง")
        return True
    
    token = getattr(Config, "LINE_NOTIFY_TOKEN", "")
    _get_bot_logger().log_action(
        "LINE Notify",
        "INFO",
        f"attempt: message_len={len(message)}, has_image={image_path is not None}"
    )
    try:
        print(f"📨 [LINE Notify] Attempt: message_len={len(message)}, image={image_path is not None}")
    except Exception:
        pass
    if not token:
        print("⚠️ ยังไม่ได้ตั้งค่า Config.LINE_NOTIFY_TOKEN")
        _get_bot_logger().log_action("LINE Notify", "ERROR", "Missing LINE_NOTIFY_TOKEN")
        return False
    
    try:
        # LINE Notify limit ประมาณ 1000 ตัวอักษร
        max_len = 1000
        message_truncated = message[:max_len]
        
        # ถ้ามีรูปภาพ ให้ส่งแบบ multipart/form-data
        image_file = None
        if image_path:
            image_file = Path(image_path)
            if not image_file.exists():
                print(f"⚠️ [LINE Notify] ไม่พบไฟล์รูปภาพ: {image_path} - ส่งข้อความเท่านั้น")
                image_file = None  # ส่งข้อความเท่านั้น
            
        if image_file and image_file.exists():
            # ส่งพร้อมรูปภาพ (multipart/form-data)
            try:
                with open(image_file, 'rb') as f:
                    files = {
                        'imageFile': (image_file.name, f, _get_image_content_type(image_file))
                    }
                    data = {'message': message_truncated}
                    headers = {'Authorization': f'Bearer {token}'}
                    
                    r = requests.post(
                        'https://notify-api.line.me/api/notify',
                        headers=headers,
                        data=data,
                        files=files,
                        timeout=30
                    )
                    
                if r.status_code != 200:
                    try:
                        print(f"❌ [LINE Notify] ส่งรูปภาพไม่สำเร็จ: {r.status_code} - {r.text}")
                    except Exception:
                        print(f"❌ [LINE Notify] ส่งรูปภาพไม่สำเร็จ: {r.status_code}")
                    _get_bot_logger().log_action(
                        "LINE Notify",
                        "ERROR",
                        f"status_code={r.status_code}, response={r.text[:200]}"
                    )
                    return False
                
                _get_bot_logger().log_action(
                    "LINE Notify",
                    "SUCCESS",
                    f"status_code=200, message_len={len(message)}, image={image_file.name}"
                )
                try:
                    print(f"✅ [LINE Notify] ส่งข้อความพร้อมรูปภาพสำเร็จ (200)")
                except Exception:
                    pass
                return True
            except Exception as e:
                print(f"⚠️ [LINE Notify] เกิดข้อผิดพลาดในการส่งรูปภาพ: {e} - ลองส่งข้อความเท่านั้น")
                # Fallback: ส่งข้อความเท่านั้น
                image_path = None
        
        # ส่งข้อความเท่านั้น (ไม่มีรูปภาพ หรือส่งรูปภาพไม่สำเร็จ)
        r = requests.post(
            'https://notify-api.line.me/api/notify',
            headers={'Authorization': f'Bearer {token}'},
            data={'message': message_truncated},
            timeout=10
        )
        
        if r.status_code != 200:
            try:
                print(f"❌ [LINE Notify] ส่งไม่สำเร็จ: {r.status_code} - {r.text}")
            except Exception:
                print(f"❌ [LINE Notify] ส่งไม่สำเร็จ: {r.status_code}")
            _get_bot_logger().log_action(
                "LINE Notify",
                "ERROR",
                f"status_code={r.status_code}, response={r.text[:200]}"
            )
            return False
        
        _get_bot_logger().log_action(
            "LINE Notify",
            "SUCCESS",
            f"status_code=200, message_len={len(message)}"
        )
        try:
            print("✅ [LINE Notify] ส่งสำเร็จ (200)")
        except Exception:
            pass
        return True
    except Exception as e:
        print(f"❌ [LINE Notify] exception: {e}")
        import traceback
        traceback.print_exc()
        _get_bot_logger().log_action("LINE Notify", "ERROR", f"exception={e}")
        return False


def _get_image_content_type(image_file: Path) -> str:
    """ตรวจสอบ Content-Type ของไฟล์รูปภาพ"""
    suffix = image_file.suffix.lower()
    if suffix in ['.jpg', '.jpeg']:
        return 'image/jpeg'
    elif suffix == '.png':
        return 'image/png'
    elif suffix == '.gif':
        return 'image/gif'
    else:
        # Default: PNG
        return 'image/png'

def line_oa_push_image(image_path: Optional[str] = None, preview_url: Optional[str] = None, to: str = None) -> bool:
    """
    ส่งรูปภาพไปยัง LINE Official Account โดยใช้ LINE Content API
    
    Args:
        image_path: Path ของไฟล์รูปภาพ (optional - ใช้เมื่อไม่มี preview_url)
        preview_url: URL สำหรับ preview (ต้องเป็น HTTPS URL ที่ LINE เข้าถึงได้)
        to: User ID / Group ID / Room ID (ถ้าไม่ระบุจะใช้ default)
    
    Returns:
        True ถ้าสำเร็จ, False ถ้าล้มเหลว
    """
    # ตรวจสอบสถานะการแจ้งเตือน LINE
    enabled = get_line_notifications_enabled()
    if not enabled:
        print(f"🔕 [LINE OA] ปิดการแจ้งเตือน LINE (สถานะ: {enabled}) - ข้ามการส่ง")
        return True
    
    access_token = getattr(Config, "LINE_OA_CHANNEL_ACCESS_TOKEN", "")
    to_id = to or getattr(Config, "LINE_OA_DEFAULT_TO", "")
    
    if not (access_token and to_id):
        print("⚠️ ยังไม่ได้ตั้งค่า LINE_OA_CHANNEL_ACCESS_TOKEN หรือ LINE_OA_DEFAULT_TO")
        _get_bot_logger().log_action("LINE OA Push Image", "ERROR", "Missing access_token or to_id")
        return False
    
    try:
        import requests
        import json
        from pathlib import Path
        
        # ตรวจสอบว่า preview_url เป็น HTTPS หรือไม่
        use_https_url = preview_url and preview_url.startswith('https://')
        
        # ถ้ามี preview_url (HTTPS) ให้ใช้เลย
        if use_https_url:
            original_url = preview_url
            preview_url_used = preview_url
            print(f"📷 [LINE OA] ใช้ HTTPS URL สำหรับรูปภาพ: {preview_url}")
        elif image_path:
            # ตรวจสอบว่ามี ngrok URL หรือไม่ (ใช้ ngrok ก่อน Imgur)
            ngrok_enabled = getattr(Config, "NGROK_ENABLED", False)
            ngrok_url = getattr(Config, "NGROK_URL", "")
            
            # ถ้าไม่มี ngrok URL ให้ลองดึงจาก ngrok API
            if ngrok_enabled and not ngrok_url:
                try:
                    ngrok_api_url = getattr(Config, "NGROK_API_URL", "http://localhost:4040/api/tunnels")
                    ngrok_response = requests.get(ngrok_api_url, timeout=5)
                    if ngrok_response.status_code == 200:
                        ngrok_data = ngrok_response.json()
                        if ngrok_data.get('tunnels') and len(ngrok_data['tunnels']) > 0:
                            # หา HTTPS tunnel
                            for tunnel in ngrok_data['tunnels']:
                                if tunnel.get('proto') == 'https':
                                    ngrok_url = tunnel.get('public_url', '')
                                    break
                            if not ngrok_url and len(ngrok_data['tunnels']) > 0:
                                # ถ้าไม่มี HTTPS ใช้ HTTP แทน (แต่ LINE API ต้องการ HTTPS)
                                ngrok_url = ngrok_data['tunnels'][0].get('public_url', '')
                except Exception as e:
                    print(f"⚠️ ไม่สามารถดึง ngrok URL ได้: {e}")
            
            # ถ้ามี ngrok URL ให้ใช้ ngrok URL สำหรับรูปภาพ
            if ngrok_enabled and ngrok_url:
                image_file = Path(image_path)
                if not image_file.exists():
                    print(f"❌ ไม่พบไฟล์รูปภาพ: {image_path}")
                    message_text = "📄 มี PDF สรุปข้อมูลแนบในอีเมลล์\n\nกรุณาตรวจสอบอีเมลล์เพื่อดู PDF สรุป"
                    return line_oa_push(message_text, to=to_id)
                
                # Copy ไฟล์รูปภาพไปยัง temp_uploads เพื่อให้ Flask serve ได้
                import shutil
                temp_uploads_dir = Path('temp_uploads')
                temp_uploads_dir.mkdir(exist_ok=True)
                
                # Copy ไฟล์ไปยัง temp_uploads (ใช้ชื่อไฟล์เดิม)
                temp_image_path = temp_uploads_dir / image_file.name
                if not temp_image_path.exists() or temp_image_path.stat().st_mtime < image_file.stat().st_mtime:
                    shutil.copy2(image_file, temp_image_path)
                    print(f"📋 [LINE OA] Copy รูปภาพไปยัง temp_uploads: {temp_image_path}")
                
                # สร้าง URL สำหรับรูปภาพ (แก้ double slash)
                ngrok_url_clean = ngrok_url.rstrip('/')  # ลบ trailing slash
                image_url = f"{ngrok_url_clean}/api/temp/image/{image_file.name}"
                print(f"📷 [LINE OA] ใช้ ngrok URL สำหรับรูปภาพ: {image_url}")
                
                original_url = image_url
                preview_url_used = image_url
                use_https_url = True
            else:
                # ถ้าไม่มี ngrok URL ให้อัปโหลดไปยัง Imgur
                image_file = Path(image_path)
                if not image_file.exists():
                    print(f"❌ ไม่พบไฟล์รูปภาพ: {image_path}")
                    # ถ้าไม่พบไฟล์รูปภาพ ให้ส่งข้อความแทน
                    message_text = "📄 มี PDF สรุปข้อมูลแนบในอีเมลล์\n\nกรุณาตรวจสอบอีเมลล์เพื่อดู PDF สรุป"
                    return line_oa_push(message_text, to=to_id)
                
                # อ่านไฟล์รูปภาพ
                with open(image_file, 'rb') as f:
                    image_data = f.read()
                
                # ตรวจสอบประเภทไฟล์
                file_ext = image_file.suffix.lower()
                content_type = 'image/png'
                if file_ext in ['.jpg', '.jpeg']:
                    content_type = 'image/jpeg'
                elif file_ext == '.gif':
                    content_type = 'image/gif'
                
                # อัปโหลดไปยัง Imgur เพื่อสร้าง HTTPS URL
                print(f"📤 [LINE OA] อัปโหลดรูปภาพไปยัง Imgur เพื่อสร้าง HTTPS URL...")
                
                try:
                    import base64
                    
                    # ลองใช้ Imgur API หลาย client_id (ถ้าตัวแรกไม่ทำงาน)
                    imgur_client_ids = [
                        "546c25a59c58ad7",  # Public client_id เก่า
                        "Client-ID 546c25a59c58ad7",  # รูปแบบที่มี Client-ID prefix
                    ]
                    
                    # แปลงรูปภาพเป็น base64
                    image_base64 = base64.b64encode(image_data).decode('utf-8')
                    
                    imgur_url = "https://api.imgur.com/3/image"
                    
                    # ลองใช้ client_id แต่ละตัว
                    imgur_success = False
                    for client_id in imgur_client_ids:
                        try:
                            imgur_headers = {
                                "Authorization": client_id if client_id.startswith("Client-ID") else f"Client-ID {client_id}"
                            }
                            
                            # อัปโหลดรูปภาพไปยัง Imgur (ใช้ base64)
                            imgur_response = requests.post(
                                imgur_url,
                                headers=imgur_headers,
                                data={
                                    'image': image_base64,
                                    'type': 'base64'
                                },
                                timeout=30
                            )
                            
                            if imgur_response.status_code == 200:
                                imgur_data = imgur_response.json()
                                if imgur_data.get('success') and imgur_data.get('data'):
                                    # ได้ HTTPS URL จาก Imgur
                                    original_url = imgur_data['data'].get('link', '')
                                    preview_url_used = imgur_data['data'].get('link', '')
                                    
                                    if original_url:
                                        print(f"✅ [LINE OA] อัปโหลดรูปภาพไปยัง Imgur สำเร็จ: {original_url[:50]}...")
                                        use_https_url = True
                                        imgur_success = True
                                        break
                            
                            # ถ้าได้ 401 หรือ 403 แสดงว่า client_id ไม่ถูกต้อง
                            if imgur_response.status_code in [401, 403]:
                                print(f"⚠️ Imgur client_id ไม่ถูกต้อง (status: {imgur_response.status_code})")
                                continue
                                
                        except Exception as e:
                            print(f"⚠️ Imgur upload error with client_id {client_id[:10]}...: {e}")
                            continue
                    
                    if not imgur_success:
                        raise Exception("Imgur upload ไม่สำเร็จ - ทุก client_id ล้มเหลว")
                        
                except Exception as e:
                    print(f"⚠️ ไม่สามารถอัปโหลดรูปภาพไปยัง Imgur: {e}")
                    print("   ใช้วิธีส่งข้อความแทน")
                    
                    # ส่งข้อความแจ้งว่ามี PDF สรุปในอีเมลล์
                    message_text = "📄 มี PDF สรุปข้อมูลแนบในอีเมลล์\n\nกรุณาตรวจสอบอีเมลล์เพื่อดู PDF สรุป"
                    return line_oa_push(message_text, to=to_id)
        else:
            # ไม่มีทั้ง preview_url และ image_path
            print("⚠️ ไม่มี URL หรือ path สำหรับรูปภาพ - ส่งข้อความแทน")
            message_text = "📄 มี PDF สรุปข้อมูลแนบในอีเมลล์\n\nกรุณาตรวจสอบอีเมลล์เพื่อดู PDF สรุป"
            return line_oa_push(message_text, to=to_id)
        
        # ส่งรูปภาพผ่าน LINE Messaging API
        push_url = "https://api.line.me/v2/bot/message/push"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "to": to_id,
            "messages": [{
                "type": "image",
                "originalContentUrl": original_url,
                "previewImageUrl": preview_url_used
            }]
        }
        
        response = requests.post(
            push_url,
            headers=headers,
            data=json.dumps(payload),
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"✅ [LINE OA] ส่งรูปภาพสำเร็จไปยัง {to_id[:10]}...")
            _get_bot_logger().log_action("LINE OA Push Image", "SUCCESS", f"to={to_id[:10]}")
            return True
        else:
            # ถ้าส่งรูปภาพไม่สำเร็จ ให้ส่งข้อความแทน
            error_msg = response.text
            print(f"⚠️ LINE OA push image ไม่สำเร็จ: {response.status_code} - {error_msg}")
            print(f"   ใช้วิธีส่งข้อความแทน")
            
            # ส่งข้อความแจ้งว่ามี PDF สรุปในอีเมลล์
            message_text = "📄 มี PDF สรุปข้อมูลแนบในอีเมลล์\n\nกรุณาตรวจสอบอีเมลล์เพื่อดู PDF สรุป"
            fallback_success = line_oa_push(message_text, to=to_id)
            
            if fallback_success:
                print(f"✅ [LINE OA] ส่งข้อความแจ้งสำเร็จ (fallback)")
                return True
            else:
                _get_bot_logger().log_action("LINE OA Push Image", "ERROR", f"status={response.status_code}, fallback_failed")
                return False
                
    except Exception as e:
        print(f"❌ LINE OA push image exception: {e}")
        import traceback
        traceback.print_exc()
        _get_bot_logger().log_action("LINE OA Push Image", "ERROR", f"exception={e}")
        return False

def line_oa_push_file(file_path: Optional[str] = None, filename: str = "สรุปภาษี.pdf", to: str = None, message: Optional[str] = None) -> bool:
    """
    ส่งไฟล์ PDF ไปยัง LINE Official Account โดยแปลงเป็นรูปภาพก่อนส่ง
    (LINE OA ไม่รองรับการส่งไฟล์ PDF โดยตรงสำหรับบัญชีฟรี)
    
    Args:
        file_path: Path ของไฟล์ PDF (required)
        filename: ชื่อไฟล์ที่จะแสดงใน LINE (default: "สรุปภาษี.pdf")
        to: User ID / Group ID / Room ID (ถ้าไม่ระบุจะใช้ default)
        message: ข้อความที่จะส่งก่อน PDF (optional)
    
    Returns:
        True ถ้าสำเร็จ, False ถ้าล้มเหลว
    """
    # ตรวจสอบสถานะการแจ้งเตือน LINE
    enabled = get_line_notifications_enabled()
    if not enabled:
        print(f"🔕 [LINE OA] ปิดการแจ้งเตือน LINE (สถานะ: {enabled}) - ข้ามการส่ง")
        return True
    
    access_token = getattr(Config, "LINE_OA_CHANNEL_ACCESS_TOKEN", "")
    to_id = to or getattr(Config, "LINE_OA_DEFAULT_TO", "")
    
    if not (access_token and to_id):
        print("⚠️ ยังไม่ได้ตั้งค่า LINE_OA_CHANNEL_ACCESS_TOKEN หรือ LINE_OA_DEFAULT_TO")
        _get_bot_logger().log_action("LINE OA Push File", "ERROR", "Missing access_token or to_id")
        return False
    
    # ส่งข้อความก่อน (ถ้ามี)
    if message and message.strip():
        print(f"📨 [LINE OA] ส่งข้อความก่อน PDF: {message[:50]}...")
        line_oa_push(message, to=to_id)
    
    if not file_path:
        print("⚠️ ไม่มี path สำหรับไฟล์ PDF - ส่งข้อความแทน")
        message_text = "📄 มี PDF สรุปข้อมูลแนบในอีเมลล์\n\nกรุณาตรวจสอบอีเมลล์เพื่อดู PDF สรุป"
        return line_oa_push(message_text, to=to_id)
    
    try:
        from pathlib import Path
        import tempfile
        
        file_file = Path(file_path)
        if not file_file.exists():
            print(f"❌ ไม่พบไฟล์ PDF: {file_path}")
            # ถ้าไม่พบไฟล์ ให้ส่งข้อความแทน
            message_text = "📄 มี PDF สรุปข้อมูลแนบในอีเมลล์\n\nกรุณาตรวจสอบอีเมลล์เพื่อดู PDF สรุป"
            return line_oa_push(message_text, to=to_id)
        
        # ส่งข้อความแทน (ไม่แปลง PDF เป็นรูปภาพ)
        print(f"📨 [LINE OA] ส่งข้อความแจ้ง PDF แทนรูปภาพ...")
        
        message_text = f"📄 มี PDF สรุปข้อมูล ({filename}) แนบในอีเมลล์\n\nกรุณาตรวจสอบอีเมลล์เพื่อดู PDF สรุป"
        success = line_oa_push(message_text, to=to_id)
        
        if success:
            print(f"✅ [LINE OA] ส่งข้อความแจ้ง PDF สำเร็จไปยัง {to_id[:10]}...")
            _get_bot_logger().log_action("LINE OA Push File", "SUCCESS", f"to={to_id[:10]}, text_only")
            return True
        else:
            print(f"❌ [LINE OA] ส่งข้อความไม่สำเร็จ")
            _get_bot_logger().log_action("LINE OA Push File", "ERROR", f"to={to_id[:10]}, text_failed")
            return False
            print(f"   ใช้วิธีส่งข้อความแทน")
            message_text = f"📄 มี PDF สรุปข้อมูล ({filename}) แนบในอีเมลล์\n\nกรุณาตรวจสอบอีเมลล์เพื่อดู PDF สรุป"
            return line_oa_push(message_text, to=to_id)
                
    except Exception as e:
        print(f"❌ LINE OA push file exception: {e}")
        import traceback
        traceback.print_exc()
        _get_bot_logger().log_action("LINE OA Push File", "ERROR", f"exception={e}")
        # ส่งข้อความแทน
        message_text = f"📄 มี PDF สรุปข้อมูล ({filename}) แนบในอีเมลล์\n\nกรุณาตรวจสอบอีเมลล์เพื่อดู PDF สรุป"
        return line_oa_push(message_text, to=to_id)

def line_oa_push(message: str, to: str = None) -> bool:
    # ตรวจสอบสถานะการแจ้งเตือน LINE
    enabled = get_line_notifications_enabled()
    if not enabled:
        print(f"🔕 [LINE OA] ปิดการแจ้งเตือน LINE (สถานะ: {enabled}) - ข้ามการส่ง")
        return True
    
    access_token = getattr(Config, "LINE_OA_CHANNEL_ACCESS_TOKEN", "")
    to_id = to or getattr(Config, "LINE_OA_DEFAULT_TO", "")
    _get_bot_logger().log_action(
        "LINE OA Push",
        "INFO",
        f"attempt: to={(to_id[:3] + '***') if to_id else 'None'}, token_present={bool(access_token)}"
    )
    try:
        masked = (to_id[:3] + '***') if to_id else 'None'
        print(f"📨 [LINE OA] Attempt: to={masked}, token_present={bool(access_token)}")
    except Exception:
        pass
    if not (access_token and to_id):
        print("⚠️ ยังไม่ได้ตั้งค่า LINE_OA_CHANNEL_ACCESS_TOKEN หรือ LINE_OA_DEFAULT_TO")
        _get_bot_logger().log_action("LINE OA Push", "ERROR", "Missing access_token or to_id")
        return False
    try:
        # LINE OA text message limit ประมาณ 2000 ตัวอักษร
        max_len = 2000
        r = requests.post(
            "https://api.line.me/v2/bot/message/push",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            data=json.dumps({"to": to_id, "messages": [{"type": "text", "text": message[:max_len]}]}),
            timeout=10
        )
        if r.status_code != 200:
            try:
                print(f"❌ LINE OA push ส่งไม่สำเร็จ: {r.status_code} - {r.text}")
            except Exception:
                print(f"❌ LINE OA push ส่งไม่สำเร็จ: {r.status_code}")
            # 401 มักเกิดจากใช้โทเคนผิดประเภท (เอา Notify token มาใส่ OA) หรือโทเคนหมดอายุ
            if r.status_code == 401:
                print("ℹ️ ตรวจสอบว่าใช้ Channel Access Token (long-lived) จาก LINE Developers และบอทอยู่ในห้อง/กลุ่มปลายทาง")
            _get_bot_logger().log_action(
                "LINE OA Push",
                "ERROR",
                f"to={to_id[:3]}***, status_code={r.status_code}, response={r.text[:200]}"
            )
            return False
        _get_bot_logger().log_action(
            "LINE OA Push",
            "SUCCESS",
            f"to={to_id[:3]}***, status_code=200, message_len={len(message)}"
        )
        try:
            print(f"✅ [LINE OA] Sent successfully (200) to {to_id[:3]}***")
        except Exception:
            pass
        return True
    except Exception as e:
        print(f"❌ LINE OA push exception: {e}")
        _get_bot_logger().log_action("LINE OA Push", "ERROR", f"exception={e}")
        return False

