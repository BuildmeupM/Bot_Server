# 🔍 แผนพัฒนาระบบ Audit Check (ตรวจภาษี)

> **ไฟล์หลัก:** `templates/auditcheck.html` (10,613 บรรทัด)  
> **Backend:** `web_app.py` — 35+ API endpoints  
> **อัปเดตล่าสุด:** 2026-03-21

---

## 📐 ภาพรวมระบบ

```
📦 Bot_Server/
├── web_app.py                              ← Backend (Flask) — ทุก API route
├── templates/
│   └── auditcheck.html                     ← หน้าเว็บ (CSS + HTML + JS รวมไฟล์เดียว)
├── static/
│   ├── css/auditcheck.css                  ← CSS เพิ่มเติม
│   └── js/auditcheck.js                    ← JS สำหรับ OCR Queue เพิ่มเติม
└── cache/
    └── auditcheck_state_*.json             ← ไฟล์บันทึกสถานะการตรวจ
```

---

## 🏗️ โครงสร้างไฟล์ auditcheck.html

| ช่วงบรรทัด | ส่วน | รายละเอียด |
|-----------|------|-----------|
| 1–1155 | **CSS** | Inline styles ทั้งหมด |
| 1156–1958 | **HTML** | โครงสร้างหน้า + Modals |
| 1959–10613 | **JavaScript** | Logic ฟังก์ชันทั้งหมด |

---

## 🏷️ 3 แท็บหลัก

| # | แท็บ | สถานะ | บรรทัด HTML |
|---|------|-------|------------|
| 1 | ตรวจภาษีหัก ณ ที่จ่าย | 🚧 ยังไม่พัฒนา | 1181–1186 |
| 2 | ระบบฝากอ่านข้อมูล (OCR Queue) | ✅ ใช้งานได้ (แท็บเริ่มต้น) | 1189–1344 |
| 3 | ตรวจภาษีมูลค่าเพิ่ม (VAT) | ✅ ใช้งานได้ (🔒 มีรหัสผ่าน) | 1346–1958 |

---

## 🔄 5 ขั้นตอนตรวจสอบ VAT (แท็บ 3)

```
startAudit()
    │
    ▼
Step 1: checkStep1()  ─── ตรวจไฟล์งบทดลอง
    │                      API: /api/auditcheck/check-trial-balance
    ▼
Step 2: checkStep2()  ─── ตรวจไฟล์ภาษีซื้อ
    │                      API: /api/auditcheck/check-purchase-tax
    ▼
Step 3: checkStep3()  ─── เทียบข้อมูลงบทดลอง (เดือนก่อน vs เดือนปัจจุบัน)
    │                      API: /api/auditcheck/compare-trial-balance-files
    ▼
Step 4: checkStep4()  ─── ตรวจไฟล์ Excel OCR
    │                      API: /api/auditcheck/check-excel-files
    │
    ├── [พบไฟล์]   → ไปต่อ Step 5
    └── [ไม่พบ]    → แสดง 3 ตัวเลือก:
                        🤖 ใช้ระบบ OCR  → runOCRForStep4()
                        📁 อัปโหลด Excel → uploadExcelForStep4()
                        📥 โหลดเทมเพลต  → downloadExcelTemplate()
    │
    ▼
Step 5: checkStep5()  ─── เทียบภาษีซื้อ vs ข้อมูล OCR
                           API: /api/auditcheck/compare-purchase-tax-ocr
                           → แสดงผลเป็น Accordion (ตรง/ไม่ตรง/ไม่มี OCR)
```

---

## ⚡ JavaScript — แบ่งตามกลุ่มฟังก์ชัน

### 🔧 Core & UI (บรรทัด 1963–2183)
| ฟังก์ชัน | บรรทัด | คำอธิบาย |
|---------|--------|---------|
| `autoRestoreAuditState()` | 1963 | กู้คืนสถานะเมื่อโหลดหน้า |
| `setupYearDropdown()` | 2033 | สร้าง Dropdown ปี |
| `switchTab()` | 2110 | สลับแท็บ |
| `showVatPasswordModal()` | 2156 | แสดง Password overlay |

### 📥 OCR Queue (บรรทัด 2184–2942)
| ฟังก์ชัน | บรรทัด | คำอธิบาย |
|---------|--------|---------|
| `submitOCRQueue()` | 2184 | ส่งคิว OCR |
| `loadOCRQueue()` | 2318 | โหลดรายการคิว |
| `renderQueueItem()` | 2430 | แสดงผลรายการคิว |
| `cancelOCRQueue()` | 2777 | ยกเลิกคิว |
| `checkUnreadFiles()` | 2817 | ตรวจไฟล์ที่ยังไม่ได้อ่าน |
| `startOCRQueuePolling()` | 3003 | Polling ทุก 5 วินาที |

### 🏢 บริษัท (บรรทัด 3024–3665)
| ฟังก์ชัน | บรรทัด | คำอธิบาย |
|---------|--------|---------|
| `loadCompanies()` | 3024 | โหลดรายชื่อบริษัท |
| `setupAutocomplete()` | 3041 | ตั้งค่า Autocomplete |
| `selectCompany()` | 3164 | เลือกบริษัท |
| `showBranchSelectionModal()` | 3202 | Modal เลือกสาขา |
| `loadCompanyInfo()` | 3539 | โหลด Tax ID, สถานะ VAT |

### 🗄️ Database Config (บรรทัด 3667–3966)
| ฟังก์ชัน | บรรทัด | คำอธิบาย |
|---------|--------|---------|
| `openDatabaseModal()` | 3667 | เปิด Modal จัดการ DB |
| `saveCompanyConfigForm()` | 3819 | บันทึกการตั้งค่าบริษัท |

### 🔍 5 Steps ตรวจสอบ (บรรทัด 3967–6559)
| ฟังก์ชัน | บรรทัด | Step |
|---------|--------|------|
| `startAudit()` | 3967 | เริ่มต้น |
| `checkStep1()` | 4198 | 1 — งบทดลอง |
| `checkStep2()` | 4246 | 2 — ภาษีซื้อ |
| `checkStep3()` | 4358 | 3 — เทียบงบ |
| `checkStep4()` | 4521 | 4 — Excel OCR |
| `checkStep5()` | 4761 | 5 — เทียบข้อมูล |
| `generateComparisonRowHTML()` | 5264 | สร้าง Accordion แต่ละแถว |

### 📊 Comparison UI (บรรทัด 6560–7280)
| ฟังก์ชัน | บรรทัด | คำอธิบาย |
|---------|--------|---------|
| `switchComparisonTab()` | 6560 | แท็บ: ทั้งหมด/ไม่ตรง/ตรง |
| `filterComparisonByReference()` | 6742 | ค้นหาตามเลขอ้างอิง |
| `viewPdfPreview()` | 7109 | ดู PDF ตัวอย่าง |

### 💾 State Management (บรรทัด 7282–7586)
| ฟังก์ชัน | บรรทัด | คำอธิบาย |
|---------|--------|---------|
| `saveAuditState()` | 7301 | บันทึกสถานะ |
| `saveAuditStateToBackend()` | 7403 | ส่งไป Server |
| `loadAuditState()` | 7428 | โหลดจาก Server |
| `restoreAuditState()` | 7494 | กู้คืนสถานะ |
| `triggerAutoSave()` | 7563 | Auto-save (debounce 3 วิ) |

### ✅ Approval & Document (บรรทัด 7579–9527)
| ฟังก์ชัน | บรรทัด | คำอธิบาย |
|---------|--------|---------|
| `approveField()` | 7586 | อนุมัติฟิลด์ |
| `cancelApproval()` | 8416 | ยกเลิกอนุมัติ |
| `moveDocumentToReview()` | 8706 | ย้ายเอกสาร |
| `toggleSelfCheckMode()` | 8781 | โหมดตรวจด้วยตัวเอง |
| `removeComparisonItem()` | 8896 | ลบรายการ |
| `markDocumentAsInvalid()` | 9243 | เอกสารใช้ไม่ได้ |

### 📤 Export & OCR (บรรทัด 9528–10530)
| ฟังก์ชัน | บรรทัด | คำอธิบาย |
|---------|--------|---------|
| `exportToExcel()` | 9528 | ส่งออกผลตรวจ |
| `showOCRConfirmModal()` | 9663 | Modal ยืนยัน OCR |
| `runOCRForStep4()` | 10380 | รัน OCR |
| `downloadExcelTemplate()` | 10475 | ดาวน์โหลดเทมเพลต |
| `uploadExcelForStep4()` | 10486 | อัปโหลด Excel |

---

## 🔌 Backend API ทั้งหมด

### จัดการบริษัท & Database
```
GET  /api/auditcheck/companies              ← รายชื่อบริษัท
POST /api/auditcheck/companies              ← เพิ่มบริษัท
GET  /api/auditcheck/company                ← ข้อมูลบริษัท (Tax ID, สถานะ)
GET  /api/auditcheck/company-branches       ← รายการสาขา
POST /api/auditcheck/branch-info            ← ข้อมูลสาขา
GET  /api/auditcheck/databases              ← รายการ Database
POST /api/auditcheck/databases              ← สร้าง Database
DEL  /api/auditcheck/databases/{id}         ← ลบ Database
POST /api/auditcheck/company-database       ← ตั้งค่า Database ของบริษัท
```

### 5 Steps ตรวจสอบ
```
POST /api/auditcheck/check-files            ← ตรวจโครงสร้างโฟลเดอร์
POST /api/auditcheck/check-trial-balance    ← Step 1: ค้นหางบทดลอง
POST /api/auditcheck/check-purchase-tax     ← Step 2: ค้นหาภาษีซื้อ
POST /api/auditcheck/compare-trial-balance-files ← Step 3: เทียบงบทดลอง
POST /api/auditcheck/check-excel-files      ← Step 4: ค้นหา Excel OCR
POST /api/auditcheck/compare-purchase-tax-ocr ← Step 5: เทียบภาษีซื้อ vs OCR
```

### OCR & ไฟล์
```
POST /api/auditcheck/run-ocr                ← รัน OCR จาก PDF
GET  /api/auditcheck/download-excel-template ← ดาวน์โหลดเทมเพลต Excel
POST /api/auditcheck/upload-excel           ← อัปโหลด Excel
POST /api/auditcheck/ocr-queue/check        ← ตรวจจำนวนไฟล์ก่อนส่งคิว
POST /api/auditcheck/ocr-queue/submit       ← ส่งเข้าคิว OCR
GET  /api/auditcheck/ocr-queue/list         ← รายการคิวทั้งหมด
POST /api/auditcheck/ocr-queue/cancel/{id}  ← ยกเลิกคิว
POST /api/auditcheck/ocr-queue/check-unread ← ตรวจไฟล์ที่ยังไม่ได้อ่าน
POST /api/auditcheck/ocr-queue/rerun-unread ← อ่านไฟล์ค้างอีกครั้ง
GET  /api/auditcheck/ocr-progress/{id}      ← ความคืบหน้า OCR
```

### เอกสาร & ส่งออก
```
POST /api/auditcheck/find-pdf-by-reference          ← ค้นหา PDF จากเลขอ้างอิง
GET  /api/auditcheck/view-pdf/{path}                ← ดูตัวอย่าง PDF
POST /api/auditcheck/move-document-to-review        ← ย้ายเอกสารไปตรวจ
POST /api/auditcheck/move-all-mismatched-documents  ← ย้ายเอกสารไม่ตรงทั้งหมด
POST /api/auditcheck/mark-documents-invalid         ← ทำเครื่องหมายเอกสารใช้ไม่ได้
POST /api/auditcheck/export-excel                   ← ส่งออกผลตรวจเป็น Excel
POST /api/auditcheck/save-state                     ← บันทึกสถานะการตรวจ
GET  /api/auditcheck/load-state                     ← โหลดสถานะการตรวจ
```

---

## 📁 โครงสร้างโฟลเดอร์ที่ระบบค้นหา

```
V:/A.โฟร์เดอร์หลัก/{บริษัท}/
└── บัญชี/
    ├── 002-รายจ่าย/
    │   └── PV/
    │       ├── {year-month}/                ← เช่น 2026-03
    │       │   └── VAT/
    │       │       ├── *.pdf                ← PDF สำหรับ OCR
    │       │       ├── *ocr*.xlsx           ← Excel จากระบบ OCR (Step 4 ค้นหา)
    │       │       └── *งบทดลอง*.xlsx       ← งบทดลอง (Step 1 ค้นหา)
    │       └── {year}/
    │           └── {year-month}/            ← โครงสร้างทางเลือก
    │               └── VAT/ (เหมือนข้างบน)
    └── 003-ภาษี/
        └── ภ.พ.30/
            └── {year}/
                └── {month-year}/
                    └── *ภาษีซื้อ*.xlsx     ← ภาษีซื้อ (Step 2 ค้นหา)
```

---

## 💡 แนวทางเพิ่มฟีเจอร์ใหม่

### เพิ่ม Step ตรวจสอบใหม่
```
1. เพิ่ม <div class="step" id="stepN"> ใน HTML          (~บรรทัด 1920)
2. สร้างฟังก์ชัน checkStepN() ใน JavaScript              (~บรรทัด 4760)
3. เรียก checkStepN() ต่อจาก checkStep5()
4. เพิ่ม API route ใน web_app.py
```

### เพิ่มแท็บใหม่
```
1. เพิ่ม <button class="tab-button"> ใน HTML             (~บรรทัด 1177)
2. เพิ่ม <div class="tab-content"> หลังแท็บสุดท้าย
3. อัปเดต switchTab() ถ้ามี Logic พิเศษ
```

### เพิ่มฟิลด์เปรียบเทียบ Step 5
```
1. อัปเดต generateComparisonRowHTML()                    (~บรรทัด 5264)
2. เพิ่ม column mapping ใน web_app.py compare-purchase-tax-ocr
3. อัปเดต approveField() สำหรับฟิลด์ใหม่
```

### เพิ่ม Company Config ใหม่
```
1. เพิ่มฟิลด์ใน HTML Company Config Form                (~บรรทัด 1651)
2. อัปเดต saveCompanyConfigForm()                        (~บรรทัด 3819)
3. อัปเดต API /api/auditcheck/company-database ใน web_app.py
```
