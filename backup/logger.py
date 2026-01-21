import logging
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from config import Config

class BotLogger:
    def __init__(self):
        self.log_file = Config.LOG_FILE
        self.report_file = Config.REPORT_FILE
        self.excel_log_file = Config.EXCEL_LOG_FILE
        
        # ตั้งค่า logging
        self.setup_logging()
        
        # เก็บข้อมูล log
        self.log_data = []
        
    def setup_logging(self):
        """ตั้งค่า logging system"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def log_action(self, action: str, status: str, details: str = "", file_info: Dict = None):
        """บันทึกการทำงาน"""
        timestamp = datetime.now()
        
        log_entry = {
            'timestamp': timestamp,
            'action': action,
            'status': status,
            'details': details,
            'filename': file_info.get('filename', '') if file_info else '',
            'company_name': file_info.get('company_name', '') if file_info else '',
            'folder_code': file_info.get('folder_code', '') if file_info else ''
        }
        
        self.log_data.append(log_entry)
        
        # บันทึกลง log file
        if status == 'SUCCESS':
            self.logger.info(f"{action}: {details}")
        elif status == 'ERROR':
            self.logger.error(f"{action}: {details}")
        elif status == 'WARNING':
            self.logger.warning(f"{action}: {details}")
        else:
            self.logger.info(f"{action}: {details}")
    
    def log_pdf_processing(self, pdf_file: str, company_name: str, status: str, details: str = ""):
        """บันทึกการประมวลผล PDF"""
        self.log_action(
            "PDF Processing",
            status,
            details,
            {
                'filename': pdf_file,
                'company_name': company_name
            }
        )
    
    def log_web_automation(self, action: str, status: str, details: str = ""):
        """บันทึกการทำงานกับเว็บ"""
        self.log_action(f"Web Automation - {action}", status, details)
    
    def log_file_operation(self, operation: str, file_path: str, status: str, details: str = ""):
        """บันทึกการทำงานกับไฟล์"""
        self.log_action(
            f"File Operation - {operation}",
            status,
            details,
            {'filename': Path(file_path).name}
        )
    
    def log_system_status(self, status: str, details: str = ""):
        """บันทึกสถานะระบบ"""
        self.log_action("System Status", status, details)
    
    def create_excel_report(self):
        """สร้างรายงาน Excel"""
        try:
            if not self.log_data:
                print("No log data to export")
                return False
            
            # สร้าง DataFrame
            df = pd.DataFrame(self.log_data)
            
            # จัดรูปแบบ timestamp
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['date'] = df['timestamp'].dt.date
            df['time'] = df['timestamp'].dt.time
            
            # จัดเรียงตาม timestamp
            df = df.sort_values('timestamp', ascending=False)
            
            # สร้างไฟล์ Excel
            with pd.ExcelWriter(self.excel_log_file, engine='openpyxl') as writer:
                # Sheet หลัก
                df.to_excel(writer, sheet_name='Bot Logs', index=False)
                
                # Sheet สรุปตามสถานะ
                status_summary = df['status'].value_counts()
                status_summary.to_excel(writer, sheet_name='Status Summary')
                
                # Sheet สรุปตามการทำงาน
                action_summary = df['action'].value_counts()
                action_summary.to_excel(writer, sheet_name='Action Summary')
                
                # Sheet สรุปตามบริษัท
                company_summary = df[df['company_name'] != '']['company_name'].value_counts()
                company_summary.to_excel(writer, sheet_name='Company Summary')
            
            print(f"Excel report created: {self.excel_log_file}")
            return True
            
        except Exception as e:
            print(f"Error creating Excel report: {e}")
            return False
    
    def create_text_report(self):
        """สร้างรายงานข้อความ"""
        try:
            with open(self.report_file, 'w', encoding='utf-8') as f:
                f.write("=== รายงานการทำงานของระบบบอท ===\n\n")
                f.write(f"วันที่สร้างรายงาน: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # สรุปสถิติ
                total_actions = len(self.log_data)
                success_count = len([log for log in self.log_data if log['status'] == 'SUCCESS'])
                error_count = len([log for log in self.log_data if log['status'] == 'ERROR'])
                warning_count = len([log for log in self.log_data if log['status'] == 'WARNING'])
                
                f.write(f"สถิติการทำงาน:\n")
                f.write(f"- จำนวนการทำงานทั้งหมด: {total_actions}\n")
                f.write(f"- สำเร็จ: {success_count}\n")
                f.write(f"- ผิดพลาด: {error_count}\n")
                f.write(f"- เตือน: {warning_count}\n\n")
                
                # รายละเอียดการทำงาน
                f.write("รายละเอียดการทำงาน:\n")
                f.write("-" * 50 + "\n")
                
                for log in self.log_data:
                    f.write(f"[{log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}] ")
                    f.write(f"{log['action']} - {log['status']}\n")
                    if log['details']:
                        f.write(f"  รายละเอียด: {log['details']}\n")
                    if log['filename']:
                        f.write(f"  ไฟล์: {log['filename']}\n")
                    if log['company_name']:
                        f.write(f"  บริษัท: {log['company_name']}\n")
                    f.write("\n")
            
            print(f"Text report created: {self.report_file}")
            return True
            
        except Exception as e:
            print(f"Error creating text report: {e}")
            return False
    
    def get_summary_stats(self) -> Dict:
        """ดึงสถิติสรุป"""
        if not self.log_data:
            return {}
        
        total = len(self.log_data)
        success = len([log for log in self.log_data if log['status'] == 'SUCCESS'])
        error = len([log for log in self.log_data if log['status'] == 'ERROR'])
        warning = len([log for log in self.log_data if log['status'] == 'WARNING'])
        
        return {
            'total_actions': total,
            'success_count': success,
            'error_count': error,
            'warning_count': warning,
            'success_rate': (success / total * 100) if total > 0 else 0
        }
    
    def clear_logs(self):
        """ล้างข้อมูล log"""
        self.log_data.clear()
        print("Log data cleared")
    
    def export_logs_to_csv(self, filename: str = "bot_logs.csv"):
        """ส่งออก log เป็น CSV"""
        try:
            if not self.log_data:
                print("No log data to export")
                return False
            
            df = pd.DataFrame(self.log_data)
            df.to_csv(filename, index=False, encoding='utf-8')
            print(f"Logs exported to CSV: {filename}")
            return True
            
        except Exception as e:
            print(f"Error exporting logs to CSV: {e}")
            return False
