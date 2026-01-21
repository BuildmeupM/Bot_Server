"""
BotV3 - ระบบส่งอีเมลล์อัตโนมัติ
หน้า Streamlit สำหรับจัดการการส่งอีเมลล์
"""

import streamlit as st
from pathlib import Path
from datetime import datetime
import sys
import os
from typing import List, Optional
import pandas as pd

# เพิ่ม current directory เข้า sys.path
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

if current_dir and str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Import modules
try:
    from config import Config
    from email_manager import EmailManager, get_global_email_manager, set_global_email_manager
except ImportError as e:
    st.error(f"❌ ไม่สามารถ import โมดูลได้: {e}")
    st.stop()

# ตั้งค่า page config
st.set_page_config(
    page_title="BotV3 - ระบบส่งอีเมลล์อัตโนมัติ",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #3498db 0%, #2980b9 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
    }
    .email-card {
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
        max-height: 400px;
        overflow-y: auto;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    """Initialize session state variables"""
    if 'email_logs' not in st.session_state:
        st.session_state.email_logs = []
    if 'email_manager' not in st.session_state:
        st.session_state.email_manager = None
    if 'smtp_configured' not in st.session_state:
        st.session_state.smtp_configured = False

def add_email_log(message: str, level: str = "info"):
    """เพิ่ม log message"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = {
        'timestamp': timestamp,
        'message': message,
        'level': level
    }
    st.session_state.email_logs.append(log_entry)
    if len(st.session_state.email_logs) > 500:
        st.session_state.email_logs = st.session_state.email_logs[-500:]

def display_email_logs():
    """แสดง logs"""
    log_html = "<div class='log-container'>"
    for log in st.session_state.email_logs[-50:]:
        color = "#00ff00" if log['level'] == "success" else \
                "#ff0000" if log['level'] == "error" else \
                "#ffaa00" if log['level'] == "warning" else "#00aaff"
        log_html += f"<div style='color: {color}'>[{log['timestamp']}] {log['message']}</div>"
    log_html += "</div>"
    st.markdown(log_html, unsafe_allow_html=True)

def main():
    """Main Email App"""
    init_session_state()
    
    st.markdown("""
        <div class='main-header'>
            <h1>📧 BotV3 - ระบบส่งอีเมลล์อัตโนมัติ</h1>
        </div>
    """, unsafe_allow_html=True)
    
    # Sidebar - การตั้งค่า SMTP
    with st.sidebar:
        st.header("⚙️ ตั้งค่า SMTP")
        
        with st.form("smtp_config_form", clear_on_submit=False):
            st.subheader("🔧 ข้อมูล SMTP Server")
            
            smtp_server = st.text_input(
                "SMTP Server",
                value=getattr(Config, 'SMTP_SERVER', ''),
                placeholder="เช่น smtp.gmail.com, smtp.outlook.com",
                help="SMTP server address"
            )
            
            smtp_port = st.number_input(
                "SMTP Port",
                min_value=1,
                max_value=65535,
                value=getattr(Config, 'SMTP_PORT', 587),
                help="587 สำหรับ TLS, 465 สำหรับ SSL"
            )
            
            smtp_use_tls = st.checkbox(
                "ใช้ TLS",
                value=getattr(Config, 'SMTP_USE_TLS', True),
                help="เลือกถ้าใช้ TLS (587), ยกเลิกถ้าใช้ SSL (465)"
            )
            
            st.divider()
            st.subheader("🔐 ข้อมูลการยืนยันตัวตน")
            
            smtp_username = st.text_input(
                "อีเมลล์ผู้ส่ง (Username)",
                value=getattr(Config, 'SMTP_USERNAME', ''),
                placeholder="your-email@gmail.com",
                help="อีเมลล์ที่ใช้ส่ง"
            )
            
            smtp_password = st.text_input(
                "รหัสผ่าน (Password)",
                type="password",
                value="",
                placeholder="รหัสผ่านหรือ App Password",
                help="สำหรับ Gmail ต้องใช้ App Password"
            )
            
            email_from = st.text_input(
                "อีเมลล์ผู้ส่ง (From)",
                value=getattr(Config, 'EMAIL_FROM', '') or smtp_username,
                placeholder="your-email@gmail.com",
                help="ถ้าไม่ระบุจะใช้ Username"
            )
            
            save_config = st.form_submit_button("💾 บันทึกการตั้งค่า", use_container_width=True, type="primary")
            
            if save_config:
                if not smtp_server or not smtp_username:
                    st.error("กรุณากรอก SMTP Server และ Username")
                else:
                    try:
                        # สร้าง EmailManager
                        email_manager = EmailManager(
                            smtp_server=smtp_server,
                            smtp_port=int(smtp_port),
                            smtp_use_tls=smtp_use_tls,
                            smtp_username=smtp_username,
                            smtp_password=smtp_password,
                            email_from=email_from or smtp_username
                        )
                        
                        # ทดสอบการเชื่อมต่อ
                        with st.spinner("กำลังทดสอบการเชื่อมต่อ..."):
                            success, message = email_manager.test_connection()
                        
                        if success:
                            st.session_state.email_manager = email_manager
                            st.session_state.smtp_configured = True
                            set_global_email_manager(email_manager)
                            st.success("✅ บันทึกการตั้งค่าและทดสอบการเชื่อมต่อสำเร็จ")
                            add_email_log("✅ บันทึกการตั้งค่า SMTP สำเร็จ", "success")
                            st.rerun()
                        else:
                            st.error(f"❌ ทดสอบการเชื่อมต่อล้มเหลว: {message}")
                            add_email_log(f"❌ ทดสอบการเชื่อมต่อล้มเหลว: {message}", "error")
                    except Exception as e:
                        st.error(f"❌ เกิดข้อผิดพลาด: {e}")
                        add_email_log(f"❌ เกิดข้อผิดพลาด: {e}", "error")
        
        # แสดงสถานะการตั้งค่า
        st.divider()
        if st.session_state.smtp_configured and st.session_state.email_manager:
            st.success("✅ SMTP ตั้งค่าแล้ว")
            if st.button("🔄 ทดสอบการเชื่อมต่ออีกครั้ง", use_container_width=True):
                with st.spinner("กำลังทดสอบ..."):
                    success, message = st.session_state.email_manager.test_connection()
                if success:
                    st.success("✅ เชื่อมต่อสำเร็จ")
                    add_email_log("✅ ทดสอบการเชื่อมต่อสำเร็จ", "success")
                else:
                    st.error(f"❌ {message}")
                    add_email_log(f"❌ ทดสอบการเชื่อมต่อล้มเหลว: {message}", "error")
        else:
            st.warning("⚠️ ยังไม่ได้ตั้งค่า SMTP")
    
    # Main content
    if not st.session_state.smtp_configured or not st.session_state.email_manager:
        st.info("📋 กรุณาตั้งค่า SMTP ในแถบด้านข้างก่อนใช้งาน")
        st.markdown("""
        ### 📖 วิธีตั้งค่า SMTP
        
        #### สำหรับ Gmail:
        1. เปิดใช้งาน 2-Step Verification
        2. สร้าง App Password จาก Google Account Settings
        3. ใช้ App Password แทนรหัสผ่านปกติ
        4. SMTP Server: `smtp.gmail.com`
        5. Port: `587` (TLS) หรือ `465` (SSL)
        
        #### สำหรับ Outlook/Hotmail:
        1. SMTP Server: `smtp-mail.outlook.com`
        2. Port: `587` (TLS)
        3. ใช้รหัสผ่านปกติ
        
        #### สำหรับ SMTP อื่นๆ:
        - ตรวจสอบข้อมูล SMTP จากผู้ให้บริการอีเมลล์ของคุณ
        """)
    else:
        # Tab สำหรับการส่งอีเมลล์
        tab1, tab2, tab3 = st.tabs(["📧 ส่งอีเมลล์", "📋 ส่งหลายฉบับ", "📊 ประวัติการส่ง"])
        
        with tab1:
            st.subheader("📧 ส่งอีเมลล์เดี่ยว")
            
            with st.form("send_single_email_form", clear_on_submit=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    to_emails_input = st.text_area(
                        "อีเมลล์ผู้รับ (To)",
                        placeholder="email1@example.com\nemail2@example.com",
                        help="ใส่ทีละบรรทัดสำหรับหลายอีเมลล์",
                        height=100
                    )
                    
                    cc_emails_input = st.text_area(
                        "อีเมลล์ CC",
                        placeholder="cc1@example.com\ncc2@example.com",
                        help="ใส่ทีละบรรทัดสำหรับหลายอีเมลล์",
                        height=80
                    )
                    
                    bcc_emails_input = st.text_area(
                        "อีเมลล์ BCC",
                        placeholder="bcc1@example.com",
                        help="ใส่ทีละบรรทัดสำหรับหลายอีเมลล์",
                        height=80
                    )
                
                with col2:
                    subject = st.text_input("หัวข้ออีเมลล์ (Subject)", placeholder="หัวข้ออีเมลล์")
                    
                    email_type = st.radio(
                        "ประเภทเนื้อหา",
                        ["Text", "HTML"],
                        help="เลือก Text สำหรับข้อความธรรมดา หรือ HTML สำหรับรูปแบบ HTML"
                    )
                    
                    if email_type == "HTML":
                        body_html = st.text_area(
                            "เนื้อหาอีเมลล์ (HTML)",
                            placeholder="<h1>หัวข้อ</h1><p>เนื้อหา...</p>",
                            height=200
                        )
                        body = ""
                    else:
                        body = st.text_area(
                            "เนื้อหาอีเมลล์ (Text)",
                            placeholder="เนื้อหาอีเมลล์...",
                            height=200
                        )
                        body_html = None
                    
                    attachments = st.file_uploader(
                        "ไฟล์แนบ",
                        accept_multiple_files=True,
                        help="เลือกไฟล์ที่ต้องการแนบ"
                    )
                
                send_button = st.form_submit_button("📤 ส่งอีเมลล์", use_container_width=True, type="primary")
                
                if send_button:
                    if not to_emails_input or not subject:
                        st.error("กรุณากรอกอีเมลล์ผู้รับและหัวข้ออีเมลล์")
                    else:
                        # แปลงอีเมลล์เป็น list
                        to_emails = [e.strip() for e in to_emails_input.split('\n') if e.strip()]
                        cc_emails = [e.strip() for e in cc_emails_input.split('\n') if e.strip()] if cc_emails_input else None
                        bcc_emails = [e.strip() for e in bcc_emails_input.split('\n') if e.strip()] if bcc_emails_input else None
                        
                        # จัดการไฟล์แนบ
                        attachment_paths = []
                        if attachments:
                            temp_dir = Path("temp_uploads")
                            temp_dir.mkdir(exist_ok=True)
                            for attachment in attachments:
                                file_path = temp_dir / attachment.name
                                with open(file_path, "wb") as f:
                                    f.write(attachment.getbuffer())
                                attachment_paths.append(file_path)
                        
                        # ส่งอีเมลล์
                        with st.spinner("กำลังส่งอีเมลล์..."):
                            success, message = st.session_state.email_manager.send_email(
                                to_emails=to_emails,
                                subject=subject,
                                body=body,
                                body_html=body_html,
                                cc_emails=cc_emails,
                                bcc_emails=bcc_emails,
                                attachments=attachment_paths if attachment_paths else None
                            )
                        
                        if success:
                            st.success(f"✅ {message}")
                            add_email_log(f"✅ ส่งอีเมลล์สำเร็จ: {subject} ไปยัง {len(to_emails)} รายการ", "success")
                            
                            # ลบไฟล์ชั่วคราว
                            for file_path in attachment_paths:
                                try:
                                    file_path.unlink()
                                except:
                                    pass
                        else:
                            st.error(f"❌ {message}")
                            add_email_log(f"❌ ส่งอีเมลล์ล้มเหลว: {message}", "error")
        
        with tab2:
            st.subheader("📋 ส่งอีเมลล์หลายฉบับ")
            st.info("💡 อัปโหลดไฟล์ CSV ที่มีคอลัมน์: to, subject, body (หรือ body_html)")
            
            uploaded_file = st.file_uploader(
                "อัปโหลดไฟล์ CSV",
                type=['csv'],
                help="CSV ต้องมีคอลัมน์: to, subject, body (หรือ body_html)"
            )
            
            if uploaded_file:
                try:
                    df = pd.read_csv(uploaded_file)
                    st.dataframe(df.head(10), use_container_width=True)
                    
                    required_columns = ['to', 'subject']
                    missing_columns = [col for col in required_columns if col not in df.columns]
                    
                    if missing_columns:
                        st.error(f"❌ ไฟล์ CSV ขาดคอลัมน์: {', '.join(missing_columns)}")
                    else:
                        if st.button("📤 ส่งอีเมลล์ทั้งหมด", use_container_width=True, type="primary"):
                            email_list = []
                            for _, row in df.iterrows():
                                email_data = {
                                    'to': str(row['to']),
                                    'subject': str(row['subject']),
                                    'body': str(row.get('body', '')),
                                    'body_html': str(row.get('body_html', '')) if 'body_html' in row else None
                                }
                                if 'cc' in row:
                                    email_data['cc'] = [str(row['cc'])]
                                if 'bcc' in row:
                                    email_data['bcc'] = [str(row['bcc'])]
                                email_list.append(email_data)
                            
                            with st.spinner(f"กำลังส่งอีเมลล์ {len(email_list)} ฉบับ..."):
                                results = st.session_state.email_manager.send_bulk_emails(email_list)
                            
                            # แสดงผลลัพธ์
                            st.success(f"✅ ส่งสำเร็จ {results['success']}/{results['total']} ฉบับ")
                            st.error(f"❌ ล้มเหลว {results['failed']}/{results['total']} ฉบับ")
                            
                            # แสดงตารางผลลัพธ์
                            results_df = pd.DataFrame(results['results'])
                            st.dataframe(results_df, use_container_width=True)
                            
                            add_email_log(
                                f"📋 ส่งอีเมลล์หลายฉบับ: สำเร็จ {results['success']}/{results['total']}",
                                "success" if results['failed'] == 0 else "warning"
                            )
                except Exception as e:
                    st.error(f"❌ เกิดข้อผิดพลาดในการอ่านไฟล์: {e}")
                    add_email_log(f"❌ เกิดข้อผิดพลาด: {e}", "error")
        
        with tab3:
            st.subheader("📊 ประวัติการส่ง")
            
            if st.session_state.email_logs:
                display_email_logs()
            else:
                st.info("ยังไม่มีประวัติการส่ง")
            
            if st.button("🧹 ล้างประวัติ", use_container_width=True):
                st.session_state.email_logs = []
                st.rerun()

if __name__ == "__main__":
    main()

