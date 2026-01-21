"""
Email Service - ระบบจัดการการส่งอีเมลล์อัตโนมัติแบบครบวงจร
รองรับการกำหนดแพทเทิร์น, default recipients, และ CC
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import json
import re
import socket
import zipfile
import tempfile
import shutil

# Setup logger if not already configured
try:
    logger = logging.getLogger(__name__)
except:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)


class EmailSignature:
    """คลาสสำหรับจัดการลายเซ็นต์อีเมลล์"""
    
    def __init__(
        self,
        signature_name: str,
        sender_name: str = "",
        sender_title: str = "",
        sender_email: str = "",
        sender_phone: str = "",
        sender_website: str = "",
        company_name: str = "",
        company_address: str = "",
        signature_html: Optional[str] = None,
        signature_block: Optional[str] = None,
        logo_path: Optional[str] = None,
        description: str = ""
    ):
        """
        Initialize Email Signature
        
        Args:
            signature_name: ชื่อลายเซ็นต์
            sender_name: ชื่อผู้ส่ง
            sender_title: ตำแหน่ง
            sender_email: อีเมลล์ผู้ส่ง
            sender_phone: เบอร์โทรศัพท์
            sender_website: เว็บไซต์
            company_name: ชื่อบริษัท
            company_address: ที่อยู่บริษัท
            signature_html: HTML template สำหรับลายเซ็นต์
            logo_path: Path ของโลโก้
            description: คำอธิบายลายเซ็นต์
        """
        self.signature_name = signature_name
        self.sender_name = sender_name
        self.sender_title = sender_title
        self.sender_email = sender_email
        self.sender_phone = sender_phone
        self.sender_website = sender_website
        self.company_name = company_name
        self.company_address = company_address
        self.signature_html = signature_html
        self.signature_block = signature_block  # บล็อคข้อความเดียว
        self.logo_path = logo_path
        self.description = description
    
    def generate_signature(self) -> tuple[str, Optional[str]]:
        """
        สร้างลายเซ็นต์ (text และ HTML)
        
        Returns:
            (text_signature, html_signature)
        """
        # ถ้ามี signature_block ใช้แทนการสร้างอัตโนมัติ
        if self.signature_block:
            text_signature = self.signature_block
            # สร้าง HTML จาก text block
            html_signature = self.signature_block.replace('\n', '<br>')
            # แทนที่ URL เป็น link
            import re
            # แทนที่ email เป็น link
            html_signature = re.sub(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', r'<a href="mailto:\1">\1</a>', html_signature)
            # แทนที่ website เป็น link
            html_signature = re.sub(r'(www\.[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', r'<a href="http://\1" target="_blank">\1</a>', html_signature)
            html_signature = re.sub(r'(https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}[^\s<]*)', r'<a href="\1" target="_blank">\1</a>', html_signature)
            html_signature = f"<p>{html_signature}</p>"
            
            # ถ้ามีโลโก้เพิ่มเข้าไป
            if self.logo_path and Path(self.logo_path).exists():
                html_signature = html_signature + '<p><img src="cid:signature_logo" alt="Logo" style="max-width: 200px;"></p>'
            
            return text_signature, html_signature
        
        # สร้าง text signature แบบเดิม
        text_parts = []
        if self.sender_name:
            text_parts.append(self.sender_name)
        if self.sender_title:
            text_parts.append(self.sender_title)
        if self.sender_phone:
            text_parts.append(f"M: {self.sender_phone}")
        if self.sender_email:
            text_parts.append(f"E: {self.sender_email}")
        if self.sender_website:
            text_parts.append(f"W: {self.sender_website}")
        if self.company_name:
            text_parts.append("")
            text_parts.append(self.company_name)
        if self.company_address:
            text_parts.append(self.company_address)
        
        text_signature = "\n".join(text_parts)
        
        # สร้าง HTML signature
        html_signature = None
        if self.signature_html:
            html_signature = self.signature_html
        else:
            # สร้าง HTML signature อัตโนมัติ
            html_parts = []
            if self.sender_name or self.sender_title:
                html_parts.append(f"<p><strong>{self.sender_name}</strong>")
                if self.sender_title:
                    html_parts[-1] += f"<br>{self.sender_title}"
                html_parts[-1] += "</p>"
            
            contact_parts = []
            if self.sender_phone:
                contact_parts.append(f"M: {self.sender_phone}")
            if self.sender_email:
                contact_parts.append(f'E: <a href="mailto:{self.sender_email}">{self.sender_email}</a>')
            if self.sender_website:
                contact_parts.append(f'W: <a href="{self.sender_website}" target="_blank">{self.sender_website}</a>')
            
            if contact_parts:
                html_parts.append(f"<p>{' I '.join(contact_parts)}</p>")
            
            if self.logo_path and Path(self.logo_path).exists():
                html_parts.append('<p><img src="cid:signature_logo" alt="Logo" style="max-width: 200px;"></p>')
            
            if self.company_name:
                html_parts.append(f"<p><strong>{self.company_name}</strong></p>")
            if self.company_address:
                html_parts.append(f"<p>{self.company_address.replace(chr(10), '<br>')}</p>")
            
            if html_parts:
                html_signature = "\n".join(html_parts)
        
        return text_signature, html_signature
    
    def to_dict(self) -> Dict[str, Any]:
        """แปลงเป็น dictionary สำหรับบันทึก"""
        return {
            "signature_name": self.signature_name,
            "sender_name": self.sender_name,
            "sender_title": self.sender_title,
            "sender_email": self.sender_email,
            "sender_phone": self.sender_phone,
            "sender_website": self.sender_website,
            "company_name": self.company_name,
            "company_address": self.company_address,
            "signature_html": self.signature_html,
            "signature_block": self.signature_block,
            "logo_path": self.logo_path,
            "description": self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmailSignature':
        """สร้าง EmailSignature จาก dictionary"""
        return cls(
            signature_name=data.get("signature_name", ""),
            sender_name=data.get("sender_name", ""),
            sender_title=data.get("sender_title", ""),
            sender_email=data.get("sender_email", ""),
            sender_phone=data.get("sender_phone", ""),
            sender_website=data.get("sender_website", ""),
            company_name=data.get("company_name", ""),
            company_address=data.get("company_address", ""),
            signature_html=data.get("signature_html"),
            signature_block=data.get("signature_block"),
            logo_path=data.get("logo_path"),
            description=data.get("description", "")
        )


class EmailPattern:
    """คลาสสำหรับจัดการแพทเทิร์นอีเมลล์"""
    
    def __init__(
        self,
        pattern_name: str,
        subject_template: str,
        body_template: str,
        body_html_template: Optional[str] = None,
        default_to: Optional[List[str]] = None,
        default_cc: Optional[List[str]] = None,
        default_bcc: Optional[List[str]] = None,
        description: str = "",
        logo_path: Optional[str] = None,
        company_name: str = "",
        line_user_id: str = "",
        tax_id: str = ""
    ):
        """
        Initialize Email Pattern
        
        Args:
            pattern_name: ชื่อแพทเทิร์น
            subject_template: Template สำหรับ subject (ใช้ {key} สำหรับ placeholder)
            body_template: Template สำหรับ body (ใช้ {key} สำหรับ placeholder)
            body_html_template: Template สำหรับ body HTML
            default_to: รายการอีเมลล์ผู้รับเริ่มต้น
            default_cc: รายการอีเมลล์ CC เริ่มต้น
            default_bcc: รายการอีเมลล์ BCC เริ่มต้น
            description: คำอธิบายแพทเทิร์น
            company_name: ชื่อบริษัทลูกค้า
            line_user_id: LINE User ID / Group ID / Room ID
            tax_id: เลขประจำตัวผู้เสียภาษีอากร
        """
        self.pattern_name = pattern_name
        self.subject_template = subject_template
        self.body_template = body_template
        self.body_html_template = body_html_template
        self.default_to = default_to or []
        self.default_cc = default_cc or []
        self.default_bcc = default_bcc or []
        self.description = description
        self.logo_path = logo_path  # Path ของโลโก้สำหรับใช้ในอีเมลล์
        self.company_name = company_name  # ชื่อบริษัทลูกค้า
        self.line_user_id = line_user_id  # LINE User ID / Group ID / Room ID
        self.tax_id = tax_id  # เลขประจำตัวผู้เสียภาษีอากร
    
    def format_email(
        self,
        data: Dict[str, Any],
        to_emails: Optional[List[str]] = None,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Format อีเมลล์ตามแพทเทิร์น
        
        Args:
            data: ข้อมูลสำหรับแทนที่ใน template (ใช้ {key} ใน template)
            to_emails: อีเมลล์ผู้รับ (ถ้าไม่ระบุจะใช้ default_to)
            cc_emails: อีเมลล์ CC (ถ้าไม่ระบุจะใช้ default_cc)
            bcc_emails: อีเมลล์ BCC (ถ้าไม่ระบุจะใช้ default_bcc)
        
        Returns:
            {
                "to": [...],
                "cc": [...],
                "bcc": [...],
                "subject": "...",
                "body": "...",
                "body_html": "..."
            }
        """
        try:
            # Format templates
            subject = self.subject_template.format(**data)
            body = self.body_template.format(**data)
            body_html = self.body_html_template.format(**data) if self.body_html_template else None
            
            # ใช้ default ถ้าไม่ระบุ
            to = to_emails if to_emails else self.default_to.copy()
            cc = cc_emails if cc_emails else self.default_cc.copy()
            bcc = bcc_emails if bcc_emails else self.default_bcc.copy()
            
            return {
                "to": to,
                "cc": cc,
                "bcc": bcc,
                "subject": subject,
                "body": body,
                "body_html": body_html
            }
        except KeyError as e:
            raise ValueError(f"Missing required data key: {e}")
        except Exception as e:
            raise ValueError(f"Error formatting email: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """แปลงเป็น dictionary สำหรับบันทึก"""
        return {
            "pattern_name": self.pattern_name,
            "subject_template": self.subject_template,
            "body_template": self.body_template,
            "body_html_template": self.body_html_template,
            "default_to": self.default_to,
            "default_cc": self.default_cc,
            "default_bcc": self.default_bcc,
            "description": self.description,
            "logo_path": self.logo_path,
            "company_name": self.company_name,
            "line_user_id": self.line_user_id,
            "tax_id": self.tax_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmailPattern':
        """สร้าง EmailPattern จาก dictionary"""
        return cls(
            pattern_name=data.get("pattern_name", ""),
            subject_template=data.get("subject_template", ""),
            body_template=data.get("body_template", ""),
            body_html_template=data.get("body_html_template"),
            default_to=data.get("default_to", []),
            default_cc=data.get("default_cc", []),
            default_bcc=data.get("default_bcc", []),
            description=data.get("description", ""),
            logo_path=data.get("logo_path"),
            company_name=data.get("company_name", ""),
            line_user_id=data.get("line_user_id", ""),
            tax_id=data.get("tax_id", "")
        )


class EmailService:
    """คลาสหลักสำหรับจัดการการส่งอีเมลล์"""
    
    def __init__(
        self,
        smtp_server: str = "",
        smtp_port: int = 587,
        smtp_use_tls: bool = True,
        smtp_username: str = "",
        smtp_password: str = "",
        email_from: str = "",
        patterns_file: Optional[Path] = None
    ):
        """
        Initialize Email Service
        
        Args:
            smtp_server: SMTP server address (e.g., smtp.gmail.com)
            smtp_port: SMTP port (587 for TLS, 465 for SSL)
            smtp_use_tls: Use TLS (True) or SSL (False)
            smtp_username: Email username
            smtp_password: Email password or app password
            email_from: From email address (defaults to smtp_username if not provided)
            patterns_file: Path to JSON file สำหรับเก็บ email patterns
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_use_tls = smtp_use_tls
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.email_from = email_from or smtp_username
        self.is_configured = bool(smtp_server and smtp_username and smtp_password)
        
        # จัดการ email patterns - ใช้ path ใน email_system folder
        email_system_dir = Path(__file__).parent
        self.patterns_file = patterns_file or email_system_dir / "email_patterns.json"
        self.patterns: Dict[str, EmailPattern] = {}
        self.load_patterns()
        
        # จัดการ email signatures - ใช้ path ใน email_system folder
        self.signatures_file = email_system_dir / "email_signatures.json"
        self.signatures: Dict[str, EmailSignature] = {}
        self.load_signatures()
    
    def validate_smtp_server(self) -> tuple[bool, str]:
        """
        ตรวจสอบความถูกต้องของ SMTP server name
        
        Returns:
            (valid, message): True ถ้าถูกต้อง, False ถ้าไม่ถูกต้อง พร้อมข้อความ
        """
        if not self.smtp_server:
            return False, "กรุณาระบุ SMTP Server"
        
        # ตรวจสอบรูปแบบพื้นฐาน
        if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$', self.smtp_server):
            return False, f"รูปแบบ SMTP Server ไม่ถูกต้อง: {self.smtp_server}"
        
        # ตรวจสอบการสะกดที่พบบ่อย
        common_typos = {
            'stmp.gmail.com': 'smtp.gmail.com',
            'smtp.gmai.com': 'smtp.gmail.com',
            'smtp.gmail.co': 'smtp.gmail.com',
            'stmp.outlook.com': 'smtp.outlook.com',
            'smtp.outlok.com': 'smtp.outlook.com',
        }
        
        if self.smtp_server.lower() in common_typos:
            suggestion = common_typos[self.smtp_server.lower()]
            return False, f"SMTP Server อาจสะกดผิด: '{self.smtp_server}' → ควรเป็น '{suggestion}'"
        
        # พยายาม resolve hostname
        try:
            socket.gethostbyname(self.smtp_server)
        except socket.gaierror as e:
            error_code = e.args[0] if e.args else None
            if error_code == 11001 or 'getaddrinfo failed' in str(e).lower():
                return False, f"ไม่พบ SMTP Server: '{self.smtp_server}' (ตรวจสอบการสะกดและเชื่อมต่ออินเทอร์เน็ต)"
            return False, f"ไม่สามารถ resolve hostname ได้: {str(e)}"
        except Exception as e:
            return False, f"เกิดข้อผิดพลาดในการตรวจสอบ hostname: {str(e)}"
        
        return True, "SMTP Server ถูกต้อง"
    
    def test_connection(self) -> tuple[bool, str]:
        """
        ทดสอบการเชื่อมต่อ SMTP
        
        Returns:
            (success, message): True ถ้าสำเร็จ, False ถ้าล้มเหลว พร้อมข้อความ
        """
        if not self.is_configured:
            return False, "ยังไม่ได้ตั้งค่า SMTP (กรุณากรอกข้อมูล SMTP)"
        
        # ตรวจสอบ SMTP server ก่อน
        valid, message = self.validate_smtp_server()
        if not valid:
            return False, message
        
        # กำหนดการใช้ TLS/SSL ตาม port โดยอัตโนมัติ
        # Port 465 = SSL, Port 587 = TLS
        use_ssl = False
        if self.smtp_port == 465:
            use_ssl = True  # Port 465 ใช้ SSL
        elif self.smtp_port == 587:
            use_ssl = False  # Port 587 ใช้ TLS
        else:
            # สำหรับ port อื่นๆ ใช้ค่าจากการตั้งค่า
            use_ssl = not self.smtp_use_tls
        
        try:
            if use_ssl:
                # ใช้ SSL สำหรับ port 465
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=10)
            else:
                # ใช้ TLS สำหรับ port 587
                server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10)
                server.starttls()
            
            server.login(self.smtp_username, self.smtp_password)
            server.quit()
            return True, "เชื่อมต่อ SMTP สำเร็จ"
        except socket.gaierror as e:
            error_code = e.args[0] if e.args else None
            if error_code == 11001 or 'getaddrinfo failed' in str(e).lower():
                return False, f"ไม่พบ SMTP Server: '{self.smtp_server}' (ตรวจสอบการสะกด - ตัวอย่าง: smtp.gmail.com, smtp.outlook.com)"
            return False, f"ไม่สามารถ resolve hostname ได้: {str(e)}"
        except socket.timeout:
            return False, f"เชื่อมต่อ SMTP timeout (ตรวจสอบ port {self.smtp_port} และ firewall)"
        except ConnectionRefusedError:
            return False, f"การเชื่อมต่อถูกปฏิเสธ (ตรวจสอบ port {self.smtp_port} และ firewall)"
        except smtplib.SMTPAuthenticationError as e:
            error_msg = "การยืนยันตัวตนล้มเหลว"
            # เพิ่มคำแนะนำตาม SMTP server
            if 'zoho' in self.smtp_server.lower():
                error_msg += "\n💡 สำหรับ Zoho: ตรวจสอบว่าใช้รหัสผ่านที่ถูกต้อง หรือใช้ App Password (ถ้าเปิด 2FA)"
            elif 'gmail' in self.smtp_server.lower():
                error_msg += "\n💡 สำหรับ Gmail: ต้องใช้ App Password แทนรหัสผ่านปกติ (เปิด 2-Step Verification ก่อน)"
            else:
                error_msg += "\n💡 ตรวจสอบ username/password หรือ App Password (ถ้าเปิด 2FA)"
            return False, error_msg
        except smtplib.SMTPConnectError as e:
            return False, f"ไม่สามารถเชื่อมต่อ SMTP server ได้ ({self.smtp_server}:{self.smtp_port}) - {str(e)}"
        except smtplib.SMTPException as e:
            return False, f"เกิดข้อผิดพลาด SMTP: {str(e)}"
        except Exception as e:
            error_msg = str(e)
            # ตรวจสอบ error messages ที่พบบ่อย
            if 'getaddrinfo failed' in error_msg.lower() or '11001' in error_msg:
                return False, f"ไม่พบ SMTP Server: '{self.smtp_server}' (ตรวจสอบการสะกด - ตัวอย่าง: smtp.gmail.com)"
            elif 'timed out' in error_msg.lower():
                return False, f"เชื่อมต่อ timeout (ตรวจสอบ port {self.smtp_port} และ firewall)"
            return False, f"เกิดข้อผิดพลาด: {error_msg}"
    
    def add_pattern(self, pattern: EmailPattern) -> bool:
        """
        เพิ่ม email pattern
        
        Args:
            pattern: EmailPattern object
        
        Returns:
            True ถ้าสำเร็จ
        """
        self.patterns[pattern.pattern_name] = pattern
        self.save_patterns()
        return True
    
    def update_pattern(self, pattern_name: str, pattern: EmailPattern) -> bool:
        """
        อัปเดต email pattern
        
        Args:
            pattern_name: ชื่อแพทเทิร์นเดิม
            pattern: EmailPattern object ใหม่
        
        Returns:
            True ถ้าสำเร็จ, False ถ้าไม่พบ pattern
        """
        if pattern_name not in self.patterns:
            return False
        
        # ถ้าเปลี่ยนชื่อ ต้องลบชื่อเก่าและเพิ่มชื่อใหม่
        if pattern_name != pattern.pattern_name:
            del self.patterns[pattern_name]
        
        self.patterns[pattern.pattern_name] = pattern
        self.save_patterns()
        return True
    
    def get_pattern(self, pattern_name: str) -> Optional[EmailPattern]:
        """ดึง email pattern"""
        return self.patterns.get(pattern_name)
    
    def list_patterns(self) -> List[str]:
        """รายชื่อ pattern ทั้งหมด"""
        return list(self.patterns.keys())
    
    def delete_pattern(self, pattern_name: str) -> bool:
        """ลบ email pattern"""
        if pattern_name in self.patterns:
            del self.patterns[pattern_name]
            self.save_patterns()
            return True
        return False
    
    def load_patterns(self):
        """โหลด patterns จากไฟล์"""
        try:
            if self.patterns_file.exists():
                with open(self.patterns_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.patterns = {
                        name: EmailPattern.from_dict(pattern_data)
                        for name, pattern_data in data.items()
                    }
        except Exception as e:
            logger.warning(f"ไม่สามารถโหลด email patterns ได้: {e}")
            self.patterns = {}
    
    def save_patterns(self):
        """บันทึก patterns ลงไฟล์"""
        try:
            data = {
                name: pattern.to_dict()
                for name, pattern in self.patterns.items()
            }
            with open(self.patterns_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"ไม่สามารถบันทึก email patterns ได้: {e}")
    
    def _ensure_signatures_initialized(self):
        """ตรวจสอบและ initialize signatures ถ้ายังไม่มี"""
        if not hasattr(self, 'signatures'):
            # ตรวจสอบ path ที่เป็นไปได้
            possible_paths = [
                Path("email_system/email_signatures.json"),
                Path("email_signatures.json"),
            ]
            for path in possible_paths:
                if path.exists():
                    self.signatures_file = path
                    break
            else:
                # ถ้าไม่พบไฟล์ ให้ใช้ path เริ่มต้น
                self.signatures_file = Path("email_system/email_signatures.json")
            self.signatures: Dict[str, EmailSignature] = {}
            self.load_signatures()
    
    def add_signature(self, signature: EmailSignature) -> bool:
        """เพิ่ม email signature"""
        self._ensure_signatures_initialized()
        self.signatures[signature.signature_name] = signature
        self.save_signatures()
        return True
    
    def get_signature(self, signature_name: str) -> Optional[EmailSignature]:
        """ดึง email signature"""
        self._ensure_signatures_initialized()
        return self.signatures.get(signature_name)
    
    def list_signatures(self) -> List[str]:
        """รายชื่อ signature ทั้งหมด"""
        self._ensure_signatures_initialized()
        return list(self.signatures.keys())
    
    def update_signature(self, signature_name: str, signature: EmailSignature) -> bool:
        """อัปเดต email signature"""
        self._ensure_signatures_initialized()
        if signature_name not in self.signatures:
            return False
        
        if signature_name != signature.signature_name:
            del self.signatures[signature_name]
        
        self.signatures[signature.signature_name] = signature
        self.save_signatures()
        return True
    
    def delete_signature(self, signature_name: str) -> bool:
        """ลบ email signature"""
        self._ensure_signatures_initialized()
        if signature_name in self.signatures:
            del self.signatures[signature_name]
            self.save_signatures()
            return True
        return False
    
    def load_signatures(self):
        """โหลด signatures จากไฟล์"""
        if not hasattr(self, 'signatures_file'):
            # ตรวจสอบ path ที่เป็นไปได้
            possible_paths = [
                Path("email_system/email_signatures.json"),
                Path("email_signatures.json"),
            ]
            for path in possible_paths:
                if path.exists():
                    self.signatures_file = path
                    break
            else:
                # ถ้าไม่พบไฟล์ ให้ใช้ path เริ่มต้น
                self.signatures_file = Path("email_system/email_signatures.json")
        
        if not hasattr(self, 'signatures'):
            self.signatures: Dict[str, EmailSignature] = {}
        
        try:
            if self.signatures_file.exists():
                with open(self.signatures_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.signatures = {
                        name: EmailSignature.from_dict(sig_data)
                        for name, sig_data in data.items()
                    }
                    logger.info(f"✅ โหลด email signatures สำเร็จ: {len(self.signatures)} รายการ")
            else:
                logger.warning(f"⚠️ ไม่พบไฟล์ signatures: {self.signatures_file}")
                self.signatures = {}
        except Exception as e:
            logger.warning(f"ไม่สามารถโหลด email signatures ได้: {e}")
            self.signatures = {}
    
    def save_signatures(self):
        """บันทึก signatures ลงไฟล์"""
        if not hasattr(self, 'signatures_file'):
            self.signatures_file = Path("email_signatures.json")
        if not hasattr(self, 'signatures'):
            self.signatures: Dict[str, EmailSignature] = {}
        
        try:
            data = {
                name: signature.to_dict()
                for name, signature in self.signatures.items()
            }
            with open(self.signatures_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"ไม่สามารถบันทึก email signatures ได้: {e}")
    
    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        body_html: Optional[str] = None,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None,
        attachments: Optional[List[Path]] = None,
        logo_path: Optional[Path] = None,
        signature_name: Optional[str] = None,
        zip_attachments: bool = True
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
            logo_path: Path ของโลโก้
            signature_name: ชื่อลายเซ็นต์ที่ต้องการใช้
        
        Returns:
            (success, message): True ถ้าสำเร็จ, False ถ้าล้มเหลว พร้อมข้อความ
        """
        if not self.is_configured:
            return False, "ยังไม่ได้ตั้งค่า SMTP (กรุณากรอกข้อมูล SMTP)"
        
        if not to_emails:
            return False, "กรุณาระบุอีเมลล์ผู้รับอย่างน้อย 1 รายการ"
        
        # รวมลายเซ็นต์ถ้ามี
        signature = None
        signature_logo_path = None
        if signature_name:
            signature = self.get_signature(signature_name)
            if signature:
                if signature.logo_path:
                    signature_logo_path = Path(signature.logo_path)
        
        # ใช้โลโก้จาก signature หรือจาก parameter
        final_logo_path = signature_logo_path if signature_logo_path and signature_logo_path.exists() else logo_path
        
        try:
            # สร้าง message - ใช้ 'related' ถ้ามีโลโก้ เพื่อให้สามารถ embed image ได้
            if final_logo_path and Path(final_logo_path).exists():
                msg = MIMEMultipart('related')
            else:
                msg = MIMEMultipart('alternative')
            
            msg['From'] = self.email_from
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
            
            # สร้าง alternative part สำหรับเนื้อหา
            if final_logo_path and Path(final_logo_path).exists():
                # ถ้ามีโลโก้ ใช้ related multipart
                alternative = MIMEMultipart('alternative')
                msg.attach(alternative)
                content_part = alternative
            else:
                content_part = msg
            
            # รวมลายเซ็นต์เข้าไปในเนื้อหา
            text_signature = ""
            html_signature = None
            if signature:
                text_sig, html_sig = signature.generate_signature()
                text_signature = text_sig
                html_signature = html_sig
                
                # ถ้ามี body_html ให้รวมแค่ HTML signature เท่านั้น (ไม่รวม text ใน body)
                if body_html:
                    if html_signature:
                        body_html = body_html + "<br><br>" + html_signature
                    else:
                        # ถ้าไม่มี HTML signature ใช้ text แทน
                        body_html = body_html + "<br><br><pre>" + text_signature.replace('\n', '<br>') + "</pre>"
                    # ไม่ต้องรวม text signature ใน body เพราะมี HTML แล้ว
                else:
                    # ถ้าไม่มี body_html ให้รวม text signature ใน text body
                    # เก็บ body เดิมไว้ก่อนเพื่อใช้สร้าง HTML
                    original_body = body
                    if body:
                        body = body + "\n\n" + text_signature
                    # ถ้ามี HTML signature แต่ไม่มี body_html สร้าง HTML body จาก body เดิม (ก่อนรวมลายเซ็นต์)
                    if html_signature:
                        # ใช้ original_body (ก่อนรวมลายเซ็นต์) เพื่อไม่ให้ซ้ำ
                        body_html = "<p>" + original_body.replace('\n', '<br>') + "</p><br><br>" + html_signature
            
            # เพิ่มเนื้อหา - ใช้ MIMEMultipart('alternative') เพื่อให้ email client เลือกแสดง HTML หรือ text
            if body_html:
                # ถ้ามีโลโก้ แทนที่ {logo} ใน HTML ด้วย embedded image
                if final_logo_path and Path(final_logo_path).exists():
                    # อ่านโลโก้และ embed
                    with open(final_logo_path, 'rb') as f:
                        logo_data = f.read()
                    
                    logo = MIMEImage(logo_data)
                    logo.add_header('Content-ID', '<logo>')
                    logo.add_header('Content-Disposition', 'inline', filename='logo.png')
                    msg.attach(logo)
                    
                    # แทนที่ {logo} ใน HTML
                    body_html = body_html.replace('{logo}', '<img src="cid:logo" alt="Logo" style="max-width: 200px;">')
                
                # ถ้ามี signature logo แทนที่ใน HTML
                if signature and signature_logo_path and signature_logo_path.exists():
                    with open(signature_logo_path, 'rb') as f:
                        sig_logo_data = f.read()
                    
                    sig_logo = MIMEImage(sig_logo_data)
                    sig_logo.add_header('Content-ID', '<signature_logo>')
                    sig_logo.add_header('Content-Disposition', 'inline', filename='signature_logo.png')
                    msg.attach(sig_logo)
                    
                    # แทนที่ signature logo ใน HTML (ถ้ายังไม่มี)
                    if 'cid:signature_logo' not in body_html:
                        # ถ้า HTML signature มี logo อยู่แล้ว ไม่ต้องทำอะไร
                        pass
                
                # สร้าง alternative part: text และ HTML
                # Email client จะเลือกแสดง HTML ถ้ารองรับ
                # ถ้ามี signature ให้ attach แค่ HTML version เท่านั้น (ไม่ attach text version) เพื่อหลีกเลี่ยงการแสดงซ้ำ
                if signature:
                    # มี signature → attach แค่ HTML version (มีลายเซ็นต์แล้ว)
                    content_part.attach(MIMEText(body_html, 'html', 'utf-8'))
                else:
                    # ไม่มี signature → attach ทั้ง text และ HTML version
                    content_part.attach(MIMEText(body, 'plain', 'utf-8'))
                    content_part.attach(MIMEText(body_html, 'html', 'utf-8'))
            else:
                # ถ้าไม่มี body_html แสดงแค่ text
                content_part.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Zip ไฟล์แนบทั้งหมด และส่งไฟล์สำคัญ (Pay-in, กองทุน กยศ., สรุปภาษี) ทั้งใน zip และนอก zip
            # แต่จะทำเฉพาะเมื่อ zip_attachments = True
            filtered_attachments = []
            zip_path = None
            temp_zip_dir = None
            files_in_zip_count = 0
            
            if attachments and zip_attachments:
                # รวบรวมไฟล์ทั้งหมดและระบุไฟล์สำคัญ
                all_files = []  # ไฟล์ทั้งหมดสำหรับ zip
                payin_file = None
                student_loan_file = None
                summary_file = None
                
                for attachment_item in attachments:
                    # รองรับทั้งรูปแบบใหม่ (dict) และรูปแบบเก่า (Path)
                    if isinstance(attachment_item, dict):
                        attachment_path = attachment_item.get('path')
                        attachment_filename = attachment_item.get('filename')
                    else:
                        attachment_path = attachment_item
                        attachment_filename = None
                    
                    if not attachment_path or not Path(attachment_path).exists():
                        continue
                    
                    # ข้าม signature logo และ pattern logo
                    attachment_path_obj = Path(attachment_path).resolve()
                    
                    # ข้าม signature logo
                    if signature_logo_path and signature_logo_path.exists():
                        try:
                            sig_logo_resolved = signature_logo_path.resolve()
                            if attachment_path_obj == sig_logo_resolved:
                                continue
                        except Exception:
                            pass
                    
                    # ข้าม pattern logo
                    if logo_path:
                        try:
                            logo_path_obj = Path(logo_path)
                            if logo_path_obj.exists():
                                logo_resolved = logo_path_obj.resolve()
                                if attachment_path_obj == logo_resolved:
                                    continue
                        except Exception:
                            pass
                    
                    # ใช้ชื่อไฟล์เดิมถ้ามี ไม่เช่นนั้นใช้ชื่อไฟล์จาก path
                    filename = attachment_filename or attachment_path_obj.name
                    filename_lower = filename.lower()
                    
                    file_info = {
                        'path': attachment_path_obj,
                        'filename': filename
                    }
                    
                    # เพิ่มไฟล์ทั้งหมดเข้า all_files สำหรับ zip
                    all_files.append(file_info)
                    
                    # ตรวจสอบว่าเป็นไฟล์ กองทุน กยศ. (ตรวจสอบก่อน Pay-in เพราะอาจมี "pay-in" ในชื่อด้วย)
                    if not student_loan_file and ('กยศ' in filename or ('กองทุน' in filename and 'กยศ' in filename)):
                        student_loan_file = file_info
                        logger.info(f"📎 พบไฟล์ กองทุน กยศ.: {filename}")
                    
                    # ตรวจสอบว่าเป็นไฟล์ Pay-in ชำระภาษี (ต้องไม่ใช่ กองทุน กยศ.)
                    elif not payin_file and not ('กยศ' in filename or 'กองทุน' in filename) and \
                         ('pay-in' in filename_lower or 'payin' in filename_lower or 
                          ('ชำระ' in filename and 'ภาษี' in filename) or
                          'slip' in filename_lower):
                        payin_file = file_info
                        logger.info(f"📎 พบไฟล์ Pay-in: {filename}")
                    
                    # ตรวจสอบว่าเป็นไฟล์ สรุปภาษี
                    elif not summary_file and ('สรุป' in filename or 'summary' in filename_lower):
                        summary_file = file_info
                        logger.info(f"📎 พบไฟล์ สรุปภาษี: {filename}")
                
                # สร้าง zip file ที่มีทุกไฟล์
                if all_files:
                    try:
                        # สร้าง temporary directory สำหรับ zip file
                        temp_zip_dir = tempfile.mkdtemp()
                        zip_filename = f"เอกสารภาษี_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
                        zip_path = Path(temp_zip_dir) / zip_filename
                        
                        # ลองใช้ ZIP_BZIP2 ก่อน (บีบอัดดีกว่า ZIP_DEFLATED แต่ช้ากว่า)
                        # ถ้าไม่รองรับให้ใช้ ZIP_DEFLATED แทน
                        compression_method = zipfile.ZIP_DEFLATED
                        compression_level = 9
                        
                        # ตรวจสอบว่า Python รองรับ BZIP2 หรือไม่
                        try:
                            # ลองสร้าง zip file ดูว่า BZIP2 ใช้ได้หรือไม่
                            test_zip = zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_BZIP2, compresslevel=9)
                            test_zip.close()
                            zip_path.unlink()  # ลบไฟล์ทดสอบ
                            compression_method = zipfile.ZIP_BZIP2
                            logger.info("📦 ใช้ BZIP2 compression (บีบอัดดีกว่า)")
                        except (AttributeError, RuntimeError):
                            # ถ้าไม่รองรับ BZIP2 ให้ใช้ DEFLATED แทน
                            compression_method = zipfile.ZIP_DEFLATED
                            logger.info("📦 ใช้ DEFLATED compression (level 9)")
                        
                        # สร้าง zip file ที่มีทุกไฟล์ (ใช้ compression level สูงสุด = 9)
                        with zipfile.ZipFile(zip_path, 'w', compression_method, compresslevel=compression_level) as zipf:
                            for file_info in all_files:
                                zipf.write(file_info['path'], file_info['filename'])
                                logger.info(f"📦 เพิ่มไฟล์เข้า zip: {file_info['filename']}")
                        
                        zip_size_mb = zip_path.stat().st_size / 1024 / 1024
                        logger.info(f"✅ สร้าง zip file สำเร็จ: {zip_path} (ขนาด: {zip_size_mb:.2f} MB) - รวม {len(all_files)} ไฟล์")
                        
                        # ถ้าไฟล์ zip ยังใหญ่เกิน 20 MB ให้แจ้งเตือน
                        if zip_size_mb > 20:
                            logger.warning(f"⚠️ ไฟล์ zip ยังใหญ่เกินไป ({zip_size_mb:.2f} MB) - อาจส่งอีเมลล์ไม่สำเร็จ")
                        
                        # เก็บจำนวนไฟล์ใน zip
                        files_in_zip_count = len(all_files)
                        
                        # สร้าง filtered_attachments: zip file + ไฟล์สำคัญ 3 ไฟล์ (ถ้ามี)
                        filtered_attachments = [{
                            'path': zip_path,
                            'filename': zip_filename
                        }]
                        
                        # เพิ่มไฟล์สำคัญ 3 ไฟล์เข้า filtered_attachments (ส่งทั้งใน zip และนอก zip)
                        if payin_file:
                            filtered_attachments.append(payin_file)
                            logger.info(f"📎 เพิ่มไฟล์ Pay-in เข้า attachments (นอก zip): {payin_file['filename']}")
                        if student_loan_file:
                            filtered_attachments.append(student_loan_file)
                            logger.info(f"📎 เพิ่มไฟล์ กองทุน กยศ. เข้า attachments (นอก zip): {student_loan_file['filename']}")
                        if summary_file:
                            filtered_attachments.append(summary_file)
                            logger.info(f"📎 เพิ่มไฟล์ สรุปภาษี เข้า attachments (นอก zip): {summary_file['filename']}")
                    except Exception as e:
                        logger.error(f"❌ เกิดข้อผิดพลาดในการสร้าง zip file: {e}", exc_info=True)
                        # ถ้า zip ไม่สำเร็จ ให้ใช้ไฟล์เดิมทั้งหมด
                        filtered_attachments = attachments
                else:
                    logger.warning("⚠️ ไม่พบไฟล์สำหรับ zip - ส่งไฟล์ทั้งหมด")
                    # ถ้าไม่พบไฟล์ ให้ใช้ไฟล์เดิมทั้งหมด
                    filtered_attachments = attachments
            elif attachments and not zip_attachments:
                # ถ้าปิดการ zip ให้ใช้ไฟล์เดิมทั้งหมด
                filtered_attachments = attachments
                logger.info("📎 ปิดการ zip ไฟล์ - ส่งไฟล์ทั้งหมดตามปกติ")
            
            # เพิ่มไฟล์แนบ (ใช้ filtered_attachments ที่ zip แล้ว)
            if filtered_attachments:
                for attachment_item in filtered_attachments:
                    # รองรับทั้งรูปแบบใหม่ (dict) และรูปแบบเก่า (Path)
                    if isinstance(attachment_item, dict):
                        attachment_path = attachment_item.get('path')
                        attachment_filename = attachment_item.get('filename')
                    else:
                        # รูปแบบเก่า: Path object
                        attachment_path = attachment_item
                        attachment_filename = None
                    
                    if not attachment_path or not Path(attachment_path).exists():
                        continue
                    
                    # ข้าม signature logo และ pattern logo - มันเป็น embedded image ไม่ใช่ attachment
                    attachment_path_obj = Path(attachment_path).resolve()
                    
                    # ข้าม signature logo
                    if signature_logo_path and signature_logo_path.exists():
                        try:
                            sig_logo_resolved = signature_logo_path.resolve()
                            if attachment_path_obj == sig_logo_resolved:
                                logger.debug(f"Skipping signature logo: {attachment_path_obj}")
                                continue  # ข้าม signature logo
                        except Exception as e:
                            logger.warning(f"Error comparing signature logo path: {e}")
                    
                    # ข้าม pattern logo (ถ้ามี)
                    if logo_path:
                        try:
                            logo_path_obj = Path(logo_path)
                            if logo_path_obj.exists():
                                logo_resolved = logo_path_obj.resolve()
                                if attachment_path_obj == logo_resolved:
                                    logger.debug(f"Skipping pattern logo: {attachment_path_obj}")
                                    continue  # ข้าม pattern logo
                        except Exception as e:
                            logger.warning(f"Error comparing pattern logo path: {e}")
                    
                    # ใช้ชื่อไฟล์เดิมถ้ามี ไม่เช่นนั้นใช้ชื่อไฟล์จาก path
                    if attachment_filename:
                        filename = attachment_filename
                    else:
                        filename = attachment_path_obj.name
                    
                    with open(attachment_path, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                    
                    encoders.encode_base64(part)
                    # ใช้ชื่อไฟล์เดิมที่ผู้ใช้อัปโหลด
                    part.add_header(
                        'Content-Disposition',
                        'attachment',
                        filename=filename
                    )
                    msg.attach(part)
            
            # ส่งอีเมลล์
            all_recipients = to_emails.copy()
            if cc_emails:
                all_recipients.extend(cc_emails)
            if bcc_emails:
                all_recipients.extend(bcc_emails)
            
            # กำหนดการใช้ TLS/SSL ตาม port โดยอัตโนมัติ
            # Port 465 = SSL, Port 587 = TLS
            use_ssl = False
            if self.smtp_port == 465:
                use_ssl = True  # Port 465 ใช้ SSL
            elif self.smtp_port == 587:
                use_ssl = False  # Port 587 ใช้ TLS
            else:
                # สำหรับ port อื่นๆ ใช้ค่าจากการตั้งค่า
                use_ssl = not self.smtp_use_tls
            
            if use_ssl:
                # ใช้ SSL สำหรับ port 465
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=120)
            else:
                # ใช้ TLS สำหรับ port 587
                server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=120)
                server.starttls()
            
            server.login(self.smtp_username, self.smtp_password)
            
            # ส่งอีเมลล์พร้อม retry mechanism
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    server.send_message(msg, to_addrs=all_recipients)
                    break  # ส่งสำเร็จ
                except smtplib.SMTPDataError as e:
                    # จัดการ error 553 (Sender is not allowed to relay emails)
                    if e.smtp_code == 553:
                        error_msg = (
                            f"❌ SMTP Server ปฏิเสธการส่งอีเมล (Error 553: Sender is not allowed to relay emails)\n"
                            f"   สาเหตุ: From address ({self.email_from}) ไม่ตรงกับ domain ของ SMTP server\n"
                            f"   วิธีแก้ไข:\n"
                            f"   1. ตรวจสอบว่า From address ตรงกับ domain ของ SMTP server\n"
                            f"      - ถ้าใช้ Gmail SMTP → From ต้องเป็น @gmail.com\n"
                            f"      - ถ้าใช้ Outlook SMTP → From ต้องเป็น @outlook.com หรือ @hotmail.com\n"
                            f"   2. ตั้งค่า email_from ให้ตรงกับ smtp_username หรือเป็น domain เดียวกัน\n"
                            f"   SMTP Server: {self.smtp_server}\n"
                            f"   SMTP Username: {self.smtp_username}\n"
                            f"   From Address: {self.email_from}"
                        )
                        logger.error(error_msg)
                        return False, error_msg
                    else:
                        # Error อื่นๆ จาก SMTPDataError
                        error_msg = f"❌ SMTP Server ปฏิเสธการส่งอีเมล (Error {e.smtp_code}): {e.smtp_error.decode('utf-8', errors='ignore')}"
                        logger.error(error_msg)
                        return False, error_msg
                except (TimeoutError, smtplib.SMTPServerDisconnected) as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"⚠️ ส่งอีเมลล์ล้มเหลว (ครั้งที่ {attempt + 1}), กำลังลองใหม่...")
                        import time
                        time.sleep(2)  # รอ 2 วินาทีก่อนลองใหม่
                        # สร้างการเชื่อมต่อใหม่
                        try:
                            server.quit()
                        except:
                            pass
                        if use_ssl:
                            server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=120)
                        else:
                            server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=120)
                            server.starttls()
                        server.login(self.smtp_username, self.smtp_password)
                    else:
                        raise  # ลองครบแล้ว ให้ raise error
            
            server.quit()
            
            # ลบ temporary zip file หลังจากส่งอีเมลล์เสร็จ
            if zip_path and zip_path.exists():
                try:
                    zip_path.unlink()
                    logger.debug(f"🗑️ ลบ temporary zip file: {zip_path.name}")
                except Exception as e:
                    logger.warning(f"ไม่สามารถลบ temporary zip file ได้: {zip_path} - {e}")
            
            # ลบ temporary directory
            if temp_zip_dir and Path(temp_zip_dir).exists():
                try:
                    shutil.rmtree(temp_zip_dir)
                    logger.debug(f"🗑️ ลบ temporary directory: {temp_zip_dir}")
                except Exception as e:
                    logger.warning(f"ไม่สามารถลบ temporary directory ได้: {temp_zip_dir} - {e}")
            
            attachment_info = ""
            if filtered_attachments:
                if zip_path and files_in_zip_count > 0:
                    attachment_info = f" พร้อมไฟล์แนบ (zip: {files_in_zip_count} ไฟล์)"
                else:
                    attachment_info = f" พร้อมไฟล์แนบ {len(filtered_attachments)} ไฟล์"
            
            return True, f"ส่งอีเมลล์สำเร็จไปยัง {len(to_emails)} รายการ (CC: {len(cc_emails or [])}){attachment_info}"
        
        except smtplib.SMTPRecipientsRefused as e:
            return False, f"อีเมลล์ผู้รับไม่ถูกต้อง: {str(e)}"
        except smtplib.SMTPAuthenticationError:
            return False, "การยืนยันตัวตนล้มเหลว (ตรวจสอบ username/password)"
        except TimeoutError as e:
            logger.error(f"SMTP Timeout: {e}", exc_info=True)
            return False, "⏰ การส่งอีเมลล์หมดเวลา (Timeout) - กรุณาลองใหม่อีกครั้ง หรือตรวจสอบขนาดไฟล์แนบ"
        except smtplib.SMTPServerDisconnected as e:
            logger.error(f"SMTP Disconnected: {e}", exc_info=True)
            return False, "🔌 การเชื่อมต่อ SMTP ขาดหาย - กรุณาตรวจสอบเครือข่ายและลองใหม่อีกครั้ง"
        except Exception as e:
            logger.error(f"Error sending email: {e}", exc_info=True)
            return False, f"เกิดข้อผิดพลาดในการส่งอีเมลล์: {str(e)}"
    
    def send_email_by_pattern(
        self,
        pattern_name: str,
        data: Dict[str, Any],
        to_emails: Optional[List[str]] = None,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None,
        attachments: Optional[List[Path]] = None,
        signature_name: Optional[str] = None,
        subject_override: Optional[str] = None,
        body_override: Optional[str] = None,
        zip_attachments: bool = True
    ) -> tuple[bool, str]:
        """
        ส่งอีเมลล์ตามแพทเทิร์น
        
        Args:
            pattern_name: ชื่อแพทเทิร์น
            data: ข้อมูลสำหรับแทนที่ใน template
            to_emails: อีเมลล์ผู้รับ (ถ้าไม่ระบุจะใช้ default จาก pattern)
            cc_emails: อีเมลล์ CC (ถ้าไม่ระบุจะใช้ default จาก pattern)
            bcc_emails: อีเมลล์ BCC (ถ้าไม่ระบุจะใช้ default จาก pattern)
            attachments: รายการไฟล์แนบ
            subject_override: หัวข้ออีเมลล์ที่จะใช้แทน pattern (ถ้ามี)
            body_override: เนื้อหาอีเมลล์ที่จะใช้แทน pattern (ถ้ามี)
        
        Returns:
            (success, message): True ถ้าสำเร็จ, False ถ้าล้มเหลว พร้อมข้อความ
        """
        pattern = self.get_pattern(pattern_name)
        if not pattern:
            return False, f"ไม่พบแพทเทิร์น: {pattern_name}"
        
        try:
            email_data = pattern.format_email(data, to_emails, cc_emails, bcc_emails)
            
            # ใช้ subject และ body จาก override ถ้ามี (แทนที่ pattern)
            subject = subject_override if subject_override else email_data["subject"]
            body = body_override if body_override else email_data["body"]
            
            # ใช้โลโก้จาก pattern ถ้ามี
            logo_path = None
            if pattern.logo_path:
                logo_path = Path(pattern.logo_path)
                if not logo_path.exists():
                    logo_path = None
            
            return self.send_email(
                to_emails=email_data["to"],
                subject=subject,  # ใช้ subject ที่ override แล้ว
                body=body,  # ใช้ body ที่ override แล้ว
                body_html=email_data["body_html"],
                cc_emails=email_data["cc"] if email_data["cc"] else None,
                bcc_emails=email_data["bcc"] if email_data["bcc"] else None,
                attachments=attachments,
                logo_path=logo_path,
                signature_name=signature_name,
                zip_attachments=zip_attachments
            )
        except Exception as e:
            return False, f"เกิดข้อผิดพลาดในการส่งอีเมลล์ตามแพทเทิร์น: {str(e)}"
    
    def send_bulk_emails(
        self,
        email_list: List[Dict],
        subject_template: str = "",
        body_template: str = "",
        body_html_template: Optional[str] = None,
        default_cc: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        ส่งอีเมลล์หลายฉบับพร้อมกัน
        
        Args:
            email_list: รายการข้อมูลอีเมลล์ [{"to": "email@example.com", "subject": "...", "body": "...", ...}, ...]
            subject_template: Template สำหรับ subject (ใช้ {key} สำหรับ placeholder)
            body_template: Template สำหรับ body (ใช้ {key} สำหรับ placeholder)
            body_html_template: Template สำหรับ body HTML
            default_cc: รายการอีเมลล์ CC เริ่มต้นสำหรับทุกอีเมลล์
        
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
            
            # รวม CC จาก default และ email_data
            cc_list = default_cc.copy() if default_cc else []
            if email_data.get('cc'):
                cc_list.extend(email_data.get('cc', []))
            cc_list = list(set(cc_list))  # ลบ duplicates
            
            # Send email
            success, message = self.send_email(
                to_emails=[to_email],
                subject=subject,
                body=body,
                body_html=body_html,
                cc_emails=cc_list if cc_list else None,
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


# Global email service instance
_global_email_service: Optional[EmailService] = None


def get_global_email_service() -> Optional[EmailService]:
    """Get global email service instance"""
    return _global_email_service


def set_global_email_service(email_service: EmailService):
    """Set global email service instance"""
    global _global_email_service
    _global_email_service = email_service

