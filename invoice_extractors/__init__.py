"""
Invoice Extractors Package
==========================
ระบบดึงข้อมูลจากใบแจ้งหนี้ของบริษัทต่างๆ

Author: BotV3
Version: 3.0.0
"""

# Export main classes and functions for backward compatibility
from .base import BaseInvoiceExtractor
from .manager import InvoiceExtractorManager

# Helper function for backward compatibility
def extract_invoice_data(text: str, filename: str, filepath: str = None):
    """
    Helper function สำหรับดึงข้อมูลจากใบแจ้งหนี้
    
    Args:
        text: ข้อความที่อ่านจาก OCR
        filename: ชื่อไฟล์ PDF
        filepath: Path ของไฟล์ (optional)
    
    Returns:
        Dictionary ที่มีข้อมูลทั้งหมด
    """
    manager = InvoiceExtractorManager()
    return manager.extract_data(text, filename, filepath)


__all__ = [
    'BaseInvoiceExtractor',
    'InvoiceExtractorManager',
    'extract_invoice_data',
]
