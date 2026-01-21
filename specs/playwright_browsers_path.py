import os, sys
from pathlib import Path

# ตั้งค่า Playwright browsers path สำหรับ PyInstaller
base = Path(getattr(sys, "_MEIPASS", Path(os.getcwd())))
candidates = [
    base / "ms-playwright",
    base / "playwright" / ".local-browsers",
    base / "_internal" / "ms-playwright",
    base / "_internal" / "playwright" / ".local-browsers",
]

# หาโฟลเดอร์ ms-playwright ที่มีอยู่
for c in candidates:
    if c.exists() and (c / "chromium").exists():
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(c)
        print(f"Set PLAYWRIGHT_BROWSERS_PATH to: {c}")
        break
else:
    # ถ้าไม่พบในโฟลเดอร์ที่แพ็ก ให้ใช้โฟลเดอร์ในเครื่อง
    home = Path.home()
    local_candidates = [
        home / "AppData" / "Local" / "ms-playwright",
        home / ".cache" / "ms-playwright",
    ]
    for c in local_candidates:
        if c.exists() and (c / "chromium").exists():
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(c)
            print(f"Set PLAYWRIGHT_BROWSERS_PATH to local: {c}")
            break

# ตั้งค่า environment variables อื่นๆ ที่จำเป็น
os.environ["PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD"] = "1"
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "")

# เพิ่ม path สำหรับ DLLs
dll_paths = [
    base / "_internal",
    base / "_internal" / "playwright",
    base,
]

for dll_path in dll_paths:
    if dll_path.exists():
        dll_str = str(dll_path)
        if dll_str not in os.environ.get("PATH", ""):
            current_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{dll_str};{current_path}"
            print(f"Added to PATH: {dll_str}")
