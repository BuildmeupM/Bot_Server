# 🗄️ ออกแบบการเก็บข้อมูลประวัติการส่งอีเมลล์

## 📊 ปัญหาของโครงสร้างปัจจุบัน

### 1. **ไม่มี Unique ID**
   - ไม่มี ID ที่เป็น unique identifier ทำให้ยากต่อการอ้างอิงหรือค้นหา
   - Frontend แสดง "การส่งครั้งที่ XXX" ซึ่งอาจไม่ตรงกับลำดับจริง

### 2. **ไม่มี Status Tracking**
   - ไม่มี field สำหรับเก็บสถานะการส่ง (สำเร็จ/ล้มเหลว)
   - ไม่สามารถแยกแยะได้ว่าอีเมลล์ส่งสำเร็จหรือไม่

### 3. **ข้อมูลไม่ครบถ้วน**
   - ไม่มีข้อมูล attachments (ไฟล์ที่แนบ)
   - ไม่มี error message ถ้าส่งไม่สำเร็จ
   - ไม่มีข้อมูล sender email
   - ไม่มีข้อมูล SMTP config ที่ใช้

### 4. **ไม่มี Metadata**
   - ไม่มีข้อมูลผู้ส่ง (user/system)
   - ไม่มีข้อมูล IP address
   - ไม่มีข้อมูล session ID

### 5. **การเรียงลำดับ**
   - ใช้ `reverse()` ซึ่งอาจไม่ถูกต้องถ้ามีข้อมูลมาก
   - ควรใช้ timestamp sorting แทน

## 🎯 โครงสร้างข้อมูลที่แนะนำ

### Schema Design

```json
{
  "id": "uuid-string",                    // Unique ID (UUID v4)
  "status": "success|failed|pending",      // สถานะการส่ง
  "sent_time": "2026-01-23T19:46:41",     // ISO 8601 format
  "created_at": "2026-01-23T19:46:40",    // เวลาที่สร้าง record
  
  // Pattern & Signature
  "pattern_name": "466 แดดดี้ โปรเจค",    // หรือ null
  "pattern_id": "pattern-uuid",            // ID ของ pattern (ถ้ามี)
  "signature_name": "วุ้นเส้น",            // หรือ null
  "signature_id": "signature-uuid",        // ID ของ signature (ถ้ามี)
  
  // Email Details
  "from_email": "yuttana.w@bmuc.co.th",   // อีเมลล์ผู้ส่ง
  "to_emails": ["email1@example.com"],    // รายการผู้รับ
  "cc_emails": ["cc@example.com"],        // รายการ CC
  "bcc_emails": ["bcc@example.com"],      // รายการ BCC (ถ้ามี)
  "subject": "หัวข้ออีเมลล์",
  "body": "เนื้อหาอีเมลล์",
  "body_html": "<html>...</html>",        // HTML version (ถ้ามี)
  
  // Attachments
  "attachments": [
    {
      "filename": "file.pdf",
      "size": 123456,
      "content_type": "application/pdf",
      "is_zipped": false
    }
  ],
  "attachment_count": 3,
  "total_size": 1234567,                  // ขนาดรวม (bytes)
  
  // LINE Integration
  "line_enabled": true,
  "line_user_id": "C28e6b9cfcfec3c419ec6cb8eb52f294b",
  "line_message": "ข้อความที่ส่งไปยัง LINE",
  "line_sent": true,                       // ส่ง LINE สำเร็จหรือไม่
  "line_sent_time": "2026-01-23T19:46:42",
  
  // Summary Data (PDF)
  "summary_pdf_generated": true,
  "summary_data": {
    "title": "สรุปข้อมูล",
    "company": "บริษัท ABC จำกัด",
    "tax_id": "0105564065416",
    "period": "ประจำเดือน 10.68",
    "amounts": {
      "pnd1": 0.00,
      "pnd3": 0.00,
      "pp30": 0.00
    }
  },
  
  // Error Tracking
  "error_message": null,                   // ข้อความ error (ถ้ามี)
  "error_code": null,                     // Error code (ถ้ามี)
  "retry_count": 0,                       // จำนวนครั้งที่ลองส่งใหม่
  
  // SMTP Config
  "smtp_server": "smtppro.zoho.com",
  "smtp_port": 587,
  "smtp_use_tls": true,
  
  // Metadata
  "user_agent": "Mozilla/5.0...",          // Browser user agent
  "ip_address": "127.0.0.1",              // IP address ของผู้ส่ง
  "session_id": "session-uuid",           // Session ID (ถ้ามี)
  
  // Statistics
  "email_size": 12345,                    // ขนาดอีเมลล์ (bytes)
  "delivery_time": 1.23,                  // เวลาที่ใช้ในการส่ง (seconds)
  
  // Additional Info
  "notes": null,                          // หมายเหตุเพิ่มเติม
  "tags": ["tax", "monthly"],             // Tags สำหรับค้นหา
  "related_ids": []                       // ID ที่เกี่ยวข้อง (เช่น bulk send)
}
```

## 🔧 การปรับปรุงที่แนะนำ

### 1. **Backend Changes**

#### A. เพิ่ม UUID สำหรับแต่ละ record
```python
import uuid
from datetime import datetime

history_entry = {
    'id': str(uuid.uuid4()),
    'status': 'success',  # หรือ 'failed', 'pending'
    'sent_time': datetime.now().isoformat(),
    'created_at': datetime.now().isoformat(),
    # ... fields อื่นๆ
}
```

#### B. เพิ่ม status tracking
```python
def save_email_history(
    status: str = 'success',  # 'success', 'failed', 'pending'
    error_message: Optional[str] = None,
    # ... fields อื่นๆ
):
```

#### C. เพิ่มข้อมูล attachments
```python
attachments = [
    {
        'filename': file.filename,
        'size': file.size,
        'content_type': file.content_type,
        'is_zipped': is_zipped
    }
    for file in attachment_files
]
```

#### D. เพิ่ม metadata
```python
metadata = {
    'user_agent': request.headers.get('User-Agent'),
    'ip_address': request.remote_addr,
    'session_id': session.get('session_id'),
}
```

### 2. **Frontend Changes**

#### A. แสดงข้อมูลที่ครบถ้วนขึ้น
- แสดง status (สำเร็จ/ล้มเหลว)
- แสดงจำนวน attachments
- แสดง error message (ถ้ามี)
- แสดงข้อมูลเพิ่มเติม (expandable)

#### B. เพิ่มการค้นหาและกรอง
- ค้นหาตาม pattern, signature, subject
- กรองตาม status, date range
- เรียงลำดับตาม field ต่างๆ

#### C. เพิ่มการแสดงรายละเอียด
- Modal สำหรับดูรายละเอียดเต็ม
- แสดง attachments list
- แสดง error details (ถ้ามี)

## 📋 Migration Plan

### Phase 1: เพิ่ม Fields ใหม่ (Backward Compatible)
- เพิ่ม `id`, `status`, `created_at` ให้กับ records ใหม่
- Records เก่ายังทำงานได้ (ใช้ default values)

### Phase 2: Migrate ข้อมูลเก่า
- สร้าง script สำหรับ migrate ข้อมูลเก่า
- เพิ่ม `id` และ `status` ให้กับ records เก่า

### Phase 3: ปรับปรุง Frontend
- แสดงข้อมูลใหม่
- เพิ่มการค้นหาและกรอง

## 🎨 UI Improvements

### 1. **History List View**
```
┌─────────────────────────────────────────────────┐
│ 📊 ประวัติการส่ง (428 รายการ)                    │
│ [🔍 ค้นหา] [📅 กรอง] [📥 Export Excel]          │
├─────────────────────────────────────────────────┤
│ ✅ #428 | Pattern: 466 แดดดี้ | วุ้นเส้น        │
│    📧 3 ผู้รับ | 📎 5 ไฟล์ | 📱 LINE ✓          │
│    2026-01-23 19:46:41                          │
│    [ดูรายละเอียด]                                │
├─────────────────────────────────────────────────┤
│ ❌ #427 | Pattern: ไม่ใช้ | ไม่ใช้ Signature   │
│    ⚠️ Error: Connection timeout                 │
│    2026-01-23 19:42:21                          │
│    [ดูรายละเอียด] [ลองส่งใหม่]                  │
└─────────────────────────────────────────────────┘
```

### 2. **Detail Modal**
- แสดงข้อมูลครบถ้วน
- แสดง attachments list
- แสดง error details (ถ้ามี)
- ปุ่ม "ลองส่งใหม่" (ถ้าส่งไม่สำเร็จ)

## 🔒 Security Considerations

1. **ไม่เก็บรหัสผ่าน** - ไม่ควรเก็บรหัสผ่านใน history
2. **Mask sensitive data** - Mask อีเมลล์บางส่วน (เช่น y***@bmuc.co.th)
3. **Access control** - จำกัดการเข้าถึง history (admin only?)

## 📈 Performance Considerations

1. **Pagination** - แบ่งหน้าเมื่อมีข้อมูลมาก
2. **Indexing** - สร้าง index สำหรับค้นหา (ถ้าใช้ database)
3. **Archiving** - ย้ายข้อมูลเก่าไป archive (ถ้ามีข้อมูลมาก)

## 🗄️ Database Option (Future)

ถ้าต้องการ scalability มากขึ้น อาจพิจารณาใช้ database:
- SQLite (เบา, ง่าย)
- PostgreSQL (powerful, scalable)
- MongoDB (flexible schema)
