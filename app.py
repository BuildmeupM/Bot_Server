"""
BotV3 - Main Streamlit Application
ไฟล์หลักสำหรับรัน Streamlit Multi-Page App
"""

import streamlit as st
from pathlib import Path
import sys
import os

# เพิ่ม current directory เข้า sys.path
try:
    script_path = Path(__file__)
    if script_path.exists():
        current_dir = script_path.parent.resolve()
    else:
        current_dir = Path(os.path.abspath(__file__)).parent
except Exception:
    try:
        current_dir = Path(os.getcwd())
    except Exception:
        current_dir = Path.cwd()

if current_dir and str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# ตั้งค่า page config
st.set_page_config(
    page_title="BotV3 - ระบบอัตโนมัติ",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS สำหรับหน้าแรก
st.markdown("""
    <style>
    /* ซ่อน search bar "app" ใน sidebar - หลายวิธีเพื่อให้แน่ใจ */
    /* วิธีที่ 1: ซ่อน input search */
    div[data-testid="stSidebar"] input[placeholder*="app"],
    div[data-testid="stSidebar"] input[placeholder*="App"],
    div[data-testid="stSidebar"] input[type="search"],
    div[data-testid="stSidebar"] input[aria-label*="app"],
    div[data-testid="stSidebar"] input[aria-label*="App"] {
        display: none !important;
    }
    /* วิธีที่ 2: ซ่อน container ของ search */
    div[data-testid="stSidebar"] > div:first-child > div:first-child,
    div[data-testid="stSidebar"] > div:first-child > div:first-child > div:first-child {
        display: none !important;
    }
    /* วิธีที่ 3: ซ่อน element ที่มี text "app" */
    div[data-testid="stSidebar"] label:has-text("app"),
    div[data-testid="stSidebar"] label:has-text("App") {
        display: none !important;
    }
    
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 30px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 40px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .feature-card {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #bae6fd;
        margin: 15px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: transform 0.2s;
        cursor: pointer;
    }
    .feature-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
        border-color: #60a5fa;
    }
    .feature-card h2 {
        color: #1f2937;
        font-size: 1.5em;
        margin-bottom: 10px;
        font-weight: bold;
    }
    .feature-card p {
        color: #4b5563;
        font-size: 1em;
        margin-bottom: 15px;
    }
    .feature-card ul {
        color: #374151;
        font-size: 0.95em;
        line-height: 1.8;
        margin: 10px 0;
        padding-left: 20px;
    }
    .feature-card li {
        color: #374151;
        margin-bottom: 8px;
    }
    .nav-button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px 30px;
        border-radius: 8px;
        text-decoration: none;
        display: inline-block;
        margin: 10px 5px;
        transition: all 0.3s;
    }
    .nav-button:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    </style>
    <script>
    // ซ่อน search bar "app" ใน sidebar หลังจาก page โหลดเสร็จ
    window.addEventListener('load', function() {
        setTimeout(function() {
            // หา sidebar
            const sidebar = document.querySelector('div[data-testid="stSidebar"]');
            if (sidebar) {
                // หา input search ทั้งหมดใน sidebar
                const searchInputs = sidebar.querySelectorAll('input[type="search"], input[placeholder*="app"], input[placeholder*="App"]');
                searchInputs.forEach(function(input) {
                    // ซ่อน input และ parent container
                    const container = input.closest('div');
                    if (container) {
                        container.style.display = 'none';
                    }
                    input.style.display = 'none';
                });
                
                // ซ่อน element แรกใน sidebar (มักจะเป็น search bar)
                const firstChild = sidebar.querySelector('div:first-child > div:first-child');
                if (firstChild && firstChild.querySelector('input')) {
                    firstChild.style.display = 'none';
                }
            }
        }, 100);
    });
    
    // ไม่ต้องใช้ JavaScript สำหรับ card click แล้ว เพราะใช้ HTML link โดยตรง
    </script>
""", unsafe_allow_html=True)

def main():
    """Main Home Page"""
    
    st.markdown("""
        <div class='main-header'>
            <h1>🤖 BotV3 - ระบบอัตโนมัติ</h1>
            <p style='font-size: 1.2em; margin-top: 10px;'>ระบบจัดการและประมวลผลเอกสารอัตโนมัติ</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.info("""
    📌 **ยินดีต้อนรับสู่ BotV3!**
    
    ระบบนี้ประกอบด้วยหลายส่วนงานที่สามารถใช้งานได้ผ่านเมนูด้านข้าง:
    - 🤖 **ประมวลผล PDF**: ระบบประมวลผลและบันทึกเอกสาร PDF อัตโนมัติ
    - 📧 **ส่งอีเมลล์**: ระบบส่งอีเมลล์อัตโนมัติ
    """)
    
    # แสดงฟีเจอร์หลัก
    col1, col2 = st.columns(2)
    
    with col1:
        # Card สำหรับประมวลผล PDF - ใช้ HTML link โดยตรง
        with st.container():
            st.markdown("""
                <a href="/ประมวลผล_PDF?page=pages/1_🤖_ประมวลผล_PDF.py" target="_self" style="text-decoration: none; color: inherit; display: block;">
                    <div class='feature-card' id='pdf-card' style="cursor: pointer;">
                        <h2>🤖 ประมวลผล PDF</h2>
                        <p>ระบบประมวลผลและบันทึกเอกสาร PDF อัตโนมัติ</p>
                    </div>
                </a>
            """, unsafe_allow_html=True)
            
            st.markdown("""
                - **สแกนและประมวลผล PDF อัตโนมัติ** - ระบบจะสแกนและประมวลผลไฟล์ PDF โดยอัตโนมัติ
                - **จัดกลุ่มตามประเภทภาษี (VAT/NoneVat)** - แยกเอกสารตามประเภทภาษีมูลค่าเพิ่ม
                - **บันทึกลงระบบ PeakEngine** - บันทึกข้อมูลลงระบบ PeakEngine อัตโนมัติ
                - **ติดตามสถานะการประมวลผลแบบเรียลไทม์** - ดูสถานะการทำงานแบบเรียลไทม์
            """)
            
            # ใช้ HTML link แทนปุ่มเพื่อให้ navigate ได้จริง
            st.markdown("""
                <a href="/ประมวลผล_PDF?page=pages/1_🤖_ประมวลผล_PDF.py" target="_self" style="text-decoration: none;">
                    <button style="
                        width: 100%;
                        padding: 12px 24px;
                        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        border: none;
                        border-radius: 8px;
                        font-size: 16px;
                        font-weight: bold;
                        cursor: pointer;
                        transition: all 0.3s;
                        margin-top: 10px;
                    " onmouseover="this.style.transform='scale(1.02)'; this.style.boxShadow='0 4px 8px rgba(0,0,0,0.2)';" 
                       onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='none';">
                        📂 ไปยังหน้าประมวลผล PDF
                    </button>
                </a>
            """, unsafe_allow_html=True)
    
    with col2:
        # Card สำหรับส่งอีเมลล์ - ใช้ HTML link โดยตรง
        with st.container():
            st.markdown("""
                <a href="/ส่งอีเมลล์?page=pages/2_📧_ส่งอีเมลล์.py" target="_self" style="text-decoration: none; color: inherit; display: block;">
                    <div class='feature-card' id='email-card' style="cursor: pointer;">
                        <h2>📧 ส่งอีเมลล์</h2>
                        <p>ระบบส่งอีเมลล์อัตโนมัติ</p>
                    </div>
                </a>
            """, unsafe_allow_html=True)
            
            st.markdown("""
                - **ส่งอีเมลล์เดี่ยวหรือหลายฉบับ** - ส่งอีเมลล์ได้ทั้งแบบเดี่ยวและแบบหลายฉบับพร้อมกัน
                - **รองรับไฟล์แนบ** - สามารถแนบไฟล์ไปกับอีเมลล์ได้
                - **ส่งแบบ HTML หรือ Text** - รองรับการส่งทั้งแบบ HTML และข้อความธรรมดา
                - **ประวัติการส่งอีเมลล์** - ดูประวัติการส่งอีเมลล์ทั้งหมด
            """)
            
            # ใช้ HTML link แทนปุ่มเพื่อให้ navigate ได้จริง
            st.markdown("""
                <a href="/ส่งอีเมลล์?page=pages/2_📧_ส่งอีเมลล์.py" target="_self" style="text-decoration: none;">
                    <button style="
                        width: 100%;
                        padding: 12px 24px;
                        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        border: none;
                        border-radius: 8px;
                        font-size: 16px;
                        font-weight: bold;
                        cursor: pointer;
                        transition: all 0.3s;
                        margin-top: 10px;
                    " onmouseover="this.style.transform='scale(1.02)'; this.style.boxShadow='0 4px 8px rgba(0,0,0,0.2)';" 
                       onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='none';">
                        📧 ไปยังหน้าส่งอีเมลล์
                    </button>
                </a>
            """, unsafe_allow_html=True)
    
    st.divider()
    
    st.markdown("### 📖 วิธีใช้งาน")
    st.markdown("""
    1. **เลือกหน้าที่ต้องการ** จากเมนูด้านข้าง (Sidebar)
    2. **ประมวลผล PDF**: 
       - วาง path โฟลเดอร์ที่ต้องการประมวลผล
       - กด "เพิ่มงาน" เพื่อเริ่มประมวลผล
       - ติดตามสถานะได้จากหน้าจอ
    3. **ส่งอีเมลล์**:
       - ตั้งค่า SMTP ในแถบด้านข้าง
       - กรอกข้อมูลอีเมลล์และส่งได้ทันที
    """)
    
    st.divider()
    
    st.markdown("### 🔧 หมายเหตุ")
    st.warning("""
    - ระบบนี้ต้องเชื่อมต่อกับ network drive (V:) เพื่อเข้าถึงข้อมูล
    - สำหรับการส่งอีเมลล์ ต้องตั้งค่า SMTP ก่อนใช้งาน
    - ใช้เมนูด้านข้างเพื่อสลับระหว่างหน้าต่างๆ
    """)

if __name__ == "__main__":
    main()
