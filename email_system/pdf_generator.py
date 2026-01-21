"""
PDF Generator - ระบบสร้าง PDF สรุปข้อมูลสำหรับส่งอีเมลล์และ LINE
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

# ===== ตรวจสอบ reportlab =====
REPORTLAB_AVAILABLE = False
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate,
        Table,
        TableStyle,
        Paragraph,
        Spacer,
    )
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
    logger.info("✅ reportlab พร้อมใช้งาน")
except Exception as e:
    REPORTLAB_AVAILABLE = False
    logger.warning(f"⚠️ reportlab ใช้งานไม่ได้: {e}")

# ===== ตรวจสอบ fpdf (fallback) =====
FPDF_AVAILABLE = False
try:
    try:
        from fpdf import FPDF
        FPDF_AVAILABLE = True
        logger.info("✅ fpdf พร้อมใช้งาน")
    except ImportError:
        from fpdf2 import FPDF  # type: ignore
        FPDF_AVAILABLE = True
        logger.info("✅ fpdf2 พร้อมใช้งาน")
except Exception as e:
    FPDF_AVAILABLE = False
    logger.warning(f"⚠️ fpdf ใช้งานไม่ได้: {e}")

# ===== ตรวจสอบ pdf2image สำหรับแปลง PDF เป็นรูปภาพ =====
PDF2IMAGE_AVAILABLE = False
try:
    from pdf2image import convert_from_path
    from PIL import Image as PILImage  # noqa
    PDF2IMAGE_AVAILABLE = True
except Exception as e:
    PDF2IMAGE_AVAILABLE = False
    logger.warning(f"⚠️ pdf2image/Pillow ใช้งานไม่ได้: {e}")


class PDFGenerator:
    """คลาสสำหรับสร้าง PDF สรุปข้อมูล"""

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize PDF Generator

        Args:
            output_dir: โฟลเดอร์สำหรับเก็บไฟล์ PDF (default: temp_uploads)
        """
        self.output_dir = output_dir or Path("temp_uploads")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ===== helper แปลงจำนวนเงินให้เป็น float แบบปลอดภัย =====
    @staticmethod
    def _to_amount(value: Any) -> float:
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        s = str(value).strip()
        if s in ("", "-", "x,xxx"):
            return 0.0
        s = s.replace(",", "")
        try:
            return float(s)
        except ValueError:
            return 0.0

    def generate_summary_pdf(
        self,
        title: str,
        company_name: str,
        period: str,
        data: List[Dict[str, Any]],
        filename: Optional[str] = None,
        tax_id: Optional[str] = None,
    ) -> Path:
        """
        สร้าง PDF สรุปข้อมูล

        Args:
            title: หัวข้อสรุป เช่น "สรุปภาษีประจำเดือน 10/2025"
            company_name: ชื่อบริษัท (บรรทัดแรก)
            period: ระยะเวลา (ไม่ใช้แล้ว - เก็บไว้เพื่อ backward compatibility)
            data: ข้อมูลตาราง [{"แบบภาษี": "...", "จำนวนเงิน": "..."}]
            filename: ชื่อไฟล์ (ถ้าไม่ระบุจะสร้างอัตโนมัติ)
            tax_id: เลขประจำตัวผู้เสียภาษีอากร

        Returns:
            Path ของไฟล์ PDF ที่สร้าง
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"summary_{timestamp}.pdf"

        pdf_path = self.output_dir / filename

        reportlab_available = REPORTLAB_AVAILABLE
        fpdf_available = FPDF_AVAILABLE

        # เผื่อกรณี import ตอนโหลด module พลาด ลอง import ซ้ำ
        if not reportlab_available and not fpdf_available:
            try:
                from reportlab.lib.pagesizes import A4  # noqa
                from reportlab.lib import colors  # noqa
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # noqa
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer  # noqa
                from reportlab.pdfbase import pdfmetrics  # noqa
                from reportlab.pdfbase.ttfonts import TTFont  # noqa

                reportlab_available = True
                logger.info("✅ reportlab import สำเร็จ (retry)")
            except Exception as e:
                logger.debug(f"reportlab retry failed: {e}")
                try:
                    from fpdf import FPDF  # noqa
                    fpdf_available = True
                    logger.info("✅ fpdf import สำเร็จ (retry)")
                except Exception as e2:
                    logger.debug(f"fpdf retry failed: {e2}")

        if reportlab_available:
            return self._generate_with_reportlab(
                pdf_path, title, company_name, period, data, tax_id
            )
        elif fpdf_available:
            return self._generate_with_fpdf(
                pdf_path, title, company_name, period, data, tax_id
            )
        else:
            error_msg = (
                "ต้องติดตั้ง reportlab หรือ fpdf เพื่อสร้าง PDF\n"
                f"REPORTLAB_AVAILABLE: {REPORTLAB_AVAILABLE}, "
                f"FPDF_AVAILABLE: {FPDF_AVAILABLE}\n"
                "กรุณาติดตั้งด้วย: pip install reportlab หรือ pip install fpdf2"
            )
            logger.error(error_msg)
            raise ImportError(error_msg)

    # ===== สร้าง PDF ด้วย reportlab (เวอร์ชันภาษาไทย / layout ตามตัวอย่าง) =====
    def _generate_with_reportlab(
        self,
        pdf_path: Path,
        title: str,
        company_name: str,
        period: str,
        data: List[Dict[str, Any]],
        tax_id: Optional[str] = None,
    ) -> Path:
        """สร้าง PDF ด้วย reportlab ในรูปแบบตารางภาษาไทย"""

        try:
            import platform

            doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
            story: List[Any] = []
            styles = getSampleStyleSheet()

            # ---------- ฟอนต์ภาษาไทย ----------
            thai_font_name: Optional[str] = None
            try:
                # ตรวจสอบฟอนต์จากโฟลเดอร์ email_system/THSarabunNew/ ก่อน
                # ถ้าไม่พบค่อยไปหาใน C:\Windows\Fonts
                font_base_paths = []
                
                # 1. ลองหาในโฟลเดอร์ email_system/THSarabunNew/ (ที่ผู้ใช้วางไว้)
                local_font_dir = Path(__file__).parent / "THSarabunNew"
                if local_font_dir.exists() and local_font_dir.is_dir():
                    font_base_paths.append(local_font_dir)
                    logger.info(f"✅ พบโฟลเดอร์ฟอนต์: {local_font_dir}")
                
                # 2. ลองหาใน C:\Windows\Fonts (Windows)
                if platform.system() == "Windows":
                    windows_fonts_dir = Path(r"C:\Windows\Fonts")
                    if windows_fonts_dir.exists():
                        font_base_paths.append(windows_fonts_dir)
                
                # กำหนด mapping ระหว่างไฟล์ฟอนต์กับชื่อที่ใช้ใน reportlab
                font_mappings = []
                for base_path in font_base_paths:
                    font_mappings.extend([
                        (base_path / "THSarabunNew.ttf", "ThaiFont", "normal"),
                        (base_path / "THSarabunNew Bold.ttf", "ThaiFont-Bold", "bold"),
                        (base_path / "THSarabunNew Italic.ttf", "ThaiFont-Italic", "italic"),
                        (base_path / "THSarabunNew BoldItalic.ttf", "ThaiFont-BoldItalic", "bolditalic"),
                    ])
                
                # ลงทะเบียนฟอนต์ Regular ก่อน (สำคัญ!)
                if font_mappings:
                    regular_font_path, regular_font_name, _ = font_mappings[0]
                    if regular_font_path.exists():
                        try:
                            pdfmetrics.registerFont(TTFont(regular_font_name, str(regular_font_path)))
                            thai_font_name = regular_font_name
                            logger.info(f"✅ ลงทะเบียนฟอนต์ภาษาไทย (Regular): {regular_font_path}")
                            
                            # ลงทะเบียนฟอนต์ style อื่นๆ (ถ้ามี)
                            bold_font_name = None
                            italic_font_name = None
                            bolditalic_font_name = None
                            
                            for font_path, font_name, style_type in font_mappings[1:]:
                                if font_path.exists():
                                    try:
                                        pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
                                        if style_type == "bold":
                                            bold_font_name = font_name
                                        elif style_type == "italic":
                                            italic_font_name = font_name
                                        elif style_type == "bolditalic":
                                            bolditalic_font_name = font_name
                                        logger.debug(f"✅ ลงทะเบียนฟอนต์: {font_name} ({style_type}) จาก {font_path}")
                                    except Exception as e:
                                        logger.debug(f"⚠️ ไม่สามารถลงทะเบียน {font_name}: {e}")
                            
                            # ลงทะเบียน Font Family เพื่อให้ <b>, <i> ทำงานได้
                            try:
                                pdfmetrics.registerFontFamily(
                                    regular_font_name,
                                    normal=regular_font_name,
                                    bold=bold_font_name or regular_font_name,
                                    italic=italic_font_name or regular_font_name,
                                    boldItalic=bolditalic_font_name or regular_font_name
                                )
                                logger.info(f"✅ ลงทะเบียน Font Family สำเร็จ: {regular_font_name} (normal={regular_font_name}, bold={bold_font_name or regular_font_name})")
                            except Exception as e:
                                logger.warning(f"⚠️ ไม่สามารถลงทะเบียน Font Family: {e}")
                        except Exception as e:
                            logger.warning(f"❌ ไม่สามารถลงทะเบียนฟอนต์ Regular: {e}")
                    else:
                        logger.warning("⚠️ ไม่พบไฟล์ฟอนต์ THSarabunNew.ttf ในโฟลเดอร์ที่กำหนด")
                else:
                    logger.warning("⚠️ ไม่พบโฟลเดอร์ฟอนต์ (email_system/THSarabunNew/ หรือ C:\\Windows\\Fonts)")
            except Exception as e:
                logger.warning(f"ไม่สามารถโหลดฟอนต์ภาษาไทย: {e}")

            base_font = thai_font_name or "Helvetica"
            
            # ตรวจสอบว่าฟอนต์ลงทะเบียนสำเร็จหรือไม่
            if thai_font_name:
                registered_fonts = pdfmetrics.getRegisteredFontNames()
                if thai_font_name in registered_fonts:
                    logger.info(f"✅ ฟอนต์ {thai_font_name} ลงทะเบียนสำเร็จและพร้อมใช้งาน")
                else:
                    logger.warning(f"⚠️ ฟอนต์ {thai_font_name} ไม่พบในรายการฟอนต์ที่ลงทะเบียนแล้ว")
                    logger.warning(f"   ฟอนต์ที่มี: {registered_fonts[:10]}...")  # แสดง 10 ตัวแรก
            else:
                logger.warning("⚠️ ไม่พบฟอนต์ภาษาไทย ใช้ Helvetica แทน (อาจแสดงผลภาษาไทยไม่ถูกต้อง)")

            # ---------- สไตล์ข้อความ ----------
            heading_center = ParagraphStyle(
                "HeadingCenter",
                parent=styles["Normal"],
                fontName=base_font,
                fontSize=14,
                alignment=1,  # center
                leading=16,
            )
            header_style = ParagraphStyle(
                "HeaderStyle",
                parent=styles["Normal"],
                fontName=base_font,
                fontSize=12,
                alignment=1,
                leading=14,
            )
            normal_style = ParagraphStyle(
                "NormalThai",
                parent=styles["Normal"],
                fontName=base_font,
                fontSize=12,
                leading=14,
            )

            # ---------- เตรียมข้อมูลตาราง ----------
            table_data: List[List[Any]] = []

            # แถว 1: ชื่อบริษัท (บรรทัดแรก)
            company_p = Paragraph(company_name or "", heading_center)
            table_data.append([company_p, ""])

            # แถว 2: เลขประจำตัวผู้เสียภาษีอากร (แสดงเฉพาะตัวเลข 13 หลัก ไม่เอาคำนำหน้า)
            if tax_id:
                tax_id_p = Paragraph(tax_id, header_style)
                table_data.append([tax_id_p, ""])

            # แถว 3: หัวข้อสรุป (title)
            title_p = Paragraph(title or "", heading_center)
            table_data.append([title_p, ""])

            # **ไม่เอาระยะเวลาอีกแล้ว**

            # แถว 4: หัวคอลัมน์
            table_data.append(
                [
                    Paragraph("<b>แบบภาษี</b>", header_style),
                    Paragraph("<b>จำนวนเงิน</b>", header_style),
                ]
            )

            # แถวข้อมูล
            total = 0.0
            for row in data or []:
                tax_form = str(row.get("แบบภาษี", "")).strip()
                amount_raw = row.get("จำนวนเงิน", "")

                # ตรวจสอบว่าเป็นข้อความพิเศษ "ไม่มียอดชำระ" หรือไม่
                amount_str = str(amount_raw).strip()
                if amount_str == "ไม่มียอดชำระ":
                    amount_display = "ไม่มียอดชำระ"
                else:
                    amount = self._to_amount(amount_raw)
                    if amount > 0:
                        total += amount
                        amount_display = f"{amount:,.2f}"
                    else:
                        # ถ้าคุณอยากกรอกตัวเลขเองทีหลัง จะส่ง string เช่น "x,xxx" มาก็ได้
                        amount_display = amount_str or "-"

                table_data.append(
                    [
                        Paragraph(tax_form, normal_style),
                        Paragraph(amount_display, normal_style),
                    ]
                )

            # แถวรวม
            total_label = Paragraph("<b>รวม</b>", normal_style)
            if data:
                total_value = Paragraph(f"<b>{total:,.2f}</b>", normal_style)
            else:
                total_value = Paragraph("-", normal_style)

            table_data.append([total_label, total_value])

            # ---------- สร้าง Table ----------
            table = Table(
                table_data,
                colWidths=[doc.width * 0.6, doc.width * 0.4],
            )

            # ---------- style ตาราง ----------
            table_style: List[tuple] = [
                # รวมเซลล์หัว 3 แถวแรก
                ("SPAN", (0, 0), (1, 0)),
                ("SPAN", (0, 1), (1, 1)),
                ("SPAN", (0, 2), (1, 2)),

                # จัดให้อยู่กลาง
                ("ALIGN", (0, 0), (1, 2), "CENTER"),
                ("VALIGN", (0, 0), (1, 2), "MIDDLE"),

                # สีพื้นหลังหัว
                ("BACKGROUND", (0, 0), (1, 0), colors.HexColor("#9fb9e9")),
                ("BACKGROUND", (0, 1), (1, 1), colors.HexColor("#c4d5f5")),
                ("BACKGROUND", (0, 2), (1, 2), colors.HexColor("#c4d5f5")),

                # หัวคอลัมน์
                ("BACKGROUND", (0, 3), (1, 3), colors.HexColor("#b7cde9")),
                ("ALIGN", (0, 3), (1, 3), "CENTER"),

                # เส้นกริด
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),

                # จัดจำนวนเงินชิดขวา
                ("ALIGN", (1, 4), (1, -2), "RIGHT"),

                # แถวรวมพื้นหลังเหลือง
                ("BACKGROUND", (0, -1), (1, -1), colors.HexColor("#ffe6aa")),
            ]

            if thai_font_name:
                table_style.append(("FONTNAME", (0, 0), (-1, -1), thai_font_name))

            table.setStyle(TableStyle(table_style))

            story.append(table)
            story.append(Spacer(1, 14))

            # footer เวลา
            story.append(
                Paragraph(
                    f"สร้างเมื่อ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    normal_style,
                )
            )

            doc.build(story)
            logger.info(f"✅ สร้าง PDF สำเร็จ: {pdf_path}")
            return pdf_path

        except Exception as e:
            logger.error(f"❌ เกิดข้อผิดพลาดในการสร้าง PDF: {e}", exc_info=True)
            raise

    # ===== fallback สร้าง PDF ด้วย fpdf (ถ้าไม่มี reportlab) =====
    def _generate_with_fpdf(
        self,
        pdf_path: Path,
        title: str,
        company_name: str,
        period: str,
        data: List[Dict[str, Any]],
    ) -> Path:
        """สร้าง PDF ด้วย fpdf (fallback) – หมายเหตุ: ถ้าอยากให้รองรับไทยจริง ๆ ควรเพิ่มฟอนต์ TTF เอง"""

        try:
            pdf = FPDF()
            pdf.add_page()

            # หมายเหตุ: Arial ไม่รองรับ Unicode ถ้าข้อความไทยเป็น ??? ให้เพิ่มฟอนต์ไทยเอง
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, company_name, ln=1, align="C")

            pdf.set_font("Arial", "", 12)
            pdf.multi_cell(0, 8, title, align="C")
            pdf.ln(2)

            pdf.cell(0, 8, period, ln=1, align="C")
            pdf.ln(5)

            # หัวตาราง
            pdf.set_font("Arial", "B", 12)
            pdf.cell(90, 8, "แบบภาษี", border=1, align="C")
            pdf.cell(90, 8, "จำนวนเงิน", border=1, align="C", ln=1)

            # ข้อมูล
            pdf.set_font("Arial", "", 11)
            total = 0.0
            for row in data or []:
                tax_form = str(row.get("แบบภาษี", "")).strip()
                amount_raw = row.get("จำนวนเงิน", "")

                # ตรวจสอบว่าเป็นข้อความพิเศษ "ไม่มียอดชำระ" หรือไม่
                amount_str = str(amount_raw).strip()
                if amount_str == "ไม่มียอดชำระ":
                    amount_display = "ไม่มียอดชำระ"
                else:
                    amount = self._to_amount(amount_raw)
                    if amount > 0:
                        total += amount
                        amount_display = f"{amount:,.2f}"
                    else:
                        amount_display = amount_str or "-"

                pdf.cell(90, 8, tax_form, border=1)
                pdf.cell(90, 8, amount_display, border=1, align="R", ln=1)

            # แถวรวม
            pdf.set_font("Arial", "B", 12)
            pdf.cell(90, 8, "รวม", border=1)
            pdf.cell(90, 8, f"{total:,.2f}", border=1, align="R", ln=1)

            pdf.ln(8)
            pdf.set_font("Arial", "I", 10)
            pdf.cell(
                0,
                8,
                f"สร้างเมื่อ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                ln=1,
            )

            pdf.output(str(pdf_path))
            logger.info(f"✅ สร้าง PDF (fpdf) สำเร็จ: {pdf_path}")
            return pdf_path

        except Exception as e:
            logger.error(f"❌ เกิดข้อผิดพลาดในการสร้าง PDF (fpdf): {e}", exc_info=True)
            raise

    # ===== แปลง PDF เป็นรูปภาพ =====
    def pdf_to_image(
        self,
        pdf_path: Path,
        output_path: Optional[Path] = None,
        dpi: int = 150,
        resize_to_half_a4: bool = True,
    ) -> Path:
        """
        แปลง PDF เป็นรูปภาพหน้าแรก

        Args:
            pdf_path: Path ของไฟล์ PDF
            output_path: Path ของไฟล์รูปภาพที่จะสร้าง (ถ้าไม่ระบุจะสร้าง .png ข้าง ๆ PDF)
            dpi: ความละเอียดของรูปภาพ (default: 150)
            resize_to_half_a4: ปรับขนาดเป็นครึ่งหนึ่งของ A4 (default: True)

        Returns:
            Path ของไฟล์รูปภาพที่สร้าง
        """
        if not PDF2IMAGE_AVAILABLE:
            raise ImportError(
                "ต้องติดตั้ง pdf2image และ Pillow เพื่อแปลง PDF เป็นรูปภาพ "
                "(pip install pdf2image pillow)"
            )

        if not pdf_path.exists():
            raise FileNotFoundError(f"ไม่พบไฟล์ PDF: {pdf_path}")

        try:
            images = convert_from_path(
                str(pdf_path), first_page=1, last_page=1, dpi=dpi
            )

            if not images:
                raise ValueError("ไม่สามารถแปลง PDF เป็นรูปภาพได้")

            if not output_path:
                output_path = pdf_path.with_suffix(".png")

            img = images[0]
            
            # ปรับขนาดเป็นครึ่งหนึ่งของ A4 ถ้าต้องการ
            if resize_to_half_a4:
                # A4 = 210mm x 297mm
                # ครึ่งหนึ่งของ A4 = 105mm x 148.5mm
                # คำนวณขนาดเป็น pixels ที่ DPI ที่กำหนด
                # 1 inch = 25.4mm
                # width = 105mm * dpi / 25.4
                # height = 148.5mm * dpi / 25.4
                half_a4_width = int(105 * dpi / 25.4)
                half_a4_height = int(148.5 * dpi / 25.4)
                
                # Resize รูปภาพให้เป็นครึ่งหนึ่งของ A4 โดยคงอัตราส่วน
                original_width, original_height = img.size
                original_ratio = original_width / original_height
                target_ratio = half_a4_width / half_a4_height
                
                if original_ratio > target_ratio:
                    # รูปภาพกว้างกว่า ใช้ width เป็นหลัก
                    new_width = half_a4_width
                    new_height = int(half_a4_width / original_ratio)
                else:
                    # รูปภาพสูงกว่า ใช้ height เป็นหลัก
                    new_height = half_a4_height
                    new_width = int(half_a4_height * original_ratio)
                
                # Resize ด้วย LANCZOS (คุณภาพดี)
                img = img.resize((new_width, new_height), PILImage.LANCZOS)
                logger.info(f"📐 ปรับขนาดรูปภาพเป็น {new_width}x{new_height} pixels (ครึ่งหนึ่งของ A4 ที่ {dpi} DPI)")

            img.save(str(output_path), "PNG")
            logger.info(f"✅ แปลง PDF เป็นรูปภาพสำเร็จ: {output_path}")
            return output_path

        except Exception as e:
            logger.error(
                f"❌ เกิดข้อผิดพลาดในการแปลง PDF เป็นรูปภาพ: {e}", exc_info=True
            )
            raise
