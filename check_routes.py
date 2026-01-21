"""
สคริปต์ตรวจสอบ routes ใน web_app.py
"""
import sys
from pathlib import Path

# เพิ่ม current directory เข้า sys.path
current_dir = Path(__file__).parent.resolve()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

print("=" * 60)
print("🔍 ตรวจสอบ routes ใน web_app.py")
print("=" * 60)

try:
    # Import Flask app
    from web_app import app
    
    print("\n📋 Routes ทั้งหมด:")
    print("-" * 60)
    
    routes = []
    for rule in app.url_map.iter_rules():
        methods = sorted(rule.methods - {'HEAD', 'OPTIONS'})
        routes.append({
            'path': str(rule),
            'methods': methods,
            'endpoint': rule.endpoint
        })
    
    # เรียงตาม path
    routes.sort(key=lambda x: x['path'])
    
    # แสดง routes ทั้งหมด
    for route in routes:
        methods_str = ', '.join(route['methods'])
        print(f"  {route['path']:50} [{methods_str}]")
    
    # ตรวจสอบ routes ที่สำคัญ
    print("\n✅ ตรวจสอบ routes ที่สำคัญ:")
    print("-" * 60)
    
    important_routes = {
        '/api/stats': ['GET'],
        '/api/admin/line-notify/status': ['GET'],
        '/api/admin/line-notify/toggle': ['POST']
    }
    
    all_found = True
    for route_path, expected_methods in important_routes.items():
        found = False
        for route in routes:
            if route['path'] == route_path:
                # ตรวจสอบ methods
                route_methods = set(route['methods'])
                expected_set = set(expected_methods)
                if expected_set.issubset(route_methods):
                    print(f"  ✅ {route_path:50} [{', '.join(expected_methods)}]")
                    found = True
                    break
                else:
                    print(f"  ⚠️  {route_path:50} พบแต่ methods ไม่ตรง [{', '.join(route['methods'])}]")
                    found = True
                    all_found = False
                    break
        
        if not found:
            print(f"  ❌ {route_path:50} - ไม่พบ!")
            all_found = False
    
    # ตรวจสอบ functions
    print("\n🔧 ตรวจสอบ functions:")
    print("-" * 60)
    
    try:
        from report_manager import get_line_notifications_enabled, set_line_notifications_enabled
        print("  ✅ get_line_notifications_enabled - พบ")
        print("  ✅ set_line_notifications_enabled - พบ")
        
        # ทดสอบการทำงาน
        current_status = get_line_notifications_enabled()
        print(f"  📊 สถานะปัจจุบัน: {current_status}")
        
    except ImportError as e:
        print(f"  ❌ ไม่สามารถ import functions: {e}")
        all_found = False
    
    print("\n" + "=" * 60)
    if all_found:
        print("✅ การตรวจสอบเสร็จสิ้น - Routes ทั้งหมดถูกต้อง!")
        print("\n💡 หมายเหตุ:")
        print("   - ถ้า server ยังไม่ restart ให้ restart server")
        print("   - ตรวจสอบว่า server กำลังรัน web_app.py (ไม่ใช่ control_api.py)")
    else:
        print("❌ พบปัญหา - บาง routes ไม่ถูกต้อง!")
        print("\n💡 วิธีแก้ไข:")
        print("   1. ตรวจสอบว่า routes ถูกเพิ่มใน web_app.py แล้ว")
        print("   2. Restart Flask server")
        print("   3. ตรวจสอบว่า server กำลังรัน web_app.py")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ เกิดข้อผิดพลาด: {e}")
    import traceback
    traceback.print_exc()

