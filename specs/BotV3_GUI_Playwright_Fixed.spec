# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

block_cipher = None

datas = []
binaries = []
hiddenimports = []

# ---- เก็บไฟล์/โมดูลของ Playwright อัตโนมัติ ----
try:
    playwright_datas = collect_data_files('playwright', include_py_files=True)
    datas += playwright_datas
except:
    pass  # ถ้าไม่สามารถเก็บไฟล์ playwright ได้
hiddenimports += collect_submodules('playwright')

# ---- แนบไฟล์/โฟลเดอร์ของโปรเจกต์ ----
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\bot_gui_tkinter.py', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\config.py', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\data_processor.py', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\file_manager.py', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\report_manager.py', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\logger.py', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\pdf_reader.py', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\main_system.py', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\web_automation_playwright.py', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\web_automation_wrapper.py', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\control_api_wrapper.py', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\playwright_setup.py', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\bot_gui_wrapper.py', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\bot_gui_complete.py', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\bot_gui_playwright_fixed.py', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\main_control.html', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\flow_bot.html', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\flowchart.html', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\คู่มือการใช้งานระบบ_BotV3_Index.html', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\คู่มือการใช้งานระบบ_BotV3_แนะนำระบบ.html', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\คู่มือการใช้งานระบบ_BotV3_การใช้งาน.html', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\คู่มือการใช้งานระบบ_BotV3_สร้างฐานข้อมูล.html', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\คู่มือการใช้งานระบบ_BotV3_แก้ไขไฟล์.html', r'.'))
datas.append((r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\คู่มือการติดตั้ง_BotV3.html', r'.'))

# ---- แนบโฟลเดอร์ ms-playwright (Chromium) ----
import os
from pathlib import Path

# หาโฟลเดอร์ ms-playwright
home = Path.home()
candidates = []
env_path = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
if env_path:
    candidates.append(Path(env_path))
candidates += [
    home / "AppData" / "Local" / "ms-playwright",  # Windows
    home / ".cache" / "ms-playwright",             # Linux/macOS
]

for p in candidates:
    if p and p.exists():
        print(f"Found Playwright browsers at: {p}")
        # แนบโฟลเดอร์ ms-playwright ทั้งหมด
        datas += collect_data_files(str(p), include_py_files=True)
        break

# แนบ Playwright binaries และ DLLs
try:
    from playwright._impl._driver import compute_driver_executable
    driver_path = compute_driver_executable()
    if driver_path and Path(driver_path).exists():
        datas.append((str(driver_path), '.'))
        print(f"Added Playwright driver: {driver_path}")
except Exception as e:
    print(f"Could not add Playwright driver: {e}")

# แนบ Playwright dependencies
try:
    import playwright
    playwright_path = Path(playwright.__file__).parent
    datas += collect_data_files('playwright', include_py_files=True)
    print(f"Added Playwright package data")
except Exception as e:
    print(f"Could not add Playwright package: {e}")

a = Analysis(
    [r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\bot_gui_playwright_fixed.py'],
    pathex=[r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3'],
    binaries=binaries,
    datas=datas,
        hiddenimports=hiddenimports + [
            # ไลบรารีอื่นที่โปรเจ็กต์ใช้
            'tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox',
            'PIL', 'PIL.Image', 'PIL.ImageTk',
            'pdfplumber', 'pymupdf', 'PyPDF2',
            'pandas', 'numpy', 'requests',
            'flask', 'flask_cors',
            'colorlog',
            # Playwright dependencies
            'playwright',
            'playwright._impl',
            'playwright._impl._browser_type',
            'playwright._impl._browser',
            'playwright._impl._page',
            'playwright._impl._context',
            'playwright._impl._element_handle',
            'playwright._impl._locator',
            'playwright._impl._frame',
            'playwright._impl._driver',
            'playwright._impl._helper',
            'playwright._impl._network',
            'playwright._impl._cdp_session',
            'playwright._impl._async_base',
            'playwright._impl._sync_base',
            'playwright.sync_api',
            'playwright.async_api',
            'playwright.sync_api._generated',
            'playwright.async_api._generated',
            'greenlet',
            'pyee',
            'websockets',
            'certifi',
            'urllib3',
            'charset_normalizer',
            'idna',
            'requests.adapters',
            'requests.auth',
            'requests.cookies',
            'requests.exceptions',
            'requests.models',
            'requests.sessions',
            'requests.structures',
            'requests.utils',
            'requests.packages',
            'requests.packages.urllib3',
            'requests.packages.urllib3.util',
            'requests.packages.urllib3.util.retry',
            'requests.packages.urllib3.util.connection',
            'requests.packages.urllib3.poolmanager',
            'requests.packages.urllib3.response',
            'requests.packages.urllib3.exceptions'
        ],
    hooksconfig={},
    runtime_hooks=[r'C:\Users\USER\OneDrive\Desktop\งานโปรเเกรม\bot\BotV3\specs\playwright_browsers_path.py'],
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
    name='BotV3_GUI_Playwright_Fixed',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,   # ปิด UPX ลดปัญหา DLL/เบราว์เซอร์
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)

# 👇 ให้ output แบบ onedir ที่ dist/BotV3_GUI_Playwright_Fixed/
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='BotV3_GUI_Playwright_Fixed'
)
