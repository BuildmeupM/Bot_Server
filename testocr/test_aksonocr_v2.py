"""
ทดสอบ AksonOCR API - Upload Model (v2)
ใช้โครงสร้างตามตัวอย่างจากเอกสาร API
"""
import requests
import mimetypes
import json
from pathlib import Path
import sys
import re
from html.parser import HTMLParser

# เพิ่ม path เพื่อ import config
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config

def clean_markdown_text(text):
    """แปลง markdown และ HTML เป็น plain text ที่อ่านง่าย"""
    if not text:
        return ""
    
    # แยก HTML tables ออกมาก่อน
    html_table_pattern = r'<table>.*?</table>'
    tables = re.findall(html_table_pattern, text, re.DOTALL)
    
    # แทนที่ HTML tables ด้วย placeholder
    placeholders = []
    for i, table in enumerate(tables):
        placeholder = f"__TABLE_{i}__"
        placeholders.append(table)
        text = text.replace(table, placeholder)
    
    # ลบ markdown formatting
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # **bold** -> bold
    text = re.sub(r'\*(.*?)\*', r'\1', text)      # *italic* -> italic
    text = re.sub(r'#+\s*(.*)', r'\1', text)      # # heading -> heading
    text = re.sub(r'\[x\]', '✓', text)            # [x] -> ✓
    text = re.sub(r'\[ \]', '☐', text)           # [ ] -> ☐
    text = re.sub(r'\[(.*?)\]', r'\1', text)      # [text] -> text
    text = re.sub(r'---+\n', '\n', text)          # --- -> newline
    text = re.sub(r'==.*?==\n', '', text)         # ==Start/End== -> remove
    
    # ลบ HTML tags ที่เหลือ
    text = re.sub(r'<[^>]+>', '', text)
    
    # แปลง HTML tables เป็น text format
    for i, table_html in enumerate(placeholders):
        # แยก table rows
        rows = re.findall(r'<tr>.*?</tr>', table_html, re.DOTALL)
        table_text = []
        for row in rows:
            cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL)
            # ลบ HTML tags ใน cell
            cleaned_cells = []
            for cell in cells:
                cell = re.sub(r'<[^>]+>', '', cell)
                cell = re.sub(r'\s+', ' ', cell).strip()
                cleaned_cells.append(cell)
            if cleaned_cells:
                # ใช้ช่องว่างแทน | เพื่อให้อ่านง่ายขึ้น
                table_text.append('   '.join(cleaned_cells))
        
        if table_text:
            formatted_table = '\n'.join(table_text)
            text = text.replace(f"__TABLE_{i}__", f"\n{formatted_table}\n")
    
    # ลบ | ที่เหลืออยู่ทั้งหมด
    text = text.replace('|', '')
    
    # ทำความสะอาด whitespace
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if line:
            cleaned_lines.append(line)
        elif cleaned_lines and cleaned_lines[-1]:  # เพิ่มบรรทัดว่างระหว่างย่อหน้า
            cleaned_lines.append('')
    
    return '\n'.join(cleaned_lines)

def test_aksonocr_v2_api():
    """ทดสอบ AksonOCR API ด้วยไฟล์ PDF - Upload Model (v2)"""
    
    # 1. API Configuration
    url = 'https://backend.aksonocr.com/api/v2/upload'
    headers = {'X-API-Key': Config.AKSON_API_KEY}
    
    # 2. ไฟล์ที่ต้องการทดสอบ
    pdf_path = Path(__file__).parent / "9. แบบ ภ.พ.36 เดือน 10.2568 (OpenAi).pdf"
    
    if not pdf_path.exists():
        print(f"❌ ไม่พบไฟล์: {pdf_path}")
        return
    
    print(f"📄 ไฟล์ที่ทดสอบ: {pdf_path.name}")
    print(f"📏 ขนาดไฟล์: {pdf_path.stat().st_size} bytes")
    print(f"🔑 API Key: {Config.AKSON_API_KEY[:10]}...")
    
    # ตรวจสอบ magic bytes เพื่อยืนยันว่าเป็น PDF จริงๆ
    try:
        with open(pdf_path, "rb") as check_file:
            magic_bytes = check_file.read(4)
            is_pdf = magic_bytes.startswith(b'%PDF')
            print(f"🔍 Magic Bytes: {magic_bytes.hex()} ({magic_bytes})")
            print(f"🔍 Is PDF: {is_pdf}")
            if not is_pdf:
                print("⚠️ ไฟล์ไม่ใช่ PDF จริงๆ (magic bytes ไม่ตรงกับ %PDF)")
    except Exception as e:
        print(f"⚠️ ไม่สามารถตรวจสอบ magic bytes ได้: {e}")
    
    print("-" * 70)
    
    # 3. หา mime type ของไฟล์
    mime_type = mimetypes.guess_type(str(pdf_path))[0] or 'application/pdf'
    print(f"📋 MIME Type: {mime_type}")
    print("-" * 70)
    
    # 4. Prepare data
    data = {'model': 'aksonocr-1.0'}
    
    try:
        print("📤 กำลังส่งไฟล์ไปยัง AksonOCR API...")
        
        # เปิดไฟล์และส่ง request
        with open(pdf_path, 'rb') as file:
            files = {'file': (pdf_path.name, file, mime_type)}
            
            response = requests.post(url, headers=headers, files=files, data=data, timeout=60)
            
            print(f"📥 Status Code: {response.status_code}")
            print("-" * 70)
            
            if response.status_code in [200, 201]:
                result = response.json()
                print("✅ สำเร็จ!")
                print(f"📋 Response Structure: {list(result.keys())}")
                print("-" * 70)
                
                # แสดงผลลัพธ์
                print("📄 ผลลัพธ์ที่ได้จากไฟล์ PDF:")
                print("=" * 70)
                
                # ตรวจสอบโครงสร้าง response
                if 'pages' in result:
                    print(f"\n📄 จำนวนหน้า: {len(result['pages'])}")
                    print("-" * 70)
                    
                    for page in result['pages']:
                        page_index = page.get('index', 0) + 1
                        print(f"\n📄 Page {page_index}:")
                        print("-" * 70)
                        
                        # แสดง markdown ที่แปลงเป็น plain text แล้ว
                        if 'markdown' in page:
                            markdown = page['markdown']
                            cleaned_text = clean_markdown_text(markdown)
                            print("📝 เนื้อหาที่อ่านได้:")
                            print("=" * 70)
                            print(cleaned_text)
                            print("=" * 70)
                            print(f"\n📏 ความยาว: {len(cleaned_text)} ตัวอักษร")
                        
                        # แสดง text ถ้ามี (ถ้าไม่มี markdown)
                        elif 'text' in page:
                            text = page['text']
                            cleaned_text = clean_markdown_text(text)
                            print("📝 เนื้อหาที่อ่านได้:")
                            print("=" * 70)
                            print(cleaned_text)
                            print("=" * 70)
                            print(f"\n📏 ความยาว: {len(cleaned_text)} ตัวอักษร")
                        
                        # แสดง confidence ถ้ามี
                        if 'confidence' in page:
                            print(f"\n🎯 Confidence: {page['confidence']}%")
                        
                        print("-" * 70)
                else:
                    # แสดงผลลัพธ์ทั้งหมด
                    print(json.dumps(result, indent=2, ensure_ascii=False))
                
            else:
                print("❌ ไม่สำเร็จ!")
                try:
                    error_data = response.json()
                    # แสดง error ทั้งหมดเพื่อ debug
                    print(f"📋 Full Error Response:")
                    print(json.dumps(error_data, indent=2, ensure_ascii=False))
                    
                    # แสดง error code และ message ถ้ามี
                    if 'error' in error_data:
                        if isinstance(error_data['error'], dict):
                            error_code = error_data['error'].get('code', 'UNKNOWN')
                            error_msg = error_data['error'].get('message', 'Unknown error')
                            print(f"📋 Error: [{error_code}] {error_msg}")
                        else:
                            print(f"📋 Error: {error_data['error']}")
                    elif 'code' in error_data:
                        print(f"📋 Error Code: {error_data['code']}")
                except Exception as e:
                    print(f"📋 Error Text: {response.text[:500]}")
                    print(f"📋 Parse Error: {e}")
                    
    except requests.exceptions.RequestException as e:
        print(f"❌ Network Error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 70)
    print("🧪 ทดสอบ AksonOCR API - Upload Model (v2)")
    print("=" * 70)
    test_aksonocr_v2_api()
    print("=" * 70)
