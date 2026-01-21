# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['bot_gui_playwright_working.py'],
    pathex=[],
    binaries=[],
    datas=[('bot_gui_tkinter.py', '.'), ('config.py', '.'), ('data_processor.py', '.'), ('file_manager.py', '.'), ('report_manager.py', '.'), ('logger.py', '.'), ('pdf_reader.py', '.'), ('main_system.py', '.'), ('web_automation_playwright.py', '.'), ('web_automation_wrapper.py', '.'), ('control_api_wrapper.py', '.'), ('playwright_setup.py', '.'), ('bot_gui_wrapper.py', '.'), ('bot_gui_chromium_fixed.py', '.'), ('bot_gui_fixed.py', '.'), ('bot_gui_playwright_final.py', '.'), ('bot_gui_playwright_working.py', '.'), ('main_control.html', '.'), ('flow_bot.html', '.'), ('flowchart.html', '.'), ('pdf_parsers', 'pdf_parsers'), ('temp_uploads', 'temp_uploads')],
    hiddenimports=['playwright.sync_api', 'playwright._impl', 'playwright._impl._api_structures', 'playwright._impl._browser_type', 'playwright._impl._browser', 'playwright._impl._page', 'playwright._impl._context', 'playwright._impl._element_handle', 'playwright._impl._locator', 'playwright._impl._frame', 'playwright._impl._js_handle', 'playwright._impl._network', 'playwright._impl._cdp_session', 'playwright._impl._accessibility', 'playwright._impl._console_message', 'playwright._impl._dialog', 'playwright._impl._download', 'playwright._impl._file_chooser', 'playwright._impl._worker', 'playwright._impl._video', 'playwright._impl._tracing', 'playwright._impl._coverage', 'playwright._impl._har', 'playwright._impl._request', 'playwright._impl._response', 'playwright._impl._route', 'playwright._impl._web_socket', 'playwright._impl._browser_context'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='BotV3_GUI_Playwright_Fixed',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
