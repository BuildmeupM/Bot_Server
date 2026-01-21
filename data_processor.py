import shutil
import json
from pathlib import Path
from typing import Dict, List, Optional
from config import Config

class DataProcessor:
    def __init__(self):
        self.processed_files = []
        self.output_files = []
        
    def process_company_data(self, pdf_data: Dict, folder_settings: Dict) -> Dict:
        """ประมวลผลข้อมูลบริษัทและกำหนดกลุ่ม"""
        processed_data = pdf_data.copy()
        
        # หาข้อมูลกลุ่มจาก folder_settings
        folder_code = pdf_data.get('folder_code', '')
        if folder_code in folder_settings:
            folder_info = folder_settings[folder_code]
            processed_data['group'] = folder_info.get('group', 'unknown')
            processed_data['group_message'] = folder_info.get('message', '')
        else:
            processed_data['group'] = 'unknown'
            processed_data['group_message'] = 'ไม่พบข้อมูลกลุ่ม'
        
        return processed_data
    
    def generate_output_filename(self, pdf_data: Dict, group: str) -> str:
        """สร้างชื่อไฟล์ผลลัพธ์ตามกลุ่ม"""
        company_name = pdf_data.get('company_name', 'Unknown')
        original_filename = pdf_data.get('filename', 'document.pdf')
        
        # กำหนดชื่อไฟล์ตามกลุ่ม
        if group == 'regular':  # group1 - VAT
            if company_name in Config.GROUP1_COMPANY_MAPPING:
                service_name = Config.GROUP1_COMPANY_MAPPING[company_name]
            else:
                service_name = f"ค่าบริการ {company_name} VAT"
        elif group == 'special':  # group3 - No VAT
            if company_name in Config.GROUP3_COMPANY_MAPPING:
                service_name = Config.GROUP3_COMPANY_MAPPING[company_name]
            else:
                service_name = f"ค่าบริการ {company_name}"
        else:
            service_name = f"ค่าบริการ {company_name}"
        
        # สร้างชื่อไฟล์ใหม่
        file_extension = Path(original_filename).suffix
        new_filename = f"{service_name}_{pdf_data.get('invoice_number', 'NO')}{file_extension}"
        
        return new_filename
    
    def create_processed_pdf(self, source_pdf: Path, output_filename: str, output_path: Path) -> Optional[Path]:
        """สร้างไฟล์ PDF ที่ประมวลผลแล้ว"""
        try:
            # สร้างโฟลเดอร์ผลลัพธ์ถ้ายังไม่มี
            output_path.mkdir(parents=True, exist_ok=True)
            
            # คัดลอกไฟล์ไปยังโฟลเดอร์ผลลัพธ์
            dest_file = output_path / output_filename
            shutil.copy2(source_pdf, dest_file)
            
            print(f"Created processed PDF: {dest_file}")
            return dest_file
            
        except Exception as e:
            print(f"Error creating processed PDF: {e}")
            return None
    
    def organize_files_by_group(self, pdf_files: List[Path], processed_data: List[Dict], 
                               base_output_path: Path) -> Dict:
        """จัดระเบียบไฟล์ตามกลุ่ม"""
        organized_files = {
            'original': [],
            'vat': [],
            'none_vat': []
        }
        
        for i, pdf_file in enumerate(pdf_files):
            if i < len(processed_data):
                data = processed_data[i]
                group = data.get('group', 'unknown')
                
                # ไฟล์ต้นฉบับ
                original_dest = self.move_file_to_output(
                    pdf_file, 'original', base_output_path
                )
                if original_dest:
                    organized_files['original'].append(original_dest)
                
                # ไฟล์ที่ประมวลผลแล้ว
                if group == 'regular':  # VAT
                    output_filename = self.generate_output_filename(data, 'regular')
                    processed_file = self.create_processed_pdf(
                        pdf_file, output_filename, 
                        base_output_path / Config.OUTPUT_FOLDERS['vat']
                    )
                    if processed_file:
                        organized_files['vat'].append(processed_file)
                        
                elif group == 'special':  # No VAT
                    output_filename = self.generate_output_filename(data, 'special')
                    processed_file = self.create_processed_pdf(
                        pdf_file, output_filename, 
                        base_output_path / Config.OUTPUT_FOLDERS['none_vat']
                    )
                    if processed_file:
                        organized_files['none_vat'].append(processed_file)
        
        return organized_files
    
    def move_file_to_output(self, source_file: Path, output_type: str, base_output_path: Path) -> Optional[Path]:
        """ย้ายไฟล์ไปยังโฟลเดอร์ผลลัพธ์"""
        if output_type in Config.OUTPUT_FOLDERS:
            dest_folder = base_output_path / Config.OUTPUT_FOLDERS[output_type]
            dest_folder.mkdir(parents=True, exist_ok=True)
            
            dest_file = dest_folder / source_file.name
            
            try:
                shutil.copy2(source_file, dest_file)
                print(f"Moved file to {output_type}: {dest_file}")
                return dest_file
            except Exception as e:
                print(f"Error moving file: {e}")
                return None
        return None
    
    def validate_processed_data(self, processed_data: List[Dict]) -> Dict:
        """ตรวจสอบความถูกต้องของข้อมูลที่ประมวลผลแล้ว"""
        validation_result = {
            'total_files': len(processed_data),
            'valid_files': 0,
            'invalid_files': 0,
            'missing_fields': [],
            'errors': []
        }
        
        required_fields = ['company_name', 'invoice_number', 'amount_before_vat', 'total_amount']
        
        for i, data in enumerate(processed_data):
            is_valid = True
            missing = []
            
            # ตรวจสอบฟิลด์ที่จำเป็น
            for field in required_fields:
                if not data.get(field):
                    missing.append(field)
                    is_valid = False
            
            if is_valid:
                validation_result['valid_files'] += 1
            else:
                validation_result['invalid_files'] += 1
                validation_result['missing_fields'].append({
                    'file_index': i,
                    'filename': data.get('filename', 'Unknown'),
                    'missing_fields': missing
                })
        
        return validation_result
    
    def create_processing_summary(self, processed_data: List[Dict], 
                                organized_files: Dict) -> Dict:
        """สร้างสรุปการประมวลผล"""
        summary = {
            'processing_date': str(Path().cwd()),
            'total_pdfs_processed': len(processed_data),
            'files_by_group': {
                'original': len(organized_files.get('original', [])),
                'vat': len(organized_files.get('vat', [])),
                'none_vat': len(organized_files.get('none_vat', []))
            },
            'companies_processed': [],
            'total_amount_processed': 0
        }
        
        # รวบรวมข้อมูลบริษัท
        companies = set()
        total_amount = 0
        
        for data in processed_data:
            company = data.get('company_name')
            if company:
                companies.add(company)
            
            amount = data.get('total_amount')
            if amount and isinstance(amount, (int, float)):
                total_amount += amount
        
        summary['companies_processed'] = list(companies)
        summary['total_amount_processed'] = total_amount
        
        return summary
    
    def export_processing_data(self, processed_data: List[Dict], 
                             output_path: Path, filename: str = "processing_data.json"):
        """ส่งออกข้อมูลการประมวลผลเป็น JSON"""
        try:
            export_file = output_path / filename
            export_file.parent.mkdir(parents=True, exist_ok=True)
            
            # แปลงข้อมูลให้เป็น JSON serializable
            export_data = []
            for data in processed_data:
                export_item = {}
                for key, value in data.items():
                    if isinstance(value, Path):
                        export_item[key] = str(value)
                    else:
                        export_item[key] = value
                export_data.append(export_item)
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            print(f"Processing data exported to: {export_file}")
            return True
            
        except Exception as e:
            print(f"Error exporting processing data: {e}")
            return False
