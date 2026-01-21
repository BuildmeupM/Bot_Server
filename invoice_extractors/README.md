# Invoice Extractors Package

โครงสร้างใหม่สำหรับ Invoice Data Extractor (Version 3.0)

## โครงสร้างโฟลเดอร์

```
invoice_extractors/
├── __init__.py              # Export main classes และ functions
├── base.py                  # BaseInvoiceExtractor
├── manager.py               # InvoiceExtractorManager
├── utils.py                 # Helper functions (parse_address, etc.)
├── extractors/
│   ├── __init__.py         # Auto-register extractors
│   ├── msc.py              # MSCInvoiceExtractor ✅
│   ├── mst.py              # MSTInvoiceExtractor
│   ├── customs.py          # CustomsDepartmentExtractor
│   ├── kln_seaport.py      # KLNSeaportExtractor
│   ├── eastern_sea.py      # EasternSeaLamchabangTerminalExtractor
│   ├── lcmt.py            # LCMTExtractor
│   ├── ngow_hok.py        # NgowHokExtractor
│   ├── siam_commercial.py # SiamCommercialSeaportExtractor
│   ├── tips.py            # TIPSExtractor
│   ├── ck_line.py         # CKLineThailandExtractor
│   ├── jinjiang.py        # JinjiangShippingAgencyExtractor
│   └── exclusive.py       # ExclusiveGlobalLogisticsExtractor
└── README.md
```

## วิธีการแยก Extractor

### ขั้นตอนที่ 1: อ่าน Extractor จากไฟล์เดิม

1. เปิดไฟล์ `invoice_data_extractor.py` (ไฟล์เดิม)
2. หา class ของ Extractor ที่ต้องการแยก (เช่น `MSTInvoiceExtractor`)
3. คัดลอกโค้ดทั้งหมดของ class นั้น

### ขั้นตอนที่ 2: สร้างไฟล์ใหม่

1. สร้างไฟล์ใหม่ใน `invoice_extractors/extractors/` (เช่น `mst.py`)
2. เพิ่ม header และ imports:

```python
"""
MST Invoice Extractor
=====================
Extractor สำหรับดึงข้อมูลจาก Mediterranean Shipping (Thailand) Co., Ltd.

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)
```

### ขั้นตอนที่ 3: วางโค้ด Extractor

1. วาง class definition ทั้งหมด
2. เปลี่ยน import จาก `BaseInvoiceExtractor` เป็น `from ..base import BaseInvoiceExtractor`
3. ตรวจสอบว่า imports อื่นๆ ครบถ้วน (re, typing, logging)

### ขั้นตอนที่ 4: Register ใน extractors/__init__.py

1. เปิด `invoice_extractors/extractors/__init__.py`
2. เพิ่ม import: `from .mst import MSTInvoiceExtractor`
3. เพิ่ม instance ใน `EXTRACTORS` list ตามลำดับความสำคัญ
4. เพิ่มใน `__all__`

### ตัวอย่าง

```python
# invoice_extractors/extractors/__init__.py
from .msc import MSCInvoiceExtractor
from .mst import MSTInvoiceExtractor  # เพิ่มบรรทัดนี้

EXTRACTORS = [
    # ... extractors อื่นๆ
    MSTInvoiceExtractor(),  # เพิ่มบรรทัดนี้ (ตามลำดับความสำคัญ)
    MSCInvoiceExtractor(),
]

__all__ = ['EXTRACTORS', 'MSCInvoiceExtractor', 'MSTInvoiceExtractor']
```

## ลำดับความสำคัญของ Extractors

ลำดับมีความสำคัญ! Extractor ที่เฉพาะเจาะจงต้องอยู่ก่อน:

1. CustomsDepartmentExtractor (กรมศุลกากร)
2. KLNSeaportExtractor
3. EasternSeaLamchabangTerminalExtractor
4. LCMTExtractor
5. NgowHokExtractor
6. SiamCommercialSeaportExtractor
7. TIPSExtractor
8. CKLineThailandExtractor
9. JinjiangShippingAgencyExtractor
10. ExclusiveGlobalLogisticsExtractor
11. MSTInvoiceExtractor (ต้องอยู่ก่อน MSC)
12. MSCInvoiceExtractor (อยู่ท้ายสุด)

## Backward Compatibility

ไฟล์ `invoice_data_extractor.py` ยังคงใช้งานได้ (เป็น backward compatibility layer):

```python
# โค้ดเดิมยังใช้งานได้
from invoice_data_extractor import extract_invoice_data

# หรือใช้โครงสร้างใหม่
from invoice_extractors import extract_invoice_data
```

## สถานะการแยก Extractors

- ✅ MSCInvoiceExtractor (msc.py)
- ⏳ MSTInvoiceExtractor
- ⏳ CustomsDepartmentExtractor
- ⏳ KLNSeaportExtractor
- ⏳ EasternSeaLamchabangTerminalExtractor
- ⏳ LCMTExtractor
- ⏳ NgowHokExtractor
- ⏳ SiamCommercialSeaportExtractor
- ⏳ TIPSExtractor
- ⏳ CKLineThailandExtractor
- ⏳ JinjiangShippingAgencyExtractor
- ⏳ ExclusiveGlobalLogisticsExtractor

## ระบบตรวจสอบและปรับยอดเงิน (Amount Validation)

ระบบจะตรวจสอบและปรับยอดเงินให้สอดคล้องกันอัตโนมัติ:

### เงื่อนไขการตรวจสอบ
- **ยอดก่อนภาษี** + **ยอดภาษี** = **ยอดรวม**

### กลยุทธ์การปรับค่า
1. **ถ้ามียอดรวม**: ใช้ยอดรวมเป็นหลักและคำนวณยอดก่อนภาษีและยอดภาษีใหม่
   - ยอดก่อนภาษี = ยอดรวม / 1.07
   - ยอดภาษี = ยอดรวม - ยอดก่อนภาษี
   
2. **ถ้าไม่มียอดรวม**: ใช้ยอดก่อนภาษีและยอดภาษีที่อ่านได้
   - ยอดรวม = ยอดก่อนภาษี + ยอดภาษี

3. **ถ้ามีแค่บางส่วน**: คำนวณส่วนที่ขาด
   - ถ้ามีแค่อยอดก่อนภาษี: คำนวณยอดภาษี (7%) และยอดรวม
   - ถ้ามีแค่อยอดภาษี: คำนวณยอดก่อนภาษีและยอดรวม

### ตัวอย่าง
- **กรณีที่ 1**: อ่านได้ยอดก่อนภาษี = 200, ยอดรวม = 107
  - ระบบจะปรับ: ยอดก่อนภาษี = 100, ยอดภาษี = 7, ยอดรวม = 107
  
- **กรณีที่ 2**: อ่านได้ยอดก่อนภาษี = 100, ยอดภาษี = 7, ยอดรวม = 107
  - ระบบจะตรวจสอบและยืนยันว่าตรงกัน (ไม่ต้องปรับ)

- **กรณีที่ 3**: อ่านได้ยอดก่อนภาษี = 200, ยอดภาษี = 7, ยอดรวม = 107 (มียอดครบแต่ไม่สอดคล้องกัน)
  - ระบบจะใช้ยอดรวมเป็นหลัก: ยอดรวม = 107
  - คำนวณยอดก่อนภาษีใหม่: 107 / 1.07 = 100
  - คำนวณยอดภาษีใหม่: 107 - 100 = 7
  - ผลลัพธ์: ยอดก่อนภาษี = 100, ยอดภาษี = 7, ยอดรวม = 107

### การทำงาน
ระบบจะทำงานอัตโนมัติใน `InvoiceExtractorManager.extract_data()` หลังจากดึงข้อมูลจาก Extractor แล้ว

## หมายเหตุ

- แต่ละ Extractor ควรอยู่ในไฟล์ของตัวเอง
- ใช้ naming convention: `company_name.py` (lowercase, underscore)
- Class name: `CompanyNameExtractor` (PascalCase)
- ระบบตรวจสอบยอดเงินจะทำงานอัตโนมัติสำหรับทุก Extractor
