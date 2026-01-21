# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# ข้อมูลไฟล์ที่ต้องรวม
datas = []
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\config.py', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\data_processor.py', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\file_manager.py', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\report_manager.py', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\logger.py', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\pdf_reader.py', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\web_automation_playwright.py', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\web_automation_wrapper.py', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\control_api_wrapper.py', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\main_system.py', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\main_control.html', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\flow_bot.html', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\flowchart.html', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\pdf_parsers', r'pdf_parsers'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\temp_uploads', r'temp_uploads'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\คู่มือการใช้งานระบบ_BotV3_Index.html', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\คู่มือการใช้งานระบบ_BotV3_แนะนำระบบ.html', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\คู่มือการใช้งานระบบ_BotV3_การใช้งาน.html', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\คู่มือการใช้งานระบบ_BotV3_สร้างฐานข้อมูล.html', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\คู่มือการใช้งานระบบ_BotV3_แก้ไขไฟล์.html', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\คู่มือการติดตั้ง_BotV3.html', r'.'))
datas.append((r'C:\Users\USER\AppData\Local\Programs\Python\Python312\Lib\site-packages\playwright', r'playwright'))


a = Analysis(
    [r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\bot_gui_tkinter.py'],
    pathex=[r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3'],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'playwright',
        'playwright.sync_api',
        'playwright._impl',
        'selenium',
        'PyPDF2',
        'pdfplumber',
        'pymupdf',
        'pandas',
        'numpy',
        'requests',
        'flask',
        'flask_cors',
        'json',
        'datetime',
        'threading',
        'subprocess',
        'shutil',
        'pathlib',
        'os',
        'sys',
        'logging',
        'colorlog'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='BotV3_GUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # แสดง console window สำหรับ debug
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)
