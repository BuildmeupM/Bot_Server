import requests
import json
import re
import mimetypes
import time
from typing import Dict, List, Optional, Any
from html.parser import HTMLParser
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def _clean_key_extract_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    ทำความสะอาดข้อมูลจาก key-extract API (ลบ emoji, whitespace ที่ไม่จำเป็น, null values, และ confidence fields)
    
    Args:
        data: Dictionary ที่มีข้อมูลจาก key-extract API
        
    Returns:
        Dictionary ที่ทำความสะอาดแล้ว (ไม่มี null values และ confidence fields)
    """
    if not isinstance(data, dict):
        return data
    
    cleaned = {}
    
    for key, value in data.items():
        # ลบ fields ที่ลงท้ายด้วย _confidence
        if key.endswith('_confidence'):
            continue
        
        # ลบ null values
        if value is None:
            continue
            
        if isinstance(value, str):
            # ลบ emoji (💰, 🏢, etc.)
            cleaned_value = re.sub(r'[💰🏢📋✅❌⚠️🔍]', '', value)
            # ลบสัญลักษณ์ "฿" (บาท) ออก
            cleaned_value = cleaned_value.replace('฿', '').replace('THB', '').replace('thb', '')
            # ลบ whitespace ที่ไม่จำเป็น (แต่เก็บช่องว่างระหว่างคำ)
            cleaned_value = re.sub(r'\s+', ' ', cleaned_value).strip()
            # ถ้าหลังทำความสะอาดแล้วเป็น empty string ให้ข้าม
            if cleaned_value:
                cleaned[key] = cleaned_value
        elif isinstance(value, list):
            # ถ้าเป็น list ให้ทำความสะอาดแต่ละ item
            cleaned_list = []
            for item in value:
                if isinstance(item, dict):
                    cleaned_item = _clean_key_extract_data(item)
                    if cleaned_item:  # ถ้า dict ไม่ว่าง
                        cleaned_list.append(cleaned_item)
                elif isinstance(item, str):
                    cleaned_item = re.sub(r'[💰🏢📋✅❌⚠️🔍]', '', item)
                    # ลบสัญลักษณ์ "฿" (บาท) ออก
                    cleaned_item = cleaned_item.replace('฿', '').replace('THB', '').replace('thb', '')
                    cleaned_item = re.sub(r'\s+', ' ', cleaned_item).strip()
                    if cleaned_item:  # ถ้า string ไม่ว่าง
                        cleaned_list.append(cleaned_item)
                elif item is not None:  # ข้าม None
                    cleaned_list.append(item)
            if cleaned_list:  # ถ้า list ไม่ว่าง
                cleaned[key] = cleaned_list
        elif isinstance(value, dict):
            # ถ้าเป็น nested dict ให้ทำความสะอาดแบบ recursive
            cleaned_dict = _clean_key_extract_data(value)
            if cleaned_dict:  # ถ้า dict ไม่ว่าง
                cleaned[key] = cleaned_dict
        else:
            # ค่าอื่นๆ (int, float, bool, etc.) เก็บไว้ตามเดิม
            cleaned[key] = value
    
    return cleaned


class HTMLTableParser(HTMLParser):
    """Parse HTML table into structured data"""
    def __init__(self):
        super().__init__()
        self.tables = []
        self.current_table = []
        self.current_row = []
        self.current_cell = ""
        self.in_table = False
        self.in_row = False
        self.in_cell = False
        self.colspan = 1
        self.rowspan = 1
        
    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            self.in_table = True
            self.current_table = []
        elif tag == 'tr':
            self.in_row = True
            self.current_row = []
        elif tag in ['td', 'th']:
            self.in_cell = True
            self.current_cell = ""
            # Check for colspan and rowspan
            self.colspan = 1
            self.rowspan = 1
            for attr, value in attrs:
                if attr == 'colspan':
                    try:
                        self.colspan = int(value)
                    except:
                        self.colspan = 1
                elif attr == 'rowspan':
                    try:
                        self.rowspan = int(value)
                    except:
                        self.rowspan = 1
    
    def handle_endtag(self, tag):
        if tag == 'td' or tag == 'th':
            cell_text = self.current_cell.strip()
            # Add cell with colspan info
            for _ in range(self.colspan):
                self.current_row.append(cell_text)
            self.in_cell = False
        elif tag == 'tr':
            if self.current_row:
                self.current_table.append(self.current_row)
            self.in_row = False
        elif tag == 'table':
            if self.current_table:
                self.tables.append(self.current_table)
            self.in_table = False
    
    def handle_data(self, data):
        if self.in_cell:
            self.current_cell += data


def parse_html_table(html_text: str) -> List[List[List[str]]]:
    """Parse HTML table tags from text and return list of tables"""
    try:
        parser = HTMLTableParser()
        parser.feed(html_text)
        return parser.tables
    except Exception as e:
        # Fallback: use regex to extract table data
        tables = []
        table_pattern = r'<table[^>]*>(.*?)</table>'
        matches = re.findall(table_pattern, html_text, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            rows = []
            row_pattern = r'<tr[^>]*>(.*?)</tr>'
            row_matches = re.findall(row_pattern, match, re.DOTALL | re.IGNORECASE)
            
            for row_match in row_matches:
                cells = []
                cell_pattern = r'<t[dh][^>]*>(.*?)</t[dh]>'
                cell_matches = re.findall(cell_pattern, row_match, re.DOTALL | re.IGNORECASE)
                
                for cell in cell_matches:
                    # Clean HTML tags from cell content
                    cell_text = re.sub(r'<[^>]+>', '', cell)
                    cell_text = cell_text.strip().replace('\n', ' ').replace('\t', ' ')
                    # Clean multiple spaces
                    cell_text = re.sub(r'\s+', ' ', cell_text)
                    cells.append(cell_text)
                
                if cells:
                    rows.append(cells)
            
            if rows:
                tables.append(rows)
        
        return tables


def convert_html_table_to_concatenated_text(html_text: str) -> str:
    """
    แปลง HTML table เป็นข้อความต่อกัน (concatenated) ด้วย pipe (|) สำหรับ ภ.ง.ด.1
    รูปแบบ: cell1 | cell2 | cell3 | cell4
    
    ตัวอย่าง:
    <table><tr><td>สรุปรายการภาษีที่นำส่ง</td><td>จำนวนราย</td></tr></table>
    จะกลายเป็น:
    สรุปรายการภาษีที่นำส่ง | จำนวนราย
    """
    if not html_text:
        return html_text
    
    # หา HTML table ทั้งหมด (รวม tag <table>...</table>)
    table_pattern = r'<table[^>]*>.*?</table>'
    table_matches = re.finditer(table_pattern, html_text, re.DOTALL | re.IGNORECASE)
    
    result_text = html_text
    replacements = []  # เก็บ replacements เพื่อทำทีหลัง (เพื่อไม่ให้ index เปลี่ยน)
    
    for match in table_matches:
        table_html = match.group(0)
        table_start = match.start()
        table_end = match.end()
        
        # Parse table
        try:
            parsed_tables = parse_html_table(table_html)
            if parsed_tables and len(parsed_tables) > 0:
                table = parsed_tables[0]
                
                # แปลง table เป็นข้อความต่อกันด้วย pipe
                formatted_rows = []
                for row in table:
                    # ทำความสะอาด cell content
                    cleaned_cells = []
                    for cell in row:
                        # ลบ HTML tags
                        cell_text = re.sub(r'<[^>]+>', '', str(cell))
                        # ลบช่องว่างส่วนเกิน
                        cell_text = re.sub(r'\s+', ' ', cell_text).strip()
                        cleaned_cells.append(cell_text)
                    
                    # รวม cell ด้วย pipe
                    formatted_row = " | ".join(cleaned_cells)
                    formatted_rows.append(formatted_row)
                
                # แทนที่ HTML table ด้วยข้อความต่อกัน
                formatted_table = "\n".join(formatted_rows)
                replacements.append((table_start, table_end, formatted_table))
        except Exception as e:
            logger.warning(f"⚠️ ไม่สามารถ parse HTML table ได้: {e}")
            continue
    
    # ทำการแทนที่จากท้ายไปหน้า (เพื่อไม่ให้ index เปลี่ยน)
    for table_start, table_end, formatted_table in reversed(replacements):
        result_text = result_text[:table_start] + formatted_table + result_text[table_end:]
    
    return result_text


def format_table(table: List[List[str]], max_width: int = 120) -> str:
    """Format table data into readable text format"""
    if not table:
        return ""
    
    # Find max width for each column
    num_cols = max(len(row) for row in table) if table else 0
    if num_cols == 0:
        return ""
    
    col_widths = [0] * num_cols
    for row in table:
        for i, cell in enumerate(row[:num_cols]):
            cell_text = str(cell).strip()
            # Remove HTML tags if any
            cell_text = re.sub(r'<[^>]+>', '', cell_text)
            col_widths[i] = max(col_widths[i], len(cell_text))
    
    # Limit column width
    total_width = sum(col_widths) + (num_cols - 1) * 3
    if total_width > max_width:
        max_col_width = max_width // num_cols
        col_widths = [min(w, max_col_width) for w in col_widths]
    
    # Format output
    output_lines = []
    for row_idx, row in enumerate(table):
        cells = [str(cell).strip() for cell in row[:num_cols]]
        # Fill missing cells
        while len(cells) < num_cols:
            cells.append("")
        
        # Clean HTML tags
        cells = [re.sub(r'<[^>]+>', '', cell) for cell in cells]
        
        # Format row
        formatted_cells = []
        for i, cell in enumerate(cells):
            if col_widths[i] > 0:
                formatted_cells.append(cell[:col_widths[i]].ljust(col_widths[i]))
            else:
                formatted_cells.append("")
        
        output_lines.append(" | ".join(formatted_cells))
        
        # Add separator after header or section titles
        if row_idx == 0 or any('**' in cell for cell in cells):
            separator = "-" * (sum(col_widths) + (num_cols - 1) * 3)
            output_lines.append(separator)
    
    return "\n".join(output_lines)


def clean_ocr_text(text: str) -> str:
    """
    ทำความสะอาดข้อความที่อ่านได้จาก OCR
    ลบ pipe characters, HTML tags ที่เหลืออยู่
    """
    if not text:
        return ""
    
    cleaned = text
    
    # ลบ HTML tags ที่เหลืออยู่ (เช่น </td></tr>, <tr><td>)
    # ลบ tag ที่เป็นคู่หรือเดี่ยว
    cleaned = re.sub(r'</td></tr>', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'<tr><td>', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'</td>', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'<td>', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'</tr>', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'<tr>', '', cleaned, flags=re.IGNORECASE)
    
    # ลบ pipe characters (|) ที่เหลืออยู่
    cleaned = cleaned.replace('|', ' ')
    
    # ลบ HTML tags ทั้งหมดที่เหลืออยู่
    cleaned = re.sub(r'<[^>]+>', '', cleaned)
    
    # ลบจุดที่ติดกันหลายๆ จุด (เช่น ................)
    cleaned = re.sub(r'\.{3,}', '', cleaned)  # ลบจุด 3 จุดขึ้นไป
    
    # ลบช่องว่างส่วนเกิน (หลายช่องว่างติดกัน)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # ลบช่องว่างที่หัวและท้าย
    cleaned = cleaned.strip()
    
    # ลบช่องว่างที่ขึ้นบรรทัดใหม่หลายบรรทัดติดกัน
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    
    return cleaned


def format_structured_text(text: str, max_line_length: int = 100) -> str:
    """
    จัดรูปแบบข้อความให้อ่านง่ายขึ้น โดยแยกข้อมูลสำคัญเป็นส่วนๆ
    
    Args:
        text: ข้อความที่ต้องการจัดรูปแบบ
        max_line_length: ความยาวสูงสุดของแต่ละบรรทัด (default: 100)
    
    Returns:
        ข้อความที่จัดรูปแบบแล้ว
    """
    if not text:
        return ""
    
    formatted = text
    
    # 0. ป้องกันการแยกตัวเลขผิด (เช่น 154,500.61 ไม่ควรถูกแยก)
    # จัดการยอดเงินก่อนเพื่อป้องกันการแยกผิด
    # Pattern 1: ตัวเลขที่มี comma และทศนิยม 2 ตำแหน่ง (เช่น 154,500.61)
    amount_pattern_comma = r'(\d{1,3}(?:,\d{3})+\.\d{2})'
    formatted = re.sub(amount_pattern_comma, lambda m: f'[AMOUNT_{m.group(1)}]', formatted)
    
    # Pattern 2: ตัวเลขที่ไม่มี comma แต่มีทศนิยม 2 ตำแหน่ง (เช่น 154500.61)
    amount_pattern_no_comma = r'(?<!\d)(\d{4,}\.\d{2})(?!\d)'  # อย่างน้อย 4 หลักก่อนจุดทศนิยม
    formatted = re.sub(amount_pattern_no_comma, lambda m: f'[AMOUNT_{m.group(1)}]', formatted)
    
    # 1. แยกเลขประจำตัวผู้เสียภาษี (13 หลัก) - รองรับทั้งแบบมีและไม่มีช่องว่าง
    # ตรวจสอบว่ามีเลขประจำตัวผู้เสียภาษีอยู่แล้วหรือไม่ (เพื่อป้องกันการซ้ำ)
    has_tax_id = '📋 เลขประจำตัวผู้เสียภาษี:' in formatted
    
    # Pattern 1: แบบมีช่องว่าง (เช่น 0 1 0 5 5 3 1 1 4 4 3 7)
    tax_id_pattern_spaced = r'(\d{1,2}\s+\d{1,2}\s+\d{1,2}\s+\d{1,2}\s+\d{1,2}\s+\d{1,2}\s+\d{1,2}\s+\d{1,2}\s+\d{1,2}\s+\d{1,2}\s+\d{1,2}\s+\d{1,2}\s+\d{1,2})'
    if not has_tax_id:
        formatted = re.sub(tax_id_pattern_spaced, lambda m: f'\n📋 เลขประจำตัวผู้เสียภาษี: {m.group(1).replace(" ", "")}\n', formatted)
    
    # Pattern 2: แบบต่อกัน 13 หลัก (เช่น 0105553114437) - แต่ไม่ใช่ส่วนของยอดเงิน
    tax_id_pattern_continuous = r'(?<!\d)(?<!\[AMOUNT_)(\d{13})(?!\d)(?!\.\d{2})'  # ไม่จับถ้าเป็นส่วนของยอดเงิน
    if not has_tax_id or '📋 เลขประจำตัวผู้เสียภาษี:' not in formatted:
        formatted = re.sub(tax_id_pattern_continuous, lambda m: f'\n📋 เลขประจำตัวผู้เสียภาษี: {m.group(1)}\n', formatted)
    
    # Pattern 3: แบบมีขีดคั่น (เช่น 0-1055-53114-43-7)
    tax_id_pattern_dashed = r'(\d{1}-\d{4}-\d{5}-\d{2}-\d{1})'
    if not has_tax_id or '📋 เลขประจำตัวผู้เสียภาษี:' not in formatted:
        formatted = re.sub(tax_id_pattern_dashed, lambda m: f'\n📋 เลขประจำตัวผู้เสียภาษี: {m.group(1)}\n', formatted)
    
    # 2. แยกชื่อบริษัท (หลัง "ชื่อผู้มีหน้าที่หักภาษี" หรือ "ชื่อ")
    # Pattern ที่มี 2 groups
    company_patterns_2groups = [
        r'(ชื่อผู้มีหน้าที่หักภาษี[^:]*[:：]\s*)([^\n]+)',
        r'(ชื่อ[^:]*[:：]\s*)([^\n]+)',
    ]
    for pattern in company_patterns_2groups:
        formatted = re.sub(pattern, r'\n🏢 \2\n', formatted, flags=re.IGNORECASE)
    
    # Pattern ที่มี 1 group - แต่ต้องไม่ใช่ข้อความที่ยาวเกินไป (อาจเป็นข้อความอื่น)
    company_patterns_1group = [
        r'(บริษัท\s+[^\n]{1,100})',  # จำกัดความยาวไม่เกิน 100 ตัวอักษร
    ]
    for pattern in company_patterns_1group:
        # ตรวจสอบว่ามี 🏢 อยู่แล้วหรือไม่ และไม่ใช่ข้อความที่ยาวเกินไป
        formatted = re.sub(pattern, lambda m: f'\n🏢 {m.group(1)}\n' if '🏢' not in m.group(0) and len(m.group(1)) < 100 else m.group(1), formatted, flags=re.IGNORECASE)
    
    # 3. แยกที่อยู่ (หลัง "ที่อยู่" หรือ "Address")
    address_patterns = [
        r'(ที่อยู่[^:]*[:：]\s*)([^\n]+(?:\n[^\n]+){0,5})',
        r'(Address[^:]*[:：]\s*)([^\n]+(?:\n[^\n]+){0,5})',
    ]
    for pattern in address_patterns:
        formatted = re.sub(pattern, r'\n📍 ที่อยู่:\n\2\n', formatted, flags=re.IGNORECASE)
    
    # 4. แยกยอดเงิน (ตัวเลขที่มีทศนิยม 2 ตำแหน่ง)
    # ไม่เพิ่ม emoji 💰 (ผู้ใช้ไม่ต้องการ)
    # amount_pattern = r'(\d{1,3}(?:,\d{3})*\.\d{2})'
    # formatted = re.sub(amount_pattern, r'💰 \1', formatted)
    
    # 5. แยกวันที่ (รูปแบบไทย) - ป้องกันการจับตัวเลขผิด
    # ไม่จับตัวเลขที่อยู่หลังจุดทศนิยม (เช่น .61)
    date_patterns = [
        r'(พิมพ์\s*ณ\s*วันที่\s+\d{1,2}\s+[^\s]+\s+\d{4})',
        r'(?<!\.)(?<!\d)(\d{1,2}\s+[^\s]+\s+\d{4})(?!\d)',  # ไม่จับถ้ามีจุดทศนิยมก่อนหน้า
    ]
    for pattern in date_patterns:
        formatted = re.sub(pattern, r'\n📅 \1\n', formatted)
    
    # 6. แยกประเภทแบบภาษี - ป้องกันการซ้ำ
    form_patterns = [
        r'(ภ\.ง\.ด\.\d+|ภงด\.\d+|ภงด\d+)',
        r'(ภ\.พ\.\d+|ภพ\.\d+|ภพ\d+)',
        r'(ภ\.ธ\.\d+|ภธ\.\d+|ภธ\d+)',
    ]
    for pattern in form_patterns:
        # ตรวจสอบว่ามี "📄 ประเภทแบบภาษี:" อยู่แล้วหรือไม่
        formatted = re.sub(pattern, lambda m: f'\n📄 ประเภทแบบภาษี: {m.group(1)}\n' if '📄 ประเภทแบบภาษี:' not in formatted[:formatted.find(m.group(0))+100] else m.group(1), formatted)
    
    # 7. แยกตารางสรุป (หลัง "สรุปรายการ" หรือ "สรุป")
    summary_patterns = [
        r'(สรุปรายการ[^\n]+)',
        r'(สรุป[^\n]+)',
    ]
    for pattern in summary_patterns:
        formatted = re.sub(pattern, r'\n📊 \1\n', formatted)
    
    # 8. แยกเดือน/ปี (หลัง "เดือนที่" หรือ "พ.ศ.")
    period_patterns = [
        r'(เดือนที่[^\n]+)',
        r'(พ\.ศ\.\s*\d{4})',
    ]
    for pattern in period_patterns:
        formatted = re.sub(pattern, r'\n📆 \1\n', formatted)
    
    # 9. แบ่งบรรทัดที่ยาวเกินไป (word wrap)
    lines = formatted.split('\n')
    wrapped_lines = []
    for line in lines:
        if len(line) > max_line_length:
            # แบ่งบรรทัดที่ยาวเกินไป
            words = line.split(' ')
            current_line = ''
            for word in words:
                if len(current_line + word) > max_line_length:
                    if current_line:
                        wrapped_lines.append(current_line.strip())
                    current_line = word + ' '
                else:
                    current_line += word + ' '
            if current_line:
                wrapped_lines.append(current_line.strip())
        else:
            wrapped_lines.append(line)
    
    formatted = '\n'.join(wrapped_lines)
    
    # 10. ลบบรรทัดว่างที่มากเกินไป
    formatted = re.sub(r'\n{3,}', '\n\n', formatted)
    
    # 11. เพิ่ม separator สำหรับส่วนสำคัญ
    formatted = re.sub(r'\n(📋|🏢|📍|💰|📅|📄|📊|📆)', r'\n\n\1', formatted)
    
    # 12. ไม่ลบ emoji 💰 ออกแล้ว (ผู้ใช้ต้องการให้แสดงยอดเงิน)
    # formatted = re.sub(r'💰\s*', '', formatted)
    
    # 13. ลบ emoji ที่ซ้ำกัน (เช่น 🏢 🏢 -> 🏢)
    formatted = re.sub(r'(🏢\s*){2,}', '🏢 ', formatted)
    formatted = re.sub(r'(📋\s*){2,}', '📋 ', formatted)
    formatted = re.sub(r'(📍\s*){2,}', '📍 ', formatted)
    formatted = re.sub(r'(📅\s*){2,}', '📅 ', formatted)
    formatted = re.sub(r'(📄\s*){2,}', '📄 ', formatted)
    formatted = re.sub(r'(📊\s*){2,}', '📊 ', formatted)
    formatted = re.sub(r'(📆\s*){2,}', '📆 ', formatted)
    
    # 14. ลบ emoji ที่อยู่ผิดที่ (เช่น emoji ที่อยู่ท้ายบรรทัดโดยไม่มีข้อความ)
    formatted = re.sub(r'\s+[🏢📋📍📅📄📊📆]+\s*$', '', formatted, flags=re.MULTILINE)
    
    # 15. ลบ emoji ที่อยู่ติดกันโดยไม่มีข้อความระหว่าง (เช่น 🏢🏢 -> 🏢)
    formatted = re.sub(r'([🏢📋📍📅📄📊📆])\s*\1+', r'\1', formatted)
    
    # 16. ลบ pattern ที่ซ้ำกัน (เช่น "📄 ประเภทแบบภาษี:" หรือ "📋 เลขประจำตัวผู้เสียภาษี:" ซ้ำหลายครั้ง)
    # เก็บเฉพาะครั้งแรกที่พบ
    seen_patterns = {}
    lines = formatted.split('\n')
    cleaned_lines = []
    for line in lines:
        # ตรวจสอบ pattern ที่ซ้ำ
        if re.match(r'^📄\s*ประเภทแบบภาษี:\s*', line):
            if 'tax_form_type' not in seen_patterns:
                cleaned_lines.append(line)
                seen_patterns['tax_form_type'] = True
            # ข้าม pattern ที่ซ้ำ
        elif re.match(r'^📅\s*\d{1,2}\s+', line):
            if 'date' not in seen_patterns:
                cleaned_lines.append(line)
                seen_patterns['date'] = True
            # ข้าม pattern ที่ซ้ำ
        elif re.match(r'^📋\s*เลขประจำตัวผู้เสียภาษี:\s*$', line):
            # บรรทัดที่มีแค่ label โดยไม่มีค่า (ซ้ำกัน) - ข้ามทั้งหมด
            # ไม่ต้องเพิ่มบรรทัดว่างนี้
            pass
        elif re.match(r'^📋\s*เลขประจำตัวผู้เสียภาษี:\s*.+', line):
            # บรรทัดที่มี label และค่า - เก็บเฉพาะครั้งแรก
            if 'tax_id_with_value' not in seen_patterns:
                cleaned_lines.append(line)
                seen_patterns['tax_id_with_value'] = True
            # ข้าม pattern ที่ซ้ำ
        else:
            cleaned_lines.append(line)
    
    formatted = '\n'.join(cleaned_lines)
    
    # 17. คืนค่ายอดเงินที่ถูกแทนที่ไว้ และเพิ่ม label
    # จับยอดเงินและเพิ่ม label "💰 ยอดชำระ:"
    formatted = re.sub(r'\[AMOUNT_([^\]]+)\]', r'\n💰 ยอดชำระ: \1\n', formatted)
    
    # จับยอดเงินที่ยังไม่ได้ label (กรณีที่ไม่ได้ถูกแทนที่ไว้ก่อนหน้า)
    # Pattern 1: ตัวเลขที่มี comma และทศนิยม 2 ตำแหน่ง (เช่น 154,500.61)
    amount_pattern_final = r'(?<!💰\sยอดชำระ:\s)(\d{1,3}(?:,\d{3})+\.\d{2})(?!\d)'
    formatted = re.sub(amount_pattern_final, r'\n💰 ยอดชำระ: \1\n', formatted)
    
    # Pattern 2: ตัวเลขที่ไม่มี comma แต่มีทศนิยม 2 ตำแหน่ง (เช่น 154500.61)
    amount_pattern_final_no_comma = r'(?<!💰\sยอดชำระ:\s)(?<!\d)(\d{4,}\.\d{2})(?!\d)'
    formatted = re.sub(amount_pattern_final_no_comma, r'\n💰 ยอดชำระ: \1\n', formatted)
    
    # 18. ลบ emoji ที่อยู่ผิดที่ (เช่น emoji ที่อยู่ท้ายตัวเลขโดยไม่มีข้อความ)
    # ลบ emoji ที่อยู่หลังตัวเลขทันที (เช่น 154,500.61 🏢)
    formatted = re.sub(r'(\d{1,3}(?:,\d{3})*\.\d{2})\s*([🏢📋📍📅📄📊📆])', r'\1', formatted)
    
    # 19. ลบ emoji ที่อยู่ตามลำพังในบรรทัด (เช่น "📅 61" หรือ "🏢 6116")
    formatted = re.sub(r'^([🏢📋📍📅📄📊📆])\s*\d+\s*$', '', formatted, flags=re.MULTILINE)
    
    # 20. ลบบรรทัดว่างที่มากเกินไปอีกครั้ง
    formatted = re.sub(r'\n{3,}', '\n\n', formatted)
    
    return formatted.strip()


def format_text_output(text: str) -> str:
    """Format text output to be more readable"""
    if not text:
        return ""
    
    formatted = text
    
    # Extract and format HTML tables
    table_pattern = r'<table[^>]*>.*?</table>'
    tables = re.findall(table_pattern, formatted, re.DOTALL | re.IGNORECASE)
    
    for table_html in tables:
        # Parse table
        parsed_tables = parse_html_table(table_html)
        if parsed_tables:
            # Format first table found
            formatted_table = format_table(parsed_tables[0])
            if formatted_table:
                # Replace HTML table with formatted table
                formatted = formatted.replace(table_html, "\n" + formatted_table + "\n", 1)
    
    # Clean up remaining HTML tags
    formatted = re.sub(r'<[^>]+>', '', formatted)
    
    # Clean up CSS inline styles artifacts (e.g. "1.15em;">")
    # Pattern: ตัวเลข + หน่วย CSS + ;">
    formatted = re.sub(r'\d+(?:\.\d+)?(?:em|px|pt|%|rem|vh|vw)[;"\'>]+', '', formatted)
    
    # Clean up other HTML/CSS artifacts
    formatted = re.sub(r'["\'][^"\']*(?:style|class|id)=["\'][^"\']*["\']', '', formatted)
    
    # Clean up orphaned quotes and semicolons
    formatted = re.sub(r'[;"\'>]{2,}', '', formatted)
    
    # Format section headers (text with **)
    formatted = re.sub(r'\*\*([^*]+)\*\*', r'\n\n=== \1 ===\n', formatted)
    
    # เพิ่มการขึ้นบรรทัดใหม่สำหรับ === และ --- เพื่อให้อ่านง่ายขึ้น
    # แยก pattern === label: === value === ให้แต่ละส่วนอยู่คนละบรรทัด
    # Pattern: === label: === value ===
    formatted = re.sub(r'===([^=]+?):\s*===\s*([^=]+?)\s*===', r'=== \1: ===\n\2', formatted)
    
    # แยก === ... === ออกเป็นบรรทัดใหม่ (สำหรับกรณีอื่นๆ)
    # แต่ต้องระวังไม่ให้แยกมากเกินไป ให้แยกเฉพาะเมื่อมี pattern === ... ===
    formatted = re.sub(r'===([^=]+?)===', r'=== \1 ===', formatted)
    formatted = re.sub(r'(===)', r'\n\1', formatted)
    formatted = re.sub(r'(===)', r'\1\n', formatted)
    
    # แยก --- ออกเป็นบรรทัดใหม่
    formatted = re.sub(r'(---)', r'\n\1\n', formatted)
    
    # แยก ### headers ออกเป็นบรรทัดใหม่
    formatted = re.sub(r'(###\s+[^\n]+)', r'\n\n\1\n', formatted)
    
    # แยก * [ ] หรือ * [x] list items ออกเป็นบรรทัดใหม่
    formatted = re.sub(r'(\*\s+\[[ x]\]\s+[^\n]+)', r'\n\1', formatted)
    
    # Clean up multiple newlines
    formatted = re.sub(r'\n{3,}', '\n\n', formatted)
    
    # ทำความสะอาดข้อความ: ลบ pipe, HTML tags ที่เหลือ
    formatted = clean_ocr_text(formatted)
    
    # สำหรับหน้า "ส่งเมลล์" ไม่ใช้ format_structured_text เพื่อให้อ่านง่ายขึ้น
    # แค่ทำความสะอาดข้อความพื้นฐานเท่านั้น
    # ลบบรรทัดว่างที่มากเกินไป
    formatted = re.sub(r'\n{3,}', '\n\n', formatted)
    
    # NOTE: ไม่ format ตัวเลขด้วยจุลภาค เพื่อให้อ่านง่าย
    # ตัวเลขจะแสดงเป็นตัวเลขล้วนๆ เช่น 9930000036677 แทนที่จะเป็น 993,000,003,667
    
    return formatted.strip()


def _parse_pp30_calculation_section(text: str) -> str:
    """
    แยกและจัดรูปแบบส่วนการคำนวณภาษี (## การคำนวณภาษี) ให้แสดงทีละบรรทัดตามลำดับ 1-16
    
    Args:
        text: ข้อความที่อ่านได้จาก OCR
        
    Returns:
        ข้อความที่จัดรูปแบบแล้ว แสดงทีละบรรทัด
    """
    if not text:
        return text
    
    # หาส่วนการคำนวณภาษี
    calc_pattern = r'##\s*การคำนวณภาษี(.*?)(?=###|$)'
    calc_match = re.search(calc_pattern, text, re.DOTALL | re.IGNORECASE)
    
    if not calc_match:
        return text
    
    calc_section = calc_match.group(1)
    before_calc = text[:calc_match.start()]
    after_calc = text[calc_match.end():]
    
    # แยกข้อมูลตามลำดับ 1-16
    formatted_lines = []
    
    # หาข้อมูลแต่ละข้อ (1-16) โดยใช้ pattern ที่หลากหลาย
    found_items = {}
    
    # Pattern ที่ครอบคลุมมากขึ้น: จับ "เลข. คำอธิบาย จำนวนเงิน เลข" หรือ "เลข. คำอธิบาย เลข"
    # รองรับทั้งแบบมี comma และไม่มี comma ในจำนวนเงิน
    patterns = [
        # Pattern 1: มีจำนวนเงินแบบมี comma (เช่น "6. ยอดซื้อ 3,500.00 6")
        r'(\d{1,2})\.\s+([^0-9]+?)\s+(\d{1,3}(?:,\d{3})+\.\d{2})\s+(\d{1,2})(?:\s|$)',
        # Pattern 2: มีจำนวนเงินแบบไม่มี comma (เช่น "1. ยอดขาย 0.00 1")
        r'(\d{1,2})\.\s+([^0-9]+?)\s+(\d+\.\d{2})\s+(\d{1,2})(?:\s|$)',
        # Pattern 3: ไม่มีจำนวนเงิน (เช่น "2. ลบ ยอดขาย 2")
        r'(\d{1,2})\.\s+([^0-9]+?)\s+(\d{1,2})(?:\s|$)',
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, calc_section)
        for match in matches:
            item_num = int(match.group(1))
            
            # ตรวจสอบว่าเป็น pattern ที่มีจำนวนเงินหรือไม่
            if len(match.groups()) >= 4:
                description = match.group(2).strip()
                amount = match.group(3)
                line_num = match.group(4)
            else:
                description = match.group(2).strip()
                amount = ''
                line_num = match.group(3)
            
            # ทำความสะอาด description
            description = re.sub(r'\s+', ' ', description).strip()
            description = description.replace('---', '').strip()
            description = description.replace('{ หรือกรณี', '').strip()
            description = description.replace('(ถ้ามี)', '').strip()
            description = description.replace('(ถ้า', '').strip()
            description = description.replace('(1.', '').strip()
            description = description.replace('(6.', '').strip()
            description = description.replace('มาหักในการคำนวณภาษีเดือนนี้', '').strip()
            description = description.replace('ตามหลักฐานใบกำกับภาษีของยอดซื้อตาม', '').strip()
            
            # เก็บเฉพาะข้อมูลที่ดีที่สุด (ถ้ามีจำนวนเงินจะดีกว่า)
            if item_num not in found_items or (amount and not found_items[item_num].get('amount')):
                found_items[item_num] = {
                    'description': description,
                    'amount': amount,
                    'line_num': line_num
                }
    
    # จัดรูปแบบตามลำดับ 1-16
    formatted_lines.append("")
    formatted_lines.append("=" * 70)
    formatted_lines.append("การคำนวณภาษี")
    formatted_lines.append("=" * 70)
    formatted_lines.append("")
    
    # ภาษีขาย (1-5)
    formatted_lines.append("ภาษีขาย:")
    for i in range(1, 6):
        if i in found_items:
            item = found_items[i]
            desc = item['description']
            amount = item['amount']
            
            # ทำความสะอาด description
            desc = desc.replace('{ หรือกรณี', '').strip()
            desc = desc.replace('(ถ้ามี)', '').strip()
            desc = desc.replace('(ถ้า', '').strip()
            
            if amount:
                formatted_lines.append(f"  {i}. {desc}")
                formatted_lines.append(f"     จำนวนเงิน: {amount}")
            else:
                formatted_lines.append(f"  {i}. {desc}")
                formatted_lines.append(f"     จำนวนเงิน: -")
        else:
            # ถ้าไม่พบข้อมูล ให้แสดง placeholder
            formatted_lines.append(f"  {i}. [ไม่พบข้อมูล]")
            formatted_lines.append(f"     จำนวนเงิน: -")
    
    formatted_lines.append("")
    
    # ภาษีซื้อ (6-7)
    formatted_lines.append("ภาษีซื้อ:")
    for i in range(6, 8):
        if i in found_items:
            item = found_items[i]
            desc = item['description']
            amount = item['amount']
            
            # ทำความสะอาด description
            desc = desc.replace('{ หรือกรณี', '').strip()
            desc = desc.replace('(ถ้ามี)', '').strip()
            desc = desc.replace('(ถ้า', '').strip()
            
            if amount:
                formatted_lines.append(f"  {i}. {desc}")
                formatted_lines.append(f"     จำนวนเงิน: {amount}")
            else:
                formatted_lines.append(f"  {i}. {desc}")
                formatted_lines.append(f"     จำนวนเงิน: -")
        else:
            formatted_lines.append(f"  {i}. [ไม่พบข้อมูล]")
            formatted_lines.append(f"     จำนวนเงิน: -")
    
    formatted_lines.append("")
    
    # ภาษีมูลค่าเพิ่ม (8-10)
    formatted_lines.append("ภาษีมูลค่าเพิ่ม:")
    for i in range(8, 11):
        if i in found_items:
            item = found_items[i]
            desc = item['description']
            amount = item['amount']
            
            # ทำความสะอาด description
            desc = desc.replace('{ หรือกรณี', '').strip()
            desc = desc.replace('(ถ้ามี)', '').strip()
            desc = desc.replace('(ถ้า', '').strip()
            
            if amount:
                formatted_lines.append(f"  {i}. {desc}")
                formatted_lines.append(f"     จำนวนเงิน: {amount}")
            else:
                formatted_lines.append(f"  {i}. {desc}")
                formatted_lines.append(f"     จำนวนเงิน: -")
        else:
            formatted_lines.append(f"  {i}. [ไม่พบข้อมูล]")
            formatted_lines.append(f"     จำนวนเงิน: -")
    
    formatted_lines.append("")
    
    # ภาษีสุทธิ (11-12)
    formatted_lines.append("ภาษีสุทธิ:")
    for i in range(11, 13):
        # ตรวจสอบ checkbox จาก calc_section
        checkbox_pattern_11 = r'\[\s*\]\s*11\.|11\.\s*\[\s*\]'
        checkbox_pattern_12 = r'\[x\]\s*12\.|12\.\s*\[x\]'
        
        if i == 11:
            checkbox = "[ ]"  # ข้อ 11 มักจะไม่ถูกเลือก
        elif i == 12:
            checkbox = "[x]" if re.search(checkbox_pattern_12, calc_section, re.IGNORECASE) else "[ ]"
        else:
            checkbox = "[ ]"
        
        if i in found_items:
            item = found_items[i]
            desc = item['description']
            amount = item['amount']
            
            # ทำความสะอาด description
            desc = desc.replace('{ หรือกรณี', '').strip()
            desc = desc.replace('(ถ้ามี)', '').strip()
            desc = desc.replace('(ถ้า', '').strip()
            desc = desc.replace('มากกว่', 'มากกว่า').strip()
            desc = desc.replace('มากกว', 'มากกว่า').strip()
            
            if amount:
                formatted_lines.append(f"  {checkbox} {i}. {desc}")
                formatted_lines.append(f"     จำนวนเงิน: {amount}")
            else:
                formatted_lines.append(f"  {checkbox} {i}. {desc}")
                formatted_lines.append(f"     จำนวนเงิน: -")
        else:
            formatted_lines.append(f"  {checkbox} {i}. [ไม่พบข้อมูล]")
            formatted_lines.append(f"     จำนวนเงิน: -")
    
    formatted_lines.append("")
    
    # กรณียื่นแบบแสดงรายการและชำระภาษีเกินกำหนดเวลา หรือยื่นเพิ่มเติม (13-16)
    formatted_lines.append("กรณียื่นแบบแสดงรายการและชำระภาษีเกินกำหนดเวลา หรือยื่นเพิ่มเติม:")
    for i in range(13, 17):
        if i in found_items:
            item = found_items[i]
            desc = item['description']
            amount = item['amount']
            
            # ทำความสะอาด description (ลบข้อความซ้ำ)
            desc = re.sub(r'^(.+?)\s+\1$', r'\1', desc)  # ลบข้อความซ้ำ
            desc = desc.replace('{ หรือกรณี', '').strip()
            desc = desc.replace('(ถ้ามี)', '').strip()
            desc = desc.replace('(ถ้า', '').strip()
            
            if amount:
                formatted_lines.append(f"  {i}. {desc}")
                formatted_lines.append(f"     จำนวนเงิน: {amount}")
            else:
                formatted_lines.append(f"  {i}. {desc}")
                formatted_lines.append(f"     จำนวนเงิน: -")
        else:
            formatted_lines.append(f"  {i}. [ไม่พบข้อมูล]")
            formatted_lines.append(f"     จำนวนเงิน: -")
    
    # รวมข้อความทั้งหมด
    formatted_calc = '\n'.join(formatted_lines)
    
    # รวมกับส่วนอื่นๆ
    result = before_calc + formatted_calc + after_calc
    
    return result


def _format_pp30_data(cleaned_data: Dict[str, Any]) -> str:
    """
    จัดรูปแบบข้อมูล ภ.พ.30 ให้ตรงกับโครงสร้างภาพ และแสดงผลแบบแนวตั้งทีละแถว
    
    Args:
        cleaned_data: Dictionary ที่มีข้อมูลจาก key-extract API
        
    Returns:
        ข้อความที่จัดรูปแบบแล้วตามโครงสร้างแบบฟอร์ม ภ.พ.30 แสดงผลแบบแนวตั้ง
    """
    text_parts = []
    
    # ส่วนหัว (Header Section)
    text_parts.append("=" * 70)
    text_parts.append("แบบแสดงรายการภาษีมูลค่าเพิ่ม ตามประมวลรัษฎากร (ภ.พ.30)")
    text_parts.append("=" * 70)
    text_parts.append("")
    
    # หมายเลขอ้างอิง
    if 'หมายเลขอ้างอิง' in cleaned_data:
        ref_num = cleaned_data.get('หมายเลขอ้างอิง', '')
        if ref_num:
            text_parts.append(f"หมายเลขอ้างอิง: {ref_num}")
    
    # เลขประจำตัวผู้เสียภาษี
    if 'เลขประจำตัวผู้เสียภาษี' in cleaned_data:
        tax_id = cleaned_data.get('เลขประจำตัวผู้เสียภาษี', '')
        if tax_id:
            # ทำความสะอาดเลขประจำตัวผู้เสียภาษี (ลบช่องว่าง)
            tax_id_clean = tax_id.replace(' ', '').replace('-', '')
            text_parts.append(f"เลขประจำตัวผู้เสียภาษี: {tax_id_clean}")
    
    # สาขาที่
    if 'สาขาที่' in cleaned_data:
        branch = cleaned_data.get('สาขาที่', '')
        if branch:
            # ทำความสะอาดสาขา (ลบช่องว่าง)
            branch_clean = branch.replace(' ', '')
            text_parts.append(f"สาขาที่: {branch_clean}")
    
    # ชื่อผู้ประกอบการ
    if 'ชื่อผู้ประกอบการ' in cleaned_data:
        company_name = cleaned_data.get('ชื่อผู้ประกอบการ', '')
        if company_name:
            # ทำความสะอาดชื่อ (ลบช่องว่างส่วนเกิน)
            company_name_clean = ' '.join(company_name.split())
            text_parts.append(f"ชื่อผู้ประกอบการ: {company_name_clean}")
    
    # ที่อยู่ผู้ประกอบการ
    if 'ที่อยู่ผู้ประกอบการ' in cleaned_data:
        address = cleaned_data.get('ที่อยู่ผู้ประกอบการ', '')
        if address:
            # แยกที่อยู่เป็นบรรทัดเพื่ออ่านง่าย
            address_clean = ' '.join(address.split())
            # แยกส่วนต่างๆ ของที่อยู่
            address_parts = address_clean.split(' - ')
            if len(address_parts) > 1:
                # แสดงที่อยู่ทีละส่วน
                for part in address_parts:
                    if part.strip() and part.strip() != '-':
                        text_parts.append(f"  {part.strip()}")
            else:
                text_parts.append(f"ที่อยู่: {address_clean}")
    
    text_parts.append("")
    
    # ข้อมูลการยื่นแบบ
    text_parts.append("-" * 70)
    text_parts.append("ข้อมูลการยื่นแบบ")
    text_parts.append("-" * 70)
    
    # เดือนภาษี
    if 'เดือนภาษี' in cleaned_data:
        month = cleaned_data.get('เดือนภาษี', '')
        if month:
            month_names = ['', 'มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 'พฤษภาคม', 
                          'มิถุนายน', 'กรกฎาคม', 'สิงหาคม', 'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม']
            try:
                month_num = int(month)
                if 1 <= month_num <= 12:
                    text_parts.append(f"เดือนภาษี: {month_names[month_num]}")
            except:
                text_parts.append(f"เดือนภาษี: {month}")
    
    # ปีภาษี
    if 'ปีภาษี (พ.ศ.)' in cleaned_data:
        year = cleaned_data.get('ปีภาษี (พ.ศ.)', '')
        if year:
            text_parts.append(f"ปีภาษี (พ.ศ.): {year}")
    
    # สถานะการยื่นแบบ
    if 'ยื่นแบบปกติ' in cleaned_data:
        filing_status = cleaned_data.get('ยื่นแบบปกติ', '')
        if filing_status:
            if filing_status.lower() in ['true', '1', 'yes', 'ยื่นปกติ']:
                text_parts.append("สถานะการยื่นแบบ: ยื่นปกติ")
            else:
                text_parts.append("สถานะการยื่นแบบ: ยื่นเพิ่มเติม")
    
    text_parts.append("")
    
    # ส่วนการคำนวณภาษี (Tax Calculation Section)
    text_parts.append("-" * 70)
    text_parts.append("การคำนวณภาษี")
    text_parts.append("-" * 70)
    text_parts.append("")
    
    # ภาษีขาย (Sales Tax)
    text_parts.append("ภาษีขาย:")
    
    # ข้อ 1: ยอดขายในเดือนนี้
    if 'ยอดขายในเดือนนี้' in cleaned_data:
        sales = cleaned_data.get('ยอดขายในเดือนนี้', '')
        if sales:
            sales_clean = sales.replace(' ', '').replace(',', '')
            text_parts.append(f"  1. ยอดขายในเดือนนี้")
            text_parts.append(f"     จำนวนเงิน: {sales_clean}")
    
    # ข้อ 2: ยอดขายที่เสียภาษีในอัตราร้อยละ 0
    if 'ยอดขายที่เสียภาษีในอัตราร้อยละ 0' in cleaned_data:
        sales_0 = cleaned_data.get('ยอดขายที่เสียภาษีในอัตราร้อยละ 0', '')
        if sales_0:
            sales_0_clean = sales_0.replace(' ', '').replace(',', '')
            text_parts.append(f"  2. ลบ ยอดขายที่เสียภาษีในอัตราร้อยละ 0")
            text_parts.append(f"     จำนวนเงิน: {sales_0_clean}")
    
    # ข้อ 3: ยอดขายที่ได้รับยกเว้น
    if 'ยอดขายที่ได้รับยกเว้น' in cleaned_data:
        sales_exempt = cleaned_data.get('ยอดขายที่ได้รับยกเว้น', '')
        if sales_exempt:
            sales_exempt_clean = sales_exempt.replace(' ', '').replace(',', '')
            text_parts.append(f"  3. ลบ ยอดขายที่ได้รับยกเว้น")
            text_parts.append(f"     จำนวนเงิน: {sales_exempt_clean}")
    
    # ข้อ 4: ยอดขายที่ต้องเสียภาษี
    if 'ยอดขายที่ต้องเสียภาษี' in cleaned_data:
        taxable_sales = cleaned_data.get('ยอดขายที่ต้องเสียภาษี', '')
        if taxable_sales:
            taxable_sales_clean = taxable_sales.replace(' ', '').replace(',', '')
            text_parts.append(f"  4. ยอดขายที่ต้องเสียภาษี (1. - 2. - 3.)")
            text_parts.append(f"     จำนวนเงิน: {taxable_sales_clean}")
    
    # ข้อ 5: ภาษีขายเดือนนี้
    if 'ภาษีขายเดือนนี้' in cleaned_data:
        sales_tax = cleaned_data.get('ภาษีขายเดือนนี้', '')
        if sales_tax:
            sales_tax_clean = sales_tax.replace(' ', '').replace(',', '')
            text_parts.append(f"  5. ภาษีขายเดือนนี้")
            text_parts.append(f"     จำนวนเงิน: {sales_tax_clean}")
    
    text_parts.append("")
    
    # ภาษีซื้อ (Purchase Tax)
    text_parts.append("ภาษีซื้อ:")
    
    # ข้อ 6: ยอดซื้อที่มีสิทธินำภาษีซื้อ
    if 'ยอดซื้อที่มีสิทธินำภาษีซื้อ' in cleaned_data:
        purchases = cleaned_data.get('ยอดซื้อที่มีสิทธินำภาษีซื้อ', '')
        if purchases:
            purchases_clean = purchases.replace(' ', '').replace(',', '')
            text_parts.append(f"  6. ยอดซื้อที่มีสิทธินำภาษีซื้อ")
            text_parts.append(f"     จำนวนเงิน: {purchases_clean}")
    
    # ข้อ 7: ภาษีซื้อเดือนนี้
    if 'ภาษีซื้อเดือนนี้' in cleaned_data:
        purchase_tax = cleaned_data.get('ภาษีซื้อเดือนนี้', '')
        if purchase_tax:
            purchase_tax_clean = purchase_tax.replace(' ', '').replace(',', '')
            text_parts.append(f"  7. ภาษีซื้อเดือนนี้")
            text_parts.append(f"     จำนวนเงิน: {purchase_tax_clean}")
    
    text_parts.append("")
    
    # ภาษีมูลค่าเพิ่ม (VAT)
    text_parts.append("ภาษีมูลค่าเพิ่ม:")
    
    # ข้อ 8: ภาษีที่ต้องชำระเดือนนี้
    if 'ภาษีที่ต้องชำระเดือนนี้' in cleaned_data:
        tax_payable = cleaned_data.get('ภาษีที่ต้องชำระเดือนนี้', '')
        if tax_payable:
            tax_payable_clean = tax_payable.replace(' ', '').replace(',', '')
            text_parts.append(f"  8. ภาษีที่ต้องชำระเดือนนี้ (ถ้า 5 มากกว่า 7)")
            text_parts.append(f"     จำนวนเงิน: {tax_payable_clean}")
    
    # ข้อ 9: ภาษีที่ชำระเกินเดือนนี้
    if 'ภาษีที่ชำระเกินเดือนนี้' in cleaned_data:
        tax_overpaid = cleaned_data.get('ภาษีที่ชำระเกินเดือนนี้', '')
        if tax_overpaid:
            tax_overpaid_clean = tax_overpaid.replace(' ', '').replace(',', '')
            text_parts.append(f"  9. ภาษีที่ชำระเกินเดือนนี้ (ถ้า 5 น้อยกว่า 7)")
            text_parts.append(f"     จำนวนเงิน: {tax_overpaid_clean}")
    
    # ข้อ 10: ภาษีที่ชำระเกินยกมา
    if 'ภาษีที่ชำระเกินยกมา' in cleaned_data:
        carry_forward = cleaned_data.get('ภาษีที่ชำระเกินยกมา', '')
        if carry_forward:
            carry_forward_clean = carry_forward.replace(' ', '').replace(',', '')
            text_parts.append(f"  10. ภาษีที่ชำระเกินยกมา")
            text_parts.append(f"      จำนวนเงิน: {carry_forward_clean}")
    
    text_parts.append("")
    
    # สุทธิ (Net Tax)
    text_parts.append("สุทธิ:")
    
    # ข้อ 11: ต้องชำระ
    if 'ต้องชำระ' in cleaned_data:
        must_pay = cleaned_data.get('ต้องชำระ', '')
        if must_pay:
            must_pay_clean = must_pay.replace(' ', '').replace(',', '')
            text_parts.append(f"  11. ต้องชำระ (ถ้า 8. มากกว่า 10.)")
            text_parts.append(f"      จำนวนเงิน: {must_pay_clean}")
    
    # ข้อ 12: ชำระเกิน
    if 'ชำระเกิน' in cleaned_data:
        overpaid = cleaned_data.get('ชำระเกิน', '')
        if overpaid:
            overpaid_clean = overpaid.replace(' ', '').replace(',', '')
            text_parts.append(f"  12. ชำระเกิน (ถ้า 10. มากกว่า 8.) หรือ (9. รวมกับ 10.)")
            text_parts.append(f"      จำนวนเงิน: {overpaid_clean}")
    
    text_parts.append("")
    
    # กรณียื่นแบบแสดงรายการและชำระภาษีเกินกำหนดเวลา หรือยื่นเพิ่มเติม
    text_parts.append("กรณียื่นแบบแสดงรายการและชำระภาษีเกินกำหนดเวลา หรือยื่นเพิ่มเติม:")
    
    # ข้อ 13: เงินเพิ่ม
    if 'เงินเพิ่ม' in cleaned_data:
        surcharge = cleaned_data.get('เงินเพิ่ม', '')
        if surcharge:
            surcharge_clean = surcharge.replace(' ', '').replace(',', '')
            text_parts.append(f"  13. เงินเพิ่ม")
            text_parts.append(f"      จำนวนเงิน: {surcharge_clean}")
    
    # ข้อ 14: เบี้ยปรับ
    if 'เบี้ยปรับ' in cleaned_data:
        penalty = cleaned_data.get('เบี้ยปรับ', '')
        if penalty:
            penalty_clean = penalty.replace(' ', '').replace(',', '')
            text_parts.append(f"  14. เบี้ยปรับ")
            text_parts.append(f"      จำนวนเงิน: {penalty_clean}")
    
    # ข้อ 15: รวมภาษี เงินเพิ่ม และเบี้ยปรับที่ต้องชำระ
    if 'รวมภาษี เงินเพิ่ม และเบี้ยปรับที่ต้องชำระ' in cleaned_data:
        total_payable = cleaned_data.get('รวมภาษี เงินเพิ่ม และเบี้ยปรับที่ต้องชำระ', '')
        if total_payable:
            total_payable_clean = total_payable.replace(' ', '').replace(',', '')
            text_parts.append(f"  15. รวมภาษี เงินเพิ่ม และเบี้ยปรับที่ต้องชำระ")
            text_parts.append(f"      จำนวนเงิน: {total_payable_clean}")
    
    # ข้อ 16: รวมภาษีที่ชำระเกิน หลังคำนวณเงินเพิ่มและเบี้ยปรับแล้ว
    if 'รวมภาษีที่ชำระเกิน หลังคำนวณเงินเพิ่มและเบี้ยปรับแล้ว' in cleaned_data:
        total_overpaid = cleaned_data.get('รวมภาษีที่ชำระเกิน หลังคำนวณเงินเพิ่มและเบี้ยปรับแล้ว', '')
        if total_overpaid:
            total_overpaid_clean = total_overpaid.replace(' ', '').replace(',', '')
            text_parts.append(f"  16. รวมภาษีที่ชำระเกิน หลังคำนวณเงินเพิ่มและเบี้ยปรับแล้ว")
            text_parts.append(f"      จำนวนเงิน: {total_overpaid_clean}")
    
    text_parts.append("")
    
    # การขอคืนภาษี
    if 'การขอคืนภาษี' in cleaned_data:
        refund_type = cleaned_data.get('การขอคืนภาษี', '')
        if refund_type:
            text_parts.append("-" * 70)
            text_parts.append("การขอคืนภาษี")
            text_parts.append("-" * 70)
            text_parts.append(f"ประเภทการขอคืน: {refund_type}")
    
    text_parts.append("")
    
    # ข้อมูลใบเสร็จ (ถ้ามี)
    if 'เลขที่ใบเสร็จ' in cleaned_data or 'วันที่ใบเสร็จ' in cleaned_data:
        text_parts.append("")
        text_parts.append("-" * 70)
        text_parts.append("สำหรับใบเสร็จรับเงิน")
        text_parts.append("-" * 70)
        
        if 'เลขที่ใบเสร็จ' in cleaned_data:
            receipt_num = cleaned_data.get('เลขที่ใบเสร็จ', '')
            if receipt_num:
                receipt_num_clean = receipt_num.replace(' ', '')
                text_parts.append(f"เลขที่ใบเสร็จ: {receipt_num_clean}")
        
        if 'วันที่ใบเสร็จ' in cleaned_data:
            receipt_date = cleaned_data.get('วันที่ใบเสร็จ', '')
            if receipt_date:
                receipt_date_clean = receipt_date.replace(' ', '')
                text_parts.append(f"วันที่: {receipt_date_clean}")
        
        if 'จำนวนเงินใบเสร็จ' in cleaned_data:
            receipt_amount = cleaned_data.get('จำนวนเงินใบเสร็จ', '')
            if receipt_amount:
                receipt_amount_clean = receipt_amount.replace(' ', '').replace(',', '')
                text_parts.append(f"จำนวนเงิน: {receipt_amount_clean} บาท")
    
    text_parts.append("")
    
    # วันที่ยื่นแบบ
    if 'วันที่ยื่นแบบ' in cleaned_data:
        filing_date = cleaned_data.get('วันที่ยื่นแบบ', '')
        if filing_date:
            filing_date_clean = ' '.join(filing_date.split())
            text_parts.append(f"ยื่นวันที่: {filing_date_clean}")
    
    return '\n'.join(text_parts)


def _detect_pp30_form(image_path: str) -> bool:
    """
    ตรวจสอบว่าเป็นเอกสาร ภ.พ.30 หรือไม่ โดยอ่านข้อความจากไฟล์ PDF
    
    Args:
        image_path: Path ของไฟล์ PDF
        
    Returns:
        True ถ้าเป็นเอกสาร ภ.พ.30, False ถ้าไม่ใช่
    """
    try:
        import PyPDF2
        with open(image_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            if len(pdf_reader.pages) > 0:
                first_page_text = pdf_reader.pages[0].extract_text()
                # ตรวจสอบว่ามีคำว่า "ภ.พ.30" หรือ "แบบแสดงรายการภาษีมูลค่าเพิ่ม"
                pp30_indicators = [
                    'ภ.พ.30',
                    'ภพ.30',
                    'ภพ30',
                    'แบบแสดงรายการภาษีมูลค่าเพิ่ม',
                    'Value Added Tax Return Form'
                ]
                for indicator in pp30_indicators:
                    if indicator in first_page_text:
                        logger.info(f"✅ ตรวจพบว่าเป็นเอกสาร ภ.พ.30 (พบ: {indicator})")
                        return True
    except Exception as e:
        logger.warning(f"⚠️ ไม่สามารถตรวจสอบประเภทเอกสารได้: {e}")
    return False


def _get_pp30_custom_fields() -> List[Dict[str, str]]:
    """
    สร้าง custom fields สำหรับ AksonOCR key-extract API สำหรับแบบภาษี ภ.พ.30
    
    Returns:
        List of custom field dictionaries
    """
    return [
        {
            "key": "ประเภทเอกสาร",
            "description": "ประเภทเอกสาร ต้องเป็น 'ภ.พ.30' หรือ 'แบบแสดงรายการภาษีมูลค่าเพิ่ม'",
            "example": "ภ.พ.30"
        },
        {
            "key": "หมายเลขอ้างอิง",
            "description": "หมายเลขอ้างอิงที่อยู่ด้านบนซ้ายของแบบฟอร์ม (เช่น P300033715473)",
            "example": "P300033715473"
        },
        {
            "key": "เลขประจำตัวผู้เสียภาษี",
            "description": "เลขประจำตัวผู้เสียภาษี 13 หลัก (เช่น 0105564035037)",
            "example": "0105564035037"
        },
        {
            "key": "สาขาที่",
            "description": "หมายเลขสาขา (เช่น 00000)",
            "example": "00000"
        },
        {
            "key": "ชื่อผู้ประกอบการ",
            "description": "ชื่อบริษัทหรือผู้ประกอบการ (เช่น บริษัท โคนาโก คอร์ปอเรชั่น จำกัด)",
            "example": "บริษัท โคนาโก คอร์ปอเรชั่น จำกัด"
        },
        {
            "key": "ที่อยู่ผู้ประกอบการ",
            "description": "ที่อยู่เต็มของผู้ประกอบการ รวมเลขที่ ถนน แขวง/ตำบล เขต/อำเภอ จังหวัด รหัสไปรษณีย์",
            "example": "เลขที่ 1367 ตรอก/ซอย กาญจนาภิเษก 008 ตำบล/แขวง บางแค อำเภอ/เขต บางแค จังหวัด กรุงเทพมหานคร รหัสไปรษณีย์ 10160"
        },
        {
            "key": "เดือนภาษี",
            "description": "เดือนภาษีที่ยื่นแบบ (1-12) เช่น 12 สำหรับธันวาคม",
            "example": "12"
        },
        {
            "key": "ปีภาษี (พ.ศ.)",
            "description": "ปีภาษี พ.ศ. (เช่น 2568)",
            "example": "2568"
        },
        {
            "key": "ยื่นแบบปกติ",
            "description": "สถานะการยื่นแบบ: 'ยื่นปกติ' หรือ 'ยื่นเพิ่มเติม' (ระบุเป็น true/false หรือ checkbox status)",
            "example": "true"
        },
        {
            "key": "1. ยอดขายในเดือนนี้",
            "description": "",
            "example": ""
        },
        {
            "key": "2. ลบ ยอดขายที่เสียภาษีในอัตราร้อยละ 0 (ถ้ามี)",
            "description": "",
            "example": ""
        },
        {
            "key": "3. ลบ ยอดขายที่ได้รับยกเว้น (ถ้ามี)",
            "description": "",
            "example": ""
        },
        {
            "key": "4. ยอดขายที่ต้องเสียภาษี (1. - 2. - 3.)",
            "description": "",
            "example": ""
        },
        {
            "key": "5. ภาษีขายเดือนนี้",
            "description": "",
            "example": ""
        },
        {
            "key": "6. ยอดซื้อที่มีสิทธินำภาษีซื้อ",
            "description": "",
            "example": ""
        },
        {
            "key": "7. ภาษีซื้อเดือนนี้(ตามหลักฐานใบกำกับภาษีของยอดซื้อตาม 6.)",
            "description": "",
            "example": ""
        },
        {
            "key": "8. ภาษีที่ต้องชำระเดือนนี้ (ถ้า 5. มากกว่า 7. )",
            "description": "",
            "example": ""
        },
        {
            "key": "9. ภาษีที่ชำระเกินเดือนนี้ (ถ้า 5. น้อยกว่า 7. )",
            "description": "",
            "example": ""
        },
        {
            "key": "10. ภาษีที่ชำระเกินยกมา",
            "description": "",
            "example": ""
        },
        {
            "key": "11. ต้องชำระ (ถ้า 8. มากกว่า 10.)",
            "description": "",
            "example": ""
        },
        {
            "key": "12. ชำระเกิน (ถ้า 10. มากกว่า 8.) หรือ (9. รวมกับ 10.)",
            "description": "",
            "example": ""
        },
        {
            "key": "13. เงินเพิ่ม",
            "description": "",
            "example": ""
        },
        {
            "key": "14. เบี้ยปรับ",
            "description": "",
            "example": ""
        },
        {
            "key": "15. รวมภาษี เงินเพิ่ม และเบี้ยปรับที่ต้องชำระ ( 11. + 13. + 14. ) หรือ ( 13. + 14. - 12. )",
            "description": "",
            "example": ""
        },
        {
            "key": "16. รวมภาษีที่ชำระเกิน หลังคำนวณเงินเพิ่มและเบี้ยปรับแล้ว( 12. - 13. - 14. )",
            "description": "",
            "example": ""
        },
        {
            "key": "การขอคืนภาษี",
            "description": "ประเภทการขอคืนภาษี: 'คืนเงินสด', 'คืนผ่านธนาคาร', หรือ 'ขอนำภาษีไปชำระในเดือนถัดไป'",
            "example": "ขอนำภาษีไปชำระในเดือนถัดไป"
        },
        {
            "key": "เลขที่ใบเสร็จ",
            "description": "เลขที่ใบเสร็จรับเงิน (ถ้ามี)",
            "example": "69002638890"
        },
        {
            "key": "วันที่ใบเสร็จ",
            "description": "วันที่ใบเสร็จรับเงิน (ถ้ามี) รูปแบบ DD/MM/YYYY",
            "example": "16/01/2560"
        },
        {
            "key": "จำนวนเงินใบเสร็จ",
            "description": "จำนวนเงินในใบเสร็จรับเงิน (ถ้ามี)",
            "example": "0.00"
        },
        {
            "key": "วันที่ยื่นแบบ",
            "description": "วันที่ยื่นแบบ รูปแบบ DD/MM/YYYY หรือ DD เดือน MM พ.ศ. YYYY",
            "example": "16 มกราคม พ.ศ. 2569"
        }
    ]


def extract_text_from_aksonocr(
    image_path: str,
    api_key: str,
    ocr_mode: str = 'v2/upload'
) -> Dict[str, Any]:
    """
    Extract text from image/PDF using AksonOCR API.
    
    Args:
        image_path: Path to image/PDF file
        api_key: AksonOCR API key
        ocr_mode: OCR mode to use
            - 'key-extract': ใช้ /api/v1/key-extract (สำหรับหน้า ประมวลผล PDF)
            - 'v2/upload': ใช้ /api/v2/upload (สำหรับหน้า ส่งเมลล์) - default
        
    Returns:
        Dictionary containing:
        - 'text': Natural text content (markdown format)
        - 'tables': List of tables (if any)
        - 'numbers': List of extracted numbers (if any)
        - 'raw_content': Raw API response content
    """
    # เลือก endpoint ตาม ocr_mode
    if ocr_mode == 'key-extract':
        # ใช้ endpoint /api/v1/key-extract (ตาม test_aksonocr.py)
        url = "https://backend.aksonocr.com/api/v1/key-extract"
        use_key_extract = True
    else:
        # ใช้ endpoint /api/v2/upload (ตาม test_aksonocr_v2.py) - default
        url = "https://backend.aksonocr.com/api/v2/upload"
        use_key_extract = False
    
    try:
        file_path = Path(image_path)
        if not file_path.exists():
            logger.error(f"❌ AksonOCR: ไม่พบไฟล์: {image_path}")
            return {
                'text': None,
                'tables': [],
                'numbers': [],
                'raw_content': None,
                'error': f'ไม่พบไฟล์: {image_path}'
            }
        
        file_extension = file_path.suffix.lower()
        filename = file_path.name
        
        # ตรวจสอบว่าเป็นไฟล์ที่รองรับหรือไม่
        if file_extension not in ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif']:
            logger.error(f"❌ AksonOCR: ไฟล์ประเภท {file_extension} ไม่รองรับ (รองรับเฉพาะ PDF และ Image)")
            return {
                'text': None,
                'tables': [],
                'numbers': [],
                'raw_content': None,
                'error': f'ไฟล์ประเภท {file_extension} ไม่รองรับ'
            }
        
        # หา mime type ของไฟล์
        mime_type = mimetypes.guess_type(str(file_path))[0] or 'application/pdf'
        
        # ตรวจสอบว่าเป็นเอกสาร ภ.พ.30 หรือไม่
        is_pp30 = _detect_pp30_form(image_path)
        
        # เปิดไฟล์และส่งไปยัง API
        with open(image_path, 'rb') as file:
            if use_key_extract:
                # ใช้รูปแบบจาก test_aksonocr.py (/api/v1/key-extract)
                # Define custom fields สำหรับ key-extract
                if is_pp30:
                    # ใช้ custom fields สำหรับ ภ.พ.30
                    logger.info("📋 ใช้ custom fields สำหรับ ภ.พ.30")
                    custom_fields = _get_pp30_custom_fields()
                    additional_instructions = 'ดึงข้อมูลจากแบบภาษี ภ.พ.30 (แบบแสดงรายการภาษีมูลค่าเพิ่ม) โดยเน้นความถูกต้องของตัวเลขและวันที่ และจัดเรียงข้อมูลตามโครงสร้างของแบบฟอร์ม'
                else:
                    # ใช้ custom fields สำหรับใบกำกับภาษีทั่วไป
                    custom_fields = [
                    {
                        "key": "ประเภทเอกสาร",
                        "description": "ประเภทเอกสาร ให้เเสดงผลแค่ถ้าหากเกินกว่านี้ให้ลบออกเช่น Receipt/Tax Invoice, Receipt, Tax Invoice, Invoice, ใบเสร็จรับเงิน/ใบกำกับภาษี, ใบเสร็จรับเงิน, ใบกำกับภาษี, ใบแจ้งหนี้",
                        "example": "Receipt / Tax Invoice / Invoice / ใบเสร็จรับเงิน/ใบกำกับภาษี / ใบเสร็จรับเงิน / ใบกำกับภาษี / ใบแจ้งหนี้ / ใบแจ้งค่าบริการ"
                    },
                    {
                        "key": "สถานะเอกสาร",
                        "description": "สถานะเอกสารว่าเป็น ต้นฉบับ (Original) หรือ สำเนา (Copy/Duplicate) ให้เเสดวผลออกมาแค่ 2 อย่างเท่านั้นคือ 1. ต้นฉบับ หรือ 2. สำเนา",
                        "example": "ต้นฉบับ หรือ สำเนา"
                    },
                    {
                        "key": "เลขที่ใบกำกับภาษี",
                        "description": "เลขที่ใบกำกับภาษีหรือใบเสร็จ",
                        "example": "IV2024001"
                    },
                    {
                        "key": "วันที่",
                        "description": "วันที่ออกใบกำกับภาษีให้ระบบเเสดงข้อมูลของวันที่ออกมาเป็นรูปแบบของ dd/mm/yyyy เท่านั้นถ้ามีข้อมูลส่วนอื่นๆ เข้ามาก็ให้ระบบทำการตัดออก",
                        "example": "15/01/2567"
                    },
                    {
                        "key": "ชื่อผู้ขาย",
                        "description": "ชื่อบริษัทหรือร้านค้าผู้ขาย",
                        "example": "บริษัท เอบีซี จำกัด"
                    },
                    {
                        "key": "เลขประจำตัวผู้เสียภาษี - ผู้ขาย",
                        "description": "เลขประจำตัวผู้เสียภาษีของบริษัทผู้ขาย (Tax ID)",
                        "example": "0105518012712"
                    },
                    {
                        "key": "ที่อยู่ผู้ขาย",
                        "description": "ที่อยู่เต็มของผู้ขาย (บริษัทผู้ขาย) รวมเลขที่ ถนน แขวง/ตำบล เขต/อำเภอ จังหวัด รหัสไปรษณีย์",
                        "example": "123 ถนนสุขุมวิท แขวงคลองตัน เขตคลองตัน กรุงเทพมหานคร 10110"
                    },
                    {
                        "key": "สาขา - ผู้ขาย",
                        "description": "สาขาของบริษัทผู้ขาย เช็คข้อมูลให้ครบถ้วนและถูกต้องถ้าหากเป็นสำนังกานใหญ่ให้เเสดงผลเป็น HQ (00000) และถ้าหากเป็นสาขาให้เเสดงผลเป็น 00001",
                        "example": "00000"
                    },
                    {
                        "key": "ชื่อผู้นำส่งภาษีมูลค่าเพิ่ม",
                        "description": "ชื่อบริษัทหรือบุคคลที่นำส่งภาษีมูลค่าเพิ่ม (สำหรับแบบ ภ.พ.36) เช่น ชื่อที่แสดงในช่อง 'ชื่อผู้นำส่งภาษีมูลค่าเพิ่ม'",
                        "example": "บริษัท ไอสาม เกทเวย์ จำกัด"
                    },
                    {
                        "key": "เลขประจำตัวผู้เสียภาษี - ผู้นำส่งภาษีมูลค่าเพิ่ม",
                        "description": "เลขประจำตัวผู้เสียภาษีของผู้นำส่งภาษีมูลค่าเพิ่ม (สำหรับแบบ ภ.พ.36) เช่น เลขที่แสดงในช่อง 'เลขประจำตัวผู้เสียภาษีอากร'",
                        "example": "0105553114437"
                    },
                    {
                        "key": "ที่อยู่ - ผู้นำส่งภาษีมูลค่าเพิ่ม",
                        "description": "ที่อยู่ของผู้นำส่งภาษีมูลค่าเพิ่ม (สำหรับแบบ ภ.พ.36) รวมเลขที่ ถนน แขวง/ตำบล เขต/อำเภอ จังหวัด รหัสไปรษณีย์",
                        "example": "อาคาร ไอทีเอฟ-ทาวเวอร์ ห้องเลขที่ - ชั้นที่ 25 เลขที่ 140/61 ถนน สีลม แขวง สุริยวงศ์ เขต บางรัก จังหวัด กรุงเทพมหานคร 10500"
                    },
                    {
                        "key": "สาขา - ผู้นำส่งภาษีมูลค่าเพิ่ม",
                        "description": "สาขาของผู้นำส่งภาษีมูลค่าเพิ่ม (สำหรับแบบ ภ.พ.36) เช่น เลขที่แสดงในช่อง 'สาขาที่'",
                        "example": "00000"
                    },
                    {
                        "key": "ชื่อผู้ซื้อ",
                        "description": "ชื่อบริษัทหรือลูกค้าผู้ซื้อ",
                        "example": "บริษัท ลูกค้า จำกัด"
                    },
                    {
                        "key": "เลขประจำตัวผู้เสียภาษี - ผู้ซื้อ",
                        "description": "เลขประจำตัวผู้เสียภาษีของลูกค้าผู้ซื้อ (Tax ID)",
                        "example": "0105568010721"
                    },
                    {
                        "key": "ที่อยู่ผู้ซื้อ",
                        "description": "ที่อยู่เต็มของผู้ซื้อ (ลูกค้า) รวมเลขที่ ถนน แขวง/ตำบล เขต/อำเภอ จังหวัด รหัสไปรษณีย์",
                        "example": "456 ถนนพหลโยธิน แขวงจตุจักร เขตจตุจักร กรุงเทพมหานคร 10900"
                    },
                    {
                        "key": "สาขา - ผู้ซื้อ",
                        "description": "สาขาของบริษัทผู้ซื้อ เช็คข้อมูลให้ครบถ้วนและถูกต้องถ้าหากเป็นสำนังกานใหญ่ให้เเสดงผลเป็น HQ (00000) และถ้าหากเป็นสาขาให้เเสดงผลเป็น 00001",
                        "example": "00000"
                    },
                    {
                        "key": "ค่าธรรมเนียม",
                        "description": "ค่าธรรมเนียมหรือค่าบริการ (Commission) สำหรับเอกสารบางประเภท เช่น เอกสารของบริษัท เคเชอร์ เพย์เมนท์ จำกัด",
                        "example": "16.54"
                    },
                    {
                        "key": "ยอดรวมก่อนภาษี",
                        "description": "ยอดรวมก่อนภาษีมูลค่าเพิ่ม",
                        "example": "1,000.00"
                    },
                    {
                        "key": "ภาษีมูลค่าเพิ่ม",
                        "description": "จำนวนเงินภาษีมูลค่าเพิ่ม (VAT)",
                        "example": "70.00"
                    },
                    {
                        "key": "ส่วนลด",
                        "description": "ส่วนลดที่รับได้ (ถ้ามี)",
                        "example": "100.00"
                    },
                    {
                        "key": "ยอดเงินที่ได้รับยกเว้นภาษี",
                        "description": "ยอดเงินที่ได้รับยกเว้นภาษีมูลค่าเพิ่ม (Non-Taxable Amount) เช่น ยอดขายที่ได้รับยกเว้น ยอดที่ได้รับยกเว้นภาษี ยอดยกเว้นภาษี",
                        "example": "500.00"
                    },
                    {
                        "key": "ยอดรวมสุทธิ",
                        "description": "ยอดรวมทั้งสิ้นที่ต้องชำระ",
                        "example": "1,070.00"
                    },
                    {
                        "key": "มีการหัก ณ ที่จ่าย",
                        "description": "ตรวจสอบว่าเอกสารมีการหัก ณ ที่จ่ายหรือไม่ (Withholding Tax) เช่น มีข้อความ 'หัก ณ ที่จ่าย', 'WHT', 'Withholding Tax', 'หักภาษี ณ ที่จ่าย'",
                        "example": "ใช่ หรือ ไม่ใช่ หรือ มี หรือ ไม่มี"
                    },
                    {
                        "key": "จำนวนเงินหัก ณ ที่จ่าย",
                        "description": "จำนวนเงินที่หัก ณ ที่จ่าย (ถ้ามี)",
                        "example": "100.00"
                    },
                    {
                        "key": "อัตราหัก ณ ที่จ่าย",
                        "description": "อัตราการหัก ณ ที่จ่าย (ถ้ามี) เช่น 3%, 5%",
                        "example": "3%"
                    },
                    {
                        "key": "การหัก ณ ที่จ่ายเป็นการกระทำการแทน",
                        "description": "ตรวจสอบว่าการหัก ณ ที่จ่ายเป็นการกระทำการแทนหรือไม่ เช่น มีข้อความ 'กระทำการแทน', 'Acting on behalf', 'ผู้รับมอบอำนาจ'",
                        "example": "ใช่ หรือ ไม่ใช่ หรือ มี หรือ ไม่มี"
                    },
                    {
                        "key": "ชื่อผู้รับมอบอำนาจ",
                        "description": "ชื่อบริษัทหรือบุคคลที่รับมอบอำนาจ (ถ้ามีการกระทำการแทน)",
                        "example": "บริษัท รับมอบอำนาจ จำกัด"
                    },
                    {
                        "key": "เลขประจำตัวผู้เสียภาษี - ผู้รับมอบอำนาจ",
                        "description": "เลขประจำตัวผู้เสียภาษีของผู้รับมอบอำนาจ (ถ้ามีการกระทำการแทน)",
                        "example": "0105518012712"
                    }
                ]
                
                # Define list/table configuration
                list_config = {
                    "listKey": "รายการสินค้า",
                    "listDescription": "รายการสินค้าหรือบริการที่ซื้อ",
                    "fields": [
                        {
                            "key": "ลำดับ",
                            "description": "ลำดับรายการ",
                            "example": "1"
                        },
                        {
                            "key": "รายการ",
                            "description": "ชื่อสินค้าหรือบริการ",
                            "example": "ค่าบริการ"
                        },
                        {
                            "key": "จำนวน",
                            "description": "จำนวนหน่วย",
                            "example": "1"
                        },
                        {
                            "key": "ราคาต่อหน่วย",
                            "description": "ราคาต่อหน่วย",
                            "example": "1,000.00"
                        },
                        {
                            "key": "จำนวนเงิน",
                            "description": "จำนวนเงินรวมของรายการ",
                            "example": "1,000.00"
                        }
                    ]
                }
                additional_instructions = 'ดึงข้อมูลจากใบกำกับภาษี โดยเน้นความถูกต้องของตัวเลขและวันที่'
                
                # Prepare payload สำหรับ key-extract
                if is_pp30:
                    # สำหรับ ภ.พ.30 ไม่ต้องใช้ listConfig (ไม่มีรายการสินค้า)
                    payload = {
                        'customFields': json.dumps(custom_fields),
                        'model': 'aksonocr-1.0',
                        'additionalInstructions': additional_instructions
                    }
                else:
                    # สำหรับใบกำกับภาษีทั่วไป ใช้ listConfig สำหรับรายการสินค้า
                    payload = {
                        'customFields': json.dumps(custom_fields),
                        'model': 'aksonocr-1.0',
                        'listConfig': json.dumps(list_config),
                        'additionalInstructions': additional_instructions
                    }
                
                # Format: {"file": (filename, file, mime_type)} - ระบุ filename และ mime_type
                files = {
                    "file": (filename, file, mime_type)
                }
                # Header: X-API-Key (ตาม test_aksonocr.py)
                headers = {
                    "X-API-Key": api_key
                }
                
                logger.info(f"📤 [AksonOCR] ส่งไฟล์: {filename} (size: {file_path.stat().st_size} bytes) - Mode: key-extract")
                logger.debug(f"📤 [AksonOCR] API URL: {url}")
                logger.debug(f"📤 [AksonOCR] Headers: X-API-Key {api_key[:10]}...")
                logger.debug(f"📤 [AksonOCR] Payload: model={payload['model']}, customFields={len(custom_fields)} fields")
                logger.debug(f"📤 [AksonOCR] Files: file={filename}, mime_type={mime_type}")
            else:
                # ใช้รูปแบบจาก test_aksonocr_v2.py (/api/v2/upload)
                # Format: {"file": (filename, file, mime_type)} - ระบุ filename และ mime_type
                files = {
                    "file": (filename, file, mime_type)
                }
                # Data: {"model": "aksonocr-1.0"} (ตาม test_aksonocr_v2.py)
                data = {"model": "aksonocr-1.0"}
                # Header: X-API-Key (ตาม test_aksonocr_v2.py)
                headers = {
                    "X-API-Key": api_key
                }
                
                logger.info(f"📤 [AksonOCR] ส่งไฟล์: {filename} (size: {file_path.stat().st_size} bytes) - Mode: v2/upload")
                logger.debug(f"📤 [AksonOCR] API URL: {url}")
                logger.debug(f"📤 [AksonOCR] Headers: X-API-Key {api_key[:10]}...")
                logger.debug(f"📤 [AksonOCR] Data: model={data['model']}")
                logger.debug(f"📤 [AksonOCR] Files: file={filename}, mime_type={mime_type}")
            
            # Retry logic สำหรับ rate limiting (429)
            max_retries = 3
            retry_delay = 2  # เริ่มต้นที่ 2 วินาที
            response = None
            
            try:
                for attempt in range(max_retries):
                    try:
                        # เพิ่ม delay ระหว่าง requests เพื่อลดโอกาสเกิด rate limit
                        if attempt > 0:
                            wait_time = retry_delay * (2 ** (attempt - 1))  # Exponential backoff: 2s, 4s, 8s
                            logger.warning(f"⏳ [AksonOCR] รอ {wait_time} วินาที ก่อน retry (ครั้งที่ {attempt + 1}/{max_retries})...")
                            time.sleep(wait_time)
                        else:
                            # เพิ่ม delay เล็กน้อยก่อน request แรกเพื่อลดโอกาสเกิด rate limit
                            time.sleep(0.5)
                        
                        # กำหนด timeout ตาม ocr_mode
                        # key-extract อาจใช้เวลานานกว่าเพราะต้อง extract ข้อมูลหลาย field
                        request_timeout = 180 if use_key_extract else 120  # key-extract: 180s, v2/upload: 120s
                        logger.info(f"⏱️ [AksonOCR] ตั้งค่า timeout: {request_timeout} วินาที (mode: {ocr_mode}, attempt: {attempt + 1}/{max_retries})")
                        
                        if use_key_extract:
                            # สำหรับ key-extract ใช้ data=payload แทน data=data
                            response = requests.post(url, headers=headers, files=files, data=payload, timeout=request_timeout)
                        else:
                            # สำหรับ v2/upload ใช้ data=data
                            response = requests.post(url, headers=headers, files=files, data=data, timeout=request_timeout)
                        
                        logger.info(f"✅ [AksonOCR] API response received: {response.status_code}")
                        
                        # ถ้าเป็น 200 หรือ 201 ให้ออกจาก retry loop (สำเร็จ)
                        if response.status_code in [200, 201]:
                            break
                        
                        # ถ้าเป็น 429 (Rate Limit) หรือ 500 (Server Error) และยังมี retry ครั้งเหลือ ให้ retry
                        if (response.status_code == 429 or response.status_code == 500) and attempt < max_retries - 1:
                            try:
                                error_data = response.json()
                                if response.status_code == 429:
                                    error_message = error_data.get('error', {}).get('message', '') if isinstance(error_data, dict) else ''
                                    logger.warning(f"⚠️ [AksonOCR] Rate limit exceeded (429): {error_message} - จะ retry ในครั้งถัดไป")
                                elif response.status_code == 500:
                                    error_code = error_data.get('error', {}).get('code', 'UNKNOWN') if isinstance(error_data, dict) else 'UNKNOWN'
                                    error_message = error_data.get('error', {}).get('message', '') if isinstance(error_data, dict) else ''
                                    logger.warning(f"⚠️ [AksonOCR] Server error (500): [{error_code}] {error_message} - จะ retry ในครั้งถัดไป")
                            except:
                                if response.status_code == 429:
                                    logger.warning(f"⚠️ [AksonOCR] Rate limit exceeded (429) - จะ retry ในครั้งถัดไป")
                                elif response.status_code == 500:
                                    logger.warning(f"⚠️ [AksonOCR] Server error (500) - จะ retry ในครั้งถัดไป")
                            continue
                        else:
                            # ไม่มี retry ครั้งเหลือแล้ว หรือเป็น error อื่นๆ
                            break
                    except requests.exceptions.Timeout as e:
                        if attempt < max_retries - 1:
                            logger.warning(f"⚠️ [AksonOCR] Request timeout - จะ retry ในครั้งถัดไป")
                            continue
                        else:
                            logger.error(f"❌ [AksonOCR] Request timeout หลังจาก {request_timeout} วินาที: {e}")
                            logger.warning(f"⚠️ [AksonOCR] จะ fallback ไปใช้ TYPHOON OCR")
                            return {
                                'text': None,
                                'tables': [],
                                'numbers': [],
                                'raw_content': None,
                                'error': f'AksonOCR timeout after {request_timeout}s'
                            }
                    except requests.exceptions.RequestException as e:
                        if attempt < max_retries - 1:
                            logger.warning(f"⚠️ [AksonOCR] Network error - จะ retry ในครั้งถัดไป: {e}")
                            continue
                        else:
                            logger.error(f"❌ [AksonOCR] Network error: {e}")
                            logger.warning(f"⚠️ [AksonOCR] จะ fallback ไปใช้ TYPHOON OCR")
                            return {
                                'text': None,
                                'tables': [],
                                'numbers': [],
                                'raw_content': None,
                                'error': f'AksonOCR network error: {e}'
                            }
            except Exception as e:
                logger.error(f"❌ [AksonOCR] Unexpected error: {e}")
                logger.warning(f"⚠️ [AksonOCR] จะ fallback ไปใช้ TYPHOON OCR")
                return {
                    'text': None,
                    'tables': [],
                    'numbers': [],
                    'raw_content': None,
                    'error': f'AksonOCR network error: {e}'
                }
            
            # รองรับ status code 200 และ 201 (201 Created = สำเร็จ)
            if response.status_code not in [200, 201]:
                # จัดการ 429 Rate Limit Error
                if response.status_code == 429:
                    error_message = 'เกินจำนวน request ที่อนุญาต กรุณาลองใหม่ในภายหลัง'
                    logger.error(f"❌ [AksonOCR] Rate limit exceeded (429): {error_message}")
                    return {
                        'text': None,
                        'tables': [],
                        'numbers': [],
                        'raw_content': None,
                        'error': error_message,
                        'error_code': 429
                    }
                
                # พยายาม parse error response สำหรับ error อื่นๆ
                error_details = None
                response_body = None
                try:
                    response_body = response.text
                    error_data = response.json()
                    if isinstance(error_data, dict):
                        error_message = error_data.get('error', {}).get('message', '') if isinstance(error_data.get('error'), dict) else error_data.get('error', '')
                        error_code = error_data.get('error', {}).get('code', 'UNKNOWN') if isinstance(error_data.get('error'), dict) else 'UNKNOWN'
                        error_details = f"[{error_code}] {error_message}"
                        # แสดง response body เต็มๆ เพื่อ debug
                        logger.error(f"❌ [AksonOCR] Full response body: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                    else:
                        error_details = str(error_data)
                        logger.error(f"❌ [AksonOCR] Full response body: {response_body}")
                except Exception as e:
                    error_details = response.text[:500] if response.text else 'No error message'
                    logger.error(f"❌ [AksonOCR] Failed to parse error response: {e}")
                    logger.error(f"❌ [AksonOCR] Raw response text: {response.text[:1000] if response.text else 'No response text'}")
                
                logger.error(f"❌ [AksonOCR] API Error ({response.status_code}): {error_details}")
                logger.error(f"❌ [AksonOCR] Response headers: {dict(response.headers)}")
                logger.error(f"❌ [AksonOCR] Request URL: {url}")
                logger.error(f"❌ [AksonOCR] Request headers: {dict(headers)}")
                logger.error(f"❌ [AksonOCR] File: {filename}, Size: {file_path.stat().st_size} bytes")
                
                return {
                    'text': None,
                    'tables': [],
                    'numbers': [],
                    'raw_content': None,
                    'error': f'AksonOCR API failed: {response.status_code} - {error_details}'
                }
        
        # ประมวลผล response จาก /api/v2/upload (รองรับทั้ง 200 และ 201)
        if response.status_code in [200, 201]:
            try:
                result = response.json()
                logger.debug(f"✅ [AksonOCR] Response structure: {list(result.keys())}")
                logger.debug(f"✅ [AksonOCR] Response preview: {str(result)[:500]}")
                
                # Extract text from response
                all_texts = []
                all_tables = []
                all_numbers = []
                raw_contents = []
                
                # รูปแบบหลัก: มี 'pages' (ตาม test_aksonocr_v2.py - /api/v2/upload)
                if 'pages' in result:
                    for page in result.get('pages', []):
                        if isinstance(page, dict):
                            # ดึง markdown ถ้ามี
                            markdown_text = page.get('markdown', '')
                            if markdown_text:
                                all_texts.append(markdown_text)
                                raw_contents.append(markdown_text)
                            
                            # ดึง text ถ้ามี (ถ้าไม่มี markdown)
                            elif 'text' in page:
                                text = page.get('text', '')
                                if text:
                                    all_texts.append(text)
                                    raw_contents.append(text)
                            
                            # Extract numbers from markdown/text
                            page_text = markdown_text or page.get('text', '')
                            if page_text:
                                number_pattern = r'\d+\.?\d*'
                                found_numbers = re.findall(number_pattern, page_text)
                                for num_str in found_numbers:
                                    try:
                                        num_value = float(num_str) if '.' in num_str else int(num_str)
                                        if num_value > 0 and num_value not in all_numbers:
                                            all_numbers.append(num_value)
                                    except ValueError:
                                        pass
                
                # รูปแบบรอง: มี 'success' และ 'data' (key-extract API)
                elif result.get('success') and 'data' in result:
                    data = result.get('data', {})
                    logger.info(f"📊 [AksonOCR] Key-extract API response received")
                    logger.info(f"📊 [AksonOCR] Data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                    
                    if isinstance(data, dict):
                        # Log ข้อมูลดิบก่อนทำความสะอาด
                        logger.info(f"📊 [AksonOCR] Raw data (before cleaning):")
                        for key, value in data.items():
                            if value:  # แสดงเฉพาะค่าที่ไม่ว่าง
                                logger.info(f"   - {key}: {value}")
                        
                        # สำหรับ key-extract API: เก็บ JSON response ทั้งหมดไว้ใน raw_content
                        # และแปลงเป็น text format สำหรับ text field
                        
                        # ทำความสะอาดข้อมูล (ลบ emoji และ whitespace ที่ไม่จำเป็น)
                        cleaned_data = _clean_key_extract_data(data)
                        
                        logger.info(f"📊 [AksonOCR] Cleaned data (after cleaning):")
                        logger.info(f"📊 [AksonOCR] Cleaned data keys: {list(cleaned_data.keys())}")
                        for key, value in cleaned_data.items():
                            if value:  # แสดงเฉพาะค่าที่ไม่ว่าง
                                logger.info(f"   - {key}: {value}")
                        
                        # เก็บ JSON response ทั้งหมด (รวม confidence และ metadata)
                        full_response_json = {
                            'success': result.get('success', True),
                            'data': cleaned_data,
                            'confidence': result.get('confidence'),
                            'fieldConfidences': result.get('fieldConfidences', []),
                            'processingTimeMs': result.get('processingTimeMs'),
                            'creditCost': result.get('creditCost')
                        }
                        
                        # Format JSON ให้สวยงาม
                        formatted_json = json.dumps(full_response_json, ensure_ascii=False, indent=2)
                        raw_contents.append(formatted_json)
                        
                        # แปลง structured data เป็น text format สำหรับ text field
                        # ตรวจสอบว่าเป็น ภ.พ.30 หรือไม่
                        doc_type = cleaned_data.get('ประเภทเอกสาร', '')
                        is_pp30_doc = ('ภ.พ.30' in doc_type or 'ภพ.30' in doc_type or 
                                      'แบบแสดงรายการภาษีมูลค่าเพิ่ม' in doc_type or
                                      'PP30' in doc_type.upper())
                        
                        if is_pp30_doc:
                            # ใช้ฟังก์ชันจัดรูปแบบเฉพาะสำหรับ ภ.พ.30
                            extracted_text = _format_pp30_data(cleaned_data)
                            if extracted_text:
                                all_texts.append(extracted_text)
                        else:
                            # สำหรับเอกสารอื่นๆ ใช้รูปแบบเดิม
                            text_parts = []
                            
                            # ดึงข้อมูลหัวบิลด์ (Document Header) - เรียงลำดับตามที่ผู้ใช้ต้องการ
                            if 'ประเภทเอกสาร' in cleaned_data:
                                doc_type = cleaned_data.get('ประเภทเอกสาร', '')
                                if doc_type:
                                    text_parts.append(f"ประเภทเอกสาร: {doc_type}")
                            if 'สถานะเอกสาร' in cleaned_data:
                                doc_status = cleaned_data.get('สถานะเอกสาร', '')
                                if doc_status:
                                    text_parts.append(f"สถานะเอกสาร: {doc_status}")
                            # ไม่แสดง "รูปแบบเอกสาร" ถ้าเป็น null (จะถูกลบออกโดย _clean_key_extract_data แล้ว)
                            
                            # ดึงข้อมูลพื้นฐาน
                            if 'invoice_number' in cleaned_data or 'เลขที่ใบกำกับภาษี' in cleaned_data:
                                invoice_num = cleaned_data.get('invoice_number') or cleaned_data.get('เลขที่ใบกำกับภาษี', '')
                                if invoice_num:
                                    text_parts.append(f"เลขที่ใบกำกับภาษี: {invoice_num}")
                            if 'invoice_date' in cleaned_data or 'receipt_date' in cleaned_data or 'วันที่' in cleaned_data:
                                date = cleaned_data.get('invoice_date') or cleaned_data.get('receipt_date') or cleaned_data.get('วันที่', '')
                                if date:
                                    text_parts.append(f"วันที่: {date}")
                            
                            # ดึงข้อมูลผู้ขาย (เรียงลำดับ: ชื่อ, เลขประจำตัวผู้เสียภาษี, ที่อยู่)
                            if 'company_name' in cleaned_data or 'ชื่อผู้ขาย' in cleaned_data:
                                company_name = cleaned_data.get('company_name') or cleaned_data.get('ชื่อผู้ขาย', '')
                                if company_name:
                                    text_parts.append(f"ชื่อผู้ขาย: {company_name}")
                            if 'tax_id' in cleaned_data or 'เลขประจำตัวผู้เสียภาษี' in cleaned_data or 'เลขประจำตัวผู้เสียภาษี - ผู้ขาย' in cleaned_data:
                                # รองรับทั้งรูปแบบเก่าและใหม่
                                tax_id_seller = cleaned_data.get('เลขประจำตัวผู้เสียภาษี - ผู้ขาย') or cleaned_data.get('tax_id') or cleaned_data.get('เลขประจำตัวผู้เสียภาษี', '')
                                if tax_id_seller:
                                    text_parts.append(f"เลขประจำตัวผู้เสียภาษี - ผู้ขาย: {tax_id_seller}")
                            if 'ที่อยู่ผู้ขาย' in cleaned_data:
                                seller_address = cleaned_data.get('ที่อยู่ผู้ขาย', '')
                                if seller_address:
                                    text_parts.append(f"ที่อยู่ผู้ขาย: {seller_address}")
                            
                            # ดึงข้อมูลผู้ซื้อ (เรียงลำดับ: ชื่อ, เลขประจำตัวผู้เสียภาษี, ที่อยู่)
                            if 'ชื่อผู้ซื้อ' in cleaned_data:
                                buyer_name = cleaned_data.get('ชื่อผู้ซื้อ', '')
                                if buyer_name:
                                    text_parts.append(f"ชื่อผู้ซื้อ: {buyer_name}")
                            if 'เลขประจำตัวผู้เสียภาษี - ผู้ซื้อ' in cleaned_data:
                                tax_id_buyer = cleaned_data.get('เลขประจำตัวผู้เสียภาษี - ผู้ซื้อ', '')
                                if tax_id_buyer:
                                    text_parts.append(f"เลขประจำตัวผู้เสียภาษี - ผู้ซื้อ: {tax_id_buyer}")
                            if 'ที่อยู่ผู้ซื้อ' in cleaned_data:
                                buyer_address = cleaned_data.get('ที่อยู่ผู้ซื้อ', '')
                                if buyer_address:
                                    text_parts.append(f"ที่อยู่ผู้ซื้อ: {buyer_address}")
                            
                            # ดึงยอดเงิน (ลบสัญลักษณ์ "฿" ออก)
                            if 'sub_total' in cleaned_data or 'ยอดรวมก่อนภาษี' in cleaned_data:
                                sub_total = cleaned_data.get('sub_total') or cleaned_data.get('ยอดรวมก่อนภาษี', '')
                                if sub_total:
                                    # ลบสัญลักษณ์ "฿" และ "THB" ออก
                                    sub_total_clean = sub_total.replace('฿', '').replace('THB', '').replace('thb', '').strip()
                                    text_parts.append(f"ยอดรวมก่อนภาษี: {sub_total_clean}")
                            if 'vat_7' in cleaned_data or 'ภาษีมูลค่าเพิ่ม' in cleaned_data:
                                vat = cleaned_data.get('vat_7') or cleaned_data.get('ภาษีมูลค่าเพิ่ม', '')
                                if vat:
                                    # ลบสัญลักษณ์ "฿" และ "THB" ออก
                                    vat_clean = vat.replace('฿', '').replace('THB', '').replace('thb', '').strip()
                                    text_parts.append(f"ภาษีมูลค่าเพิ่ม: {vat_clean}")
                            if 'net_total' in cleaned_data or 'ยอดรวมสุทธิ' in cleaned_data:
                                net_total = cleaned_data.get('net_total') or cleaned_data.get('ยอดรวมสุทธิ', '')
                                if net_total:
                                    # ลบสัญลักษณ์ "฿" และ "THB" ออก
                                    net_total_clean = net_total.replace('฿', '').replace('THB', '').replace('thb', '').strip()
                                    text_parts.append(f"ยอดรวมสุทธิ: {net_total_clean}")
                            if 'withholding_tax' in cleaned_data:
                                wht = cleaned_data.get('withholding_tax', '')
                                if wht:
                                    # ลบสัญลักษณ์ "฿" และ "THB" ออก
                                    wht_clean = wht.replace('฿', '').replace('THB', '').replace('thb', '').strip()
                                    text_parts.append(f"หักภาษี ณ ที่จ่าย: {wht_clean}")
                            
                            # ดึงรายการสินค้า/บริการ
                            items = cleaned_data.get('items') or cleaned_data.get('รายการสินค้า', [])
                            if items and isinstance(items, list):
                                text_parts.append("\nรายการสินค้า/บริการ:")
                                for item in items:
                                    if isinstance(item, dict):
                                        desc = item.get('description') or item.get('รายการ', '')
                                        amount = item.get('amount') or item.get('จำนวนเงิน', '')
                                        if desc or amount:
                                            item_text = f"  - {desc}: {amount}"
                                            text_parts.append(item_text)
                            
                            # รวมข้อความทั้งหมด
                            extracted_text = '\n'.join(text_parts)
                            if extracted_text:
                                all_texts.append(extracted_text)
                            else:
                                # ถ้าไม่มี text_parts ให้ใช้ JSON แทน
                                all_texts.append(formatted_json)
                                
                            # Extract numbers จากข้อมูล
                            for key, value in cleaned_data.items():
                                if isinstance(value, str):
                                    # ลบ emoji, สัญลักษณ์ "฿", และ whitespace
                                    value_clean = re.sub(r'[💰🏢]', '', value)
                                    value_clean = value_clean.replace('฿', '').replace('THB', '').replace('thb', '')
                                    value_clean = value_clean.replace(',', '').replace(' ', '').strip()
                                    # ลองแปลงเป็นตัวเลข
                                    try:
                                        num_value = float(value_clean) if '.' in value_clean else int(value_clean)
                                        if num_value > 0 and num_value not in all_numbers:
                                            all_numbers.append(num_value)
                                    except ValueError:
                                        pass
                                elif isinstance(value, (int, float)) and value > 0:
                                    if value not in all_numbers:
                                        all_numbers.append(value)
                                
                                # Extract numbers จากรายการสินค้า
                                if key in ['items', 'รายการสินค้า'] and isinstance(value, list):
                                    for item in value:
                                        if isinstance(item, dict):
                                            for item_key, item_value in item.items():
                                                if isinstance(item_value, str):
                                                    item_value_clean = re.sub(r'[💰🏢]', '', item_value).replace(',', '').replace(' ', '').strip()
                                                    try:
                                                        num_value = float(item_value_clean) if '.' in item_value_clean else int(item_value_clean)
                                                        if num_value > 0 and num_value not in all_numbers:
                                                            all_numbers.append(num_value)
                                                    except ValueError:
                                                        pass
                
                
                # รูปแบบ 3: มี 'markdown' โดยตรง
                elif 'markdown' in result:
                    markdown_text = result.get('markdown', '')
                    if markdown_text:
                        all_texts.append(markdown_text)
                        raw_contents.append(markdown_text)
                
                # รูปแบบ 4: มี 'text' โดยตรง
                elif 'text' in result:
                    text = result.get('text', '')
                    if text:
                        all_texts.append(text)
                        raw_contents.append(text)
                
                # ถ้ายังไม่มีข้อความ ให้ใช้ response ทั้งหมดเป็น text
                if not all_texts:
                    logger.warning(f"⚠️ [AksonOCR] ไม่พบข้อความใน response - ใช้ response ทั้งหมด")
                    response_str = json.dumps(result, ensure_ascii=False, indent=2)
                    all_texts.append(response_str)
                    raw_contents.append(response_str)
                
                # Extract numbers จากข้อความทั้งหมด
                if all_texts:
                    full_text = '\n'.join(all_texts)
                    number_pattern = r'\d+\.?\d*'
                    found_numbers = re.findall(number_pattern, full_text)
                    for num_str in found_numbers:
                        try:
                            num_value = float(num_str) if '.' in num_str else int(num_str)
                            if num_value not in all_numbers:
                                all_numbers.append(num_value)
                        except ValueError:
                            pass
                
                # Try to extract tables from markdown (if structured)
                # Markdown tables are in format: | col1 | col2 |
                markdown_table_pattern = r'\|[^\n]+\|'
                if all_texts:
                    full_text = '\n'.join(all_texts)
                    table_matches = re.findall(markdown_table_pattern, full_text)
                    if table_matches:
                        # Parse markdown tables
                        for match in table_matches:
                            cells = [cell.strip() for cell in match.split('|') if cell.strip()]
                            if cells:
                                all_tables.append(cells)
                
                logger.info(f"✅ [AksonOCR] อ่านข้อมูลสำเร็จ: {len(all_texts)} หน้า, {len(''.join(all_texts))} ตัวอักษร")
                
                return {
                    'text': '\n'.join(all_texts) if all_texts else '',
                    'tables': all_tables,
                    'numbers': all_numbers,
                    'raw_content': '\n\n---\n\n'.join(raw_contents) if raw_contents else ''
                }
            except json.JSONDecodeError as e:
                logger.error(f"❌ AksonOCR: ไม่สามารถ parse JSON response ได้: {e}")
                logger.error(f"Response text: {response.text[:500]}")
                return {
                    'text': None,
                    'tables': [],
                    'numbers': [],
                    'raw_content': None,
                    'error': f'JSON decode error: {e}'
                }
        else:
            # พยายาม parse error response
            try:
                error_data = response.json()
                error_message = error_data.get('error', {}).get('message', response.text) if isinstance(error_data, dict) else response.text
                logger.error(f"❌ AksonOCR API Error: {response.status_code} - {error_message}")
            except:
                logger.error(f"❌ AksonOCR API Error: {response.status_code} - {response.text}")
            
            return {
                'text': None,
                'tables': [],
                'numbers': [],
                'raw_content': None,
                'error': f'AksonOCR API Error: {response.status_code}'
            }
    except Exception as e:
        logger.error(f"❌ AksonOCR Error: {e}", exc_info=True)
        return {
            'text': None,
            'tables': [],
            'numbers': [],
            'raw_content': None,
            'error': str(e)
        }


def extract_text_from_image(
    image_path: str, 
    api_key: str, 
    model: str, 
    task_type: str, 
    max_tokens: int, 
    temperature: float, 
    top_p: float, 
    repetition_penalty: float, 
    pages: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Extract text, tables, and numbers from image/PDF using OCR API.
        
        Returns:
        Dictionary containing:
        - 'text': Natural text content
        - 'tables': List of tables (if any)
        - 'numbers': List of extracted numbers (if any)
        - 'raw_content': Raw API response content
    """
    url = "https://api.opentyphoon.ai/v1/ocr"

    with open(image_path, 'rb') as file:
        files = {'file': file}
        data = {
            'model': model,
            'task_type': task_type,
            'max_tokens': str(max_tokens),
            'temperature': str(temperature),
            'top_p': str(top_p),
            'repetition_penalty': str(repetition_penalty)
        }

        if pages:
            data['pages'] = json.dumps(pages)

        headers = {
            'Authorization': f'Bearer {api_key}'
        }

        response = requests.post(url, files=files, data=data, headers=headers)

        if response.status_code == 200:
            result = response.json()

            # Extract text, tables, and numbers from successful results
            all_texts = []
            all_tables = []
            all_numbers = []
            raw_contents = []

            for page_result in result.get('results', []):
                if page_result.get('success') and page_result.get('message'):
                    content = page_result['message']['choices'][0]['message']['content']
                    raw_contents.append(content)
                    
                    try:
                        # Try to parse as JSON if it's structured output
                        parsed_content = json.loads(content)
                        
                        # Extract natural text
                        text = parsed_content.get('natural_text', '')
                        if text:
                            all_texts.append(text)
                        
                        # Extract tables if available
                        if 'tables' in parsed_content:
                            tables = parsed_content['tables']
                            if isinstance(tables, list):
                                all_tables.extend(tables)
                            else:
                                all_tables.append(tables)
                        
                        # Extract numbers if available (could be in various formats)
                        if 'numbers' in parsed_content:
                            numbers = parsed_content['numbers']
                            if isinstance(numbers, list):
                                all_numbers.extend(numbers)
                            else:
                                all_numbers.append(numbers)
                        
                        # If no natural_text but content exists, use content directly
                        if not text and isinstance(parsed_content, str):
                            all_texts.append(parsed_content)
                        elif not text:
                            # Try to extract text from other fields
                            if 'text' in parsed_content:
                                all_texts.append(str(parsed_content['text']))
                            elif 'content' in parsed_content:
                                all_texts.append(str(parsed_content['content']))
                            else:
                                # Use entire parsed content as text
                                all_texts.append(json.dumps(parsed_content, ensure_ascii=False, indent=2))
                        
                        # Look for numbers in text by checking numeric patterns
                        if text:
                            # Find all numbers (integers and decimals) in text
                            number_pattern = r'\d+\.?\d*'
                            found_numbers = re.findall(number_pattern, text)
                            for num_str in found_numbers:
                                try:
                                    num_value = float(num_str) if '.' in num_str else int(num_str)
                                    if num_value not in all_numbers:
                                        all_numbers.append(num_value)
                                except ValueError:
                                    pass
                        
                    except json.JSONDecodeError:
                        # If not JSON, treat as plain text
                        all_texts.append(content)
                        
                        # Extract numbers from plain text
                        number_pattern = r'\d+\.?\d*'
                        found_numbers = re.findall(number_pattern, content)
                        for num_str in found_numbers:
                            try:
                                num_value = float(num_str) if '.' in num_str else int(num_str)
                                if num_value not in all_numbers:
                                    all_numbers.append(num_value)
                            except ValueError:
                                pass
                                
                elif not page_result.get('success'):
                    print(f"Error processing {page_result.get('filename', 'unknown')}: {page_result.get('error', 'Unknown error')}")

            return {
                'text': '\n'.join(all_texts),
                'tables': all_tables,
                'numbers': all_numbers,
                'raw_content': '\n\n---\n\n'.join(raw_contents)
            }
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return {
                'text': None,
                'tables': [],
                'numbers': [],
                'raw_content': None
            }

# Usage
if __name__ == "__main__":
    api_key = "sk-fvOVV7K2bHQ39bBfvFoT5TwoxPpReDLKEDjMwXHZwxUzpf3J"
    image_path = "V:/A.โฟร์เดอร์หลัก/Build000 ทดสอบระบบ/ทดสอบ ocr I3/แบบร่าง ภ.พ.30 เดือน 10_68.pdf"
    model = "typhoon-ocr"
    task_type = "v1.5"
    max_tokens = 2000  # ลดลงจาก 16000 เพื่อความเร็ว
    temperature = 0.1
    top_p = 0.6
    repetition_penalty = 1.1
    pages = [1]
    
    result = extract_text_from_image(
        image_path, api_key, model, task_type, 
        max_tokens, temperature, top_p, repetition_penalty, pages
    )
    
    # Display formatted results
    print("\n" + "=" * 100)
    print("ผลการดึงข้อมูลจากเอกสาร (OCR RESULT)")
    print("=" * 100)
    
    # Format and display text with tables
    formatted_text = format_text_output(result['text'])
    if formatted_text:
        print("\n" + formatted_text)
    
    # Display extracted tables (if any structured tables found)
    if result['tables']:
        print("\n" + "-" * 100)
        print("ตารางที่ดึงได้ (EXTRACTED TABLES):")
        print("-" * 100)
        for i, table in enumerate(result['tables'], 1):
            print(f"\n[ตาราง {i} / Table {i}]")
            if isinstance(table, list) and isinstance(table[0], list):
                formatted_table = format_table(table)
                print(formatted_table)
            else:
                print(json.dumps(table, ensure_ascii=False, indent=2))
    
    # Display extracted numbers
    if result['numbers']:
        print("\n" + "-" * 100)
        print("ตัวเลขที่ดึงได้ (EXTRACTED NUMBERS):")
        print("-" * 100)
        # Format numbers with commas
        formatted_numbers = []
        for num in result['numbers']:
            if isinstance(num, (int, float)):
                if isinstance(num, float):
                    formatted_numbers.append(f"{num:,.2f}")

                else:
                    formatted_numbers.append(f"{num:,}")
            else:
                formatted_numbers.append(str(num))
        print(", ".join(formatted_numbers))
    
    print("\n" + "=" * 100)
    
    # Optional: Save results to JSON file
    # with open('ocr_result.json', 'w', encoding='utf-8') as f:
    #     json.dump(result, f, ensure_ascii=False, indent=2)


# ===== TaxOCRResult Class =====
class TaxOCRResult:
    """
    คลาสสำหรับเก็บและจัดการข้อมูล OCR Result
    
    ตัวอย่างการใช้งาน:
        # วิธีที่ 1: ใช้ extract_tax_data
        processor = TaxOCRProcessor()
        result = processor.extract_tax_data(Path("file.pdf"))
        
        # วิธีที่ 2: ใช้ extract_tax_amounts with return_result_object=True
        result = processor.extract_tax_amounts(Path("file.pdf"), return_result_object=True)
        
        # วิธีที่ 3: ใช้ helper function
        result = extract_tax_data_from_pdf("file.pdf")
        
        # ดึงข้อมูล
        company_name = result.get_company_name()
        tax_id = result.get_tax_id(formatted=True)  # "01055-531144-37"
        filing_period = result.get_filing_period()  # "ประจำเดือน ตุลาคม/2568"
        amount = result.get_amount('รวมยอดภาษีที่นำส่งทั้งสิ้น')
        summary = result.get_tax_amounts_summary()
        
        # แปลงเป็น dictionary หรือ JSON
        data_dict = result.to_dict()
        json_str = result.to_json()
    """
    
    def __init__(self, data: Dict[str, Any]):
        """
        Initialize TaxOCRResult จาก dictionary
        
        Args:
            data: Dictionary ที่มีข้อมูล OCR result
        """
        self._data = data
        self.success = data.get('success', False)
        self.error = data.get('error', None)
        self.tax_form_type = data.get('tax_form_type', None)
        self.company_name = data.get('company_name', None)
        self.tax_id = data.get('tax_id', None)
        self.filing_type = data.get('filing_type', None)
        self.filing_period = data.get('filing_period', {'month': None, 'year': None})
        self.payment_date = data.get('payment_date', None)
        self.due_date = data.get('due_date', None)
        self.amounts = data.get('amounts', {})
        self.raw_text = data.get('raw_text', '')
        self.method = data.get('method', 'unknown')
        self.tables = data.get('tables', [])
    
    def get_raw_data(self) -> Dict[str, Any]:
        """ดึงข้อมูลดิบทั้งหมด"""
        return self._data.copy()
    
    def get_company_name(self) -> Optional[str]:
        """ดึงชื่อบริษัท"""
        return self.company_name
    
    def get_tax_id(self, formatted: bool = False) -> Optional[str]:
        """
        ดึงเลขประจำตัวผู้เสียภาษี
        
        Args:
            formatted: ถ้า True จะ format เป็นรูปแบบ XXXXX-XXXXX-XX-X (5-5-2-1)
        """
        if not self.tax_id:
            return None
        if formatted and len(self.tax_id) == 13:
            return f"{self.tax_id[:5]}-{self.tax_id[5:10]}-{self.tax_id[10:12]}-{self.tax_id[12:]}"
        return self.tax_id
    
    def get_filing_period(self, format_str: str = None) -> Optional[str]:
        """
        ดึงระยะเวลาการยื่นแบบ
        
        Args:
            format_str: รูปแบบการ format (เช่น "ประจำเดือน {month}/{year}")
        """
        if not self.filing_period or not self.filing_period.get('month') or not self.filing_period.get('year'):
            return None
        
        month = self.filing_period.get('month', '')
        year = self.filing_period.get('year', '')
        
        if format_str:
            return format_str.format(month=month, year=year)
        
        # Default format
        return f"ประจำเดือน {month}/{year}"
    
    def get_amount(self, key: str, default: float = 0.0) -> float:
        """
        ดึงยอดเงินตาม key
        
        Args:
            key: ชื่อ key ของยอดเงิน (เช่น 'รวมยอดภาษีที่นำส่งทั้งสิ้น')
            default: ค่า default ถ้าไม่พบ
        """
        return self.amounts.get(key, default)
    
    def get_all_amounts(self) -> Dict[str, float]:
        """ดึงยอดเงินทั้งหมด"""
        return self.amounts.copy()
    
    def get_tax_amounts_summary(self) -> Dict[str, float]:
        """
        ดึงยอดเงินที่สำคัญสำหรับสรุป
        
        Returns:
            Dictionary ที่มียอดเงินสำคัญ
        """
        summary = {}
        
        # ภ.ง.ด.53, ภ.ง.ด.1, ภ.ง.ด.3
        if self.tax_form_type in ['ภ.ง.ด.53', 'ภ.ง.ด.1', 'ภ.ง.ด.3']:
            summary['รวมยอดภาษีที่นำส่งทั้งสิ้น'] = self.get_amount('รวมยอดภาษีที่นำส่งทั้งสิ้น', 0.0)
            summary['เงินเพิ่ม'] = self.get_amount('เงินเพิ่ม', 0.0)
            summary['รวมยอดภาษีที่นำส่งทั้งสิ้น และเงินเพิ่ม'] = self.get_amount('รวมยอดภาษีที่นำส่งทั้งสิ้น และเงินเพิ่ม', 0.0)
        
        # ภ.ง.ด.54
        elif self.tax_form_type == 'ภ.ง.ด.54':
            summary['รวมเป็นเงินทั้งสิ้น'] = self.get_amount('รวมเป็นเงินทั้งสิ้น', 0.0)
        
        # ภ.พ.36
        elif self.tax_form_type == 'ภ.พ.36':
            summary['จำนวนเงินภาษีมูลค่าเพิ่มที่ต้องนำส่ง'] = self.get_amount('จำนวนเงินภาษีมูลค่าเพิ่มที่ต้องนำส่ง', 0.0)
        
        # ภ.พ.30
        elif self.tax_form_type == 'ภ.พ.30':
            summary['ต้องชำระ (ภ.พ.30)'] = self.get_amount('ต้องชำระ (ภ.พ.30)', 0.0)
            summary['ชำระเกิน (ภ.พ.30)'] = self.get_amount('ชำระเกิน (ภ.พ.30)', 0.0)
        
        # ประกันสังคม
        elif self.tax_form_type == 'ประกันสังคม':
            summary['รวมเงินสมทบที่นำส่งทั้งสิ้น'] = self.get_amount('รวมเงินสมทบที่นำส่งทั้งสิ้น', 0.0)
        
        # กองทุน กยศ.
        elif self.tax_form_type == 'กองทุน กยศ.':
            summary['ยอดชำระ (บาท)'] = self.get_amount('ยอดชำระ (บาท)', 0.0)
        
        # Pay-In Slip
        elif 'Pay-In' in self.tax_form_type or 'Pay-in' in self.tax_form_type:
            summary['ยอดชำระ (บาท)'] = self.get_amount('ยอดชำระ (บาท)', 0.0)
        
        return summary
    
    def format_pp30_amounts(self) -> str:
        """
        จัดรูปแบบ amounts สำหรับ ภ.พ.30 ให้แสดงผลแบบแนวตั้งทีละบรรทัด
        
        Returns:
            ข้อความที่จัดรูปแบบแล้ว แสดงทีละบรรทัดตามลำดับ 1-16
        """
        if self.tax_form_type != 'ภ.พ.30':
            return ""
        
        # รายการข้อ 1-16 พร้อมคำอธิบาย
        items = [
            (1, 'ยอดขายในเดือนนี้ (ภ.พ.30)', 'ยอดขายในเดือนนี้'),
            (2, 'ยอดขายที่เสียภาษีในอัตราร้อยละ 0 (ภ.พ.30)', 'ลบ ยอดขายที่เสียภาษีในอัตราร้อยละ 0'),
            (3, 'ยอดขายที่ได้รับยกเว้น (ภ.พ.30)', 'ลบ ยอดขายที่ได้รับยกเว้น'),
            (4, 'ยอดขายที่ต้องเสียภาษี (ภ.พ.30)', 'ยอดขายที่ต้องเสียภาษี (1. - 2. - 3.)'),
            (5, 'ภาษีขายเดือนนี้ (ภ.พ.30)', 'ภาษีขายเดือนนี้'),
            (6, 'ยอดซื้อที่มีสิทธินำภาษีซื้อ (ภ.พ.30)', 'ยอดซื้อที่มีสิทธินำภาษีซื้อ'),
            (7, 'ภาษีซื้อเดือนนี้ (ภ.พ.30)', 'ภาษีซื้อเดือนนี้'),
            (8, 'ภาษีที่ต้องชำระเดือนนี้ (ภ.พ.30)', 'ภาษีที่ต้องชำระเดือนนี้'),
            (9, 'ภาษีที่ชำระเกินเดือนนี้ (ภ.พ.30)', 'ภาษีที่ชำระเกินเดือนนี้'),
            (10, 'ภาษีที่ชำระเกินยกมา (ภ.พ.30)', 'ภาษีที่ชำระเกินยกมา'),
            (11, 'ต้องชำระ (ภ.พ.30)', 'ต้องชำระ'),
            (12, 'ชำระเกิน (ภ.พ.30)', 'ชำระเกิน'),
            (13, 'เงินเพิ่ม (ภ.พ.30)', 'เงินเพิ่ม'),
            (14, 'เบี้ยปรับ (ภ.พ.30)', 'เบี้ยปรับ'),
            (15, 'รวมภาษี เงินเพิ่ม และเบี้ยปรับที่ต้องชำระ (ภ.พ.30)', 'รวมภาษี เงินเพิ่ม และเบี้ยปรับที่ต้องชำระ'),
            (16, 'รวมภาษีที่ชำระเกิน หลังคำนวณเงินเพิ่มและเบี้ยปรับแล้ว (ภ.พ.30)', 'รวมภาษีที่ชำระเกิน หลังคำนวณเงินเพิ่มและเบี้ยปรับแล้ว'),
        ]
        
        formatted_lines = []
        
        for item_num, full_key, description in items:
            amount = self.get_amount(full_key, 0.0)
            
            # Format จำนวนเงิน
            if amount > 0:
                # Format เป็นตัวเลขที่มี comma และทศนิยม 2 ตำแหน่ง
                amount_str = f"{amount:,.2f}"
            else:
                amount_str = "-"
            
            # แสดงผลในรูปแบบ: "1. คำอธิบาย\n     จำนวนเงิน: 0.00"
            formatted_lines.append(f"{item_num}. {description}")
            formatted_lines.append(f"     จำนวนเงิน: {amount_str}")
        
        return "\n".join(formatted_lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """แปลงเป็น dictionary"""
        return {
            'success': self.success,
            'error': self.error,
            'tax_form_type': self.tax_form_type,
            'company_name': self.company_name,
            'tax_id': self.tax_id,
            'filing_type': self.filing_type,
            'filing_period': self.filing_period,
            'payment_date': self.payment_date,
            'due_date': self.due_date,
            'amounts': self.amounts,
            'raw_text': self.raw_text,
            'method': self.method,
            'tables': self.tables
        }
    
    def to_json(self) -> str:
        """แปลงเป็น JSON string"""
        import json
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    def __repr__(self) -> str:
        return f"TaxOCRResult(success={self.success}, tax_form_type={self.tax_form_type}, company_name={self.company_name})"


# ===== TaxOCRProcessor Class =====
class TaxOCRProcessor:
    """คลาสสำหรับประมวลผล OCR จากไฟล์แบบยื่นภาษี"""
    
    def __init__(self):
        # Import config สำหรับ API key
        try:
            from config import Config
            # AksonOCR Settings (Primary)
            self.akson_api_key = getattr(Config, 'AKSON_API_KEY', '')
            self.akson_api_url = getattr(Config, 'AKSON_API_URL', 'https://backend.aksonocr.com/api/v2/upload')
            self.akson_enabled = getattr(Config, 'AKSON_ENABLED', True)
            # TYPHOON OCR Settings (Fallback)
            self.typhoon_api_key = getattr(Config, 'TYPHOON_API_KEY', '')
            self.typhoon_api_url = getattr(Config, 'TYPHOON_API_URL', 'https://api.opentyphoon.ai/v1/ocr')
            self.typhoon_enabled = getattr(Config, 'TYPHOON_ENABLED', True)
        except ImportError:
            self.akson_api_key = ''
            self.akson_api_url = 'https://backend.aksonocr.com/api/v2/upload'
            self.akson_enabled = True
            self.typhoon_api_key = ''
            self.typhoon_api_url = 'https://api.opentyphoon.ai/v1/ocr'
            self.typhoon_enabled = True
        
        # ตรวจสอบว่ามี requests หรือไม่
        try:
            import requests
            self.requests_available = True
        except ImportError:
            self.requests_available = False
            logger.warning("⚠️ requests library ไม่พร้อมใช้งาน")
        
        # Import TaxFormParser
        try:
            from email_system.tax_form_parser import TaxFormParser
            self.parser = TaxFormParser()
        except ImportError:
            try:
                from tax_form_parser import TaxFormParser
                self.parser = TaxFormParser()
            except ImportError:
                logger.warning("⚠️ TaxFormParser ไม่พร้อมใช้งาน")
                self.parser = None
    
    def extract_tax_amounts(self, pdf_path: Path, return_result_object: bool = False) -> Dict[str, Any]:
        """
        อ่านข้อมูลยอดเงินจากไฟล์แบบยื่นภาษี
        
        Args:
            pdf_path: Path ของไฟล์ PDF แบบยื่นภาษี
            return_result_object: ถ้า True จะ return TaxOCRResult object แทน dictionary
            
        Returns:
            Dictionary หรือ TaxOCRResult object ที่มีข้อมูลยอดเงินที่อ่านได้
        """
        if not pdf_path.exists():
            error_result = {
                'success': False,
                'error': f'ไม่พบไฟล์: {pdf_path}'
            }
            if return_result_object:
                return TaxOCRResult(error_result)
            return error_result
        
        try:
            # ฟังก์ชันตรวจสอบว่า amounts ทั้งหมดเป็น 0.0 หรือไม่
            def all_amounts_zero(result: Dict[str, Any]) -> bool:
                """ตรวจสอบว่า amounts ทั้งหมดเป็น 0.0 หรือไม่"""
                if not result.get('success'):
                    return True  # ถ้าไม่สำเร็จ ถือว่าไม่มีข้อมูล
                amounts = result.get('amounts', {})
                if not amounts:
                    return True  # ถ้าไม่มี amounts ถือว่าไม่มีข้อมูล
                
                # ตรวจสอบว่าเป็นกรณี "ขอนำภาษีไปชำระในเดือนถัดไป" หรือไม่
                if amounts.get('__carry_forward__'):
                    logger.info("✅ ตรวจพบ flag '__carry_forward__' - เป็นกรณีไม่มียอดชำระจริง ไม่ต้อง retry")
                    return False  # ไม่ต้อง retry เพราะเป็นกรณีพิเศษ
                
                # ตรวจสอบว่าเป็น ภ.ง.ด.1 ที่มีคำว่า "สำหรับใบเสร็จรับเงิน" หรือไม่
                tax_form_type = result.get('tax_form_type', '') or ''
                raw_text = result.get('raw_text', '') or ''
                
                # ตรวจสอบว่าเป็น ภ.ง.ด.1 หรือไม่
                is_pnd1 = ('ภ.ง.ด.1' in tax_form_type or 'ภงด.1' in tax_form_type or 'ภงด1' in tax_form_type or 
                          'ภ.ง.ด.1' in raw_text or 'ภงด.1' in raw_text)
                
                # ตรวจสอบว่ามีคำว่า "สำหรับใบเสร็จรับเงิน" ใน raw_text หรือไม่
                has_receipt_text = 'สำหรับใบเสร็จรับเงิน' in raw_text
                
                if is_pnd1 and has_receipt_text:
                    logger.info("✅ ตรวจพบ ภ.ง.ด.1 ที่มีคำว่า 'สำหรับใบเสร็จรับเงิน' - ยอดเงิน 0.00 เป็นค่าที่ถูกต้อง ไม่ต้อง retry")
                    return False  # ไม่ต้อง retry เพราะเป็นกรณีพิเศษ (ยอดเงิน 0.00 ถูกต้อง)
                
                # ตรวจสอบว่าทุกค่าคือ 0.0 หรือไม่
                for key, value in amounts.items():
                    if key == '__carry_forward__':  # ข้าม flag พิเศษ
                        continue
                    if isinstance(value, (int, float)) and value > 0:
                        return False  # พบค่าที่ไม่ใช่ 0
                return True  # ทุกค่าเป็น 0.0
            
            # ลองใช้ AksonOCR ก่อน (Primary OCR Service)
            # สำหรับหน้า "ส่งเมลล์" อ่านรอบเดียว (ไม่ retry)
            if self.akson_enabled and self.akson_api_key and self.requests_available:
                result = self._extract_with_aksonocr(pdf_path, ocr_mode='v2/upload')  # ใช้ v2/upload สำหรับหน้า "ส่งเมลล์"
                if result.get('success'):
                    # ลบ flag พิเศษ '__carry_forward__' ก่อน return
                    if result.get('amounts') and '__carry_forward__' in result['amounts']:
                        del result['amounts']['__carry_forward__']
                    if return_result_object:
                        return TaxOCRResult(result)
                    return result
            
            # ถ้า AksonOCR ไม่สำเร็จหรือไม่มี ให้ใช้ TYPHOON OCR (Fallback)
            # สำหรับหน้า "ส่งเมลล์" อ่านรอบเดียว (ไม่ retry)
            if self.typhoon_enabled and self.typhoon_api_key and self.requests_available:
                result = self._extract_with_typhoon(pdf_path)
                if result.get('success'):
                    # ลบ flag พิเศษ '__carry_forward__' ก่อน return
                    if result.get('amounts') and '__carry_forward__' in result['amounts']:
                        del result['amounts']['__carry_forward__']
                    if return_result_object:
                        return TaxOCRResult(result)
                    return result
            
            # ถ้า TYPHOON ไม่สำเร็จหรือไม่มี ให้ใช้ PyPDF2
            # สำหรับหน้า "ส่งเมลล์" อ่านรอบเดียว (ไม่ retry)
            result = self._extract_with_pypdf2(pdf_path)
            if result.get('success'):
                # ลบ flag พิเศษ '__carry_forward__' ก่อน return
                if result.get('amounts') and '__carry_forward__' in result['amounts']:
                    del result['amounts']['__carry_forward__']
                if return_result_object:
                    return TaxOCRResult(result)
                return result
            
        except Exception as e:
            logger.error(f"❌ เกิดข้อผิดพลาดในการอ่าน OCR: {e}", exc_info=True)
            error_result = {
                'success': False,
                'error': f'เกิดข้อผิดพลาด: {e}'
            }
            if return_result_object:
                return TaxOCRResult(error_result)
            return error_result
    
    def extract_tax_data(self, pdf_path: Path) -> TaxOCRResult:
        """
        อ่านข้อมูลจากไฟล์ PDF และ return เป็น TaxOCRResult object
        
        Args:
            pdf_path: Path ของไฟล์ PDF แบบยื่นภาษี
            
        Returns:
            TaxOCRResult object ที่มีข้อมูล OCR
        """
        return self.extract_tax_amounts(pdf_path, return_result_object=True)
    
    def get_ocr_raw_data(self, pdf_path: Path) -> Dict[str, Any]:
        """
        ดึงข้อมูลดิบจาก OCR (raw OCR data) โดยไม่ผ่าน parser
        
        Args:
            pdf_path: Path ของไฟล์ PDF
            
        Returns:
            Dictionary ที่มีข้อมูลดิบจาก OCR
        """
        if not pdf_path.exists():
            return {
                'success': False,
                'error': f'ไม่พบไฟล์: {pdf_path}'
            }
        
        try:
            # ลองใช้ AksonOCR ก่อน (Primary OCR Service)
            # ใช้ key-extract mode สำหรับหน้า "ประมวลผล PDF"
            if self.akson_enabled and self.akson_api_key and self.requests_available:
                logger.info(f"🔄 กำลังใช้ AksonOCR (key-extract) อ่านไฟล์: {pdf_path.name}")
                ocr_result = extract_text_from_aksonocr(
                    str(pdf_path),
                    self.akson_api_key,
                    ocr_mode='key-extract'  # ใช้ key-extract สำหรับหน้า "ประมวลผล PDF"
                )
                
                if ocr_result.get('text') or ocr_result.get('raw_content'):
                    # สำหรับ key-extract API: ใช้ raw_content ที่เป็น JSON format
                    # สำหรับ v2/upload API: ใช้ text ที่เป็น markdown/text
                    raw_content = ocr_result.get('raw_content', '')
                    text = ocr_result.get('text', '')
                    
                    # ถ้า raw_content เป็น JSON (key-extract response) ให้ใช้ raw_content เป็นหลัก
                    if raw_content and ('"success"' in raw_content or '"data"' in raw_content):
                        # raw_content เป็น JSON format แล้ว ไม่ต้อง clean
                        # แต่ถ้าไม่มี raw_content ให้ใช้ text
                        if not text:
                            text = raw_content
                    else:
                        # ถ้าไม่ใช่ JSON ให้ clean text และ raw_content
                        text = clean_ocr_text(text) if text else ''
                        raw_content = clean_ocr_text(raw_content) if raw_content else text
                    
                    return {
                        'success': True,
                        'text': text,
                        'raw_content': raw_content,  # สำหรับ key-extract จะเป็น JSON format ที่สวยงาม
                        'tables': ocr_result.get('tables', []),
                        'numbers': ocr_result.get('numbers', []),
                        'method': 'aksonocr'
                    }
                else:
                    # AksonOCR ไม่สำเร็จ - return error
                    error_msg = ocr_result.get('error', 'AksonOCR ไม่สามารถอ่านข้อมูลได้')
                    logger.error(f"❌ AksonOCR ไม่สำเร็จ: {error_msg}")
                    return {
                        'success': False,
                        'text': None,
                        'raw_content': None,
                        'tables': [],
                        'numbers': [],
                        'error': error_msg,
                        'method': 'aksonocr'
                    }
            
            # ถ้า AksonOCR ไม่ได้เปิดใช้งาน ให้ใช้ PyPDF2
            if not (self.akson_enabled and self.akson_api_key and self.requests_available):
                # ใช้ PyPDF2
                import PyPDF2
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    all_text = []
                    for page in pdf_reader.pages:
                        text = page.extract_text()
                        all_text.append(text)
                
                # ทำความสะอาดข้อความที่ได้
                text = clean_ocr_text('\n'.join(all_text))
                
                return {
                    'success': True,
                    'text': text,
                    'raw_content': text,
                    'tables': [],
                    'numbers': [],
                    'method': 'pypdf2'
                }
        except Exception as e:
            logger.error(f"❌ เกิดข้อผิดพลาดในการอ่าน OCR raw data: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'เกิดข้อผิดพลาด: {e}'
            }
    
    def _extract_with_aksonocr(self, pdf_path: Path, ocr_mode: str = 'v2/upload') -> Dict[str, Any]:
        """
        ใช้ AksonOCR ในการอ่าน
        
        Args:
            pdf_path: Path ของไฟล์ PDF
            ocr_mode: OCR mode ('key-extract' หรือ 'v2/upload')
                - 'key-extract': สำหรับหน้า "ประมวลผล PDF"
                - 'v2/upload': สำหรับหน้า "ส่งเมลล์" (default)
        """
        try:
            logger.info(f"🔄 กำลังใช้ AksonOCR ({ocr_mode}) อ่านไฟล์: {pdf_path.name}")
            
            if not self.akson_api_key:
                return {
                    'success': False,
                    'error': 'AksonOCR API key ไม่ได้ตั้งค่า'
                }
            
            # เรียกใช้ extract_text_from_aksonocr function
            ocr_result = extract_text_from_aksonocr(
                str(pdf_path),
                self.akson_api_key,
                ocr_mode=ocr_mode  # ส่ง ocr_mode ไปยัง extract_text_from_aksonocr
            )
            
            if ocr_result.get('error'):
                return {
                    'success': False,
                    'error': ocr_result.get('error', 'AksonOCR error')
                }
            
            if ocr_result.get('text') or ocr_result.get('raw_content'):
                # ใช้ raw_content สำหรับการ parse
                raw_content = ocr_result.get('raw_content', '') or ocr_result.get('text', '')
                
                # ทำความสะอาด raw_content
                raw_content = clean_ocr_text(raw_content)
                
                # Format text output สำหรับแสดงผล
                formatted_text = format_text_output(ocr_result.get('text', ''))
                
                # ทำความสะอาด formatted_text
                formatted_text = clean_ocr_text(formatted_text)
                
                # ถ้าเป็น ภ.พ.30 และมีส่วนการคำนวณภาษี ให้จัดรูปแบบส่วนนั้น
                if 'ภ.พ.30' in formatted_text or 'ภพ.30' in formatted_text:
                    formatted_text = _parse_pp30_calculation_section(formatted_text)
                
                # ใช้ TaxFormParser เพื่อ parse ข้อมูล
                if self.parser:
                    parsed_data = self.parser.parse_tax_form(formatted_text, raw_content=raw_content)
                    
                    return {
                        'success': True,
                        'raw_text': raw_content,
                        'formatted_text': formatted_text,
                        'amounts': parsed_data.get('amounts', {}),
                        'tax_form_type': parsed_data.get('tax_form_type', ''),
                        'company_name': parsed_data.get('company_name'),
                        'tax_id': parsed_data.get('tax_id'),
                        'filing_type': parsed_data.get('filing_type'),
                        'filing_period': parsed_data.get('filing_period'),
                        'payment_date': parsed_data.get('payment_date'),
                        'due_date': parsed_data.get('due_date'),
                        'office_address': parsed_data.get('office_address'),
                        'method': 'aksonocr'
                    }
                else:
                    return {
                        'success': True,
                        'raw_text': raw_content,
                        'formatted_text': formatted_text,
                        'amounts': {},
                        'tax_form_type': '',
                        'company_name': None,
                        'tax_id': None,
                        'filing_type': None,
                        'filing_period': {'month': None, 'year': None},
                        'payment_date': None,
                        'due_date': None,
                        'office_address': None,
                        'method': 'aksonocr'
                    }
            else:
                return {
                    'success': False,
                    'error': 'AksonOCR ไม่สามารถอ่านข้อมูลได้'
                }
                
        except Exception as e:
            logger.error(f"❌ AksonOCR error: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'AksonOCR error: {e}'
            }
    
    def _extract_with_typhoon(self, pdf_path: Path) -> Dict[str, Any]:
        """ใช้ TYPHOON OCR ในการอ่าน"""
        try:
            logger.info(f"🔄 กำลังใช้ TYPHOON OCR อ่านไฟล์: {pdf_path.name}")
            
            if not self.typhoon_api_key:
                return {
                    'success': False,
                    'error': 'TYPHOON OCR API key ไม่ได้ตั้งค่า'
                }
            
            # ตรวจสอบว่าเป็น ภ.ง.ด.54, Pay-In Slip, ภ.พ.30 หรือไม่
            is_pnd54 = False
            is_pay_in_slip = False
            is_pp30 = False
            is_pp36 = False
            try:
                import PyPDF2
                with open(pdf_path, 'rb') as check_file:
                    pdf_reader = PyPDF2.PdfReader(check_file)
                    if len(pdf_reader.pages) > 0:
                        first_page_text = pdf_reader.pages[0].extract_text()
                        if 'ภ.ง.ด.54' in first_page_text or 'ภงด.54' in first_page_text or 'ภงด54' in first_page_text:
                            is_pnd54 = True
                            logger.info("📋 ตรวจพบว่าเป็นเอกสาร ภ.ง.ด.54 - ใช้ max_tokens = 1200")
                        elif 'ชุดชำระเงิน/Pay-In Slip' in first_page_text or 'Pay-In Slip (สำหรับผู้เสียภาษีเพื่อเป็นหลักฐาน' in first_page_text:
                            is_pay_in_slip = True
                            logger.info("📋 ตรวจพบว่าเป็นเอกสาร Pay-In Slip - ใช้ max_tokens = 1200")
                        elif 'ภ.พ.30' in first_page_text or 'ภพ.30' in first_page_text or 'ภพ30' in first_page_text:
                            is_pp30 = True
                            logger.info("📋 ตรวจพบว่าเป็นเอกสาร ภ.พ.30 - ใช้ max_tokens = 2000 (ลดลงจาก 16000)")
                        elif 'ภ.พ.36' in first_page_text or 'ภพ.36' in first_page_text or 'ภพ36' in first_page_text:
                            is_pp36 = True
                            logger.info("📋 ตรวจพบว่าเป็นเอกสาร ภ.พ.36 - ใช้ max_tokens = 16000 (ไม่จำกัด)")
            except Exception as e:
                logger.warning(f"⚠️ ไม่สามารถตรวจสอบประเภทเอกสารได้: {e}")
            
            # กำหนด max_tokens ตามประเภทเอกสาร
            if is_pnd54 or is_pay_in_slip:
                max_tokens = 1200  # เอกสารสั้น
            elif is_pp30:
                max_tokens = 2000  # ภ.พ.30 (ลดลงจาก 16000 เพื่อความเร็ว)
            elif is_pp36:
                max_tokens = 16000  # ภ.พ.36 ต้องการ token เยอะ
            else:
                max_tokens = 2500  # default (ลดลงจาก 16000)
            
            # เรียกใช้ extract_text_from_image function
            ocr_result = extract_text_from_image(
                str(pdf_path),
                self.typhoon_api_key,
                'typhoon-ocr',
                'v1.5',
                max_tokens,
                0.1,
                0.6,
                1.1,
                [1]  # อ่านเฉพาะหน้าแรก
            )
            
            if ocr_result.get('text') or ocr_result.get('raw_content'):
                # ใช้ raw_content สำหรับการ parse (ไม่ format ตัวเลข)
                raw_content = ocr_result.get('raw_content', '') or ocr_result.get('text', '')
                
                # แปลง HTML table ใน raw_content เป็นข้อความต่อกันด้วย pipe (|) สำหรับ ภ.ง.ด.1
                # เพื่อให้ parser อ่านได้ง่ายขึ้น
                raw_content = convert_html_table_to_concatenated_text(raw_content)
                
                # ทำความสะอาด raw_content: ลบ pipe, HTML tags ที่เหลือ
                raw_content = clean_ocr_text(raw_content)
                
                # Format text output สำหรับแสดงผล
                formatted_text = format_text_output(ocr_result.get('text', ''))
                
                # แปลง HTML table ใน formatted_text ด้วย (เพื่อความสอดคล้อง)
                formatted_text = convert_html_table_to_concatenated_text(formatted_text)
                
                # ทำความสะอาด formatted_text: ลบ pipe, HTML tags ที่เหลือ
                formatted_text = clean_ocr_text(formatted_text)
                
                # ใช้ TaxFormParser เพื่อ parse ข้อมูล
                parsed_data = None
                if self.parser:
                    try:
                        parsed_data = self.parser.parse_tax_form(formatted_text, raw_content)
                    except Exception as parse_error:
                        logger.error(f"❌ เกิดข้อผิดพลาดในการ parse ข้อมูล: {parse_error}", exc_info=True)
                        parsed_data = None
                
                # ถ้า parse ไม่สำเร็จ ให้ใช้ข้อมูลพื้นฐาน
                if not parsed_data:
                    parsed_data = {
                        'tax_form_type': None,
                        'company_name': None,
                        'tax_id': None,
                        'filing_type': None,
                        'filing_period': {'month': None, 'year': None},
                        'payment_date': None,
                        'due_date': None,
                        'amounts': {}
                    }
                
                return {
                    'success': True,
                    'tax_form_type': parsed_data.get('tax_form_type'),
                    'company_name': parsed_data.get('company_name'),
                    'tax_id': parsed_data.get('tax_id'),
                    'filing_type': parsed_data.get('filing_type'),
                    'filing_period': parsed_data.get('filing_period'),
                    'payment_date': parsed_data.get('payment_date'),
                    'due_date': parsed_data.get('due_date'),
                    'amounts': parsed_data.get('amounts', {}),
                    'raw_text': formatted_text,
                    'method': 'typhoon',
                    'tables': ocr_result.get('tables', [])
                }
            else:
                return {
                    'success': False,
                    'error': 'TYPHOON OCR ไม่สามารถอ่านข้อความได้'
                }
                
        except Exception as e:
            logger.error(f"❌ TYPHOON OCR error: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'TYPHOON OCR error: {e}'
            }
    
    def _extract_with_pypdf2(self, pdf_path: Path) -> Dict[str, Any]:
        """ใช้ PyPDF2 อ่านข้อความพื้นฐาน (ไม่มี OCR)"""
        try:
            import PyPDF2
            
            logger.info(f"🔄 กำลังใช้ PyPDF2 อ่านไฟล์: {pdf_path.name}")
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                all_text = []
                
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    all_text.append(text)
            
            raw_text = '\n'.join(all_text)
            
            # ทำความสะอาดข้อความ: ลบ pipe, HTML tags ที่เหลือ
            raw_text = clean_ocr_text(raw_text)
            
            # ใช้ TaxFormParser เพื่อ parse ข้อมูล
            parsed_data = None
            if self.parser:
                try:
                    parsed_data = self.parser.parse_tax_form(raw_text, raw_text)
                except Exception as parse_error:
                    logger.error(f"❌ เกิดข้อผิดพลาดในการ parse ข้อมูล: {parse_error}", exc_info=True)
                    parsed_data = None
            
            # ถ้า parse ไม่สำเร็จ ให้ใช้ข้อมูลพื้นฐาน
            if not parsed_data:
                parsed_data = {
                    'tax_form_type': None,
                    'company_name': None,
                    'tax_id': None,
                    'filing_type': None,
                    'filing_period': {'month': None, 'year': None},
                    'payment_date': None,
                    'due_date': None,
                    'amounts': {}
                }
            
            return {
                'success': True,
                'tax_form_type': parsed_data.get('tax_form_type'),
                'company_name': parsed_data.get('company_name'),
                'tax_id': parsed_data.get('tax_id'),
                'filing_type': parsed_data.get('filing_type'),
                'filing_period': parsed_data.get('filing_period'),
                'payment_date': parsed_data.get('payment_date'),
                'due_date': parsed_data.get('due_date'),
                'amounts': parsed_data.get('amounts', {}),
                'raw_text': raw_text,
                'method': 'pypdf2'
            }
            
        except Exception as e:
            logger.error(f"❌ PyPDF2 error: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'PyPDF2 error: {e}'
            }


# ===== Helper Functions =====
def extract_tax_amounts_from_pdf(pdf_path: str, return_result_object: bool = False) -> Dict[str, Any]:
    """
    Helper function สำหรับเรียกใช้ OCR จากไฟล์ PDF
    
    Args:
        pdf_path: Path ของไฟล์ PDF
        return_result_object: ถ้า True จะ return TaxOCRResult object
        
    Returns:
        Dictionary หรือ TaxOCRResult object ที่มีข้อมูลยอดเงิน
    """
    processor = TaxOCRProcessor()
    return processor.extract_tax_amounts(Path(pdf_path), return_result_object=return_result_object)


def extract_tax_data_from_pdf(pdf_path: str) -> TaxOCRResult:
    """
    Helper function สำหรับเรียกใช้ OCR และ return เป็น TaxOCRResult object
    
    Args:
        pdf_path: Path ของไฟล์ PDF
        
    Returns:
        TaxOCRResult object ที่มีข้อมูล OCR
    """
    processor = TaxOCRProcessor()
    return processor.extract_tax_data(Path(pdf_path))


def get_ocr_raw_data_from_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Helper function สำหรับดึงข้อมูลดิบจาก OCR
    
    Args:
        pdf_path: Path ของไฟล์ PDF
        
    Returns:
        Dictionary ที่มีข้อมูลดิบจาก OCR
    """
    processor = TaxOCRProcessor()
    return processor.get_ocr_raw_data(Path(pdf_path))