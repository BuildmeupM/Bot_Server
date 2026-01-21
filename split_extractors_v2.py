"""
Script สำหรับแยก Extractor ออกจากไฟล์เดิม (Version 2)
ใช้ AST เพื่อแยก class definitions
"""
import ast
import re
from pathlib import Path

# อ่านไฟล์เดิม
source_file = Path("สำรอง/invoice_data_extractor.py")
target_dir = Path("invoice_extractors/extractors")

# Mapping ชื่อ class กับชื่อไฟล์
extractor_mapping = {
    'MSCInvoiceExtractor': 'msc.py',
    'MSTInvoiceExtractor': 'mst.py',
    'CustomsDepartmentExtractor': 'customs.py',
    'KLNSeaportExtractor': 'kln_seaport.py',
    'EasternSeaLamchabangTerminalExtractor': 'eastern_sea.py',
    'SiamCommercialSeaportExtractor': 'siam_commercial.py',
    'LCMTExtractor': 'lcmt.py',
    'NgowHokExtractor': 'ngow_hok.py',
    'TIPSExtractor': 'tips.py',
    'CKLineThailandExtractor': 'ck_line.py',
    'JinjiangShippingAgencyExtractor': 'jinjiang.py',
    'ExclusiveGlobalLogisticsExtractor': 'exclusive.py',
}

# อ่านไฟล์
with open(source_file, 'r', encoding='utf-8') as f:
    content = f.read()

# หา class definitions ด้วย regex (เพราะ AST อาจมีปัญหา)
class_pattern = r'^class\s+(\w+Extractor)\(BaseInvoiceExtractor\):'
matches = list(re.finditer(class_pattern, content, re.MULTILINE))

print(f"Found {len(matches)} extractors:")
for m in matches:
    print(f"  - {m.group(1)}")

# แยกแต่ละ class
for i, match in enumerate(matches):
    class_name = match.group(1)
    start_pos = match.start()
    
    # หาตำแหน่งสิ้นสุดของ class
    if i + 1 < len(matches):
        end_pos = matches[i + 1].start()
    else:
        # หา class ถัดไปหรือ end of file
        next_class = content.find('\n# ===== Main Extractor Manager', start_pos + 1)
        if next_class == -1:
            next_class = content.find('\nclass InvoiceExtractorManager', start_pos + 1)
        if next_class == -1:
            end_pos = len(content)
        else:
            end_pos = next_class
    
    # ดึงโค้ดของ class
    class_code = content[start_pos:end_pos].strip()
    
    # สร้างไฟล์ใหม่
    if class_name in extractor_mapping:
        filename = extractor_mapping[class_name]
        filepath = target_dir / filename
        
        # เพิ่ม header และ imports
        header = f'''"""
{class_name.replace('Extractor', '')} Invoice Extractor
{'=' * (len(class_name.replace('Extractor', '')) + 20)}
Extractor สำหรับดึงข้อมูลจาก {class_name.replace('Extractor', '')}

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


'''
        
        # เขียนไฟล์
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(header + class_code)
        
        print(f"✅ Created {filename} ({len(class_code)} chars)")

print("Done!")
