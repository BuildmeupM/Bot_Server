# Bot_Server Project Restructure Script
# จัดเรียงไฟล์โปรเจกต์ให้เป็นระเบียบ
# ย้ายไฟล์ที่ไม่ใช้งานไป _archive/ และเอกสารไป docs/

$ErrorActionPreference = "SilentlyContinue"

Write-Host "=== Bot_Server Project Restructure ===" -ForegroundColor Cyan
Write-Host ""

# --- 1. Create directories ---
Write-Host "[1/5] Creating directories..." -ForegroundColor Yellow
$dirs = @(
    "_archive\old_versions",
    "_archive\old_gui",
    "_archive\scripts",
    "_archive\debug",
    "_archive\specs",
    "_archive\logs",
    "docs\images"
)
foreach ($d in $dirs) {
    New-Item -ItemType Directory -Force -Path $d | Out-Null
}
Write-Host "  Done" -ForegroundColor Green

# --- 2. Move old versions & unused Python files ---
Write-Host "[2/5] Moving unused Python files to _archive/..." -ForegroundColor Yellow

$old_versions = @(
    "BotV2.py",
    "main_bot.py",
    "app.py",
    "control_api.py",
    "control_api_wrapper.py",
    "data_processor.py",
    "web_automation_wrapper.py",
    "web_automation_playwright_backup.py",
    "msc_data_extractor.py",
    "excel_writer_service.py",
    "example_usage.py",
    "tax_ocr_processor.py"
)
foreach ($f in $old_versions) {
    if (Test-Path $f) {
        Move-Item $f "_archive\old_versions\$f" -Force
        Write-Host "  Moved $f" -ForegroundColor DarkGray
    }
}

$old_gui = @("bot_gui_tkinter.py", "bot_gui_streamlit.py", "bot_gui_wrapper.py")
foreach ($f in $old_gui) {
    if (Test-Path $f) {
        Move-Item $f "_archive\old_gui\$f" -Force
        Write-Host "  Moved $f" -ForegroundColor DarkGray
    }
}

$scripts = @(
    "check_routes.py",
    "cleanup_temp_uploads.py",
    "move_email_files.py",
    "debug_environment.py",
    "split_extractors.py",
    "split_extractors_v2.py",
    "playwright_setup.py"
)
foreach ($f in $scripts) {
    if (Test-Path $f) {
        Move-Item $f "_archive\scripts\$f" -Force
        Write-Host "  Moved $f" -ForegroundColor DarkGray
    }
}

# Move unused requirements
$reqs = @("requirements_desktop.txt", "requirements_exe.txt", "requirements_setup.txt", "requirements_test.txt")
foreach ($f in $reqs) {
    if (Test-Path $f) {
        Move-Item $f "_archive\old_versions\$f" -Force
        Write-Host "  Moved $f" -ForegroundColor DarkGray
    }
}

Write-Host "  Done" -ForegroundColor Green

# --- 3. Move directories ---
Write-Host "[3/5] Moving unused directories to _archive/..." -ForegroundColor Yellow

$moveDirs = @(
    @{From="backup"; To="_archive\backup"},
    @{From="BotV3"; To="_archive\BotV3"},
    @{From="BotV3_final"; To="_archive\BotV3_final"},
    @{From="dist"; To="_archive\dist"},
    @{From="specs"; To="_archive\specs_old"},
    @{From="ocr_bot"; To="_archive\ocr_bot"},
    @{From="pages"; To="_archive\pages"},
    @{From="testocr"; To="_archive\testocr"}
)
foreach ($item in $moveDirs) {
    $src = $item.From
    $dst = $item.To
    if (Test-Path $src) {
        Move-Item $src $dst -Force
        Write-Host "  Moved $src/" -ForegroundColor DarkGray
    }
}

# Thai backup folder
if (Test-Path "สำรอง") {
    Move-Item "สำรอง" "_archive\สำรอง" -Force
    Write-Host "  Moved สำรอง/" -ForegroundColor DarkGray
}

Write-Host "  Done" -ForegroundColor Green

# --- 4. Move debug artifacts ---
Write-Host "[4/5] Moving debug artifacts and docs..." -ForegroundColor Yellow

$debug_files = @(
    "debug_env_20250820_094053.json",
    "debug_login_username_not_found.png",
    "peakengine_login.png",
    "api_test_result.json",
    "api_test_result_fixed.json",
    "5.13.0"
)
foreach ($f in $debug_files) {
    if (Test-Path $f) {
        Move-Item $f "_archive\debug\$f" -Force
        Write-Host "  Moved $f" -ForegroundColor DarkGray
    }
}

# Move spec files
$spec_files = @("BotV3_GUI_Playwright_Fixed.spec", "BotV3_GUI_Playwright_Working.spec")
foreach ($f in $spec_files) {
    if (Test-Path $f) {
        Move-Item $f "_archive\specs\$f" -Force
        Write-Host "  Moved $f" -ForegroundColor DarkGray
    }
}

# Move bot_log.txt
if (Test-Path "bot_log.txt") {
    Move-Item "bot_log.txt" "_archive\logs\bot_log.txt" -Force
    Write-Host "  Moved bot_log.txt" -ForegroundColor DarkGray
}

# Move documentation .md files to docs/
$md_docs = @(
    "COMPANY_EXTRACTION_INFO.md",
    "EMAIL_HISTORY_DESIGN.md",
    "EXCLUSIVE_GLOBAL_LOGISTICS_EXTRACTION_RULES.md",
    "FILE_RENAMING_SUMMARY.md",
    "IMPROVEMENTS_EMAIL_SENDING.md",
    "INVOICE_EXTRACTION_CONDITIONS.md",
    "NGROK_SETUP.md",
    "README_CONTROL_SYSTEM.md",
    "README_DESKTOP_UI.md",
    "README_GUI_APP.md",
    "README_WEB_APP.md",
    "UI_IMPROVEMENTS_EMAIL_SENDING.md"
)
foreach ($f in $md_docs) {
    if (Test-Path $f) {
        Move-Item $f "docs\$f" -Force
        Write-Host "  Moved $f -> docs/" -ForegroundColor DarkGray
    }
}

# Move HTML docs
$html_docs = @("flow_bot.html", "flowchart.html", "main_control.html")
foreach ($f in $html_docs) {
    if (Test-Path $f) {
        Move-Item $f "docs\$f" -Force
        Write-Host "  Moved $f -> docs/" -ForegroundColor DarkGray
    }
}

# Move Thai manual HTML files
Get-ChildItem -Filter "คู่มือ*.html" | ForEach-Object {
    Move-Item $_.FullName "docs\$($_.Name)" -Force
    Write-Host "  Moved $($_.Name) -> docs/" -ForegroundColor DarkGray
}

# Move Thai manual PNG images
Get-ChildItem -Filter "คู่มือ*.png" | ForEach-Object {
    Move-Item $_.FullName "docs\images\$($_.Name)" -Force
    Write-Host "  Moved $($_.Name) -> docs/images/" -ForegroundColor DarkGray
}

Write-Host "  Done" -ForegroundColor Green

# --- 5. Summary ---
Write-Host ""
Write-Host "[5/5] Summary:" -ForegroundColor Yellow
Write-Host ""

$rootFiles = (Get-ChildItem -File | Where-Object { $_.Name -ne "restructure_project.ps1" }).Count
$rootDirs = (Get-ChildItem -Directory | Where-Object { $_.Name -notin @(".git", ".vscode", ".agents", "__pycache__", "node_modules") }).Count
$archiveCount = (Get-ChildItem -Path "_archive" -Recurse -File).Count

Write-Host "  Root-level files: $rootFiles" -ForegroundColor White
Write-Host "  Root-level directories: $rootDirs" -ForegroundColor White
Write-Host "  Files archived: $archiveCount" -ForegroundColor White
Write-Host ""
Write-Host "=== Restructure Complete ===" -ForegroundColor Green
Write-Host "Active Python modules remain at root level (imports preserved)." -ForegroundColor Cyan
Write-Host "Unused files moved to _archive/ | Docs moved to docs/" -ForegroundColor Cyan
