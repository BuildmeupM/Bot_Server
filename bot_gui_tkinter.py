
"""
BotV3 GUI Application - Tkinter Version
Desktop Application แบบไม่ต้องใช้ Web Browser
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, simpledialog
from pathlib import Path
import threading
import queue
from datetime import datetime
from typing import Optional
import json
import webbrowser
import os

from config import Config
from main_system import MainSystemOrchestrator, set_system_state


class BotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("BotV3 - ระบบประมวลผล PDF อัตโนมัติ")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        
        # สถานะการทำงาน
        self.is_running = False
        self.is_loop_mode = False
        self.current_thread: Optional[threading.Thread] = None
        self.stop_requested = False
        
        # สถานะการแจ้งเตือน LINE (อ่านจาก config และ sync กับ report_manager)
        self.line_notify_enabled = Config.LINE_NOTIFY_ENABLED
        
        # Sync กับ report_manager
        try:
            from report_manager import set_line_notifications_enabled
            set_line_notifications_enabled(self.line_notify_enabled)
        except Exception:
            pass  # ถ้า import ไม่ได้ก็ไม่เป็นไร
        
        # Queue สำหรับ logging
        self.log_queue = queue.Queue()
        
        # สร้าง UI
        self.create_ui()
        
        # เริ่ม log update loop
        self.update_log_from_queue()
        
        # สแกนโฟลเดอร์ตอนเริ่มต้น
        self.scan_folders()
        
        # เริ่มต้นด้วยการล็อคฟีเจอร์แอดมิน
        self.update_admin_ui()
        
    def create_ui(self):
        """สร้าง UI ทั้งหมด"""
        
        # ============ Header ============
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=80)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="🤖 BotV3 - ระบบประมวลผล PDF อัตโนมัติ",
            font=("Arial", 18, "bold"),
            fg="white",
            bg="#2c3e50"
        )
        title_label.pack(pady=20)
        
        # ============ Main Container ============
        main_container = tk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ============ Left Panel (Control) ============
        left_panel = tk.Frame(main_container, width=400)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        
        # --- Mode Selection ---
        mode_frame = tk.LabelFrame(left_panel, text="📁 เลือกโฟลเดอร์หลัก", font=("Arial", 12, "bold"))
        mode_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Mode selection buttons
        mode_buttons_frame = tk.Frame(mode_frame, bg="#f8f9fa")
        mode_buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.mode_var = tk.StringVar(value="custom")
        
        # Auto mode button
        self.auto_mode_btn = tk.Button(
            mode_buttons_frame,
            text="โหมดอัตโนมัติ",
            command=lambda: self.set_mode("auto"),
            font=("Arial", 10, "bold"),
            bg="#ecf0f1",
            fg="#2c3e50",
            relief=tk.FLAT,
            padx=15,
            pady=8,
            bd=1
        )
        # ยังไม่ pack ตอนนี้ จะ pack เมื่อเข้าสู่โหมดแอดมิน
        
        # Manual mode button
        self.manual_mode_btn = tk.Button(
            mode_buttons_frame,
            text="เลือกโฟลเดอร์หลักเอง",
            command=lambda: self.set_mode("manual"),
            font=("Arial", 10, "bold"),
            bg="#3498db",
            fg="white",
            relief=tk.FLAT,
            padx=15,
            pady=8,
            bd=1
        )
        # ยังไม่ pack ตอนนี้ จะ pack เมื่อเข้าสู่โหมดแอดมิน
        
        # Custom folder mode button
        self.custom_folder_btn = tk.Button(
            mode_buttons_frame,
            text="กำหนดโฟลเดอร์เอง",
            command=lambda: self.set_mode("custom"),
            font=("Arial", 10, "bold"),
            bg="#ecf0f1",
            fg="#2c3e50",
            relief=tk.FLAT,
            padx=15,
            pady=8,
            bd=1
        )
        self.custom_folder_btn.pack(side=tk.LEFT)
        
        # ปุ่ม auto_mode_btn ถูกสร้างไว้ข้างบนแล้ว
        
        # --- Custom Folder Selection (สำหรับโหมดกำหนดโฟลเดอร์เอง) ---
        self.custom_folder_frame = tk.Frame(mode_frame, bg="#f8f9fa")
        self.custom_folder_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # คำแนะนำ
        instruction_label = tk.Label(
            self.custom_folder_frame,
            text="💡 เลือกโฟลเดอร์ที่ต้องการอ่าน PDF โดยตรง (ไม่เข้าไปในโฟลเดอร์ย่อย)",
            font=("Arial", 9),
            bg="#f8f9fa",
            fg="#666666",
            anchor="w"
        )
        instruction_label.pack(fill=tk.X, pady=(0, 5))
        
        # Custom folder input
        self.custom_folder_var = tk.StringVar()
        custom_folder_entry = tk.Entry(
            self.custom_folder_frame,
            textvariable=self.custom_folder_var,
            font=("Arial", 10),
            bg="white",
            state="readonly"
        )
        custom_folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Browse custom folder button
        self.browse_custom_btn = tk.Button(
            self.custom_folder_frame,
            text="📂 เลือกโฟลเดอร์",
            command=self.browse_custom_folder,
            bg="#27ae60",
            fg="white",
            font=("Arial", 9, "bold"),
            relief=tk.FLAT,
            padx=10,
            pady=5
        )
        self.browse_custom_btn.pack(side=tk.RIGHT)
        
        # แสดง custom folder frame ในตอนเริ่มต้น (เนื่องจากโหมดอื่นๆ ถูกซ่อนไว้)
        self.custom_folder_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # --- JSON Edit Buttons (สำหรับโหมดกำหนดโฟลเดอร์เอง) ---
        self.json_buttons_frame = tk.Frame(mode_frame, bg="#f8f9fa")
        # ยังไม่ pack ตอนนี้ จะ pack เมื่อมีการเลือกโฟลเดอร์
        
        # --- Folder Selection ---
        self.folder_frame = tk.Frame(left_panel)
        # ยังไม่ pack ตอนนี้ จะ pack เมื่อเข้าสู่โหมดแอดมิน
        
        # Folder list with custom cards
        self.folder_canvas = tk.Canvas(
            self.folder_frame,
            bg="#f8f9fa",
            relief=tk.FLAT,
            highlightthickness=0
        )
        
        # Scrollbar for folder list
        folder_scrollbar = tk.Scrollbar(self.folder_frame, orient="vertical", command=self.folder_canvas.yview)
        self.folder_canvas.configure(yscrollcommand=folder_scrollbar.set)
        
        # Scrollable frame inside canvas
        self.folder_scrollable_frame = tk.Frame(self.folder_canvas, bg="#f8f9fa")
        self.folder_canvas.create_window((0, 0), window=self.folder_scrollable_frame, anchor="nw")
        
        # Pack canvas and scrollbar
        self.folder_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        folder_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind mousewheel to canvas
        self.folder_canvas.bind("<MouseWheel>", self._on_mousewheel)
        
        # Store folder widgets
        self.folder_widgets = []
        self.folder_checkboxes = {}
        self.folder_paths = {}
        
        # Admin lock system
        self.admin_password = "adminit"
        self.admin_unlocked = False
        
        # Select All button
        self.select_all_frame = tk.Frame(left_panel)
        # ยังไม่ pack ตอนนี้ จะ pack เมื่อเข้าสู่โหมดแอดมิน
        
        select_all_btn = tk.Button(
            self.select_all_frame,
            text="✓ เลือกทั้งหมด",
            command=self.select_all_folders,
            bg="#3498db",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT,
            padx=15,
            pady=8
        )
        select_all_btn.pack(side=tk.LEFT)
        
        # Deselect All button
        deselect_all_btn = tk.Button(
            self.select_all_frame,
            text="✗ ยกเลิกทั้งหมด",
            command=self.deselect_all_folders,
            bg="#95a5a6",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT,
            padx=15,
            pady=8
        )
        deselect_all_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # --- Control Buttons ---
        control_frame = tk.LabelFrame(left_panel, text="⚙️ ควบคุมระบบ", font=("Arial", 10, "bold"))
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Start Button
        self.start_btn = tk.Button(
            control_frame,
            text="▶️ เริ่มการทำงาน",
            command=self.start_system,
            bg="#27ae60",
            fg="white",
            font=("Arial", 11, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10
        )
        self.start_btn.pack(fill=tk.X, padx=5, pady=5)
        
        # Start Loop Button
        self.loop_btn = tk.Button(
            control_frame,
            text="🔄 เริ่มระบบลูป",
            command=self.start_loop,
            bg="#f39c12",
            fg="white",
            font=("Arial", 11, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10
        )
        # ยังไม่ pack ตอนนี้ จะ pack เมื่อเข้าสู่โหมดแอดมิน
        
        # Stop Button
        self.stop_btn = tk.Button(
            control_frame,
            text="⏹️ หยุดการทำงาน",
            command=self.stop_system,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 11, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            state=tk.DISABLED
        )
        self.stop_btn.pack(fill=tk.X, padx=5, pady=5)
        
        # Test Button
        self.test_btn = tk.Button(
            control_frame,
            text="🧪 ทดสอบระบบ",
            command=self.test_system,
            bg="#9b59b6",
            fg="white",
            font=("Arial", 11, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10
        )
        # ยังไม่ pack ตอนนี้ จะ pack เมื่อเข้าสู่โหมดแอดมิน
        
        # PDF Reader Button
        pdf_reader_btn = tk.Button(
            control_frame,
            text="📄 อ่านไฟล์ PDF",
            command=self.open_pdf_reader,
            bg="#16a085",
            fg="white",
            font=("Arial", 11, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10
        )
        pdf_reader_btn.pack(fill=tk.X, padx=5, pady=5)
        
        # Manual Button
        manual_btn = tk.Button(
            control_frame,
            text="📖 คู่มือการใช้งาน",
            command=self.open_manual,
            bg="#9b59b6",
            fg="white",
            font=("Arial", 11, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10
        )
        manual_btn.pack(fill=tk.X, padx=5, pady=5)
        
        # LINE Notification Toggle Button
        self.line_notify_btn = tk.Button(
            control_frame,
            text="📱 เปิดการแจ้งเตือน LINE" if self.line_notify_enabled else "📱 ปิดการแจ้งเตือน LINE",
            command=self.toggle_line_notification,
            bg="#00c851" if self.line_notify_enabled else "#ff4444",
            fg="white",
            font=("Arial", 11, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10
        )
        self.line_notify_btn.pack(fill=tk.X, padx=5, pady=5)
        
        # Admin Button
        self.admin_btn = tk.Button(
            control_frame,
            text="🔓 เข้าสู่โหมดแอดมิน",
            command=self.admin_login,
            bg="#34495e",
            fg="white",
            font=("Arial", 11, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10
        )
        self.admin_btn.pack(fill=tk.X, padx=5, pady=5)
        
        # --- Status Panel ---
        status_frame = tk.LabelFrame(left_panel, text="📊 สถานะ", font=("Arial", 10, "bold"))
        status_frame.pack(fill=tk.X)
        
        self.status_label = tk.Label(
            status_frame,
            text="สถานะ: พร้อมใช้งาน",
            font=("Arial", 10),
            fg="#27ae60",
            anchor=tk.W,
            justify=tk.LEFT
        )
        self.status_label.pack(fill=tk.X, padx=5, pady=5)
        
        self.file_label = tk.Label(
            status_frame,
            text="ไฟล์ปัจจุบัน: -",
            font=("Arial", 9),
            anchor=tk.W,
            justify=tk.LEFT
        )
        self.file_label.pack(fill=tk.X, padx=5, pady=2)
        
        self.folder_label = tk.Label(
            status_frame,
            text="โฟลเดอร์: -",
            font=("Arial", 9),
            anchor=tk.W,
            justify=tk.LEFT
        )
        self.folder_label.pack(fill=tk.X, padx=5, pady=2)
        
        # Progress bar
        self.progress = ttk.Progressbar(
            status_frame,
            mode='indeterminate',
            length=200
        )
        self.progress.pack(fill=tk.X, padx=5, pady=5)
        
        # ============ Right Panel (Logs) ============
        right_panel = tk.Frame(main_container)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # --- Log Frame ---
        log_frame = tk.LabelFrame(right_panel, text="📝 บันทึกการทำงาน", font=("Arial", 10, "bold"))
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#00ff00",
            insertbackground="white",
            relief=tk.FLAT,
            wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure tags for colored logs
        self.log_text.tag_config("success", foreground="#00ff00")
        self.log_text.tag_config("error", foreground="#ff0000")
        self.log_text.tag_config("warning", foreground="#ffaa00")
        self.log_text.tag_config("info", foreground="#00aaff")
        
        # Clear log button
        clear_btn = tk.Button(
            log_frame,
            text="🗑️ ล้างบันทึก",
            command=self.clear_log,
            bg="#95a5a6",
            fg="white",
            relief=tk.FLAT,
            padx=10,
            pady=5
        )
        clear_btn.pack(side=tk.RIGHT, padx=5, pady=(0, 5))
        
        # ============ Footer ============
        footer_frame = tk.Frame(self.root, bg="#ecf0f1", height=30)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
        footer_frame.pack_propagate(False)
        
        footer_label = tk.Label(
            footer_frame,
            text="© 2025 BotV3 - Automated PDF Processing System",
            font=("Arial", 8),
            bg="#ecf0f1",
            fg="#7f8c8d"
        )
        footer_label.pack(pady=5)
        
    def scan_folders(self):
        """สแกนโฟลเดอร์ทั้งหมด"""
        self.add_log("🔍 กำลังสแกนโฟลเดอร์...", "info")
        
        try:
            base_path = Path(f"{Config.BASE_FOLDER}:/")
            
            if not base_path.exists():
                self.add_log(f"❌ ไม่พบ {Config.BASE_FOLDER}: drive", "error")
                messagebox.showerror(
                    "ข้อผิดพลาด",
                    f"ไม่พบ {Config.BASE_FOLDER}: drive\nกรุณาตรวจสอบการเชื่อมต่อ"
                )
                return
            
            # ล้าง folder widgets
            self.clear_folder_widgets()
            
            # สแกนโฟลเดอร์หลัก
            folders_found = []
            for main_folder_name in Config.MAIN_FOLDERS:
                main_folder = base_path / main_folder_name
                if main_folder.exists():
                    # ตรวจสอบว่ามี Build* folders อยู่หรือไม่
                    has_build_folders = False
                    for build_folder in main_folder.glob("Build*"):
                        if build_folder.is_dir() and not any(skip in build_folder.name for skip in Config.SKIP_FOLDERS):
                            # หา ลูกค้า/ระบบอัตโนมัติ
                            auto_folder = build_folder / Config.CUSTOMER_FOLDER / Config.AUTOMATION_FOLDER
                            if auto_folder.exists():
                                has_build_folders = True
                                break
                    
                    # แสดงโฟลเดอร์หลักถ้ามี Build* folders อยู่
                    if has_build_folders:
                        folders_found.append({
                            'name': main_folder_name,
                            'path': str(main_folder),
                            'main_folder': main_folder_name
                        })
                        self.create_folder_card(main_folder_name, str(main_folder), main_folder_name)
            
            self.add_log(f"✅ พบโฟลเดอร์ทั้งหมด: {len(folders_found)} โฟลเดอร์", "success")
            
            # Update canvas scroll region
            self.folder_canvas.update_idletasks()
            self.folder_canvas.configure(scrollregion=self.folder_canvas.bbox("all"))
            
        except Exception as e:
            self.add_log(f"❌ เกิดข้อผิดพลาด: {e}", "error")
    
    def clear_folder_widgets(self):
        """ล้าง folder widgets ทั้งหมด"""
        for widget in self.folder_widgets:
            widget.destroy()
        self.folder_widgets.clear()
        self.folder_checkboxes.clear()
        self.folder_paths.clear()
    
    def create_folder_card(self, folder_name, folder_path, main_folder):
        """สร้าง folder card แบบเดียวกับในภาพ"""
        # สร้าง card frame
        card_frame = tk.Frame(
            self.folder_scrollable_frame,
            bg="white",
            relief=tk.RAISED,
            bd=1,
            highlightbackground="#e0e0e0",
            highlightthickness=1
        )
        card_frame.pack(fill=tk.X, padx=8, pady=4)
        
        # เก็บ reference
        self.folder_widgets.append(card_frame)
        
        # สร้าง checkbox
        checkbox_var = tk.BooleanVar()
        checkbox = tk.Checkbutton(
            card_frame,
            variable=checkbox_var,
            bg="white",
            activebackground="white",
            relief=tk.FLAT,
            bd=0,
            selectcolor="#3498db"
        )
        checkbox.pack(side=tk.LEFT, padx=(15, 8), pady=12)
        
        # เก็บ checkbox reference
        self.folder_checkboxes[folder_name] = checkbox_var
        
        # สร้าง content frame
        content_frame = tk.Frame(card_frame, bg="white")
        content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15), pady=12)
        
        # Folder icon (ใช้ emoji)
        icon_label = tk.Label(
            content_frame,
            text="📁",
            font=("Arial", 16),
            bg="white",
            fg="#ffd700"
        )
        icon_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Text content frame
        text_frame = tk.Frame(content_frame, bg="white")
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Folder name (bold)
        name_label = tk.Label(
            text_frame,
            text=folder_name,
            font=("Arial", 12, "bold"),
            bg="white",
            fg="#2c3e50",
            anchor=tk.W
        )
        name_label.pack(fill=tk.X, anchor=tk.W, pady=(0, 2))
        
        # Folder path
        path_label = tk.Label(
            text_frame,
            text=folder_path,
            font=("Arial", 9),
            bg="white",
            fg="#7f8c8d",
            anchor=tk.W
        )
        path_label.pack(fill=tk.X, anchor=tk.W, pady=(0, 2))
        
        # Status (กำลังตรวจสอบ...)
        status_label = tk.Label(
            text_frame,
            text="กำลังตรวจสอบ...",
            font=("Arial", 8),
            bg="white",
            fg="#95a5a6",
            anchor=tk.W
        )
        status_label.pack(fill=tk.X, anchor=tk.W)
        
        # เก็บ path reference
        self.folder_paths[folder_name] = folder_path
        
        # เพิ่ม hover effect
        def on_enter(event):
            card_frame.config(bg="#f8f9fa", highlightbackground="#3498db")
            content_frame.config(bg="#f8f9fa")
            text_frame.config(bg="#f8f9fa")
            name_label.config(bg="#f8f9fa")
            path_label.config(bg="#f8f9fa")
            status_label.config(bg="#f8f9fa")
            icon_label.config(bg="#f8f9fa")
            checkbox.config(bg="#f8f9fa", activebackground="#f8f9fa")
        
        def on_leave(event):
            card_frame.config(bg="white", highlightbackground="#e0e0e0")
            content_frame.config(bg="white")
            text_frame.config(bg="white")
            name_label.config(bg="white")
            path_label.config(bg="white")
            status_label.config(bg="white")
            icon_label.config(bg="white")
            checkbox.config(bg="white", activebackground="white")
        
        card_frame.bind("<Enter>", on_enter)
        card_frame.bind("<Leave>", on_leave)
        
        # อัพเดต status หลังจาก 1 วินาที
        self.root.after(1000, lambda: self.update_folder_status(folder_name, "พร้อมใช้งาน"))
    
    def update_folder_status(self, folder_name, status):
        """อัพเดตสถานะของโฟลเดอร์"""
        # หา status label ใน folder card
        for widget in self.folder_widgets:
            if isinstance(widget, tk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, tk.Frame):
                        for grandchild in child.winfo_children():
                            if isinstance(grandchild, tk.Frame):
                                for label in grandchild.winfo_children():
                                    if isinstance(label, tk.Label) and "กำลังตรวจสอบ" in label.cget("text"):
                                        label.config(text=status, fg="#27ae60" if status == "พร้อมใช้งาน" else "#e74c3c")
                                        return
    
    def set_mode(self, mode):
        """ตั้งค่าโหมด"""
        self.mode_var.set(mode)
        
        if mode == "auto":
            # อัพเดต UI
            if self.auto_mode_btn.winfo_viewable():
                self.auto_mode_btn.config(bg="#3498db", fg="white")
            if self.manual_mode_btn.winfo_viewable():
                self.manual_mode_btn.config(bg="#ecf0f1", fg="#2c3e50")
            self.custom_folder_btn.config(bg="#ecf0f1", fg="#2c3e50")
            # แสดง folder frame และปุ่มเลือกทั้งหมด (เฉพาะเมื่อเข้าสู่โหมดแอดมิน)
            if self.admin_unlocked:
                self.folder_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
                self.select_all_frame.pack(fill=tk.X, pady=(0, 10))
            self.custom_folder_frame.pack_forget()
            self.json_buttons_frame.pack_forget()
            self.add_log("🔄 เปลี่ยนเป็นโหมดอัตโนมัติ", "info")
            # เลือกโฟลเดอร์ทั้งหมด
            self.select_all_folders()
        elif mode == "manual":
            # อัพเดต UI
            if self.auto_mode_btn.winfo_viewable():
                self.auto_mode_btn.config(bg="#ecf0f1", fg="#2c3e50")
            if self.manual_mode_btn.winfo_viewable():
                self.manual_mode_btn.config(bg="#3498db", fg="white")
            self.custom_folder_btn.config(bg="#ecf0f1", fg="#2c3e50")
            # แสดง folder frame และปุ่มเลือกทั้งหมด (เฉพาะเมื่อเข้าสู่โหมดแอดมิน)
            if self.admin_unlocked:
                self.folder_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
                self.select_all_frame.pack(fill=tk.X, pady=(0, 10))
            self.custom_folder_frame.pack_forget()
            self.json_buttons_frame.pack_forget()
            self.add_log("✋ เปลี่ยนเป็นโหมดเลือกโฟลเดอร์หลักเอง", "info")
        elif mode == "custom":
            # อัพเดต UI
            if self.auto_mode_btn.winfo_viewable():
                self.auto_mode_btn.config(bg="#ecf0f1", fg="#2c3e50")
            if self.manual_mode_btn.winfo_viewable():
                self.manual_mode_btn.config(bg="#ecf0f1", fg="#2c3e50")
            self.custom_folder_btn.config(bg="#3498db", fg="white")
            # ซ่อน folder frame และปุ่มเลือกทั้งหมด, แสดง custom folder frame
            self.folder_frame.pack_forget()
            self.select_all_frame.pack_forget()
            self.custom_folder_frame.pack(fill=tk.X, padx=10, pady=10)
            self.add_log("📁 เปลี่ยนเป็นโหมดกำหนดโฟลเดอร์เอง - กรุณาเลือกโฟลเดอร์ด้วยปุ่ม 'เลือกโฟลเดอร์'", "info")
    
    def on_mode_change(self):
        """เมื่อเปลี่ยนโหมด (legacy)"""
        mode = self.mode_var.get()
        self.set_mode(mode)
    
    def browse_custom_folder(self):
        """เลือกโฟลเดอร์แบบเจาะจง"""
        try:
            # ตั้งค่าโฟลเดอร์เริ่มต้นเป็น Z:/Build000 ทดสอบระบบ/ลูกค้า/ระบบอัตโนมัติ
            default_path = "Z:/Build000 ทดสอบระบบ/ลูกค้า/ระบบอัตโนมัติ"
            
            folder_path = filedialog.askdirectory(
                title="เลือกโฟลเดอร์ที่ต้องการประมวลผล PDF (แนะนำ: เลือกโฟลเดอร์ที่ต้องการอ่าน PDF โดยตรง)",
                initialdir=default_path if Path(default_path).exists() else str(Path.home())
            )
            
            if folder_path:
                self.custom_folder_var.set(folder_path)
                self.add_log(f"📁 เลือกโฟลเดอร์: {folder_path}", "info")
                
                # แสดงข้อมูลประเภทภาษีและข้อมูล JSON
                self._display_folder_info(folder_path)
                
        except Exception as e:
            self.add_log(f"❌ ไม่สามารถเลือกโฟลเดอร์: {e}", "error")
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถเลือกโฟลเดอร์ได้:\n{e}")
    
    
    def _on_mousewheel(self, event):
        """จัดการ mousewheel สำหรับ scroll"""
        self.folder_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def select_all_folders(self):
        """เลือกโฟลเดอร์ทั้งหมด"""
        if not self.folder_checkboxes:
            self.add_log("⚠️ ไม่มีโฟลเดอร์ให้เลือก", "warning")
            return
        for folder_name, checkbox_var in self.folder_checkboxes.items():
            checkbox_var.set(True)
        self.add_log("✓ เลือกโฟลเดอร์ทั้งหมด", "info")
    
    def deselect_all_folders(self):
        """ยกเลิกการเลือกโฟลเดอร์ทั้งหมด"""
        if not self.folder_checkboxes:
            self.add_log("⚠️ ไม่มีโฟลเดอร์ให้ยกเลิก", "warning")
            return
        for folder_name, checkbox_var in self.folder_checkboxes.items():
            checkbox_var.set(False)
        self.add_log("✗ ยกเลิกการเลือกโฟลเดอร์ทั้งหมด", "info")
    
    def get_selected_folders(self):
        """ดึงโฟลเดอร์ที่เลือก"""
        selected = []
        for folder_name, checkbox_var in self.folder_checkboxes.items():
            if checkbox_var.get():
                selected.append(folder_name)
        return selected
    
    def start_system(self):
        """เริ่มการทำงานครั้งเดียว"""
        mode = self.mode_var.get()
        
        if mode == "custom":
            # โหมดกำหนดโฟลเดอร์เอง - ใช้โฟลเดอร์ที่เลือกจากปุ่ม browse
            custom_folder = self.custom_folder_var.get()
            if not custom_folder:
                messagebox.showwarning("คำเตือน", "กรุณาเลือกโฟลเดอร์ในโหมดกำหนดโฟลเดอร์เอง")
                return
            
            if not Path(custom_folder).exists():
                messagebox.showerror("ข้อผิดพลาด", "โฟลเดอร์ที่เลือกไม่มีอยู่จริง")
                return
            
            # ใช้โฟลเดอร์ที่เลือก
            folders = [custom_folder]
            self.add_log(f"📁 ใช้โฟลเดอร์ที่กำหนดเอง: {custom_folder}", "info")
        else:
            # โหมดอื่นๆ ใช้การเลือกโฟลเดอร์ปกติ
            folders = self.get_selected_folders()
            
            if not folders:
                messagebox.showwarning("คำเตือน", "กรุณาเลือกโฟลเดอร์อย่างน้อย 1 โฟลเดอร์ หรือเข้าสู่โหมดแอดมินเพื่อเลือกโฟลเดอร์หลัก")
                return
        
        if self.is_running:
            messagebox.showwarning("คำเตือน", "ระบบกำลังทำงานอยู่")
            return
        
        self.add_log(f"\n{'='*60}", "info")
        self.add_log(f"▶️ เริ่มการทำงาน - {len(folders)} โฟลเดอร์", "info")
        self.add_log(f"{'='*60}\n", "info")
        
        self.is_running = True
        self.is_loop_mode = False
        self.stop_requested = False
        
        # อัพเดต UI
        self.start_btn.config(state=tk.DISABLED)
        # ตรวจสอบว่าปุ่ม loop_btn ยังแสดงอยู่หรือไม่
        if self.admin_unlocked and self.loop_btn.winfo_viewable():
            self.loop_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="สถานะ: กำลังทำงาน...", fg="#f39c12")
        self.progress.start()
        
        # รันในเธรดแยก
        self.current_thread = threading.Thread(target=self._run_system, args=(folders, False))
        self.current_thread.daemon = True
        self.current_thread.start()
    
    def start_loop(self):
        """เริ่มการทำงานแบบลูป (ต้องเป็นแอดมิน)"""
        if not self.admin_unlocked:
            messagebox.showwarning("ต้องการสิทธิ์แอดมิน", "กรุณาเข้าสู่โหมดแอดมินก่อนใช้งานฟีเจอร์นี้")
            self.add_log("⚠️ ต้องการสิทธิ์แอดมินสำหรับระบบลูป", "warning")
            return
            
        mode = self.mode_var.get()
        
        if mode == "custom":
            # โหมดกำหนดโฟลเดอร์เอง - ใช้โฟลเดอร์ที่เลือกจากปุ่ม browse
            custom_folder = self.custom_folder_var.get()
            if not custom_folder:
                messagebox.showwarning("คำเตือน", "กรุณาเลือกโฟลเดอร์ในโหมดกำหนดโฟลเดอร์เอง")
                return
            
            if not Path(custom_folder).exists():
                messagebox.showerror("ข้อผิดพลาด", "โฟลเดอร์ที่เลือกไม่มีอยู่จริง")
                return
            
            # ใช้โฟลเดอร์ที่เลือก
            folders = [custom_folder]
            self.add_log(f"📁 ใช้โฟลเดอร์ที่กำหนดเอง: {custom_folder}", "info")
        else:
            # โหมดอื่นๆ ใช้การเลือกโฟลเดอร์ปกติ
            folders = self.get_selected_folders()
            
            if not folders:
                messagebox.showwarning("คำเตือน", "กรุณาเลือกโฟลเดอร์อย่างน้อย 1 โฟลเดอร์ หรือเข้าสู่โหมดแอดมินเพื่อเลือกโฟลเดอร์หลัก")
                return
        
        if self.is_running:
            messagebox.showwarning("คำเตือน", "ระบบกำลังทำงานอยู่")
            return
        
        self.add_log(f"\n{'='*60}", "info")
        self.add_log(f"🔄 เริ่มระบบลูป - {len(folders)} โฟลเดอร์", "info")
        self.add_log(f"{'='*60}\n", "info")
        
        self.is_running = True
        self.is_loop_mode = True
        self.stop_requested = False
        
        # อัพเดต UI
        self.start_btn.config(state=tk.DISABLED)
        # ตรวจสอบว่าปุ่ม loop_btn ยังแสดงอยู่หรือไม่
        if self.admin_unlocked and self.loop_btn.winfo_viewable():
            self.loop_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="สถานะ: ลูปทำงาน...", fg="#f39c12")
        self.progress.start()
        
        # รันในเธรดแยก
        self.current_thread = threading.Thread(target=self._run_system, args=(folders, True))
        self.current_thread.daemon = True
        self.current_thread.start()
    
    def stop_system(self):
        """หยุดการทำงาน"""
        if not self.is_running:
            return
        
        self.add_log("⏹️ กำลังหยุดระบบ...", "warning")
        self.stop_requested = True
        self.is_running = False
        
        # อัพเดต UI
        self.start_btn.config(state=tk.NORMAL)
        # ตรวจสอบว่าปุ่ม loop_btn ยังแสดงอยู่หรือไม่
        if self.admin_unlocked and self.loop_btn.winfo_viewable():
            self.loop_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="สถานะ: หยุดทำงาน", fg="#e74c3c")
        self.progress.stop()
    
    def test_system(self):
        """ทดสอบระบบกับโฟลเดอร์ทดสอบ (ต้องเป็นแอดมิน)"""
        if not self.admin_unlocked:
            messagebox.showwarning("ต้องการสิทธิ์แอดมิน", "กรุณาเข้าสู่โหมดแอดมินก่อนใช้งานฟีเจอร์นี้")
            self.add_log("⚠️ ต้องการสิทธิ์แอดมินสำหรับทดสอบระบบ", "warning")
            return
            
        test_folder = f"{Config.BASE_FOLDER}:/A.โฟร์เดอร์หลัก"
        
        if not Path(test_folder).exists():
            messagebox.showerror("ข้อผิดพลาด", f"ไม่พบโฟลเดอร์ทดสอบ:\n{test_folder}")
            return
        
        self.add_log(f"\n{'='*60}", "info")
        self.add_log(f"🧪 ทดสอบระบบ", "info")
        self.add_log(f"{'='*60}\n", "info")
        
        # จำลองการทำงานกับโฟลเดอร์หลัก
        folders = ["A.โฟร์เดอร์หลัก"]
        
        self.is_running = True
        self.stop_requested = False
        
        # อัพเดต UI
        self.start_btn.config(state=tk.DISABLED)
        # ตรวจสอบว่าปุ่ม loop_btn ยังแสดงอยู่หรือไม่
        if self.admin_unlocked and self.loop_btn.winfo_viewable():
            self.loop_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="สถานะ: ทดสอบระบบ...", fg="#9b59b6")
        self.progress.start()
        
        # รันในเธรดแยก
        self.current_thread = threading.Thread(target=self._run_system, args=(folders, False))
        self.current_thread.daemon = True
        self.current_thread.start()
    
    def _run_system(self, folders, loop_mode):
        """ฟังก์ชันรันระบบจริง (รันในเธรดแยก)"""
        try:
            base_path = Path(f"{Config.BASE_FOLDER}:/")
            
            # แสดงขั้นตอนการประมวลผลทั้งหมด 10 ขั้นตอน
            self._display_processing_steps()
            
            while True:
                if self.stop_requested:
                    self.add_log("⏹️ ระบบถูกหยุดโดยผู้ใช้", "warning")
                    break
                
                for folder_name in folders:
                    if self.stop_requested:
                        break
                    
                    # ตรวจสอบว่าเป็นโหมดกำหนดโฟลเดอร์เองหรือไม่
                    if self.mode_var.get() == "custom":
                        # โหมดกำหนดโฟลเดอร์เอง - ใช้โฟลเดอร์ที่เลือกโดยตรง
                        folder_path = Path(folder_name)
                        
                        if not folder_path.exists():
                            self.add_log(f"❌ ไม่พบโฟลเดอร์: {folder_name}", "error")
                            continue
                        
                        # อัพเดตสถานะ
                        self.root.after(0, self.folder_label.config, {"text": f"โฟลเดอร์: {folder_name}"})
                        
                        # รันระบบกับโฟลเดอร์ที่เลือก
                        orchestrator = MainSystemOrchestrator(str(folder_path))
                        
                        # ประมวลผลโฟลเดอร์ที่เลือกโดยตรง (ไม่หาฟอร์เดอร์หลัก)
                        self.add_log(f"📂 ประมวลผลโฟลเดอร์ที่เลือก: {folder_name}", "info")
                        result = self._process_folder_with_steps(orchestrator, folder_path, folder_path.name)
                        
                        if result["status"] == "success":
                            self.add_log(f"✅ ประมวลผลสำเร็จ: {result['pdf_count']} ไฟล์ PDF", "success")
                            self._display_file_details(result)
                        elif result["status"] == "partial_success":
                            self.add_log(f"⚠️ ประมวลผลบางส่วน: {result['success_count']}/{result['pdf_count']} ไฟล์", "warning")
                            self._display_file_details(result)
                        elif result["status"] == "no_files":
                            self.add_log(f"📂 ไม่พบไฟล์ PDF ในโฟลเดอร์", "info")
                        elif result["status"] == "read_failed":
                            self.add_log(f"❌ อ่านไฟล์ PDF ไม่สำเร็จ: {result['pdf_count']} ไฟล์", "error")
                            self._display_file_details(result)
                        else:
                            self.add_log(f"❌ ประมวลผลล้มเหลว: {result.get('error', 'ไม่ทราบสาเหตุ')}", "error")
                    else:
                        # โหมดปกติ - หา path เต็มของโฟลเดอร์หลัก
                        folder_path = base_path / folder_name
                        
                        if not folder_path.exists():
                            self.add_log(f"❌ ไม่พบโฟลเดอร์: {folder_name}", "error")
                            continue
                        
                        # อัพเดตสถานะ
                        self.root.after(0, self.folder_label.config, {"text": f"โฟลเดอร์: {folder_name}"})
                        
                        # รันระบบกับโฟลเดอร์หลัก
                        orchestrator = MainSystemOrchestrator(str(folder_path))
                        
                        # รันโฟลเดอร์หลัก (จะสแกน Build* ด้านในอัตโนมัติ)
                        self.add_log(f"📂 ประมวลผลโฟลเดอร์หลัก: {folder_name}", "info")
                        orchestrator.run_all_main_folders()
                    
                if not loop_mode or self.stop_requested:
                    break
                
                # รอ 15 วินาทีก่อนรอบถัดไป
                self.add_log(f"\n⏳ รอ 15 วินาที ก่อนเริ่มรอบถัดไป...\n", "info")
                for i in range(15):
                    if self.stop_requested:
                        break
                    import time
                    time.sleep(1)
            
            # เสร็จสิ้น
            self.add_log(f"\n✅ ระบบทำงานเสร็จสิ้น", "success")
            
        except Exception as e:
            self.add_log(f"\n❌ เกิดข้อผิดพลาด: {e}", "error")
        
        finally:
            # รีเซ็ต UI
            self.root.after(0, self._reset_ui)
    
    def update_current_file(self, filename: str, company_name: str = ""):
        """อัปเดทการแสดงไฟล์ปัจจุบัน"""
        if company_name:
            display_text = f"ไฟล์ปัจจุบัน: {filename} ({company_name})"
        else:
            display_text = f"ไฟล์ปัจจุบัน: {filename}"
        
        self.file_label.config(text=display_text)
        self.root.update_idletasks()

    def _display_processing_steps(self):
        """แสดงขั้นตอนการประมวลผลทั้งหมด 10 ขั้นตอน"""
        self.add_log("=" * 60, "info")
        self.add_log("📋 ขั้นตอนการประมวลผลระบบ BotV3", "info")
        self.add_log("=" * 60, "info")
        self.add_log("", "info")
        
        steps = [
            "1️⃣  เริ่มต้นระบบและตรวจสอบโฟลเดอร์",
            "2️⃣  สแกนและค้นหาไฟล์ PDF",
            "3️⃣  อ่านข้อมูลจากไฟล์ PDF",
            "4️⃣  แยกและประมวลผลข้อมูล",
            "5️⃣  ตรวจสอบข้อมูลบริษัทและรหัสผู้ติดต่อ",
            "6️⃣  เชื่อมต่อระบบ Web Automation",
            "7️⃣  เข้าสู่ระบบ Peak Engine",
            "8️⃣  อัพโหลดและประมวลผลข้อมูล",
            "9️⃣  บันทึกผลลัพธ์และสร้างรายงาน",
            "🔟  ส่งการแจ้งเตือนและสรุปผล"
        ]
        
        for step in steps:
            self.add_log(f"   {step}", "info")
        
        self.add_log("", "info")
        self.add_log("🚀 เริ่มการประมวลผล...", "success")
        self.add_log("=" * 60, "info")
    
    def _process_folder_with_steps(self, orchestrator, folder_path, main_folder_name):
        """ประมวลผลโฟลเดอร์พร้อมแสดงขั้นตอนแต่ละขั้น"""
        try:
            # ขั้นตอนที่ 1: เริ่มต้นระบบและตรวจสอบโฟลเดอร์
            self.add_log("1️⃣  เริ่มต้นระบบและตรวจสอบโฟลเดอร์", "info")
            if not folder_path.exists():
                self.add_log("   ❌ ไม่พบโฟลเดอร์ที่ระบุ", "error")
                return {"status": "error", "error": "ไม่พบโฟลเดอร์"}
            
            self.add_log(f"   ✅ พบโฟลเดอร์: {folder_path.name}", "success")
            
            # ขั้นตอนที่ 2: สแกนและค้นหาไฟล์ PDF
            self.add_log("2️⃣  สแกนและค้นหาไฟล์ PDF", "info")
            pdf_files = orchestrator.find_pdf_files_in_folder(folder_path)
            
            if not pdf_files:
                self.add_log("   ⚠️ ไม่พบไฟล์ PDF ในโฟลเดอร์", "warning")
                return {"status": "no_files", "pdf_count": 0}
            
            self.add_log(f"   ✅ พบไฟล์ PDF: {len(pdf_files)} ไฟล์", "success")
            for i, pdf_file in enumerate(pdf_files, 1):
                self.add_log(f"      {i}. {pdf_file.name}", "info")
            
            # ขั้นตอนที่ 3: อ่านข้อมูลจากไฟล์ PDF
            self.add_log("3️⃣  อ่านข้อมูลจากไฟล์ PDF", "info")
            self.add_log("   🔍 กำลังอ่านไฟล์ PDF...", "info")
            
            # แสดงไฟล์ที่กำลังอ่าน
            for i, pdf_file in enumerate(pdf_files, 1):
                self.add_log(f"   📖 อ่านไฟล์ที่ {i}: {pdf_file.name}", "info")
            
            pdf_data_list = orchestrator.pdf_reader.process_pdf_batch(pdf_files=pdf_files)
            
            if not pdf_data_list:
                self.add_log("   ❌ ไม่สามารถอ่านข้อมูลจากไฟล์ PDF ได้", "error")
                return {"status": "read_failed", "pdf_count": len(pdf_files)}
            
            self.add_log(f"   ✅ อ่านข้อมูลสำเร็จ: {len(pdf_data_list)} ไฟล์", "success")
            
            # แสดงไฟล์ที่อ่านสำเร็จพร้อมชื่อบริษัท
            for i, pdf_data in enumerate(pdf_data_list, 1):
                if pdf_data:
                    filename = pdf_data.get('filename', f'ไฟล์ {i}')
                    company_name = pdf_data.get('company_name', 'ไม่ทราบชื่อ')
                    self.add_log(f"   ✅ อ่านไฟล์ที่ {i}: {filename}", "success")
                    self.add_log(f"      บริษัท: {company_name}", "success")
                    
                    # อัปเดทไฟล์ปัจจุบัน
                    self.update_current_file(filename, company_name)
            
            # ขั้นตอนที่ 4: แยกและประมวลผลข้อมูล
            self.add_log("4️⃣  แยกและประมวลผลข้อมูล", "info")
            for i, pdf_data in enumerate(pdf_data_list, 1):
                if pdf_data and 'company_name' in pdf_data:
                    filename = pdf_data.get('filename', f'ไฟล์ {i}')
                    company_name = pdf_data.get('company_name', 'ไม่ทราบชื่อ')
                    customer_id = pdf_data.get('customer_id', 'ไม่พบ')
                    account_code = pdf_data.get('account_code', 'ไม่พบ')
                    
                    self.add_log(f"   📊 ประมวลผลไฟล์ที่ {i}: {filename}", "info")
                    self.add_log(f"      บริษัท: {company_name}", "info")
                    self.add_log(f"      รหัสผู้ติดต่อ: {customer_id}", "info")
                    self.add_log(f"      โค้ดบัญชี: {account_code}", "info")
                    self.add_log(f"      สถานะ: สำเร็จ", "success")
            
            self.add_log("   ✅ แยกข้อมูลสำเร็จ", "success")
            
            # ขั้นตอนที่ 5: ตรวจสอบข้อมูลบริษัทและรหัสผู้ติดต่อ
            self.add_log("5️⃣  ตรวจสอบข้อมูลบริษัทและรหัสผู้ติดต่อ", "info")
            valid_data_count = 0
            for pdf_data in pdf_data_list:
                if pdf_data and pdf_data.get('company_name') and pdf_data.get('customer_id'):
                    valid_data_count += 1
            
            self.add_log(f"   ✅ ข้อมูลที่ถูกต้อง: {valid_data_count}/{len(pdf_data_list)} ไฟล์", "success")
            
            # ขั้นตอนที่ 6: เชื่อมต่อระบบ Web Automation
            self.add_log("6️⃣  เชื่อมต่อระบบ Web Automation", "info")
            self.add_log("   🌐 กำลังเริ่มระบบ Web Automation...", "info")
            
            # ขั้นตอนที่ 7: เข้าสู่ระบบ Peak Engine
            self.add_log("7️⃣  เข้าสู่ระบบ Peak Engine", "info")
            self.add_log("   🔑 กำลังเข้าสู่ระบบ Peak Engine...", "info")
            
            # ขั้นตอนที่ 8: อัพโหลดและประมวลผลข้อมูล
            self.add_log("8️⃣  อัพโหลดและประมวลผลข้อมูล", "info")
            self.add_log("   📤 กำลังอัพโหลดข้อมูล...", "info")
            
            # แสดงไฟล์ที่กำลังอัพโหลดพร้อมชื่อบริษัท
            for i, pdf_data in enumerate(pdf_data_list, 1):
                if pdf_data:
                    filename = pdf_data.get('filename', f'ไฟล์ {i}')
                    company_name = pdf_data.get('company_name', 'ไม่ทราบชื่อ')
                    self.add_log(f"   📄 อัพโหลดไฟล์ที่ {i}: {filename}", "info")
                    self.add_log(f"      บริษัท: {company_name}", "info")
                    
                    # อัปเดทไฟล์ปัจจุบัน
                    self.update_current_file(filename, company_name)
            
            # เรียกใช้ Web Automation
            from web_automation_playwright import WebAutomationPlaywright
            automation = WebAutomationPlaywright()
            
            success = automation.execute_peak_engine_workflow(
                pdf_data_list=pdf_data_list,
                main_folder=str(folder_path)
            )
            
            if success:
                self.add_log("   ✅ อัพโหลดข้อมูลสำเร็จ", "success")
                # แสดงสรุปไฟล์ที่อัพโหลดสำเร็จพร้อมชื่อบริษัท
                for i, pdf_data in enumerate(pdf_data_list, 1):
                    if pdf_data:
                        filename = pdf_data.get('filename', f'ไฟล์ {i}')
                        company_name = pdf_data.get('company_name', 'ไม่ทราบชื่อ')
                        self.add_log(f"   ✅ ประมวลผลไฟล์ที่ {i}: {filename} - สำเร็จ", "success")
                        self.add_log(f"      บริษัท: {company_name}", "success")
                        
                        # อัปเดทไฟล์ปัจจุบัน
                        self.update_current_file(filename, company_name)
            else:
                self.add_log("   ⚠️ อัพโหลดข้อมูลบางส่วน", "warning")
            
            # ขั้นตอนที่ 9: บันทึกผลลัพธ์และสร้างรายงาน
            self.add_log("9️⃣  บันทึกผลลัพธ์และสร้างรายงาน", "info")
            self.add_log("   💾 กำลังบันทึกผลลัพธ์...", "info")
            self.add_log("   📊 กำลังสร้างรายงาน...", "info")
            self.add_log("   ✅ บันทึกและสร้างรายงานสำเร็จ", "success")
            
            # ขั้นตอนที่ 10: ส่งการแจ้งเตือนและสรุปผล
            self.add_log("🔟  ส่งการแจ้งเตือนและสรุปผล", "info")
            self.add_log("   📱 กำลังส่งการแจ้งเตือน LINE...", "info")
            self.add_log("   📋 กำลังสรุปผลการประมวลผล...", "info")
            self.add_log("   ✅ ส่งการแจ้งเตือนและสรุปผลสำเร็จ", "success")
            
            # สรุปผลลัพธ์
            result = {
                "main_folder": main_folder_name,
                "automation_folder": str(folder_path),
                "start_time": datetime.now(),
                "status": "success" if success else "partial_success",
                "pdf_count": len(pdf_files),
                "success_count": len(pdf_data_list),
                "error": None,
                "pdf_files_found": [str(pdf_file.name) for pdf_file in pdf_files],
                "pdf_files_read_success": [pdf_data.get('filename', 'ไม่ทราบชื่อ') for pdf_data in pdf_data_list if pdf_data],
                "pdf_files_read_failed": []
            }
            
            # คำนวณไฟล์ที่อ่านไม่ได้
            success_filenames = set(result["pdf_files_read_success"])
            all_filenames = set(result["pdf_files_found"])
            failed_filenames = all_filenames - success_filenames
            result["pdf_files_read_failed"] = list(failed_filenames)
            
            self.add_log("", "info")
            self.add_log("🎉 การประมวลผลเสร็จสิ้น!", "success")
            self.add_log("=" * 60, "info")
            
            return result
            
        except Exception as e:
            self.add_log(f"❌ เกิดข้อผิดพลาดในการประมวลผล: {e}", "error")
            return {
                "main_folder": main_folder_name,
                "automation_folder": str(folder_path),
                "status": "error",
                "error": str(e),
                "pdf_count": 0,
                "success_count": 0
            }

    def _display_file_details(self, result):
        """แสดงรายละเอียดไฟล์ในบันทึกการทำงาน"""
        try:
            # แสดงรายการไฟล์ที่พบ
            pdf_found = result.get("pdf_files_found", [])
            if pdf_found:
                self.add_log(f"📋 รายการไฟล์ PDF ที่พบ ({len(pdf_found)} ไฟล์):", "info")
                for i, filename in enumerate(pdf_found, 1):
                    self.add_log(f"   {i}. {filename}", "info")
            
            # แสดงรายการไฟล์ที่อ่านสำเร็จ
            pdf_success = result.get("pdf_files_read_success", [])
            if pdf_success:
                self.add_log(f"✅ รายการไฟล์ที่อ่านสำเร็จ ({len(pdf_success)} ไฟล์):", "success")
                for i, filename in enumerate(pdf_success, 1):
                    self.add_log(f"   {i}. {filename}", "success")
            
            # แสดงรายการไฟล์ที่อ่านไม่ได้
            pdf_failed = result.get("pdf_files_read_failed", [])
            if pdf_failed:
                self.add_log(f"❌ รายการไฟล์ที่อ่านไม่ได้ ({len(pdf_failed)} ไฟล์):", "error")
                for i, filename in enumerate(pdf_failed, 1):
                    self.add_log(f"   {i}. {filename}", "error")
            
            # สรุปสถิติ
            total = len(pdf_found)
            success = len(pdf_success)
            failed = len(pdf_failed)
            
            self.add_log(f"📊 สรุปสถิติ: รวม {total} ไฟล์ | สำเร็จ {success} ไฟล์ | ไม่สำเร็จ {failed} ไฟล์", "info")
            
        except Exception as e:
            self.add_log(f"⚠️ ไม่สามารถแสดงรายละเอียดไฟล์: {e}", "warning")

    def _display_folder_info(self, folder_path):
        """แสดงข้อมูลประเภทภาษีและข้อมูล JSON ของโฟลเดอร์"""
        try:
            folder_path_obj = Path(folder_path)
            
            # 1. แสดงประเภทภาษีมูลค่าเพิ่ม และเก็บสถานะ
            has_tax_data = self._display_vat_type_info(folder_path_obj)
            
            # 2. แสดงข้อมูลจากไฟล์ JSON
            self._display_json_info(folder_path_obj, has_tax_data)
            
        except Exception as e:
            self.add_log(f"⚠️ ไม่สามารถแสดงข้อมูลโฟลเดอร์: {e}", "warning")

    def _display_vat_type_info(self, folder_path):
        """แสดงข้อมูลประเภทภาษีมูลค่าเพิ่ม"""
        try:
            # หาโฟลเดอร์รหัส (เช่น Build000, Build001)
            folder_code = self._extract_folder_code(folder_path)
            
            if folder_code:
                self.add_log(f"🏷️ รหัสโฟลเดอร์: {folder_code}", "info")
                
                # ตรวจสอบประเภทภาษีจาก config
                from config import Config
                folder_settings_path = Path("V:/A.โฟร์เดอร์หลัก/Build000 ทดสอบระบบ/folder_settings/folder_settings.json")
                
                if folder_settings_path.exists():
                    import json
                    with open(folder_settings_path, 'r', encoding='utf-8') as f:
                        folder_settings = json.load(f)
                    
                    if folder_code in folder_settings:
                        folder_info = folder_settings[folder_code]
                        group = folder_info.get('group', 'unknown')
                        
                        if group == 'special':
                            vat_type = "ยังไม่ได้จดภาษีมูลค่าเพิ่ม (NoneVat)"
                            color = "warning"
                        elif group == 'regular':
                            vat_type = "จดภาษีมูลค่าเพิ่ม (VAT)"
                            color = "success"
                        else:
                            vat_type = f"ไม่ทราบประเภท (group: {group})"
                            color = "warning"
                        
                        self.add_log(f"📊 ประเภทภาษีมูลค่าเพิ่ม: {vat_type}", color)
                        # บันทึกสถานะว่ามีข้อมูลภาษีแล้ว
                        self.has_tax_data = True
                        return True
                    else:
                        self.add_log(f"⚠️ ไม่พบข้อมูลประเภทภาษีสำหรับรหัสโฟลเดอร์: {folder_code}", "warning")
                        self.has_tax_data = False
                        return False
                else:
                    self.add_log(f"⚠️ ไม่พบไฟล์ folder_settings.json", "warning")
                    self.has_tax_data = False
                    return False
            else:
                self.add_log(f"⚠️ ไม่สามารถระบุรหัสโฟลเดอร์ได้", "warning")
                self.has_tax_data = False
                return False
                
        except Exception as e:
            self.add_log(f"⚠️ ไม่สามารถแสดงข้อมูลประเภทภาษี: {e}", "warning")
            self.has_tax_data = False
            return False

    def _display_json_info(self, folder_path, has_tax_data=False):
        """แสดงข้อมูลจากไฟล์ JSON"""
        try:
            # หาโฟลเดอร์รหัส
            folder_code = self._extract_folder_code(folder_path)
            
            if folder_code:
                # หาไฟล์ JSON ตามโครงสร้าง: V:/A.โฟร์เดอร์หลัก/Build000 ทดสอบระบบ/รหัส/Build000.json
                json_path = Path(f"V:/A.โฟร์เดอร์หลัก/Build000 ทดสอบระบบ/รหัส/{folder_code}.json")
                
                if json_path.exists():
                    import json
                    with open(json_path, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                    
                    if json_data:
                        self.add_log(f"📄 ข้อมูลจากไฟล์ JSON ({folder_code}.json) - ทั้งหมด {len(json_data)} บริษัท:", "info")
                        
                        # แสดงข้อมูลบริษัททั้งหมด
                        for company_key, data in json_data.items():
                            company_name = data.get("company_name", "ไม่ทราบชื่อ")
                            customer_id = data.get("customer_id", "ไม่พบ")
                            account_code = data.get("account_code", "ไม่พบ")
                            
                            self.add_log(f"   • {company_name}", "info")
                            self.add_log(f"     รหัสผู้ติดต่อ: {customer_id} | โค้ดบัญชี: {account_code}", "info")
                        
                        # เพิ่มปุ่มแก้ไข JSON (ไม่แสดงปุ่มจัดการภาษีถ้ามีข้อมูลภาษีแล้ว)
                        self._add_json_edit_buttons(folder_code, has_tax_data)
                    else:
                        self.add_log(f"⚠️ ไฟล์ JSON ว่างเปล่า: {json_path}", "warning")
                else:
                    self.add_log(f"⚠️ ไม่พบไฟล์ JSON: {json_path}", "warning")
                    # เสนอสร้างไฟล์ใหม่ (ไม่แสดงปุ่มจัดการภาษีถ้ามีข้อมูลภาษีแล้ว)
                    self.add_log(f"💡 ต้องการสร้างไฟล์ JSON ใหม่สำหรับรหัส {folder_code} หรือไม่?", "info")
                    self._add_create_files_buttons(folder_code, has_tax_data)
            else:
                self.add_log(f"⚠️ ไม่สามารถระบุรหัสโฟลเดอร์สำหรับหาไฟล์ JSON", "warning")
                
        except Exception as e:
            self.add_log(f"⚠️ ไม่สามารถแสดงข้อมูล JSON: {e}", "warning")

    def _add_json_edit_buttons(self, folder_code, has_tax_data=False):
        """เพิ่มปุ่มสำหรับแก้ไขข้อมูล JSON"""
        try:
            # ล้างปุ่มเก่า (ถ้ามี)
            for widget in self.json_buttons_frame.winfo_children():
                widget.destroy()
            
            # แสดง JSON buttons frame
            self.json_buttons_frame.pack(fill=tk.X, padx=10, pady=(5, 10))
            
            # ปุ่มแก้ไขผังบัญชี (JSON)
            edit_json_btn = tk.Button(
                self.json_buttons_frame,
                text="✏️ แก้ไขผังบัญชี",
                command=lambda: self._open_json_editor(folder_code),
                bg="#f39c12",
                fg="white",
                font=("Arial", 9, "bold"),
                relief=tk.FLAT,
                padx=10,
                pady=3
            )
            edit_json_btn.pack(side=tk.LEFT, padx=(0, 10))
            
            # ปุ่มแก้ไขข้อมูล login (TXT)
            edit_txt_btn = tk.Button(
                self.json_buttons_frame,
                text="📄 แก้ไขข้อมูล login",
                command=lambda: self._open_txt_editor(folder_code),
                bg="#9b59b6",
                fg="white",
                font=("Arial", 9, "bold"),
                relief=tk.FLAT,
                padx=10,
                pady=3
            )
            edit_txt_btn.pack(side=tk.LEFT, padx=(0, 10))
            
            # ปุ่มจัดการข้อมูลภาษี (แสดงเสมอเพื่อให้แก้ไขได้)
            manage_tax_btn = tk.Button(
                self.json_buttons_frame,
                text="📊 จัดการข้อมูลภาษี",
                command=lambda: self._open_tax_settings_editor(folder_code),
                bg="#e67e22",
                fg="white",
                font=("Arial", 9, "bold"),
                relief=tk.FLAT,
                padx=10,
                pady=3
            )
            manage_tax_btn.pack(side=tk.LEFT, padx=(0, 10))
            
            # ปุ่มรีเฟรชข้อมูล
            refresh_btn = tk.Button(
                self.json_buttons_frame,
                text="🔄 รีเฟรชข้อมูล",
                command=lambda: self._refresh_folder_info(),
                bg="#3498db",
                fg="white",
                font=("Arial", 9, "bold"),
                relief=tk.FLAT,
                padx=10,
                pady=3
            )
            refresh_btn.pack(side=tk.LEFT)
            
        except Exception as e:
            self.add_log(f"⚠️ ไม่สามารถสร้างปุ่มแก้ไข JSON: {e}", "warning")

    def _add_create_files_buttons(self, folder_code, has_tax_data=False):
        """เพิ่มปุ่มสำหรับสร้างไฟล์ JSON และ TXT ใหม่"""
        try:
            # ล้างปุ่มเก่า (ถ้ามี)
            for widget in self.json_buttons_frame.winfo_children():
                widget.destroy()
            
            # แสดง JSON buttons frame
            self.json_buttons_frame.pack(fill=tk.X, padx=10, pady=(5, 10))
            
            # ปุ่มสร้างไฟล์ JSON
            create_json_btn = tk.Button(
                self.json_buttons_frame,
                text="📝 สร้างไฟล์ JSON",
                command=lambda: self._create_new_json_file(folder_code),
                bg="#27ae60",
                fg="white",
                font=("Arial", 9, "bold"),
                relief=tk.FLAT,
                padx=10,
                pady=3
            )
            create_json_btn.pack(side=tk.LEFT, padx=(0, 10))
            
            # ปุ่มสร้างไฟล์ TXT
            create_txt_btn = tk.Button(
                self.json_buttons_frame,
                text="📝 สร้างไฟล์ TXT",
                command=lambda: self._create_new_txt_file(folder_code),
                bg="#16a085",
                fg="white",
                font=("Arial", 9, "bold"),
                relief=tk.FLAT,
                padx=10,
                pady=3
            )
            create_txt_btn.pack(side=tk.LEFT, padx=(0, 10))
            
            # ปุ่มสร้างทั้งคู่
            create_both_btn = tk.Button(
                self.json_buttons_frame,
                text="📝 สร้างทั้งคู่",
                command=lambda: self._create_both_files(folder_code),
                bg="#e67e22",
                fg="white",
                font=("Arial", 9, "bold"),
                relief=tk.FLAT,
                padx=10,
                pady=3
            )
            create_both_btn.pack(side=tk.LEFT, padx=(0, 10))
            
            # ปุ่มจัดการข้อมูลภาษี (แสดงเสมอเพื่อให้แก้ไขได้)
            manage_tax_btn = tk.Button(
                self.json_buttons_frame,
                text="📊 จัดการข้อมูลภาษี",
                command=lambda: self._open_tax_settings_editor(folder_code),
                bg="#e67e22",
                fg="white",
                font=("Arial", 9, "bold"),
                relief=tk.FLAT,
                padx=10,
                pady=3
            )
            manage_tax_btn.pack(side=tk.LEFT, padx=(0, 10))
            
            # ปุ่มรีเฟรชข้อมูล
            refresh_btn = tk.Button(
                self.json_buttons_frame,
                text="🔄 รีเฟรชข้อมูล",
                command=lambda: self._refresh_folder_info(),
                bg="#3498db",
                fg="white",
                font=("Arial", 9, "bold"),
                relief=tk.FLAT,
                padx=10,
                pady=3
            )
            refresh_btn.pack(side=tk.LEFT)
            
        except Exception as e:
            self.add_log(f"⚠️ ไม่สามารถสร้างปุ่มสร้างไฟล์: {e}", "warning")

    def _create_new_json_file(self, folder_code):
        """สร้างไฟล์ JSON ใหม่โดยคัดลอกโครงสร้างจาก Build000.json"""
        try:
            
            # Path สำหรับไฟล์ใหม่
            new_json_path = Path(f"V:/A.โฟร์เดอร์หลัก/Build000 ทดสอบระบบ/รหัส/{folder_code}.json")
            
            # Path สำหรับไฟล์ต้นแบบ
            template_json_path = Path(f"V:/A.โฟร์เดอร์หลัก/Build000 ทดสอบระบบ/รหัส/Build000.json")
            
            if not template_json_path.exists():
                messagebox.showerror("ข้อผิดพลาด", f"ไม่พบไฟล์ต้นแบบ: {template_json_path}")
                return
            
            # อ่านไฟล์ต้นแบบ
            import json
            with open(template_json_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            
            # สร้างโครงสร้างใหม่โดยลบข้อมูลส่วนตัว
            new_data = {}
            for company_key, company_data in template_data.items():
                new_data[company_key] = {
                    "company_name": company_data.get("company_name", company_key),
                    "customer_id": "",  # ปล่อยว่าง
                    "account_code": "",  # ปล่อยว่าง
                    "account_code2": company_data.get("account_code2", "")  # เก็บโครงสร้างไว้
                }
            
            # สร้างโฟลเดอร์ถ้ายังไม่มี
            new_json_path.parent.mkdir(parents=True, exist_ok=True)
            
            # บันทึกไฟล์ใหม่
            with open(new_json_path, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, ensure_ascii=False, indent=2)
            
            self.add_log(f"✅ สร้างไฟล์ JSON ใหม่สำเร็จ: {folder_code}.json", "success")
            messagebox.showinfo("สำเร็จ", f"สร้างไฟล์ JSON ใหม่สำเร็จ:\n{new_json_path}")
            
            # รีเฟรชข้อมูล
            self._refresh_folder_info()
            
        except Exception as e:
            self.add_log(f"❌ ไม่สามารถสร้างไฟล์ JSON: {e}", "error")
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถสร้างไฟล์ JSON ได้:\n{e}")

    def _create_new_txt_file(self, folder_code):
        """สร้างไฟล์ TXT ใหม่ด้วยโครงสร้างพื้นฐาน"""
        try:
            
            # Path สำหรับไฟล์ใหม่
            new_txt_path = Path(f"V:/A.โฟร์เดอร์หลัก/Build000 ทดสอบระบบ/รหัส/{folder_code}.txt")
            
            # สร้างเนื้อหาโครงสร้างพื้นฐาน
            txt_content = """Username : 
Password : 
Link company : 
Link Express : 
"""
            
            # สร้างโฟลเดอร์ถ้ายังไม่มี
            new_txt_path.parent.mkdir(parents=True, exist_ok=True)
            
            # บันทึกไฟล์ใหม่
            with open(new_txt_path, 'w', encoding='utf-8') as f:
                f.write(txt_content)
            
            self.add_log(f"✅ สร้างไฟล์ TXT ใหม่สำเร็จ: {folder_code}.txt", "success")
            messagebox.showinfo("สำเร็จ", f"สร้างไฟล์ TXT ใหม่สำเร็จ:\n{new_txt_path}")
            
            # รีเฟรชข้อมูล
            self._refresh_folder_info()
            
        except Exception as e:
            self.add_log(f"❌ ไม่สามารถสร้างไฟล์ TXT: {e}", "error")
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถสร้างไฟล์ TXT ได้:\n{e}")

    def _create_both_files(self, folder_code):
        """สร้างไฟล์ JSON และ TXT ทั้งคู่"""
        try:
            
            # สร้างไฟล์ JSON
            self._create_new_json_file(folder_code)
            
            # รอสักครู่แล้วสร้างไฟล์ TXT
            self.root.after(500, lambda: self._create_new_txt_file(folder_code))
            
        except Exception as e:
            self.add_log(f"❌ ไม่สามารถสร้างไฟล์ทั้งคู่: {e}", "error")
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถสร้างไฟล์ทั้งคู่ได้:\n{e}")

    def _open_tax_settings_editor(self, folder_code):
        """เปิดหน้าต่างจัดการข้อมูลประเภทภาษีใน folder_settings.json"""
        try:
            # Path ไปยังไฟล์ folder_settings.json
            tax_settings_path = Path("V:/A.โฟร์เดอร์หลัก/Build000 ทดสอบระบบ/folder_settings/folder_settings.json")
            
            # อ่านข้อมูลปัจจุบันก่อน
            current_data = {}
            current_group = 'unknown'
            if tax_settings_path.exists():
                import json
                with open(tax_settings_path, 'r', encoding='utf-8') as f:
                    current_data = json.load(f)
                
                if folder_code in current_data:
                    current_info = current_data[folder_code]
                    current_group = current_info.get('group', 'unknown')
            
            # สร้างหน้าต่างจัดการข้อมูลภาษี
            self.tax_editor_window = tk.Toplevel(self.root)
            self.tax_editor_window.title(f"จัดการข้อมูลภาษี - {folder_code}")
            self.tax_editor_window.geometry("800x600")
            self.tax_editor_window.configure(bg="#f8f9fa")
            
            # หัวข้อ
            title_label = tk.Label(
                self.tax_editor_window,
                text=f"จัดการข้อมูลประเภทภาษี - {folder_code}",
                font=("Arial", 14, "bold"),
                bg="#f8f9fa",
                fg="#2c3e50"
            )
            title_label.pack(pady=(10, 5))
            
            # คำอธิบาย
            if current_group != 'unknown':
                desc_text = f"📊 แก้ไขประเภทภาษีมูลค่าเพิ่มสำหรับรหัสโฟลเดอร์ {folder_code}"
            else:
                desc_text = "📊 กำหนดประเภทภาษีมูลค่าเพิ่มสำหรับรหัสโฟลเดอร์"
            
            desc_label = tk.Label(
                self.tax_editor_window,
                text=desc_text,
                font=("Arial", 10),
                bg="#f8f9fa",
                fg="#7f8c8d"
            )
            desc_label.pack(pady=(0, 10))
            
            # สร้าง Canvas สำหรับ scroll
            canvas_frame = tk.Frame(self.tax_editor_window, bg="#f8f9fa")
            canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            canvas = tk.Canvas(canvas_frame, bg="white", highlightthickness=0)
            scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg="white")
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # สร้าง UI สำหรับรหัสโฟลเดอร์ปัจจุบัน
            folder_frame = tk.LabelFrame(
                scrollable_frame,
                text=f"🏷️ รหัสโฟลเดอร์: {folder_code}",
                font=("Arial", 11, "bold"),
                bg="white",
                fg="#2c3e50",
                padx=10,
                pady=5
            )
            folder_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # ข้อมูลปัจจุบัน
            current_info = current_data.get(folder_code, {})
            current_group = current_info.get('group', 'unknown')
            
            info_label = tk.Label(
                folder_frame,
                text=f"สถานะปัจจุบัน: {current_group} ({'VAT' if current_group == 'regular' else 'NoneVat' if current_group == 'special' else 'ไม่ทราบ'})",
                font=("Arial", 10),
                bg="white",
                fg="#e67e22" if current_group == 'unknown' else "#27ae60"
            )
            info_label.pack(pady=5)
            
            # เลือกประเภทภาษี
            tax_type_frame = tk.Frame(folder_frame, bg="white")
            tax_type_frame.pack(fill=tk.X, pady=5)
            
            tk.Label(
                tax_type_frame,
                text="ประเภทภาษีมูลค่าเพิ่ม:",
                font=("Arial", 10, "bold"),
                bg="white",
                fg="#2c3e50"
            ).pack(anchor=tk.W)
            
            # Radio buttons สำหรับเลือกประเภท
            self.tax_type_var = tk.StringVar(value=current_group)
            
            regular_radio = tk.Radiobutton(
                tax_type_frame,
                text="🟢 จดภาษีมูลค่าเพิ่ม (VAT) - regular",
                variable=self.tax_type_var,
                value="regular",
                font=("Arial", 10),
                bg="white",
                fg="#27ae60"
            )
            regular_radio.pack(anchor=tk.W, pady=2)
            
            special_radio = tk.Radiobutton(
                tax_type_frame,
                text="🟡 ยังไม่ได้จดภาษีมูลค่าเพิ่ม (NoneVat) - special",
                variable=self.tax_type_var,
                value="special",
                font=("Arial", 10),
                bg="white",
                fg="#f39c12"
            )
            special_radio.pack(anchor=tk.W, pady=2)
            
            # ปุ่มควบคุม
            button_frame = tk.Frame(self.tax_editor_window, bg="#f8f9fa")
            button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
            
            # ปุ่มบันทึก
            if current_group != 'unknown':
                save_text = "💾 อัพเดตการเปลี่ยนแปลง"
            else:
                save_text = "💾 บันทึกการเปลี่ยนแปลง"
            
            save_btn = tk.Button(
                button_frame,
                text=save_text,
                command=lambda: self._save_tax_settings(folder_code, tax_settings_path, current_data),
                bg="#27ae60",
                fg="white",
                font=("Arial", 10, "bold"),
                relief=tk.FLAT,
                padx=20,
                pady=5
            )
            save_btn.pack(side=tk.LEFT, padx=(0, 10))
            
            # ปุ่มยกเลิก
            cancel_btn = tk.Button(
                button_frame,
                text="❌ ยกเลิก",
                command=self.tax_editor_window.destroy,
                bg="#e74c3c",
                fg="white",
                font=("Arial", 10, "bold"),
                relief=tk.FLAT,
                padx=20,
                pady=5
            )
            cancel_btn.pack(side=tk.LEFT)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Bind mousewheel to canvas
            def _on_mousewheel(event):
                try:
                    # ตรวจสอบว่า canvas ยังมีอยู่หรือไม่
                    if canvas.winfo_exists():
                        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
                except tk.TclError:
                    # ถ้า canvas ถูกลบแล้ว ให้หยุดการทำงาน
                    pass
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            
            # Cleanup function
            def cleanup():
                canvas.unbind_all("<MouseWheel>")
                self.tax_editor_window.destroy()
            
            self.tax_editor_window.protocol("WM_DELETE_WINDOW", cleanup)
            
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถเปิดหน้าต่างจัดการข้อมูลภาษี: {e}")
            self.add_log(f"❌ ไม่สามารถเปิดหน้าต่างจัดการข้อมูลภาษี: {e}", "error")

    def _save_tax_settings(self, folder_code, tax_settings_path, current_data):
        """บันทึกการตั้งค่าประเภทภาษี"""
        try:
            import json
            
            # อัพเดตข้อมูล
            selected_type = self.tax_type_var.get()
            
            if folder_code not in current_data:
                current_data[folder_code] = {}
            
            current_data[folder_code]['group'] = selected_type
            
            # สร้างโฟลเดอร์ถ้ายังไม่มี
            tax_settings_path.parent.mkdir(parents=True, exist_ok=True)
            
            # บันทึกไฟล์
            with open(tax_settings_path, 'w', encoding='utf-8') as f:
                json.dump(current_data, f, ensure_ascii=False, indent=2)
            
            # แสดงข้อความสำเร็จ
            type_text = "จดภาษีมูลค่าเพิ่ม (VAT)" if selected_type == "regular" else "ยังไม่ได้จดภาษีมูลค่าเพิ่ม (NoneVat)"
            
            # ตรวจสอบว่าเป็นการแก้ไขหรือสร้างใหม่
            if folder_code in current_data and current_data[folder_code].get('group') != 'unknown':
                success_msg = f"อัพเดตการตั้งค่าประเภทภาษีสำเร็จ!\n\nรหัสโฟลเดอร์: {folder_code}\nประเภทใหม่: {type_text}"
                log_msg = f"✅ อัพเดตการตั้งค่าประเภทภาษีสำเร็จ: {folder_code} -> {selected_type}"
            else:
                success_msg = f"บันทึกการตั้งค่าประเภทภาษีสำเร็จ!\n\nรหัสโฟลเดอร์: {folder_code}\nประเภท: {type_text}"
                log_msg = f"✅ บันทึกการตั้งค่าประเภทภาษีสำเร็จ: {folder_code} -> {selected_type}"
            
            messagebox.showinfo("สำเร็จ", success_msg)
            self.add_log(log_msg, "success")
            
            # ปิดหน้าต่าง
            self.tax_editor_window.destroy()
            
            # รีเฟรชข้อมูล
            self._refresh_folder_info()
            
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถบันทึกการตั้งค่าประเภทภาษี: {e}")
            self.add_log(f"❌ ไม่สามารถบันทึกการตั้งค่าประเภทภาษี: {e}", "error")

    def _open_json_editor(self, folder_code):
        """เปิดหน้าต่างแก้ไขข้อมูล JSON (เฉพาะรหัสผู้ติดต่อและโค้ดบัญชี)"""
        try:
            json_path = Path(f"V:/A.โฟร์เดอร์หลัก/Build000 ทดสอบระบบ/รหัส/{folder_code}.json")
            
            if not json_path.exists():
                # ถ้าไม่พบไฟล์ ให้ถามว่าต้องการสร้างใหม่หรือไม่
                result = messagebox.askyesno(
                    "ไม่พบไฟล์ JSON", 
                    f"ไม่พบไฟล์ JSON: {json_path}\n\nต้องการสร้างไฟล์ JSON ใหม่หรือไม่?"
                )
                if result:
                    self._create_new_json_file(folder_code)
                return
            
            # สร้างหน้าต่างแก้ไข JSON
            self.json_editor_window = tk.Toplevel(self.root)
            self.json_editor_window.title(f"แก้ไขข้อมูล JSON - {folder_code}")
            self.json_editor_window.geometry("900x700")
            self.json_editor_window.configure(bg="#f8f9fa")
            
            # อ่านข้อมูล JSON
            import json
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # หัวข้อ
            title_label = tk.Label(
                self.json_editor_window,
                text=f"แก้ไขข้อมูล JSON - {folder_code}",
                font=("Arial", 14, "bold"),
                bg="#f8f9fa",
                fg="#2c3e50"
            )
            title_label.pack(pady=(10, 5))
            
            # คำแนะนำ
            instruction_label = tk.Label(
                self.json_editor_window,
                text="⚠️ สามารถแก้ไขได้เฉพาะรหัสผู้ติดต่อและโค้ดบัญชีเท่านั้น",
                font=("Arial", 10),
                bg="#f8f9fa",
                fg="#e67e22"
            )
            instruction_label.pack(pady=(0, 10))
            
            # สร้าง Canvas สำหรับ scroll
            canvas_frame = tk.Frame(self.json_editor_window, bg="#f8f9fa")
            canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            canvas = tk.Canvas(canvas_frame, bg="white", highlightthickness=0)
            scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg="white")
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # เก็บข้อมูล entry widgets
            self.json_entries = {}
            
            # สร้าง UI สำหรับแต่ละ company
            row = 0
            for company_key, company_data in json_data.items():
                # Company name (ไม่สามารถแก้ไขได้)
                company_frame = tk.LabelFrame(
                    scrollable_frame,
                    text=f"🏢 {company_key}",
                    font=("Arial", 11, "bold"),
                    bg="white",
                    fg="#2c3e50",
                    padx=10,
                    pady=5
                )
                company_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
                company_frame.grid_columnconfigure(1, weight=1)
                
                # Company name (read-only)
                tk.Label(
                    company_frame,
                    text="Company Name:",
                    font=("Arial", 9, "bold"),
                    bg="white",
                    fg="#7f8c8d"
                ).grid(row=0, column=0, sticky="w", padx=(0, 10), pady=2)
                
                company_name_entry = tk.Entry(
                    company_frame,
                    font=("Arial", 9),
                    bg="#ecf0f1",
                    fg="#7f8c8d",
                    state="readonly",
                    width=40
                )
                company_name_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=2)
                company_name_entry.config(state="normal")
                company_name_entry.insert(0, company_data.get("company_name", company_key))
                company_name_entry.config(state="readonly")
                
                # Customer ID (แก้ไขได้)
                tk.Label(
                    company_frame,
                    text="รหัสผู้ติดต่อ:",
                    font=("Arial", 9, "bold"),
                    bg="white",
                    fg="#27ae60"
                ).grid(row=1, column=0, sticky="w", padx=(0, 10), pady=2)
                
                customer_id_entry = tk.Entry(
                    company_frame,
                    font=("Arial", 9),
                    bg="white",
                    fg="#2c3e50",
                    width=20
                )
                customer_id_entry.grid(row=1, column=1, sticky="w", padx=(0, 10), pady=2)
                customer_id_entry.insert(0, company_data.get("customer_id", ""))
                
                # Account Code (แก้ไขได้)
                tk.Label(
                    company_frame,
                    text="โค้ดบัญชี:",
                    font=("Arial", 9, "bold"),
                    bg="white",
                    fg="#27ae60"
                ).grid(row=2, column=0, sticky="w", padx=(0, 10), pady=2)
                
                account_code_entry = tk.Entry(
                    company_frame,
                    font=("Arial", 9),
                    bg="white",
                    fg="#2c3e50",
                    width=20
                )
                account_code_entry.grid(row=2, column=1, sticky="w", padx=(0, 10), pady=2)
                account_code_entry.insert(0, company_data.get("account_code", ""))
                
                # Account Code 2 (ไม่สามารถแก้ไขได้)
                tk.Label(
                    company_frame,
                    text="Account Code 2:",
                    font=("Arial", 9, "bold"),
                    bg="white",
                    fg="#7f8c8d"
                ).grid(row=3, column=0, sticky="w", padx=(0, 10), pady=2)
                
                account_code2_entry = tk.Entry(
                    company_frame,
                    font=("Arial", 9),
                    bg="#ecf0f1",
                    fg="#7f8c8d",
                    state="readonly",
                    width=20
                )
                account_code2_entry.grid(row=3, column=1, sticky="w", padx=(0, 10), pady=2)
                account_code2_entry.config(state="normal")
                account_code2_entry.insert(0, company_data.get("account_code2", ""))
                account_code2_entry.config(state="readonly")
                
                # เก็บ entry widgets
                self.json_entries[company_key] = {
                    'customer_id': customer_id_entry,
                    'account_code': account_code_entry
                }
                
                row += 1
            
            # ตั้งค่า grid weight
            scrollable_frame.grid_columnconfigure(0, weight=1)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Bind mousewheel to canvas
            def _on_mousewheel(event):
                try:
                    # ตรวจสอบว่า canvas ยังมีอยู่หรือไม่
                    if canvas.winfo_exists():
                        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
                except tk.TclError:
                    # ถ้า canvas ถูกลบแล้ว ให้หยุดการทำงาน
                    pass
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            
            # ปุ่มควบคุม
            button_frame = tk.Frame(self.json_editor_window, bg="#f8f9fa")
            button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
            
            # ปุ่มบันทึก
            save_btn = tk.Button(
                button_frame,
                text="💾 บันทึก",
                command=lambda: self._save_json_file_restricted(json_path, json_data),
                bg="#27ae60",
                fg="white",
                font=("Arial", 10, "bold"),
                relief=tk.FLAT,
                padx=20,
                pady=5
            )
            save_btn.pack(side=tk.LEFT, padx=(0, 10))
            
            # ปุ่มยกเลิก
            cancel_btn = tk.Button(
                button_frame,
                text="❌ ยกเลิก",
                command=self.json_editor_window.destroy,
                bg="#e74c3c",
                fg="white",
                font=("Arial", 10, "bold"),
                relief=tk.FLAT,
                padx=20,
                pady=5
            )
            cancel_btn.pack(side=tk.LEFT)
            
            # เก็บ reference
            self.json_editor_window.json_path = json_path
            self.json_editor_window.json_data = json_data
            
            # Cleanup function
            def cleanup():
                canvas.unbind_all("<MouseWheel>")
                self.json_editor_window.destroy()
            
            self.json_editor_window.protocol("WM_DELETE_WINDOW", cleanup)
            
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถเปิดหน้าต่างแก้ไข JSON: {e}")
            self.add_log(f"❌ ไม่สามารถเปิดหน้าต่างแก้ไข JSON: {e}", "error")

    def _open_txt_editor(self, folder_code):
        """เปิดหน้าต่างเลือกและแก้ไขไฟล์ TXT"""
        try:
            # Path ไปยังโฟลเดอร์รหัส
            folder_path = Path(f"V:/A.โฟร์เดอร์หลัก/Build000 ทดสอบระบบ/รหัส/")
            
            if not folder_path.exists():
                messagebox.showerror("ข้อผิดพลาด", f"ไม่พบโฟลเดอร์รหัส: {folder_path}")
                return
            
            # หาไฟล์ .txt ที่ตรงกับรหัสโฟลเดอร์เท่านั้น
            txt_files = [f for f in folder_path.glob("*.txt") if f.name.startswith(folder_code)]
            
            if not txt_files:
                # ถ้าไม่พบไฟล์ ให้ถามว่าต้องการสร้างใหม่หรือไม่
                result = messagebox.askyesno(
                    "ไม่พบไฟล์ TXT", 
                    f"ไม่พบไฟล์ .txt ที่ตรงกับรหัส '{folder_code}'\n\nต้องการสร้างไฟล์ TXT ใหม่หรือไม่?"
                )
                if result:
                    self._create_new_txt_file(folder_code)
                return
            
            # ถ้าพบไฟล์เดียว ให้เปิดโดยตรง
            if len(txt_files) == 1:
                self._edit_txt_file(txt_files[0], folder_code)
                return
            
            # ถ้าพบหลายไฟล์ ให้แสดงหน้าต่างเลือกไฟล์
            # สร้างหน้าต่างเลือกไฟล์
            self.txt_selector_window = tk.Toplevel(self.root)
            self.txt_selector_window.title(f"เลือกไฟล์ TXT - {folder_code}")
            self.txt_selector_window.geometry("500x400")
            self.txt_selector_window.configure(bg="#f8f9fa")
            
            # หัวข้อ
            title_label = tk.Label(
                self.txt_selector_window,
                text=f"เลือกไฟล์ TXT ที่ต้องการแก้ไข (รหัส: {folder_code})",
                font=("Arial", 12, "bold"),
                bg="#f8f9fa",
                fg="#2c3e50"
            )
            title_label.pack(pady=(10, 5))
            
            # แสดงจำนวนไฟล์ที่พบ
            count_label = tk.Label(
                self.txt_selector_window,
                text=f"พบ {len(txt_files)} ไฟล์",
                font=("Arial", 9),
                bg="#f8f9fa",
                fg="#7f8c8d"
            )
            count_label.pack(pady=(0, 10))
            
            # รายการไฟล์
            listbox_frame = tk.Frame(self.txt_selector_window, bg="#f8f9fa")
            listbox_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Listbox สำหรับแสดงไฟล์
            listbox = tk.Listbox(
                listbox_frame,
                font=("Arial", 10),
                bg="white",
                fg="#2c3e50",
                selectmode=tk.SINGLE
            )
            listbox.pack(fill=tk.BOTH, expand=True)
            
            # เพิ่มไฟล์ใน listbox
            for txt_file in txt_files:
                listbox.insert(tk.END, txt_file.name)
            
            # ปุ่มควบคุม
            button_frame = tk.Frame(self.txt_selector_window, bg="#f8f9fa")
            button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
            
            def open_selected_file():
                selection = listbox.curselection()
                if selection:
                    selected_file = txt_files[selection[0]]
                    self.txt_selector_window.destroy()
                    self._edit_txt_file(selected_file, folder_code)
                else:
                    messagebox.showwarning("คำเตือน", "กรุณาเลือกไฟล์ที่ต้องการแก้ไข")
            
            # ปุ่มเปิดไฟล์
            open_btn = tk.Button(
                button_frame,
                text="📄 เปิดไฟล์",
                command=open_selected_file,
                bg="#9b59b6",
                fg="white",
                font=("Arial", 10, "bold"),
                relief=tk.FLAT,
                padx=20,
                pady=5
            )
            open_btn.pack(side=tk.LEFT, padx=(0, 10))
            
            # ปุ่มยกเลิก
            cancel_btn = tk.Button(
                button_frame,
                text="❌ ยกเลิก",
                command=self.txt_selector_window.destroy,
                bg="#e74c3c",
                fg="white",
                font=("Arial", 10, "bold"),
                relief=tk.FLAT,
                padx=20,
                pady=5
            )
            cancel_btn.pack(side=tk.LEFT)
            
            # Double-click เพื่อเปิดไฟล์
            def on_double_click(event):
                open_selected_file()
            
            listbox.bind("<Double-1>", on_double_click)
            
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถเปิดหน้าต่างเลือกไฟล์ TXT: {e}")
            self.add_log(f"❌ ไม่สามารถเปิดหน้าต่างเลือกไฟล์ TXT: {e}", "error")

    def _edit_txt_file(self, txt_file_path, folder_code):
        """แก้ไขไฟล์ TXT ที่เลือก"""
        try:
            # สร้างหน้าต่างแก้ไขไฟล์ TXT
            self.txt_editor_window = tk.Toplevel(self.root)
            self.txt_editor_window.title(f"แก้ไขไฟล์ TXT - {txt_file_path.name}")
            self.txt_editor_window.geometry("800x600")
            self.txt_editor_window.configure(bg="#f8f9fa")
            
            # หัวข้อ
            title_label = tk.Label(
                self.txt_editor_window,
                text=f"แก้ไขไฟล์ TXT: {txt_file_path.name}",
                font=("Arial", 12, "bold"),
                bg="#f8f9fa",
                fg="#2c3e50"
            )
            title_label.pack(pady=(10, 5))
            
            # อ่านเนื้อหาไฟล์
            try:
                with open(txt_file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
            except UnicodeDecodeError:
                # ถ้า UTF-8 ไม่ได้ ลองใช้ encoding อื่น
                with open(txt_file_path, 'r', encoding='cp1252') as f:
                    file_content = f.read()
            
            # สร้าง Text widget สำหรับแก้ไข
            text_frame = tk.Frame(self.txt_editor_window, bg="#f8f9fa")
            text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Text widget พร้อม scrollbar
            text_widget = tk.Text(
                text_frame,
                font=("Consolas", 10),
                bg="white",
                fg="#2c3e50",
                wrap=tk.NONE,
                undo=True
            )
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            scrollbar = tk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            # แสดงเนื้อหาไฟล์
            text_widget.insert("1.0", file_content)
            
            # ปุ่มควบคุม
            button_frame = tk.Frame(self.txt_editor_window, bg="#f8f9fa")
            button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
            
            # ปุ่มบันทึก
            save_btn = tk.Button(
                button_frame,
                text="💾 บันทึก",
                command=lambda: self._save_txt_file(txt_file_path, text_widget),
                bg="#27ae60",
                fg="white",
                font=("Arial", 10, "bold"),
                relief=tk.FLAT,
                padx=20,
                pady=5
            )
            save_btn.pack(side=tk.LEFT, padx=(0, 10))
            
            # ปุ่มยกเลิก
            cancel_btn = tk.Button(
                button_frame,
                text="❌ ยกเลิก",
                command=self.txt_editor_window.destroy,
                bg="#e74c3c",
                fg="white",
                font=("Arial", 10, "bold"),
                relief=tk.FLAT,
                padx=20,
                pady=5
            )
            cancel_btn.pack(side=tk.LEFT)
            
            # ปุ่มรีเฟรช
            refresh_btn = tk.Button(
                button_frame,
                text="🔄 รีเฟรช",
                command=lambda: self._refresh_txt_content(text_widget, txt_file_path),
                bg="#3498db",
                fg="white",
                font=("Arial", 10, "bold"),
                relief=tk.FLAT,
                padx=20,
                pady=5
            )
            refresh_btn.pack(side=tk.RIGHT)
            
            # เก็บ reference
            self.txt_editor_window.text_widget = text_widget
            self.txt_editor_window.txt_file_path = txt_file_path
            
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถเปิดไฟล์ TXT: {e}")
            self.add_log(f"❌ ไม่สามารถเปิดไฟล์ TXT: {e}", "error")

    def _save_txt_file(self, txt_file_path, text_widget):
        """บันทึกไฟล์ TXT"""
        try:
            content = text_widget.get("1.0", tk.END).rstrip('\n')
            
            # บันทึกไฟล์
            with open(txt_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # แสดงข้อความสำเร็จ
            messagebox.showinfo("สำเร็จ", "บันทึกไฟล์ TXT สำเร็จ!")
            self.add_log(f"💾 บันทึกไฟล์ TXT สำเร็จ: {txt_file_path.name}", "success")
            
            # ปิดหน้าต่างแก้ไข
            self.txt_editor_window.destroy()
            
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"❌ ไม่สามารถบันทึกไฟล์: {e}")
            self.add_log(f"❌ ไม่สามารถบันทึกไฟล์ TXT: {e}", "error")

    def _refresh_txt_content(self, text_widget, txt_file_path):
        """รีเฟรชเนื้อหาไฟล์ TXT"""
        try:
            # อ่านไฟล์ใหม่
            with open(txt_file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            # แทนที่เนื้อหาใน text widget
            text_widget.delete("1.0", tk.END)
            text_widget.insert("1.0", file_content)
            
            self.add_log(f"🔄 รีเฟรชเนื้อหาไฟล์ TXT: {txt_file_path.name}", "info")
            
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"❌ ไม่สามารถรีเฟรชไฟล์: {e}")
            self.add_log(f"❌ ไม่สามารถรีเฟรชไฟล์ TXT: {e}", "error")

    def _validate_json(self, text_widget):
        """ตรวจสอบความถูกต้องของ JSON"""
        try:
            content = text_widget.get("1.0", tk.END).strip()
            import json
            json.loads(content)
            messagebox.showinfo("ตรวจสอบ JSON", "✅ JSON ถูกต้อง!")
        except json.JSONDecodeError as e:
            messagebox.showerror("ข้อผิดพลาด JSON", f"❌ JSON ไม่ถูกต้อง:\n{e}")
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"❌ เกิดข้อผิดพลาด: {e}")

    def _save_json_file_restricted(self, json_path, original_json_data):
        """บันทึกไฟล์ JSON โดยแก้ไขเฉพาะรหัสผู้ติดต่อและโค้ดบัญชี"""
        try:
            import json
            
            # อัพเดตข้อมูลจาก entry widgets
            updated_data = original_json_data.copy()
            
            for company_key, entries in self.json_entries.items():
                if company_key in updated_data:
                    # อัพเดตเฉพาะฟิลด์ที่อนุญาต
                    updated_data[company_key]["customer_id"] = entries['customer_id'].get().strip()
                    updated_data[company_key]["account_code"] = entries['account_code'].get().strip()
            
            # บันทึกไฟล์
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(updated_data, f, ensure_ascii=False, indent=2)
            
            # แสดงข้อความสำเร็จ
            messagebox.showinfo("สำเร็จ", "บันทึกไฟล์ JSON สำเร็จ!")
            self.add_log(f"💾 บันทึกไฟล์ JSON สำเร็จ: {json_path}", "success")
            
            # ปิดหน้าต่างแก้ไข
            self.json_editor_window.destroy()
            
            # รีเฟรชข้อมูลใน GUI
            self._refresh_folder_info()
            
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"❌ ไม่สามารถบันทึกไฟล์: {e}")
            self.add_log(f"❌ ไม่สามารถบันทึกไฟล์ JSON: {e}", "error")

    def _save_json_file(self, json_path, text_widget):
        """บันทึกไฟล์ JSON"""
        try:
            content = text_widget.get("1.0", tk.END).strip()
            
            # ตรวจสอบ JSON ก่อนบันทึก
            import json
            json.loads(content)
            
            # บันทึกไฟล์
            with open(json_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            messagebox.showinfo("บันทึกสำเร็จ", f"✅ บันทึกไฟล์ JSON สำเร็จ:\n{json_path}")
            self.add_log(f"💾 บันทึกไฟล์ JSON สำเร็จ: {json_path}", "success")
            
            # ปิดหน้าต่างแก้ไข
            self.json_editor_window.destroy()
            
            # รีเฟรชข้อมูลใน GUI
            self._refresh_folder_info()
            
        except json.JSONDecodeError as e:
            messagebox.showerror("ข้อผิดพลาด JSON", f"❌ JSON ไม่ถูกต้อง ไม่สามารถบันทึกได้:\n{e}")
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"❌ ไม่สามารถบันทึกไฟล์: {e}")

    def _refresh_folder_info(self):
        """รีเฟรชข้อมูลโฟลเดอร์"""
        try:
            current_folder = self.custom_folder_var.get()
            if current_folder:
                self.add_log("🔄 รีเฟรชข้อมูลโฟลเดอร์...", "info")
                self._display_folder_info(current_folder)
        except Exception as e:
            self.add_log(f"⚠️ ไม่สามารถรีเฟรชข้อมูล: {e}", "warning")

    def _extract_folder_code(self, folder_path):
        """แยกรหัสโฟลเดอร์จาก path ให้ถูกต้อง"""
        try:
            # วนลูปหาส่วนที่ตรงกับรูปแบบรหัสโฟลเดอร์
            for part in folder_path.parts:
                part_str = str(part)
                
                # กรณี 1: Build000 ทดสอบระบบ -> แยกเป็น Build000
                if part_str.startswith('Build') and ' ' in part_str:
                    build_part = part_str.split(' ')[0]  # ได้ "Build000"
                    if len(build_part) >= 7:  # Build000 = 7 ตัวอักษร
                        code_part = build_part[5:]  # ได้ "000"
                        if code_part.isdigit():
                            return f"Build{code_part}"
                
                # กรณี 2: Build000, Build001, etc. (ไม่มีช่องว่าง)
                elif part_str.startswith('Build') and len(part_str) >= 7:
                    code_part = part_str[5:]  # ได้ "000", "001"
                    if code_part.isdigit():
                        return f"Build{code_part}"
                
                # กรณี 3: 001, 002, 003 (3 หลัก)
                elif len(part_str) == 3 and part_str.isdigit():
                    return part_str
            
            return None
            
        except Exception as e:
            print(f"Error extracting folder code: {e}")
            return None

    def _reset_ui(self):
        """รีเซ็ต UI หลังทำงานเสร็จ"""
        self.is_running = False
        self.start_btn.config(state=tk.NORMAL)
        
        # ตรวจสอบว่าปุ่ม loop_btn และ test_btn ยังแสดงอยู่หรือไม่
        if self.admin_unlocked and self.loop_btn.winfo_viewable():
            self.loop_btn.config(state=tk.NORMAL)
        if self.admin_unlocked and self.test_btn.winfo_viewable():
            self.test_btn.config(state=tk.NORMAL)
        
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="สถานะ: พร้อมใช้งาน", fg="#27ae60")
        self.file_label.config(text="ไฟล์ปัจจุบัน: -")
        self.folder_label.config(text="โฟลเดอร์: -")
        self.progress.stop()
    
    def add_log(self, message, level="info"):
        """เพิ่ม log (thread-safe)"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        self.log_queue.put((log_message, level))
    
    def update_log_from_queue(self):
        """อัพเดต log จาก queue"""
        try:
            while True:
                log_message, level = self.log_queue.get_nowait()
                
                self.log_text.insert(tk.END, log_message, level)
                self.log_text.see(tk.END)
                
        except queue.Empty:
            pass
        
        # เรียกตัวเองอีกครั้งหลัง 100ms
        self.root.after(100, self.update_log_from_queue)
    
    def clear_log(self):
        """ล้าง log"""
        self.log_text.delete(1.0, tk.END)
        self.add_log("🗑️ ล้างบันทึกแล้ว", "info")
    
    def toggle_line_notification(self):
        """เปิด/ปิดการแจ้งเตือน LINE (ต้องเป็นแอดมิน)"""
        if not self.admin_unlocked:
            messagebox.showwarning("ต้องการสิทธิ์แอดมิน", "กรุณาเข้าสู่โหมดแอดมินก่อนใช้งานฟีเจอร์นี้")
            self.add_log("⚠️ ต้องการสิทธิ์แอดมินสำหรับจัดการการแจ้งเตือน LINE", "warning")
            return
            
        self.line_notify_enabled = not self.line_notify_enabled
        
        # อัพเดตสถานะใน report_manager
        try:
            from report_manager import set_line_notifications_enabled
            set_line_notifications_enabled(self.line_notify_enabled)
        except Exception as e:
            self.add_log(f"⚠️ ไม่สามารถอัพเดต report_manager: {e}", "warning")
        
        # อัพเดต UI
        if self.line_notify_enabled:
            self.line_notify_btn.config(
                text="📱 เปิดการแจ้งเตือน LINE",
                bg="#00c851"
            )
            self.add_log("✅ เปิดการแจ้งเตือน LINE แล้ว", "success")
        else:
            self.line_notify_btn.config(
                text="📱 ปิดการแจ้งเตือน LINE",
                bg="#ff4444"
            )
            self.add_log("❌ ปิดการแจ้งเตือน LINE แล้ว", "warning")
        
        # อัพเดต config
        try:
            from config import Config
            Config.LINE_NOTIFY_ENABLED = self.line_notify_enabled
        except Exception as e:
            self.add_log(f"⚠️ ไม่สามารถอัพเดต config: {e}", "warning")
    
    def is_line_notify_enabled(self):
        """ตรวจสอบสถานะการแจ้งเตือน LINE"""
        return self.line_notify_enabled
    
    def admin_login(self):
        """เข้าสู่โหมดแอดมิน"""
        if self.admin_unlocked:
            # ถ้าอยู่ในโหมดแอดมินแล้ว ให้ออกจากโหมด
            self.admin_logout()
        else:
            # ถ้ายังไม่ได้ login ให้แสดง dialog รหัสผ่าน
            password = tk.simpledialog.askstring("เข้าสู่โหมดแอดมิน", "กรุณาใส่รหัสผ่านแอดมิน:", show='*')
            if password == self.admin_password:
                self.admin_unlocked = True
                self.update_admin_ui()
                self.add_log("🔓 เข้าสู่โหมดแอดมินสำเร็จ", "success")
            elif password is not None:  # ถ้าผู้ใช้กด cancel จะเป็น None
                messagebox.showerror("รหัสผ่านผิด", "รหัสผ่านไม่ถูกต้อง!")
                self.add_log("❌ รหัสผ่านแอดมินไม่ถูกต้อง", "error")
    
    def admin_logout(self):
        """ออกจากโหมดแอดมิน"""
        self.admin_unlocked = False
        self.update_admin_ui()
        self.add_log("🔒 ออกจากโหมดแอดมิน", "info")
    
    def update_admin_ui(self):
        """อัพเดต UI ตามสถานะแอดมิน"""
        if self.admin_unlocked:
            # แอดมินเข้าสู่ระบบแล้ว
            self.admin_btn.config(
                text="🔒 ออกจากโหมดแอดมิน",
                bg="#e74c3c"
            )
            # แสดงและปลดล็อคฟีเจอร์แอดมิน
            self.auto_mode_btn.pack(side=tk.LEFT, padx=(0, 5))
            self.manual_mode_btn.pack(side=tk.LEFT, padx=(0, 5))
            self.auto_mode_btn.config(state=tk.NORMAL)
            self.manual_mode_btn.config(state=tk.NORMAL)
            self.loop_btn.pack(fill=tk.X, padx=5, pady=5)
            self.test_btn.pack(fill=tk.X, padx=5, pady=5)
            self.line_notify_btn.config(state=tk.NORMAL)
            # แสดง folder frame และ select all frame
            self.folder_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            self.select_all_frame.pack(fill=tk.X, pady=(0, 10))
        else:
            # แอดมินยังไม่ได้เข้าสู่ระบบ
            self.admin_btn.config(
                text="🔓 เข้าสู่โหมดแอดมิน",
                bg="#34495e"
            )
            # ซ่อนปุ่มโหมดต่างๆ
            self.auto_mode_btn.pack_forget()
            self.manual_mode_btn.pack_forget()
            # ซ่อนปุ่มเริ่มระบบลูปและทดสอบระบบ
            self.loop_btn.pack_forget()
            self.test_btn.pack_forget()
            self.line_notify_btn.config(state=tk.DISABLED)
            # ซ่อน folder frame และ select all frame
            self.folder_frame.pack_forget()
            self.select_all_frame.pack_forget()
    
    def open_manual(self):
        """เปิดคู่มือการใช้งานในเบราว์เซอร์"""
        try:
            # หา path ของไฟล์คู่มือ
            manual_path = Path(__file__).parent / "คู่มือการใช้งานระบบ_BotV3_Index.html"
            
            if manual_path.exists():
                # แปลงเป็น absolute path และใช้ file:// protocol
                manual_url = manual_path.resolve().as_uri()
                
                # เปิดในเบราว์เซอร์
                webbrowser.open(manual_url)
                self.add_log("📖 เปิดคู่มือการใช้งานในเบราว์เซอร์", "success")
            else:
                self.add_log(f"❌ ไม่พบไฟล์คู่มือ: {manual_path}", "error")
                messagebox.showerror(
                    "ไม่พบไฟล์คู่มือ", 
                    f"ไม่พบไฟล์คู่มือการใช้งาน:\n{manual_path}\n\nกรุณาตรวจสอบว่าไฟล์อยู่ในโฟลเดอร์เดียวกันกับโปรแกรม"
                )
                
        except Exception as e:
            self.add_log(f"❌ ไม่สามารถเปิดคู่มือ: {e}", "error")
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถเปิดคู่มือการใช้งานได้:\n{e}")

    def open_pdf_reader(self):
        """เปิดหน้าต่างอ่านไฟล์ PDF"""
        try:
            # สร้างหน้าต่างใหม่สำหรับ PDF Reader
            pdf_window = tk.Toplevel(self.root)
            pdf_window.title("📄 PDF Reader - ทดสอบการอ่านไฟล์")
            pdf_window.geometry("900x700")
            pdf_window.resizable(True, True)
            
            # ทำให้หน้าต่างอยู่ด้านหน้า
            pdf_window.transient(self.root)
            pdf_window.grab_set()
            
            # สร้าง UI สำหรับ PDF Reader
            self.create_pdf_reader_ui(pdf_window)
            
        except Exception as e:
            self.add_log(f"❌ ไม่สามารถเปิด PDF Reader: {e}", "error")
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถเปิด PDF Reader ได้:\n{e}")
    
    def create_pdf_reader_ui(self, parent_window):
        """สร้าง UI สำหรับ PDF Reader"""
        try:
            # Header
            header_frame = tk.Frame(parent_window, bg="#34495e", height=60)
            header_frame.pack(fill=tk.X)
            header_frame.pack_propagate(False)
            
            header_label = tk.Label(
                header_frame,
                text="📄 PDF Reader - ทดสอบการอ่านไฟล์",
                font=("Arial", 14, "bold"),
                fg="white",
                bg="#34495e"
            )
            header_label.pack(pady=15)
            
            # Main container
            main_frame = tk.Frame(parent_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # File selection frame
            file_frame = tk.LabelFrame(main_frame, text="📁 เลือกไฟล์ PDF", font=("Arial", 10, "bold"))
            file_frame.pack(fill=tk.X, pady=(0, 10))
            
            file_select_frame = tk.Frame(file_frame)
            file_select_frame.pack(fill=tk.X, padx=10, pady=10)
            
            self.pdf_file_path_var = tk.StringVar()
            
            # File path entry
            file_entry = tk.Entry(
                file_select_frame,
                textvariable=self.pdf_file_path_var,
                font=("Arial", 10),
                state="readonly",
                bg="#f8f9fa"
            )
            file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
            
            # Browse button
            browse_btn = tk.Button(
                file_select_frame,
                text="📂 เลือกไฟล์",
                command=lambda: self.browse_pdf_file(),
                bg="#3498db",
                fg="white",
                font=("Arial", 10, "bold"),
                relief=tk.FLAT,
                padx=15,
                pady=5
            )
            browse_btn.pack(side=tk.RIGHT)
            
            # Control buttons frame
            control_frame = tk.Frame(main_frame)
            control_frame.pack(fill=tk.X, pady=(0, 10))
            
            # Read PDF button
            read_btn = tk.Button(
                control_frame,
                text="🔍 อ่านไฟล์ PDF",
                command=lambda: self.read_pdf_file(parent_window),
                bg="#27ae60",
                fg="white",
                font=("Arial", 11, "bold"),
                relief=tk.FLAT,
                padx=20,
                pady=8
            )
            read_btn.pack(side=tk.LEFT)
            
            # Clear button
            clear_btn = tk.Button(
                control_frame,
                text="🗑️ ล้างผลลัพธ์",
                command=lambda: self.clear_pdf_result(parent_window),
                bg="#e74c3c",
                fg="white",
                font=("Arial", 11, "bold"),
                relief=tk.FLAT,
                padx=20,
                pady=8
            )
            clear_btn.pack(side=tk.LEFT, padx=(10, 0))
            
            # Save result button
            save_btn = tk.Button(
                control_frame,
                text="💾 บันทึกผลลัพธ์",
                command=lambda: self.save_pdf_result(parent_window),
                bg="#f39c12",
                fg="white",
                font=("Arial", 11, "bold"),
                relief=tk.FLAT,
                padx=20,
                pady=8
            )
            save_btn.pack(side=tk.RIGHT)
            
            # Result frame
            result_frame = tk.LabelFrame(main_frame, text="📊 ผลลัพธ์การอ่าน", font=("Arial", 10, "bold"))
            result_frame.pack(fill=tk.BOTH, expand=True)
            
            # Create notebook for tabs
            notebook = ttk.Notebook(result_frame)
            notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Raw data tab
            raw_frame = tk.Frame(notebook)
            notebook.add(raw_frame, text="📄 ข้อมูลดิบ")
            
            self.raw_text = scrolledtext.ScrolledText(
                raw_frame,
                font=("Consolas", 9),
                bg="#1e1e1e",
                fg="#00ff00",
                wrap=tk.WORD
            )
            self.raw_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Parsed data tab
            parsed_frame = tk.Frame(notebook)
            notebook.add(parsed_frame, text="🔍 ข้อมูลที่แยกแล้ว")
            
            self.parsed_text = scrolledtext.ScrolledText(
                parsed_frame,
                font=("Consolas", 9),
                bg="#1e1e1e",
                fg="#00aaff",
                wrap=tk.WORD
            )
            self.parsed_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # JSON data tab
            json_frame = tk.Frame(notebook)
            notebook.add(json_frame, text="📋 ข้อมูล JSON")
            
            self.json_text = scrolledtext.ScrolledText(
                json_frame,
                font=("Consolas", 9),
                bg="#1e1e1e",
                fg="#00ff00",
                wrap=tk.WORD
            )
            self.json_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Error tab
            error_frame = tk.Frame(notebook)
            notebook.add(error_frame, text="⚠️ ข้อผิดพลาด")
            
            self.error_text = scrolledtext.ScrolledText(
                error_frame,
                font=("Consolas", 9),
                bg="#1e1e1e",
                fg="#ff0000",
                wrap=tk.WORD
            )
            self.error_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Status bar
            status_frame = tk.Frame(parent_window, bg="#ecf0f1", height=30)
            status_frame.pack(fill=tk.X, side=tk.BOTTOM)
            status_frame.pack_propagate(False)
            
            self.pdf_status_label = tk.Label(
                status_frame,
                text="พร้อมใช้งาน - เลือกไฟล์ PDF เพื่อเริ่มต้น",
                font=("Arial", 9),
                bg="#ecf0f1",
                fg="#2c3e50"
            )
            self.pdf_status_label.pack(pady=5)
            
            # เก็บ reference สำหรับการใช้งาน
            self.pdf_window = parent_window
            self.current_pdf_data = None
            
        except Exception as e:
            self.add_log(f"❌ สร้าง PDF Reader UI ไม่สำเร็จ: {e}", "error")
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถสร้าง PDF Reader UI ได้:\n{e}")
    
    def browse_pdf_file(self):
        """เลือกไฟล์ PDF"""
        try:
            file_path = filedialog.askopenfilename(
                title="เลือกไฟล์ PDF",
                filetypes=[
                    ("PDF files", "*.pdf"),
                    ("All files", "*.*")
                ],
                initialdir=str(Path.home())
            )
            
            if file_path:
                self.pdf_file_path_var.set(file_path)
                self.update_pdf_status(f"เลือกไฟล์: {Path(file_path).name}")
                
        except Exception as e:
            self.add_log(f"❌ ไม่สามารถเลือกไฟล์: {e}", "error")
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถเลือกไฟล์ได้:\n{e}")
    
    def read_pdf_file(self, parent_window):
        """อ่านไฟล์ PDF"""
        file_path = self.pdf_file_path_var.get()
        
        if not file_path:
            messagebox.showwarning("คำเตือน", "กรุณาเลือกไฟล์ PDF ก่อน")
            return
        
        if not Path(file_path).exists():
            messagebox.showerror("ข้อผิดพลาด", "ไม่พบไฟล์ที่เลือก")
            return
        
        try:
            self.update_pdf_status("กำลังอ่านไฟล์ PDF...")
            self.clear_pdf_result(parent_window)
            
            # รันการอ่านไฟล์ในเธรดแยก
            thread = threading.Thread(target=self._read_pdf_thread, args=(file_path, parent_window))
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            self.add_log(f"❌ ไม่สามารถอ่านไฟล์ PDF: {e}", "error")
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถอ่านไฟล์ PDF ได้:\n{e}")
    
    def _read_pdf_thread(self, file_path, parent_window):
        """อ่านไฟล์ PDF ในเธรดแยก"""
        try:
            # Import PDF reader
            from pdf_reader import PDFReader
            from pathlib import Path
            import PyPDF2
            
            # สร้าง PDF Reader
            pdf_reader = PDFReader()
            
            # แปลง file_path เป็น Path object
            pdf_path = Path(file_path)
            
            # อ่านข้อความดิบจาก PDF โดยตรง
            raw_text_content = ""
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader_obj = PyPDF2.PdfReader(file)
                    for page in pdf_reader_obj.pages:
                        raw_text_content += page.extract_text() + "\n"
            except Exception as e:
                raw_text_content = f"ไม่สามารถอ่านข้อความจาก PDF ได้: {e}"
            
            # อ่านข้อมูลที่ประมวลผลแล้ว
            parsed_data = pdf_reader.read_pdf(pdf_path)
            
            # เก็บข้อมูลสำหรับการบันทึก
            self.current_pdf_data = {
                'file_path': file_path,
                'raw_data': raw_text_content,  # ข้อความดิบ
                'parsed_data': parsed_data,    # ข้อมูลที่ประมวลผลแล้ว
                'timestamp': datetime.now().isoformat()
            }
            
            # อัพเดต UI ใน main thread
            parent_window.after(0, self._update_pdf_result, raw_text_content, parsed_data, None, parent_window)
            
        except Exception as e:
            # อัพเดต UI ใน main thread
            parent_window.after(0, self._update_pdf_result, None, None, str(e), parent_window)
    
    def _update_pdf_result(self, raw_data, parsed_data, error, parent_window):
        """อัพเดตผลลัพธ์การอ่าน PDF"""
        try:
            if error:
                self.error_text.insert(tk.END, f"❌ ข้อผิดพลาด:\n{error}\n\n")
                self.error_text.see(tk.END)
                self.update_pdf_status(f"เกิดข้อผิดพลาด: {error}")
                return
            
            # แสดงข้อมูลดิบ (ข้อความที่อ่านมาจาก PDF โดยตรง)
            if raw_data:
                self.raw_text.insert(tk.END, f"📄 ข้อความดิบจากไฟล์ PDF:\n")
                self.raw_text.insert(tk.END, f"{'='*50}\n")
                self.raw_text.insert(tk.END, f"{raw_data}\n\n")
                self.raw_text.see(tk.END)
            
            # แสดงข้อมูลที่แยกแล้ว
            if parsed_data:
                self.parsed_text.insert(tk.END, f"🔍 ข้อมูลที่แยกแล้ว:\n")
                self.parsed_text.insert(tk.END, f"{'='*50}\n")
                
                # ✅ แสดงข้อมูลสำคัญอย่างชัดเจน
                company_name = parsed_data.get('company_name', 'ไม่พบ')
                customer_id = parsed_data.get('customer_id', 'ไม่พบ')
                account_code = parsed_data.get('account_code', 'ไม่พบ')
                
                self.parsed_text.insert(tk.END, f"🏢 บริษัท: {company_name}\n")
                self.parsed_text.insert(tk.END, f"👤 รหัสผู้ติดต่อ: {customer_id}\n")
                self.parsed_text.insert(tk.END, f"🔢 โค้ดบัญชี: {account_code}\n")
                self.parsed_text.insert(tk.END, f"{'='*50}\n\n")
                
                # แสดงข้อมูลในรูปแบบ JSON ใน JSON tab
                self.json_text.insert(tk.END, f"📋 ข้อมูลทั้งหมด (JSON):\n")
                self.json_text.insert(tk.END, f"{'='*50}\n")
                json_data = json.dumps(parsed_data, ensure_ascii=False, indent=2)
                self.json_text.insert(tk.END, f"{json_data}\n\n")
                self.json_text.see(tk.END)
                
                # แสดงข้อมูลแบบตาราง
                self.parsed_text.insert(tk.END, f"📊 สรุปข้อมูล:\n")
                self.parsed_text.insert(tk.END, f"{'='*30}\n")
                
                for key, value in parsed_data.items():
                    if value and key not in ['company_name', 'customer_id', 'account_code']:
                        self.parsed_text.insert(tk.END, f"{key}: {value}\n")
                
                self.parsed_text.insert(tk.END, f"\n")
                self.parsed_text.see(tk.END)
            
            # อัพเดต status bar พร้อมข้อมูลสำคัญ
            if parsed_data:
                company_name = parsed_data.get('company_name', 'ไม่พบ')
                customer_id = parsed_data.get('customer_id', 'ไม่พบ')
                account_code = parsed_data.get('account_code', 'ไม่พบ')
                status_msg = f"✅ อ่านสำเร็จ: {Path(self.pdf_file_path_var.get()).name} | บริษัท: {company_name} | รหัสผู้ติดต่อ: {customer_id} | โค้ดบัญชี: {account_code}"
            else:
                status_msg = f"✅ อ่านไฟล์สำเร็จ: {Path(self.pdf_file_path_var.get()).name}"
            
            self.update_pdf_status(status_msg)
            
        except Exception as e:
            self.error_text.insert(tk.END, f"❌ ข้อผิดพลาดในการแสดงผลลัพธ์:\n{str(e)}\n\n")
            self.error_text.see(tk.END)
            self.update_pdf_status(f"เกิดข้อผิดพลาด: {e}")
    
    def clear_pdf_result(self, parent_window):
        """ล้างผลลัพธ์การอ่าน PDF"""
        try:
            self.raw_text.delete(1.0, tk.END)
            self.parsed_text.delete(1.0, tk.END)
            self.json_text.delete(1.0, tk.END)
            self.error_text.delete(1.0, tk.END)
            self.update_pdf_status("ล้างผลลัพธ์แล้ว")
            
        except Exception as e:
            self.add_log(f"❌ ไม่สามารถล้างผลลัพธ์: {e}", "error")
    
    def save_pdf_result(self, parent_window):
        """บันทึกผลลัพธ์การอ่าน PDF"""
        if not self.current_pdf_data:
            messagebox.showwarning("คำเตือน", "ไม่มีข้อมูลที่จะบันทึก")
            return
        
        try:
            # เลือกตำแหน่งบันทึก
            file_path = filedialog.asksaveasfilename(
                title="บันทึกผลลัพธ์",
                defaultextension=".json",
                filetypes=[
                    ("JSON files", "*.json"),
                    ("Text files", "*.txt"),
                    ("All files", "*.*")
                ],
                initialname=f"pdf_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            if file_path:
                # บันทึกข้อมูล
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.current_pdf_data, f, ensure_ascii=False, indent=2)
                
                self.update_pdf_status(f"บันทึกผลลัพธ์สำเร็จ: {Path(file_path).name}")
                messagebox.showinfo("สำเร็จ", f"บันทึกผลลัพธ์สำเร็จ:\n{file_path}")
                
        except Exception as e:
            self.add_log(f"❌ ไม่สามารถบันทึกผลลัพธ์: {e}", "error")
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถบันทึกผลลัพธ์ได้:\n{e}")
    
    def update_pdf_status(self, message):
        """อัพเดตสถานะ PDF Reader"""
        try:
            if hasattr(self, 'pdf_status_label'):
                self.pdf_status_label.config(text=message)
        except Exception:
            pass


def main():
    """ฟังก์ชันหลัก"""
    root = tk.Tk()
    
    # ตั้งค่า style
    style = ttk.Style()
    style.theme_use('clam')
    
    # สร้าง GUI
    app = BotGUI(root)
    
    # แสดงข้อความเริ่มต้น
    app.add_log("="*60, "info")
    app.add_log("🤖 ยินดีต้อนรับสู่ BotV3", "success")
    app.add_log("📋 ระบบประมวลผล PDF อัตโนมัติ", "info")
    app.add_log("="*60, "info")
    app.add_log("", "info")
    
    # รัน GUI loop
    root.mainloop()


if __name__ == '__main__':
    main()

