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
    _line_notifications_enabled = enabled

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

def line_notify(message: str) -> bool:
    # ตรวจสอบสถานะการแจ้งเตือน LINE
    if not get_line_notifications_enabled():
        print("🔕 [LINE Notify] ปิดการแจ้งเตือน LINE - ข้ามการส่ง")
        return True
    
    token = getattr(Config, "LINE_NOTIFY_TOKEN", "")
    _get_bot_logger().log_action(
        "LINE Notify",
        "INFO",
        f"attempt: message_len={len(message)}"
    )
    try:
        print(f"📨 [LINE Notify] Attempt: message_len={len(message)}")
    except Exception:
        pass
    if not token:
        print("⚠️ ยังไม่ได้ตั้งค่า Config.LINE_NOTIFY_TOKEN")
        _get_bot_logger().log_action("LINE Notify", "ERROR", "Missing LINE_NOTIFY_TOKEN")
        return False
    try:
        # LINE Notify limit ประมาณ 1000 ตัวอักษร
        max_len = 1000
        r = requests.post(
            'https://notify-api.line.me/api/notify',
            headers={'Authorization': f'Bearer {token}'},
            data={'message': message[:max_len]},
            timeout=10
        )
        if r.status_code != 200:
            try:
                print(f"❌ LINE Notify ส่งไม่สำเร็จ: {r.status_code} - {r.text}")
            except Exception:
                print(f"❌ LINE Notify ส่งไม่สำเร็จ: {r.status_code}")
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
            print("✅ [LINE Notify] Sent successfully (200)")
        except Exception:
            pass
        return True
    except Exception as e:
        print(f"❌ LINE Notify exception: {e}")
        _get_bot_logger().log_action("LINE Notify", "ERROR", f"exception={e}")
        return False

def line_oa_push(message: str, to: str = None) -> bool:
    # ตรวจสอบสถานะการแจ้งเตือน LINE
    if not get_line_notifications_enabled():
        print("🔕 [LINE OA] ปิดการแจ้งเตือน LINE - ข้ามการส่ง")
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

