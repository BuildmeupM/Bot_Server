"""
Email Manager - ระบบจัดการการส่งอีเมลล์อัตโนมัติ
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EmailManager:
    """จัดการการส่งอีเมลล์อัตโนมัติ"""
    
    def __init__(
        self,
        smtp_server: str = "",
        smtp_port: int = 587,
        smtp_use_tls: bool = True,
        smtp_username: str = "",
        smtp_password: str = "",
        email_from: str = ""
    ):
        """
        Initialize Email Manager
        
        Args:
            smtp_server: SMTP server address (e.g., smtp.gmail.com)
            smtp_port: SMTP port (587 for TLS, 465 for SSL)
            smtp_use_tls: Use TLS (True) or SSL (False)
            smtp_username: Email username
            smtp_password: Email password or app password
            email_from: From email address (defaults to smtp_username if not provided)
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_use_tls = smtp_use_tls
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.email_from = email_from or smtp_username
        self.is_configured = bool(smtp_server and smtp_username and smtp_password)
    
    def test_connection(self) -> tuple[bool, str]:
        """
        ทดสอบการเชื่อมต่อ SMTP
        
        Returns:
            (success, message): True ถ้าสำเร็จ, False ถ้าล้มเหลว พร้อมข้อความ
        """
        if not self.is_configured:
            return False, "ยังไม่ได้ตั้งค่า SMTP (กรุณากรอกข้อมูล SMTP)"
        
        try:
            if self.smtp_use_tls:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            
            server.login(self.smtp_username, self.smtp_password)
            server.quit()
            return True, "เชื่อมต่อ SMTP สำเร็จ"
        except smtplib.SMTPAuthenticationError:
            return False, "การยืนยันตัวตนล้มเหลว (ตรวจสอบ username/password)"
        except smtplib.SMTPConnectError:
            return False, f"ไม่สามารถเชื่อมต่อ SMTP server ได้ ({self.smtp_server}:{self.smtp_port})"
        except Exception as e:
            return False, f"เกิดข้อผิดพลาด: {str(e)}"
    
    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        body_html: Optional[str] = None,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None,
        attachments: Optional[List[Path]] = None
    ) -> tuple[bool, str]:
        """
        ส่งอีเมลล์
        
        Args:
            to_emails: รายการอีเมลล์ผู้รับ
            subject: หัวข้ออีเมลล์
            body: เนื้อหาอีเมลล์ (text)
            body_html: เนื้อหาอีเมลล์ (HTML) - ถ้ามีจะใช้แทน text
            cc_emails: รายการอีเมลล์ CC
            bcc_emails: รายการอีเมลล์ BCC
            attachments: รายการไฟล์แนบ
        
        Returns:
            (success, message): True ถ้าสำเร็จ, False ถ้าล้มเหลว พร้อมข้อความ
        """
        if not self.is_configured:
            return False, "ยังไม่ได้ตั้งค่า SMTP (กรุณากรอกข้อมูล SMTP)"
        
        if not to_emails:
            return False, "กรุณาระบุอีเมลล์ผู้รับอย่างน้อย 1 รายการ"
        
        try:
            # สร้าง message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_from
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
            
            # เพิ่มเนื้อหา
            if body_html:
                msg.attach(MIMEText(body_html, 'html', 'utf-8'))
            else:
                msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # เพิ่มไฟล์แนบ
            if attachments:
                for attachment_path in attachments:
                    if not attachment_path.exists():
                        continue
                    
                    with open(attachment_path, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                    
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment_path.name}'
                    )
                    msg.attach(part)
            
            # ส่งอีเมลล์
            all_recipients = to_emails.copy()
            if cc_emails:
                all_recipients.extend(cc_emails)
            if bcc_emails:
                all_recipients.extend(bcc_emails)
            
            if self.smtp_use_tls:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg, to_addrs=all_recipients)
            server.quit()
            
            return True, f"ส่งอีเมลล์สำเร็จไปยัง {len(to_emails)} รายการ"
        
        except smtplib.SMTPRecipientsRefused as e:
            return False, f"อีเมลล์ผู้รับไม่ถูกต้อง: {str(e)}"
        except smtplib.SMTPAuthenticationError:
            return False, "การยืนยันตัวตนล้มเหลว (ตรวจสอบ username/password)"
        except Exception as e:
            logger.error(f"Error sending email: {e}", exc_info=True)
            return False, f"เกิดข้อผิดพลาดในการส่งอีเมลล์: {str(e)}"
    
    def send_bulk_emails(
        self,
        email_list: List[Dict],
        subject_template: str = "",
        body_template: str = "",
        body_html_template: Optional[str] = None
    ) -> Dict[str, any]:
        """
        ส่งอีเมลล์หลายฉบับพร้อมกัน
        
        Args:
            email_list: รายการข้อมูลอีเมลล์ [{"to": "email@example.com", "subject": "...", "body": "...", ...}, ...]
            subject_template: Template สำหรับ subject (ใช้ {key} สำหรับ placeholder)
            body_template: Template สำหรับ body (ใช้ {key} สำหรับ placeholder)
            body_html_template: Template สำหรับ body HTML
        
        Returns:
            {
                "total": จำนวนทั้งหมด,
                "success": จำนวนที่สำเร็จ,
                "failed": จำนวนที่ล้มเหลว,
                "results": [{"to": "...", "success": True/False, "message": "..."}, ...]
            }
        """
        results = {
            "total": len(email_list),
            "success": 0,
            "failed": 0,
            "results": []
        }
        
        for email_data in email_list:
            to_email = email_data.get('to', '')
            if not to_email:
                results["results"].append({
                    "to": "",
                    "success": False,
                    "message": "ไม่มีอีเมลล์ผู้รับ"
                })
                results["failed"] += 1
                continue
            
            # Format templates
            subject = subject_template.format(**email_data) if subject_template else email_data.get('subject', '')
            body = body_template.format(**email_data) if body_template else email_data.get('body', '')
            body_html = body_html_template.format(**email_data) if body_html_template else email_data.get('body_html')
            
            # Send email
            success, message = self.send_email(
                to_emails=[to_email],
                subject=subject,
                body=body,
                body_html=body_html,
                cc_emails=email_data.get('cc'),
                bcc_emails=email_data.get('bcc'),
                attachments=[Path(f) for f in email_data.get('attachments', [])] if email_data.get('attachments') else None
            )
            
            results["results"].append({
                "to": to_email,
                "success": success,
                "message": message
            })
            
            if success:
                results["success"] += 1
            else:
                results["failed"] += 1
        
        return results


# Global email manager instance
_global_email_manager: Optional[EmailManager] = None


def get_global_email_manager() -> Optional[EmailManager]:
    """Get global email manager instance"""
    return _global_email_manager


def set_global_email_manager(email_manager: EmailManager):
    """Set global email manager instance"""
    global _global_email_manager
    _global_email_manager = email_manager

