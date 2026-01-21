"""
Invoice Data Extractor (Backward Compatibility)
===============================================
ไฟล์นี้เป็น backward compatibility layer
สำหรับรองรับโค้ดเดิมที่ import จาก invoice_data_extractor

โครงสร้างใหม่: invoice_extractors/
- invoice_extractors/base.py - BaseInvoiceExtractor
- invoice_extractors/manager.py - InvoiceExtractorManager
- invoice_extractors/extractors/ - แต่ละ Extractor

Author: BotV3
Version: 3.0.0 (Refactored)
"""

# Import จากโครงสร้างใหม่
from invoice_extractors import (
    BaseInvoiceExtractor,
    InvoiceExtractorManager,
    extract_invoice_data
)

# Export สำหรับ backward compatibility
__all__ = [
    'BaseInvoiceExtractor',
    'InvoiceExtractorManager',
    'extract_invoice_data',
]

# หมายเหตุ: Extractor classes แต่ละตัวจะถูกย้ายไปที่ invoice_extractors/extractors/
# เช่น MSCInvoiceExtractor -> invoice_extractors.extractors.msc.MSCInvoiceExtractor
