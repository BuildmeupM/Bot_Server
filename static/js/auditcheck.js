        // เก็บข้อมูล OCR จาก Step 4 เพื่อใช้ใน Step 5 (global variable)
        let step4OCRData = null;
        
        // เก็บข้อมูล Step 4 สำหรับใช้เมื่อกดยกเลิก
        let step4Data = null;
        
        // Load companies on page load
        document.addEventListener('DOMContentLoaded', function() {
            loadCompanies();
            
            // Setup year dropdown first - ใช้ setTimeout เพื่อให้แน่ใจว่า DOM พร้อมแล้ว
            setTimeout(function() {
                setupYearDropdown();
                
                // Auto-restore สถานะการตรวจสอบ (ถ้ามี)
                autoRestoreAuditState();
            }, 100);
        });
        
        /**
         * Auto-restore สถานะการตรวจสอบเมื่อโหลดหน้าเว็บ
         */
        async function autoRestoreAuditState() {
            // รอให้ form elements พร้อมก่อน
            await new Promise(resolve => setTimeout(resolve, 500));
            
            const taxMonth = document.getElementById('taxMonth')?.value;
            const taxYear = document.getElementById('taxYear')?.value;
            const company = document.getElementById('companyValue')?.value || document.getElementById('companySelect')?.value;
            
            // ถ้ายังไม่ได้เลือกข้อมูล ให้ไม่ restore
            if (!taxMonth || !taxYear || !company) {
                console.log('⚠️ ยังไม่ได้เลือกข้อมูล - ข้าม auto-restore');
                return;
            }
            
            const taxMonthFormatted = `${taxYear}-${taxMonth}`;
            
            // โหลดสถานะ
            const savedState = await loadAuditState(company, taxMonthFormatted);
            
            if (savedState) {
                // แปลงวันที่และเวลาล่าสุดที่บันทึก
                const lastSavedTimestamp = savedState.last_saved || savedState.timestamp;
                let lastSavedDate = '';
                if (lastSavedTimestamp) {
                    try {
                        const dateObj = new Date(lastSavedTimestamp);
                        lastSavedDate = dateObj.toLocaleString('th-TH', {
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                            second: '2-digit',
                            hour12: false
                        });
                    } catch (e) {
                        lastSavedDate = lastSavedTimestamp;
                    }
                } else {
                    lastSavedDate = 'ไม่ทราบวันที่';
                }
                
                // ถามผู้ใช้ว่าต้องการ restore หรือไม่
                const shouldRestore = confirm(
                    `ต้องการจะดึงข้อมูลเดิมที่เคยตรวจไปแล้ว วันที่และเวลาล่าสุดที่ระบบบันทึก หรือไม่?\n\n` +
                    `📅 วันที่และเวลาล่าสุดที่บันทึก: ${lastSavedDate}\n\n` +
                    `📊 สรุปข้อมูลที่บันทึกไว้:\n` +
                    `- หมายเหตุ: ${Object.keys(savedState.comparisonNotes || {}).length} รายการ\n` +
                    `- การอนุมัติ: ${Object.keys(savedState.comparisonApprovals || {}).length} รายการ\n` +
                    `- เอกสารใช้ไม่ได้: ${Object.keys(savedState.invalidDocuments || {}).length} รายการ\n\n` +
                    `กด "OK" เพื่อดึงข้อมูลเดิม หรือ "Cancel" เพื่อเริ่มตรวจใหม่`
                );
                
                if (shouldRestore) {
                    restoreAuditState(savedState);
                    
                    // ถ้ามี comparison results ให้ refresh Step 5
                    if (savedState.comparisonResults && savedState.comparisonResults.count > 0) {
                        console.log('🔄 กำลัง refresh Step 5 เพื่อแสดงข้อมูลที่ restore...');
                        // Trigger Step 5 check อีกครั้ง (แต่ใช้ข้อมูลที่ restore แล้ว)
                        setTimeout(() => {
                            checkStep5(taxMonthFormatted, company);
                        }, 1000);
                    }
                    
                    showToast('success', '✅ โหลดข้อมูลการตรวจสอบที่บันทึกไว้เรียบร้อยแล้ว');
                }
            }
        }
        
        function setupYearDropdown() {
            console.log('🔄 เริ่มต้น setupYearDropdown()');
            const yearSelect = document.getElementById('taxYear');
            if (!yearSelect) {
                console.error('❌ ไม่พบ element taxYear');
                // ลองหาใหม่หลังจาก delay
                setTimeout(function() {
                    const retrySelect = document.getElementById('taxYear');
                    if (retrySelect) {
                        console.log('✅ พบ element taxYear หลังจาก delay');
                        setupYearDropdown();
                    } else {
                        console.error('❌ ยังไม่พบ element taxYear หลังจาก delay');
                    }
                }, 500);
                return;
            }
            
            console.log('✅ พบ element taxYear แล้ว กำลังสร้าง dropdown...');
            
            // ล้าง options เดิมทั้งหมด
            yearSelect.innerHTML = '';
            
            const currentYear = new Date().getFullYear();
            
            // เพิ่มปีจากปีปัจจุบัน - 1 ถึงปีปัจจุบัน + 1 (ย้อนหลัง 1 ปี, ปีปัจจุบัน, ล่วงหน้า 1 ปี)
            for (let year = currentYear - 1; year <= currentYear + 1; year++) {
                const option = document.createElement('option');
                option.value = year;
                option.textContent = year;
                // ตั้งค่าเริ่มต้นเป็นปีปัจจุบัน
                if (year === currentYear) {
                    option.selected = true;
                }
                yearSelect.appendChild(option);
            }
            
            console.log(`✅ สร้าง dropdown ปีสำเร็จ: ${currentYear - 1}, ${currentYear}, ${currentYear + 1}`);
            console.log(`✅ ตั้งค่าเริ่มต้นเป็นปีปัจจุบัน: ${currentYear}`);
            
            // ตรวจสอบว่า options ถูกสร้างหรือไม่
            if (yearSelect.options.length === 0) {
                console.error('❌ ไม่สามารถสร้าง dropdown ปีได้ - ลองสร้างแบบ hardcode');
                // ลองสร้างแบบ hardcode
                const years = [currentYear - 1, currentYear, currentYear + 1];
                years.forEach(year => {
                    const option = document.createElement('option');
                    option.value = year;
                    option.textContent = year;
                    if (year === currentYear) {
                        option.selected = true;
                    }
                    yearSelect.appendChild(option);
                });
                console.log(`✅ สร้าง dropdown ปีแบบ hardcode สำเร็จ: ${yearSelect.options.length} ปี`);
            }
            
            // ตั้งค่าเดือนปัจจุบันหลังจากสร้าง dropdown เสร็จ
            setTimeout(function() {
                const now = new Date();
                const month = String(now.getMonth() + 1).padStart(2, '0');
                const taxMonthEl = document.getElementById('taxMonth');
                
                // ตั้งค่าเดือน
                if (taxMonthEl) {
                    taxMonthEl.value = month;
                    console.log(`✅ ตั้งค่าเดือน: ${month}`);
                }
                
                // ตรวจสอบว่าปีถูกตั้งค่าถูกต้องหรือไม่
                if (yearSelect && yearSelect.value != currentYear) {
                    yearSelect.value = currentYear;
                    console.log(`✅ ตั้งค่าปีเป็นปีปัจจุบัน: ${currentYear}`);
                }
            }, 100);
        }
        
        function switchTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Remove active class from all buttons
            document.querySelectorAll('.tab-button').forEach(btn => {
                btn.classList.remove('active');
            });
            
            // Show selected tab
            document.getElementById(tabName + '-tab').classList.add('active');
            
            // Add active class to clicked button
            event.target.classList.add('active');
            
            // ถ้าเป็น OCR queue tab ให้โหลดคิว
            if (tabName === 'ocr-queue') {
                loadOCRQueue();
                startOCRQueuePolling();
            } else {
                stopOCRQueuePolling();
            }
        }
        
        // ========== OCR Queue System ==========
        let ocrQueuePollingInterval = null;
        
        // ตัวแปรสำหรับเก็บข้อมูลคิวที่กำลังจะส่ง
        let pendingOCRQueueData = null;
        
        // ฟังก์ชันสำหรับส่งคิว OCR (แสดง modal ยืนยันก่อน)
        async function submitOCRQueue() {
            const pathInput = document.getElementById('ocrQueuePath');
            const path = pathInput.value.trim();
            
            if (!path) {
                alert('กรุณาระบุที่อยู่ไฟล์หรือโฟลเดอร์');
                return;
            }
            
            const submitBtn = document.getElementById('submitOCRQueueBtn');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span style="font-size: 1.2em;">⏳</span><span>กำลังตรวจสอบ...</span>';
            
            try {
                // เรียก API เพื่อนับไฟล์และคำนวณเวลา
                const checkResponse = await fetch('/api/auditcheck/ocr-queue/check', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        path: path
                    })
                });
                
                const checkData = await checkResponse.json();
                
                if (!checkData.success) {
                    alert('เกิดข้อผิดพลาด: ' + (checkData.error || 'ไม่ทราบสาเหตุ'));
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<span style="font-size: 1.2em;">🚀</span><span>เริ่มอ่านข้อมูล OCR</span>';
                    return;
                }
                
                // เก็บข้อมูลไว้สำหรับยืนยัน (ยังไม่เก็บ ocr_mode เพราะจะให้เลือกใน modal)
                pendingOCRQueueData = {
                    path: path,
                    total_files: checkData.total_files || 0,
                    estimated_time: checkData.estimated_time || 0
                };
                
                // แสดง modal ยืนยัน
                showOCRQueueConfirmModal(checkData.total_files || 0, checkData.estimated_time || 0, path);
                
            } catch (error) {
                console.error('Error checking OCR queue:', error);
                alert('เกิดข้อผิดพลาดในการตรวจสอบ: ' + error.message);
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<span style="font-size: 1.2em;">🚀</span><span>เริ่มอ่านข้อมูล OCR</span>';
            }
        }
        
        // ฟังก์ชันสำหรับแสดง modal ยืนยัน
        function showOCRQueueConfirmModal(totalFiles, estimatedTime, path) {
            const modal = document.getElementById('ocrQueueConfirmModal');
            const pathElement = document.getElementById('ocrQueueConfirmPath');
            const totalFilesElement = document.getElementById('ocrQueueConfirmTotalFiles');
            const estimatedTimeElement = document.getElementById('ocrQueueConfirmEstimatedTime');
            
            pathElement.textContent = path;
            totalFilesElement.textContent = `${totalFiles.toLocaleString('th-TH')} ไฟล์`;
            estimatedTimeElement.textContent = formatEstimatedTime(estimatedTime);
            
            // รีเซ็ต radio button เป็น "อ่านใหม่ทั้งหมด"
            const newModeRadio = document.getElementById('ocrQueueModeNew');
            if (newModeRadio) {
                newModeRadio.checked = true;
            }
            
            modal.style.display = 'flex';
        }
        
        // ฟังก์ชันสำหรับปิด modal ยืนยัน
        function closeOCRQueueConfirmModal() {
            const modal = document.getElementById('ocrQueueConfirmModal');
            modal.style.display = 'none';
            pendingOCRQueueData = null;
        }
        
        // ฟังก์ชันสำหรับยืนยันและส่งคิวจริงๆ
        async function confirmOCRQueueSubmit() {
            if (!pendingOCRQueueData) {
                alert('ไม่พบข้อมูลคิว กรุณาลองอีกครั้ง');
                return;
            }
            
            // ดึงค่า OCR mode ที่เลือกใน modal
            const ocrModeRadio = document.querySelector('input[name="ocrQueueMode"]:checked');
            const ocrMode = ocrModeRadio ? ocrModeRadio.value : 'new';
            
            const confirmBtn = document.getElementById('ocrQueueConfirmBtn');
            confirmBtn.disabled = true;
            confirmBtn.innerHTML = '<span>⏳ กำลังส่งคิว...</span>';
            
            try {
                const response = await fetch('/api/auditcheck/ocr-queue/submit', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        path: pendingOCRQueueData.path,
                        ocr_mode: ocrMode
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // ปิด modal
                    closeOCRQueueConfirmModal();
                    
                    // ล้าง input
                    document.getElementById('ocrQueuePath').value = '';
                    
                    // แสดง toast
                    showToast('success', `✅ ส่งคิวสำเร็จ! คิว ID: ${data.queue_id}`);
                    
                    // โหลดคิวใหม่
                    loadOCRQueue();
                } else {
                    alert('เกิดข้อผิดพลาด: ' + (data.error || 'ไม่ทราบสาเหตุ'));
                }
            } catch (error) {
                console.error('Error submitting OCR queue:', error);
                alert('เกิดข้อผิดพลาดในการส่งคิว: ' + error.message);
            } finally {
                confirmBtn.disabled = false;
                confirmBtn.innerHTML = '✅ ยืนยันและเริ่มอ่าน';
            }
        }
        
        // ฟังก์ชันสำหรับโหลดคิวทั้งหมด
        async function loadOCRQueue() {
            try {
                const response = await fetch('/api/auditcheck/ocr-queue/list');
                const data = await response.json();
                
                if (data.success) {
                    renderOCRQueueList(data.queues || []);
                }
            } catch (error) {
                console.error('Error loading OCR queue:', error);
            }
        }
        
        // ฟังก์ชันสำหรับแสดงคิวทั้งหมด (แยกตามสถานะ)
        function renderOCRQueueList(queues) {
            const queueList = document.getElementById('ocrQueueList');
            
            if (!queues || queues.length === 0) {
                queueList.innerHTML = `
                    <div style="background: #1e293b; padding: 30px; border-radius: 10px; text-align: center; color: #94a3b8;">
                        <div style="font-size: 3em; margin-bottom: 10px;">📭</div>
                        <div>ยังไม่มีคิวที่กำลังทำงาน</div>
                    </div>
                `;
                return;
            }
            
            // กรองรายการที่หมดเวลาแล้ว (30 นาทีหลังจากเสร็จ)
            const now = new Date();
            const validQueues = queues.filter(queue => {
                if (queue.status === 'completed' && queue.auto_remove_at) {
                    const removeTime = new Date(queue.auto_remove_at);
                    return now < removeTime;
                }
                return true; // แสดงรายการที่ยังไม่เสร็จหรือไม่มี auto_remove_at
            });
            
            // แยกตามสถานะ
            const processingQueues = validQueues.filter(q => q.status === 'processing');
            const pendingQueues = validQueues.filter(q => q.status === 'pending');
            const completedQueues = validQueues.filter(q => q.status === 'completed');
            const failedQueues = validQueues.filter(q => q.status === 'failed');
            
            let html = '';
            
            // ส่วนที่กำลังประมวลผล
            if (processingQueues.length > 0) {
                html += `<h3 style="color: #3b82f6; margin-bottom: 15px; display: flex; align-items: center; gap: 8px;"><span>🔄</span><span>ข้อมูลที่กำลังอ่าน (${processingQueues.length})</span></h3>`;
                processingQueues.forEach(queue => {
                    html += renderQueueItem(queue);
                });
            }
            
            // ส่วนที่รอคิว
            if (pendingQueues.length > 0) {
                html += `<h3 style="color: #fbbf24; margin-top: 30px; margin-bottom: 15px; display: flex; align-items: center; gap: 8px;"><span>⏳</span><span>คิวที่กำลังรอ (${pendingQueues.length})</span></h3>`;
                pendingQueues.forEach(queue => {
                    html += renderQueueItem(queue);
                });
            }
            
            // ส่วนที่เสร็จแล้ว (แสดงชื่อบริษัท)
            if (completedQueues.length > 0) {
                // จัดกลุ่มตามชื่อบริษัท
                const groupedByCompany = {};
                completedQueues.forEach(queue => {
                    const companyName = extractCompanyNameFromPath(queue.path);
                    if (!groupedByCompany[companyName]) {
                        groupedByCompany[companyName] = [];
                    }
                    groupedByCompany[companyName].push(queue);
                });
                
                // แสดงแต่ละกลุ่มบริษัท
                Object.keys(groupedByCompany).forEach(companyName => {
                    const companyQueues = groupedByCompany[companyName];
                    html += `<h3 style="color: #10b981; margin-top: 30px; margin-bottom: 15px; display: flex; align-items: center; gap: 8px;"><span>✅</span><span>รายการที่เสร็จแล้ว ${companyName} (${companyQueues.length})</span></h3>`;
                    companyQueues.forEach(queue => {
                        html += renderQueueItem(queue);
                    });
                });
            }
            
            // ส่วนที่ล้มเหลว
            if (failedQueues.length > 0) {
                html += `<h3 style="color: #ef4444; margin-top: 30px; margin-bottom: 15px; display: flex; align-items: center; gap: 8px;"><span>❌</span><span>รายการที่ล้มเหลว (${failedQueues.length})</span></h3>`;
                failedQueues.forEach(queue => {
                    html += renderQueueItem(queue);
                });
            }
            
            if (html === '') {
                html = `
                    <div style="background: #1e293b; padding: 30px; border-radius: 10px; text-align: center; color: #94a3b8;">
                        <div style="font-size: 3em; margin-bottom: 10px;">📭</div>
                        <div>ยังไม่มีคิวที่กำลังทำงาน</div>
                    </div>
                `;
            }
            
            queueList.innerHTML = html;
        }
        
        // ฟังก์ชันสำหรับ escape HTML
        function escapeHtml(text) {
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // ฟังก์ชันสำหรับแสดงรายการคิวแต่ละรายการ
        function renderQueueItem(queue) {
            const status = queue.status || 'pending';
            const statusColors = {
                'pending': { bg: '#fbbf2415', border: '#fbbf24', text: '⏳ รอคิว' },
                'processing': { bg: '#3b82f615', border: '#3b82f6', text: '🔄 กำลังประมวลผล' },
                'completed': { bg: '#10b98115', border: '#10b981', text: '✅ เสร็จสิ้น' },
                'failed': { bg: '#ef444415', border: '#ef4444', text: '❌ ล้มเหลว' }
            };
            
            const statusInfo = statusColors[status] || statusColors['pending'];
            const progress = queue.progress || 0;
            const total = queue.total || 0;
            const completed = queue.completed || 0;
            const estimatedTime = queue.estimated_time || 0;
            
            // คำนวณเวลาที่เหลือก่อนถอดออก (สำหรับรายการที่เสร็จแล้ว)
            let autoRemoveInfo = '';
            if (status === 'completed' && queue.auto_remove_at) {
                const now = new Date();
                const removeTime = new Date(queue.auto_remove_at);
                const remainingMs = removeTime - now;
                
                if (remainingMs > 0) {
                    const remainingMinutes = Math.floor(remainingMs / 60000);
                    const remainingSeconds = Math.floor((remainingMs % 60000) / 1000);
                    autoRemoveInfo = `
                        <div style="color: #94a3b8; font-size: 0.85em; margin-top: 8px;">
                            ⏰ รายการนี้จะถูกถอดออกจากหน้าเว็บอีก ${remainingMinutes} นาที ${remainingSeconds > 0 ? remainingSeconds + ' วินาที' : ''}
                        </div>
                    `;
                }
            }
            
            // สร้าง HTML สำหรับแสดงข้อมูลที่ OCR อ่านได้
            let ocrResultsHtml = '';
            if (status === 'completed') {
                if (queue.ocr_results && queue.ocr_results.length > 0) {
                    ocrResultsHtml = `
                        <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #334155;">
                            <button onclick="toggleOCRResults('${queue.queue_id}')" style="width: 100%; padding: 12px; background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); color: #ffffff; border: 1px solid #3b82f6; border-radius: 8px; cursor: pointer; font-size: 0.95em; font-weight: 600; display: flex; align-items: center; justify-content: center; gap: 8px; transition: all 0.3s; box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);" onmouseover="this.style.background='linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%)'; this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 8px rgba(59, 130, 246, 0.4)';" onmouseout="this.style.background='linear-gradient(135deg, #1e40af 0%, #3b82f6 100%)'; this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 4px rgba(59, 130, 246, 0.3)';">
                                <span style="font-size: 1.1em;">📊</span>
                                <span id="ocrResultsIcon-${queue.queue_id}">▼</span>
                                <span>ดูข้อมูลที่อ่านได้ (${queue.ocr_results.length} ไฟล์)</span>
                            </button>
                            <div id="ocrResults-${queue.queue_id}" style="display: none; margin-top: 10px; padding: 15px; background: #0f172a; border-radius: 8px; border: 1px solid #334155;">
                    `;
                
                queue.ocr_results.forEach((result, idx) => {
                    const filename = escapeHtml(result.filename || '');
                    const taxFormType = escapeHtml(result.tax_form_type || '');
                    const companyName = escapeHtml(result.company_name || '');
                    const taxId = escapeHtml(result.tax_id || '');
                    const branch = escapeHtml(result.branch || '');
                    const date = escapeHtml(result.date || '');
                    const documentNumber = escapeHtml(result.document_number || '');
                    const referenceNumber = escapeHtml(result.reference_number || '');
                    
                    ocrResultsHtml += `
                        <div style="margin-bottom: ${idx < queue.ocr_results.length - 1 ? '20px' : '0'}; padding-bottom: ${idx < queue.ocr_results.length - 1 ? '20px' : '0'}; border-bottom: ${idx < queue.ocr_results.length - 1 ? '1px solid #334155' : 'none'};">
                            <div style="color: #60a5fa; font-weight: 600; margin-bottom: 15px; font-size: 1em; display: flex; align-items: center; gap: 8px;">
                                <span>🤖</span>
                                <span>ไฟล์ OCR</span>
                            </div>
                            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px; padding: 8px; background: #1e293b; border-radius: 6px; border-left: 3px solid #60a5fa;">
                                <span style="color: #94a3b8; font-size: 0.9em; min-width: 120px;">📄 ชื่อไฟล์:</span>
                                <span style="color: #cbd5e1; font-size: 0.9em; font-weight: 600; word-break: break-all;">${filename}</span>
                            </div>
                            
                            <div style="display: flex; flex-direction: column; gap: 10px;">
                    `;
                    
                    // แสดงข้อมูลแบบรายการแนวตั้ง
                    if (documentNumber && documentNumber !== 'ไม่พบ') {
                        ocrResultsHtml += `
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span style="color: #94a3b8; font-size: 0.9em; min-width: 200px;">เลขที่เอกสาร:</span>
                                <span style="color: #10b981; font-size: 0.9em; font-weight: 600;">${documentNumber}</span>
                            </div>
                        `;
                    }
                    
                    if (date && date !== 'ไม่พบ') {
                        ocrResultsHtml += `
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span style="color: #94a3b8; font-size: 0.9em; min-width: 200px;">วันที่:</span>
                                <span style="color: #10b981; font-size: 0.9em; font-weight: 600;">${date}</span>
                            </div>
                        `;
                    }
                    
                    if (companyName && companyName !== 'ไม่พบ') {
                        ocrResultsHtml += `
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span style="color: #94a3b8; font-size: 0.9em; min-width: 200px;">ชื่อบริษัท:</span>
                                <span style="color: #10b981; font-size: 0.9em; font-weight: 600;">${companyName}</span>
                            </div>
                        `;
                    }
                    
                    if (taxId && taxId !== 'ไม่พบ') {
                        ocrResultsHtml += `
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span style="color: #94a3b8; font-size: 0.9em; min-width: 200px;">เลขประจำตัวผู้เสียภาษี:</span>
                                <span style="color: #10b981; font-size: 0.9em; font-weight: 600;">${taxId}</span>
                            </div>
                        `;
                    }
                    
                    if (branch && branch !== 'ไม่พบ') {
                        ocrResultsHtml += `
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span style="color: #94a3b8; font-size: 0.9em; min-width: 200px;">สาขา:</span>
                                <span style="color: #10b981; font-size: 0.9em; font-weight: 600;">${branch}</span>
                            </div>
                        `;
                    }
                    
                    if (referenceNumber && referenceNumber !== 'ไม่พบ') {
                        ocrResultsHtml += `
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span style="color: #94a3b8; font-size: 0.9em; min-width: 200px;">เลขที่เอกสารอ้างอิง (จากชื่อไฟล์):</span>
                                <span style="color: #10b981; font-size: 0.9em; font-weight: 600;">${referenceNumber}</span>
                            </div>
                        `;
                    }
                    
                    // แสดงข้อมูลยอดเงิน
                    const amountBeforeVat = result.amount_before_vat || (result.amounts && result.amounts['ยอดก่อนภาษี']) || 0;
                    const vatAmount = result.vat_amount || (result.amounts && result.amounts['ภาษีมูลค่าเพิ่ม']) || 0;
                    const totalAmount = result.total_amount || (result.amounts && result.amounts['ยอดรวม']) || 0;
                    
                    if (amountBeforeVat > 0 || vatAmount > 0 || totalAmount > 0) {
                        if (amountBeforeVat > 0) {
                            const amountValue = typeof amountBeforeVat === 'number' 
                                ? amountBeforeVat.toLocaleString('th-TH', {minimumFractionDigits: 2, maximumFractionDigits: 2})
                                : escapeHtml(String(amountBeforeVat));
                            ocrResultsHtml += `
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <span style="color: #94a3b8; font-size: 0.9em; min-width: 200px;">ยอดก่อนภาษีมูลค่าเพิ่ม:</span>
                                    <span style="color: #10b981; font-size: 0.9em; font-weight: 600;">${amountValue}</span>
                                </div>
                            `;
                        }
                        
                        if (vatAmount > 0) {
                            const amountValue = typeof vatAmount === 'number' 
                                ? vatAmount.toLocaleString('th-TH', {minimumFractionDigits: 2, maximumFractionDigits: 2})
                                : escapeHtml(String(vatAmount));
                            ocrResultsHtml += `
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <span style="color: #94a3b8; font-size: 0.9em; min-width: 200px;">ยอดภาษีมูลค่าเพิ่ม:</span>
                                    <span style="color: #10b981; font-size: 0.9em; font-weight: 600;">${amountValue}</span>
                                </div>
                            `;
                        }
                        
                        if (totalAmount > 0) {
                            const amountValue = typeof totalAmount === 'number' 
                                ? totalAmount.toLocaleString('th-TH', {minimumFractionDigits: 2, maximumFractionDigits: 2})
                                : escapeHtml(String(totalAmount));
                            ocrResultsHtml += `
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <span style="color: #94a3b8; font-size: 0.9em; min-width: 200px;">ยอดหลังบวกภาษีมูลค่าเพิ่ม:</span>
                                    <span style="color: #10b981; font-size: 0.9em; font-weight: 600;">${amountValue}</span>
                                </div>
                            `;
                        }
                    }
                    
                    if (taxFormType && taxFormType !== 'ไม่ระบุ' && taxFormType !== 'ไม่พบ') {
                        ocrResultsHtml += `
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span style="color: #94a3b8; font-size: 0.9em; min-width: 200px;">ประเภทเอกสาร:</span>
                                <span style="color: #10b981; font-size: 0.9em; font-weight: 600;">${taxFormType}</span>
                            </div>
                        `;
                    }
                    
                    const documentStatus = escapeHtml(result.document_status || '');
                    if (documentStatus && documentStatus !== 'ไม่พบ') {
                        ocrResultsHtml += `
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span style="color: #94a3b8; font-size: 0.9em; min-width: 200px;">สถานะเอกสาร:</span>
                                <span style="color: #cbd5e1; font-size: 0.9em;">${documentStatus}</span>
                            </div>
                        `;
                    }
                    
                    ocrResultsHtml += `</div>`;
                    
                    // แสดงรายการสินค้า
                    const items = result.items || [];
                    if (items && Array.isArray(items) && items.length > 0) {
                        ocrResultsHtml += `
                            <div style="margin-top: 20px;">
                                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
                                    <span style="color: #94a3b8; font-size: 0.9em;">📦 รายการสินค้า:</span>
                                    <span style="color: #64748b; font-size: 0.85em;">(${items.length} รายการ)</span>
                                </div>
                                <div style="max-height: 300px; overflow-y: auto; padding-right: 5px;">
                        `;
                        
                        items.forEach((item, itemIdx) => {
                            // รองรับทั้ง key ภาษาไทยและอังกฤษ
                            const itemName = escapeHtml(item['รายการ'] || item.name || item.product_name || item.description || 'ไม่ระบุ');
                            
                            // ดึงจำนวน (รองรับทั้งภาษาไทยและอังกฤษ)
                            let quantity = 0;
                            const quantityStr = item['จำนวน'] || item.quantity || item.qty || '0';
                            try {
                                // ลบหน่วยออก (เช่น "2 ใบ" -> "2")
                                const quantityClean = typeof quantityStr === 'string' ? quantityStr.split()[0] : String(quantityStr);
                                quantity = parseFloat(quantityClean.replace(/,/g, '')) || 0;
                            } catch {
                                quantity = 0;
                            }
                            
                            // ดึงราคา (รองรับทั้งภาษาไทยและอังกฤษ)
                            let price = 0;
                            const priceStr = item['ราคาต่อหน่วย'] || item.price || item.unit_price || '0';
                            try {
                                price = parseFloat(String(priceStr).replace(/,/g, '').replace('฿', '').trim()) || 0;
                            } catch {
                                price = 0;
                            }
                            
                            // ดึงยอดรวม (รองรับทั้งภาษาไทยและอังกฤษ)
                            let subtotal = 0;
                            const subtotalStr = item['จำนวนเงิน'] || item.subtotal || item.total || '0';
                            try {
                                subtotal = parseFloat(String(subtotalStr).replace(/,/g, '').replace('฿', '').trim()) || 0;
                            } catch {
                                // ถ้าไม่มียอดรวม ให้คำนวณจากจำนวน x ราคา
                                subtotal = quantity * price;
                            }
                            
                            ocrResultsHtml += `
                                <div style="background: #1e293b; border-left: 4px solid #3b82f6; padding: 12px; border-radius: 6px; margin-bottom: 10px;">
                                    <div style="display: flex; align-items: flex-start; gap: 10px;">
                                        <div style="width: 28px; height: 28px; border-radius: 50%; background: #334155; display: flex; align-items: center; justify-content: center; flex-shrink: 0; margin-top: 2px;">
                                            <span style="color: #cbd5e1; font-size: 0.85em; font-weight: 600;">${itemIdx + 1}</span>
                                        </div>
                                        <div style="flex: 1;">
                                            <div style="color: #cbd5e1; font-size: 0.9em; font-weight: 600; margin-bottom: 8px;">${itemName}</div>
                                            <div style="color: #94a3b8; font-size: 0.85em; margin-bottom: 4px;">
                                                จำนวน: <span style="color: #cbd5e1;">${typeof quantity === 'number' ? quantity.toLocaleString('th-TH', {minimumFractionDigits: 2, maximumFractionDigits: 2}) : quantity}</span> 
                                                ราคา: <span style="color: #cbd5e1;">${typeof price === 'number' ? price.toLocaleString('th-TH', {minimumFractionDigits: 2, maximumFractionDigits: 2}) : price}</span>
                                            </div>
                                            <div style="color: #10b981; font-size: 0.9em; font-weight: 600;">
                                                ยอดรวม: ${typeof subtotal === 'number' ? subtotal.toLocaleString('th-TH', {minimumFractionDigits: 2, maximumFractionDigits: 2}) : subtotal} บาท
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            `;
                        });
                        
                        ocrResultsHtml += `</div></div>`;
                    }
                    
                    ocrResultsHtml += `</div>`;
                });
                
                    ocrResultsHtml += `</div></div>`;
                } else {
                    // แสดงข้อความแจ้งเตือนถ้ายังไม่มีข้อมูล
                    ocrResultsHtml = `
                        <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #334155;">
                            <div style="padding: 12px; background: #1e293b; border-radius: 8px; border: 1px solid #475569; text-align: center;">
                                <div style="color: #94a3b8; font-size: 0.9em;">
                                    <span style="font-size: 1.2em; margin-right: 8px;">ℹ️</span>
                                    ข้อมูลที่อ่านได้จะแสดงที่นี่ (รายการนี้ประมวลผลก่อนการอัปเดตระบบ)
                                </div>
                            </div>
                        </div>
                    `;
                }
            }
            
            return `
                <div style="background: ${statusInfo.bg}; border-left: 4px solid ${statusInfo.border}; padding: 20px; border-radius: 10px; margin-bottom: 15px;">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 15px;">
                        <div style="flex: 1;">
                            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                                <span style="font-weight: 600; color: ${statusInfo.border};">${statusInfo.text}</span>
                                <span style="color: #94a3b8; font-size: 0.85em;">ID: ${queue.queue_id}</span>
                            </div>
                            <div style="color: #cbd5e1; font-size: 0.9em; word-break: break-all; margin-bottom: 10px;">
                                📁 ${queue.path}
                            </div>
                        </div>
                        ${status === 'processing' || status === 'pending' ? `
                            <button onclick="cancelOCRQueue('${queue.queue_id}')" style="padding: 8px 16px; background: #ef4444; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.85em; font-weight: 600; transition: all 0.3s;" onmouseover="this.style.background='#dc2626';" onmouseout="this.style.background='#ef4444';">ยกเลิก</button>
                        ` : ''}
                    </div>
                    
                    ${status === 'processing' || status === 'pending' ? `
                        <div style="margin-bottom: 10px;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                <span style="color: #cbd5e1; font-size: 0.9em;">ความคืบหน้า</span>
                                <span style="color: #cbd5e1; font-size: 0.9em; font-weight: 600;">${completed}/${total} ไฟล์ (${progress.toFixed(1)}%)</span>
                            </div>
                            <div style="background: #0f172a; height: 12px; border-radius: 6px; overflow: hidden;">
                                <div style="background: linear-gradient(90deg, ${statusInfo.border} 0%, ${statusInfo.border}dd 100%); height: 100%; width: ${progress}%; transition: width 0.3s;"></div>
                            </div>
                        </div>
                        ${estimatedTime > 0 ? `
                            <div style="color: #94a3b8; font-size: 0.85em; margin-top: 8px;">
                                ⏱️ เวลาที่คาดว่าจะใช้: ${formatEstimatedTime(estimatedTime)}
                            </div>
                        ` : ''}
                        ${queue.current_file ? `
                            <div style="color: #60a5fa; font-size: 0.85em; margin-top: 8px;">
                                📄 กำลังอ่าน: ${queue.current_file}
                            </div>
                        ` : ''}
                    ` : ''}
                    
                    ${status === 'completed' ? `
                        <div style="color: #10b981; font-size: 0.9em; margin-top: 10px;">
                            ✅ ประมวลผลเสร็จสิ้น: ${completed} ไฟล์
                        </div>
                        ${autoRemoveInfo}
                        ${ocrResultsHtml}
                        <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #334155;">
                            <button onclick="checkUnreadFiles('${queue.queue_id}', '${escapeHtml(queue.path)}')" style="width: 100%; padding: 12px; background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: #ffffff; border: 1px solid #f59e0b; border-radius: 8px; cursor: pointer; font-size: 0.95em; font-weight: 600; display: flex; align-items: center; justify-content: center; gap: 8px; transition: all 0.3s; box-shadow: 0 2px 4px rgba(245, 158, 11, 0.3);" onmouseover="this.style.background='linear-gradient(135deg, #d97706 0%, #b45309 100%)'; this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 8px rgba(245, 158, 11, 0.4)';" onmouseout="this.style.background='linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'; this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 4px rgba(245, 158, 11, 0.3)';">
                                <span style="font-size: 1.1em;">🔍</span>
                                <span>รีเช็คไฟล์ที่ยังไม่ได้อ่าน</span>
                            </button>
                            <div id="unreadFiles-${queue.queue_id}" style="display: none; margin-top: 10px;"></div>
                        </div>
                    ` : ''}
                    
                    ${status === 'failed' ? `
                        <div style="color: #ef4444; font-size: 0.9em; margin-top: 10px;">
                            ❌ ${queue.error || 'เกิดข้อผิดพลาด'}
                        </div>
                    ` : ''}
                    
                    <div style="color: #64748b; font-size: 0.8em; margin-top: 10px;">
                        🕐 สร้างเมื่อ: ${formatDateTime(queue.created_at)}
                    </div>
                </div>
            `;
        }
        
        // ฟังก์ชันสำหรับยกเลิกคิว
        async function cancelOCRQueue(queueId) {
            if (!confirm('ต้องการยกเลิกคิวนี้หรือไม่?')) {
                return;
            }
            
            try {
                const response = await fetch(`/api/auditcheck/ocr-queue/cancel/${queueId}`, {
                    method: 'POST'
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showToast('success', '✅ ยกเลิกคิวสำเร็จ');
                    loadOCRQueue();
                } else {
                    alert('เกิดข้อผิดพลาด: ' + (data.error || 'ไม่ทราบสาเหตุ'));
                }
            } catch (error) {
                console.error('Error canceling OCR queue:', error);
                alert('เกิดข้อผิดพลาดในการยกเลิกคิว: ' + error.message);
            }
        }
        
        // ฟังก์ชันสำหรับ format เวลาที่คาดว่าจะใช้
        function formatEstimatedTime(seconds) {
            if (seconds < 60) {
                return `${Math.ceil(seconds)} วินาที`;
            } else if (seconds < 3600) {
                const minutes = Math.floor(seconds / 60);
                const secs = Math.ceil(seconds % 60);
                return `${minutes} นาที ${secs > 0 ? secs + ' วินาที' : ''}`;
            } else {
                const hours = Math.floor(seconds / 3600);
                const minutes = Math.floor((seconds % 3600) / 60);
                return `${hours} ชั่วโมง ${minutes} นาที`;
            }
        }
        
        // ฟังก์ชันรีเช็คไฟล์ที่ยังไม่ได้อ่าน
        async function checkUnreadFiles(queueId, folderPath) {
            const unreadFilesDiv = document.getElementById(`unreadFiles-${queueId}`);
            unreadFilesDiv.style.display = 'block';
            unreadFilesDiv.innerHTML = '<div style="padding: 15px; text-align: center; color: #94a3b8;">⏳ กำลังตรวจสอบไฟล์ที่ยังไม่ได้อ่าน...</div>';
            
            try {
                const response = await fetch('/api/auditcheck/ocr-queue/check-unread', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        folder_path: folderPath
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    const unreadFiles = data.unread_files || [];
                    const allFiles = data.all_files || [];
                    const readFiles = data.read_files || [];
                    
                    let html = '';
                    
                    if (unreadFiles.length === 0) {
                        html = `
                            <div style="padding: 15px; background: #10b98115; border-radius: 8px; border: 1px solid #10b981; text-align: center;">
                                <div style="color: #10b981; font-size: 1em; font-weight: 600; margin-bottom: 5px;">
                                    ✅ ครบทุกไฟล์แล้ว
                                </div>
                                <div style="color: #94a3b8; font-size: 0.85em;">
                                    อ่านครบทั้งหมด ${allFiles.length} ไฟล์
                                </div>
                            </div>
                        `;
                    } else {
                        html = `
                            <div style="padding: 15px; background: #f59e0b15; border-radius: 8px; border: 1px solid #f59e0b; margin-bottom: 15px;">
                                <div style="color: #f59e0b; font-size: 1em; font-weight: 600; margin-bottom: 10px;">
                                    ⚠️ พบไฟล์ที่ยังไม่ได้อ่าน: ${unreadFiles.length} ไฟล์
                                </div>
                                <div style="color: #94a3b8; font-size: 0.85em; margin-bottom: 10px;">
                                    อ่านแล้ว: ${readFiles.length} ไฟล์ | ทั้งหมด: ${allFiles.length} ไฟล์
                                </div>
                                <div style="max-height: 300px; overflow-y: auto; background: #0f172a; border-radius: 6px; padding: 10px; margin-top: 10px;">
                                    <div style="color: #cbd5e1; font-size: 0.9em; font-weight: 600; margin-bottom: 8px;">รายชื่อไฟล์ที่ยังไม่ได้อ่าน:</div>
                        `;
                        
                        unreadFiles.forEach((filename, idx) => {
                            html += `
                                <div style="padding: 8px; margin-bottom: 5px; background: #1e293b; border-radius: 4px; border-left: 3px solid #f59e0b; color: #cbd5e1; font-size: 0.85em;">
                                    ${idx + 1}. ${escapeHtml(filename)}
                                </div>
                            `;
                        });
                        
                        html += `
                                </div>
                                <button onclick="rerunOCRForUnreadFiles('${queueId}', '${escapeHtml(folderPath)}')" style="width: 100%; margin-top: 15px; padding: 12px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: #ffffff; border: 1px solid #10b981; border-radius: 8px; cursor: pointer; font-size: 0.95em; font-weight: 600; display: flex; align-items: center; justify-content: center; gap: 8px; transition: all 0.3s; box-shadow: 0 2px 4px rgba(16, 185, 129, 0.3);" onmouseover="this.style.background='linear-gradient(135deg, #059669 0%, #047857 100%)'; this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 8px rgba(16, 185, 129, 0.4)';" onmouseout="this.style.background='linear-gradient(135deg, #10b981 0%, #059669 100%)'; this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 4px rgba(16, 185, 129, 0.3)';">
                                    <span style="font-size: 1.1em;">🔄</span>
                                    <span>อ่านใหม่รอบที่ 2 (${unreadFiles.length} ไฟล์)</span>
                                </button>
                            </div>
                        `;
                    }
                    
                    unreadFilesDiv.innerHTML = html;
                } else {
                    unreadFilesDiv.innerHTML = `
                        <div style="padding: 15px; background: #ef444415; border-radius: 8px; border: 1px solid #ef4444; text-align: center;">
                            <div style="color: #ef4444; font-size: 0.9em;">
                                ❌ ${data.error || 'เกิดข้อผิดพลาดในการตรวจสอบ'}
                            </div>
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Error checking unread files:', error);
                unreadFilesDiv.innerHTML = `
                    <div style="padding: 15px; background: #ef444415; border-radius: 8px; border: 1px solid #ef4444; text-align: center;">
                        <div style="color: #ef4444; font-size: 0.9em;">
                            ❌ เกิดข้อผิดพลาด: ${error.message}
                        </div>
                    </div>
                `;
            }
        }
        
        // ฟังก์ชันอ่านใหม่รอบที่ 2 สำหรับไฟล์ที่ยังไม่ได้อ่าน
        async function rerunOCRForUnreadFiles(queueId, folderPath) {
            if (!confirm(`ต้องการอ่านไฟล์ที่ยังไม่ได้อ่านใหม่หรือไม่?`)) {
                return;
            }
            
            try {
                const response = await fetch('/api/auditcheck/ocr-queue/rerun-unread', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        folder_path: folderPath,
                        original_queue_id: queueId
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showToast('success', `✅ เริ่มอ่านไฟล์ที่ยังไม่ได้อ่านแล้ว (${data.unread_count || 0} ไฟล์)`);
                    // รีโหลดรายการคิว
                    setTimeout(() => {
                        loadOCRQueue();
                    }, 1000);
                } else {
                    alert('เกิดข้อผิดพลาด: ' + (data.error || 'ไม่ทราบสาเหตุ'));
                }
            } catch (error) {
                console.error('Error rerunning OCR for unread files:', error);
                alert('เกิดข้อผิดพลาดในการอ่านใหม่: ' + error.message);
            }
        }
        
        // ฟังก์ชันสำหรับดึงชื่อบริษัทจาก path
        function extractCompanyNameFromPath(path) {
            if (!path) return 'ไม่ระบุ';
            
            // แปลง path เป็น array ของส่วนต่างๆ
            const pathParts = path.split(/[/\\]/).filter(p => p.trim() !== '');
            
            // หา "Build" หรือชื่อบริษัท (มักจะอยู่หลัง "A.โฟร์เดอร์หลัก" หรือ "AA.โฟรเดอร์หลัก" หรือ "AAA.โฟรเดอร์หลัก")
            for (let i = 0; i < pathParts.length; i++) {
                const part = pathParts[i];
                
                // ถ้าเจอ Build ให้ใช้ส่วนนั้น (เช่น "Build000 ทดสอบระบบ")
                if (part && part.includes('Build')) {
                    return part;
                }
                
                // ถ้าเจอส่วนที่อยู่หลัง "โฟร์เดอร์หลัก" หรือ "โฟรเดอร์หลัก" และไม่ใช่ส่วนสุดท้าย
                if (i > 0 && (pathParts[i-1].includes('โฟร์เดอร์หลัก') || pathParts[i-1].includes('โฟรเดอร์หลัก'))) {
                    if (part && part.trim() !== '' && !part.includes('โฟร์เดอร์') && !part.includes('โฟรเดอร์')) {
                        return part;
                    }
                }
            }
            
            // ถ้าหาไม่เจอ ให้ใช้ส่วนที่ 2 หรือ 3 (มักจะเป็นชื่อบริษัท)
            if (pathParts.length >= 2) {
                return pathParts[1] || 'ไม่ระบุ';
            }
            
            // ถ้ายังหาไม่เจอ ให้ใช้ส่วนสุดท้ายของ path
            const lastPart = pathParts[pathParts.length - 1];
            return lastPart || 'ไม่ระบุ';
        }
        
        // ฟังก์ชันสำหรับแสดง/ซ่อนข้อมูลที่ OCR อ่านได้
        function toggleOCRResults(queueId) {
            const resultsDiv = document.getElementById(`ocrResults-${queueId}`);
            const iconSpan = document.getElementById(`ocrResultsIcon-${queueId}`);
            
            if (resultsDiv.style.display === 'none') {
                resultsDiv.style.display = 'block';
                iconSpan.textContent = '▲';
            } else {
                resultsDiv.style.display = 'none';
                iconSpan.textContent = '▼';
            }
        }
        
        // ฟังก์ชันสำหรับ format วันที่เวลา
        function formatDateTime(dateString) {
            if (!dateString) return '-';
            const date = new Date(dateString);
            return date.toLocaleString('th-TH', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        }
        
        // ฟังก์ชันสำหรับเริ่ม polling
        function startOCRQueuePolling() {
            if (ocrQueuePollingInterval) {
                return; // กำลัง polling อยู่แล้ว
            }
            
            ocrQueuePollingInterval = setInterval(() => {
                loadOCRQueue();
            }, 30000); // อัพเดททุก 30 วินาที (30000ms)
        }
        
        // ฟังก์ชันสำหรับหยุด polling
        function stopOCRQueuePolling() {
            if (ocrQueuePollingInterval) {
                clearInterval(ocrQueuePollingInterval);
                ocrQueuePollingInterval = null;
            }
        }
        
        let allCompanies = [];
        let selectedCompanyIndex = -1;
        
        async function loadCompanies() {
            try {
                const response = await fetch('/api/auditcheck/companies');
                const data = await response.json();
                
                if (data.success) {
                    allCompanies = data.companies;
                    setupAutocomplete();
                } else {
                    showAlert('error', 'ไม่สามารถโหลดรายชื่อบริษัทได้: ' + data.error);
                }
            } catch (error) {
                console.error('Error loading companies:', error);
                showAlert('error', 'เกิดข้อผิดพลาดในการโหลดรายชื่อบริษัท');
            }
        }
        
        function setupAutocomplete() {
            const input = document.getElementById('companySelect');
            const dropdown = document.getElementById('companyDropdown');
            const clearBtn = document.getElementById('clearCompany');
            
            function showDropdown(searchTerm = '') {
                selectedCompanyIndex = -1;
                
                if (searchTerm === '') {
                    // แสดงรายการทั้งหมด
                    dropdown.innerHTML = '';
                    allCompanies.forEach((company, index) => {
                        const item = document.createElement('div');
                        item.className = 'autocomplete-item';
                        item.textContent = company;
                        item.addEventListener('click', function() {
                            selectCompany(company);
                        });
                        dropdown.appendChild(item);
                    });
                } else {
                    // กรองบริษัทที่ตรงกับคำค้นหา
                    const filtered = allCompanies.filter(company => 
                        company.toLowerCase().includes(searchTerm.toLowerCase())
                    );
                    
                    if (filtered.length === 0) {
                        dropdown.innerHTML = '<div class="autocomplete-item">ไม่พบบริษัทที่ตรงกับคำค้นหา</div>';
                    } else {
                        dropdown.innerHTML = '';
                        filtered.forEach((company, index) => {
                            const item = document.createElement('div');
                            item.className = 'autocomplete-item';
                            item.textContent = company;
                            item.addEventListener('click', function() {
                                selectCompany(company);
                            });
                            dropdown.appendChild(item);
                        });
                    }
                }
                
                dropdown.classList.add('show');
            }
            
            // แสดง dropdown เมื่อคลิกที่ input
            input.addEventListener('click', function(e) {
                if (dropdown.classList.contains('show')) {
                    dropdown.classList.remove('show');
                } else {
                    showDropdown(input.value);
                }
            });
            
            // แสดง dropdown เมื่อ focus
            input.addEventListener('focus', function(e) {
                showDropdown(input.value);
            });
            
            input.addEventListener('input', function(e) {
                const searchTerm = e.target.value;
                selectedCompanyIndex = -1;
                
                if (searchTerm === '') {
                    clearBtn.style.display = 'none';
                    document.getElementById('companyValue').value = '';
                } else {
                    clearBtn.style.display = 'block';
                }
                
                showDropdown(searchTerm);
            });
            
            input.addEventListener('keydown', function(e) {
                const items = dropdown.querySelectorAll('.autocomplete-item');
                
                if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    selectedCompanyIndex = Math.min(selectedCompanyIndex + 1, items.length - 1);
                    updateSelection(items);
                } else if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    selectedCompanyIndex = Math.max(selectedCompanyIndex - 1, -1);
                    updateSelection(items);
                } else if (e.key === 'Enter') {
                    e.preventDefault();
                    if (selectedCompanyIndex >= 0 && items[selectedCompanyIndex]) {
                        selectCompany(items[selectedCompanyIndex].textContent);
                    }
                } else if (e.key === 'Escape') {
                    dropdown.classList.remove('show');
                }
            });
            
            // ปิด dropdown เมื่อคลิกนอก (แต่ไม่ปิดเมื่อคลิกที่ input หรือ clear button)
            document.addEventListener('click', function(e) {
                if (!input.contains(e.target) && !dropdown.contains(e.target) && !clearBtn.contains(e.target)) {
                    dropdown.classList.remove('show');
                }
            });
            
            // ป้องกันการปิด dropdown เมื่อคลิกที่ clear button
            clearBtn.addEventListener('click', function(e) {
                e.stopPropagation();
            });
        }
        
        function updateSelection(items) {
            items.forEach((item, index) => {
                if (index === selectedCompanyIndex) {
                    item.classList.add('selected');
                    item.scrollIntoView({ block: 'nearest' });
                } else {
                    item.classList.remove('selected');
                }
            });
        }
        
        // ตัวแปรเก็บข้อมูลสาขาที่เลือก
        let selectedBranch = null;
        let selectedCompanyForBranch = null;
        let baseCompanyName = null; // เก็บชื่อบริษัทหลัก (ไม่รวมสาขา) สำหรับบริษัทพิเศษ
        
        async function selectCompany(company) {
            const input = document.getElementById('companySelect');
            const dropdown = document.getElementById('companyDropdown');
            const clearBtn = document.getElementById('clearCompany');
            
            dropdown.classList.remove('show');
            selectedCompanyIndex = -1;
            
            // ตรวจสอบว่าเป็นบริษัทพิเศษที่ต้องเลือกสาขาหรือไม่
            const specialCompany = "Build214 บริษัท เอส.ยู. คอมพาเนียน จำกัด รายเดือน";
            if (company === specialCompany) {
                // แสดง modal เลือกสาขา
                selectedCompanyForBranch = company;
                await showBranchSelectionModal(company);
                return;
            }
            
            // สำหรับบริษัทปกติ ให้ทำงานตามเดิม
            input.value = company;
            document.getElementById('companyValue').value = company;
            clearBtn.style.display = 'block';
            selectedBranch = null; // รีเซ็ตสาขา
            baseCompanyName = null; // รีเซ็ตชื่อบริษัทหลัก
            
            // ซ่อนส่วนข้อมูลภายในสาขา (สำหรับบริษัทปกติ)
            const branchInfoSection = document.getElementById('branchInfoSection');
            if (branchInfoSection) {
                branchInfoSection.style.display = 'none';
            }
            
            // แสดงส่วนข้อมูลบริษัท
            document.getElementById('companyInfoGroup').style.display = 'block';
            
            // โหลดข้อมูลบริษัทที่บันทึกไว้
            loadCompanyInfo(company);
        }
        
        // แสดง modal เลือกสาขา
        async function showBranchSelectionModal(company) {
            const modal = document.getElementById('branchSelectionModal');
            const loadingDiv = document.getElementById('branchLoading');
            const branchListDiv = document.getElementById('branchList');
            const errorDiv = document.getElementById('branchError');
            const companyNameDiv = document.getElementById('branchModalCompanyName');
            
            // แสดง modal
            modal.style.display = 'flex';
            companyNameDiv.textContent = company;
            
            // ซ่อนส่วนอื่นๆ และแสดง loading
            loadingDiv.style.display = 'block';
            branchListDiv.style.display = 'none';
            errorDiv.style.display = 'none';
            
            try {
                // เรียก API เพื่อดึงรายการสาขา
                const response = await fetch(`/api/auditcheck/company-branches?company=${encodeURIComponent(company)}`);
                const data = await response.json();
                
                if (!data.success) {
                    throw new Error(data.error || 'ไม่สามารถโหลดรายการสาขาได้');
                }
                
                const branches = data.branches || [];
                
                if (branches.length === 0) {
                    throw new Error('ไม่พบสาขาในบริษัทนี้');
                }
                
                // สร้างรายการสาขา
                branchListDiv.innerHTML = '';
                branches.forEach((branch, index) => {
                    const branchItem = document.createElement('div');
                    branchItem.style.cssText = `
                        padding: 16px 20px;
                        margin-bottom: 12px;
                        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
                        border: 2px solid #334155;
                        border-radius: 12px;
                        cursor: pointer;
                        transition: all 0.3s ease;
                        display: flex;
                        align-items: center;
                        gap: 16px;
                    `;
                    branchItem.onmouseover = function() {
                        this.style.borderColor = '#10b981';
                        this.style.background = 'linear-gradient(135deg, #1e293b 0%, #1e293b 100%)';
                        this.style.transform = 'translateX(4px)';
                        this.style.boxShadow = '0 4px 12px rgba(16, 185, 129, 0.2)';
                    };
                    branchItem.onmouseout = function() {
                        this.style.borderColor = '#334155';
                        this.style.background = 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)';
                        this.style.transform = 'translateX(0)';
                        this.style.boxShadow = 'none';
                    };
                    branchItem.onclick = function() {
                        selectBranch(branch, company);
                    };
                    
                    branchItem.innerHTML = `
                        <div style="width: 48px; height: 48px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 24px; flex-shrink: 0;">
                            📁
                        </div>
                        <div style="flex: 1;">
                            <div style="color: #fafafa; font-size: 1.1em; font-weight: 600; margin-bottom: 4px;">${escapeHtml(branch.name)}</div>
                            <div style="color: #94a3b8; font-size: 0.85em; word-break: break-all;">${escapeHtml(branch.path)}</div>
                        </div>
                        <div style="color: #10b981; font-size: 1.5em;">→</div>
                    `;
                    
                    branchListDiv.appendChild(branchItem);
                });
                
                // แสดงรายการสาขา
                loadingDiv.style.display = 'none';
                branchListDiv.style.display = 'block';
                
            } catch (error) {
                console.error('Error loading branches:', error);
                loadingDiv.style.display = 'none';
                errorDiv.style.display = 'block';
                document.getElementById('branchErrorMessage').textContent = error.message || 'เกิดข้อผิดพลาดในการโหลดรายการสาขา';
            }
        }
        
        // เลือกสาขา
        function selectBranch(branch, company) {
            selectedBranch = branch;
            baseCompanyName = company; // เก็บชื่อบริษัทหลักไว้สำหรับใช้ใน modal
            
            // อัปเดต company value ให้รวมสาขา (ใช้ path ของสาขา)
            // แต่เก็บชื่อบริษัทเดิมไว้ใน companySelect
            const input = document.getElementById('companySelect');
            const companyValue = branch.path; // ใช้ path ของสาขาเป็น company value
            
            input.value = `${company} - ${branch.name}`;
            document.getElementById('companyValue').value = companyValue;
            
            // ปิด modal
            closeBranchSelectionModal();
            
            // แสดงปุ่ม clear
            document.getElementById('clearCompany').style.display = 'block';
            
            // แสดงส่วนข้อมูลบริษัท
            document.getElementById('companyInfoGroup').style.display = 'block';
            
            // แสดงส่วนข้อมูลภายในสาขา
            const branchInfoSection = document.getElementById('branchInfoSection');
            const branchInfoTitle = document.getElementById('branchInfoTitle');
            const branchInfoPath = document.getElementById('branchInfoPath');
            if (branchInfoSection && branchInfoTitle && branchInfoPath) {
                branchInfoSection.style.display = 'block';
                branchInfoTitle.textContent = `ข้อมูลภายในสาขา: ${branch.name}`;
                branchInfoPath.textContent = branch.path;
            }
            
            // โหลดข้อมูลบริษัท (ใช้ชื่อบริษัทเดิม)
            loadCompanyInfo(company);
            
            // โหลดข้อมูลภายในสาขา
            loadBranchInfo();
            
            // เริ่มทำงานตามระบบที่ตั้งไว้ทันที (สำหรับบริษัทพิเศษที่มีสาขา)
            // ตรวจสอบว่ามีเดือนภาษีและปีภาษีเลือกไว้แล้วหรือไม่
            const taxMonth = document.getElementById('taxMonth')?.value;
            const taxYear = document.getElementById('taxYear')?.value;
            
            if (taxMonth && taxYear) {
                // ถ้ามีเดือนและปีภาษีแล้ว ให้เริ่มทำงานทันที
                setTimeout(() => {
                    startAudit();
                }, 500); // รอสักครู่เพื่อให้ UI อัปเดตเสร็จก่อน
            } else {
                // ถ้ายังไม่มีเดือนและปีภาษี ให้แสดงข้อความแจ้งเตือน
                showAlert('info', 'กรุณาเลือกเดือนและปีภาษีก่อนเริ่มตรวจสอบ');
            }
        }
        
        // โหลดข้อมูลภายในสาขา
        async function loadBranchInfo() {
            if (!selectedBranch) {
                return;
            }
            
            const branchInfoContent = document.getElementById('branchInfoContent');
            if (!branchInfoContent) {
                return;
            }
            
            branchInfoContent.innerHTML = '<div style="padding: 20px; text-align: center; color: #94a3b8;"><div style="font-size: 1.2em; margin-bottom: 10px;">⏳</div><div>กำลังโหลดข้อมูล...</div></div>';
            
            try {
                const response = await fetch('/api/auditcheck/branch-info', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        branch_path: selectedBranch.path
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    let html = '';
                    
                    // แสดงโครงสร้างโฟลเดอร์
                    if (data.folders && data.folders.length > 0) {
                        html += '<div style="margin-bottom: 20px;">';
                        html += '<div style="color: #60a5fa; font-size: 1em; font-weight: 600; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">';
                        html += '<span>📁</span>';
                        html += `<span>โฟลเดอร์ย่อย (${data.folders.length})</span>`;
                        html += '</div>';
                        html += '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 10px;">';
                        
                        data.folders.forEach((folder, idx) => {
                            html += `
                                <div style="padding: 12px; background: #0f172a; border-radius: 8px; border: 1px solid #334155; transition: all 0.3s;" onmouseover="this.style.borderColor='#3b82f6'; this.style.background='#1e293b';" onmouseout="this.style.borderColor='#334155'; this.style.background='#0f172a';">
                                    <div style="color: #cbd5e1; font-size: 0.9em; font-weight: 600; margin-bottom: 5px; word-break: break-word;">📁 ${escapeHtml(folder.name)}</div>
                                    <div style="color: #94a3b8; font-size: 0.8em; word-break: break-all;">${escapeHtml(folder.path)}</div>
                                </div>
                            `;
                        });
                        
                        html += '</div>';
                        html += '</div>';
                    }
                    
                    // แสดงไฟล์ PDF
                    if (data.pdf_files && data.pdf_files.length > 0) {
                        html += '<div style="margin-bottom: 20px;">';
                        html += '<div style="color: #10b981; font-size: 1em; font-weight: 600; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">';
                        html += '<span>📄</span>';
                        html += `<span>ไฟล์ PDF (${data.pdf_files.length})</span>`;
                        html += '</div>';
                        html += '<div style="max-height: 400px; overflow-y: auto; background: #0f172a; border-radius: 8px; padding: 10px;">';
                        
                        data.pdf_files.forEach((file, idx) => {
                            const fileSizeKB = (file.size / 1024).toFixed(2);
                            const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2);
                            const sizeDisplay = file.size > 1024 * 1024 ? `${fileSizeMB} MB` : `${fileSizeKB} KB`;
                            
                            html += `
                                <div style="padding: 10px; margin-bottom: 8px; background: #1e293b; border-radius: 6px; border-left: 3px solid #10b981; display: flex; align-items: center; justify-content: space-between;">
                                    <div style="flex: 1; min-width: 0;">
                                        <div style="color: #cbd5e1; font-size: 0.9em; font-weight: 600; margin-bottom: 4px; word-break: break-word;">📄 ${escapeHtml(file.name)}</div>
                                        <div style="color: #94a3b8; font-size: 0.8em; word-break: break-all;">${escapeHtml(file.path)}</div>
                                    </div>
                                    <div style="color: #94a3b8; font-size: 0.85em; margin-left: 10px; flex-shrink: 0;">${sizeDisplay}</div>
                                </div>
                            `;
                        });
                        
                        html += '</div>';
                        html += '</div>';
                    }
                    
                    if (!data.folders || data.folders.length === 0) {
                        if (!data.pdf_files || data.pdf_files.length === 0) {
                            html = '<div style="padding: 20px; text-align: center; color: #94a3b8;"><div style="font-size: 1.2em; margin-bottom: 10px;">📭</div><div>ไม่พบโฟลเดอร์หรือไฟล์ในสาขานี้</div></div>';
                        }
                    }
                    
                    branchInfoContent.innerHTML = html;
                } else {
                    branchInfoContent.innerHTML = `
                        <div style="padding: 20px; background: #ef444415; border-radius: 8px; border: 1px solid #ef4444; text-align: center;">
                            <div style="color: #ef4444; font-size: 0.9em;">
                                ❌ ${data.error || 'เกิดข้อผิดพลาดในการโหลดข้อมูล'}
                            </div>
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Error loading branch info:', error);
                branchInfoContent.innerHTML = `
                    <div style="padding: 20px; background: #ef444415; border-radius: 8px; border: 1px solid #ef4444; text-align: center;">
                        <div style="color: #ef4444; font-size: 0.9em;">
                            ❌ เกิดข้อผิดพลาด: ${error.message}
                        </div>
                    </div>
                `;
            }
        }
        
        // ปิด modal เลือกสาขา
        function closeBranchSelectionModal() {
            const modal = document.getElementById('branchSelectionModal');
            modal.style.display = 'none';
            
            // ถ้ายังไม่ได้เลือกสาขา ให้รีเซ็ต
            if (!selectedBranch && selectedCompanyForBranch) {
                const input = document.getElementById('companySelect');
                input.value = '';
                document.getElementById('companyValue').value = '';
                document.getElementById('clearCompany').style.display = 'none';
                document.getElementById('companyInfoGroup').style.display = 'none';
            }
            
            selectedCompanyForBranch = null;
        }
        
        function clearCompany() {
            const input = document.getElementById('companySelect');
            const dropdown = document.getElementById('companyDropdown');
            const clearBtn = document.getElementById('clearCompany');
            
            input.value = '';
            document.getElementById('companyValue').value = '';
            dropdown.classList.remove('show');
            clearBtn.style.display = 'none';
            selectedCompanyIndex = -1;
            selectedBranch = null; // รีเซ็ตสาขา
            selectedCompanyForBranch = null;
            baseCompanyName = null; // รีเซ็ตชื่อบริษัทหลัก
            
            // ซ่อนส่วนข้อมูลบริษัทเมื่อล้างบริษัท
            document.getElementById('companyInfoGroup').style.display = 'none';
            
            // ซ่อนส่วนข้อมูลภายในสาขา
            const branchInfoSection = document.getElementById('branchInfoSection');
            if (branchInfoSection) {
                branchInfoSection.style.display = 'none';
            }
        }
        
        // ฟังก์ชันแปลงวันที่จาก YYYY-MM-DD เป็น dd/mm/yyyy
        function formatDate(dateString) {
            if (!dateString || dateString === '-') {
                return '-';
            }
            
            try {
                // แปลงจาก YYYY-MM-DD เป็น Date object
                const date = new Date(dateString + 'T00:00:00');
                
                // ตรวจสอบว่า date ถูกต้องหรือไม่
                if (isNaN(date.getTime())) {
                    return dateString; // ถ้าแปลงไม่ได้ให้คืนค่าเดิม
                }
                
                // แปลงเป็น dd/mm/yyyy
                const day = String(date.getDate()).padStart(2, '0');
                const month = String(date.getMonth() + 1).padStart(2, '0');
                const year = date.getFullYear();
                
                return `${day}/${month}/${year}`;
            } catch (error) {
                console.error('Error formatting date:', error);
                return dateString; // ถ้าเกิดข้อผิดพลาดให้คืนค่าเดิม
            }
        }
        
        // ฟังก์ชันตัดคำหลัง "จำกัด" ออก
        function removeTextAfterLimited(companyName) {
            if (!companyName || companyName === '-') {
                return companyName;
            }
            
            // หาตำแหน่งของคำว่า "จำกัด"
            const limitedIndex = companyName.indexOf('จำกัด');
            
            if (limitedIndex !== -1) {
                // ตัดคำหลัง "จำกัด" ออก (รวมช่องว่างที่ตามมาด้วย)
                return companyName.substring(0, limitedIndex + 'จำกัด'.length).trim();
            }
            
            return companyName;
        }
        
        // โหลดข้อมูลบริษัทที่บันทึกไว้
        async function loadCompanyInfo(company) {
            if (!company) {
                document.getElementById('companyInfoGroup').style.display = 'none';
                return;
            }
            
            try {
                // แยก Build และชื่อบริษัทจาก company string (รูปแบบ: "Build001 ชื่อบริษัท")
                const parts = company.split(' ');
                const build = parts[0]; // Build001
                const companyName = parts.slice(1).join(' '); // ส่วนที่เหลือ
                
                // ตั้งค่า Build และชื่อบริษัทใน UI
                document.getElementById('companyBuild').textContent = build;
                document.getElementById('companyName').textContent = removeTextAfterLimited(companyName || company);
                
                // โหลดข้อมูลบริษัทจาก API (ส่ง customer parameter ด้วย)
                const customer = companyName || company;
                const apiUrl = `/api/auditcheck/company?build=${encodeURIComponent(build)}&company_name=${encodeURIComponent(companyName || company)}&customer=${encodeURIComponent(customer)}`;
                console.log('🔍 เรียก API:', apiUrl);
                console.log('📋 พารามิเตอร์:', { build, companyName, customer });
                
                const response = await fetch(apiUrl);
                const data = await response.json();
                console.log('📦 Response จาก API:', data);
                
                if (data.success && data.company) {
                    // แสดงข้อมูลบริษัท
                    const comp = data.company;
                    console.log('✅ พบข้อมูลบริษัท:', comp);
                    document.getElementById('companyBuild').textContent = comp.build || build;
                    document.getElementById('companyName').textContent = removeTextAfterLimited(comp.company_name || companyName || company);
                    document.getElementById('companyTaxId').textContent = comp.tax_id || '-';
                    document.getElementById('companyAddress').textContent = comp.company_address || '-';
                    document.getElementById('companyVatStatus').textContent = comp.vat_status || '-';
                    document.getElementById('companyVatDate').textContent = formatDate(comp.vat_registration_date);
                    
                    // ซ่อนข้อความ "ยังไม่มีข้อมูล"
                    document.getElementById('noCompanyData').style.display = 'none';
                } else {
                    // ไม่พบข้อมูล - แสดงข้อความให้เพิ่มข้อมูล
                    console.warn('⚠️ ไม่พบข้อมูลบริษัท:', data);
                    document.getElementById('companyTaxId').textContent = '-';
                    document.getElementById('companyAddress').textContent = '-';
                    document.getElementById('companyVatStatus').textContent = '-';
                    document.getElementById('companyVatDate').textContent = '-';
                    document.getElementById('noCompanyData').style.display = 'block';
                }
            } catch (error) {
                console.error('Error loading company info:', error);
                // แสดงข้อความให้เพิ่มข้อมูล
                document.getElementById('companyTaxId').textContent = '-';
                document.getElementById('companyAddress').textContent = '-';
                document.getElementById('companyVatStatus').textContent = '-';
                document.getElementById('companyVatDate').textContent = '-';
                document.getElementById('noCompanyData').style.display = 'block';
            }
        }
        
        // ===== ฟังก์ชันจัดการข้อมูลบริษัท =====
        let editingDbConfigId = null;
        
        // ตรวจสอบเลขประจำตัวผู้เสียภาษี 13 หลัก
        function validateTaxId(input) {
            const taxId = input.value.trim();
            const errorDiv = document.getElementById('taxIdError');
            
            if (taxId === '') {
                errorDiv.style.display = 'none';
                input.style.borderColor = '#334155';
                return true;
            }
            
            if (taxId.length !== 13) {
                errorDiv.textContent = 'กรุณากรอกเลขประจำตัวผู้เสียภาษีให้ครบ 13 หลัก';
                errorDiv.style.display = 'block';
                input.style.borderColor = '#ef4444';
                return false;
            }
            
            // ตรวจสอบว่าเป็นตัวเลขทั้งหมด
            if (!/^\d{13}$/.test(taxId)) {
                errorDiv.textContent = 'กรุณากรอกเฉพาะตัวเลขเท่านั้น';
                errorDiv.style.display = 'block';
                input.style.borderColor = '#ef4444';
                return false;
            }
            
            errorDiv.style.display = 'none';
            input.style.borderColor = '#10b981';
            return true;
        }
        
        // จัดการเมื่อเปลี่ยนสถานะภาษีมูลค่าเพิ่ม
        function handleVatStatusChange() {
            const vatStatus = document.getElementById('companyVatStatusInput').value;
            const vatDateInput = document.getElementById('companyVatDateInput');
            const vatDateRequired = document.getElementById('vatDateRequired');
            
            if (vatStatus === 'จดภาษีมูลค่าเพิ่ม') {
                // บังคับกรอกวันที่
                vatDateInput.removeAttribute('disabled');
                vatDateInput.setAttribute('required', 'required');
                vatDateRequired.style.display = 'inline';
                vatDateInput.style.borderColor = '#3b82f6';
                vatDateInput.style.opacity = '1';
                vatDateInput.style.cursor = 'text';
            } else if (vatStatus === 'ยังไม่จดภาษีมูลค่าเพิ่ม') {
                // ห้ามกรอกวันที่ - disable input
                vatDateInput.removeAttribute('required');
                vatDateInput.setAttribute('disabled', 'disabled');
                vatDateInput.value = ''; // ล้างค่าที่กรอกไว้
                vatDateRequired.style.display = 'none';
                vatDateInput.style.borderColor = '#334155';
                vatDateInput.style.opacity = '0.5';
                vatDateInput.style.cursor = 'not-allowed';
            } else {
                // ไม่ได้เลือกสถานะ
                vatDateInput.removeAttribute('required');
                vatDateInput.removeAttribute('disabled');
                vatDateRequired.style.display = 'none';
                vatDateInput.style.borderColor = '#334155';
                vatDateInput.style.opacity = '1';
                vatDateInput.style.cursor = 'text';
            }
        }
        
        // เปิด modal เพิ่ม/แก้ไขข้อมูลบริษัท
        async function openDatabaseModal(dbId = null) {
            editingDbConfigId = dbId;
            const modal = document.getElementById('databaseModal');
            const form = document.getElementById('companyForm');
            
            // รีเซ็ตฟอร์ม
            form.reset();
            
            // โหลดรายการฐานข้อมูล
            await loadDatabasesForCompany();
            
            // ถ้าเป็นการแก้ไข ให้โหลดข้อมูลบริษัทที่เลือกอยู่
            // สำหรับบริษัทพิเศษที่มีสาขา ให้ใช้ชื่อบริษัทหลัก (ไม่รวมสาขา)
            let company = null;
            
            // ถ้ามี baseCompanyName (บริษัทพิเศษที่มีสาขา) ให้ใช้ชื่อนั้น
            if (baseCompanyName) {
                company = baseCompanyName;
            } else {
                // สำหรับบริษัทปกติ
                const companySelectValue = document.getElementById('companySelect')?.value || '';
                const companyValueValue = document.getElementById('companyValue')?.value || '';
                
                // ถ้า companySelect มี " - " แสดงว่ามีสาขา ให้ตัดส่วนสาขาออก
                const specialCompany = "Build214 บริษัท เอส.ยู. คอมพาเนียน จำกัด รายเดือน";
                if (companySelectValue.includes(' - ') && companySelectValue.startsWith(specialCompany)) {
                    company = specialCompany;
                } else if (companyValueValue && !companyValueValue.startsWith('V:/')) {
                    // ถ้า companyValue ไม่ใช่ path ให้ใช้ companyValue
                    company = companyValueValue;
                } else {
                    // ใช้ companySelect
                    company = companySelectValue;
                }
            }
            
            if (company) {
                try {
                    // แยก Build และชื่อบริษัท
                    const parts = company.split(' ');
                    const build = parts[0];
                    const companyName = parts.slice(1).join(' ');
                    
                    // โหลดข้อมูลบริษัท
                    const customer = companyName || company;
                    const response = await fetch(`/api/auditcheck/company?build=${encodeURIComponent(build)}&company_name=${encodeURIComponent(companyName || company)}&customer=${encodeURIComponent(customer)}`);
                    const data = await response.json();
                    
                    if (data.success && data.company) {
                        // แสดงข้อมูลบริษัทในฟอร์ม
                        const comp = data.company;
                        document.getElementById('companyBuildInput').value = comp.build || '';
                        document.getElementById('companyNameInput').value = comp.company_name || '';
                        document.getElementById('companyTaxIdInput').value = comp.tax_id || '';
                        document.getElementById('companyVatStatusInput').value = comp.vat_status || '';
                        document.getElementById('companyVatDateInput').value = comp.vat_registration_date || '';
                        document.getElementById('companyAddressInput').value = comp.company_address || '';
                        
                        // ตรวจสอบสถานะภาษีมูลค่าเพิ่มเพื่อบังคับกรอกวันที่
                        handleVatStatusChange();
                        // ตรวจสอบเลขประจำตัวผู้เสียภาษี
                        validateTaxId(document.getElementById('companyTaxIdInput'));
                    } else {
                        // ถ้ายังไม่มีข้อมูล ให้ใส่ Build และชื่อบริษัทจากที่เลือก (เชื่อมโยงกัน)
                        document.getElementById('companyBuildInput').value = build;
                        document.getElementById('companyNameInput').value = companyName || company;
                    }
                    
                    // โหลดฐานข้อมูลที่เชื่อมโยงกับบริษัทนี้
                    await loadCompanyDatabase(company);
                } catch (error) {
                    console.error('Error loading company data:', error);
                    // ถ้าโหลดไม่ได้ ให้ใส่ Build และชื่อบริษัทจากที่เลือก (เชื่อมโยงกัน)
                    const parts = company.split(' ');
                    const build = parts[0];
                    const companyName = parts.slice(1).join(' ');
                    document.getElementById('companyBuildInput').value = build;
                    document.getElementById('companyNameInput').value = companyName || company;
                    
                    // โหลดฐานข้อมูลที่เชื่อมโยงกับบริษัทนี้
                    await loadCompanyDatabase(company);
                }
            }
            
            modal.style.display = 'flex';
        }
        
        // โหลดรายการฐานข้อมูลทั้งหมด
        async function loadDatabasesForCompany() {
            try {
                const response = await fetch('/api/auditcheck/databases');
                const data = await response.json();
                
                const select = document.getElementById('companyDatabaseSelect');
                // เก็บค่าเดิม
                const currentValue = select.value;
                
                // ล้าง options (ยกเว้น option แรก)
                while (select.options.length > 1) {
                    select.remove(1);
                }
                
                if (data.success && data.databases && data.databases.length > 0) {
                    data.databases.forEach(db => {
                        const option = document.createElement('option');
                        option.value = db.id;
                        option.textContent = `${db.name} (${db.type})${db.description ? ' - ' + db.description : ''}`;
                        select.appendChild(option);
                    });
                }
                
                // คืนค่าที่เลือกไว้เดิม
                if (currentValue) {
                    select.value = currentValue;
                }
            } catch (error) {
                console.error('Error loading databases:', error);
            }
        }
        
        // โหลดฐานข้อมูลที่เชื่อมโยงกับบริษัท
        async function loadCompanyDatabase(company) {
            try {
                const response = await fetch(`/api/auditcheck/databases?company=${encodeURIComponent(company)}`);
                const data = await response.json();
                
                if (data.success && data.companyDatabase) {
                    document.getElementById('companyDatabaseSelect').value = data.companyDatabase;
                } else {
                    document.getElementById('companyDatabaseSelect').value = '';
                }
            } catch (error) {
                console.error('Error loading company database:', error);
                document.getElementById('companyDatabaseSelect').value = '';
            }
        }
        
        // เปิด modal จัดการฐานข้อมูล (placeholder - ต้องสร้าง modal ใหม่)
        function openDatabaseManagementModal() {
            showAlert('info', 'ฟีเจอร์จัดการฐานข้อมูลจะเปิดในหน้าต่างใหม่\nกรุณาเพิ่มฐานข้อมูลผ่าน API หรือสร้างหน้าจัดการฐานข้อมูลแยก');
            // TODO: สร้าง modal สำหรับจัดการฐานข้อมูล (เพิ่ม/แก้ไข/ลบ)
        }
        
        // ปิด modal
        function closeDatabaseModal() {
            document.getElementById('databaseModal').style.display = 'none';
            editingDbConfigId = null;
            // รีเซ็ตฟอร์ม
            document.getElementById('companyForm').reset();
        }
        
        // บันทึกข้อมูลบริษัทจากฟอร์ม
        async function saveCompanyConfigForm() {
            const form = document.getElementById('companyForm');
            
            // ตรวจสอบ validation
            if (!form.checkValidity()) {
                form.reportValidity();
                return;
            }
            
            const build = document.getElementById('companyBuildInput').value.trim();
            const companyName = document.getElementById('companyNameInput').value.trim();
            const taxId = document.getElementById('companyTaxIdInput').value.trim();
            const vatStatus = document.getElementById('companyVatStatusInput').value.trim();
            const vatDate = document.getElementById('companyVatDateInput').value.trim();
            const companyAddress = document.getElementById('companyAddressInput').value.trim();
            
            // Validation
            if (!build) {
                showAlert('warning', 'กรุณากรอก Build');
                document.getElementById('companyBuildInput').focus();
                return;
            }
            
            if (!companyName) {
                showAlert('warning', 'กรุณากรอกชื่อบริษัท');
                document.getElementById('companyNameInput').focus();
                return;
            }
            
            if (!vatStatus) {
                showAlert('warning', 'กรุณาเลือกสถานะภาษีมูลค่าเพิ่ม');
                document.getElementById('companyVatStatusInput').focus();
                return;
            }
            
            // ถ้าเลือก "จดภาษีมูลค่าเพิ่ม" ต้องบังคับกรอกวันที่
            if (vatStatus === 'จดภาษีมูลค่าเพิ่ม' && !vatDate) {
                showAlert('warning', 'กรุณากรอกวันที่จดภาษีมูลค่าเพิ่ม (จำเป็นเมื่อเลือก "จดภาษีมูลค่าเพิ่ม")');
                document.getElementById('companyVatDateInput').focus();
                return;
            }
            
            if (!companyAddress) {
                showAlert('warning', 'กรุณากรอกที่อยู่บริษัท');
                document.getElementById('companyAddressInput').focus();
                return;
            }
            
            // ตรวจสอบ Tax ID ถ้ามีการกรอก ต้องเป็น 13 หลัก
            if (taxId && taxId.length !== 13) {
                showAlert('warning', 'เลขประจำตัวผู้เสียภาษีต้องเป็น 13 หลัก');
                document.getElementById('companyTaxIdInput').focus();
                return;
            }
            
            try {
                // บันทึกข้อมูลบริษัท (Build และชื่อบริษัทจะเชื่อมโยงกัน)
                // ส่ง customer parameter เพื่อแยกไฟล์ตาม customer
                const response = await fetch('/api/auditcheck/companies', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        build: build,
                        company_name: companyName,
                        customer: companyName, // ใช้ company_name เป็น customer identifier
                        tax_id: taxId || '',
                        vat_status: vatStatus,
                        vat_registration_date: vatDate || '',
                        company_address: companyAddress
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    // บันทึกการเชื่อมโยงฐานข้อมูล (ถ้ามีการเลือก)
                    const selectedDatabaseId = document.getElementById('companyDatabaseSelect').value.trim();
                    const newCompanyDisplay = `${build} ${companyName}`;
                    
                    if (selectedDatabaseId) {
                        try {
                            const dbMappingResponse = await fetch('/api/auditcheck/company-database', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json'
                                },
                                body: JSON.stringify({
                                    company: newCompanyDisplay,
                                    database_id: selectedDatabaseId
                                })
                            });
                            
                            const dbMappingResult = await dbMappingResponse.json();
                            if (dbMappingResult.success) {
                                showAlert('success', `บันทึกข้อมูลบริษัทและฐานข้อมูลสำเร็จ\nBuild: ${build} และชื่อบริษัท: ${companyName} เชื่อมโยงกันแล้ว\nฐานข้อมูลถูกเชื่อมโยงแล้ว`);
                            } else {
                                showAlert('warning', `บันทึกข้อมูลบริษัทสำเร็จ แต่ไม่สามารถบันทึกการเชื่อมโยงฐานข้อมูลได้: ${dbMappingResult.error || 'ไม่ทราบสาเหตุ'}`);
                            }
                        } catch (dbError) {
                            console.error('Error saving database mapping:', dbError);
                            showAlert('warning', `บันทึกข้อมูลบริษัทสำเร็จ แต่เกิดข้อผิดพลาดในการบันทึกการเชื่อมโยงฐานข้อมูล: ${dbError.message}`);
                        }
                    } else {
                        // ถ้าไม่เลือกฐานข้อมูล ให้ลบการเชื่อมโยงเดิม (ถ้ามี)
                        try {
                            await fetch('/api/auditcheck/company-database', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json'
                                },
                                body: JSON.stringify({
                                    company: newCompanyDisplay,
                                    database_id: ''
                                })
                            });
                        } catch (dbError) {
                            console.error('Error removing database mapping:', dbError);
                        }
                        showAlert('success', `บันทึกข้อมูลบริษัทสำเร็จ\nBuild: ${build} และชื่อบริษัท: ${companyName} เชื่อมโยงกันแล้ว`);
                    }
                    
                    closeDatabaseModal();
                    
                    // อัพเดทชื่อบริษัทใน dropdown ให้ตรงกับ Build และชื่อบริษัทที่บันทึก (เชื่อมโยงกัน)
                    document.getElementById('companySelect').value = newCompanyDisplay;
                    document.getElementById('companyValue').value = newCompanyDisplay;
                    
                    // โหลดข้อมูลบริษัทใหม่เพื่อแสดงข้อมูลที่บันทึก (Build และชื่อบริษัทเชื่อมโยงกัน)
                    await loadCompanyInfo(newCompanyDisplay);
                } else {
                    showAlert('error', result.error || 'เกิดข้อผิดพลาดในการบันทึก');
                }
            } catch (error) {
                console.error('Error saving company data:', error);
                showAlert('error', 'เกิดข้อผิดพลาดในการบันทึก: ' + error.message);
            }
        }
        
        // ปิด modal เมื่อคลิกนอก
        document.addEventListener('click', function(e) {
            const modal = document.getElementById('databaseModal');
            if (e.target === modal) {
                closeDatabaseModal();
            }
        });
        
        async function startAudit() {
            const taxMonth = document.getElementById('taxMonth').value;
            const taxYear = document.getElementById('taxYear').value;
            const company = document.getElementById('companyValue').value || document.getElementById('companySelect').value;
            
            if (!taxMonth || !taxYear) {
                showAlert('warning', 'กรุณาเลือกเดือนและปีภาษี');
                return;
            }
            
            // สร้าง taxMonth ในรูปแบบ YYYY-MM
            const taxMonthFormatted = `${taxYear}-${taxMonth}`;
            
            if (!company || company.trim() === '') {
                showAlert('warning', 'กรุณาเลือกบริษัทที่ต้องการตรวจสอบ');
                return;
            }
            
            // ตรวจสอบว่าชื่อบริษัทที่เลือกอยู่ในรายการหรือไม่ (ข้ามการตรวจสอบสำหรับบริษัทพิเศษที่มีสาขา)
            // สำหรับบริษัทพิเศษที่มีสาขา companyValue จะเป็น path ของสาขา ไม่ใช่ชื่อบริษัท
            const specialCompany = "Build214 บริษัท เอส.ยู. คอมพาเนียน จำกัด รายเดือน";
            const isSpecialCompanyWithBranch = baseCompanyName === specialCompany && selectedBranch !== null;
            
            if (!isSpecialCompanyWithBranch && !allCompanies.includes(company)) {
                // ตรวจสอบว่า company เป็น path หรือไม่ (สำหรับสาขา)
                if (!company.startsWith('V:/') && !company.startsWith('V:\\')) {
                    showAlert('warning', 'กรุณาเลือกบริษัทจากรายการที่แสดง');
                    return;
                }
            }
            
            // Show steps container
            document.getElementById('stepsContainer').style.display = 'block';
            
            // Reset all steps
            resetSteps();
            
            // เริ่มตรวจสอบไฟล์ตามโครงสร้างโฟลเดอร์
            await checkFilesStructure(taxMonthFormatted, company);
        }
        
        async function checkFilesStructure(taxMonth, company) {
            const step = document.getElementById('step1');
            const status = document.getElementById('step1Status');
            const details = document.getElementById('step1Details');
            
            step.classList.add('active');
            status.textContent = 'กำลังตรวจสอบ...';
            status.className = 'step-status checking';
            
            try {
                const response = await fetch('/api/auditcheck/check-files', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        taxMonth: taxMonth,
                        company: company
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    step.classList.remove('active');
                    
                    let html = '';
                    
                    // แสดงโครงสร้างโฟลเดอร์
                    if (data.folderStructure && data.folderStructure.length > 0) {
                        html += '<div style="margin-bottom: 15px;">';
                        html += '<strong>📁 โครงสร้างโฟลเดอร์ที่พบ:</strong><br>';
                        data.folderStructure.forEach((folder, index) => {
                            html += `<div style="margin-left: 20px; margin-top: 15px; padding: 15px; background: #0f172a; border-radius: 5px; border-left: 3px solid #10b981;">`;
                            html += `<div style="color: #10b981; font-weight: 600; margin-bottom: 8px;">✅ ${folder.month_year_folder_name || folder.month_year_folder}</div>`;
                            html += `<div style="color: #cbd5e1; font-size: 0.9em; margin-bottom: 10px;">📂 Path: ${folder.month_year_folder}</div>`;
                            html += `<div style="color: #fbbf24; font-size: 0.9em; margin-bottom: 10px;">📊 พบไฟล์ทั้งหมด: ${folder.files_count} ไฟล์</div>`;
                            
                            // แสดงรายการไฟล์ในโฟลเดอร์นี้
                            if (folder.files && folder.files.length > 0) {
                                html += `<div style="margin-top: 10px;">`;
                                html += `<div style="color: #60a5fa; font-size: 0.9em; margin-bottom: 5px;">📄 รายการไฟล์:</div>`;
                                html += `<div style="margin-left: 15px; max-height: 200px; overflow-y: auto;">`;
                                folder.files.forEach(file => {
                                    const fileSizeKB = (file.size / 1024).toFixed(2);
                                    const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2);
                                    const sizeDisplay = file.size > 1024 * 1024 ? `${fileSizeMB} MB` : `${fileSizeKB} KB`;
                                    html += `<div style="color: #cbd5e1; font-size: 0.85em; margin-bottom: 5px; padding: 5px; background: #1e293b; border-radius: 3px;">`;
                                    html += `📄 <strong>${file.name}</strong> <span style="color: #94a3b8;">(${sizeDisplay})</span>`;
                                    html += `</div>`;
                                });
                                html += `</div>`;
                                html += `</div>`;
                            } else {
                                html += `<div style="color: #fbbf24; font-size: 0.9em; margin-top: 10px;">⚠️ ไม่พบไฟล์ในโฟลเดอร์นี้</div>`;
                            }
                            
                            html += `</div>`;
                        });
                        html += '</div>';
                    }
                    
                    // แสดงไฟล์ที่พบ
                    if (data.foundFiles && data.foundFiles.length > 0) {
                        html += '<div style="margin-bottom: 15px;">';
                        html += `<strong>✅ ไฟล์ที่พบ (${data.totalFiles} ไฟล์):</strong><br>`;
                        html += '<div class="file-list" style="max-height: 300px;">';
                        data.foundFiles.forEach(file => {
                            const fileSizeKB = (file.size / 1024).toFixed(2);
                            html += `<div class="file-item success">`;
                            html += `<strong>${file.name}</strong> <span style="color: #94a3b8; font-size: 0.85em;">(${fileSizeKB} KB)</span>`;
                            html += `</div>`;
                        });
                        html += '</div>';
                        html += '</div>';
                    }
                    
                    // แสดงไฟล์ที่ขาดหายไป
                    if (data.missingFiles && data.missingFiles.length > 0) {
                        html += '<div style="margin-bottom: 15px;">';
                        html += `<strong>❌ สิ่งที่ขาดหายไป:</strong><br>`;
                        html += '<div class="file-list" style="max-height: 400px;">';
                        data.missingFiles.forEach(missing => {
                            if (typeof missing === 'object') {
                                html += `<div class="file-item error" style="padding: 15px;">`;
                                html += `<strong>${missing.message}</strong><br>`;
                                
                                // แสดงโฟลเดอร์ที่มีอยู่
                                if (missing.existing_folders && missing.existing_folders.length > 0) {
                                    html += `<span style="color: #fbbf24; margin-top: 8px; display: block;">📂 โฟลเดอร์ที่มีอยู่ใน "${missing.year_folder_path || missing.parent_path || 'โฟลเดอร์นี้'}":</span>`;
                                    html += `<div style="margin-left: 20px; margin-top: 8px; background: #0f172a; padding: 10px; border-radius: 5px;">`;
                                    missing.existing_folders.forEach(folder => {
                                        html += `<div style="color: #cbd5e1; font-size: 0.9em; margin-bottom: 3px;">📁 ${folder}</div>`;
                                    });
                                    html += `</div>`;
                                }
                                
                                // แสดงไฟล์ที่มีอยู่ (ถ้ามี)
                                if (missing.existing_files && missing.existing_files.length > 0) {
                                    html += `<span style="color: #fbbf24; margin-top: 8px; display: block;">📄 ไฟล์ที่มีอยู่ใน "${missing.year_folder_path || missing.parent_path || 'โฟลเดอร์นี้'}":</span>`;
                                    html += `<div style="margin-left: 20px; margin-top: 8px; background: #0f172a; padding: 10px; border-radius: 5px;">`;
                                    missing.existing_files.slice(0, 10).forEach(file => {
                                        html += `<div style="color: #cbd5e1; font-size: 0.9em; margin-bottom: 3px;">📄 ${file}</div>`;
                                    });
                                    if (missing.existing_files.length > 10) {
                                        html += `<div style="color: #94a3b8; font-size: 0.85em; margin-top: 5px;">... และอีก ${missing.existing_files.length - 10} ไฟล์</div>`;
                                    }
                                    html += `</div>`;
                                }
                                
                                // แสดง existing_items (สำหรับกรณีอื่นๆ)
                                if (missing.existing_items && missing.existing_items.length > 0) {
                                    html += `<span style="color: #fbbf24; margin-top: 8px; display: block;">📂 โฟลเดอร์/ไฟล์ที่มีอยู่ใน "${missing.parent_path || 'โฟลเดอร์นี้'}":</span>`;
                                    html += `<div style="margin-left: 20px; margin-top: 8px; background: #0f172a; padding: 10px; border-radius: 5px;">`;
                                    missing.existing_items.forEach(item => {
                                        html += `<div style="color: #cbd5e1; font-size: 0.9em; margin-bottom: 3px;">• ${item}</div>`;
                                    });
                                    html += `</div>`;
                                }
                                
                                // แสดงข้อความเมื่อไม่มีอะไรเลย
                                if ((!missing.existing_folders || missing.existing_folders.length === 0) && 
                                    (!missing.existing_files || missing.existing_files.length === 0) && 
                                    (!missing.existing_items || missing.existing_items.length === 0)) {
                                    html += `<div style="margin-left: 20px; margin-top: 8px; color: #94a3b8; font-size: 0.9em;">ไม่มีโฟลเดอร์หรือไฟล์ใดๆ</div>`;
                                }
                                
                                if (missing.expected) {
                                    html += `<div style="margin-top: 8px; color: #60a5fa; font-size: 0.9em;">💡 คาดหวัง: ${missing.expected}</div>`;
                                }
                                
                                if (missing.expected_patterns && missing.expected_patterns.length > 0) {
                                    html += `<div style="margin-top: 8px; color: #60a5fa; font-size: 0.9em;">💡 รูปแบบที่คาดหวัง: ${missing.expected_patterns.join(', ')}</div>`;
                                }
                                
                                html += `</div>`;
                            } else {
                                html += `<div class="file-item error">${missing}</div>`;
                            }
                        });
                        html += '</div>';
                        html += '</div>';
                    }
                    
                    if (data.hasFiles) {
                        step.classList.add('completed');
                        status.textContent = 'พบไฟล์';
                        status.className = 'step-status success';
                    } else {
                        step.classList.add('error');
                        status.textContent = 'ไม่พบไฟล์';
                        status.className = 'step-status error';
                    }
                    
                    details.innerHTML = html || 'ไม่พบข้อมูล';
                    
                    // ถ้ามีไฟล์ ให้ดำเนินการขั้นตอนถัดไป
                    if (data.hasFiles) {
                        await checkStep2(taxMonth, company);
                    }
                } else {
                    step.classList.remove('active');
                    step.classList.add('error');
                    status.textContent = 'เกิดข้อผิดพลาด';
                    status.className = 'step-status error';
                    details.innerHTML = `❌ เกิดข้อผิดพลาด: ${data.error || 'Unknown error'}`;
                }
            } catch (error) {
                step.classList.remove('active');
                step.classList.add('error');
                status.textContent = 'เกิดข้อผิดพลาด';
                status.className = 'step-status error';
                details.textContent = '❌ เกิดข้อผิดพลาด: ' + error.message;
            }
        }
        
        function resetSteps() {
            for (let i = 1; i <= 5; i++) {
                const step = document.getElementById(`step${i}`);
                step.classList.remove('active', 'completed', 'error');
                
                const status = document.getElementById(`step${i}Status`);
                status.textContent = 'รอตรวจสอบ';
                status.className = 'step-status pending';
                
                const details = document.getElementById(`step${i}Details`);
                details.textContent = i === 1 ? 'กำลังตรวจสอบ...' : 'รอการตรวจสอบขั้นตอนก่อนหน้า...';
            }
        }
        
        async function checkStep1(taxMonth, company) {
            const step = document.getElementById('step1');
            const status = document.getElementById('step1Status');
            const details = document.getElementById('step1Details');
            
            step.classList.add('active');
            status.textContent = 'กำลังตรวจสอบ...';
            status.className = 'step-status checking';
            
            try {
                const response = await fetch('/api/auditcheck/check-trial-balance', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        taxMonth: taxMonth,
                        company: company
                    })
                });
                
                const data = await response.json();
                
                if (data.success && data.exists) {
                    step.classList.remove('active');
                    step.classList.add('completed');
                    status.textContent = 'พบไฟล์';
                    status.className = 'step-status success';
                    details.innerHTML = `✅ พบไฟล์งบทดลอง: <strong>${data.filePath || 'N/A'}</strong>`;
                    
                    // Continue to step 2 (เดิมเป็น Step 3 - ภาษีซื้อ)
                    await checkStep2(taxMonth, company);
                } else {
                    step.classList.remove('active');
                    step.classList.add('error');
                    status.textContent = 'ไม่พบไฟล์';
                    status.className = 'step-status error';
                    details.innerHTML = `❌ ไม่พบไฟล์งบทดลองสำหรับเดือน ${taxMonth}`;
                }
            } catch (error) {
                step.classList.remove('active');
                step.classList.add('error');
                status.textContent = 'เกิดข้อผิดพลาด';
                status.className = 'step-status error';
                details.textContent = '❌ เกิดข้อผิดพลาด: ' + error.message;
            }
        }
        
        async function checkStep2(taxMonth, company) {
            // Step 2 ตอนนี้คือ ภาษีซื้อ (เดิมเป็น Step 3)
            const step = document.getElementById('step2');
            const status = document.getElementById('step2Status');
            const details = document.getElementById('step2Details');
            
            step.classList.add('active');
            status.textContent = 'กำลังตรวจสอบ...';
            status.className = 'step-status checking';
            
            try {
                const response = await fetch('/api/auditcheck/check-purchase-tax', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        taxMonth: taxMonth,
                        company: company
                    })
                });
                
                const data = await response.json();
                
                if (data.success && data.exists) {
                    step.classList.remove('active');
                    
                    let html = '';
                    html += `<div style="margin-bottom: 15px;">`;
                    html += `<strong style="color: #60a5fa;">📄 ไฟล์ภาษีซื้อที่พบ:</strong><br>`;
                    if (data.purchaseTaxFiles && data.purchaseTaxFiles.length > 0) {
                        html += `<div class="file-list" style="max-height: 100px; margin-top: 5px;">`;
                        data.purchaseTaxFiles.forEach(file => {
                            html += `<div class="file-item success" style="font-size: 0.85em;">${file}</div>`;
                        });
                        html += `</div>`;
                    }
                    html += `</div>`;
                    
                    // แสดงข้อมูลโฟลเดอร์ VAT เหมือน Step 4
                    if (data.vatFolderInfo) {
                        html += `<div style="margin-top: 15px; padding: 15px; background: #1e293b; border-radius: 5px; border-left: 4px solid #3b82f6;">`;
                        html += `<div style="color: #60a5fa; font-weight: 600; margin-bottom: 10px;">📂 ข้อมูลโฟลเดอร์ VAT:</div>`;
                        
                        if (data.vatFolderInfo.month_year_folder) {
                            html += `<div style="margin-left: 20px; margin-top: 5px; color: #cbd5e1; font-size: 0.9em;">`;
                            html += `โฟลเดอร์เดือน-ปี: ${data.vatFolderInfo.month_year_folder}`;
                            html += `</div>`;
                        }
                        
                        if (data.vatFolderInfo.found) {
                            html += `<div style="margin-left: 20px; margin-top: 10px; color: #10b981;">✅ พบโฟลเดอร์ VAT:</div>`;
                            if (data.vatFolderInfo.folders && data.vatFolderInfo.folders.length > 0) {
                                data.vatFolderInfo.folders.forEach(vatFolder => {
                                    html += `<div style="margin-left: 30px; margin-top: 5px; color: #cbd5e1; font-size: 0.9em;">📂 ${vatFolder.name} (${vatFolder.path})</div>`;
                                    if (vatFolder.pdf_files_count !== undefined) {
                                        html += `<div style="margin-left: 35px; color: #6ee7b7; font-size: 0.85em;">📄 พบไฟล์ PDF/JPG/PNG: ${vatFolder.pdf_files_count} ไฟล์</div>`;
                                    }
                                });
                            }
                        } else {
                            html += `<div style="margin-left: 20px; margin-top: 10px; color: #ef4444;">❌ ไม่พบโฟลเดอร์ VAT/vat/Vat</div>`;
                        }
                        html += `</div>`;
                    }
                    
                    // แสดงการเปรียบเทียบจำนวนรายการกับไฟล์ PDF
                    if (data.purchaseTaxRowCount !== undefined && data.pdfFilesCount !== undefined) {
                        html += `<div style="margin-top: 15px; padding: 15px; background: ${data.countMatch ? '#0f172a' : '#1e293b'}; border-radius: 5px; border-left: 4px solid ${data.countMatch ? '#10b981' : '#ef4444'};">`;
                        html += `<div style="color: ${data.countMatch ? '#10b981' : '#ef4444'}; font-weight: 600; margin-bottom: 10px;">`;
                        html += data.countMatch ? '✅' : '❌';
                        html += ` การเปรียบเทียบจำนวนรายการ:</div>`;
                        html += `<div style="color: #cbd5e1; margin-bottom: 5px;">`;
                        html += `📊 จำนวนรายการในไฟล์ภาษีซื้อ: <strong style="color: #60a5fa;">${data.purchaseTaxRowCount || 0}</strong> รายการ</div>`;
                        html += `<div style="color: #cbd5e1; margin-bottom: 5px;">`;
                        html += `📁 จำนวนไฟล์ที่รองรับ OCR (PDF/JPG/PNG) ในโฟลเดอร์ VAT: <strong style="color: #60a5fa;">${data.pdfFilesCount || 0}</strong> ไฟล์</div>`;
                        html += `<div style="color: ${data.countMatch ? '#10b981' : '#ef4444'}; font-weight: 600; margin-top: 10px;">`;
                        html += data.countMatch ? '✅ จำนวนรายการตรงกัน' : '❌ จำนวนรายการไม่ตรงกัน';
                        html += `</div>`;
                        html += `</div>`;
                    }
                    
                    if (data.countMatch) {
                        step.classList.add('completed');
                        status.textContent = 'พบไฟล์และจำนวนตรงกัน';
                        status.className = 'step-status success';
                    } else {
                        step.classList.add('error');
                        status.textContent = 'พบไฟล์แต่จำนวนไม่ตรงกัน';
                        status.className = 'step-status error';
                    }
                    
                    details.innerHTML = html;
                    
                    // Continue to step 3 (เดิมเป็น Step 4 - งบทดลอง)
                    await checkStep3(taxMonth, company);
                } else {
                    step.classList.remove('active');
                    step.classList.add('error');
                    status.textContent = 'ไม่พบไฟล์';
                    status.className = 'step-status error';
                    details.innerHTML = `❌ ไม่พบไฟล์ภาษีซื้อสำหรับเดือน ${taxMonth}`;
                }
            } catch (error) {
                step.classList.remove('active');
                step.classList.add('error');
                status.textContent = 'เกิดข้อผิดพลาด';
                status.className = 'step-status error';
                details.textContent = '❌ เกิดข้อผิดพลาด: ' + error.message;
            }
        }
        
        async function checkStep3(taxMonth, company) {
            // Step 3 ตอนนี้คือ งบทดลอง (เดิมเป็น Step 4)
            const step = document.getElementById('step3');
            const status = document.getElementById('step3Status');
            const details = document.getElementById('step3Details');
            
            step.classList.add('active');
            status.textContent = 'กำลังตรวจสอบ...';
            status.className = 'step-status checking';
            
            try {
                const response = await fetch('/api/auditcheck/compare-trial-balance-files', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        taxMonth: taxMonth,
                        company: company
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    step.classList.remove('active');
                    
                    let html = '';
                    
                    // แสดงข้อมูลไฟล์งบทดลองที่พบ
                    if (data.trialBalanceFiles && data.trialBalanceFiles.length > 0) {
                        html += `<div style="margin-bottom: 15px;">`;
                        html += `<strong>📊 ไฟล์งบทดลองที่พบ:</strong><br>`;
                        html += `<div class="file-list" style="max-height: 150px;">`;
                        data.trialBalanceFiles.forEach(file => {
                            html += `<div class="file-item success">📄 ${file}</div>`;
                        });
                        html += `</div>`;
                        html += `</div>`;
                        
                        // แสดงข้อมูลที่อ่านได้จากงบทดลอง
                        if (data.trialBalanceData) {
                            const tbData = data.trialBalanceData;
                            html += `<div style="margin-bottom: 15px; padding: 15px; background: #0f172a; border-radius: 5px; border-left: 3px solid #60a5fa;">`;
                            html += `<strong style="color: #60a5fa; margin-bottom: 10px; display: block;">📋 ข้อมูลงบทดลอง:</strong>`;
                            
                            if (tbData.company_name) {
                                html += `<div style="color: #cbd5e1; font-size: 0.9em; margin-bottom: 5px;">🏢 ชื่อกิจการ: <strong>${tbData.company_name}</strong></div>`;
                            }
                            if (tbData.report_date) {
                                html += `<div style="color: #cbd5e1; font-size: 0.9em; margin-bottom: 5px;">📅 วันที่ออกรายงาน: <strong>${tbData.report_date}</strong></div>`;
                            }
                            if (tbData.period) {
                                html += `<div style="color: #cbd5e1; font-size: 0.9em; margin-bottom: 10px;">📆 ช่วงเวลา: <strong>${tbData.period}</strong></div>`;
                            }
                            
                            html += `<div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #334155;">`;
                            html += `<strong style="color: #10b981; margin-bottom: 8px; display: block;">💰 ยอดคงเหลือ:</strong>`;
                            
                            // ฟังก์ชันสำหรับตรวจสอบว่ายอดไม่เป็น 0 หรือไม่
                            function formatBalance(value, label) {
                                const numValue = parseFloat(value) || 0;
                                const isNonZero = numValue !== 0;
                                const color = isNonZero ? '#ef4444' : '#cbd5e1';
                                const fontWeight = isNonZero ? '600' : 'normal';
                                const formatted = numValue.toLocaleString('th-TH', {minimumFractionDigits: 2, maximumFractionDigits: 2});
                                return `<span style="color: ${color}; font-size: 0.9em; font-weight: ${fontWeight};">${label} ${formatted}</span>`;
                            }
                            
                            // ภาษีซื้อ
                            const purchaseTaxDebit = parseFloat(tbData.purchase_tax?.debit || 0);
                            const purchaseTaxCredit = parseFloat(tbData.purchase_tax?.credit || 0);
                            const purchaseTaxHasBalance = purchaseTaxDebit !== 0 || purchaseTaxCredit !== 0;
                            const purchaseTaxDebitFormatted = formatBalance(purchaseTaxDebit, 'เดบิต');
                            const purchaseTaxCreditFormatted = formatBalance(purchaseTaxCredit, 'เครดิต');
                            html += `<div style="margin-left: 10px; margin-bottom: 8px; ${purchaseTaxHasBalance ? 'padding: 8px; background: rgba(239, 68, 68, 0.1); border-left: 3px solid #ef4444; border-radius: 3px;' : ''}">`;
                            html += `<span style="color: #cbd5e1; font-size: 0.9em;">📊 ภาษีซื้อ:</span> `;
                            html += purchaseTaxDebitFormatted;
                            html += ` | `;
                            html += purchaseTaxCreditFormatted;
                            if (purchaseTaxHasBalance) {
                                html += ` <span style="color: #ef4444; font-size: 0.85em; margin-left: 5px;">⚠️ ต้องตรวจสอบ</span>`;
                            }
                            html += `</div>`;
                            
                            // ภาษีซื้อยังไม่ถึงกำหนด
                            const purchaseTaxNotDueDebit = parseFloat(tbData.purchase_tax_not_due?.debit || 0);
                            const purchaseTaxNotDueCredit = parseFloat(tbData.purchase_tax_not_due?.credit || 0);
                            const purchaseTaxNotDueHasBalance = purchaseTaxNotDueDebit !== 0 || purchaseTaxNotDueCredit !== 0;
                            const purchaseTaxNotDueDebitFormatted = formatBalance(purchaseTaxNotDueDebit, 'เดบิต');
                            const purchaseTaxNotDueCreditFormatted = formatBalance(purchaseTaxNotDueCredit, 'เครดิต');
                            html += `<div style="margin-left: 10px; margin-bottom: 8px; ${purchaseTaxNotDueHasBalance ? 'padding: 8px; background: rgba(239, 68, 68, 0.1); border-left: 3px solid #ef4444; border-radius: 3px;' : ''}">`;
                            html += `<span style="color: #cbd5e1; font-size: 0.9em;">📊 ภาษีซื้อยังไม่ถึงกำหนด:</span> `;
                            html += purchaseTaxNotDueDebitFormatted;
                            html += ` | `;
                            html += purchaseTaxNotDueCreditFormatted;
                            if (purchaseTaxNotDueHasBalance) {
                                html += ` <span style="color: #ef4444; font-size: 0.85em; margin-left: 5px;">⚠️ ต้องตรวจสอบ</span>`;
                            }
                            html += `</div>`;
                            
                            // ภาษีขาย ภ.พ.30
                            const salesTaxVat30Debit = parseFloat(tbData.sales_tax_vat30?.debit || 0);
                            const salesTaxVat30Credit = parseFloat(tbData.sales_tax_vat30?.credit || 0);
                            const salesTaxVat30HasBalance = salesTaxVat30Debit !== 0 || salesTaxVat30Credit !== 0;
                            const salesTaxVat30DebitFormatted = formatBalance(salesTaxVat30Debit, 'เดบิต');
                            const salesTaxVat30CreditFormatted = formatBalance(salesTaxVat30Credit, 'เครดิต');
                            html += `<div style="margin-left: 10px; margin-bottom: 8px; ${salesTaxVat30HasBalance ? 'padding: 8px; background: rgba(239, 68, 68, 0.1); border-left: 3px solid #ef4444; border-radius: 3px;' : ''}">`;
                            html += `<span style="color: #cbd5e1; font-size: 0.9em;">📊 ภาษีขาย ภ.พ.30:</span> `;
                            html += salesTaxVat30DebitFormatted;
                            html += ` | `;
                            html += salesTaxVat30CreditFormatted;
                            if (salesTaxVat30HasBalance) {
                                html += ` <span style="color: #ef4444; font-size: 0.85em; margin-left: 5px;">⚠️ ต้องตรวจสอบ</span>`;
                            }
                            html += `</div>`;
                            
                            html += `</div>`;
                            html += `</div>`;
                        }
                    } else {
                        html += `<div style="margin-bottom: 15px; color: #ef4444;">`;
                        html += `⚠️ ไม่พบไฟล์ Excel ที่มีคำว่า "งบทดลอง" ในโฟลเดอร์ VAT/vat/Vat`;
                        html += `</div>`;
                    }
                    
                    // Step 3 ไม่ต้องเปรียบเทียบกับไฟล์ OCR - แสดงเฉพาะข้อมูลงบทดลองเท่านั้น
                    if (data.trialBalanceFiles && data.trialBalanceFiles.length > 0) {
                        step.classList.add('completed');
                        status.textContent = 'พบข้อมูล';
                        status.className = 'step-status success';
                        html += `<div style="color: #10b981; font-weight: 600; margin-top: 10px;">`;
                        html += `✅ พบข้อมูลงบทดลอง: ${data.trialBalanceCount || 0} รายการ`;
                        html += `</div>`;
                    } else {
                        step.classList.add('error');
                        status.textContent = 'ไม่พบข้อมูล';
                        status.className = 'step-status error';
                        html += `<div style="color: #ef4444; font-weight: 600; margin-top: 10px;">`;
                        html += `❌ ไม่พบไฟล์งบทดลอง`;
                        html += `</div>`;
                    }
                    
                    details.innerHTML = html;
                    
                    // Continue to step 4 (เดิมเป็น Step 2 - รัน OCR)
                    await checkStep4(taxMonth, company);
                } else {
                    step.classList.remove('active');
                    step.classList.add('error');
                    status.textContent = 'เกิดข้อผิดพลาด';
                    status.className = 'step-status error';
                    details.textContent = '❌ เกิดข้อผิดพลาด: ' + (data.error || 'Unknown error');
                }
            } catch (error) {
                step.classList.remove('active');
                step.classList.add('error');
                status.textContent = 'เกิดข้อผิดพลาด';
                status.className = 'step-status error';
                details.textContent = '❌ เกิดข้อผิดพลาด: ' + error.message;
            }
        }
        
        async function checkStep4(taxMonth, company) {
            // Step 4 ตอนนี้คือ รัน OCR (เดิมเป็น Step 2)
            const step = document.getElementById('step4');
            const status = document.getElementById('step4Status');
            const details = document.getElementById('step4Details');
            
            step.classList.add('active');
            status.textContent = 'กำลังตรวจสอบ...';
            status.className = 'step-status checking';
            
            try {
                const response = await fetch('/api/auditcheck/check-excel-files', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        taxMonth: taxMonth,
                        company: company
                    })
                });
                
                const data = await response.json();
                
                if (data.success && data.exists) {
                    step.classList.remove('active');
                    step.classList.add('completed');
                    status.textContent = 'พบไฟล์ Excel';
                    status.className = 'step-status success';
                    
                    let html = `<div style="margin-bottom: 15px;">`;
                    html += `<strong>✅ พบไฟล์ Excel ที่ส่งออกจากระบบ OCR:</strong><br>`;
                    
                    // แสดงผลการค้นหา
                    if (data.searchResults && data.searchResults.length > 0) {
                        html += `<div style="margin-top: 10px; margin-bottom: 15px;">`;
                        html += `<span style="color: #60a5fa; font-size: 0.9em;">🔍 วิธีการค้นหา:</span><br>`;
                        data.searchResults.forEach((result, index) => {
                            html += `<div style="margin-left: 15px; margin-top: 5px; color: #cbd5e1; font-size: 0.85em;">`;
                            if (result.search_method === 'direct') {
                                html += `✅ พบโดยตรง: ${result.folder_path} (รูปแบบ: ${result.pattern_found || 'N/A'})`;
                            } else if (result.search_method === 'year_then_month') {
                                html += `✅ พบผ่านโฟลเดอร์ปี: ${result.year_folder} → ${result.folder_path} (รูปแบบ: ${result.pattern_found || 'N/A'})`;
                            }
                            
                            // แสดงข้อมูลเกี่ยวกับโฟลเดอร์ VAT
                            if (result.vat_folder_info) {
                                html += `<br><span style="color: #10b981; margin-left: 10px;">📁 โฟลเดอร์ VAT:</span> `;
                                if (result.vat_folder_info.found) {
                                    html += `<span style="color: #10b981;">✅ พบโฟลเดอร์ VAT</span>`;
                                    if (result.vat_folder_info.folders && result.vat_folder_info.folders.length > 0) {
                                        result.vat_folder_info.folders.forEach(vatFolder => {
                                            html += `<br><span style="margin-left: 25px; color: #cbd5e1;">📂 ${vatFolder.name} (${vatFolder.path})</span>`;
                                            if (vatFolder.excel_files && vatFolder.excel_files.length > 0) {
                                                html += `<br><span style="margin-left: 30px; color: #6ee7b7; font-size: 0.9em;">📄 พบไฟล์ Excel: ${vatFolder.excel_files.join(', ')}</span>`;
                                            }
                                        });
                                    }
                                } else {
                                    html += `<span style="color: #fbbf24;">⚠️ ไม่พบโฟลเดอร์ VAT (ค้นหาในโฟลเดอร์เดือน-ปีโดยตรง)</span>`;
                                }
                            }
                            
                            html += `</div>`;
                        });
                        html += `</div>`;
                    }
                    
                    if (data.excelData && data.excelData.length > 0) {
                        data.excelData.forEach((excel, index) => {
                            if (excel.error) {
                                html += `<div style="margin-top: 10px; padding: 10px; background: #0f172a; border-radius: 5px; border-left: 3px solid #ef4444;">`;
                                html += `<div style="color: #ef4444;">❌ ${excel.path}</div>`;
                                html += `<div style="color: #94a3b8; font-size: 0.9em; margin-top: 5px;">ข้อผิดพลาด: ${excel.error}</div>`;
                                html += `</div>`;
                            } else {
                                const fileSizeKB = (excel.file_size / 1024).toFixed(2);
                                const fileSizeMB = (excel.file_size / (1024 * 1024)).toFixed(2);
                                const sizeDisplay = excel.file_size > 1024 * 1024 ? `${fileSizeMB} MB` : `${fileSizeKB} KB`;
                                
                                html += `<div style="margin-top: 10px; padding: 15px; background: #0f172a; border-radius: 5px; border-left: 3px solid #10b981;">`;
                                html += `<div style="color: #10b981; font-weight: 600;">📊 ${excel.path}</div>`;
                                html += `<div style="color: #cbd5e1; font-size: 0.9em; margin-top: 8px;">`;
                                html += `📈 จำนวนรายการ: <strong>${excel.row_count}</strong> รายการ<br>`;
                                html += `📦 ขนาดไฟล์: ${sizeDisplay}`;
                                html += `</div>`;
                                
                                if (excel.headers && excel.headers.length > 0) {
                                    html += `<div style="margin-top: 8px; color: #60a5fa; font-size: 0.85em;">📋 คอลัมน์: ${excel.headers.slice(0, 5).join(', ')}${excel.headers.length > 5 ? '...' : ''}</div>`;
                                }
                                
                                html += `</div>`;
                            }
                        });
                    } else {
                        html += `<div style="margin-top: 10px; color: #cbd5e1;">พบไฟล์ Excel ${data.fileCount || 0} ไฟล์</div>`;
                        if (data.files && data.files.length > 0) {
                            html += '<div class="file-list" style="max-height: 200px;">';
                            data.files.forEach(file => {
                                html += `<div class="file-item success">${file}</div>`;
                            });
                            html += '</div>';
                        }
                    }
                    
                    html += `</div>`;
                    details.innerHTML = html;
                    
                    // Continue to step 5
                    await checkStep5(taxMonth, company);
                } else {
                    step.classList.remove('active');
                    step.classList.add('error');
                    status.textContent = 'ไม่พบไฟล์ Excel';
                    status.className = 'step-status error';
                    
                    // เก็บข้อมูล Step 4 สำหรับใช้เมื่อกดยกเลิก
                    step4Data = {
                        taxMonth: taxMonth,
                        company: company
                    };
                    
                    let html = `<div style="margin-bottom: 15px;">`;
                    html += `<strong>❌ ไม่พบไฟล์ Excel OCR ในโฟลเดอร์ VAT/vat/Vat สำหรับเดือน ${taxMonth}</strong><br>`;
                    html += `<div style="margin-top: 10px; color: #cbd5e1; font-size: 0.9em;">💡 ระบบค้นหาไฟล์ Excel ที่มีคำว่า "ocr" หรือ "invoice_data" ในชื่อไฟล์ภายในโฟลเดอร์ VAT/vat/Vat</div>`;
                    
                    // แสดงรายการโฟลเดอร์ที่มีอยู่จริง
                    if (data.searchResults && data.searchResults.length > 0) {
                        data.searchResults.forEach((result, index) => {
                            if (result.search_method === 'not_found') {
                                html += `<div style="margin-top: 15px; padding: 15px; background: #0f172a; border-radius: 5px; border-left: 3px solid #ef4444;">`;
                                html += `<div style="color: #fbbf24; margin-bottom: 10px;">📂 โฟลเดอร์ที่มีอยู่ใน "${result.pv_folder}":</div>`;
                                
                                if (result.all_pv_folders && result.all_pv_folders.length > 0) {
                                    html += `<div style="margin-left: 20px; background: #1e293b; padding: 10px; border-radius: 5px; max-height: 200px; overflow-y: auto;">`;
                                    result.all_pv_folders.forEach(folder => {
                                        html += `<div style="color: #cbd5e1; font-size: 0.9em; margin-bottom: 3px;">📁 ${folder}</div>`;
                                    });
                                    html += `</div>`;
                                } else {
                                    html += `<div style="margin-left: 20px; color: #94a3b8; font-size: 0.9em;">ไม่มีโฟลเดอร์ใดๆ</div>`;
                                }
                                
                                // แสดงโฟลเดอร์ปีที่พบ
                                if (result.year_folders && result.year_folders.length > 0) {
                                    html += `<div style="margin-top: 10px; color: #60a5fa; margin-bottom: 5px;">📅 โฟลเดอร์ปีที่พบ:</div>`;
                                    html += `<div style="margin-left: 20px; background: #1e293b; padding: 10px; border-radius: 5px;">`;
                                    result.year_folders.forEach(yearFolder => {
                                        html += `<div style="color: #cbd5e1; font-size: 0.9em; margin-bottom: 3px;">📁 ${yearFolder}</div>`;
                                    });
                                    html += `</div>`;
                                    
                                    // แสดงโฟลเดอร์ย่อยในโฟลเดอร์ปี
                                    if (result.year_folder_subfolders && result.year_folder_subfolders.length > 0) {
                                        html += `<div style="margin-top: 10px; color: #60a5fa; margin-bottom: 5px;">📂 โฟลเดอร์ย่อยในโฟลเดอร์ปี:</div>`;
                                        html += `<div style="margin-left: 20px; background: #1e293b; padding: 10px; border-radius: 5px; max-height: 150px; overflow-y: auto;">`;
                                        result.year_folder_subfolders.forEach(subfolder => {
                                            html += `<div style="color: #cbd5e1; font-size: 0.9em; margin-bottom: 3px;">📁 ${subfolder}</div>`;
                                        });
                                        html += `</div>`;
                                    }
                                }
                                
                                if (data.monthYearPatterns && data.monthYearPatterns.length > 0) {
                                    html += `<div style="margin-top: 10px; color: #60a5fa; font-size: 0.9em;">💡 คาดหวังโฟลเดอร์: ${data.monthYearPatterns.join(', ')}</div>`;
                                }
                                html += `</div>`;
                            } else if (result.vat_folder_info) {
                                // แสดงข้อมูลเกี่ยวกับโฟลเดอร์ VAT เมื่อพบโฟลเดอร์เดือน-ปีแล้วแต่ไม่พบไฟล์ Excel
                                html += `<div style="margin-top: 15px; padding: 15px; background: #0f172a; border-radius: 5px; border-left: 3px solid #ef4444;">`;
                                html += `<div style="color: #fbbf24; margin-bottom: 10px;">📁 ข้อมูลโฟลเดอร์ VAT:</div>`;
                                html += `<div style="margin-left: 20px; color: #cbd5e1; font-size: 0.9em;">โฟลเดอร์เดือน-ปี: ${result.vat_folder_info.month_year_folder}</div>`;
                                
                                if (result.vat_folder_info.found) {
                                    html += `<div style="margin-left: 20px; margin-top: 10px; color: #10b981;">✅ พบโฟลเดอร์ VAT:</div>`;
                                    if (result.vat_folder_info.folders && result.vat_folder_info.folders.length > 0) {
                                        result.vat_folder_info.folders.forEach(vatFolder => {
                                            html += `<div style="margin-left: 30px; margin-top: 5px; color: #cbd5e1; font-size: 0.9em;">📂 ${vatFolder.name} (${vatFolder.path})</div>`;
                                            if (vatFolder.excel_files && vatFolder.excel_files.length > 0) {
                                                html += `<div style="margin-left: 35px; color: #6ee7b7; font-size: 0.85em;">📄 พบไฟล์ Excel: ${vatFolder.excel_files.join(', ')}</div>`;
                                            } else {
                                                html += `<div style="margin-left: 35px; color: #ef4444; font-size: 0.85em;">❌ ไม่พบไฟล์ Excel OCR ในโฟลเดอร์นี้</div>`;
                                                // แสดงไฟล์ Excel ที่มีอยู่จริงในโฟลเดอร์ VAT
                                                html += `<div style="margin-left: 35px; color: #94a3b8; font-size: 0.85em; margin-top: 5px;">💡 ตรวจสอบไฟล์ Excel ที่มีอยู่ในโฟลเดอร์นี้</div>`;
                                            }
                                        });
                                    }
                                } else {
                                    html += `<div style="margin-left: 20px; margin-top: 10px; color: #ef4444;">❌ ไม่พบโฟลเดอร์ VAT/vat/Vat</div>`;
                                    html += `<div style="margin-left: 20px; margin-top: 5px; color: #94a3b8; font-size: 0.85em;">💡 ระบบจะค้นหาไฟล์ Excel OCR ในโฟลเดอร์เดือน-ปีโดยตรง</div>`;
                                }
                                html += `</div>`;
                            }
                        });
                    }
                    
                    // เพิ่มตัวเลือกเมื่อไม่พบไฟล์ OCR
                    html += `<div style="margin-top: 20px; padding: 20px; background: #1e293b; border-radius: 8px; border: 2px solid #3b82f6;">`;
                    html += `<div style="color: #60a5fa; font-weight: 600; margin-bottom: 15px; font-size: 1.1em;">💡 ตัวเลือกการดำเนินการ:</div>`;
                    html += `<div style="display: flex; gap: 15px; flex-wrap: wrap;">`;
                    
                    // ปุ่ม "ใช้ระบบ OCR" - ใช้ companyValue.value โดยตรงเพื่อหลีกเลี่ยงปัญหา escape
                    const currentCompany = document.getElementById('companyValue')?.value || document.getElementById('companySelect')?.value || company || '';
                    // Escape สำหรับใช้ใน onclick attribute
                    const currentCompanyEscaped = currentCompany.replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/"/g, '&quot;');
                    html += `<button onclick="runOCRForStep4('${taxMonth}', '${currentCompanyEscaped}')" class="btn" style="flex: 1; min-width: 200px; background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%);">`;
                    html += `🤖 ใช้ระบบ OCR<br>`;
                    html += `<span style="font-size: 0.85em; opacity: 0.9;">รัน OCR จากไฟล์ PDF และสร้าง Excel</span>`;
                    html += `</button>`;
                    
                    // ปุ่ม "เลือกไฟล์ Excel"
                    html += `<button onclick="uploadExcelForStep4('${taxMonth}', '${currentCompanyEscaped}')" class="btn" style="flex: 1; min-width: 200px; background: linear-gradient(90deg, #10b981 0%, #059669 100%);">`;
                    html += `📁 เลือกไฟล์ Excel<br>`;
                    html += `<span style="font-size: 0.85em; opacity: 0.9;">เลือกไฟล์ Excel ที่มีอยู่แล้ว</span>`;
                    html += `</button>`;
                    
                    html += `</div>`;
                    html += `</div>`;
                    
                    html += `</div>`;
                    details.innerHTML = html;
                }
            } catch (error) {
                step.classList.remove('active');
                step.classList.add('error');
                status.textContent = 'เกิดข้อผิดพลาด';
                status.className = 'step-status error';
                details.textContent = '❌ เกิดข้อผิดพลาด: ' + error.message;
            }
        }
        
        async function checkStep5(taxMonth, company) {
            const step = document.getElementById('step5');
            const status = document.getElementById('step5Status');
            const details = document.getElementById('step5Details');
            
            // ล้าง HTML เดิมทั้งหมดก่อนเพื่อป้องกันการสร้างซ้ำ
            if (details) {
                details.innerHTML = '';
            }
            
            step.classList.add('active');
            status.textContent = 'กำลังตรวจสอบ...';
            status.className = 'step-status checking';
            
            try {
                // ส่งข้อมูล OCR จาก Step 4 ไปด้วย (ถ้ามี)
                const requestBody = {
                    taxMonth: taxMonth,
                    company: company
                };
                
                // ถ้ามีข้อมูล OCR จาก Step 4 ให้ส่งไปด้วย
                console.log('📊 checkStep5 - step4OCRData:', step4OCRData ? step4OCRData.length : 0, 'items');
                if (step4OCRData && step4OCRData.length > 0) {
                    requestBody.ocrDataFromStep2 = step4OCRData;
                    console.log('📊 Sending ocrDataFromStep2 to API:', step4OCRData.length, 'items');
                } else {
                    console.warn('⚠️ No step4OCRData available for Step 5');
                }
                
                const response = await fetch('/api/auditcheck/compare-purchase-tax-ocr', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(requestBody)
                });
                
                const data = await response.json();
                
                // เก็บ path ของโฟลเดอร์ VAT
                if (data.vatFolderPath) {
                    vatFolderPath = data.vatFolderPath;
                }
                
                // เก็บ comparison results ไว้ในตัวแปร global
                if (data.comparisons) {
                    window.comparisonResults = data.comparisons;
                }
                
                step.classList.remove('active');
                
                if (data.success) {
                    if (data.allMatch) {
                        step.classList.add('completed');
                        status.textContent = 'ข้อมูลตรงกันทั้งหมด';
                        status.className = 'step-status success';
                    } else {
                        step.classList.add('error');
                        status.textContent = 'พบข้อมูลไม่ตรงกัน';
                        status.className = 'step-status error';
                    }
                    
                    // Display comparison table
                    let html = '';
                    
                    // ประกาศตัวแปร uniqueComparisons ไว้ก่อนเพื่อให้ใช้ได้ใน setTimeout
                    let uniqueComparisons = [];
                    
                    // แสดงข้อมูลไฟล์ที่ใช้
                    if (data.purchaseTaxFiles && data.purchaseTaxFiles.length > 0) {
                        html += `<div style="margin-bottom: 15px;">`;
                        html += `<strong style="color: #60a5fa;">📄 ไฟล์ภาษีซื้อที่พบ (${data.purchaseTaxFileCount || 0} ไฟล์):</strong><br>`;
                        html += `<div class="file-list" style="max-height: 100px; margin-top: 5px;">`;
                        data.purchaseTaxFiles.forEach(file => {
                            html += `<div class="file-item success" style="font-size: 0.85em;">${file}</div>`;
                        });
                        html += `</div>`;
                        html += `</div>`;
                    }
                    
                    if (data.ocrFiles && data.ocrFiles.length > 0) {
                        html += `<div style="margin-bottom: 15px;">`;
                        html += `<strong style="color: #60a5fa;">📄 ไฟล์ OCR ที่พบ (${data.ocrFileCount || 0} ไฟล์):</strong><br>`;
                        html += `<div class="file-list" style="max-height: 100px; margin-top: 5px;">`;
                        data.ocrFiles.forEach(file => {
                            html += `<div class="file-item success" style="font-size: 0.85em;">${file}</div>`;
                        });
                        html += `</div>`;
                        html += `</div>`;
                    }
                    
                    if (data.comparisons && data.comparisons.length > 0) {
                        // ลบรายการซ้ำออกจาก comparisons ก่อนใช้งาน
                        // ใช้ unique key จาก invoice_no หรือ document_no เพื่อตรวจสอบซ้ำ
                        const seenKeys = new Set();
                        uniqueComparisons = [];
                        data.comparisons.forEach(comp => {
                            // สร้าง unique key จาก invoice_no หรือ document_no
                            const purchaseInvoiceNo = comp.purchase_data?.invoice_no || comp.invoice_no || '';
                            const ocrDocumentNo = comp.ocr_data?.document_no || comp.document_no || '';
                            const uniqueKey = `${purchaseInvoiceNo}_${ocrDocumentNo}_${comp.match_status || ''}`;
                            
                            if (!seenKeys.has(uniqueKey)) {
                                seenKeys.add(uniqueKey);
                                uniqueComparisons.push(comp);
                            }
                        });
                        
                        
                        // แยกรายการตามสถานะ (ประกาศเป็น let เพื่อให้ใช้ได้ใน setTimeout)
                        let allComparisons = uniqueComparisons;
                        let fullMatchedComparisons = uniqueComparisons.filter(comp => comp.match_status === 'full_match');
                        let partialMatchedComparisons = uniqueComparisons.filter(comp => comp.match_status === 'partial_match');
                        let mismatchedComparisons = uniqueComparisons.filter(comp => comp.match_status === 'no_match');
                        let noOcrDataComparisons = uniqueComparisons.filter(comp => comp.match_status === 'no_ocr_data'); // ไม่มี OCR ใน cache
                        
                        html += `<div style="margin-top: 15px;">`;
                        
                        // Header พร้อมปุ่ม VAT-Info
                        html += `<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">`;
                        html += `<strong style="color: #cbd5e1; font-size: 1.1em;">📊 ผลการเปรียบเทียบ:</strong>`;
                        html += `<a href="https://vsinter.rd.go.th/rd-webcontent-web/#/vatsearch" target="_blank" rel="noopener noreferrer" style="padding: 8px 16px; background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.9em; font-weight: 600; display: flex; align-items: center; gap: 6px; text-decoration: none; transition: all 0.3s;" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(59, 130, 246, 0.4)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';">`;
                        html += `<span style="font-size: 1.1em;">🔍</span> ไปยังหน้า VAT-Info`;
                        html += `</a>`;
                        html += `</div>`;
                        
                        // สร้าง Tabs
                        html += `<div class="comparison-tabs">`;
                        html += `<button class="comparison-tab active" onclick="switchComparisonTab('all')">`;
                        html += `ข้อมูลทั้งหมด <span class="comparison-tab-badge all">${allComparisons.length}</span>`;
                        html += `</button>`;
                        html += `<button class="comparison-tab" onclick="switchComparisonTab('mismatch')">`;
                        html += `ข้อมูลไม่ตรงกัน <span class="comparison-tab-badge mismatch">${mismatchedComparisons.length}</span>`;
                        html += `</button>`;
                        html += `<button class="comparison-tab" onclick="switchComparisonTab('no_ocr_data')">`;
                        html += `ไม่มีข้อมูล OCR <span class="comparison-tab-badge no-ocr-data">${noOcrDataComparisons.length}</span>`;
                        html += `</button>`;
                        html += `<button class="comparison-tab" onclick="switchComparisonTab('partial')">`;
                        html += `ตรงกันบางส่วน <span class="comparison-tab-badge partial">${partialMatchedComparisons.length}</span>`;
                        html += `</button>`;
                        html += `<button class="comparison-tab" onclick="switchComparisonTab('match')">`;
                        html += `ข้อมูลที่ตรงกัน <span class="comparison-tab-badge match">${fullMatchedComparisons.length}</span>`;
                        html += `</button>`;
                        html += `</div>`;
                        
                        // Search Box สำหรับค้นหาเลขที่เอกสารอ้างอิง
                        html += `<div style="margin: 15px 0; padding: 12px; background: #1e293b; border-radius: 8px; border: 1px solid #334155;">`;
                        html += `<div style="display: flex; align-items: center; gap: 10px;">`;
                        html += `<span style="color: #cbd5e1; font-size: 0.95em; font-weight: 600;">🔍 ค้นหาเลขที่เอกสารอ้างอิง:</span>`;
                        html += `<input type="text" id="comparisonReferenceSearch" placeholder="พิมพ์เลขที่เอกสารอ้างอิง..." oninput="filterComparisonByReference(this.value)" style="flex: 1; padding: 8px 12px; background: #0f172a; border: 1px solid #334155; border-radius: 6px; color: #fafafa; font-size: 0.9em; transition: all 0.3s;" onfocus="this.style.borderColor='#3b82f6'; this.style.boxShadow='0 0 0 3px rgba(59, 130, 246, 0.1)';" onblur="this.style.borderColor='#334155'; this.style.boxShadow='none';" />`;
                        html += `<button onclick="clearComparisonSearch()" id="clearSearchBtn" style="padding: 8px 16px; background: #334155; color: #cbd5e1; border: 1px solid #475569; border-radius: 6px; cursor: pointer; font-size: 0.9em; font-weight: 600; transition: all 0.3s; display: none;" onmouseover="this.style.background='#475569';" onmouseout="this.style.background='#334155';">ล้าง</button>`;
                        html += `</div>`;
                        html += `<div id="comparisonSearchResult" style="margin-top: 8px; color: #94a3b8; font-size: 0.85em; display: none;"></div>`;
                        html += `</div>`;
                        
                        // ปุ่มย้ายเอกสารทั้งหมดที่ไม่ตรงกัน
                        const mismatchedCount = mismatchedComparisons.length + partialMatchedComparisons.length;
                        if (mismatchedCount > 0) {
                            html += `<div style="margin: 15px 0; padding: 12px; background: #1e293b; border-radius: 8px; border: 1px solid #334155;">`;
                            html += `<div style="display: flex; justify-content: space-between; align-items: center;">`;
                            html += `<div style="color: #cbd5e1; font-size: 0.95em;">`;
                            html += `📋 พบรายการที่ไม่ตรงกันทั้งหมด <strong style="color: #fbbf24;">${mismatchedCount}</strong> รายการ`;
                            html += `</div>`;
                            html += `<button onclick="moveAllMismatchedDocuments()" style="padding: 10px 20px; background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.9em; font-weight: 600; display: flex; align-items: center; gap: 8px; transition: all 0.3s;" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(245, 158, 11, 0.4)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';">`;
                            html += `<span style="font-size: 1.1em;">📦</span> ย้ายเอกสารทั้งหมดที่ไม่ตรงกัน`;
                            html += `</button>`;
                            html += `</div>`;
                            html += `</div>`;
                        }
                        
                        // เก็บ initial_note ไว้ใน comparisonNotes และ initialNotes ก่อนแสดงผล และเก็บข้อมูล comparisons
                        allComparisonsData = allComparisons; // เก็บข้อมูล comparisons ทั้งหมด
                        allComparisons.forEach((comp, index) => {
                            const noteKey = String(index);
                            if (comp.initial_note) {
                                // เก็บ initial note เพื่อ restore เมื่อยกเลิกการอนุมัติ
                                if (!initialNotes[noteKey]) {
                                    initialNotes[noteKey] = comp.initial_note;
                                }
                                // เก็บใน comparisonNotes ถ้ายังไม่มี
                                if (!comparisonNotes[noteKey]) {
                                    comparisonNotes[noteKey] = comp.initial_note;
                                }
                            }
                            
                            // ตรวจสอบว่า OCR อ่านไม่ได้หรือไม่ (ไม่มีข้อมูล OCR หรือ ocr_data เป็น null/empty)
                            const hasOcrData = comp.ocr_data && Object.keys(comp.ocr_data).length > 0 && comp.ocr_data.document_no;
                            const ocrReadFailed = !hasOcrData;
                            
                            // ถ้า OCR อ่านไม่ได้ ให้เปิดโหมด "ตรวจด้วยตัวเอง" อัตโนมัติ
                            if (ocrReadFailed && !selfCheckMode[index]) {
                                selfCheckMode[index] = true;
                                console.log(`🔍 [Debug] OCR อ่านไม่ได้สำหรับรายการที่ ${index + 1} (เลขที่ใบกำกับ: ${comp.purchase_data?.invoice_no || comp.invoice_no || 'N/A'}) - เปิดโหมด "ตรวจด้วยตัวเอง" อัตโนมัติ`);
                            }
                        });
                        
                        // Tab: ข้อมูลทั้งหมด
                        html += `<div class="comparison-tab-content active" id="comparison-tab-all">`;
                        let allCount = 0;
                        allComparisons.forEach((comp, index) => {
                            html += generateComparisonRowHTML(comp, index, 'all');
                            allCount++;
                        });
                        html += `</div>`;
                        
                        // Tab: ข้อมูลไม่ตรงกัน
                        html += `<div class="comparison-tab-content" id="comparison-tab-mismatch">`;
                        if (mismatchedComparisons.length > 0) {
                            let mismatchCount = 0;
                            mismatchedComparisons.forEach((comp, index) => {
                                const actualIndex = allComparisons.indexOf(comp);
                                html += generateComparisonRowHTML(comp, actualIndex, 'mismatch');
                                mismatchCount++;
                            });
                        } else {
                            html += `<div style="text-align: center; padding: 40px; color: #94a3b8;">`;
                            html += `✅ ไม่มีข้อมูลที่ไม่ตรงกัน`;
                            html += `</div>`;
                        }
                        html += `</div>`;
                        
                        // Tab: ไม่มีข้อมูล OCR
                        html += `<div class="comparison-tab-content" id="comparison-tab-no_ocr_data">`;
                        if (noOcrDataComparisons.length > 0) {
                            let noOcrDataCount = 0;
                            noOcrDataComparisons.forEach((comp, index) => {
                                const actualIndex = allComparisons.indexOf(comp);
                                html += generateComparisonRowHTML(comp, actualIndex, 'no_ocr_data');
                                noOcrDataCount++;
                            });
                        } else {
                            html += `<div style="text-align: center; padding: 40px; color: #94a3b8;">`;
                            html += `✅ ไม่มีรายการที่ไม่มีข้อมูล OCR`;
                            html += `</div>`;
                        }
                        html += `</div>`;
                        
                        // Tab: ตรงกันบางส่วน
                        html += `<div class="comparison-tab-content" id="comparison-tab-partial">`;
                        if (partialMatchedComparisons.length > 0) {
                            let partialCount = 0;
                            partialMatchedComparisons.forEach((comp, index) => {
                                const actualIndex = allComparisons.indexOf(comp);
                                html += generateComparisonRowHTML(comp, actualIndex, 'partial');
                                partialCount++;
                            });
                        } else {
                            html += `<div style="text-align: center; padding: 40px; color: #94a3b8;">`;
                            html += `⚠️ ไม่มีข้อมูลที่ตรงกันบางส่วน`;
                            html += `</div>`;
                        }
                        html += `</div>`;
                        
                        // Tab: ข้อมูลที่ตรงกัน
                        html += `<div class="comparison-tab-content" id="comparison-tab-match">`;
                        if (fullMatchedComparisons.length > 0) {
                            let matchCount = 0;
                            fullMatchedComparisons.forEach((comp, index) => {
                                const actualIndex = allComparisons.indexOf(comp);
                                html += generateComparisonRowHTML(comp, actualIndex, 'match');
                                matchCount++;
                            });
                        } else {
                            html += `<div style="text-align: center; padding: 40px; color: #94a3b8;">`;
                            html += `❌ ไม่มีข้อมูลที่ตรงกัน`;
                            html += `</div>`;
                        }
                        html += `</div>`;
                        
                        // Pagination Controls
                        html += `<div class="comparison-pagination-container" style="margin-top: 20px; padding: 15px; background: #1e293b; border-radius: 8px; border: 1px solid #334155; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">`;
                        
                        // ตัวเลือกแสดงรายการต่อหน้า
                        html += `<div style="display: flex; align-items: center; gap: 10px;">`;
                        html += `<span style="color: #cbd5e1; font-size: 0.9em;">แสดงรายการ:</span>`;
                        html += `<select id="comparisonItemsPerPage" onchange="changeComparisonItemsPerPage(this.value)" style="padding: 6px 12px; background: #0f172a; border: 1px solid #334155; border-radius: 6px; color: #fafafa; font-size: 0.9em; cursor: pointer;">`;
                        html += `<option value="10" ${comparisonPagination.itemsPerPage === 10 ? 'selected' : ''}>10</option>`;
                        html += `<option value="25" ${comparisonPagination.itemsPerPage === 25 ? 'selected' : ''}>25</option>`;
                        html += `<option value="50" ${comparisonPagination.itemsPerPage === 50 ? 'selected' : ''}>50</option>`;
                        html += `<option value="100" ${comparisonPagination.itemsPerPage === 100 ? 'selected' : ''}>100</option>`;
                        html += `</select>`;
                        html += `<span style="color: #94a3b8; font-size: 0.85em;">รายการต่อหน้า</span>`;
                        html += `</div>`;
                        
                        // Pagination Info และ Navigation
                        html += `<div style="display: flex; align-items: center; gap: 15px; flex-wrap: wrap;">`;
                        html += `<div id="comparisonPaginationInfo" style="color: #cbd5e1; font-size: 0.9em;"></div>`;
                        html += `<div id="comparisonPaginationNav" style="display: flex; gap: 5px;"></div>`;
                        html += `</div>`;
                        
                        html += `</div>`;
                        
                        html += `</div>`;
                    } else {
                        html += `<div style="color: #ef4444; margin-top: 15px;">`;
                        html += `⚠️ ไม่พบข้อมูลสำหรับการเปรียบเทียบ`;
                        if (data.debug) {
                            html += `<div style="margin-top: 10px; padding: 10px; background: #1e293b; border-radius: 5px; font-size: 0.9em;">`;
                            html += `<div>📊 จำนวนข้อมูลภาษีซื้อ: ${data.purchaseTaxDataCount || 0}</div>`;
                            html += `<div>📊 จำนวนข้อมูล OCR: ${data.ocrDataCount || 0}</div>`;
                            if (data.debug.purchase_invoice_nos && data.debug.purchase_invoice_nos.length > 0) {
                                html += `<div style="margin-top: 5px;">📋 เลขที่ใบกำกับภาษี (ตัวอย่าง): ${data.debug.purchase_invoice_nos.join(', ')}</div>`;
                            }
                            if (data.debug.ocr_document_nos && data.debug.ocr_document_nos.length > 0) {
                                html += `<div style="margin-top: 5px;">📋 เลขที่เอกสาร OCR (ตัวอย่าง): ${data.debug.ocr_document_nos.join(', ')}</div>`;
                            }
                            html += `</div>`;
                        }
                        html += `</div>`;
                    }
                    
                    // ล้าง HTML เดิมทั้งหมดก่อนเพื่อป้องกันการสร้างซ้ำ
                    if (details) {
                        // ลบ comparison elements ทั้งหมดก่อน (ใช้ data-index แทน id selector)
                        const existingComparisonElements = details.querySelectorAll('.comparison-tabs, .comparison-tab-content, .comparison-row, [data-index]');
                        existingComparisonElements.forEach(el => el.remove());
                        
                        // ใช้ innerHTML = '' เพื่อล้างทั้งหมดก่อน
                        details.innerHTML = '';
                        
                        // รอให้ DOM อัปเดตก่อน
                        await new Promise(resolve => setTimeout(resolve, 10));
                        
                        // ตั้งค่า HTML ใหม่
                        details.innerHTML = html;
                        
                        // ลบ duplicates ทันทีหลังจาก set HTML (ไม่ต้องรอ setTimeout)
                        const removeDuplicatesImmediately = () => {
                            const allTab = document.getElementById('comparison-tab-all');
                            if (allTab) {
                                const rows = Array.from(allTab.querySelectorAll('.comparison-row'));
                                
                                if (rows.length === 0) {
                                    return;
                                }
                                
                                const seenIndices = new Map(); // Map<index, firstRowElement>
                                const duplicatesToRemove = [];
                                
                                rows.forEach((row, idx) => {
                                    let rowIndex = row.getAttribute('data-index');
                                    
                                    // ถ้าไม่มี data-index ให้ข้าม (ไม่ควรลบ)
                                    if (rowIndex === null || rowIndex === undefined || rowIndex === '') {
                                        return;
                                    }
                                    
                                    if (seenIndices.has(rowIndex)) {
                                        // พบ duplicate - เก็บไว้เพื่อลบ (เก็บเฉพาะตัวแรก)
                                        duplicatesToRemove.push(row);
                                    } else {
                                        seenIndices.set(rowIndex, row);
                                    }
                                });
                                
                                // ตรวจสอบว่ามี duplicates จริงๆ และไม่ลบทุกอย่าง
                                if (duplicatesToRemove.length > 0 && duplicatesToRemove.length < rows.length) {
                                    duplicatesToRemove.forEach(row => row.remove());
                                } else if (duplicatesToRemove.length > 0 && duplicatesToRemove.length >= rows.length) {
                                    // ไม่ลบถ้าจะลบทุกอย่าง (ป้องกัน data loss)
                                }
                            }
                        };
                        
                        // รอให้ DOM อัปเดตก่อนตรวจสอบ (เพิ่ม delay เพื่อให้แน่ใจว่า HTML ถูก render แล้ว)
                        setTimeout(removeDuplicatesImmediately, 50);
                        
                        // ตรวจสอบและตั้งค่า active tab ให้ถูกต้อง
                        setTimeout(() => {
                            const allTab = document.getElementById('comparison-tab-all');
                            if (allTab && !allTab.classList.contains('active')) {
                                // ถ้า all tab ไม่ได้ active ให้ตั้งค่าเป็น active
                                document.querySelectorAll('.comparison-tab-content').forEach(content => {
                                    content.classList.remove('active');
                                });
                                    allTab.classList.add('active');
                                    
                                    // อัปเดต tab button
                                    document.querySelectorAll('.comparison-tab').forEach(tab => tab.classList.remove('active'));
                                    const allTabButton = document.querySelector('.comparison-tab[onclick*="switchComparisonTab(\'all\')"]');
                                    if (allTabButton) {
                                        allTabButton.classList.add('active');
                                    }
                                }
                            
                            // อัปเดต pagination หลังจากตั้งค่า tab
                            comparisonPagination.currentTab = 'all';
                            updateComparisonPagination();
                        }, 50);
                        
                        // ตรวจสอบอีกครั้งหลังจาก set HTML
                        setTimeout(() => {
                            // ตรวจสอบและลบ duplicates จากทุก tab
                            const allTabs = ['all', 'mismatch', 'partial', 'match'];
                            allTabs.forEach(tabName => {
                                const tabElement = document.getElementById(`comparison-tab-${tabName}`);
                                if (!tabElement) return;
                                
                                const rows = Array.from(tabElement.querySelectorAll('.comparison-row'));
                                if (rows.length === 0) return;
                                
                                // ตรวจสอบ duplicates โดยใช้ data-index
                                const seenIndices = new Map(); // Map<index, firstRowElement>
                                const duplicatesToRemove = [];
                                
                                rows.forEach((row, idx) => {
                                    let rowIndex = row.getAttribute('data-index');
                                    
                                    // ถ้าไม่มี data-index ให้สร้างจาก index (แต่ต้องระวังว่าอาจทำให้ซ้ำได้)
                                    if (rowIndex === null || rowIndex === undefined || rowIndex === '') {
                                        // ใช้ index จากตำแหน่งใน DOM แทน
                                        rowIndex = String(idx);
                                        row.setAttribute('data-index', rowIndex);
                                    }
                                    
                                    if (seenIndices.has(rowIndex)) {
                                        // พบ duplicate - เก็บไว้เพื่อลบ (เก็บเฉพาะตัวแรก)
                                        duplicatesToRemove.push(row);
                                    } else {
                                        seenIndices.set(rowIndex, row);
                                    }
                                });
                                
                                // ลบ duplicates เฉพาะถ้ามีจริงๆ และต้องไม่ลบทุกอย่าง
                                if (duplicatesToRemove.length > 0 && duplicatesToRemove.length < rows.length) {
                                    duplicatesToRemove.forEach(row => row.remove());
                                }
                            });
                            
                            // ตรวจสอบว่า tab content แสดงผลหรือไม่
                            const activeTab = document.querySelector('.comparison-tab-content.active');
                            if (!activeTab) {
                                const allTab = document.getElementById('comparison-tab-all');
                                if (allTab) {
                                    allTab.classList.add('active');
                                    // อัปเดต tab button
                                    document.querySelectorAll('.comparison-tab').forEach(tab => tab.classList.remove('active'));
                                    const allTabButton = document.querySelector('.comparison-tab[onclick*="switchComparisonTab(\'all\')"]');
                                    if (allTabButton) {
                                        allTabButton.classList.add('active');
                                    }
                                }
                            }
                            
                            // อัปเดต pagination หลังจากตรวจสอบ duplicates
                            updateComparisonPagination();
                        }, 100);
                    }
                    
                    // ตรวจสอบว่าข้อมูลแสดงผลหรือไม่หลังจาก 1 วินาที
                    setTimeout(() => {
                        const activeTab = document.querySelector('.comparison-tab-content.active');
                        const visibleRows = activeTab ? Array.from(activeTab.querySelectorAll('.comparison-row')) : [];
                        
                        if (!activeTab) {
                            // พยายามตั้งค่า all tab เป็น active อีกครั้ง
                            const allTab = document.getElementById('comparison-tab-all');
                            if (allTab) {
                                document.querySelectorAll('.comparison-tab-content').forEach(content => {
                                    content.classList.remove('active');
                                });
                                allTab.classList.add('active');
                                document.querySelectorAll('.comparison-tab').forEach(tab => tab.classList.remove('active'));
                                const allTabButton = document.querySelector('.comparison-tab[onclick*="switchComparisonTab(\'all\')"]');
                                if (allTabButton) {
                                    allTabButton.classList.add('active');
                                }
                            }
                        } else if (visibleRows.length === 0 && data.comparisons && data.comparisons.length > 0) {
                            // ตรวจสอบว่า rows ถูกซ่อนหรือไม่
                            const allRowsInTab = Array.from(activeTab.querySelectorAll('.comparison-row'));
                            if (allRowsInTab.length > 0) {
                                // พยายามแสดง rows ที่ถูกซ่อน
                                allRowsInTab.forEach((row) => {
                                    const style = window.getComputedStyle(row);
                                    if (style.display === 'none' || style.visibility === 'hidden') {
                                        row.style.display = 'block';
                                        row.style.visibility = 'visible';
                                    }
                                });
                            }
                        }
                    }, 1000);
                    
                    // แสดงปุ่มส่งออก Excel เมื่อมีข้อมูล
                    const exportBtn = document.getElementById('exportExcelBtn');
                    if (exportBtn && data.comparisons && data.comparisons.length > 0) {
                        exportBtn.style.display = 'flex';
                    }
                } else {
                    step.classList.add('error');
                    status.textContent = 'เกิดข้อผิดพลาด';
                    status.className = 'step-status error';
                    details.textContent = '❌ เกิดข้อผิดพลาด: ' + (data.error || 'Unknown error');
                }
            } catch (error) {
                step.classList.remove('active');
                step.classList.add('error');
                status.textContent = 'เกิดข้อผิดพลาด';
                status.className = 'step-status error';
                details.textContent = '❌ เกิดข้อผิดพลาด: ' + error.message;
            }
        }
        
        function generateComparisonRowHTML(comp, index, tabName = 'all') {
            const purchaseData = comp.purchase_data || {};
            const ocrData = comp.ocr_data || {};
            const matchDetails = comp.match_details || {};
            
            // ดึงข้อมูลบริษัทจากระบบ
            const companyName = (document.getElementById('companyName')?.textContent || '').trim();
            const companyTaxId = (document.getElementById('companyTaxId')?.textContent || '').trim();
            const companyAddress = (document.getElementById('companyAddress')?.textContent || '').trim();
            
            const buyerName = (ocrData.buyer_name || '').trim();
            const buyerTaxId = (ocrData.buyer_tax_id || '').trim();
            const buyerAddress = (ocrData.buyer_address || ocrData.address || ocrData.address_full || '').trim();
            
            // ใช้ global functions normalizeText และ normalizeAddress ที่กำหนดไว้แล้ว
            
            // คำนวณผลการเปรียบเทียบข้อมูลบริษัท
            let companyDataMatches = 0;
            let companyDataTotal = 0;
            let companyNameMatch = false;
            let companyTaxIdMatch = false;
            let companyAddressMatch = false;
            
            // เปรียบเทียบชื่อ
            if (buyerName && buyerName !== '-' && companyName && companyName !== '-') {
                companyDataTotal++;
                const normalizedBuyerName = normalizeText(buyerName);
                const normalizedCompanyName = normalizeText(companyName);
                
                if (normalizedBuyerName === normalizedCompanyName || 
                    normalizedBuyerName.includes(normalizedCompanyName) || 
                    normalizedCompanyName.includes(normalizedBuyerName)) {
                    companyNameMatch = true;
                    companyDataMatches++;
                } else {
                    const minLength = Math.min(normalizedBuyerName.length, normalizedCompanyName.length);
                    const maxLength = Math.max(normalizedBuyerName.length, normalizedCompanyName.length);
                    if (minLength > 0) {
                        let matchingChars = 0;
                        for (let i = 0; i < minLength; i++) {
                            if (normalizedBuyerName[i] === normalizedCompanyName[i]) {
                                matchingChars++;
                            }
                        }
                        const similarity = matchingChars / maxLength;
                        if (similarity >= 0.8) {
                            companyNameMatch = true;
                            companyDataMatches++;
                        }
                    }
                }
                
                // ตรวจสอบว่าถูกอนุมัติแล้วหรือไม่
                const companyNameApprovalKey = `${index}-company_name_match`;
                const isCompanyNameApproved = comparisonApprovals[companyNameApprovalKey] || false;
                if (isCompanyNameApproved && !companyNameMatch) {
                    companyDataMatches++; // ถ้าถูกอนุมัติแล้วให้นับเป็น match
                }
            }
            
            // เปรียบเทียบเลขประจำตัวผู้เสียภาษี
            if (buyerTaxId && buyerTaxId !== '-' && companyTaxId && companyTaxId !== '-') {
                companyDataTotal++;
                const normalizedBuyerTaxId = buyerTaxId.replace(/\s+/g, '').replace(/[-\s]/g, '');
                const normalizedCompanyTaxId = companyTaxId.replace(/\s+/g, '').replace(/[-\s]/g, '');
                if (normalizedBuyerTaxId === normalizedCompanyTaxId) {
                    companyTaxIdMatch = true;
                    companyDataMatches++;
                }
                
                // ตรวจสอบว่าถูกอนุมัติแล้วหรือไม่
                const taxIdApprovalKey = `${index}-tax_id_match`;
                const isTaxIdApproved = comparisonApprovals[taxIdApprovalKey] || false;
                if (isTaxIdApproved && !companyTaxIdMatch) {
                    companyDataMatches++; // ถ้าถูกอนุมัติแล้วให้นับเป็น match
                }
            }
            
            // เปรียบเทียบที่อยู่
            if (buyerAddress && buyerAddress !== '-' && companyAddress && companyAddress !== '-') {
                companyDataTotal++;
                const normalizedBuyerAddress = normalizeAddress(buyerAddress);
                const normalizedCompanyAddress = normalizeAddress(companyAddress);
                
                if (normalizedBuyerAddress === normalizedCompanyAddress) {
                    companyAddressMatch = true;
                    companyDataMatches++;
                } else {
                    // ฟังก์ชันสำหรับแปลงคำภาษาอังกฤษเป็นภาษาไทย
                    const transliterateToThai = (text) => {
                        const map = {
                            'klongsong': 'คลองสอง',
                            'klong song': 'คลองสอง',
                            'klongluang': 'คลองหลวง',
                            'klong luang': 'คลองหลวง',
                            'pathumthani': 'ปทุมธานี',
                            'pathum thani': 'ปทุมธานี'
                        };
                        let result = text.toLowerCase();
                        for (const [eng, thai] of Object.entries(map)) {
                            result = result.replace(new RegExp(eng, 'gi'), thai);
                        }
                        return result;
                    };
                    
                    const extractKeyParts = (addr) => {
                        const parts = [];
                        const addrNorm = (addr || '').replace(/^เลขที่\s*/i, '').trim();
                        const addrLower = addrNorm.toLowerCase();
                        
                        // หาเลขที่บ้าน (ต้องตรงกันเป๊ะ)
                        const houseNoPatterns = [
                            /\d+\/\d+/,  // เช่น 5/29
                            /\b\d{2,}\b/  // เช่น 129 (เลขที่บ้าน 2 หลักขึ้นไป)
                        ];
                        for (const pattern of houseNoPatterns) {
                            const matches = addrNorm.match(pattern);
                            if (matches) {
                                parts.push(...matches.map(m => m.trim()));
                                break; // หาแค่ตัวแรก
                            }
                        }
                        
                        // หาเลขไปรษณีย์
                        const postalCode = addrNorm.match(/\b\d{5}\b/g);
                        if (postalCode) parts.push(...postalCode);
                        
                        // หาหมู่ที่ (รองรับทั้ง M0015, M15, หมู่ที่ 15)
                        const mooMatch = addrNorm.match(/(?:m0*|หมู่ที่\s*)(\d+)/i);
                        if (mooMatch) {
                            parts.push(`หมู่${mooMatch[1]}`);
                        }
                        
                        // หาตำบล อำเภอ จังหวัด (รองรับทั้งไทยและอังกฤษ)
                        const locations = {
                            'ตำบล': addrLower.match(/ตำบล\s*([^\s,]+)/i),
                            'อำเภอ': addrLower.match(/อำเภอ\s*([^\s,]+)/i),
                            'จังหวัด': addrLower.match(/จังหวัด\s*([^\s,]+)/i),
                            'tambon': addrLower.match(/tambon\s*([^\s,]+)/i),
                            'amphoe': addrLower.match(/amphoe\s*([^\s,]+)/i),
                            'province': addrLower.match(/province\s*([^\s,]+)/i)
                        };
                        
                        // หาชื่อตำบล อำเภอ จังหวัด (โดยตรง)
                        const locationNames = [
                            'คลองสอง', 'klongsong', 'klong song',
                            'คลองหลวง', 'klongluang', 'klong luang',
                            'ปทุมธานี', 'pathumthani', 'pathum thani'
                        ];
                        
                        locationNames.forEach(name => {
                            const thaiName = transliterateToThai(name);
                            if (addrLower.includes(name.toLowerCase()) || addrLower.includes(thaiName)) {
                                parts.push(thaiName);
                            }
                        });
                        
                        return parts;
                    };
                    
                    const buyerKeyParts = extractKeyParts(buyerAddress);
                    const companyKeyParts = extractKeyParts(companyAddress);
                    
                    // แยกเลขที่บ้านออกมาเปรียบเทียบแยก
                    const buyerHouseNo = buyerKeyParts.find(p => /^\d+/.test(p));
                    const companyHouseNo = companyKeyParts.find(p => /^\d+/.test(p));
                    
                    // ถ้าเลขที่บ้านไม่ตรงกัน ให้ถือว่าไม่ตรงกัน (ยกเว้นกรณีที่ไม่มีเลขที่บ้าน)
                    if (buyerHouseNo && companyHouseNo) {
                        // แปลง 5/29 เป็น 529 สำหรับเปรียบเทียบ
                        const normalizeHouseNo = (no) => no.replace(/\//g, '').replace(/\D/g, '');
                        const buyerNoNorm = normalizeHouseNo(buyerHouseNo);
                        const companyNoNorm = normalizeHouseNo(companyHouseNo);
                        
                        // ถ้าเลขที่บ้านไม่ตรงกันเลย ให้ถือว่าไม่ตรงกัน
                        if (buyerNoNorm !== companyNoNorm && 
                            !buyerNoNorm.includes(companyNoNorm) && 
                            !companyNoNorm.includes(buyerNoNorm)) {
                            // ไม่ตรงกัน - ไม่ต้องทำอะไร (companyAddressMatch ยังเป็น false)
                        } else {
                            // เลขที่บ้านตรงกันหรือคล้ายกัน - เปรียบเทียบส่วนอื่นต่อ
                            const otherBuyerParts = buyerKeyParts.filter(p => p !== buyerHouseNo);
                            const otherCompanyParts = companyKeyParts.filter(p => p !== companyHouseNo);
                            const matchingParts = otherBuyerParts.filter(part => 
                                otherCompanyParts.some(cp => {
                                    const partNorm = transliterateToThai(part);
                                    const cpNorm = transliterateToThai(cp);
                                    return cpNorm === partNorm || cpNorm.includes(partNorm) || partNorm.includes(cpNorm);
                                })
                            );
                            
                            // ต้องมีส่วนอื่นๆ ตรงกันอย่างน้อย 3 ส่วน (เช่น หมู่ที่, ตำบล, อำเภอ, จังหวัด, รหัสไปรษณีย์)
                            if (matchingParts.length >= 3) {
                                companyAddressMatch = true;
                                companyDataMatches++;
                            }
                        }
                    } else {
                        // ไม่มีเลขที่บ้าน - เปรียบเทียบส่วนอื่น
                        const matchingParts = buyerKeyParts.filter(part => 
                            companyKeyParts.some(cp => {
                                const partNorm = transliterateToThai(part);
                                const cpNorm = transliterateToThai(cp);
                                return cpNorm === partNorm || cpNorm.includes(partNorm) || partNorm.includes(cpNorm);
                            })
                        );
                        const matchRatio = buyerKeyParts.length > 0 ? matchingParts.length / Math.max(buyerKeyParts.length, companyKeyParts.length) : 0;
                        
                        // ต้องมีส่วนที่ตรงกันอย่างน้อย 70% หรืออย่างน้อย 3 ส่วน
                        if (matchRatio >= 0.7 || (matchingParts.length >= 3 && buyerKeyParts.length > 0)) {
                            companyAddressMatch = true;
                            companyDataMatches++;
                        }
                    }
                }
                
                // ตรวจสอบว่าถูกอนุมัติแล้วหรือไม่
                const addressApprovalKey = `${index}-address_match`;
                const isAddressApproved = comparisonApprovals[addressApprovalKey] || false;
                if (isAddressApproved && !companyAddressMatch) {
                    companyDataMatches++; // ถ้าถูกอนุมัติแล้วให้นับเป็น match
                }
            }
            
            // คำนวณสถานะเอกสาร (เดิม) - แยกจากข้อมูลบริษัท
            const documentMatchedCount = comp.matched_count || 0;
            const documentTotalCount = comp.total_count || 0;
            
            // กำหนด match_status ของเอกสาร
            let documentMatchStatus = comp.match_status || (comp.match ? 'full_match' : 'no_match');
            
            // คำนวณสถานะข้อมูลบริษัท (ใหม่) - แยกจากเอกสาร
            let companyDataMatchStatus = 'no_match';
            if (companyDataTotal > 0) {
                if (companyDataMatches === companyDataTotal) {
                    companyDataMatchStatus = 'full_match';
                } else if (companyDataMatches > 0) {
                    companyDataMatchStatus = 'partial_match';
                } else {
                    companyDataMatchStatus = 'no_match';
                }
            }
            
            // กำหนดสีและข้อความตาม match_status ของเอกสาร
            let documentMatchClass, documentMatchText, documentMatchColor;
            if (documentMatchStatus === 'full_match') {
                documentMatchClass = 'match';
                documentMatchText = 'ตรงกัน';
                documentMatchColor = '#10b981'; // สีเขียว
            } else if (documentMatchStatus === 'partial_match') {
                documentMatchClass = 'partial-match';
                documentMatchText = `ตรงกันบางส่วน (${documentMatchedCount}/${documentTotalCount})`;
                documentMatchColor = '#fbbf24'; // สีเหลือง
            } else {
                documentMatchClass = 'mismatch';
                documentMatchText = 'ไม่ตรงกัน';
                documentMatchColor = '#ef4444'; // สีแดง
            }
            
            // กำหนดสีและข้อความตาม match_status ของข้อมูลบริษัท
            let companyDataMatchClass, companyDataMatchText, companyDataMatchColor;
            if (companyDataTotal > 0) {
                if (companyDataMatchStatus === 'full_match') {
                    companyDataMatchClass = 'match';
                    // ถ้าตรงกันหมดแล้ว ให้แสดงแค่ "ตรงกัน" โดยไม่ต้องแสดงตัวเลข
                    companyDataMatchText = `ตรงกัน`;
                    companyDataMatchColor = '#10b981'; // สีเขียว
                } else if (companyDataMatchStatus === 'partial_match') {
                    companyDataMatchClass = 'partial-match';
                    companyDataMatchText = `ตรงกันบางส่วน (${companyDataMatches}/${companyDataTotal})`;
                    companyDataMatchColor = '#fbbf24'; // สีเหลือง
                } else {
                    companyDataMatchClass = 'mismatch';
                    companyDataMatchText = `ไม่ตรงกัน (${companyDataMatches}/${companyDataTotal})`;
                    companyDataMatchColor = '#ef4444'; // สีแดง
                }
            }
            
            let html = '';
            
            // ใช้ tabName และ index เพื่อสร้าง unique ID สำหรับแต่ละ tab (แก้ปัญหา duplicate IDs)
            const uniqueId = `comparison-row-${tabName}-${index}`;
            // ดึง reference number สำหรับใช้ในการค้นหา
            const referenceNoForSearch = purchaseData?.reference_no || comp.invoice_no || ocrData?.document_no || '';
            html += `<div class="comparison-row" id="${uniqueId}" data-index="${index}" data-tab="${tabName}" data-reference="${referenceNoForSearch.toLowerCase()}">`;
            
            // Header (คลิกได้)
            html += `<div class="comparison-row-header" onclick="toggleComparisonRow(${index})">`;
            html += `<div class="comparison-row-header-left">`;
            html += `<div class="comparison-row-number">${index + 1}</div>`;
            html += `<div class="comparison-row-title">`;
            // แสดงชื่อบริษัทและเลขที่อ้างอิงจากรายงานภาษีซื้อ
            const contactCompanyName = purchaseData?.contact || ocrData?.company_name || '-';
            const referenceNo = purchaseData?.reference_no || comp.invoice_no || ocrData?.document_no || `รายการที่ ${index + 1}`;
            html += `<div class="comparison-row-title-main">${contactCompanyName}</div>`;
            html += `<div class="comparison-row-title-sub" style="color: #94a3b8; font-size: 0.85em; margin-top: 2px;">เลขที่อ้างอิง: ${referenceNo}</div>`;
            // แสดงชื่อไฟล์ OCR (ถ้ามี)
            const ocrFilename = ocrData?.filename || ocrData?.old_filename || null;
            if (ocrFilename) {
                html += `<div class="comparison-row-title-sub" style="color: #60a5fa; font-size: 0.85em; margin-top: 2px;">📄 ไฟล์ OCR: ${ocrFilename}</div>`;
            }
            html += `<div class="comparison-row-title-sub">`;
            if (comp.purchase_data && comp.ocr_data) {
                html += `ภาษีซื้อ: ${comp.purchaseTax || '0.00'} | OCR: ${comp.ocrFile || '0.00'}`;
            } else if (comp.purchase_data) {
                html += `ภาษีซื้อ: ${comp.purchaseTax || '0.00'} | OCR: ไม่พบข้อมูล`;
            } else if (comp.ocr_data) {
                html += `ภาษีซื้อ: ไม่พบข้อมูล | OCR: ${comp.ocrFile || '0.00'}`;
            }
            html += `</div>`;
            html += `</div>`;
            html += `</div>`;
            
            // แสดงสถานะเอกสาร (เดิม)
            html += `<div class="comparison-row-status ${documentMatchClass}" style="color: ${documentMatchColor}; background-color: ${documentMatchColor}20; border: 1px solid ${documentMatchColor}; margin-right: 8px;">${documentMatchText}</div>`;
            
            // แสดงสถานะข้อมูลบริษัท (ใหม่) - ถ้ามีข้อมูลบริษัท
            if (companyDataTotal > 0) {
                html += `<div class="comparison-row-status ${companyDataMatchClass}" style="color: ${companyDataMatchColor}; background-color: ${companyDataMatchColor}20; border: 1px solid ${companyDataMatchColor}; margin-right: 8px;" title="สถานะข้อมูลบริษัท (ชื่อ, เลขประจำตัวผู้เสียภาษี, ที่อยู่)">`;
                html += `<span style="font-size: 0.9em;">🏢</span> `;
                html += `${companyDataMatchText}`;
                html += `</div>`;
            }
            
            html += `<div class="comparison-row-toggle">▼</div>`;
            html += `</div>`;
            
            // Content (ซ่อนไว้ก่อน)
            html += `<div class="comparison-row-content">`;
            html += `<div class="comparison-content-wrapper">`;
            
            // ตรวจสอบว่า OCR อ่านไม่ได้หรือไม่ (ไม่มีข้อมูล OCR หรือ ocr_data เป็น null/empty)
            // ตรวจสอบหลายเงื่อนไข:
            // 1. comp.ocr_data เป็น null หรือ undefined
            // 2. comp.ocr_data เป็น object ว่างเปล่า
            // 3. comp.ocr_data ไม่มี document_no (เลขที่เอกสาร)
            // 4. comp.match_status === 'no_match' และไม่มี ocr_data
            const hasOcrData = comp.ocr_data && 
                               typeof comp.ocr_data === 'object' && 
                               Object.keys(comp.ocr_data).length > 0 && 
                               (comp.ocr_data.document_no || comp.ocr_data.filename);
            const ocrReadFailed = !hasOcrData || comp.match_status === 'no_match';
            
            // ถ้า OCR อ่านไม่ได้ ให้เปิดโหมด "ตรวจด้วยตัวเอง" อัตโนมัติ
            if (ocrReadFailed && !selfCheckMode[index]) {
                selfCheckMode[index] = true;
                const invoiceNo = comp.purchase_data?.invoice_no || comp.invoice_no || 'N/A';
                console.log(`🔍 [Debug] OCR อ่านไม่ได้สำหรับรายการที่ ${index + 1} (เลขที่ใบกำกับ: ${invoiceNo}) - เปิดโหมด "ตรวจด้วยตัวเอง" อัตโนมัติ`);
                console.log(`   - ocr_data:`, comp.ocr_data);
                console.log(`   - match_status:`, comp.match_status);
            }
            
            // ตรวจสอบว่า row นี้อยู่ในโหมด "ตรวจด้วยตัวเอง" หรือไม่
            const isSelfCheckMode = selfCheckMode[index] || false;
            
            // Container สำหรับฝั่งภาษีซื้อและไฟล์ OCR
            html += `<div class="comparison-sides-container">`;
            
            // ฝั่งภาษีซื้อ (เพิ่ม class self-check-mode ถ้าอยู่ในโหมด "ตรวจด้วยตัวเอง")
            html += `<div class="comparison-side purchase-tax${isSelfCheckMode ? ' self-check-mode' : ''}">`;
            html += `<div class="comparison-side-header">📄 ภาษีซื้อ${isSelfCheckMode ? ' (ตรวจด้วยตัวเอง)' : ''}</div>`;
            
            if (comp.purchase_data) {
                // ฟิลด์ที่สามารถอนุมัติได้
                const approvableFields = [
                    { key: 'document_no_match', label: 'เลขที่ใบกำกับภาษี', value: purchaseData.invoice_no || '-' },
                    { key: 'date_match', label: 'วันที่ใบกำกับภาษี', value: purchaseData.invoice_date || '-' },
                    { key: 'company_name_match', label: 'ผู้ติดต่อ', value: purchaseData.contact || '-' },
                    { key: 'tax_id_match', label: 'เลขทะเบียนผู้เสียภาษี', value: purchaseData.tax_id || '-' },
                    { key: 'branch_match', label: 'สาขา/สำนักงานใหญ่', value: purchaseData.branch || '-' },
                    { key: 'reference_no_match', label: 'เลขที่เอกสารอ้างอิง', value: purchaseData.reference_no || '-' },
                    { key: 'amount_before_vat_match', label: 'รายการภาษี 7%', value: (purchaseData.tax_7 || 0).toLocaleString('th-TH', {minimumFractionDigits: 2, maximumFractionDigits: 2}) },
                    { key: 'vat_amount_match', label: 'ภาษีมูลค่าเพิ่ม', value: (purchaseData.vat || 0).toLocaleString('th-TH', {minimumFractionDigits: 2, maximumFractionDigits: 2}) },
                    { key: 'total_amount_match', label: 'มูลค่ารวมภาษี', value: comp.purchaseTax || '0.00' },
                    { key: 'document_type_match', label: 'ประเภทใบกำกับ', value: purchaseData.invoice_type || '-' }
                ];
                
                // แสดงฟิลด์ที่สามารถอนุมัติได้
                approvableFields.forEach(field => {
                    const isMatch = matchDetails?.[field.key];
                    const isApproved = comparisonApprovals[`${index}-${field.key}`] || false;
                    
                    html += `<div class="comparison-field" style="position: relative;" data-field-key="${field.key}" data-field-index="${index}">`;
                    html += `<span class="comparison-field-label">${field.label}:</span>`;
                    html += `<div style="display: flex; align-items: center; gap: 8px;">`;
                    
                    // ถ้าอยู่ในโหมด "ตรวจด้วยตัวเอง":
                    // - เลขที่ใบกำกับภาษี (document_no_match) ให้แสดงเป็นสีเขียว
                    // - รายการอื่นๆ ให้แสดงเป็นสีแดง
                    let valueColor, valueFontWeight;
                    if (isSelfCheckMode) {
                        if (field.key === 'document_no_match') {
                            // เลขที่ใบกำกับภาษี: สีเขียว
                            valueColor = '#10b981';
                            valueFontWeight = '400';
                        } else {
                            // รายการอื่นๆ: สีแดง
                            valueColor = '#ef4444';
                            valueFontWeight = '600';
                        }
                    } else {
                        // โหมดปกติ: ใช้ logic เดิม
                        valueColor = isMatch ? '#10b981' : (!isMatch && !isApproved ? '#ef4444' : '#10b981');
                        valueFontWeight = (!isMatch && !isApproved ? '600' : '400');
                    }
                    
                    html += `<span class="comparison-field-value ${isMatch ? 'match' : (isApproved ? 'approved' : 'mismatch')}" style="color: ${valueColor}; font-weight: ${valueFontWeight};">${field.value}</span>`;
                    
                    // ปุ่มอนุมัติ: ถ้าอยู่ในโหมด "ตรวจด้วยตัวเอง" ให้แสดงทุก field (ไม่ว่าจะ match หรือไม่ match), ถ้าไม่ใช่ให้แสดงเฉพาะ field ที่ไม่ match
                    const shouldShowApproveButton = isSelfCheckMode ? true : (!isMatch && !isApproved);
                    
                    // ในโหมด "ตรวจด้วยตัวเอง": เลขที่ใบกำกับภาษีไม่ต้องแสดงปุ่มอนุมัติ (เพราะเป็นสีเขียวอยู่แล้ว)
                    // แต่รายการอื่นๆ ให้แสดงปุ่มอนุมัติ
                    let shouldShowButton = shouldShowApproveButton && !isApproved;
                    if (isSelfCheckMode && field.key === 'document_no_match') {
                        shouldShowButton = false; // ไม่แสดงปุ่มอนุมัติสำหรับเลขที่ใบกำกับภาษี
                    }
                    
                    if (shouldShowButton) {
                        html += `<button onclick="approveField(${index}, '${field.key}', '${field.label}')" data-field-key="${field.key}" data-field-index="${index}" style="padding: 4px 10px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.8em; font-weight: 600; display: flex; align-items: center; gap: 4px; transition: all 0.3s; white-space: nowrap;" onmouseover="this.style.transform='scale(1.05)'; this.style.boxShadow='0 2px 8px rgba(16, 185, 129, 0.4)';" onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='none';" title="อนุมัติความไม่ตรงกันนี้">`;
                        html += `<span style="font-size: 1em;">✓</span> อนุมัติ`;
                        html += `</button>`;
                    } else if (isApproved) {
                        html += `<button onclick="cancelApproval(${index}, '${field.key}', '${field.label}')" data-field-key="${field.key}" data-field-index="${index}" style="padding: 4px 10px; background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.8em; font-weight: 600; display: flex; align-items: center; gap: 4px; transition: all 0.3s; white-space: nowrap;" onmouseover="this.style.transform='scale(1.05)'; this.style.boxShadow='0 2px 8px rgba(239, 68, 68, 0.4)';" onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='none';" title="ยกเลิกการอนุมัติ">`;
                        html += `<span style="font-size: 1em;">✕</span> ยกเลิก`;
                        html += `</button>`;
                    }
                    
                    html += `</div>`;
                    html += `</div>`;
                });
                
                // ฟิลด์ที่ไม่สามารถอนุมัติได้ (แสดงอย่างเดียว)
                html += `<div class="comparison-field">`;
                html += `<span class="comparison-field-label">รายการยกเว้นภาษี:</span>`;
                const exemptColor = isSelfCheckMode ? '#ef4444' : '';
                html += `<span class="comparison-field-value" style="${exemptColor ? `color: ${exemptColor}; font-weight: 600;` : ''}">${(purchaseData.exempt || 0).toLocaleString('th-TH', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>`;
                html += `</div>`;
                
                html += `<div class="comparison-field">`;
                html += `<span class="comparison-field-label">รายการภาษี 0%:</span>`;
                const tax0Color = isSelfCheckMode ? '#ef4444' : '';
                html += `<span class="comparison-field-value" style="${tax0Color ? `color: ${tax0Color}; font-weight: 600;` : ''}">${(purchaseData.tax_0 || 0).toLocaleString('th-TH', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>`;
                html += `</div>`;
                
                // ช่องหมายเหตุ
                const initialNote = comp.initial_note || '';
                const noteKey = String(index);
                
                // เก็บ initial note ไว้เพื่อ restore เมื่อยกเลิกการอนุมัติ
                if (!initialNotes[noteKey] && initialNote) {
                    initialNotes[noteKey] = initialNote;
                }
                
                if (!comparisonNotes[noteKey] && initialNote) {
                    comparisonNotes[noteKey] = initialNote;
                }
                const currentNote = comparisonNotes[noteKey] || initialNote;
                
                html += `<div class="comparison-field" style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #334155;">`;
                html += `<span class="comparison-field-label">📝 หมายเหตุ:</span>`;
                html += `<textarea id="note-${index}" class="note-textarea" placeholder="กรอกหมายเหตุ (ถ้ามี)..." style="width: 100%; min-height: 60px; padding: 8px; background: #0f172a; border: 1px solid #334155; border-radius: 4px; color: #fafafa; font-size: 0.9em; font-family: inherit; resize: vertical;" onchange="saveNote(${index}, this.value)">${currentNote}</textarea>`;
                html += `</div>`;
                
                // ปุ่มดู PDF และปุ่มอื่นๆ (ถ้ามีเลขที่เอกสารอ้างอิง)
                const referenceNo = purchaseData.reference_no || comp.invoice_no || ocrData.document_no || '';
                if (referenceNo) {
                    const isInvalid = invalidDocuments[index] || false;
                    html += `<div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #334155; display: flex; gap: 10px; flex-wrap: wrap;">`;
                    
                    // ปุ่มดูไฟล์ (PDF/JPG/PNG)
                    html += `<button onclick="viewPdfPreview('${referenceNo}', ${index})" style="flex: 1; min-width: 120px; padding: 10px; background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.9em; font-weight: 600; transition: all 0.3s; display: flex; align-items: center; justify-content: center; gap: 8px;" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(59, 130, 246, 0.4)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';">`;
                    html += `<span style="font-size: 1.1em;">📄</span> ดูไฟล์`;
                    html += `</button>`;
                    
                    // ปุ่มตรวจสอบเพิ่ม
                    html += `<button onclick="moveDocumentToReview('${referenceNo}', ${index})" style="flex: 1; min-width: 120px; padding: 10px; background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.9em; font-weight: 600; transition: all 0.3s; display: flex; align-items: center; justify-content: center; gap: 8px;" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(245, 158, 11, 0.4)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';">`;
                    html += `<span style="font-size: 1.1em;">📋</span> ตรวจสอบเพิ่ม`;
                    html += `</button>`;
                    
                    // ปุ่มเอกสารนี้ใช้งานไม่ได้
                    html += `<button onclick="markDocumentAsInvalid(${index}, '${referenceNo}')" style="flex: 1; min-width: 120px; padding: 10px; background: linear-gradient(135deg, ${isInvalid ? '#dc2626' : '#ef4444'} 0%, ${isInvalid ? '#991b1b' : '#dc2626'} 100%); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.9em; font-weight: 600; transition: all 0.3s; display: flex; align-items: center; justify-content: center; gap: 8px; ${isInvalid ? 'opacity: 0.7;' : ''}" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(239, 68, 68, 0.4)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';">`;
                    html += `<span style="font-size: 1.1em;">${isInvalid ? '✓' : '❌'}</span> ${isInvalid ? 'ใช้งานไม่ได้แล้ว' : 'เอกสารนี้ใช้งานไม่ได้'}`;
                    html += `</button>`;
                    
                    // ปุ่มตรวจด้วยตัวเอง
                    const isSelfCheck = selfCheckMode[index] || false;
                    html += `<button onclick="toggleSelfCheckMode(${index}, '${referenceNo}')" style="flex: 1; min-width: 120px; padding: 10px; background: linear-gradient(135deg, ${isSelfCheck ? '#8b5cf6' : '#a855f7'} 0%, ${isSelfCheck ? '#7c3aed' : '#9333ea'} 100%); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.9em; font-weight: 600; transition: all 0.3s; display: flex; align-items: center; justify-content: center; gap: 8px; ${isSelfCheck ? 'opacity: 0.9; border: 2px solid #a855f7;' : ''}" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(168, 85, 247, 0.4)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';">`;
                    html += `<span style="font-size: 1.1em;">${isSelfCheck ? '✓' : '🔍'}</span> ${isSelfCheck ? 'กำลังตรวจด้วยตัวเอง' : 'ตรวจด้วยตัวเอง'}`;
                    html += `</button>`;
                    
                    // ปุ่มลบรายการ
                    html += `<button onclick="removeComparisonItem(${index}, '${referenceNo}')" style="flex: 1; min-width: 120px; padding: 10px; background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.9em; font-weight: 600; transition: all 0.3s; display: flex; align-items: center; justify-content: center; gap: 8px;" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(107, 114, 128, 0.4)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';">`;
                    html += `<span style="font-size: 1.1em;">🗑️</span> ลบรายการ`;
                    html += `</button>`;
                    
                    html += `</div>`;
                }
            } else {
                html += `<div style="color: #ef4444; text-align: center; padding: 20px;">ไม่พบข้อมูล</div>`;
            }
            
            html += `</div>`; // ปิดฝั่งภาษีซื้อ
            
            // ฝั่ง OCR (ย้ายมาด้านขวาบน)
            html += `<div class="comparison-side ocr">`;
            html += `<div class="comparison-side-header">🤖 ไฟล์ OCR</div>`;
            
            // ตรวจสอบอีกครั้งว่า OCR อ่านได้หรือไม่ (สำหรับแสดงผล)
            const hasOcrDataForDisplay = comp.ocr_data && 
                                         typeof comp.ocr_data === 'object' && 
                                         Object.keys(comp.ocr_data).length > 0 && 
                                         (comp.ocr_data.document_no || comp.ocr_data.filename || comp.ocr_data.company_name);
            
            if (hasOcrDataForDisplay) {
                // ตรวจสอบว่าชื่อบริษัทเป็น "บมจ.ธนาคารกสิกรไทย" หรือไม่
                const isKasikornBank = ocrData.company_name && (
                    ocrData.company_name.includes('บมจ.ธนาคารกสิกรไทย') || 
                    ocrData.company_name.includes('ธนาคารกสิกรไทย') || 
                    ocrData.company_name.includes('กสิกรไทย')
                );
                
                // ตรวจสอบว่าชื่อบริษัทเป็น "มายออเดอร์ อินเทลลิเจนซ์" หรือไม่
                const isMyOrderIntelligence = ocrData.company_name && (
                    ocrData.company_name.includes('มายออเดอร์') || 
                    ocrData.company_name.includes('MyOrder') || 
                    ocrData.company_name.includes('MYORDER')
                );
                
                // สำหรับบมจ.ธนาคารกสิกรไทย: ดึงค่าธรรมเนียมมาเป็นยอดก่อนภาษีมูลค่าเพิ่ม (ถ้ายังไม่มี)
                if (isKasikornBank && (!ocrData.amount_before_vat || ocrData.amount_before_vat === 0)) {
                    // ค้นหาค่าธรรมเนียมจากรายการสินค้าหรือข้อมูลอื่นๆ
                    if (ocrData.items && Array.isArray(ocrData.items) && ocrData.items.length > 0) {
                        // ลองหาค่าธรรมเนียมจากรายการสินค้า
                        for (const item of ocrData.items) {
                            const itemName = (item['รายการ'] || item['description'] || item['รายการสินค้า'] || '').toLowerCase();
                            if (itemName.includes('ค่าธรรมเนียม') || itemName.includes('commission') || itemName.includes('fee')) {
                                const itemAmount = parseFloat((item['จำนวนเงิน'] || item['amount'] || '0').toString().replace(/,/g, '')) || 0;
                                if (itemAmount > 0) {
                                    ocrData.amount_before_vat = itemAmount;
                                    console.log(`🏦 [ดีบัค บมจ.ธนาคารกสิกรไทย] พบค่าธรรมเนียมจากรายการสินค้า: ${itemAmount}`);
                                    break;
                                }
                            }
                        }
                    }
                }
                
                // สำหรับมายออเดอร์ อินเทลลิเจนซ์: แปลงรายการสินค้าเป็น 2 บรรทัด
                let myOrderLine1 = null, myOrderLine2 = null, hasMyOrderSplit = false;
                if (isMyOrderIntelligence && ocrData.items && Array.isArray(ocrData.items) && ocrData.items.length > 0) {
                    // หารายการ "ค่าบริการเรียกเก็บเงินปลายทาง" (มีภาษีมูลค่าเพิ่ม)
                    const serviceItem = ocrData.items.find(item => {
                        const itemName = (item['รายการ'] || item['description'] || item['รายการสินค้า'] || '').toLowerCase();
                        return itemName.includes('ค่าบริการเรียกเก็บเงินปลายทาง') || itemName.includes('cod');
                    });
                    
                    // หารายการ "ค่าขนส่งภายในประเทศ" (ไม่มีภาษีมูลค่าเพิ่ม)
                    const shippingItem = ocrData.items.find(item => {
                        const itemName = (item['รายการ'] || item['description'] || item['รายการสินค้า'] || '').toLowerCase();
                        return itemName.includes('ค่าขนส่งภายในประเทศ') || itemName.includes('shipping');
                    });
                    
                    if (serviceItem && shippingItem) {
                        // รายการที่ 1: ค่าบริการเรียกเก็บเงินปลายทาง (มีภาษีมูลค่าเพิ่ม)
                        // ยอดก่อนภาษี = ราคาต่อหน่วย
                        // ยอดภาษี = ภาษีมูลค่าเพิ่มจาก OCR
                        // ยอดรวม = จำนวนเงิน
                        const serviceBeforeVat = parseFloat((serviceItem['ราคาต่อหน่วย'] || serviceItem['unit_price'] || serviceItem['ราคา'] || serviceItem['price'] || '0').toString().replace(/,/g, '')) || 0;
                        const vatAmountFromOCR = ocrData.vat_amount || 0;
                        const serviceTotal = parseFloat((serviceItem['จำนวนเงิน'] || serviceItem['amount'] || '0').toString().replace(/,/g, '')) || 0;
                        
                        myOrderLine1 = {
                            amount_before_vat: serviceBeforeVat,
                            vat_amount: vatAmountFromOCR,
                            total_amount: serviceTotal
                        };
                        
                        // รายการที่ 2: ค่าขนส่งภายในประเทศ (ไม่มีภาษีมูลค่าเพิ่ม)
                        // ยอดก่อนภาษี = จำนวนเงิน
                        // ยอดภาษี = 0
                        // ยอดรวม = จำนวนเงิน
                        const shippingAmount = parseFloat((shippingItem['จำนวนเงิน'] || shippingItem['amount'] || '0').toString().replace(/,/g, '')) || 0;
                        
                        myOrderLine2 = {
                            amount_before_vat: shippingAmount,
                            vat_amount: 0,
                            total_amount: shippingAmount
                        };
                        
                        hasMyOrderSplit = true;
                        console.log(`📦 [ดีบัค มายออเดอร์ อินเทลลิเจนซ์] รายการที่ 1: ${serviceBeforeVat} + ${vatAmountFromOCR} = ${serviceTotal}`);
                        console.log(`📦 [ดีบัค มายออเดอร์ อินเทลลิเจนซ์] รายการที่ 2: ${shippingAmount} (ไม่มีภาษี)`);
                    }
                }
                
                // คำนวณยอดหลังบวกภาษีมูลค่าเพิ่มเสมอ (ไม่ใช้ค่าจาก OCR สำหรับกรณีปกติ)
                const amountBeforeVat = ocrData.amount_before_vat || 0;
                const vatAmount = ocrData.vat_amount || 0;
                
                // ตรวจสอบกรณีพิเศษ
                const isCustomsDepartment = ocrData.company_name && (ocrData.company_name.includes('กรมศุลกากร') || ocrData.company_name.includes('กรมศุล'));
                
                let ocrTotalAmount = 0;
                let isAutoCalculated = false;
                
                // รายชื่อบริษัทที่อนุญาตให้คำนวณอัตโนมัติ
                const allowedCompaniesForAutoCalc = [
                    'บมจ.ธนาคารกสิกรไทย',
                    'ธนาคารกสิกรไทย',
                    'กสิกรไทย',
                    'มายออเดอร์ อินเทลลิเจนซ์',
                    'มายออเดอร์ อินเทลลิเจนซ์ จำกัด',
                    'MyOrder Intelligence',
                    'MYORDER INTELLIGENCE',
                    'MyOrder'
                ];
                
                // รายชื่อประเภทเอกสารที่อนุญาตให้คำนวณอัตโนมัติ
                const allowedDocumentTypesForAutoCalc = [
                    'ภ.พ.36',
                    'ภพ.36',
                    'PP36',
                    'pp36'
                ];
                
                // ตรวจสอบว่าบริษัทนี้อยู่ในรายชื่อที่อนุญาตหรือไม่
                const isAllowedCompany = ocrData.company_name && allowedCompaniesForAutoCalc.some(company => 
                    ocrData.company_name.includes(company)
                );
                
                // ตรวจสอบว่าประเภทเอกสารนี้อยู่ในรายชื่อที่อนุญาตหรือไม่ (สำหรับ ภ.พ.36)
                const isAllowedDocumentType = ocrData.document_type && allowedDocumentTypesForAutoCalc.some(docType => 
                    ocrData.document_type.includes(docType)
                );
                
                // สำหรับมายออเดอร์ อินเทลลิเจนซ์: คำนวณยอดรวมทั้งสิ้นจาก line1 + line2
                if (hasMyOrderSplit && myOrderLine1 && myOrderLine2) {
                    ocrTotalAmount = myOrderLine1.total_amount + myOrderLine2.total_amount;
                    isAutoCalculated = true;
                    console.log(`📦 [ดีบัค มายออเดอร์ อินเทลลิเจนซ์] ยอดรวมทั้งสิ้น: ${myOrderLine1.total_amount} + ${myOrderLine2.total_amount} = ${ocrTotalAmount}`);
                } else if (isAllowedCompany || isKasikornBank || isMyOrderIntelligence || isAllowedDocumentType) {
                    // สำหรับบริษัทหรือประเภทเอกสารที่กำหนดเท่านั้น: คำนวณยอดรวมจากยอดก่อนภาษี + ภาษี (เฉพาะที่อนุญาต)
                    ocrTotalAmount = ocrData.total_amount || 0;
                    if (ocrTotalAmount === 0 || !ocrData.total_amount) {
                        if (amountBeforeVat > 0 && vatAmount > 0) {
                            ocrTotalAmount = amountBeforeVat + vatAmount;
                            isAutoCalculated = true;
                            const identifier = ocrData.company_name || ocrData.document_type || 'Unknown';
                            console.log(`💰 [ดีบัค] คำนวณยอดหลังบวกภาษีอัตโนมัติ (${identifier}): ${amountBeforeVat} + ${vatAmount} = ${ocrTotalAmount}`);
                        } else if (amountBeforeVat > 0) {
                            ocrTotalAmount = amountBeforeVat;
                            isAutoCalculated = true;
                            const identifier = ocrData.company_name || ocrData.document_type || 'Unknown';
                            console.log(`💰 [ดีบัค] ใช้ยอดก่อนภาษีเป็นยอดรวม (${identifier}): ${ocrTotalAmount}`);
                        }
                    }
                } else {
                    // สำหรับกรณีปกติ: ใช้ค่าจาก OCR โดยตรง (ไม่คำนวณอัตโนมัติ)
                    ocrTotalAmount = ocrData.total_amount || 0;
                }
                
                // ดีบัคสำหรับบมจ.ธนาคารกสิกรไทย
                if (isKasikornBank) {
                    console.log(`🏦 [ดีบัค บมจ.ธนาคารกสิกรไทย] ชื่อบริษัท: ${ocrData.company_name}`);
                    console.log(`🏦 [ดีบัค บมจ.ธนาคารกสิกรไทย] ยอดก่อนภาษีมูลค่าเพิ่ม: ${amountBeforeVat}`);
                    console.log(`🏦 [ดีบัค บมจ.ธนาคารกสิกรไทย] ยอดภาษีมูลค่าเพิ่ม: ${vatAmount}`);
                    console.log(`🏦 [ดีบัค บมจ.ธนาคารกสิกรไทย] ยอดหลังบวกภาษีมูลค่าเพิ่ม: ${ocrTotalAmount}`);
                    console.log(`🏦 [ดีบัค บมจ.ธนาคารกสิกรไทย] รายการสินค้า:`, ocrData.items);
                }
                
                // ดีบัคสำหรับมายออเดอร์ อินเทลลิเจนซ์
                if (hasMyOrderSplit && myOrderLine1 && myOrderLine2) {
                    console.log(`📦 [ดีบัค มายออเดอร์ อินเทลลิเจนซ์] ชื่อบริษัท: ${ocrData.company_name}`);
                    console.log(`📦 [ดีบัค มายออเดอร์ อินเทลลิเจนซ์] รายการที่ 1 - ยอดก่อนภาษี: ${myOrderLine1.amount_before_vat}, ยอดภาษี: ${myOrderLine1.vat_amount}, ยอดรวม: ${myOrderLine1.total_amount}`);
                    console.log(`📦 [ดีบัค มายออเดอร์ อินเทลลิเจนซ์] รายการที่ 2 - ยอดก่อนภาษี: ${myOrderLine2.amount_before_vat}, ยอดภาษี: ${myOrderLine2.vat_amount}, ยอดรวม: ${myOrderLine2.total_amount}`);
                    console.log(`📦 [ดีบัค มายออเดอร์ อินเทลลิเจนซ์] ยอดรวมทั้งสิ้น: ${ocrTotalAmount}`);
                }
                
                html += `<div class="comparison-field">`;
                html += `<span class="comparison-field-label">เลขที่เอกสาร:</span>`;
                html += `<span class="comparison-field-value ${matchDetails?.document_no_match ? 'match' : 'mismatch'}" style="color: ${matchDetails?.document_no_match ? '#10b981' : '#ef4444'}; font-weight: ${matchDetails?.document_no_match ? '400' : '600'};">${ocrData.document_no || '-'}</span>`;
                html += `</div>`;
                
                html += `<div class="comparison-field">`;
                html += `<span class="comparison-field-label">วันที่:</span>`;
                html += `<span class="comparison-field-value ${matchDetails?.date_match ? 'match' : 'mismatch'}" style="color: ${matchDetails?.date_match ? '#10b981' : '#ef4444'}; font-weight: ${matchDetails?.date_match ? '400' : '600'};">${ocrData.date || '-'}</span>`;
                html += `</div>`;
                
                // หมายเหตุ: isCustomsDepartment ถูกประกาศไว้แล้วในส่วนการคำนวณยอดรวมด้านบน
                
                html += `<div class="comparison-field">`;
                html += `<span class="comparison-field-label">ชื่อบริษัท:</span>`;
                html += `<span class="comparison-field-value ${matchDetails?.company_name_match ? 'match' : 'mismatch'}" style="color: ${matchDetails?.company_name_match ? '#10b981' : '#ef4444'}; font-weight: ${matchDetails?.company_name_match ? '400' : '600'};">${ocrData.company_name || '-'}</span>`;
                html += `</div>`;
                
                html += `<div class="comparison-field">`;
                html += `<span class="comparison-field-label">เลขประจำตัวผู้เสียภาษี:</span>`;
                // สำหรับกรมศุลกากร: แสดง "ไม่มีข้อมูล" แทน "-"
                const displayTaxId = isCustomsDepartment ? 'ไม่มีข้อมูล' : (ocrData.tax_id || '-');
                html += `<span class="comparison-field-value ${matchDetails?.tax_id_match ? 'match' : 'mismatch'}" style="color: ${matchDetails?.tax_id_match ? '#10b981' : '#ef4444'}; font-weight: ${matchDetails?.tax_id_match ? '400' : '600'};">${displayTaxId}</span>`;
                html += `</div>`;
                
                html += `<div class="comparison-field">`;
                html += `<span class="comparison-field-label">สาขา:</span>`;
                // สำหรับกรมศุลกากร: แสดง "ไม่มีข้อมูล" แทน "-"
                const displayBranch = isCustomsDepartment ? 'ไม่มีข้อมูล' : (ocrData.branch || '-');
                html += `<span class="comparison-field-value ${matchDetails?.branch_match ? 'match' : 'mismatch'}" style="color: ${matchDetails?.branch_match ? '#10b981' : '#ef4444'}; font-weight: ${matchDetails?.branch_match ? '400' : '600'};">${displayBranch}</span>`;
                html += `</div>`;
                
                html += `<div class="comparison-field">`;
                html += `<span class="comparison-field-label">เลขที่เอกสารอ้างอิง (จากชื่อไฟล์):</span>`;
                html += `<span class="comparison-field-value ${matchDetails?.reference_no_match ? 'match' : 'mismatch'}" style="color: ${matchDetails?.reference_no_match ? '#10b981' : '#ef4444'}; font-weight: ${matchDetails?.reference_no_match ? '400' : '600'};">${ocrData.reference_number || '-'}</span>`;
                html += `</div>`;
                
                // สำหรับมายออเดอร์ อินเทลลิเจนซ์: แสดง 2 บรรทัดแยกกัน
                if (hasMyOrderSplit && myOrderLine1 && myOrderLine2) {
                    html += `<div class="comparison-field" style="background: #1e3a5f; padding: 12px; border-radius: 5px; border-left: 3px solid #3b82f6; margin-bottom: 10px;">`;
                    html += `<div style="color: #60a5fa; font-weight: bold; margin-bottom: 8px;">📋 รายการที่ 1: ค่าบริการเรียกเก็บเงินปลายทาง</div>`;
                    html += `<div class="comparison-field" style="margin-left: 10px; margin-bottom: 5px;">`;
                    html += `<span class="comparison-field-label">ยอดก่อนภาษี:</span>`;
                    html += `<span class="comparison-field-value ${matchDetails?.amount_before_vat_match ? 'match' : 'mismatch'}" style="color: ${matchDetails?.amount_before_vat_match ? '#10b981' : '#ef4444'}; font-weight: ${matchDetails?.amount_before_vat_match ? '400' : '600'};">${myOrderLine1.amount_before_vat.toLocaleString('th-TH', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>`;
                    html += `</div>`;
                    html += `<div class="comparison-field" style="margin-left: 10px; margin-bottom: 5px;">`;
                    html += `<span class="comparison-field-label">ยอดภาษี:</span>`;
                    html += `<span class="comparison-field-value ${matchDetails?.vat_amount_match ? 'match' : 'mismatch'}" style="color: ${matchDetails?.vat_amount_match ? '#10b981' : '#ef4444'}; font-weight: ${matchDetails?.vat_amount_match ? '400' : '600'};">${myOrderLine1.vat_amount.toLocaleString('th-TH', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>`;
                    html += `</div>`;
                    html += `<div class="comparison-field" style="margin-left: 10px; margin-top: 8px; padding-top: 8px; border-top: 1px solid #475569;">`;
                    html += `<span class="comparison-field-label" style="font-weight: 600;">ยอดรวม:</span>`;
                    html += `<span class="comparison-field-value" style="color: #10b981; font-weight: 600; font-size: 1.05em;">${myOrderLine1.total_amount.toLocaleString('th-TH', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>`;
                    html += `</div>`;
                    html += `</div>`;
                    
                    html += `<div class="comparison-field" style="background: #1e3a5f; padding: 12px; border-radius: 5px; border-left: 3px solid #3b82f6; margin-bottom: 10px;">`;
                    html += `<div style="color: #60a5fa; font-weight: bold; margin-bottom: 8px;">📋 รายการที่ 2: ค่าขนส่งภายในประเทศ (ไม่มีภาษีมูลค่าเพิ่ม)</div>`;
                    html += `<div class="comparison-field" style="margin-left: 10px; margin-bottom: 5px;">`;
                    html += `<span class="comparison-field-label">ยอดก่อนภาษี:</span>`;
                    html += `<span class="comparison-field-value ${matchDetails?.amount_before_vat_match ? 'match' : 'mismatch'}" style="color: ${matchDetails?.amount_before_vat_match ? '#10b981' : '#ef4444'}; font-weight: ${matchDetails?.amount_before_vat_match ? '400' : '600'};">${myOrderLine2.amount_before_vat.toLocaleString('th-TH', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>`;
                    html += `</div>`;
                    html += `<div class="comparison-field" style="margin-left: 10px; margin-top: 8px; padding-top: 8px; border-top: 1px solid #475569;">`;
                    html += `<span class="comparison-field-label" style="font-weight: 600;">ยอดรวม:</span>`;
                    html += `<span class="comparison-field-value" style="color: #10b981; font-weight: 600; font-size: 1.05em;">${myOrderLine2.total_amount.toLocaleString('th-TH', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>`;
                    html += `</div>`;
                    html += `</div>`;
                    
                    html += `<div class="comparison-field" style="margin-top: 12px; padding-top: 12px; border-top: 2px solid #475569;">`;
                    html += `<span class="comparison-field-label" style="font-weight: 600; font-size: 1.1em;">ยอดรวมทั้งสิ้น:</span>`;
                    const totalAmountDisplay = ocrTotalAmount.toLocaleString('th-TH', {minimumFractionDigits: 2, maximumFractionDigits: 2});
                    html += `<span class="comparison-field-value ${matchDetails?.total_amount_match ? 'match' : 'mismatch'}" style="color: ${matchDetails?.total_amount_match ? '#10b981' : '#ef4444'}; font-weight: 600; font-size: 1.1em;">
                        ${totalAmountDisplay}
                        ${isAutoCalculated ? ' <span style="color: #60a5fa; font-size: 0.85em;">(คำนวณอัตโนมัติ)</span>' : ''}
                    </span>`;
                    html += `</div>`;
                } else {
                    // กรณีปกติ: แสดงยอดเงินแบบปกติ
                    html += `<div class="comparison-field">`;
                    html += `<span class="comparison-field-label">ยอดก่อนภาษีมูลค่าเพิ่ม:</span>`;
                    html += `<span class="comparison-field-value ${matchDetails?.amount_before_vat_match ? 'match' : 'mismatch'}" style="color: ${matchDetails?.amount_before_vat_match ? '#10b981' : '#ef4444'}; font-weight: ${matchDetails?.amount_before_vat_match ? '400' : '600'};">${(ocrData.amount_before_vat || 0).toLocaleString('th-TH', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>`;
                    html += `</div>`;
                    
                    html += `<div class="comparison-field">`;
                    html += `<span class="comparison-field-label">ยอดภาษีมูลค่าเพิ่ม:</span>`;
                    html += `<span class="comparison-field-value ${matchDetails?.vat_amount_match ? 'match' : 'mismatch'}" style="color: ${matchDetails?.vat_amount_match ? '#10b981' : '#ef4444'}; font-weight: ${matchDetails?.vat_amount_match ? '400' : '600'};">${(ocrData.vat_amount || 0).toLocaleString('th-TH', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>`;
                    html += `</div>`;
                    
                    html += `<div class="comparison-field">`;
                    html += `<span class="comparison-field-label">ยอดหลังบวกภาษีมูลค่าเพิ่ม:</span>`;
                    const totalAmountDisplay = ocrTotalAmount.toLocaleString('th-TH', {minimumFractionDigits: 2, maximumFractionDigits: 2});
                    html += `<span class="comparison-field-value ${matchDetails?.total_amount_match ? 'match' : 'mismatch'}" style="color: ${matchDetails?.total_amount_match ? '#10b981' : '#ef4444'}; font-weight: ${matchDetails?.total_amount_match ? '400' : '600'};">
                        ${totalAmountDisplay}
                        ${isAutoCalculated ? ' <span style="color: #60a5fa; font-size: 0.85em;">(คำนวณอัตโนมัติ)</span>' : ''}
                    </span>`;
                    html += `</div>`;
                }
                
                // แสดงข้อมูลดีบัคสำหรับบมจ.ธนาคารกสิกรไทย
                if (isKasikornBank) {
                    html += `<div class="comparison-field" style="background: #1e293b; padding: 10px; border-radius: 5px; border-left: 4px solid #60a5fa; margin-top: 10px;">`;
                    html += `<span class="comparison-field-label" style="color: #60a5fa; font-weight: 600;">🏦 ดีบัค - บมจ.ธนาคารกสิกรไทย:</span>`;
                    html += `<div style="margin-top: 5px; font-size: 0.9em; color: #cbd5e1;">`;
                    html += `<div>• ยอดก่อนภาษีมูลค่าเพิ่ม (จากค่าธรรมเนียม): ${(ocrData.amount_before_vat || 0).toLocaleString('th-TH', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>`;
                    html += `<div>• ยอดภาษีมูลค่าเพิ่ม: ${(ocrData.vat_amount || 0).toLocaleString('th-TH', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>`;
                    html += `<div>• ยอดหลังบวกภาษีมูลค่าเพิ่ม: ${ocrTotalAmount.toLocaleString('th-TH', {minimumFractionDigits: 2, maximumFractionDigits: 2})} ${isAutoCalculated ? '(คำนวณอัตโนมัติ)' : ''}</div>`;
                    html += `</div>`;
                    html += `</div>`;
                }
                
                // แสดงข้อมูลดีบัคสำหรับมายออเดอร์ อินเทลลิเจนซ์
                if (hasMyOrderSplit && myOrderLine1 && myOrderLine2) {
                    html += `<div class="comparison-field" style="background: #1e293b; padding: 10px; border-radius: 5px; border-left: 4px solid #3b82f6; margin-top: 10px;">`;
                    html += `<span class="comparison-field-label" style="color: #3b82f6; font-weight: 600;">📦 ดีบัค - มายออเดอร์ อินเทลลิเจนซ์:</span>`;
                    html += `<div style="margin-top: 5px; font-size: 0.9em; color: #cbd5e1;">`;
                    html += `<div style="margin-bottom: 5px;"><strong>รายการที่ 1:</strong> ยอดก่อนภาษี: ${myOrderLine1.amount_before_vat.toLocaleString('th-TH', {minimumFractionDigits: 2, maximumFractionDigits: 2})}, ยอดภาษี: ${myOrderLine1.vat_amount.toLocaleString('th-TH', {minimumFractionDigits: 2, maximumFractionDigits: 2})}, ยอดรวม: ${myOrderLine1.total_amount.toLocaleString('th-TH', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>`;
                    html += `<div style="margin-bottom: 5px;"><strong>รายการที่ 2:</strong> ยอดก่อนภาษี: ${myOrderLine2.amount_before_vat.toLocaleString('th-TH', {minimumFractionDigits: 2, maximumFractionDigits: 2})}, ยอดภาษี: ${myOrderLine2.vat_amount.toLocaleString('th-TH', {minimumFractionDigits: 2, maximumFractionDigits: 2})}, ยอดรวม: ${myOrderLine2.total_amount.toLocaleString('th-TH', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>`;
                    html += `<div><strong>ยอดรวมทั้งสิ้น:</strong> ${ocrTotalAmount.toLocaleString('th-TH', {minimumFractionDigits: 2, maximumFractionDigits: 2})} ${isAutoCalculated ? '(คำนวณอัตโนมัติ)' : ''}</div>`;
                    html += `</div>`;
                    html += `</div>`;
                }
                
                // ย้ายประเภทเอกสารและสถานะเอกสารมาหลังยอดหลังบวกภาษีมูลค่าเพิ่ม
                html += `<div class="comparison-field">`;
                html += `<span class="comparison-field-label">ประเภทเอกสาร:</span>`;
                html += `<span class="comparison-field-value ${matchDetails?.document_type_match ? 'match' : 'mismatch'}" style="color: ${matchDetails?.document_type_match ? '#10b981' : '#ef4444'}; font-weight: ${matchDetails?.document_type_match ? '400' : '600'};">${ocrData.document_type || '-'}</span>`;
                html += `</div>`;
                
                html += `<div class="comparison-field">`;
                html += `<span class="comparison-field-label">สถานะเอกสาร:</span>`;
                html += `<span class="comparison-field-value">${ocrData.document_status || '-'}</span>`;
                html += `</div>`;
                
                
                // แสดงรายการสินค้า (ถ้ามี)
                if (ocrData.items && Array.isArray(ocrData.items) && ocrData.items.length > 0) {
                    html += `<div class="comparison-field" style="margin-top: 20px; padding-top: 20px; border-top: 2px solid #334155;">`;
                    html += `<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 15px;">`;
                    html += `<span style="font-size: 1.2em;">📦</span>`;
                    html += `<span class="comparison-field-label" style="font-weight: 600; color: #60a5fa; font-size: 1em;">รายการสินค้า:</span>`;
                    html += `<span style="color: #94a3b8; font-size: 0.9em;">(${ocrData.items.length} รายการ)</span>`;
                    html += `</div>`;
                    html += `<div style="max-height: 400px; overflow-y: auto; background: #0f172a; padding: 12px; border-radius: 8px; border: 1px solid #334155;">`;
                    ocrData.items.forEach((item, itemIndex) => {
                        const itemName = item['รายการ'] || item['description'] || item['รายการสินค้า'] || item['ชื่อสินค้า'] || '-';
                        const itemAmount = item['จำนวนเงิน'] || item['amount'] || item['ยอดรวม'] || '-';
                        const itemQuantity = item['จำนวน'] || item['quantity'] || '';
                        const itemPrice = item['ราคา'] || item['price'] || item['ราคาต่อหน่วย'] || item['unit_price'] || '';
                        
                        // แปลงจำนวนเงินเป็นตัวเลข (ถ้าเป็น string ให้ลบ comma และแปลงเป็นตัวเลข)
                        let amountValue = itemAmount;
                        if (typeof itemAmount === 'string' && itemAmount !== '-') {
                            amountValue = parseFloat(itemAmount.replace(/,/g, '')) || 0;
                        } else if (typeof itemAmount === 'number') {
                            amountValue = itemAmount;
                        }
                        
                        html += `<div style="padding: 12px; margin-bottom: 10px; background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border-radius: 6px; border-left: 4px solid #60a5fa; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2); transition: all 0.2s;" onmouseover="this.style.transform='translateX(2px)'; this.style.boxShadow='0 4px 8px rgba(96, 165, 250, 0.3)';" onmouseout="this.style.transform='translateX(0)'; this.style.boxShadow='0 2px 4px rgba(0, 0, 0, 0.2)';">`;
                        
                        // ชื่อรายการ
                        html += `<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">`;
                        html += `<span style="background: #60a5fa; color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.85em; font-weight: 600; flex-shrink: 0;">${itemIndex + 1}</span>`;
                        html += `<strong style="color: #fafafa; font-size: 0.95em; flex: 1;">${itemName}</strong>`;
                        html += `</div>`;
                        
                        // จำนวนและราคา
                        if (itemQuantity || itemPrice) {
                            html += `<div style="display: flex; gap: 15px; margin-left: 32px; margin-bottom: 6px; flex-wrap: wrap;">`;
                            if (itemQuantity) {
                                html += `<div style="display: flex; align-items: center; gap: 4px;">`;
                                html += `<span style="color: #94a3b8; font-size: 0.85em;">จำนวน:</span>`;
                                html += `<span style="color: #cbd5e1; font-size: 0.85em; font-weight: 500;">${itemQuantity}</span>`;
                                html += `</div>`;
                            }
                            if (itemPrice) {
                                html += `<div style="display: flex; align-items: center; gap: 4px;">`;
                                html += `<span style="color: #94a3b8; font-size: 0.85em;">ราคา:</span>`;
                                html += `<span style="color: #cbd5e1; font-size: 0.85em; font-weight: 500;">${itemPrice}</span>`;
                                html += `</div>`;
                            }
                            html += `</div>`;
                        }
                        
                        // ยอดรวม
                        if (amountValue && amountValue !== '-' && amountValue !== 0) {
                            html += `<div style="margin-left: 32px; margin-top: 6px; padding-top: 8px; border-top: 1px solid #334155;">`;
                            html += `<div style="display: flex; align-items: center; gap: 8px;">`;
                            html += `<span style="color: #10b981; font-size: 0.9em; font-weight: 600;">ยอดรวม:</span>`;
                            html += `<span style="color: #10b981; font-size: 1em; font-weight: 700;">${typeof amountValue === 'number' ? amountValue.toLocaleString('th-TH', {minimumFractionDigits: 2, maximumFractionDigits: 2}) : amountValue}</span>`;
                            html += `<span style="color: #10b981; font-size: 0.9em; font-weight: 500;">บาท</span>`;
                            html += `</div>`;
                            html += `</div>`;
                        }
                        
                        html += `</div>`;
                    });
                    html += `</div>`;
                    html += `</div>`;
                }
                
                // เพิ่มปุ่มลบรายการสำหรับกรณีที่อ่านได้แค่ OCR (ไม่มีข้อมูลภาษีซื้อ)
                if (!comp.purchase_data && comp.ocr_data) {
                    const ocrReferenceNo = ocrData.reference_number || ocrData.document_no || '';
                    if (ocrReferenceNo) {
                        html += `<div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #334155; display: flex; gap: 10px; flex-wrap: wrap;">`;
                        
                        // ปุ่มลบรายการ
                        html += `<button onclick="removeComparisonItem(${index}, '${ocrReferenceNo}')" style="flex: 1; min-width: 120px; padding: 10px; background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.9em; font-weight: 600; transition: all 0.3s; display: flex; align-items: center; justify-content: center; gap: 8px;" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(107, 114, 128, 0.4)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';">`;
                        html += `<span style="font-size: 1.1em;">🗑️</span> ลบรายการ`;
                        html += `</button>`;
                        
                        html += `</div>`;
                    }
                }
            } else {
                html += `<div style="color: #ef4444; text-align: center; padding: 20px;">ไม่พบข้อมูล</div>`;
            }
            
            html += `</div>`; // ปิดฝั่ง OCR
            
            html += `</div>`; // ปิด comparison-sides-container
            
            // ส่วนข้อมูลบริษัท (แนวนอน) - วางไว้ด้านล่าง
            // ตรวจสอบว่ามีข้อมูลบริษัทในระบบหรือไม่
            const hasCompanyDataInSystem = (companyName && companyName !== '-') ||
                                          (companyTaxId && companyTaxId !== '-') ||
                                          (companyAddress && companyAddress !== '-');
            
            // ตรวจสอบว่ามีข้อมูลบริษัทที่ต้องเปรียบเทียบหรือไม่
            const hasCompanyDataToCompare = (buyerName && buyerName !== '-' && companyName && companyName !== '-') ||
                                            (buyerTaxId && buyerTaxId !== '-' && companyTaxId && companyTaxId !== '-') ||
                                            (buyerAddress && buyerAddress !== '-' && companyAddress && companyAddress !== '-');
            
            // ตรวจสอบว่าถูกอนุมัติข้อมูลบริษัททั้งหมดแล้วหรือไม่
            const companyDataApprovalKey = `${index}-company_data_all`;
            const isCompanyDataApproved = comparisonApprovals[companyDataApprovalKey] || false;
            
            // ตรวจสอบว่ามีข้อมูลที่ไม่ตรงกันหรือไม่
            const hasMismatch = (!companyNameMatch && buyerName && buyerName !== '-' && companyName && companyName !== '-') ||
                               (!companyTaxIdMatch && buyerTaxId && buyerTaxId !== '-' && companyTaxId && companyTaxId !== '-') ||
                               (!companyAddressMatch && buyerAddress && buyerAddress !== '-' && companyAddress && companyAddress !== '-');
            
            // แสดงสถานะ "ไม่มีข้อมูลบริษัท" ถ้าไม่มีข้อมูลบริษัทในระบบเลย
            if (!hasCompanyDataInSystem) {
                html += `<div class="company-data-section" style="width: 100%; margin: 20px 0; padding: 15px; background: linear-gradient(135deg, #fbbf2415 0%, #f59e0b15 100%); border-radius: 10px; border: 2px solid #fbbf24; border-left: 5px solid #fbbf24;">`;
                html += `<div style="display: flex; align-items: center; gap: 12px;">`;
                html += `<span style="font-size: 1.8em;">⚠️</span>`;
                html += `<div style="flex: 1;">`;
                html += `<div style="font-weight: 700; color: #fbbf24; font-size: 1.1em; margin-bottom: 4px;">ไม่มีข้อมูลบริษัท</div>`;
                html += `<div style="color: #94a3b8; font-size: 0.9em;">ระบบไม่พบข้อมูลบริษัทในระบบ กรุณาเพิ่มข้อมูลบริษัทก่อนทำการตรวจสอบ</div>`;
                html += `</div>`;
                html += `</div>`;
                html += `</div>`;
            } else if (hasCompanyDataToCompare) {
                // แสดงข้อมูลบริษัทแบบแนวนอน
                html += `<div class="company-data-section" style="width: 100%; margin: 20px 0; padding: 15px; background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border-radius: 10px; border: 2px solid #334155; border-left: 5px solid #60a5fa;">`;
                
                // ส่วนหัว
                html += `<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 15px;">`;
                html += `<div style="display: flex; align-items: center; gap: 10px;">`;
                html += `<span style="font-size: 1.5em;">🏢</span>`;
                html += `<div>`;
                html += `<div style="font-weight: 700; color: #60a5fa; font-size: 1.1em; margin-bottom: 4px;">ข้อมูลบริษัท</div>`;
                html += `<div style="color: #94a3b8; font-size: 0.85em;">เปรียบเทียบข้อมูลจาก OCR กับข้อมูลบริษัท</div>`;
                html += `</div>`;
                html += `</div>`;
                
                // ปุ่มอนุมัติข้อมูลบริษัททั้งหมด
                if (hasMismatch && !isCompanyDataApproved) {
                    html += `<button onclick="approveCompanyData(${index})" data-field-key="company_data_all" data-field-index="${index}" style="padding: 10px 20px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 0.9em; font-weight: 600; display: flex; align-items: center; gap: 8px; transition: all 0.3s; white-space: nowrap; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 16px rgba(16, 185, 129, 0.4)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 12px rgba(16, 185, 129, 0.3)';" title="อนุมัติข้อมูลบริษัททั้งหมด (ชื่อ, เลขประจำตัวผู้เสียภาษี, ที่อยู่)">`;
                    html += `<span style="font-size: 1.2em;">✓</span>`;
                    html += `<span>อนุมัติข้อมูลบริษัท</span>`;
                    html += `</button>`;
                } else if (isCompanyDataApproved) {
                    html += `<button onclick="cancelCompanyDataApproval(${index})" data-field-key="company_data_all" data-field-index="${index}" style="padding: 10px 20px; background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 0.9em; font-weight: 600; display: flex; align-items: center; gap: 8px; transition: all 0.3s; white-space: nowrap; box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 16px rgba(239, 68, 68, 0.4)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 12px rgba(239, 68, 68, 0.3)';" title="ยกเลิกการอนุมัติข้อมูลบริษัท">`;
                    html += `<span style="font-size: 1.2em;">✕</span>`;
                    html += `<span>ยกเลิกการอนุมัติ</span>`;
                    html += `</button>`;
                }
                
                html += `</div>`;
                
                // ส่วนแสดงผลการเปรียบเทียบแบบแนวนอน (3 คอลัมน์)
                html += `<div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin-top: 15px;">`;
                
                // คอลัมน์ที่ 1: ชื่อ
                if (buyerName && buyerName !== '-' && companyName && companyName !== '-') {
                    const nameApprovalKey = `${index}-company_name_match`;
                    const isNameApproved = comparisonApprovals[nameApprovalKey] || false;
                    const nameMatchColor = isNameApproved ? '#10b981' : (companyNameMatch ? '#10b981' : '#ef4444');
                    const nameMatchText = isNameApproved ? '✅ อนุมัติแล้ว' : (companyNameMatch ? '✅ ตรงกัน' : '❌ ไม่ตรงกัน');
                    
                    html += `<div style="padding: 12px; background: ${nameMatchColor}15; border-radius: 8px; border-left: 4px solid ${nameMatchColor}; flex: 1;">`;
                    html += `<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">`;
                    html += `<div style="display: flex; align-items: center; gap: 8px;">`;
                    html += `<span style="font-size: 1.1em;">🏢</span>`;
                    html += `<span style="font-weight: 600; color: ${nameMatchColor}; font-size: 0.95em;">ผลการเปรียบเทียบชื่อ: ${nameMatchText}</span>`;
                    html += `</div>`;
                    
                    // ปุ่มอนุมัติชื่อ (แสดงเฉพาะเมื่อไม่ตรงกันหรือยังไม่ได้อนุมัติ)
                    if (!isNameApproved && !companyNameMatch) {
                        html += `<button onclick="approveField(${index}, 'company_name_match', 'ชื่อบริษัท')" data-field-key="company_name_match" data-field-index="${index}" style="padding: 6px 12px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.85em; font-weight: 600; display: flex; align-items: center; gap: 6px; transition: all 0.3s; white-space: nowrap;" onmouseover="this.style.transform='scale(1.05)'; this.style.boxShadow='0 2px 8px rgba(16, 185, 129, 0.4)';" onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='none';" title="อนุมัติความไม่ตรงกันของชื่อ">`;
                        html += `<span style="font-size: 1em;">✓</span> อนุมัติ`;
                        html += `</button>`;
                    } else if (isNameApproved) {
                        html += `<button onclick="cancelApproval(${index}, 'company_name_match', 'ชื่อบริษัท')" data-field-key="company_name_match" data-field-index="${index}" style="padding: 6px 12px; background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.85em; font-weight: 600; display: flex; align-items: center; gap: 6px; transition: all 0.3s; white-space: nowrap;" onmouseover="this.style.transform='scale(1.05)'; this.style.boxShadow='0 2px 8px rgba(239, 68, 68, 0.4)';" onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='none';" title="ยกเลิกการอนุมัติ">`;
                        html += `<span style="font-size: 1em;">✕</span> ยกเลิก`;
                        html += `</button>`;
                    }
                    
                    html += `</div>`;
                    html += `<div style="color: #94a3b8; font-size: 0.85em; margin-bottom: 5px;">ชื่อจาก OCR:</div>`;
                    html += `<div style="color: ${isNameApproved || companyNameMatch ? '#10b981' : '#cbd5e1'}; font-size: 0.9em; margin-bottom: 10px; word-break: break-word;">${buyerName}</div>`;
                    html += `<div style="color: #94a3b8; font-size: 0.85em; margin-bottom: 5px;">ชื่อบริษัท:</div>`;
                    html += `<div style="color: ${isNameApproved || companyNameMatch ? '#10b981' : '#cbd5e1'}; font-size: 0.9em; margin-bottom: 10px; word-break: break-word;">${companyName}</div>`;
                    
                    // ปุ่มวิเคราะห์ความคล้ายคลึง (แสดงเฉพาะเมื่อไม่ตรงกัน)
                    if (!isNameApproved && !companyNameMatch) {
                        // Escape HTML และ quotes สำหรับชื่อบริษัท
                        const escapedBuyerName = buyerName.replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/"/g, '\\"').replace(/\n/g, '\\n');
                        const escapedCompanyName = companyName.replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/"/g, '\\"').replace(/\n/g, '\\n');
                        html += `<button onclick="analyzeCompanyNameSimilarity(${index}, '${escapedBuyerName}', '${escapedCompanyName}')" style="width: 100%; padding: 8px 12px; background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.85em; font-weight: 600; display: flex; align-items: center; justify-content: center; gap: 6px; transition: all 0.3s; margin-top: 8px;" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(59, 130, 246, 0.4)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';" title="วิเคราะห์ความคล้ายคลึงของชื่อบริษัท">`;
                        html += `<span style="font-size: 1em;">🔍</span>`;
                        html += `<span>วิเคราะห์ความคล้ายคลึง</span>`;
                        html += `</button>`;
                    }
                    
                    html += `</div>`;
                } else {
                    html += `<div style="padding: 12px; background: #33415515; border-radius: 8px; border-left: 4px solid #334155; flex: 1;">`;
                    html += `<div style="color: #94a3b8; font-size: 0.9em;">ไม่มีข้อมูลชื่อ</div>`;
                    html += `</div>`;
                }
                
                // คอลัมน์ที่ 2: เลขประจำตัวผู้เสียภาษี
                if (buyerTaxId && buyerTaxId !== '-' && companyTaxId && companyTaxId !== '-') {
                    const taxIdApprovalKey = `${index}-company_tax_id_match`;
                    const isTaxIdApproved = comparisonApprovals[taxIdApprovalKey] || false;
                    const taxIdMatchColor = isTaxIdApproved ? '#10b981' : (companyTaxIdMatch ? '#10b981' : '#ef4444');
                    const taxIdMatchText = isTaxIdApproved ? '✅ อนุมัติแล้ว' : (companyTaxIdMatch ? '✅ ตรงกัน' : '❌ ไม่ตรงกัน');
                    
                    html += `<div style="padding: 12px; background: ${taxIdMatchColor}15; border-radius: 8px; border-left: 4px solid ${taxIdMatchColor}; flex: 1;">`;
                    html += `<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">`;
                    html += `<div style="display: flex; align-items: center; gap: 8px;">`;
                    html += `<span style="font-size: 1.1em;">🆔</span>`;
                    html += `<span style="font-weight: 600; color: ${taxIdMatchColor}; font-size: 0.95em;">ผลการเปรียบเทียบเลขประจำตัวผู้เสียภาษี: ${taxIdMatchText}</span>`;
                    html += `</div>`;
                    
                    // ปุ่มอนุมัติเลขประจำตัวผู้เสียภาษี (แสดงเฉพาะเมื่อไม่ตรงกันหรือยังไม่ได้อนุมัติ)
                    if (!isTaxIdApproved && !companyTaxIdMatch) {
                        html += `<button onclick="approveField(${index}, 'company_tax_id_match', 'เลขประจำตัวผู้เสียภาษี')" data-field-key="company_tax_id_match" data-field-index="${index}" style="padding: 6px 12px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.85em; font-weight: 600; display: flex; align-items: center; gap: 6px; transition: all 0.3s; white-space: nowrap;" onmouseover="this.style.transform='scale(1.05)'; this.style.boxShadow='0 2px 8px rgba(16, 185, 129, 0.4)';" onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='none';" title="อนุมัติความไม่ตรงกันของเลขประจำตัวผู้เสียภาษี">`;
                        html += `<span style="font-size: 1em;">✓</span> อนุมัติ`;
                        html += `</button>`;
                    } else if (isTaxIdApproved) {
                        html += `<button onclick="cancelApproval(${index}, 'company_tax_id_match', 'เลขประจำตัวผู้เสียภาษี')" data-field-key="company_tax_id_match" data-field-index="${index}" style="padding: 6px 12px; background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.85em; font-weight: 600; display: flex; align-items: center; gap: 6px; transition: all 0.3s; white-space: nowrap;" onmouseover="this.style.transform='scale(1.05)'; this.style.boxShadow='0 2px 8px rgba(239, 68, 68, 0.4)';" onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='none';" title="ยกเลิกการอนุมัติ">`;
                        html += `<span style="font-size: 1em;">✕</span> ยกเลิก`;
                        html += `</button>`;
                    }
                    
                    html += `</div>`;
                    html += `<div style="color: #94a3b8; font-size: 0.85em; margin-bottom: 5px;">เลขจาก OCR:</div>`;
                    html += `<div style="color: #cbd5e1; font-size: 0.9em; margin-bottom: 10px;">${buyerTaxId}</div>`;
                    html += `<div style="color: #94a3b8; font-size: 0.85em; margin-bottom: 5px;">เลขประจำตัวผู้เสียภาษี 13 หลัก:</div>`;
                    html += `<div style="color: #cbd5e1; font-size: 0.9em;">${companyTaxId}</div>`;
                    html += `</div>`;
                } else {
                    html += `<div style="padding: 12px; background: #33415515; border-radius: 8px; border-left: 4px solid #334155; flex: 1;">`;
                    html += `<div style="color: #94a3b8; font-size: 0.9em;">ไม่มีข้อมูลเลขประจำตัวผู้เสียภาษี</div>`;
                    html += `</div>`;
                }
                
                // คอลัมน์ที่ 3: ที่อยู่
                if (buyerAddress && buyerAddress !== '-' && companyAddress && companyAddress !== '-') {
                    const addressApprovalKey = `${index}-address_match`;
                    const isAddressApproved = comparisonApprovals[addressApprovalKey] || false;
                    const addressMatchColor = isAddressApproved ? '#10b981' : (companyAddressMatch ? '#10b981' : '#ef4444');
                    const addressMatchText = isAddressApproved ? '✅ อนุมัติแล้ว' : (companyAddressMatch ? '✅ ตรงกัน' : '❌ ไม่ตรงกัน');
                    
                    html += `<div style="padding: 12px; background: ${addressMatchColor}15; border-radius: 8px; border-left: 4px solid ${addressMatchColor}; flex: 1;">`;
                    html += `<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">`;
                    html += `<div style="display: flex; align-items: center; gap: 8px;">`;
                    html += `<span style="font-size: 1.2em;">📍</span>`;
                    html += `<span style="font-weight: 600; color: ${addressMatchColor}; font-size: 0.95em;">ผลการเปรียบเทียบที่อยู่: ${addressMatchText}</span>`;
                    html += `</div>`;
                    
                    // ปุ่มอนุมัติที่อยู่ (แสดงเฉพาะเมื่อไม่ตรงกันหรือยังไม่ได้อนุมัติ)
                    if (!isAddressApproved && !companyAddressMatch) {
                        html += `<button onclick="approveField(${index}, 'address_match', 'ที่อยู่บริษัท')" data-field-key="address_match" data-field-index="${index}" style="padding: 6px 12px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.85em; font-weight: 600; display: flex; align-items: center; gap: 6px; transition: all 0.3s; white-space: nowrap;" onmouseover="this.style.transform='scale(1.05)'; this.style.boxShadow='0 2px 8px rgba(16, 185, 129, 0.4)';" onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='none';" title="อนุมัติความไม่ตรงกันของที่อยู่">`;
                        html += `<span style="font-size: 1em;">✓</span> อนุมัติ`;
                        html += `</button>`;
                    } else if (isAddressApproved) {
                        html += `<button onclick="cancelApproval(${index}, 'address_match', 'ที่อยู่บริษัท')" data-field-key="address_match" data-field-index="${index}" style="padding: 6px 12px; background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.85em; font-weight: 600; display: flex; align-items: center; gap: 6px; transition: all 0.3s; white-space: nowrap;" onmouseover="this.style.transform='scale(1.05)'; this.style.boxShadow='0 2px 8px rgba(239, 68, 68, 0.4)';" onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='none';" title="ยกเลิกการอนุมัติ">`;
                        html += `<span style="font-size: 1em;">✕</span> ยกเลิก`;
                        html += `</button>`;
                    }
                    
                    html += `</div>`;
                    
                    // แสดงที่อยู่ทั้งสองฝั่งเพื่อเปรียบเทียบ (แสดงเป็น 2 แถว)
                    html += `<div style="display: flex; flex-direction: column; gap: 12px; margin-top: 10px;">`;
                    
                    // แถวที่ 1: ที่อยู่บริษัท
                    html += `<div>`;
                    html += `<div style="color: #94a3b8; font-size: 0.85em; margin-bottom: 5px;">ที่อยู่บริษัท:</div>`;
                    html += `<div style="color: ${companyAddressMatch || isAddressApproved ? '#10b981' : '#ef4444'}; font-size: 0.9em; padding: 8px; background: #0f172a; border-radius: 4px; word-break: break-word; min-height: 40px; border: 1px solid ${companyAddressMatch || isAddressApproved ? '#10b981' : '#ef4444'}40;">${companyAddress}</div>`;
                    html += `</div>`;
                    
                    // แถวที่ 2: ที่อยู่จาก OCR
                    html += `<div>`;
                    html += `<div style="color: #94a3b8; font-size: 0.85em; margin-bottom: 5px;">ที่อยู่จาก OCR:</div>`;
                    html += `<div style="color: ${companyAddressMatch || isAddressApproved ? '#10b981' : '#ef4444'}; font-size: 0.9em; padding: 8px; background: #0f172a; border-radius: 4px; word-break: break-word; min-height: 40px; border: 1px solid ${companyAddressMatch || isAddressApproved ? '#10b981' : '#ef4444'}40;">${buyerAddress}</div>`;
                    html += `</div>`;
                    
                    html += `</div>`; // ปิด flex container
                    html += `</div>`;
                } else if (buyerAddress && buyerAddress !== '-' && (!companyAddress || companyAddress === '-')) {
                    html += `<div style="padding: 12px; background: #fbbf2415; border-radius: 8px; border-left: 4px solid #fbbf24; flex: 1;">`;
                    html += `<div style="display: flex; align-items: center; gap: 8px;">`;
                    html += `<span style="font-size: 1.2em;">⚠️</span>`;
                    html += `<span style="color: #fbbf24; font-weight: 600; font-size: 0.9em;">ไม่สามารถเปรียบเทียบได้: ยังไม่มีข้อมูลที่อยู่บริษัท</span>`;
                    html += `</div>`;
                    html += `</div>`;
                } else {
                    html += `<div style="padding: 12px; background: #33415515; border-radius: 8px; border-left: 4px solid #334155; flex: 1;">`;
                    html += `<div style="color: #94a3b8; font-size: 0.9em;">ไม่มีข้อมูลที่อยู่</div>`;
                    html += `</div>`;
                }
                
                html += `</div>`; // ปิด grid
                html += `</div>`; // ปิด company-data-section
            }
            
            // ปิด tag สำคัญทั้งหมด
            html += `</div>`; // ปิด comparison-content-wrapper
            html += `</div>`; // ปิด comparison-row-content
            html += `</div>`; // ปิด comparison-row
            
            return html;
        }
        
        function switchComparisonTab(tabName) {
            // ซ่อน tab content ทั้งหมด
            document.querySelectorAll('.comparison-tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // ลบ active class จาก tab ทั้งหมด
            document.querySelectorAll('.comparison-tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // แสดง tab content ที่เลือก
            const selectedContent = document.getElementById(`comparison-tab-${tabName}`);
            if (selectedContent) {
                selectedContent.classList.add('active');
            }
            
            // เพิ่ม active class ให้ tab ที่เลือก
            const tabs = document.querySelectorAll('.comparison-tab');
            let tabIndex = -1;
            if (tabName === 'all') {
                tabIndex = 0;
            } else if (tabName === 'mismatch') {
                tabIndex = 1;
            } else if (tabName === 'no_ocr_data') {
                tabIndex = 2;
            } else if (tabName === 'partial') {
                tabIndex = 3;
            } else if (tabName === 'match') {
                tabIndex = 4;
            }
            
            if (tabIndex >= 0 && tabs[tabIndex]) {
                tabs[tabIndex].classList.add('active');
            }
            
            // อัปเดต pagination เมื่อเปลี่ยน tab
            comparisonPagination.currentTab = tabName;
            comparisonPagination.currentPage = 1; // รีเซ็ตหน้าเป็น 1 เมื่อเปลี่ยน tab
            
            // รีเซ็ต search เมื่อเปลี่ยน tab (optional - ถ้าต้องการให้ search ค้างไว้ให้ comment บรรทัดนี้)
            // comparisonSearchTerm = '';
            // const searchInput = document.getElementById('comparisonReferenceSearch');
            // const clearBtn = document.getElementById('clearSearchBtn');
            // const searchResult = document.getElementById('comparisonSearchResult');
            // if (searchInput) searchInput.value = '';
            // if (clearBtn) clearBtn.style.display = 'none';
            // if (searchResult) searchResult.style.display = 'none';
            
            updateComparisonPagination();
        }
        
        // ฟังก์ชันสำหรับเปลี่ยนจำนวนรายการต่อหน้า
        function changeComparisonItemsPerPage(itemsPerPage) {
            comparisonPagination.itemsPerPage = parseInt(itemsPerPage);
            comparisonPagination.currentPage = 1; // รีเซ็ตหน้าเป็น 1 เมื่อเปลี่ยนจำนวนรายการต่อหน้า
            updateComparisonPagination();
        }
        
        // ฟังก์ชันสำหรับเปลี่ยนหน้า
        function changeComparisonPage(page) {
            comparisonPagination.currentPage = parseInt(page);
            updateComparisonPagination();
        }
        
        // ฟังก์ชันสำหรับอัปเดต pagination
        function updateComparisonPagination() {
            const activeTab = document.querySelector('.comparison-tab-content.active');
            if (!activeTab) return;
            
            const allRows = Array.from(activeTab.querySelectorAll('.comparison-row'));
            const itemsPerPage = comparisonPagination.itemsPerPage;
            
            // ถ้ามี search term ให้ filter rows ก่อน
            let visibleRows = allRows;
            if (comparisonSearchTerm) {
                visibleRows = allRows.filter(row => {
                    const referenceNo = row.getAttribute('data-reference') || '';
                    return referenceNo.includes(comparisonSearchTerm);
                });
            }
            
            const totalItems = visibleRows.length;
            const totalPages = Math.ceil(totalItems / itemsPerPage);
            const currentPage = Math.min(comparisonPagination.currentPage, totalPages || 1);
            
            // อัปเดต currentPage ถ้ามันเกิน totalPages
            if (currentPage !== comparisonPagination.currentPage) {
                comparisonPagination.currentPage = currentPage;
            }
            
            // คำนวณ range ของรายการที่จะแสดง
            const startIndex = (currentPage - 1) * itemsPerPage;
            const endIndex = Math.min(startIndex + itemsPerPage, totalItems);
            
            // ซ่อน rows ทั้งหมดก่อน
            allRows.forEach(row => {
                row.style.display = 'none';
            });
            
            // แสดงเฉพาะ rows ที่อยู่ในหน้าที่เลือก
            visibleRows.forEach((row, visibleIndex) => {
                if (visibleIndex >= startIndex && visibleIndex < endIndex) {
                    row.style.display = '';
                }
            });
            
            // อัปเดต pagination info
            const paginationInfo = document.getElementById('comparisonPaginationInfo');
            if (paginationInfo) {
                if (totalItems === 0) {
                    paginationInfo.textContent = comparisonSearchTerm ? `ไม่พบรายการที่ตรงกับ "${comparisonSearchTerm}"` : 'ไม่พบรายการ';
                } else {
                    const searchText = comparisonSearchTerm ? ` (ค้นหา: "${comparisonSearchTerm}")` : '';
                    paginationInfo.textContent = `แสดง ${startIndex + 1}-${endIndex} จาก ${totalItems} รายการ${searchText}`;
                }
            }
            
            // อัปเดต pagination navigation
            const paginationNav = document.getElementById('comparisonPaginationNav');
            if (paginationNav && totalPages > 1) {
                let navHtml = '';
                
                // ปุ่ม Previous
                if (currentPage > 1) {
                    navHtml += `<button onclick="changeComparisonPage(${currentPage - 1})" style="padding: 6px 12px; background: #334155; color: #fafafa; border: 1px solid #475569; border-radius: 6px; cursor: pointer; font-size: 0.85em; transition: all 0.3s;" onmouseover="this.style.background='#475569';" onmouseout="this.style.background='#334155';">‹ ก่อนหน้า</button>`;
                } else {
                    navHtml += `<button disabled style="padding: 6px 12px; background: #1e293b; color: #64748b; border: 1px solid #334155; border-radius: 6px; font-size: 0.85em; cursor: not-allowed;">‹ ก่อนหน้า</button>`;
                }
                
                // แสดงหมายเลขหน้า
                const maxVisiblePages = 5;
                let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
                let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
                
                // ปรับ startPage ถ้า endPage ใกล้ totalPages
                if (endPage - startPage < maxVisiblePages - 1) {
                    startPage = Math.max(1, endPage - maxVisiblePages + 1);
                }
                
                // ปุ่มหน้าแรก
                if (startPage > 1) {
                    navHtml += `<button onclick="changeComparisonPage(1)" style="padding: 6px 12px; background: #334155; color: #fafafa; border: 1px solid #475569; border-radius: 6px; cursor: pointer; font-size: 0.85em; transition: all 0.3s;" onmouseover="this.style.background='#475569';" onmouseout="this.style.background='#334155';">1</button>`;
                    if (startPage > 2) {
                        navHtml += `<span style="color: #94a3b8; padding: 0 5px;">...</span>`;
                    }
                }
                
                // หมายเลขหน้า
                for (let i = startPage; i <= endPage; i++) {
                    if (i === currentPage) {
                        navHtml += `<button disabled style="padding: 6px 12px; background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white; border: none; border-radius: 6px; font-size: 0.85em; font-weight: 600; cursor: default;">${i}</button>`;
                    } else {
                        navHtml += `<button onclick="changeComparisonPage(${i})" style="padding: 6px 12px; background: #334155; color: #fafafa; border: 1px solid #475569; border-radius: 6px; cursor: pointer; font-size: 0.85em; transition: all 0.3s;" onmouseover="this.style.background='#475569';" onmouseout="this.style.background='#334155';">${i}</button>`;
                    }
                }
                
                // ปุ่มหน้าสุดท้าย
                if (endPage < totalPages) {
                    if (endPage < totalPages - 1) {
                        navHtml += `<span style="color: #94a3b8; padding: 0 5px;">...</span>`;
                    }
                    navHtml += `<button onclick="changeComparisonPage(${totalPages})" style="padding: 6px 12px; background: #334155; color: #fafafa; border: 1px solid #475569; border-radius: 6px; cursor: pointer; font-size: 0.85em; transition: all 0.3s;" onmouseover="this.style.background='#475569';" onmouseout="this.style.background='#334155';">${totalPages}</button>`;
                }
                
                // ปุ่ม Next
                if (currentPage < totalPages) {
                    navHtml += `<button onclick="changeComparisonPage(${currentPage + 1})" style="padding: 6px 12px; background: #334155; color: #fafafa; border: 1px solid #475569; border-radius: 6px; cursor: pointer; font-size: 0.85em; transition: all 0.3s;" onmouseover="this.style.background='#475569';" onmouseout="this.style.background='#334155';">ถัดไป ›</button>`;
                } else {
                    navHtml += `<button disabled style="padding: 6px 12px; background: #1e293b; color: #64748b; border: 1px solid #334155; border-radius: 6px; font-size: 0.85em; cursor: not-allowed;">ถัดไป ›</button>`;
                }
                
                paginationNav.innerHTML = navHtml;
            } else if (paginationNav) {
                paginationNav.innerHTML = '';
            }
        }
        
        // ตัวแปรสำหรับเก็บ search term
        let comparisonSearchTerm = '';
        
        // ฟังก์ชันสำหรับค้นหาเลขที่เอกสารอ้างอิง
        function filterComparisonByReference(searchTerm) {
            comparisonSearchTerm = searchTerm.trim().toLowerCase();
            const clearBtn = document.getElementById('clearSearchBtn');
            const searchResult = document.getElementById('comparisonSearchResult');
            
            // แสดง/ซ่อนปุ่มล้าง
            if (comparisonSearchTerm) {
                clearBtn.style.display = 'block';
            } else {
                clearBtn.style.display = 'none';
                searchResult.style.display = 'none';
            }
            
            // รีเซ็ตหน้าเป็น 1 เมื่อค้นหา
            comparisonPagination.currentPage = 1;
            
            // อัปเดต pagination (จะ filter และแสดงผลให้อัตโนมัติ)
            updateComparisonPagination();
            
            // แสดงผลการค้นหา
            const activeTab = document.querySelector('.comparison-tab-content.active');
            if (comparisonSearchTerm && activeTab) {
                const allRows = Array.from(activeTab.querySelectorAll('.comparison-row'));
                const visibleCount = allRows.filter(row => {
                    const referenceNo = row.getAttribute('data-reference') || '';
                    return referenceNo.includes(comparisonSearchTerm);
                }).length;
                
                searchResult.style.display = 'block';
                if (visibleCount === 0) {
                    searchResult.textContent = `ไม่พบรายการที่ตรงกับ "${searchTerm}"`;
                    searchResult.style.color = '#ef4444';
                } else {
                    searchResult.textContent = `พบ ${visibleCount} รายการที่ตรงกับ "${searchTerm}"`;
                    searchResult.style.color = '#10b981';
                }
            } else {
                searchResult.style.display = 'none';
            }
        }
        
        // ฟังก์ชันสำหรับล้างการค้นหา
        function clearComparisonSearch() {
            const searchInput = document.getElementById('comparisonReferenceSearch');
            if (searchInput) {
                searchInput.value = '';
                filterComparisonByReference('');
            }
        }
        
        // ฟังก์ชัน normalize สำหรับเปรียบเทียบข้อความ (global function)
        function normalizeText(text) {
            if (!text) return '';
            return text
                .toLowerCase()
                .replace(/\s+/g, '')
                .replace(/[.,\-_()]/g, '')
                .replace(/บริษัท|จำกัด|co\.?|ltd\.?/gi, '')
                .trim();
        }
        
        // ฟังก์ชัน normalize สำหรับเปรียบเทียบที่อยู่ (global function)
        function normalizeAddress(address) {
            if (!address) return '';
            // แปลงเป็นตัวพิมพ์เล็ก
            let normalized = address.toLowerCase();
            // ลบคำนำหน้า "เลขที่" ที่ทำให้เปรียบเทียบไม่ตรง (บริษัทใช้ "เลขที่ 3/53" แต่ OCR ใช้ "3/53")
            normalized = normalized.replace(/^เลขที่\s*/i, '').replace(/\s*เลขที่\s*/g, ' ');
            
            // แปลงคำภาษาอังกฤษเป็นภาษาไทย (สำหรับ OCR ที่อ่านเป็นภาษาอังกฤษ)
            const transliterationMap = {
                'klongsong': 'คลองสอง',
                'klongsong': 'คลองสอง',
                'klongluang': 'คลองหลวง',
                'klong luang': 'คลองหลวง',
                'pathumthani': 'ปทุมธานี',
                'pathum thani': 'ปทุมธานี',
                'moo': 'หมู่',
                'm': 'หมู่',
                'tambon': 'ตำบล',
                'amphoe': 'อำเภอ',
                'changwat': 'จังหวัด',
                'province': 'จังหวัด'
            };
            
            // แทนที่คำภาษาอังกฤษด้วยภาษาไทย
            for (const [eng, thai] of Object.entries(transliterationMap)) {
                normalized = normalized.replace(new RegExp(eng, 'gi'), thai);
            }
            
            // แปลงรูปแบบ M0015, M015, M15 เป็น หมู่ที่ 15
            normalized = normalized.replace(/m0*(\d+)/gi, 'หมู่ที่$1');
            normalized = normalized.replace(/m\s*(\d+)/gi, 'หมู่ที่$1');
            
            // ลบคำนำหน้าที่ไม่จำเป็น (แต่เก็บเลขที่บ้านไว้)
            normalized = normalized.replace(/ห้องเลขที่\s*-\s*|ชั้นที่\s*-\s*|ถนน\s*-\s*/g, '');
            normalized = normalized.replace(/ห้องเลขที่|ชั้นที่/g, '');
            
            // ลบช่องว่างซ้ำและเครื่องหมาย
            normalized = normalized.replace(/\s+/g, ' ');
            normalized = normalized.replace(/[.,\-_]/g, '');
            
            return normalized.trim();
        }
        
        // ฟังก์ชันสำหรับ normalize ชื่อบริษัท (แปลงรูปแบบต่างๆ ให้เป็นรูปแบบมาตรฐาน)
        function normalizeCompanyNameForComparison(name) {
            if (!name) return '';
            
            let normalized = name.trim();
            
            // แปลง "บจก." เป็น "บริษัท ... จำกัด"
            normalized = normalized.replace(/^บจก\.\s*/i, 'บริษัท ');
            normalized = normalized.replace(/^บจก\s*/i, 'บริษัท ');
            
            // ถ้ายังไม่มี "จำกัด" ให้เพิ่ม
            if (!normalized.includes('จำกัด') && !normalized.includes('จํากัด')) {
                // ถ้าไม่มี "บริษัท" อยู่แล้ว ให้เพิ่ม
                if (!normalized.includes('บริษัท')) {
                    normalized = 'บริษัท ' + normalized;
                }
                normalized = normalized + ' จำกัด';
            }
            
            // ลบช่องว่างซ้ำ
            normalized = normalized.replace(/\s+/g, ' ').trim();
            
            // แปลงเป็นตัวพิมพ์เล็กสำหรับการเปรียบเทียบ
            normalized = normalized.toLowerCase();
            
            // ลบอักขระพิเศษ
            normalized = normalized.replace(/[.,\-_()]/g, '');
            
            return normalized;
        }
        
        // ฟังก์ชันคำนวณความคล้ายคลึงระหว่างสองข้อความ (Levenshtein distance)
        function calculateSimilarity(str1, str2) {
            if (!str1 || !str2) return 0;
            
            const len1 = str1.length;
            const len2 = str2.length;
            
            if (len1 === 0) return len2 === 0 ? 1 : 0;
            if (len2 === 0) return 0;
            
            // สร้าง matrix สำหรับ Levenshtein distance
            const matrix = [];
            for (let i = 0; i <= len1; i++) {
                matrix[i] = [i];
            }
            for (let j = 0; j <= len2; j++) {
                matrix[0][j] = j;
            }
            
            // คำนวณ distance
            for (let i = 1; i <= len1; i++) {
                for (let j = 1; j <= len2; j++) {
                    const cost = str1[i - 1] === str2[j - 1] ? 0 : 1;
                    matrix[i][j] = Math.min(
                        matrix[i - 1][j] + 1,      // deletion
                        matrix[i][j - 1] + 1,      // insertion
                        matrix[i - 1][j - 1] + cost // substitution
                    );
                }
            }
            
            const distance = matrix[len1][len2];
            const maxLen = Math.max(len1, len2);
            const similarity = 1 - (distance / maxLen);
            
            return similarity;
        }
        
        // ฟังก์ชันวิเคราะห์ความคล้ายคลึงของชื่อบริษัท
        function analyzeCompanyNameSimilarity(index, ocrName, companyName) {
            // Escape HTML เพื่อป้องกัน XSS
            function escapeHtml(text) {
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            }
            
            const safeOcrName = escapeHtml(ocrName);
            const safeCompanyName = escapeHtml(companyName);
            
            // Normalize ชื่อทั้งสอง
            const normalizedOcr = normalizeCompanyNameForComparison(ocrName);
            const normalizedCompany = normalizeCompanyNameForComparison(companyName);
            
            // คำนวณความคล้ายคลึง
            const similarity = calculateSimilarity(normalizedOcr, normalizedCompany);
            const similarityPercent = Math.round(similarity * 100);
            
            // ตรวจสอบว่ามีคำสำคัญที่เหมือนกันหรือไม่
            const ocrWords = normalizedOcr.split(/\s+/).filter(w => w.length > 2);
            const companyWords = normalizedCompany.split(/\s+/).filter(w => w.length > 2);
            const commonWords = ocrWords.filter(w => companyWords.includes(w));
            const commonWordsPercent = ocrWords.length > 0 ? Math.round((commonWords.length / Math.max(ocrWords.length, companyWords.length)) * 100) : 0;
            
            // ตรวจสอบรูปแบบพิเศษ
            const patterns = {
                'บจก_แปลงเป็น_บริษัท': ocrName.includes('บจก') && companyName.includes('บริษัท') && companyName.includes('จำกัด'),
                'บริษัท_แปลงเป็น_บจก': companyName.includes('บริษัท') && ocrName.includes('บจก'),
                'คำสำคัญเหมือนกัน': commonWords.length >= Math.min(ocrWords.length, companyWords.length) * 0.7
            };
            
            // สร้างข้อความวิเคราะห์
            let analysisHtml = `
                <div style="max-width: 600px; padding: 20px;">
                    <h3 style="color: #fafafa; margin-bottom: 20px; display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 1.5em;">🔍</span>
                        <span>ผลการวิเคราะห์ความคล้ายคลึง</span>
                    </h3>
                    
                    <div style="background: #1e293b; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                        <div style="color: #94a3b8; font-size: 0.9em; margin-bottom: 8px;">ชื่อจาก OCR:</div>
                        <div style="color: #cbd5e1; font-size: 1em; font-weight: 500; margin-bottom: 15px;">${safeOcrName}</div>
                        <div style="color: #94a3b8; font-size: 0.9em; margin-bottom: 8px;">ชื่อบริษัท:</div>
                        <div style="color: #cbd5e1; font-size: 1em; font-weight: 500;">${safeCompanyName}</div>
                    </div>
                    
                    <div style="background: #1e293b; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                        <div style="color: #94a3b8; font-size: 0.9em; margin-bottom: 8px;">ชื่อที่ Normalize แล้ว:</div>
                        <div style="color: #60a5fa; font-size: 0.9em; margin-bottom: 8px; font-family: monospace;">${normalizedOcr}</div>
                        <div style="color: #60a5fa; font-size: 0.9em; font-family: monospace;">${normalizedCompany}</div>
                    </div>
                    
                    <div style="background: ${similarity >= 0.8 ? '#10b98115' : similarity >= 0.6 ? '#fbbf2415' : '#ef444415'}; padding: 15px; border-radius: 8px; border-left: 4px solid ${similarity >= 0.8 ? '#10b981' : similarity >= 0.6 ? '#fbbf24' : '#ef4444'}; margin-bottom: 15px;">
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
                            <span style="color: #cbd5e1; font-weight: 600;">ระดับความคล้ายคลึง:</span>
                            <span style="color: ${similarity >= 0.8 ? '#10b981' : similarity >= 0.6 ? '#fbbf24' : '#ef4444'}; font-weight: 700; font-size: 1.2em;">${similarityPercent}%</span>
                        </div>
                        <div style="background: #0f172a; height: 8px; border-radius: 4px; overflow: hidden; margin-bottom: 10px;">
                            <div style="background: linear-gradient(90deg, ${similarity >= 0.8 ? '#10b981' : similarity >= 0.6 ? '#fbbf24' : '#ef4444'} 0%, ${similarity >= 0.8 ? '#059669' : similarity >= 0.6 ? '#d97706' : '#dc2626'} 100%); height: 100%; width: ${similarityPercent}%; transition: width 0.3s;"></div>
                        </div>
                        <div style="color: #94a3b8; font-size: 0.85em;">
                            ${similarity >= 0.8 ? '✅ คล้ายคลึงกันมาก - น่าจะเป็นบริษัทเดียวกัน' : 
                              similarity >= 0.6 ? '⚠️ คล้ายคลึงกันปานกลาง - อาจเป็นบริษัทเดียวกัน' : 
                              '❌ คล้ายคลึงกันน้อย - อาจไม่ใช่บริษัทเดียวกัน'}
                        </div>
                    </div>
            `;
            
            // แสดงรูปแบบที่พบ
            if (patterns['บจก_แปลงเป็น_บริษัท'] || patterns['บริษัท_แปลงเป็น_บจก']) {
                analysisHtml += `
                    <div style="background: #10b98115; padding: 12px; border-radius: 8px; border-left: 4px solid #10b981; margin-bottom: 15px;">
                        <div style="color: #10b981; font-weight: 600; margin-bottom: 5px;">✓ พบรูปแบบที่คล้ายกัน:</div>
                        <div style="color: #cbd5e1; font-size: 0.9em;">
                            ${patterns['บจก_แปลงเป็น_บริษัท'] ? '• "บจก." ถูกแปลงเป็น "บริษัท ... จำกัด" (เป็นรูปแบบมาตรฐานเดียวกัน)' : ''}
                            ${patterns['บริษัท_แปลงเป็น_บจก'] ? '• "บริษัท ... จำกัด" ถูกแปลงเป็น "บจก." (เป็นรูปแบบมาตรฐานเดียวกัน)' : ''}
                        </div>
                    </div>
                `;
            }
            
            // แสดงคำที่เหมือนกัน
            if (commonWords.length > 0) {
                analysisHtml += `
                    <div style="background: #1e293b; padding: 12px; border-radius: 8px; margin-bottom: 15px;">
                        <div style="color: #94a3b8; font-size: 0.9em; margin-bottom: 8px;">คำที่เหมือนกัน (${commonWords.length} คำ):</div>
                        <div style="color: #60a5fa; font-size: 0.9em;">
                            ${commonWords.map(w => `<span style="background: #3b82f615; padding: 2px 6px; border-radius: 4px; margin-right: 4px;">${w}</span>`).join('')}
                        </div>
                        <div style="color: #94a3b8; font-size: 0.85em; margin-top: 8px;">
                            ความเหมือนของคำ: ${commonWordsPercent}%
                        </div>
                    </div>
                `;
            }
            
            // คำแนะนำ
            let recommendation = '';
            let recommendationColor = '';
            if (similarity >= 0.8 || patterns['บจก_แปลงเป็น_บริษัท'] || patterns['บริษัท_แปลงเป็น_บจก']) {
                recommendation = '✅ แนะนำให้อนุมัติ: ชื่อบริษัทคล้ายคลึงกันมาก และเป็นรูปแบบมาตรฐานเดียวกัน (บจก. = บริษัท ... จำกัด)';
                recommendationColor = '#10b981';
            } else if (similarity >= 0.6 && commonWordsPercent >= 50) {
                recommendation = '⚠️ พิจารณาอนุมัติ: ชื่อบริษัทคล้ายคลึงกันปานกลาง แต่มีคำสำคัญที่เหมือนกัน';
                recommendationColor = '#fbbf24';
            } else {
                recommendation = '❌ ไม่แนะนำให้อนุมัติ: ชื่อบริษัทคล้ายคลึงกันน้อย อาจไม่ใช่บริษัทเดียวกัน';
                recommendationColor = '#ef4444';
            }
            
            analysisHtml += `
                    <div style="background: ${recommendationColor}15; padding: 15px; border-radius: 8px; border-left: 4px solid ${recommendationColor}; margin-bottom: 15px;">
                        <div style="color: ${recommendationColor}; font-weight: 600; margin-bottom: 8px;">💡 คำแนะนำ:</div>
                        <div style="color: #cbd5e1; font-size: 0.95em; line-height: 1.6;">${recommendation}</div>
                    </div>
                    
                    <div style="display: flex; gap: 10px; margin-top: 20px;">
                        <button onclick="approveField(${index}, 'company_name_match', 'ชื่อบริษัท'); closeAnalysisModal();" style="flex: 1; padding: 12px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 600; transition: all 0.3s;" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(16, 185, 129, 0.4)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';">✓ อนุมัติ</button>
                        <button onclick="closeAnalysisModal();" style="flex: 1; padding: 12px; background: #334155; color: #cbd5e1; border: 1px solid #475569; border-radius: 8px; cursor: pointer; font-weight: 600; transition: all 0.3s;" onmouseover="this.style.background='#475569';" onmouseout="this.style.background='#334155';">ปิด</button>
                    </div>
                </div>
            `;
            
            // สร้าง modal
            const modal = document.createElement('div');
            modal.id = 'companyNameAnalysisModal';
            modal.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.7); z-index: 10000; display: flex; align-items: center; justify-content: center; padding: 20px;';
            modal.innerHTML = `
                <div style="background: #0f172a; border-radius: 12px; max-width: 700px; width: 100%; max-height: 90vh; overflow-y: auto; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);">
                    ${analysisHtml}
                </div>
            `;
            
            modal.onclick = function(e) {
                if (e.target === modal) {
                    closeAnalysisModal();
                }
            };
            
            document.body.appendChild(modal);
            
            // ฟังก์ชันปิด modal
            window.closeAnalysisModal = function() {
                const modal = document.getElementById('companyNameAnalysisModal');
                if (modal) {
                    modal.remove();
                }
            };
        }
        
        // Helper function: หา row element ใน tab ที่ active อยู่
        function findRowInActiveTab(index) {
            const activeTabContent = document.querySelector('.comparison-tab-content.active');
            if (activeTabContent) {
                // หา row ที่มี index ตรงกันใน active tab โดยใช้ data-index attribute
                const rows = activeTabContent.querySelectorAll('.comparison-row');
                for (let row of rows) {
                    const rowIndex = parseInt(row.getAttribute('data-index'));
                    if (rowIndex === index) {
                        return row;
                    }
                }
                // Fallback: หาโดยใช้ ID (ถ้ายังมี)
                const row = activeTabContent.querySelector(`#comparison-row-${index}`);
                if (row) {
                    return row;
                }
            }
            // Fallback: หา row แรกที่เจอ (สำหรับกรณีที่ไม่มี active tab)
            return document.querySelector(`[data-index="${index}"]`);
        }
        
        function toggleComparisonRow(index) {
            const row = findRowInActiveTab(index);
            if (row) {
                // ปิด rows อื่นๆ ที่เปิดอยู่ (optional - ถ้าต้องการให้เปิดได้ทีละ row เดียว)
                // const allExpandedRows = document.querySelectorAll('.comparison-row.expanded');
                // allExpandedRows.forEach(r => {
                //     if (r !== row) {
                //         r.classList.remove('expanded');
                //     }
                // });
                
                row.classList.toggle('expanded');
                console.log(`🔄 Toggled row ${index}, expanded: ${row.classList.contains('expanded')}`);
            } else {
                console.warn(`⚠️ Row ${index} not found in active tab`);
            }
        }
        
        // ฟังก์ชันสำหรับแสดง PDF Preview (เปิดในแท็บใหม่)
        async function viewPdfPreview(referenceNo, index) {
            console.log('📄 viewPdfPreview called:', referenceNo);
            
            try {
                // ดึงค่าจาก form
                const taxMonth = document.getElementById('taxMonth')?.value;
                const taxYear = document.getElementById('taxYear')?.value;
                const company = document.getElementById('companyValue')?.value || document.getElementById('companySelect')?.value;
                
                // ตรวจสอบว่ามีค่าครบถ้วนหรือไม่
                if (!taxMonth || !taxYear || !company) {
                    alert('ไม่พบข้อมูลเดือนภาษีหรือบริษัท กรุณาเลือกข้อมูลก่อนดู PDF');
                    return;
                }
                
                // สร้าง taxMonth ในรูปแบบ YYYY-MM
                const taxMonthFormatted = `${taxYear}-${taxMonth}`;
                
                console.log('📊 Sending data:', {
                    referenceNo: referenceNo,
                    taxMonth: taxMonthFormatted,
                    company: company
                });
                
                // เรียก API เพื่อค้นหาไฟล์ PDF
                const response = await fetch('/api/auditcheck/find-pdf-by-reference', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        referenceNo: referenceNo,
                        taxMonth: taxMonthFormatted,
                        company: company
                    })
                });
                
                const result = await response.json();
                console.log('📊 API Response:', result);
                
                if (result.success && result.found) {
                    // เปิดไฟล์ในแท็บใหม่
                    const fileUrl = `/api/auditcheck/view-pdf/${encodeURIComponent(result.pdfPath)}`;
                    window.open(fileUrl, '_blank', 'noopener,noreferrer');
                } else {
                    alert(result.message || result.error || 'ไม่พบไฟล์ (PDF/JPG/PNG) สำหรับเลขที่อ้างอิงนี้');
                }
            } catch (error) {
                console.error('❌ Error finding file:', error);
                alert('เกิดข้อผิดพลาดในการค้นหาไฟล์: ' + error.message);
            }
        }
        
        // ฟังก์ชันแสดง PDF/Image Modal
        function showPdfModal(filePath, filename, referenceNo) {
            // ตรวจสอบประเภทไฟล์จากนามสกุล
            const fileExtension = filename.split('.').pop().toLowerCase();
            const isImage = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'tif'].includes(fileExtension);
            const isPdf = fileExtension === 'pdf';
            
            // กำหนด icon และ title ตามประเภทไฟล์
            let fileIcon = '📄';
            let fileTypeLabel = 'Preview';
            if (isImage) {
                fileIcon = '🖼️';
                fileTypeLabel = 'Preview รูปภาพ';
            } else if (isPdf) {
                fileIcon = '📄';
                fileTypeLabel = 'Preview PDF';
            }
            
            // สร้าง modal HTML
            let contentHtml = '';
            if (isImage) {
                // แสดงรูปภาพ
                contentHtml = `
                    <div style="flex: 1; overflow: auto; padding: 20px; background: #0f172a; display: flex; align-items: center; justify-content: center;">
                        <img src="/api/auditcheck/view-pdf/${encodeURIComponent(filePath)}" 
                             alt="${filename}" 
                             style="max-width: 100%; max-height: 100%; object-fit: contain; border-radius: 8px; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);" 
                             onerror="this.onerror=null; this.src='data:image/svg+xml,%3Csvg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'400\\' height=\\'300\\'%3E%3Crect fill=\\'%23ef4444\\' width=\\'400\\' height=\\'300\\'/%3E%3Ctext fill=\\'white\\' font-family=\\'Arial\\' font-size=\\'20\\' x=\\'50%25\\' y=\\'50%25\\' text-anchor=\\'middle\\' dominant-baseline=\\'middle\\'%3Eไม่สามารถโหลดรูปภาพได้%3C/text%3E%3C/svg%3E';">
                    </div>
                `;
            } else {
                // แสดง PDF ด้วย iframe
                contentHtml = `
                    <div style="flex: 1; overflow: hidden; padding: 20px; background: #0f172a;">
                        <iframe src="/api/auditcheck/view-pdf/${encodeURIComponent(filePath)}" 
                                style="width: 100%; height: 100%; border: none; border-radius: 8px; background: white;"></iframe>
                    </div>
                `;
            }
            
            const modalHtml = `
                <div id="pdfPreviewModal" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); z-index: 10000; display: flex; align-items: center; justify-content: center; padding: 20px;">
                    <div style="background: #1e293b; border-radius: 12px; width: 95%; max-width: 1200px; height: 90vh; display: flex; flex-direction: column; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);">
                        <!-- Header -->
                        <div style="padding: 20px; border-bottom: 1px solid #334155; display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <h3 style="margin: 0; color: #fafafa; font-size: 1.2em; display: flex; align-items: center; gap: 10px;">
                                    <span style="font-size: 1.5em;">${fileIcon}</span>
                                    <span>${fileTypeLabel}</span>
                                </h3>
                                <p style="margin: 5px 0 0 34px; color: #94a3b8; font-size: 0.9em;">เลขที่อ้างอิง: ${referenceNo}</p>
                                <p style="margin: 2px 0 0 34px; color: #64748b; font-size: 0.85em;">${filename}</p>
                            </div>
                            <button onclick="closePdfModal()" style="background: #ef4444; color: white; border: none; border-radius: 6px; padding: 10px 20px; cursor: pointer; font-size: 1em; font-weight: 600; transition: all 0.3s;" onmouseover="this.style.background='#dc2626'" onmouseout="this.style.background='#ef4444'">
                                ✕ ปิด
                            </button>
                        </div>
                        <!-- Content -->
                        ${contentHtml}
                    </div>
                </div>
            `;
            
            // เพิ่ม modal เข้าไปใน body
            document.body.insertAdjacentHTML('beforeend', modalHtml);
            
            // เพิ่ม event listener สำหรับปิด modal เมื่อคลิกนอก modal
            document.getElementById('pdfPreviewModal').addEventListener('click', function(e) {
                if (e.target.id === 'pdfPreviewModal') {
                    closePdfModal();
                }
            });
        }
        
        // ฟังก์ชันปิด PDF Modal
        function closePdfModal() {
            const modal = document.getElementById('pdfPreviewModal');
            if (modal) {
                modal.remove();
            }
        }
        
        // เก็บหมายเหตุในตัวแปร global
        let comparisonNotes = {};
        
        // เก็บ initial note (หมายเหตุเดิม) เพื่อ restore เมื่อยกเลิกการอนุมัติ
        let initialNotes = {};
        
        // เก็บสถานะการอนุมัติในตัวแปร global
        let comparisonApprovals = {};
        
        // เก็บ path ของโฟลเดอร์ VAT
        let vatFolderPath = null;
        
        // เก็บสถานะเอกสารใช้ไม่ได้ (key = index, value = true/false)
        let invalidDocuments = {};
        
        // เก็บสถานะโหมด "ตรวจด้วยตัวเอง" (key = index, value = true/false)
        let selfCheckMode = {};
        
        // เก็บข้อมูล comparisons ทั้งหมดเพื่อใช้ในฟังก์ชัน markAllDocumentsAsInvalid
        let allComparisonsData = [];
        
        // ตัวแปรสำหรับ pagination
        let comparisonPagination = {
            currentPage: 1,
            itemsPerPage: 25, // ค่าเริ่มต้น
            currentTab: 'all'
        };
        
        // ========== ระบบบันทึกสถานะการตรวจสอบ (Auto-save/Auto-restore) ==========
        
        // ตัวแปรสำหรับเก็บสถานะการบันทึก
        let saveStateTimeout = null;
        const SAVE_STATE_DEBOUNCE_MS = 2000; // บันทึกหลังจากไม่มีการเปลี่ยนแปลง 2 วินาที
        
        /**
         * สร้าง key สำหรับเก็บสถานะใน LocalStorage
         * รองรับการแยกสาขาสำหรับบริษัทพิเศษ
         */
        function getStateKey(company, taxMonth) {
            if (!company || !taxMonth) return null;
            
            // สำหรับบริษัทพิเศษที่มีสาขา ให้รวมสาขาเข้าไปใน key
            if (selectedBranch && baseCompanyName) {
                const specialCompany = "Build214 บริษัท เอส.ยู. คอมพาเนียน จำกัด รายเดือน";
                if (baseCompanyName === specialCompany) {
                    // ใช้ชื่อสาขาใน key เพื่อแยกข้อมูลตามสาขา
                    const branchName = selectedBranch.name.replace(/[\/\\:]/g, '_');
                    return `auditcheck_state_${baseCompanyName}_${branchName}_${taxMonth}`;
                }
            }
            
            return `auditcheck_state_${company}_${taxMonth}`;
        }
        
        /**
         * บันทึกสถานะการตรวจสอบทั้งหมดลง LocalStorage และ Backend
         */
        function saveAuditState() {
            const taxMonth = document.getElementById('taxMonth')?.value;
            const taxYear = document.getElementById('taxYear')?.value;
            const company = document.getElementById('companyValue')?.value || document.getElementById('companySelect')?.value;
            
            if (!taxMonth || !taxYear || !company) {
                console.log('⚠️ ไม่สามารถบันทึกสถานะ: ยังไม่ได้เลือกเดือนภาษีหรือบริษัท');
                return;
            }
            
            const taxMonthFormatted = `${taxYear}-${taxMonth}`;
            const stateKey = getStateKey(company, taxMonthFormatted);
            
            if (!stateKey) {
                console.error('❌ ไม่สามารถสร้าง state key ได้');
                return;
            }
            
            // รวบรวมข้อมูลสถานะทั้งหมด
            const now = new Date();
            
            // สำหรับบริษัทพิเศษที่มีสาขา ให้เก็บข้อมูลสาขาด้วย
            let branchInfo = null;
            if (selectedBranch && baseCompanyName) {
                const specialCompany = "Build214 บริษัท เอส.ยู. คอมพาเนียน จำกัด รายเดือน";
                if (baseCompanyName === specialCompany) {
                    branchInfo = {
                        branch_name: selectedBranch.name,
                        branch_path: selectedBranch.path,
                        base_company: baseCompanyName
                    };
                }
            }
            
            const auditState = {
                version: '1.1', // เพิ่มเวอร์ชันเพื่อรองรับสาขา
                timestamp: now.toISOString(),
                last_saved: now.toISOString(), // วันที่และเวลาล่าสุดที่บันทึก
                company: company,
                base_company: baseCompanyName || company, // เก็บชื่อบริษัทหลักด้วย
                branch_info: branchInfo, // ข้อมูลสาขา (ถ้ามี)
                taxMonth: taxMonthFormatted,
                taxYear: taxYear,
                taxMonthValue: taxMonth,
                
                // ข้อมูลการตรวจสอบ
                comparisonNotes: comparisonNotes,
                initialNotes: initialNotes, // เก็บ initial notes เพื่อ restore
                comparisonApprovals: comparisonApprovals,
                invalidDocuments: invalidDocuments,
                selfCheckMode: selfCheckMode, // เก็บสถานะโหมด "ตรวจด้วยตัวเอง"
                vatFolderPath: vatFolderPath,
                
                // ข้อมูล Step 4 (OCR)
                step4OCRData: step4OCRData ? {
                    count: step4OCRData.length,
                    // เก็บเฉพาะ metadata เพื่อประหยัดพื้นที่ (ถ้าต้องการข้อมูลเต็มให้โหลดจาก backend)
                    metadata: step4OCRData.map(item => ({
                        filename: item.filename || item.old_filename,
                        document_no: item.document_no,
                        company_name: item.company_name
                    }))
                } : null,
                
                // ข้อมูล comparisons (เก็บเฉพาะ metadata)
                comparisonResults: window.comparisonResults ? {
                    count: window.comparisonResults.length,
                    metadata: window.comparisonResults.map((comp, idx) => ({
                        index: idx,
                        purchase_reference: comp.purchase_data?.reference_no,
                        ocr_document_no: comp.ocr_data?.document_no,
                        match_status: comp.match_status
                    }))
                } : null,
                
                // Step ที่ทำเสร็จแล้ว
                completedSteps: {
                    step1: document.getElementById('step1')?.classList.contains('completed') || false,
                    step2: document.getElementById('step2')?.classList.contains('completed') || false,
                    step3: document.getElementById('step3')?.classList.contains('completed') || false,
                    step4: document.getElementById('step4')?.classList.contains('completed') || false,
                    step5: document.getElementById('step5')?.classList.contains('completed') || false
                }
            };
            
            // บันทึกลง LocalStorage
            try {
                localStorage.setItem(stateKey, JSON.stringify(auditState));
                console.log('✅ บันทึกสถานะลง LocalStorage:', stateKey);
            } catch (error) {
                console.error('❌ ไม่สามารถบันทึกลง LocalStorage:', error);
            }
            
            // บันทึกลง Backend (async, ไม่ต้องรอ)
            saveAuditStateToBackend(auditState).catch(error => {
                console.error('❌ ไม่สามารถบันทึกลง Backend:', error);
            });
        }
        
        /**
         * บันทึกสถานะลง Backend
         */
        async function saveAuditStateToBackend(auditState) {
            try {
                const response = await fetch('/api/auditcheck/save-state', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(auditState)
                });
                
                if (response.ok) {
                    const result = await response.json();
                    console.log('✅ บันทึกสถานะลง Backend สำเร็จ:', result.message || 'OK');
                } else {
                    console.warn('⚠️ ไม่สามารถบันทึกลง Backend:', response.status);
                }
            } catch (error) {
                console.error('❌ Error saving state to backend:', error);
            }
        }
        
        /**
         * โหลดสถานะการตรวจสอบจาก LocalStorage และ Backend
         * รองรับการแยกสาขาสำหรับบริษัทพิเศษ
         */
        async function loadAuditState(company, taxMonthFormatted) {
            // สำหรับบริษัทพิเศษที่มีสาขา ให้ใช้ baseCompanyName สำหรับสร้าง stateKey
            // แต่ใช้ company (path) สำหรับการเรียก API
            let companyForStateKey = company;
            if (selectedBranch && baseCompanyName) {
                const specialCompany = "Build214 บริษัท เอส.ยู. คอมพาเนียน จำกัด รายเดือน";
                if (baseCompanyName === specialCompany) {
                    // ใช้ baseCompanyName สำหรับสร้าง stateKey เพื่อให้ตรงกับที่บันทึกไว้
                    companyForStateKey = baseCompanyName;
                }
            }
            
            const stateKey = getStateKey(companyForStateKey, taxMonthFormatted);
            
            if (!stateKey) {
                console.log('⚠️ ไม่สามารถโหลดสถานะ: ไม่มี company หรือ taxMonth');
                return null;
            }
            
            // ลองโหลดจาก LocalStorage ก่อน
            let auditState = null;
            try {
                const savedState = localStorage.getItem(stateKey);
                if (savedState) {
                    auditState = JSON.parse(savedState);
                    console.log('✅ โหลดสถานะจาก LocalStorage:', stateKey);
                }
            } catch (error) {
                console.error('❌ ไม่สามารถโหลดจาก LocalStorage:', error);
            }
            
            // ลองโหลดจาก Backend (ถ้า LocalStorage ไม่มีหรือเก่าเกินไป)
            try {
                // สำหรับบริษัทพิเศษที่มีสาขา ให้ส่งข้อมูลสาขาไปด้วย
                let loadUrl = `/api/auditcheck/load-state?company=${encodeURIComponent(company)}&taxMonth=${encodeURIComponent(taxMonthFormatted)}`;
                if (selectedBranch && baseCompanyName) {
                    const specialCompany = "Build214 บริษัท เอส.ยู. คอมพาเนียน จำกัด รายเดือน";
                    if (baseCompanyName === specialCompany) {
                        loadUrl += `&branch_name=${encodeURIComponent(selectedBranch.name)}&base_company=${encodeURIComponent(baseCompanyName)}`;
                    }
                }
                
                const response = await fetch(loadUrl);
                if (response.ok) {
                    const backendState = await response.json();
                    if (backendState.success && backendState.state) {
                        // เปรียบเทียบ timestamp (ใช้ backend ถ้าใหม่กว่า)
                        if (!auditState || !auditState.timestamp || 
                            new Date(backendState.state.timestamp) > new Date(auditState.timestamp)) {
                            auditState = backendState.state;
                            console.log('✅ โหลดสถานะจาก Backend (ใหม่กว่า):', stateKey);
                            // อัพเดท LocalStorage ด้วย
                            localStorage.setItem(stateKey, JSON.stringify(auditState));
                        }
                    }
                }
            } catch (error) {
                console.error('❌ ไม่สามารถโหลดจาก Backend:', error);
            }
            
            return auditState;
        }
        
        /**
         * Restore สถานะการตรวจสอบ
         */
        function restoreAuditState(auditState) {
            if (!auditState) {
                console.log('⚠️ ไม่มีสถานะที่บันทึกไว้');
                return false;
            }
            
            console.log('🔄 กำลัง restore สถานะการตรวจสอบ...');
            
            // Restore ข้อมูลพื้นฐาน
            if (auditState.taxYear && document.getElementById('taxYear')) {
                document.getElementById('taxYear').value = auditState.taxYear;
            }
            if (auditState.taxMonthValue && document.getElementById('taxMonth')) {
                document.getElementById('taxMonth').value = auditState.taxMonthValue;
            }
            if (auditState.company && (document.getElementById('companyValue') || document.getElementById('companySelect'))) {
                const companyInput = document.getElementById('companyValue') || document.getElementById('companySelect');
                if (companyInput) companyInput.value = auditState.company;
            }
            
            // Restore ข้อมูลการตรวจสอบ
            if (auditState.comparisonNotes) {
                comparisonNotes = auditState.comparisonNotes;
                console.log('✅ Restore comparisonNotes:', Object.keys(comparisonNotes).length, 'items');
            }
            
            if (auditState.initialNotes) {
                initialNotes = auditState.initialNotes;
                console.log('✅ Restore initialNotes:', Object.keys(initialNotes).length, 'items');
            }
            
            if (auditState.comparisonApprovals) {
                comparisonApprovals = auditState.comparisonApprovals;
                console.log('✅ Restore comparisonApprovals:', Object.keys(comparisonApprovals).length, 'items');
            }
            
            if (auditState.invalidDocuments) {
                invalidDocuments = auditState.invalidDocuments;
                console.log('✅ Restore invalidDocuments:', Object.keys(invalidDocuments).length, 'items');
            }
            
            if (auditState.selfCheckMode) {
                selfCheckMode = auditState.selfCheckMode;
                console.log('✅ Restore selfCheckMode:', Object.keys(selfCheckMode).length, 'items');
            }
            
            if (auditState.vatFolderPath) {
                vatFolderPath = auditState.vatFolderPath;
                console.log('✅ Restore vatFolderPath:', vatFolderPath);
            }
            
            // Restore Step ที่ทำเสร็จแล้ว (แสดง visual indicator)
            if (auditState.completedSteps) {
                Object.keys(auditState.completedSteps).forEach(stepId => {
                    const stepElement = document.getElementById(stepId);
                    if (stepElement && auditState.completedSteps[stepId]) {
                        stepElement.classList.add('completed');
                        console.log(`✅ Restore ${stepId}: completed`);
                    }
                });
            }
            
            console.log('✅ Restore สถานะเสร็จสิ้น');
            return true;
        }
        
        /**
         * Auto-save ด้วย debounce (เรียกเมื่อมีการเปลี่ยนแปลงข้อมูล)
         */
        function triggerAutoSave() {
            // Clear timeout เดิม
            if (saveStateTimeout) {
                clearTimeout(saveStateTimeout);
            }
            
            // ตั้ง timeout ใหม่
            saveStateTimeout = setTimeout(() => {
                saveAuditState();
                saveStateTimeout = null;
            }, SAVE_STATE_DEBOUNCE_MS);
        }
        
        // ========== จบระบบบันทึกสถานะ ==========
        
        // ฟังก์ชันบันทึกหมายเหตุ (แก้ไขให้ trigger auto-save)
        function saveNote(index, noteText) {
            comparisonNotes[index] = noteText;
            console.log('📝 Note saved for index', index, ':', noteText);
            triggerAutoSave(); // Trigger auto-save
        }
        
        // ฟังก์ชันอนุมัติฟิลด์เฉพาะจุด
        function approveField(index, fieldKey, fieldLabel) {
            const approvalKey = `${index}-${fieldKey}`;
            
            // บันทึกสถานะการอนุมัติ (ไม่ต้องยืนยัน)
            comparisonApprovals[approvalKey] = true;
            console.log('✅ Field approved:', approvalKey, fieldLabel);
            console.log(`🔍 [Debug] comparisonApprovals หลังอนุมัติ:`, Object.keys(comparisonApprovals).filter(k => k.startsWith(`${index}-`)));
            
            // รีเฟรชการแสดงผล (หา row ใน tab ที่ active อยู่)
            const row = findRowInActiveTab(index);
            if (row) {
                // หาปุ่มอนุมัติที่ตรงกับ fieldKey โดยใช้ data attributes เป็นหลัก
                // วิธีที่ 1: หาจาก data-field-key และ data-field-index และตรวจสอบว่าเป็นปุ่มอนุมัติ (รวมทั้งใน company-data-section)
                let approveButtons = Array.from(row.querySelectorAll(`button[data-field-key="${fieldKey}"][data-field-index="${index}"]`)).filter(btn => 
                    btn.textContent && (btn.textContent.includes('อนุมัติ') || btn.textContent.includes('✓'))
                );
                
                // วิธีที่ 2: ถ้าไม่เจอ ให้หาจาก onclick attribute (สำหรับปุ่มที่สร้างจาก HTML)
                if (approveButtons.length === 0) {
                    approveButtons = Array.from(row.querySelectorAll(`button[onclick*="approveField(${index}, '${fieldKey}'"]`));
                }
                
                // วิธีที่ 3: หาจาก field container ที่มี data-field-key ตรงกัน
                if (approveButtons.length === 0) {
                    const fieldContainer = row.querySelector(`.comparison-field[data-field-key="${fieldKey}"][data-field-index="${index}"]`);
                    if (fieldContainer) {
                        const button = fieldContainer.querySelector('button');
                        if (button && button.textContent && (button.textContent.includes('อนุมัติ') || button.textContent.includes('✓'))) {
                            approveButtons = [button];
                        }
                    }
                }
                
                // วิธีที่ 4: หาจาก company-data-section (สำหรับข้อมูลบริษัท)
                if (approveButtons.length === 0 && (fieldKey === 'company_name_match' || fieldKey === 'tax_id_match' || fieldKey === 'address_match')) {
                    const companyDataSection = row.querySelector('.company-data-section');
                    if (companyDataSection) {
                        const companyButtons = Array.from(companyDataSection.querySelectorAll(`button[data-field-key="${fieldKey}"][data-field-index="${index}"]`)).filter(btn => 
                            btn.textContent && (btn.textContent.includes('อนุมัติ') || btn.textContent.includes('✓'))
                        );
                        if (companyButtons.length > 0) {
                            approveButtons = companyButtons;
                        }
                    }
                }
                
                console.log(`🔍 Found ${approveButtons.length} approve buttons for field ${fieldKey} at index ${index}`);
                
                approveButtons.forEach(approveButton => {
                    // หา fieldContainer (อาจอยู่ใน comparison-field หรือ company-data-section)
                    let fieldContainer = approveButton.closest('.comparison-field');
                    if (!fieldContainer) {
                        // ถ้าไม่เจอใน comparison-field ให้หาจาก company-data-section
                        const companyDataSection = approveButton.closest('.company-data-section');
                        if (companyDataSection) {
                            fieldContainer = companyDataSection;
                        }
                    }
                    
                    if (fieldContainer) {
                        // หา fieldValue ทั้งสองฝั่ง (ภาษีซื้อและ OCR) - สำหรับ comparison-field เท่านั้น
                        const fieldValue = fieldContainer.querySelector('.comparison-field-value');
                        if (fieldValue) {
                            // เปลี่ยนสีของ fieldValue
                            fieldValue.style.color = '#10b981';
                            fieldValue.style.fontWeight = '400';
                            fieldValue.classList.remove('mismatch');
                            fieldValue.classList.add('approved');
                        }
                        
                        // เปลี่ยนปุ่มเป็นปุ่ม "ยกเลิก"
                        const cancelButton = document.createElement('button');
                        cancelButton.onclick = () => cancelApproval(index, fieldKey, fieldLabel);
                        cancelButton.setAttribute('data-field-key', fieldKey);
                        cancelButton.setAttribute('data-field-index', String(index));
                        
                        // กำหนด style ตามตำแหน่งของปุ่ม (company-data-section หรือ comparison-field)
                        const isInCompanyData = approveButton.closest('.company-data-section') !== null;
                        if (isInCompanyData) {
                            cancelButton.style.cssText = 'padding: 6px 12px; background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.85em; font-weight: 600; display: flex; align-items: center; gap: 6px; transition: all 0.3s; white-space: nowrap;';
                        } else {
                            cancelButton.style.cssText = 'padding: 4px 10px; background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.8em; font-weight: 600; display: flex; align-items: center; gap: 4px; transition: all 0.3s; white-space: nowrap;';
                        }
                        
                        cancelButton.setAttribute('onmouseover', "this.style.transform='scale(1.05)'; this.style.boxShadow='0 2px 8px rgba(239, 68, 68, 0.4)';");
                        cancelButton.setAttribute('onmouseout', "this.style.transform='scale(1)'; this.style.boxShadow='none';");
                        cancelButton.setAttribute('title', 'ยกเลิกการอนุมัติ');
                        cancelButton.innerHTML = '<span style="font-size: 1em;">✕</span> ยกเลิก';
                        approveButton.replaceWith(cancelButton);
                        console.log(`✅ เปลี่ยนปุ่มอนุมัติเป็นปุ่มยกเลิก: ${fieldKey} (ใน ${isInCompanyData ? 'company-data-section' : 'comparison-field'})`);
                    }
                });
                
                // อัพเดทฝั่ง OCR ด้วย
                const ocrSide = row.querySelector('.comparison-side.ocr');
                if (ocrSide) {
                    const ocrFields = ocrSide.querySelectorAll('.comparison-field');
                    ocrFields.forEach(ocrField => {
                        const ocrLabel = ocrField.querySelector('.comparison-field-label');
                        if (ocrLabel) {
                            // ตรวจสอบว่าเป็น field ที่ตรงกันหรือไม่
                            let isTargetField = false;
                            if (fieldKey === 'tax_id_match' && ocrLabel.textContent.includes('เลขประจำตัวผู้เสียภาษี')) {
                                isTargetField = true;
                            } else if (fieldKey === 'company_name_match' && ocrLabel.textContent.includes('ชื่อบริษัท')) {
                                isTargetField = true;
                            } else if (fieldKey === 'branch_match' && ocrLabel.textContent.includes('สาขา')) {
                                isTargetField = true;
                            } else if (fieldKey === 'document_no_match' && ocrLabel.textContent.includes('เลขที่เอกสาร')) {
                                isTargetField = true;
                            } else if (fieldKey === 'date_match' && ocrLabel.textContent.includes('วันที่')) {
                                isTargetField = true;
                            } else if (fieldKey === 'amount_before_vat_match' && ocrLabel.textContent.includes('ยอดก่อนภาษี')) {
                                isTargetField = true;
                            } else if (fieldKey === 'vat_amount_match' && ocrLabel.textContent.includes('ยอดภาษีมูลค่าเพิ่ม')) {
                                isTargetField = true;
                            } else if (fieldKey === 'total_amount_match' && ocrLabel.textContent.includes('ยอดหลังบวก')) {
                                isTargetField = true;
                            } else if (fieldKey === 'document_type_match' && ocrLabel.textContent.includes('ประเภทเอกสาร')) {
                                isTargetField = true;
                            } else if (fieldKey === 'reference_no_match' && ocrLabel.textContent.includes('เลขที่เอกสารอ้างอิง')) {
                                isTargetField = true;
                            }
                            
                            if (isTargetField) {
                                const ocrValue = ocrField.querySelector('.comparison-field-value');
                                if (ocrValue) {
                                    ocrValue.style.color = '#10b981';
                                    ocrValue.style.fontWeight = '400';
                                    ocrValue.classList.remove('mismatch');
                                    ocrValue.classList.add('approved');
                                }
                            }
                        }
                    });
                }
                
                // อัพเดท UI ในส่วนข้อมูลบริษัท (company_name_match, tax_id_match, address_match)
                const companyDataSection = row.querySelector('.company-data-section');
                if (companyDataSection) {
                    // อัพเดทสถานะชื่อบริษัท
                    if (fieldKey === 'company_name_match') {
                        // หา span ที่มีข้อความ "ผลการเปรียบเทียบชื่อ"
                        const allSpans = companyDataSection.querySelectorAll('span');
                        allSpans.forEach(span => {
                            if (span.textContent && span.textContent.includes('ผลการเปรียบเทียบชื่อ')) {
                                span.textContent = 'ผลการเปรียบเทียบชื่อ: ✅ อนุมัติแล้ว';
                                span.style.color = '#10b981';
                            }
                        });
                        
                        // อัพเดทสีของชื่อทั้งสองฝั่ง (ใช้วิธีที่แม่นยำกว่า)
                        const allDivs = companyDataSection.querySelectorAll('div');
                        allDivs.forEach(div => {
                            const divText = div.textContent || '';
                            // หา div ที่มี label "ชื่อจาก OCR:" หรือ "ชื่อบริษัท:"
                            if (divText.trim() === 'ชื่อจาก OCR:' || divText.trim() === 'ชื่อบริษัท:') {
                                // หา div ถัดไปที่เป็น name value box
                                let nextDiv = div.nextElementSibling;
                                // ข้าม element อื่นๆ จนกว่าจะเจอ div
                                while (nextDiv && (nextDiv.tagName !== 'DIV' || nextDiv.textContent.trim() === '')) {
                                    nextDiv = nextDiv.nextElementSibling;
                                }
                                if (nextDiv && nextDiv.tagName === 'DIV' && nextDiv.textContent.trim() !== '') {
                                    nextDiv.style.color = '#10b981';
                                    nextDiv.style.fontWeight = '600';
                                    console.log(`✅ อัพเดทสีชื่อ: ${divText.trim()} -> ${nextDiv.textContent.substring(0, 20)}...`);
                                }
                            }
                        });
                        
                        // อัพเดทสีของ container
                        const containers = companyDataSection.querySelectorAll('div[style*="border-left"]');
                        containers.forEach(container => {
                            if (container.textContent && container.textContent.includes('ผลการเปรียบเทียบชื่อ')) {
                                container.style.background = '#10b98115';
                                container.style.borderLeftColor = '#10b981';
                            }
                        });
                    }
                    
                    // อัพเดทสถานะเลขประจำตัวผู้เสียภาษี
                    if (fieldKey === 'tax_id_match') {
                        // หา span ที่มีข้อความ "ผลการเปรียบเทียบเลขประจำตัวผู้เสียภาษี"
                        const allSpans = companyDataSection.querySelectorAll('span');
                        allSpans.forEach(span => {
                            if (span.textContent && span.textContent.includes('ผลการเปรียบเทียบเลขประจำตัวผู้เสียภาษี')) {
                                span.textContent = 'ผลการเปรียบเทียบเลขประจำตัวผู้เสียภาษี: ✅ อนุมัติแล้ว';
                                span.style.color = '#10b981';
                            }
                        });
                        
                        // อัพเดทสีของเลขประจำตัวผู้เสียภาษีทั้งสองฝั่ง
                        const taxIdLabels = companyDataSection.querySelectorAll('div');
                        taxIdLabels.forEach(div => {
                            const divText = div.textContent || '';
                            if (divText.includes('เลขจาก OCR:') || divText.includes('เลขประจำตัวผู้เสียภาษี')) {
                                // หา div ถัดไปที่เป็น tax id box
                                let nextDiv = div.nextElementSibling;
                                while (nextDiv && nextDiv.tagName !== 'DIV') {
                                    nextDiv = nextDiv.nextElementSibling;
                                }
                                if (nextDiv && nextDiv.tagName === 'DIV') {
                                    nextDiv.style.color = '#10b981';
                                }
                            }
                        });
                        
                        // อัพเดทสีของ container
                        const containers = companyDataSection.querySelectorAll('div[style*="border-left"]');
                        containers.forEach(container => {
                            if (container.textContent && container.textContent.includes('ผลการเปรียบเทียบเลขประจำตัวผู้เสียภาษี')) {
                                container.style.background = '#10b98115';
                                container.style.borderLeftColor = '#10b981';
                            }
                        });
                    }
                    
                    // อัพเดทสถานะที่อยู่
                    if (fieldKey === 'address_match') {
                        // หา span ที่มีข้อความ "ผลการเปรียบเทียบที่อยู่"
                        const allSpans = companyDataSection.querySelectorAll('span');
                        allSpans.forEach(span => {
                            if (span.textContent && span.textContent.includes('ผลการเปรียบเทียบที่อยู่')) {
                                span.textContent = 'ผลการเปรียบเทียบที่อยู่: ✅ อนุมัติแล้ว';
                                span.style.color = '#10b981';
                            }
                        });
                        
                        // อัพเดทสีของที่อยู่ทั้งสองฝั่ง
                        const addressLabels = companyDataSection.querySelectorAll('div');
                        addressLabels.forEach(div => {
                            const divText = div.textContent || '';
                            if (divText.includes('ที่อยู่บริษัท:') || divText.includes('ที่อยู่จาก OCR:')) {
                                // หา div ถัดไปที่เป็น address box
                                let nextDiv = div.nextElementSibling;
                                while (nextDiv && nextDiv.tagName !== 'DIV') {
                                    nextDiv = nextDiv.nextElementSibling;
                                }
                                if (nextDiv && nextDiv.tagName === 'DIV') {
                                    nextDiv.style.color = '#10b981';
                                    nextDiv.style.borderColor = '#10b98140';
                                }
                            }
                        });
                        
                        // อัพเดทสีของ container
                        const containers = companyDataSection.querySelectorAll('div[style*="border-left"]');
                        containers.forEach(container => {
                            if (container.textContent && container.textContent.includes('ผลการเปรียบเทียบที่อยู่')) {
                                container.style.background = '#10b98115';
                                container.style.borderLeftColor = '#10b981';
                            }
                        });
                    }
                    
                    // อัพเดทปุ่มอนุมัติในส่วนข้อมูลบริษัท (หาจาก company-data-section)
                    if (fieldKey === 'company_name_match' || fieldKey === 'tax_id_match' || fieldKey === 'address_match') {
                        // หาปุ่มอนุมัติในส่วนข้อมูลบริษัท
                        const companyDataButtons = companyDataSection.querySelectorAll(`button[data-field-key="${fieldKey}"][data-field-index="${index}"]`);
                        companyDataButtons.forEach(button => {
                            if (button.textContent && (button.textContent.includes('อนุมัติ') || button.textContent.includes('✓'))) {
                                // เปลี่ยนปุ่มเป็นปุ่ม "ยกเลิก"
                                const cancelButton = document.createElement('button');
                                cancelButton.onclick = () => cancelApproval(index, fieldKey, fieldLabel);
                                cancelButton.setAttribute('data-field-key', fieldKey);
                                cancelButton.setAttribute('data-field-index', String(index));
                                cancelButton.style.cssText = 'padding: 6px 12px; background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.85em; font-weight: 600; display: flex; align-items: center; gap: 6px; transition: all 0.3s; white-space: nowrap;';
                                cancelButton.setAttribute('onmouseover', "this.style.transform='scale(1.05)'; this.style.boxShadow='0 2px 8px rgba(239, 68, 68, 0.4)';");
                                cancelButton.setAttribute('onmouseout', "this.style.transform='scale(1)'; this.style.boxShadow='none';");
                                cancelButton.setAttribute('title', 'ยกเลิกการอนุมัติ');
                                cancelButton.innerHTML = '<span style="font-size: 1em;">✕</span> ยกเลิก';
                                button.replaceWith(cancelButton);
                                console.log(`✅ อัพเดทปุ่มอนุมัติในส่วนข้อมูลบริษัท: ${fieldKey}`);
                            }
                        });
                    }
                }
            }
            
            // ตรวจสอบว่าทุก field ที่ไม่ match ถูก approve แล้วหรือไม่
            console.log(`🔍 [Debug] ก่อนเรียก checkAndUpdateRowStatus: comparisonApprovals[${approvalKey}]=${comparisonApprovals[approvalKey]}`);
            console.log(`🔍 [Debug] comparisonApprovals object ก่อนเรียก checkAndUpdateRowStatus:`, comparisonApprovals);
            checkAndUpdateRowStatus(index);
            console.log(`🔍 [Debug] หลังเรียก checkAndUpdateRowStatus: comparisonApprovals[${approvalKey}]=${comparisonApprovals[approvalKey]}`);
            
            // แสดง toast notification
            showToast('success', `✅ อนุมัติ "${fieldLabel}" เรียบร้อยแล้ว`);
            
            // Trigger auto-save
            triggerAutoSave();
        }
        
        /**
         * ตรวจสอบและอัพเดทสถานะ row (เปลี่ยนจาก "ตรงกันบางส่วน" เป็น "ตรงกัน" ถ้าทุก field ถูก approve)
         */
        function checkAndUpdateRowStatus(index) {
            const row = findRowInActiveTab(index);
            if (!row) return;
            
            // หา comparison data จาก window.comparisonResults หรือ allComparisonsData
            const comp = (window.comparisonResults && window.comparisonResults[index]) || 
                        (allComparisonsData && allComparisonsData[index]);
            
            if (!comp) {
                console.warn(`⚠️ ไม่พบ comparison data สำหรับ index ${index}`);
                return;
            }
            
            const matchDetails = comp.match_details || {};
            
            // รายการ fields ที่สามารถอนุมัติได้ (รวม address_match ด้วย)
            const approvableFieldKeys = [
                'document_no_match',
                'date_match',
                'company_name_match',
                'tax_id_match',
                'branch_match',
                'reference_no_match',
                'amount_before_vat_match',
                'vat_amount_match',
                'total_amount_match',
                'document_type_match',
                'address_match'
            ];
            
            // ตรวจสอบว่าทุก field ที่ไม่ match ถูก approve แล้วหรือไม่
            let allMismatchedFieldsApproved = true;
            let hasMismatchedFields = false;
            
            approvableFieldKeys.forEach(fieldKey => {
                const isMatch = matchDetails[fieldKey];
                if (!isMatch) {
                    hasMismatchedFields = true;
                    const isApproved = comparisonApprovals[`${index}-${fieldKey}`] || false;
                    if (!isApproved) {
                        allMismatchedFieldsApproved = false;
                    }
                }
            });
            
            // อัพเดทสถานะข้อมูลบริษัท badge ทุกครั้ง (ไม่ต้องรอให้ approve ทั้งหมด)
            // ตรวจสอบสถานะจาก UI ด้านล่าง (ผลการเปรียบเทียบ) แทนที่จะคำนวณจากข้อมูลดิบ
            const companyDataSection = row.querySelector('.company-data-section');
            let companyDataMatches = 0;
            let companyDataTotal = 0;
            
            if (companyDataSection) {
                // ตรวจสอบสถานะจาก UI elements ด้านล่าง
                const allSpans = companyDataSection.querySelectorAll('span');
                
                // ตรวจสอบชื่อบริษัท
                const nameSpan = Array.from(allSpans).find(span => 
                    span.textContent && span.textContent.includes('ผลการเปรียบเทียบชื่อ')
                );
                if (nameSpan) {
                    companyDataTotal++;
                    const nameText = nameSpan.textContent || '';
                    // ตรวจสอบว่ามี "✅ อนุมัติแล้ว" หรือ "✅ ตรงกัน" หรือไม่
                    if (nameText.includes('✅ อนุมัติแล้ว') || nameText.includes('✅ ตรงกัน')) {
                        companyDataMatches++;
                        console.log(`✅ [Debug] ชื่อบริษัท: ตรงกันหรืออนุมัติแล้ว (จาก UI)`);
                    } else {
                        console.log(`⚠️ [Debug] ชื่อบริษัท: ไม่ตรงกัน (จาก UI)`);
                    }
                }
                
                // ตรวจสอบเลขประจำตัวผู้เสียภาษี
                const taxIdSpan = Array.from(allSpans).find(span => 
                    span.textContent && span.textContent.includes('ผลการเปรียบเทียบเลขประจำตัวผู้เสียภาษี')
                );
                if (taxIdSpan) {
                    companyDataTotal++;
                    const taxIdText = taxIdSpan.textContent || '';
                    // ตรวจสอบว่ามี "✅ อนุมัติแล้ว" หรือ "✅ ตรงกัน" หรือไม่
                    if (taxIdText.includes('✅ อนุมัติแล้ว') || taxIdText.includes('✅ ตรงกัน')) {
                        companyDataMatches++;
                        console.log(`✅ [Debug] เลขประจำตัวผู้เสียภาษี: ตรงกันหรืออนุมัติแล้ว (จาก UI)`);
                    } else {
                        console.log(`⚠️ [Debug] เลขประจำตัวผู้เสียภาษี: ไม่ตรงกัน (จาก UI)`);
                    }
                }
                
                // ตรวจสอบที่อยู่
                const addressSpan = Array.from(allSpans).find(span => 
                    span.textContent && span.textContent.includes('ผลการเปรียบเทียบที่อยู่')
                );
                if (addressSpan) {
                    companyDataTotal++;
                    const addressText = addressSpan.textContent || '';
                    // ตรวจสอบว่ามี "✅ อนุมัติแล้ว" หรือ "✅ ตรงกัน" หรือไม่
                    if (addressText.includes('✅ อนุมัติแล้ว') || addressText.includes('✅ ตรงกัน')) {
                        companyDataMatches++;
                        console.log(`✅ [Debug] ที่อยู่: ตรงกันหรืออนุมัติแล้ว (จาก UI)`);
                    } else {
                        console.log(`⚠️ [Debug] ที่อยู่: ไม่ตรงกัน (จาก UI)`);
                    }
                }
            } else {
                // ถ้าไม่มี company-data-section ให้ใช้วิธีเดิม (คำนวณจากข้อมูลดิบ)
                const companyName = (document.getElementById('companyName')?.textContent || '').trim();
                const companyTaxId = (document.getElementById('companyTaxId')?.textContent || '').trim();
                const companyAddress = (document.getElementById('companyAddress')?.textContent || '').trim();
                
                const ocrData = comp.ocr_data || {};
                const buyerName = (ocrData.buyer_name || '').trim();
                const buyerTaxId = (ocrData.buyer_tax_id || '').trim();
                const buyerAddress = (ocrData.buyer_address || ocrData.address || ocrData.address_full || '').trim();
                
                // ตรวจสอบชื่อบริษัท
                if (buyerName && buyerName !== '-' && companyName && companyName !== '-') {
                    companyDataTotal++;
                    const companyNameApprovalKey = `${index}-company_name_match`;
                    const isCompanyNameApproved = comparisonApprovals[companyNameApprovalKey] || false;
                    const normalizedBuyerName = normalizeText(buyerName);
                    const normalizedCompanyName = normalizeText(companyName);
                    const companyNameMatch = normalizedBuyerName === normalizedCompanyName || 
                        normalizedBuyerName.includes(normalizedCompanyName) || 
                        normalizedCompanyName.includes(normalizedBuyerName);
                    
                    if (companyNameMatch || isCompanyNameApproved) {
                        companyDataMatches++;
                    }
                }
                
                // ตรวจสอบเลขประจำตัวผู้เสียภาษี
                if (buyerTaxId && buyerTaxId !== '-' && companyTaxId && companyTaxId !== '-') {
                    companyDataTotal++;
                    const taxIdApprovalKey = `${index}-tax_id_match`;
                    const isTaxIdApproved = comparisonApprovals[taxIdApprovalKey] || false;
                    const normalizedBuyerTaxId = buyerTaxId.replace(/\s+/g, '').replace(/[-\s]/g, '');
                    const normalizedCompanyTaxId = companyTaxId.replace(/\s+/g, '').replace(/[-\s]/g, '');
                    const taxIdMatch = normalizedBuyerTaxId === normalizedCompanyTaxId;
                    
                    if (taxIdMatch || isTaxIdApproved) {
                        companyDataMatches++;
                    }
                }
                
                // ตรวจสอบที่อยู่
                if (buyerAddress && buyerAddress !== '-' && companyAddress && companyAddress !== '-') {
                    companyDataTotal++;
                    const addressApprovalKey = `${index}-address_match`;
                    const isAddressApproved = comparisonApprovals[addressApprovalKey] || false;
                    const normalizedBuyerAddress = normalizeAddress(buyerAddress);
                    const normalizedCompanyAddress = normalizeAddress(companyAddress);
                    const addressMatch = normalizedBuyerAddress === normalizedCompanyAddress;
                    
                    if (addressMatch || isAddressApproved) {
                        companyDataMatches++;
                    }
                }
            }
            
            console.log(`🔍 [Debug] สรุป: companyDataMatches=${companyDataMatches}/${companyDataTotal} (ตรวจสอบจาก UI)`);
            
            // ตรวจสอบว่าทุก field ตรงกันหรือถูกอนุมัติหมดแล้วหรือไม่
            const allCompanyDataMatched = companyDataMatches === companyDataTotal;
            console.log(`🔍 [Debug] ทุก field ตรงกันหรือถูกอนุมัติหมดแล้ว: ${allCompanyDataMatched} (${companyDataMatches} === ${companyDataTotal})`);
            
            // อัพเดทสถานะข้อมูลบริษัท badge ทันที
            const statusElements = row.querySelectorAll('.comparison-row-status');
            console.log(`🔍 [Debug] หา status badge: พบ ${statusElements.length} elements`);
            console.log(`🔍 [Debug] companyDataMatches: ${companyDataMatches}, companyDataTotal: ${companyDataTotal}`);
            console.log(`🔍 [Debug] comparisonApprovals สำหรับ index ${index}:`, Object.keys(comparisonApprovals).filter(k => k.startsWith(`${index}-`)));
            console.log(`🔍 [Debug] comparisonApprovals object:`, comparisonApprovals);
            
            let foundCompanyDataBadge = false;
            statusElements.forEach((statusElement, idx) => {
                const elementText = statusElement.textContent || '';
                console.log(`🔍 [Debug] Status element ${idx}: "${elementText.substring(0, 50)}..."`);
                
                if (elementText.includes('🏢')) {
                    foundCompanyDataBadge = true;
                    console.log(`🔍 [Debug] พบ badge ข้อมูลบริษัท!`);
                    if (companyDataTotal > 0) {
                        const oldText = statusElement.textContent;
                        let newStatusText = '';
                        let newClassName = '';
                        let newColor = '';
                        let newBgColor = '';
                        let newBorderColor = '';
                        
                        // ตรวจสอบว่าทุก field ตรงกันหรือถูกอนุมัติหมดแล้วหรือไม่
                        const isAllMatched = companyDataMatches === companyDataTotal;
                        console.log(`🔍 [Debug] ตรวจสอบสถานะ: companyDataMatches=${companyDataMatches}, companyDataTotal=${companyDataTotal}, isAllMatched=${isAllMatched}`);
                        
                        if (isAllMatched) {
                            newClassName = 'comparison-row-status match';
                            newColor = '#10b981';
                            newBgColor = 'rgba(16, 185, 129, 0.2)';
                            newBorderColor = '#10b981';
                            // ถ้าตรงกันหมดแล้ว ให้แสดงแค่ "ตรงกัน" โดยไม่ต้องแสดงตัวเลข
                            newStatusText = `ตรงกัน`;
                            console.log(`✅ อัพเดทสถานะข้อมูลบริษัท: "${oldText}" -> "🏢 ${newStatusText}" (${companyDataMatches}/${companyDataTotal})`);
                        } else if (companyDataMatches > 0) {
                            newClassName = 'comparison-row-status partial-match';
                            newColor = '#fbbf24';
                            newBgColor = 'rgba(251, 191, 36, 0.2)';
                            newBorderColor = '#fbbf24';
                            newStatusText = `ตรงกันบางส่วน (${companyDataMatches}/${companyDataTotal})`;
                            console.log(`✅ อัพเดทสถานะข้อมูลบริษัท: "${oldText}" -> "🏢 ${newStatusText}"`);
                        } else {
                            newClassName = 'comparison-row-status mismatch';
                            newColor = '#ef4444';
                            newBgColor = 'rgba(239, 68, 68, 0.2)';
                            newBorderColor = '#ef4444';
                            newStatusText = `ไม่ตรงกัน (${companyDataMatches}/${companyDataTotal})`;
                            console.log(`✅ อัพเดทสถานะข้อมูลบริษัท: "${oldText}" -> "🏢 ${newStatusText}"`);
                        }
                        
                        // อัพเดท className
                        statusElement.className = newClassName;
                        
                        // อัพเดท styles
                        statusElement.style.color = newColor;
                        statusElement.style.backgroundColor = newBgColor;
                        statusElement.style.border = `1px solid ${newBorderColor}`;
                        
                        // อัพเดท innerHTML โดยเก็บ span 🏢 ไว้
                        // หา span ที่มี emoji 🏢
                        const emojiSpan = statusElement.querySelector('span[style*="font-size"]');
                        if (emojiSpan) {
                            // ถ้ามี span อยู่แล้ว ให้เก็บไว้และอัพเดทเฉพาะ text
                            statusElement.innerHTML = `<span style="font-size: 0.9em;">🏢</span> ${newStatusText}`;
                        } else {
                            // ถ้าไม่มี span ให้สร้างใหม่
                            statusElement.innerHTML = `<span style="font-size: 0.9em;">🏢</span> ${newStatusText}`;
                        }
                        
                        // Force reflow เพื่อให้ browser render ใหม่
                        statusElement.offsetHeight;
                        
                        console.log(`✅ [Debug] อัพเดท badge สำเร็จ: "${oldText}" -> "${statusElement.textContent}"`);
                    } else {
                        console.warn(`⚠️ [Debug] companyDataTotal = 0 ไม่สามารถอัพเดทสถานะได้`);
                    }
                }
            });
            
            if (!foundCompanyDataBadge) {
                console.warn(`⚠️ [Debug] ไม่พบ badge ข้อมูลบริษัท (🏢) ใน row ${index}`);
            }
            
            // ถ้ามี field ที่ไม่ match และทุก field ถูก approve แล้ว
            if (hasMismatchedFields && allMismatchedFieldsApproved) {
                // เปลี่ยนสถานะจาก "ตรงกันบางส่วน" เป็น "ตรงกัน"
                const statusElements = row.querySelectorAll('.comparison-row-status');
                statusElements.forEach(statusElement => {
                    statusElement.className = 'comparison-row-status match';
                    statusElement.style.color = '#10b981';
                    statusElement.style.backgroundColor = 'rgba(16, 185, 129, 0.2)';
                    statusElement.style.border = '1px solid #10b981';
                    // ตรวจสอบว่าเป็นสถานะข้อมูลบริษัทหรือไม่ (มี emoji 🏢)
                    if (statusElement.textContent.includes('🏢')) {
                        // คำนวณสถานะข้อมูลบริษัทใหม่
                        const purchaseData = comp.purchase_data || {};
                        const ocrData = comp.ocr_data || {};
                        const buyerName = purchaseData.contact || purchaseData.company_name || '';
                        const companyName = ocrData.company_name || '';
                        const buyerTaxId = purchaseData.tax_id || '';
                        const companyTaxId = ocrData.tax_id || '';
                        const buyerAddress = purchaseData.address || '';
                        const companyAddress = ocrData.address || '';
                        
                        let companyDataMatches = 0;
                        let companyDataTotal = 0;
                        
                        // ตรวจสอบชื่อบริษัท
                        if (buyerName && buyerName !== '-' && companyName && companyName !== '-') {
                            companyDataTotal++;
                            const normalizedBuyerName = normalizeText(buyerName);
                            const normalizedCompanyName = normalizeText(companyName);
                            const companyNameMatch = normalizedBuyerName === normalizedCompanyName || 
                                normalizedBuyerName.includes(normalizedCompanyName) || 
                                normalizedCompanyName.includes(normalizedBuyerName);
                            if (companyNameMatch) {
                                companyDataMatches++;
                            } else {
                                const companyNameApprovalKey = `${index}-company_name_match`;
                                const isCompanyNameApproved = comparisonApprovals[companyNameApprovalKey] || false;
                                if (isCompanyNameApproved) {
                                    companyDataMatches++;
                                }
                            }
                        }
                        
                        // ตรวจสอบเลขประจำตัวผู้เสียภาษี
                        if (buyerTaxId && buyerTaxId !== '-' && companyTaxId && companyTaxId !== '-') {
                            companyDataTotal++;
                            const normalizedBuyerTaxId = buyerTaxId.replace(/\s+/g, '').replace(/[-\s]/g, '');
                            const normalizedCompanyTaxId = companyTaxId.replace(/\s+/g, '').replace(/[-\s]/g, '');
                            const taxIdMatch = normalizedBuyerTaxId === normalizedCompanyTaxId;
                            if (taxIdMatch) {
                                companyDataMatches++;
                            } else {
                                const taxIdApprovalKey = `${index}-tax_id_match`;
                                const isTaxIdApproved = comparisonApprovals[taxIdApprovalKey] || false;
                                if (isTaxIdApproved) {
                                    companyDataMatches++;
                                }
                            }
                        }
                        
                        // ตรวจสอบที่อยู่
                        if (buyerAddress && buyerAddress !== '-' && companyAddress && companyAddress !== '-') {
                            companyDataTotal++;
                            const normalizedBuyerAddress = normalizeAddress(buyerAddress);
                            const normalizedCompanyAddress = normalizeAddress(companyAddress);
                            const addressMatch = normalizedBuyerAddress === normalizedCompanyAddress;
                            if (addressMatch) {
                                companyDataMatches++;
                            } else {
                                const addressApprovalKey = `${index}-address_match`;
                                const isAddressApproved = comparisonApprovals[addressApprovalKey] || false;
                                if (isAddressApproved) {
                                    companyDataMatches++;
                                }
                            }
                        }
                        
                        if (companyDataTotal > 0) {
                            if (companyDataMatches === companyDataTotal) {
                                statusElement.textContent = `🏢 ตรงกัน (${companyDataMatches}/${companyDataTotal})`;
                            } else if (companyDataMatches > 0) {
                                statusElement.textContent = `🏢 ตรงกันบางส่วน (${companyDataMatches}/${companyDataTotal})`;
                            } else {
                                statusElement.textContent = `🏢 ไม่ตรงกัน (${companyDataMatches}/${companyDataTotal})`;
                            }
                        }
                    } else {
                        // สถานะเอกสาร
                        statusElement.textContent = 'ตรงกัน';
                    }
                    
                    console.log(`✅ เปลี่ยนสถานะ row ${index} จาก "ตรงกันบางส่วน" เป็น "ตรงกัน"`);
                });
                
                // ซ่อนหมายเหตุในหน้าเว็บ แต่เก็บหมายเหตุไว้เพื่อ Excel export
                const noteKey = String(index);
                const noteTextarea = document.getElementById(`note-${index}`);
                if (noteTextarea) {
                    // เก็บ initial note ไว้ถ้ายังไม่มี (เก็บจาก comparisonNotes ปัจจุบัน)
                    if (!initialNotes[noteKey] && comparisonNotes[noteKey]) {
                        initialNotes[noteKey] = comparisonNotes[noteKey];
                    }
                    
                    // เก็บหมายเหตุปัจจุบันไว้ใน comparisonNotes เพื่อ Excel export
                    // ถ้ามี initial note ให้ใช้ initial note, ถ้าไม่มีให้ใช้หมายเหตุปัจจุบัน
                    const noteToKeep = initialNotes[noteKey] || comparisonNotes[noteKey] || '';
                    comparisonNotes[noteKey] = noteToKeep;
                    
                    // ซ่อนในหน้าเว็บ (ลบจาก textarea) แต่เก็บไว้ใน comparisonNotes
                    noteTextarea.value = '';
                    
                    console.log(`✅ ซ่อนหมายเหตุในหน้าเว็บสำหรับ row ${index} (เก็บไว้สำหรับ Excel export: "${noteToKeep.substring(0, 50)}...")`);
                }
            }
            // หมายเหตุ: สถานะข้อมูลบริษัท badge ถูกอัพเดททุกครั้งที่เรียกฟังก์ชันนี้ (ไม่ต้องรอให้ approve ทั้งหมด)
        }
        
        /**
         * Restore สถานะ row กลับเป็น "ตรงกันบางส่วน" และ restore หมายเหตุเดิม
         */
        function restoreRowStatus(index) {
            const row = findRowInActiveTab(index);
            if (!row) return;
            
            // หา comparison data
            const comp = (window.comparisonResults && window.comparisonResults[index]) || 
                        (allComparisonsData && allComparisonsData[index]);
            
            if (!comp) return;
            
            const matchDetails = comp.match_details || {};
            const matchedCount = comp.matched_count || 0;
            const totalCount = comp.total_count || 0;
            
            // ตรวจสอบว่ามี field ที่ไม่ match หรือไม่
            const approvableFieldKeys = [
                'document_no_match', 'date_match', 'company_name_match', 'tax_id_match',
                'branch_match', 'reference_no_match', 'amount_before_vat_match',
                'vat_amount_match', 'total_amount_match', 'document_type_match'
            ];
            
            let hasMismatchedFields = false;
            approvableFieldKeys.forEach(fieldKey => {
                if (!matchDetails[fieldKey]) {
                    hasMismatchedFields = true;
                }
            });
            
            // ถ้ามี field ที่ไม่ match ให้เปลี่ยนสถานะกลับเป็น "ตรงกันบางส่วน"
            if (hasMismatchedFields) {
                const statusElement = row.querySelector('.comparison-row-status');
                if (statusElement) {
                    statusElement.className = 'comparison-row-status partial-match';
                    statusElement.style.color = '#fbbf24';
                    statusElement.style.backgroundColor = 'rgba(251, 191, 36, 0.2)';
                    statusElement.style.border = '1px solid #fbbf24';
                    statusElement.textContent = `ตรงกันบางส่วน (${matchedCount}/${totalCount})`;
                    
                    console.log(`✅ เปลี่ยนสถานะ row ${index} กลับเป็น "ตรงกันบางส่วน"`);
                }
            }
            
            // Restore หมายเหตุเดิม
            const noteKey = String(index);
            const noteTextarea = document.getElementById(`note-${index}`);
            if (noteTextarea && initialNotes[noteKey]) {
                comparisonNotes[noteKey] = initialNotes[noteKey];
                noteTextarea.value = initialNotes[noteKey];
                
                console.log(`✅ Restore หมายเหตุเดิมสำหรับ row ${index}`);
            }
        }
        
        // ฟังก์ชันยกเลิกการอนุมัติฟิลด์เฉพาะจุด
        // ฟังก์ชันอนุมัติข้อมูลบริษัททั้งหมด (ชื่อ, เลขประจำตัวผู้เสียภาษี, ที่อยู่)
        function approveCompanyData(index) {
            const approvalKey = `${index}-company_data_all`;
            
            // อนุมัติข้อมูลบริษัททั้งหมด
            comparisonApprovals[approvalKey] = true;
            
            // อนุมัติแต่ละส่วนของข้อมูลบริษัทด้วย (ถ้ายังไม่ตรงกัน)
            const nameApprovalKey = `${index}-company_name_match`;
            const taxIdApprovalKey = `${index}-company_tax_id_match`;
            const addressApprovalKey = `${index}-address_match`;
            
            // ตรวจสอบว่ามีข้อมูลที่ต้องอนุมัติหรือไม่
            const row = findRowInActiveTab(index);
            if (row) {
                // อนุมัติชื่อ (ถ้ามีและไม่ตรงกัน)
                const nameField = row.querySelector('.comparison-field:has(.comparison-field-label:contains("ชื่อผู้ซื้อ"))');
                if (nameField && !comparisonApprovals[nameApprovalKey]) {
                    comparisonApprovals[nameApprovalKey] = true;
                }
                
                // อนุมัติเลขประจำตัวผู้เสียภาษี (ถ้ามีและไม่ตรงกัน)
                const taxIdField = row.querySelector('.comparison-field:has(.comparison-field-label:contains("เลขประจำตัวผู้เสียภาษี - ผู้ซื้อ"))');
                if (taxIdField && !comparisonApprovals[taxIdApprovalKey]) {
                    comparisonApprovals[taxIdApprovalKey] = true;
                }
                
                // อนุมัติที่อยู่ (ถ้ามีและไม่ตรงกัน)
                if (!comparisonApprovals[addressApprovalKey]) {
                    comparisonApprovals[addressApprovalKey] = true;
                }
            }
            
            console.log('✅ Company data approved:', approvalKey);
            triggerAutoSave();
            
            // รีเฟรชการแสดงผล
            refreshComparisonRow(index);
        }
        
        // ฟังก์ชันยกเลิกการอนุมัติข้อมูลบริษัททั้งหมด
        function cancelCompanyDataApproval(index) {
            const approvalKey = `${index}-company_data_all`;
            
            // ยกเลิกการอนุมัติข้อมูลบริษัททั้งหมด
            delete comparisonApprovals[approvalKey];
            
            // ยกเลิกการอนุมัติแต่ละส่วนด้วย (ถ้าถูกอนุมัติผ่านปุ่มนี้)
            const nameApprovalKey = `${index}-company_name_match`;
            const taxIdApprovalKey = `${index}-company_tax_id_match`;
            const addressApprovalKey = `${index}-address_match`;
            
            // ตรวจสอบว่าถูกอนุมัติผ่านปุ่มนี้หรือไม่ (อาจจะต้องเก็บข้อมูลเพิ่มเติม)
            // สำหรับตอนนี้ให้ยกเลิกทั้งหมด
            delete comparisonApprovals[nameApprovalKey];
            delete comparisonApprovals[taxIdApprovalKey];
            delete comparisonApprovals[addressApprovalKey];
            
            console.log('❌ Company data approval cancelled:', approvalKey);
            triggerAutoSave();
            
            // รีเฟรชการแสดงผล
            refreshComparisonRow(index);
        }
        
        // ฟังก์ชันรีเฟรช comparison row
        function refreshComparisonRow(index) {
            const row = findRowInActiveTab(index);
            if (!row) {
                console.warn(`⚠️ Cannot find row with index: ${index}`);
                return;
            }
            
            // หา tab name จาก row element
            const tabName = row.getAttribute('data-tab') || 'all';
            
            // หา comp data จาก allComparisonsData (ถ้ามี)
            if (typeof allComparisonsData !== 'undefined' && allComparisonsData && allComparisonsData[index]) {
                const comp = allComparisonsData[index];
                const newRowHTML = generateComparisonRowHTML(comp, index, tabName);
                
                // แทนที่ row เดิม
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = newRowHTML;
                const newRow = tempDiv.firstElementChild;
                
                if (newRow) {
                    row.replaceWith(newRow);
                    console.log(`✅ Refreshed comparison row ${index} in tab ${tabName}`);
                }
            } else {
                // ถ้าไม่มี allComparisonsData ให้รีโหลดหน้าใหม่
                console.log('⚠️ allComparisonsData not found, reloading page...');
                location.reload();
            }
        }
        
        function cancelApproval(index, fieldKey, fieldLabel) {
            const approvalKey = `${index}-${fieldKey}`;
            
            // ลบสถานะการอนุมัติ
            delete comparisonApprovals[approvalKey];
            console.log('❌ Field approval cancelled:', approvalKey, fieldLabel);
            
            // รีเฟรชการแสดงผล (หา row ใน tab ที่ active อยู่)
            const row = findRowInActiveTab(index);
            if (!row) {
                console.error('❌ Cannot find row:', `comparison-row-${index}`);
                return;
            }
            
            // หาปุ่มยกเลิกที่ตรงกับ fieldKey โดยใช้ data attribute เป็นหลัก
            // วิธีที่ 1: หาจาก data-field-key และ data-field-index และตรวจสอบว่าเป็นปุ่มยกเลิก
            let cancelButtons = Array.from(row.querySelectorAll(`button[data-field-key="${fieldKey}"][data-field-index="${index}"]`)).filter(btn => 
                btn.textContent && (btn.textContent.includes('ยกเลิก') || btn.textContent.includes('✕'))
            );
            
            // วิธีที่ 2: ถ้าไม่เจอ ให้หาจาก field container ที่มี data-field-key ตรงกัน
            if (cancelButtons.length === 0) {
                const fieldContainer = row.querySelector(`.comparison-field[data-field-key="${fieldKey}"][data-field-index="${index}"]`);
                if (fieldContainer) {
                    const button = fieldContainer.querySelector('button');
                    if (button && button.textContent && (button.textContent.includes('ยกเลิก') || button.textContent.includes('✕'))) {
                        cancelButtons = [button];
                    }
                }
            }
            
            // วิธีที่ 3: ถ้ายังไม่เจอ ให้หาจาก onclick attribute (สำหรับปุ่มที่สร้างจาก HTML)
            if (cancelButtons.length === 0) {
                cancelButtons = Array.from(row.querySelectorAll(`button[onclick*="cancelApproval(${index}, '${fieldKey}'"]`));
            }
            
            console.log(`🔍 Found ${cancelButtons.length} cancel buttons for field ${fieldKey} at index ${index}`);
            
            if (cancelButtons.length === 0) {
                console.error(`❌ Cannot find cancel button for field ${fieldKey} at index ${index}`);
                // ลองหา field container และปุ่มภายใน
                const fieldContainer = row.querySelector(`.comparison-field[data-field-key="${fieldKey}"][data-field-index="${index}"]`);
                if (fieldContainer) {
                    const allButtons = fieldContainer.querySelectorAll('button');
                    console.log(`🔍 Found ${allButtons.length} buttons in field container:`, Array.from(allButtons).map(btn => ({
                        text: btn.textContent,
                        dataKey: btn.getAttribute('data-field-key'),
                        dataIndex: btn.getAttribute('data-field-index'),
                        onclick: btn.onclick ? 'has onclick' : 'no onclick'
                    })));
                }
                return;
            }
            
            cancelButtons.forEach(cancelButton => {
                // หา fieldContainer
                const fieldContainer = cancelButton.closest('.comparison-field');
                if (!fieldContainer) {
                    console.error('❌ Cannot find field container for cancel button');
                    return;
                }
                
                // หา fieldValue ทั้งสองฝั่ง (ภาษีซื้อและ OCR)
                const fieldValue = fieldContainer.querySelector('.comparison-field-value');
                if (fieldValue) {
                    // เปลี่ยนสีของ fieldValue กลับเป็น mismatch
                    fieldValue.style.color = '#ef4444';
                    fieldValue.style.fontWeight = '600';
                    fieldValue.classList.remove('approved');
                    fieldValue.classList.add('mismatch');
                }
                
                // เปลี่ยนปุ่มเป็นปุ่ม "อนุมัติ"
                const approveButton = document.createElement('button');
                approveButton.onclick = () => approveField(index, fieldKey, fieldLabel);
                approveButton.setAttribute('data-field-key', fieldKey);
                approveButton.setAttribute('data-field-index', String(index));
                approveButton.style.cssText = 'padding: 4px 10px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.8em; font-weight: 600; display: flex; align-items: center; gap: 4px; transition: all 0.3s; white-space: nowrap;';
                approveButton.setAttribute('onmouseover', "this.style.transform='scale(1.05)'; this.style.boxShadow='0 2px 8px rgba(16, 185, 129, 0.4)';");
                approveButton.setAttribute('onmouseout', "this.style.transform='scale(1)'; this.style.boxShadow='none';");
                approveButton.setAttribute('title', 'อนุมัติความไม่ตรงกันนี้');
                approveButton.innerHTML = '<span style="font-size: 1em;">✓</span> อนุมัติ';
                
                // Replace ปุ่มยกเลิกด้วยปุ่มอนุมัติ
                try {
                    cancelButton.replaceWith(approveButton);
                    console.log(`✅ Successfully replaced cancel button with approve button for field ${fieldKey} at index ${index}`);
                } catch (error) {
                    console.error('❌ Error replacing button:', error);
                    // Fallback: ลบปุ่มเก่าและเพิ่มปุ่มใหม่
                    if (cancelButton.parentNode) {
                        cancelButton.parentNode.removeChild(cancelButton);
                        fieldContainer.appendChild(approveButton);
                    }
                }
            });
            
            // อัพเดทฝั่ง OCR ด้วย
            const ocrSide = row.querySelector('.comparison-side.ocr');
            if (ocrSide) {
                const ocrFields = ocrSide.querySelectorAll('.comparison-field');
                ocrFields.forEach(ocrField => {
                    const ocrLabel = ocrField.querySelector('.comparison-field-label');
                    if (ocrLabel) {
                        // ตรวจสอบว่าเป็น field ที่ตรงกันหรือไม่
                        let isTargetField = false;
                        if (fieldKey === 'tax_id_match' && ocrLabel.textContent.includes('เลขประจำตัวผู้เสียภาษี')) {
                            isTargetField = true;
                        } else if (fieldKey === 'company_name_match' && ocrLabel.textContent.includes('ชื่อบริษัท')) {
                            isTargetField = true;
                        } else if (fieldKey === 'branch_match' && ocrLabel.textContent.includes('สาขา')) {
                            isTargetField = true;
                        } else if (fieldKey === 'document_no_match' && ocrLabel.textContent.includes('เลขที่เอกสาร')) {
                            isTargetField = true;
                        } else if (fieldKey === 'date_match' && ocrLabel.textContent.includes('วันที่')) {
                            isTargetField = true;
                        } else if (fieldKey === 'amount_before_vat_match' && ocrLabel.textContent.includes('ยอดก่อนภาษี')) {
                            isTargetField = true;
                        } else if (fieldKey === 'vat_amount_match' && ocrLabel.textContent.includes('ยอดภาษีมูลค่าเพิ่ม')) {
                            isTargetField = true;
                        } else if (fieldKey === 'total_amount_match' && ocrLabel.textContent.includes('ยอดหลังบวก')) {
                            isTargetField = true;
                        } else if (fieldKey === 'document_type_match' && ocrLabel.textContent.includes('ประเภทเอกสาร')) {
                            isTargetField = true;
                        } else if (fieldKey === 'reference_no_match' && ocrLabel.textContent.includes('เลขที่เอกสารอ้างอิง')) {
                            isTargetField = true;
                        }
                        
                        if (isTargetField) {
                            const ocrValue = ocrField.querySelector('.comparison-field-value');
                            if (ocrValue) {
                                ocrValue.style.color = '#ef4444';
                                ocrValue.style.fontWeight = '600';
                                ocrValue.classList.remove('approved');
                                ocrValue.classList.add('mismatch');
                            }
                        }
                    }
                });
            }
            
            // Restore สถานะ row และหมายเหตุเดิม
            restoreRowStatus(index);
            
            // แสดง toast notification
            showToast('success', `❌ ยกเลิกการอนุมัติ "${fieldLabel}" เรียบร้อยแล้ว`);
            
            // Trigger auto-save
            triggerAutoSave();
        }
        
        // ฟังก์ชันแสดง toast notification
        function showToast(type, message) {
            const toastHtml = `
                <div id="toast" style="position: fixed; bottom: 30px; right: 30px; background: ${type === 'success' ? '#10b981' : '#ef4444'}; color: white; padding: 15px 20px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); z-index: 10001; font-size: 0.95em; font-weight: 600; animation: slideIn 0.3s ease-out;">
                    ${message}
                </div>
            `;
            
            document.body.insertAdjacentHTML('beforeend', toastHtml);
            
            // ลบ toast หลัง 3 วินาที
            setTimeout(() => {
                const toast = document.getElementById('toast');
                if (toast) {
                    toast.style.animation = 'slideOut 0.3s ease-in';
                    setTimeout(() => toast.remove(), 300);
                }
            }, 3000);
        }
        
        // ฟังก์ชันย้ายเอกสารทั้งหมดที่ไม่ตรงกัน
        async function moveAllMismatchedDocuments() {
            // รวบรวม reference numbers จากรายการที่ไม่ตรงกันทั้งหมด
            const mismatchedReferenceNos = [];
            
            // ดึงข้อมูลจาก comparison results ที่เก็บไว้ใน DOM หรือจากตัวแปร global
            const comparisonResults = window.comparisonResults || [];
            
            comparisonResults.forEach(comp => {
                // รวมรายการที่ไม่ตรงกัน (no_match และ partial_match)
                if (comp.match_status === 'no_match' || comp.match_status === 'partial_match') {
                    const referenceNo = comp.purchase_data?.reference_no || comp.ocr_data?.reference_number || comp.ocr_data?.document_no;
                    if (referenceNo && !mismatchedReferenceNos.includes(referenceNo)) {
                        mismatchedReferenceNos.push(referenceNo);
                    }
                }
            });
            
            if (mismatchedReferenceNos.length === 0) {
                alert('ไม่พบรายการที่ไม่ตรงกัน');
                return;
            }
            
            // ยืนยันการย้าย
            const confirmed = confirm(
                `ต้องการย้ายเอกสารทั้งหมด ${mismatchedReferenceNos.length} รายการที่ไม่ตรงกันไปยังโฟลเดอร์ "ไฟล์ที่ต้องตรวจสอบ" ใช่หรือไม่?\n\n` +
                `รายการที่จะย้าย:\n${mismatchedReferenceNos.slice(0, 5).join(', ')}${mismatchedReferenceNos.length > 5 ? ' ...' : ''}`
            );
            
            if (!confirmed) {
                return;
            }
            
            // แสดง loading
            const loadingHtml = `
                <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 10000; display: flex; align-items: center; justify-content: center;" id="moveAllLoadingOverlay">
                    <div style="background: #1e293b; padding: 30px; border-radius: 12px; text-align: center;">
                        <div class="spinner" style="border: 4px solid #334155; border-top: 4px solid #f59e0b; border-radius: 50%; width: 50px; height: 50px; animation: spin 1s linear infinite; margin: 0 auto 15px;"></div>
                        <div style="color: #fafafa; font-size: 1.1em;">กำลังย้ายเอกสาร ${mismatchedReferenceNos.length} รายการ...</div>
                    </div>
                </div>
            `;
            document.body.insertAdjacentHTML('beforeend', loadingHtml);
            
            try {
                // ดึงค่าจาก form
                const taxMonth = document.getElementById('taxMonth')?.value;
                const taxYear = document.getElementById('taxYear')?.value;
                const company = document.getElementById('companyValue')?.value || document.getElementById('companySelect')?.value;
                
                if (!taxMonth || !taxYear || !company) {
                    document.getElementById('moveAllLoadingOverlay')?.remove();
                    alert('ไม่พบข้อมูลเดือนภาษีหรือบริษัท กรุณาเลือกข้อมูลก่อนย้ายเอกสาร');
                    return;
                }
                
                const taxMonthFormatted = `${taxYear}-${taxMonth}`;
                
                console.log('📦 Sending move all request:', {
                    referenceNos: mismatchedReferenceNos,
                    taxMonth: taxMonthFormatted,
                    company: company,
                    vatFolderPath: vatFolderPath
                });
                
                // เรียก API เพื่อย้ายไฟล์ทั้งหมด
                const response = await fetch('/api/auditcheck/move-all-mismatched-documents', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        referenceNos: mismatchedReferenceNos,
                        taxMonth: taxMonthFormatted,
                        company: company,
                        vatFolderPath: vatFolderPath
                    })
                });
                
                const result = await response.json();
                console.log('📦 API Response:', result);
                
                // ลบ loading
                document.getElementById('moveAllLoadingOverlay')?.remove();
                
                if (result.success) {
                    // สร้างข้อความสรุปผล
                    let message = `✅ ย้ายเอกสารเสร็จสิ้น!\n\n`;
                    message += `สรุปผล:\n`;
                    message += `- สำเร็จ: ${result.success_count}/${result.total} รายการ\n`;
                    if (result.failed_count > 0) {
                        message += `- ล้มเหลว: ${result.failed_count} รายการ\n`;
                    }
                    if (result.not_found_count > 0) {
                        message += `- ไม่พบไฟล์: ${result.not_found_count} รายการ\n`;
                    }
                    
                    if (result.results.failed.length > 0 || result.results.not_found.length > 0) {
                        message += `\nรายละเอียด:\n`;
                        result.results.failed.forEach(item => {
                            message += `- ❌ ${item.reference_no}: ${item.message}\n`;
                        });
                        result.results.not_found.forEach(item => {
                            message += `- ⚠️ ${item.reference_no}: ${item.message}\n`;
                        });
                    }
                    
                    alert(message);
                } else {
                    alert(result.error || 'ไม่สามารถย้ายเอกสารได้');
                }
            } catch (error) {
                console.error('❌ Error moving all documents:', error);
                document.getElementById('moveAllLoadingOverlay')?.remove();
                alert('เกิดข้อผิดพลาดในการย้ายเอกสาร: ' + error.message);
            }
        }
        
        // ฟังก์ชันสำหรับย้ายเอกสารไปยังโฟลเดอร์ "ไฟล์ที่ต้องตรวจสอบ"
        async function moveDocumentToReview(referenceNo, index) {
            console.log('📋 moveDocumentToReview called:', referenceNo);
            
            // ยืนยันการย้ายเอกสาร
            const confirmed = confirm(`ต้องการย้ายเอกสาร ${referenceNo} ไปยังโฟลเดอร์ "ไฟล์ที่ต้องตรวจสอบ" ใช่หรือไม่?`);
            if (!confirmed) {
                return;
            }
            
            // แสดง loading
            const loadingHtml = `
                <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 10000; display: flex; align-items: center; justify-content: center;" id="moveLoadingOverlay">
                    <div style="background: #1e293b; padding: 30px; border-radius: 12px; text-align: center;">
                        <div class="spinner" style="border: 4px solid #334155; border-top: 4px solid #f59e0b; border-radius: 50%; width: 50px; height: 50px; animation: spin 1s linear infinite; margin: 0 auto 15px;"></div>
                        <div style="color: #fafafa; font-size: 1.1em;">กำลังย้ายเอกสาร...</div>
                    </div>
                </div>
            `;
            document.body.insertAdjacentHTML('beforeend', loadingHtml);
            
            try {
                // ดึงค่าจาก form
                const taxMonth = document.getElementById('taxMonth')?.value;
                const taxYear = document.getElementById('taxYear')?.value;
                const company = document.getElementById('companyValue')?.value || document.getElementById('companySelect')?.value;
                
                // ตรวจสอบว่ามีค่าครบถ้วนหรือไม่
                if (!taxMonth || !taxYear || !company) {
                    console.error('❌ Missing required data:', { taxMonth, taxYear, company });
                    document.getElementById('moveLoadingOverlay')?.remove();
                    alert('ไม่พบข้อมูลเดือนภาษีหรือบริษัท กรุณาเลือกข้อมูลก่อนย้ายเอกสาร');
                    return;
                }
                
                // สร้าง taxMonth ในรูปแบบ YYYY-MM
                const taxMonthFormatted = `${taxYear}-${taxMonth}`;
                
                console.log('📊 Sending move request:', {
                    referenceNo: referenceNo,
                    taxMonth: taxMonthFormatted,
                    company: company
                });
                
                // เรียก API เพื่อย้ายไฟล์
                const response = await fetch('/api/auditcheck/move-document-to-review', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        referenceNo: referenceNo,
                        taxMonth: taxMonthFormatted,
                        company: company
                    })
                });
                
                const result = await response.json();
                console.log('📊 API Response:', result);
                
                // ลบ loading
                document.getElementById('moveLoadingOverlay')?.remove();
                
                if (result.success) {
                    alert(`✅ ย้ายเอกสารสำเร็จ!\n\nไฟล์: ${result.filename}\nย้ายไปยัง: ไฟล์ที่ต้องตรวจสอบ`);
                } else {
                    alert(result.message || result.error || 'ไม่สามารถย้ายเอกสารได้');
                }
            } catch (error) {
                console.error('❌ Error moving document:', error);
                document.getElementById('moveLoadingOverlay')?.remove();
                alert('เกิดข้อผิดพลาดในการย้ายเอกสาร: ' + error.message);
            }
        }
        
        // ฟังก์ชันเปิด/ปิดโหมด "ตรวจด้วยตัวเอง"
        async function toggleSelfCheckMode(index, referenceNo) {
            const isCurrentlyEnabled = selfCheckMode[index] || false;
            
            // เก็บ scroll position และ expanded state ก่อน re-render
            const scrollPosition = window.pageYOffset || document.documentElement.scrollTop;
            const rowElement = findRowInActiveTab(index);
            const wasExpanded = rowElement ? rowElement.classList.contains('expanded') : false;
            
            if (isCurrentlyEnabled) {
                // ปิดโหมด "ตรวจด้วยตัวเอง"
                delete selfCheckMode[index];
                console.log(`🔍 ปิดโหมด "ตรวจด้วยตัวเอง" สำหรับ row ${index}`);
                showToast('success', '✅ ปิดโหมด "ตรวจด้วยตัวเอง" แล้ว');
            } else {
                // เปิดโหมด "ตรวจด้วยตัวเอง"
                selfCheckMode[index] = true;
                console.log(`🔍 เปิดโหมด "ตรวจด้วยตัวเอง" สำหรับ row ${index}`);
                showToast('success', '✅ เปิดโหมด "ตรวจด้วยตัวเอง" แล้ว - ทุกฟิลด์ในฝั่งภาษีซื้อจะแสดงปุ่มอนุมัติ');
            }
            
            // Re-render เฉพาะ row ที่ต้องการ (ไม่ re-render ทั้งหน้า)
            await reRenderSingleRow(index);
            
            // ทำให้ row เปิดอยู่ (expanded) หลังจาก re-render
            const newRowElement = findRowInActiveTab(index);
            if (newRowElement) {
                // ถ้าเดิม expanded หรือกำลังเปิดโหมด "ตรวจด้วยตัวเอง" ให้ expanded
                if (wasExpanded || !isCurrentlyEnabled) {
                    newRowElement.classList.add('expanded');
                }
            }
            
            // Restore scroll position
            window.scrollTo(0, scrollPosition);
            
            // Trigger auto-save
            triggerAutoSave();
        }
        
        // ฟังก์ชัน re-render เฉพาะ row เดียว (ไม่ re-render ทั้งหน้า)
        async function reRenderSingleRow(index) {
            if (!allComparisonsData || !Array.isArray(allComparisonsData) || index < 0 || index >= allComparisonsData.length) {
                return;
            }
            
            const comp = allComparisonsData[index];
            if (!comp) {
                return;
            }
            
            // หา tab content ที่ active อยู่
            const activeTabContent = document.querySelector('.comparison-tab-content.active');
            
            if (activeTabContent) {
                // หา row element เฉพาะใน tab ที่ active อยู่โดยใช้ data-index
                const rowElement = findRowInActiveTab(index);
                
                if (rowElement) {
                    // เก็บ expanded state และ tab name ก่อน replace
                    const wasExpanded = rowElement.classList.contains('expanded');
                    const tabName = rowElement.getAttribute('data-tab') || 'all';
                    
                    // สร้าง HTML ใหม่สำหรับ row นี้โดยใช้ tabName ที่ถูกต้อง
                    const newRowHTML = generateComparisonRowHTML(comp, index, tabName);
                    
                    // สร้าง temporary container เพื่อแปลง HTML string เป็น DOM
                    const tempDiv = document.createElement('div');
                    tempDiv.innerHTML = newRowHTML.trim();
                    const newRowElement = tempDiv.firstElementChild;
                    
                    if (newRowElement && rowElement.parentElement) {
                        // Replace old row with new row
                        rowElement.parentElement.replaceChild(newRowElement, rowElement);
                        
                        // Restore expanded state ถ้าเดิม expanded
                        if (wasExpanded) {
                            newRowElement.classList.add('expanded');
                        }
                        
                    }
                } else {
                    console.warn(`⚠️ ไม่พบ row element สำหรับ index ${index} ใน tab ที่ active`);
                }
            } else {
                // ถ้าไม่พบ active tab ให้ re-render ในทุก tab ที่มี row นี้ (fallback)
                const rowElements = document.querySelectorAll(`[data-index="${index}"]`);
                
                if (rowElements.length > 0) {
                    rowElements.forEach(rowElement => {
                        const wasExpanded = rowElement.classList.contains('expanded');
                        const tabName = rowElement.getAttribute('data-tab') || 'all';
                        
                        // สร้าง HTML ใหม่สำหรับ row นี้โดยใช้ tabName ที่ถูกต้อง
                        const newRowHTML = generateComparisonRowHTML(comp, index, tabName);
                        
                        const tempDiv = document.createElement('div');
                        tempDiv.innerHTML = newRowHTML.trim();
                        const newRowElement = tempDiv.firstElementChild;
                        
                        if (newRowElement && rowElement.parentElement) {
                            rowElement.parentElement.replaceChild(newRowElement, rowElement);
                            if (wasExpanded) {
                                newRowElement.classList.add('expanded');
                            }
                        }
                    });
                    
                    console.log(`✅ Re-rendered row ${index} in ${rowElements.length} tab(s) (fallback)`);
                } else {
                    console.warn(`⚠️ ไม่พบ row element สำหรับ index ${index}`);
                }
            }
        }
        
        // ฟังก์ชันสำหรับลบรายการออก
        async function removeComparisonItem(index, referenceNo) {
            // ยืนยันการลบ
            const confirmed = await showDeleteConfirmModal(referenceNo);
            if (!confirmed) {
                return;
            }
            
            try {
                // ลบรายการออกจาก allComparisonsData
                if (allComparisonsData && Array.isArray(allComparisonsData)) {
                    allComparisonsData.splice(index, 1);
                    
                    // ลบข้อมูลที่เกี่ยวข้องออกจาก comparisonNotes, invalidDocuments, และ selfCheckMode
                    // ต้องปรับ index ทั้งหมดที่มากกว่า index ที่ลบ
                    const newComparisonNotes = {};
                    const newInvalidDocuments = {};
                    const newSelfCheckMode = {};
                    
                    for (let i = 0; i < allComparisonsData.length; i++) {
                        const oldIndex = i < index ? i : i + 1;
                        if (comparisonNotes[String(oldIndex)]) {
                            newComparisonNotes[String(i)] = comparisonNotes[String(oldIndex)];
                        }
                        if (invalidDocuments[oldIndex] !== undefined) {
                            newInvalidDocuments[i] = invalidDocuments[oldIndex];
                        }
                        if (selfCheckMode[oldIndex] !== undefined) {
                            newSelfCheckMode[i] = selfCheckMode[oldIndex];
                        }
                    }
                    
                    comparisonNotes = newComparisonNotes;
                    invalidDocuments = newInvalidDocuments;
                    selfCheckMode = newSelfCheckMode;
                    
                    // Re-render หน้าใหม่
                    await reRenderComparisonResults();
                    
                    showToast('ลบรายการสำเร็จ', 'success');
                } else {
                    showToast('ไม่พบข้อมูลรายการ', 'error');
                }
            } catch (error) {
                console.error('❌ Error removing comparison item:', error);
                showToast('เกิดข้อผิดพลาดในการลบรายการ: ' + error.message, 'error');
            }
        }
        
        // ฟังก์ชันแสดง modal ยืนยันการลบ
        function showDeleteConfirmModal(referenceNo) {
            return new Promise((resolve) => {
                const modalHtml = `
                    <div id="deleteConfirmModal" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.7); z-index: 10000; display: flex; align-items: center; justify-content: center; animation: fadeIn 0.3s;">
                        <div style="background: #1e293b; padding: 30px; border-radius: 12px; max-width: 500px; width: 90%; border: 1px solid #334155; animation: slideUp 0.3s;">
                            <div style="text-align: center; margin-bottom: 20px;">
                                <div style="font-size: 3em; margin-bottom: 10px;">🗑️</div>
                                <h3 style="color: #fafafa; margin: 0; font-size: 1.3em;">ยืนยันการลบรายการ</h3>
                            </div>
                            <div style="color: #cbd5e1; margin-bottom: 25px; line-height: 1.6;">
                                <p>คุณต้องการลบรายการนี้ออกหรือไม่?</p>
                                <p style="color: #fbbf24; font-weight: 600; margin-top: 10px;">เลขที่อ้างอิง: ${referenceNo}</p>
                                <p style="font-size: 0.9em; margin-top: 10px; color: #94a3b8;">การลบรายการนี้จะไม่สามารถกู้คืนได้</p>
                            </div>
                            <div style="display: flex; gap: 10px; justify-content: flex-end;">
                                <button onclick="closeDeleteConfirmModal(false)" style="padding: 10px 20px; background: #334155; color: #fafafa; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; transition: all 0.3s;" onmouseover="this.style.background='#475569';" onmouseout="this.style.background='#334155';">ยกเลิก</button>
                                <button onclick="closeDeleteConfirmModal(true)" style="padding: 10px 20px; background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; transition: all 0.3s;" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(239, 68, 68, 0.4)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';">ลบรายการ</button>
                            </div>
                        </div>
                    </div>
                `;
                document.body.insertAdjacentHTML('beforeend', modalHtml);
                
                window.closeDeleteConfirmModal = function(confirmed) {
                    const modal = document.getElementById('deleteConfirmModal');
                    if (modal) {
                        modal.style.animation = 'fadeOut 0.3s';
                        setTimeout(() => {
                            modal.remove();
                            delete window.closeDeleteConfirmModal;
                        }, 300);
                    }
                    resolve(confirmed);
                };
            });
        }
        
        // ฟังก์ชัน re-render comparison results หลังจากลบรายการ
        async function reRenderComparisonResults() {
            if (!allComparisonsData || !Array.isArray(allComparisonsData)) {
                return;
            }
            
            // ลบรายการซ้ำออกก่อนใช้งาน (ป้องกัน duplicates)
            const seenKeys = new Set();
            const uniqueComparisons = [];
            allComparisonsData.forEach(comp => {
                const purchaseInvoiceNo = comp.purchase_data?.invoice_no || comp.invoice_no || '';
                const ocrDocumentNo = comp.ocr_data?.document_no || comp.document_no || '';
                const uniqueKey = `${purchaseInvoiceNo}_${ocrDocumentNo}_${comp.match_status || ''}`;
                
                if (!seenKeys.has(uniqueKey)) {
                    seenKeys.add(uniqueKey);
                    uniqueComparisons.push(comp);
                }
            });
            
            // อัปเดต allComparisonsData ให้เป็น unique
            if (uniqueComparisons.length !== allComparisonsData.length) {
                allComparisonsData = uniqueComparisons;
            }
            
            // แยกรายการตามสถานะ
            const fullMatchedComparisons = allComparisonsData.filter(comp => comp.match_status === 'full_match');
            const partialMatchedComparisons = allComparisonsData.filter(comp => comp.match_status === 'partial_match');
            const mismatchedComparisons = allComparisonsData.filter(comp => comp.match_status === 'no_match');
            
            let html = '';
            
            if (allComparisonsData.length > 0) {
                html += `<div style="margin-top: 15px;">`;
                
                // Header พร้อมปุ่ม VAT-Info
                html += `<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">`;
                html += `<strong style="color: #cbd5e1; font-size: 1.1em;">📊 ผลการเปรียบเทียบ:</strong>`;
                html += `<a href="https://vsinter.rd.go.th/rd-webcontent-web/#/vatsearch" target="_blank" rel="noopener noreferrer" style="padding: 8px 16px; background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.9em; font-weight: 600; display: flex; align-items: center; gap: 6px; text-decoration: none; transition: all 0.3s;" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(59, 130, 246, 0.4)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';">`;
                html += `<span style="font-size: 1.1em;">🔍</span> ไปยังหน้า VAT-Info`;
                html += `</a>`;
                html += `</div>`;
                
                // สร้าง Tabs
                html += `<div class="comparison-tabs">`;
                html += `<button class="comparison-tab active" onclick="switchComparisonTab('all')">`;
                html += `ข้อมูลทั้งหมด <span class="comparison-tab-badge all">${allComparisonsData.length}</span>`;
                html += `</button>`;
                html += `<button class="comparison-tab" onclick="switchComparisonTab('mismatch')">`;
                html += `ข้อมูลไม่ตรงกัน <span class="comparison-tab-badge mismatch">${mismatchedComparisons.length}</span>`;
                html += `</button>`;
                html += `<button class="comparison-tab" onclick="switchComparisonTab('partial')">`;
                html += `ตรงกันบางส่วน <span class="comparison-tab-badge partial">${partialMatchedComparisons.length}</span>`;
                html += `</button>`;
                html += `<button class="comparison-tab" onclick="switchComparisonTab('match')">`;
                html += `ข้อมูลที่ตรงกัน <span class="comparison-tab-badge match">${fullMatchedComparisons.length}</span>`;
                html += `</button>`;
                html += `</div>`;
                
                // Search Box สำหรับค้นหาเลขที่เอกสารอ้างอิง
                html += `<div style="margin: 15px 0; padding: 12px; background: #1e293b; border-radius: 8px; border: 1px solid #334155;">`;
                html += `<div style="display: flex; align-items: center; gap: 10px;">`;
                html += `<span style="color: #cbd5e1; font-size: 0.95em; font-weight: 600;">🔍 ค้นหาเลขที่เอกสารอ้างอิง:</span>`;
                html += `<input type="text" id="comparisonReferenceSearch" placeholder="พิมพ์เลขที่เอกสารอ้างอิง..." oninput="filterComparisonByReference(this.value)" style="flex: 1; padding: 8px 12px; background: #0f172a; border: 1px solid #334155; border-radius: 6px; color: #fafafa; font-size: 0.9em; transition: all 0.3s;" onfocus="this.style.borderColor='#3b82f6'; this.style.boxShadow='0 0 0 3px rgba(59, 130, 246, 0.1)';" onblur="this.style.borderColor='#334155'; this.style.boxShadow='none';" />`;
                html += `<button onclick="clearComparisonSearch()" id="clearSearchBtn" style="padding: 8px 16px; background: #334155; color: #cbd5e1; border: 1px solid #475569; border-radius: 6px; cursor: pointer; font-size: 0.9em; font-weight: 600; transition: all 0.3s; display: none;" onmouseover="this.style.background='#475569';" onmouseout="this.style.background='#334155';">ล้าง</button>`;
                html += `</div>`;
                html += `<div id="comparisonSearchResult" style="margin-top: 8px; color: #94a3b8; font-size: 0.85em; display: none;"></div>`;
                html += `</div>`;
                
                // ปุ่มย้ายเอกสารทั้งหมดที่ไม่ตรงกัน
                const mismatchedCount = mismatchedComparisons.length + partialMatchedComparisons.length;
                if (mismatchedCount > 0) {
                    html += `<div style="margin: 15px 0; padding: 12px; background: #1e293b; border-radius: 8px; border: 1px solid #334155;">`;
                    html += `<div style="display: flex; justify-content: space-between; align-items: center;">`;
                    html += `<div style="color: #cbd5e1; font-size: 0.95em;">`;
                    html += `📋 พบรายการที่ไม่ตรงกันทั้งหมด <strong style="color: #fbbf24;">${mismatchedCount}</strong> รายการ`;
                    html += `</div>`;
                    html += `<button onclick="moveAllMismatchedDocuments()" style="padding: 10px 20px; background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.9em; font-weight: 600; display: flex; align-items: center; gap: 8px; transition: all 0.3s;" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(245, 158, 11, 0.4)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';">`;
                    html += `<span style="font-size: 1.1em;">📦</span> ย้ายเอกสารทั้งหมดที่ไม่ตรงกัน`;
                    html += `</button>`;
                    html += `</div>`;
                    html += `</div>`;
                }
                
                // Tab: ข้อมูลทั้งหมด
                html += `<div class="comparison-tab-content active" id="comparison-tab-all">`;
                allComparisonsData.forEach((comp, index) => {
                    html += generateComparisonRowHTML(comp, index, 'all');
                });
                html += `</div>`;
                
                // Tab: ข้อมูลไม่ตรงกัน
                html += `<div class="comparison-tab-content" id="comparison-tab-mismatch">`;
                if (mismatchedComparisons.length > 0) {
                    mismatchedComparisons.forEach((comp) => {
                        const actualIndex = allComparisonsData.indexOf(comp);
                        html += generateComparisonRowHTML(comp, actualIndex, 'mismatch');
                    });
                } else {
                    html += `<div style="text-align: center; padding: 40px; color: #94a3b8;">`;
                    html += `✅ ไม่มีข้อมูลที่ไม่ตรงกัน`;
                    html += `</div>`;
                }
                html += `</div>`;
                
                // Tab: ตรงกันบางส่วน
                html += `<div class="comparison-tab-content" id="comparison-tab-partial">`;
                if (partialMatchedComparisons.length > 0) {
                    partialMatchedComparisons.forEach((comp) => {
                        const actualIndex = allComparisonsData.indexOf(comp);
                        html += generateComparisonRowHTML(comp, actualIndex, 'partial');
                    });
                } else {
                    html += `<div style="text-align: center; padding: 40px; color: #94a3b8;">`;
                    html += `⚠️ ไม่มีข้อมูลที่ตรงกันบางส่วน`;
                    html += `</div>`;
                }
                html += `</div>`;
                
                // Tab: ข้อมูลที่ตรงกัน
                html += `<div class="comparison-tab-content" id="comparison-tab-match">`;
                if (fullMatchedComparisons.length > 0) {
                    fullMatchedComparisons.forEach((comp) => {
                        const actualIndex = allComparisonsData.indexOf(comp);
                        html += generateComparisonRowHTML(comp, actualIndex, 'match');
                    });
                } else {
                    html += `<div style="text-align: center; padding: 40px; color: #94a3b8;">`;
                    html += `❌ ไม่มีข้อมูลที่ตรงกัน`;
                    html += `</div>`;
                }
                html += `</div>`;
                
                // Pagination Controls
                html += `<div class="comparison-pagination-container" style="margin-top: 20px; padding: 15px; background: #1e293b; border-radius: 8px; border: 1px solid #334155; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">`;
                
                // ตัวเลือกแสดงรายการต่อหน้า
                html += `<div style="display: flex; align-items: center; gap: 10px;">`;
                html += `<span style="color: #cbd5e1; font-size: 0.9em;">แสดงรายการ:</span>`;
                html += `<select id="comparisonItemsPerPage" onchange="changeComparisonItemsPerPage(this.value)" style="padding: 6px 12px; background: #0f172a; border: 1px solid #334155; border-radius: 6px; color: #fafafa; font-size: 0.9em; cursor: pointer;">`;
                html += `<option value="10" ${comparisonPagination.itemsPerPage === 10 ? 'selected' : ''}>10</option>`;
                html += `<option value="25" ${comparisonPagination.itemsPerPage === 25 ? 'selected' : ''}>25</option>`;
                html += `<option value="50" ${comparisonPagination.itemsPerPage === 50 ? 'selected' : ''}>50</option>`;
                html += `<option value="100" ${comparisonPagination.itemsPerPage === 100 ? 'selected' : ''}>100</option>`;
                html += `</select>`;
                html += `<span style="color: #94a3b8; font-size: 0.85em;">รายการต่อหน้า</span>`;
                html += `</div>`;
                
                // Pagination Info และ Navigation
                html += `<div style="display: flex; align-items: center; gap: 15px; flex-wrap: wrap;">`;
                html += `<div id="comparisonPaginationInfo" style="color: #cbd5e1; font-size: 0.9em;"></div>`;
                html += `<div id="comparisonPaginationNav" style="display: flex; gap: 5px;"></div>`;
                html += `</div>`;
                
                html += `</div>`;
                
                html += `</div>`;
            } else {
                html += `<div style="color: #ef4444; margin-top: 15px;">`;
                html += `⚠️ ไม่พบข้อมูลสำหรับการเปรียบเทียบ`;
                html += `</div>`;
            }
            
            // อัปเดต HTML ใน details element
            const step5Details = document.getElementById('step5Details');
            if (step5Details) {
                // ลบ comparison-tabs และ tab-content ทั้งหมดก่อนเพื่อป้องกันการสร้างซ้ำ (ใช้ data-index แทน id selector)
                const existingComparisonElements = step5Details.querySelectorAll('.comparison-tabs, .comparison-tab-content, .comparison-row, [data-index], [style*="margin-top: 15px"]');
                existingComparisonElements.forEach(el => el.remove());
                
                // หา element ที่มี comparison-tabs เพื่อแทนที่เฉพาะส่วนนั้น
                const comparisonSection = step5Details.querySelector('[style*="margin-top: 15px"]');
                if (comparisonSection) {
                    // ถ้ายังมี comparisonSection อยู่ ให้ลบทั้งหมดก่อน
                    let current = comparisonSection;
                    let removedCount = 0;
                    while (current && current.nextSibling) {
                        const next = current.nextSibling;
                        // หยุดถ้าเจอ element ที่ไม่ใช่ comparison-related
                        if (!next.classList.contains('comparison-tabs') && 
                            !next.classList.contains('comparison-tab-content') && 
                            !next.classList.contains('comparison-row') &&
                            !next.querySelector('.comparison-tabs')) {
                            break;
                        }
                        current = next;
                    }
                    // ลบทุกอย่างตั้งแต่ comparisonSection ไปจนถึง current
                    let toRemove = comparisonSection;
                    while (toRemove && toRemove !== current?.nextSibling) {
                        const next = toRemove.nextSibling;
                        toRemove.remove();
                        removedCount++;
                        toRemove = next;
                    }
                    console.log(`🗑️ Removed ${removedCount} elements before re-rendering`);
                }
                
                // เพิ่ม HTML ใหม่ทั้งหมด (แทนที่ทั้งหมด)
                step5Details.innerHTML = html;
                
                // ลบ duplicates ทันทีหลังจาก set HTML
                const removeDuplicatesImmediately = () => {
                    const allTabs = ['all', 'mismatch', 'partial', 'match'];
                    allTabs.forEach(tabName => {
                        const tabElement = document.getElementById(`comparison-tab-${tabName}`);
                        if (!tabElement) return;
                        
                        const rows = Array.from(tabElement.querySelectorAll('.comparison-row'));
                        if (rows.length === 0) return;
                        
                        const seenIndices = new Set();
                        const duplicatesToRemove = [];
                        
                        rows.forEach(row => {
                            const rowIndex = row.getAttribute('data-index');
                            if (rowIndex !== null && rowIndex !== undefined) {
                                if (seenIndices.has(rowIndex)) {
                                    duplicatesToRemove.push(row);
                                } else {
                                    seenIndices.add(rowIndex);
                                }
                            }
                        });
                        
                        if (duplicatesToRemove.length > 0) {
                            duplicatesToRemove.forEach(row => row.remove());
                        }
                    });
                };
                
                // รอให้ DOM อัปเดตก่อนตรวจสอบ
                setTimeout(removeDuplicatesImmediately, 10);
                
                // ตรวจสอบและตั้งค่า active tab ให้ถูกต้อง
                setTimeout(() => {
                    const allTab = document.getElementById('comparison-tab-all');
                    if (allTab && !allTab.classList.contains('active')) {
                        // ถ้า all tab ไม่ได้ active ให้ตั้งค่าเป็น active
                        document.querySelectorAll('.comparison-tab-content').forEach(content => {
                            content.classList.remove('active');
                        });
                        allTab.classList.add('active');
                        
                        // อัปเดต tab button
                        document.querySelectorAll('.comparison-tab').forEach(tab => tab.classList.remove('active'));
                        const allTabButton = document.querySelector('.comparison-tab[onclick*="switchComparisonTab(\'all\')"]');
                        if (allTabButton) {
                            allTabButton.classList.add('active');
                        }
                        console.log('✅ Set "all" tab as active after re-render');
                    }
                    
                    // อัปเดต pagination หลังจากตั้งค่า tab
                    comparisonPagination.currentTab = 'all';
                    updateComparisonPagination();
                }, 50);
            }
        }
        
        // ฟังก์ชันสำหรับปุ่ม "เอกสารนี้ใช้งานไม่ได้" (แต่ละรายการ)
        async function markDocumentAsInvalid(index, referenceNo) {
            const isCurrentlyInvalid = invalidDocuments[index] || false;
            
            if (isCurrentlyInvalid) {
                // ถ้าใช้งานไม่ได้แล้ว ให้ถามว่าต้องการยกเลิกหรือไม่
                const confirmed = await showCancelInvalidModal();
                if (!confirmed) {
                    return;
                }
                // ยกเลิกการทำเครื่องหมาย
                delete invalidDocuments[index];
                // ลบคอมเมนต์ "เอกสารใช้ไม่ได้ให้เอาออก"
                const noteKey = String(index);
                const currentNote = comparisonNotes[noteKey] || '';
                if (currentNote.includes('เอกสารใช้ไม่ได้ให้เอาออก')) {
                    comparisonNotes[noteKey] = currentNote.replace(/\n?เอกสารใช้ไม่ได้ให้เอาออก/g, '').trim();
                }
                
                // อัปเดต UI (ใช้ findRowInActiveTab เพื่อหา row ใน tab ที่ active)
                const row = findRowInActiveTab(index);
                if (row) {
                    row.style.opacity = '1';
                    row.style.border = '';
                }
                
                // อัปเดตปุ่ม
                const button = event?.target?.closest('button');
                if (button) {
                    button.style.background = 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)';
                    button.innerHTML = '<span style="font-size: 1.1em;">❌</span> เอกสารนี้ใช้งานไม่ได้';
                    button.style.opacity = '1';
                }
                
                showToast('success', '✅ ยกเลิกการทำเครื่องหมายเอกสารใช้งานไม่ได้แล้ว');
                
                // Trigger auto-save
                triggerAutoSave();
                return;
            }
            
            // ถ้ายังไม่ได้ทำเครื่องหมาย ให้แสดง popup modal
            const confirmed = await showInvalidDocumentModal();
            if (!confirmed) {
                return;
            }
            
            // แสดง loading
            const loadingHtml = `
                <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 10000; display: flex; align-items: center; justify-content: center;" id="markInvalidLoadingOverlay-${index}">
                    <div style="background: #1e293b; padding: 30px; border-radius: 12px; text-align: center;">
                        <div class="spinner" style="border: 4px solid #334155; border-top: 4px solid #ef4444; border-radius: 50%; width: 50px; height: 50px; animation: spin 1s linear infinite; margin: 0 auto 15px;"></div>
                        <div style="color: #fafafa; font-size: 1.1em;">กำลังย้ายไฟล์และทำเครื่องหมายเอกสาร...</div>
                    </div>
                </div>
            `;
            document.body.insertAdjacentHTML('beforeend', loadingHtml);
            
            try {
                // เตรียมข้อมูลส่งไป API
                const taxMonth = document.getElementById('taxMonth')?.value;
                const taxYear = document.getElementById('taxYear')?.value;
                const company = document.getElementById('companyValue')?.value || document.getElementById('companySelect')?.value;
                
                if (!taxMonth || !taxYear || !company) {
                    throw new Error('กรุณาเลือกเดือนภาษีและบริษัทก่อน');
                }
                
                const taxMonthFormatted = `${taxYear}-${taxMonth}`;
                
                // ดึงข้อมูล OCR จาก comparison
                const comp = allComparisonsData[index];
                const ocrData = comp?.ocr_data || {};
                const purchaseData = comp?.purchase_data || {};
                const ocrFilename = ocrData.filename || ocrData.old_filename || '';
                
                const requestData = {
                    taxMonth: taxMonthFormatted,
                    company: company,
                    vatFolderPath: vatFolderPath,
                    documents: [{
                        index: index,
                        referenceNo: referenceNo,
                        ocrFilename: ocrFilename,
                        invoiceNo: comp?.invoice_no || ocrData.document_no || '',
                        purchaseData: purchaseData,
                        ocrData: ocrData
                    }]
                };
                
                // เรียก API เพื่อย้ายไฟล์
                const response = await fetch('/api/auditcheck/mark-documents-invalid', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(requestData)
                });
                
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({ error: 'Failed to mark document as invalid' }));
                    throw new Error(errorData.error || 'ไม่สามารถทำเครื่องหมายเอกสารได้');
                }
                
                const result = await response.json();
                
                document.getElementById(`markInvalidLoadingOverlay-${index}`)?.remove();
                
                if (result.success) {
                    // ทำเครื่องหมายว่าใช้ไม่ได้
                    invalidDocuments[index] = true;
                    
                    // เพิ่มคอมเมนต์
                    const noteKey = String(index);
                    const existingNote = comparisonNotes[noteKey] || '';
                    comparisonNotes[noteKey] = existingNote ? existingNote + '\nเอกสารใช้ไม่ได้ให้เอาออก' : 'เอกสารใช้ไม่ได้ให้เอาออก';
                    
                    // อัปเดต UI (ใช้ findRowInActiveTab เพื่อหา row ใน tab ที่ active)
                    const row = findRowInActiveTab(index);
                    if (row) {
                        row.style.opacity = '0.6';
                        row.style.border = '2px solid #ef4444';
                    }
                    
                    // อัปเดตปุ่ม
                    const button = event?.target?.closest('button');
                    if (button) {
                        button.style.background = 'linear-gradient(135deg, #dc2626 0%, #991b1b 100%)';
                        button.innerHTML = '<span style="font-size: 1.1em;">✓</span> ใช้งานไม่ได้แล้ว';
                        button.style.opacity = '0.7';
                    }
                    
                    showToast('success', `✅ ทำเครื่องหมายเอกสารใช้งานไม่ได้สำเร็จ!\n\nย้ายไฟล์: ${result.movedCount || 0} ไฟล์`);
                    
                    // Trigger auto-save
                    triggerAutoSave();
                } else {
                    throw new Error(result.error || 'ไม่สามารถทำเครื่องหมายเอกสารได้');
                }
            } catch (error) {
                console.error('❌ Error marking document as invalid:', error);
                document.getElementById(`markInvalidLoadingOverlay-${index}`)?.remove();
                alert('เกิดข้อผิดพลาด: ' + error.message);
            }
        }
        
        // ฟังก์ชันแสดง popup modal สำหรับยืนยันการทำเครื่องหมายเอกสารใช้งานไม่ได้
        function showInvalidDocumentModal() {
            return new Promise((resolve) => {
                const modalHtml = `
                    <div id="invalidDocumentModal" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 10002; display: flex; align-items: center; justify-content: center; animation: fadeIn 0.3s ease-out;">
                        <div style="background: #1e293b; padding: 30px; border-radius: 12px; max-width: 500px; width: 90%; box-shadow: 0 10px 30px rgba(0,0,0,0.5); animation: slideUp 0.3s ease-out;">
                            <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 20px;">
                                <div style="font-size: 2.5em;">⚠️</div>
                                <div>
                                    <h3 style="color: #fafafa; margin: 0; font-size: 1.3em; font-weight: 600;">ทำเครื่องหมายเอกสารใช้งานไม่ได้</h3>
                                    <p style="color: #94a3b8; margin: 5px 0 0 0; font-size: 0.95em;">คุณต้องการทำเครื่องหมายว่าอะสารนี้ใช้งานไม่ได้หรือไม่?</p>
                                </div>
                            </div>
                            
                            <div style="background: #0f172a; padding: 20px; border-radius: 8px; margin-bottom: 25px; border: 1px solid #334155;">
                                <div style="color: #cbd5e1; font-size: 0.95em; font-weight: 600; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                                    <span style="font-size: 1.2em;">📋</span> ระบบจะดำเนินการดังนี้:
                                </div>
                                <ul style="color: #cbd5e1; font-size: 0.9em; margin: 0; padding-left: 25px; line-height: 1.8;">
                                    <li>ย้ายไฟล์ไปยังโฟลเดอร์ "เอกสารใช้งานไม่ได้"</li>
                                    <li>เพิ่มคอมเมนต์ "เอกสารใช้ไม่ได้ให้เอาออก"</li>
                                    <li>ไฮไลท์สีแดงทั้งแถบในรายงาน Excel</li>
                                </ul>
                            </div>
                            
                            <div style="display: flex; gap: 10px; justify-content: flex-end;">
                                <button id="cancelInvalidBtn" style="padding: 12px 24px; background: #334155; color: #fafafa; border: none; border-radius: 6px; cursor: pointer; font-size: 0.95em; font-weight: 600; transition: all 0.3s;" onmouseover="this.style.background='#475569';" onmouseout="this.style.background='#334155';">
                                    ยกเลิก
                                </button>
                                <button id="confirmInvalidBtn" style="padding: 12px 24px; background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.95em; font-weight: 600; transition: all 0.3s;" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(239, 68, 68, 0.4)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';">
                                    ยืนยัน
                                </button>
                            </div>
                        </div>
                    </div>
                `;
                
                document.body.insertAdjacentHTML('beforeend', modalHtml);
                
                const modal = document.getElementById('invalidDocumentModal');
                const cancelBtn = document.getElementById('cancelInvalidBtn');
                const confirmBtn = document.getElementById('confirmInvalidBtn');
                
                // ปิด modal เมื่อคลิกปุ่มยกเลิกหรือคลิกนอก modal
                const closeModal = (result) => {
                    modal.style.animation = 'fadeOut 0.3s ease-in';
                    setTimeout(() => {
                        modal.remove();
                        resolve(result);
                    }, 300);
                };
                
                cancelBtn.addEventListener('click', () => closeModal(false));
                confirmBtn.addEventListener('click', () => closeModal(true));
                
                modal.addEventListener('click', (e) => {
                    if (e.target.id === 'invalidDocumentModal') {
                        closeModal(false);
                    }
                });
                
                // ปิด modal เมื่อกด ESC
                const handleEsc = (e) => {
                    if (e.key === 'Escape') {
                        closeModal(false);
                        document.removeEventListener('keydown', handleEsc);
                    }
                };
                document.addEventListener('keydown', handleEsc);
            });
        }
        
        // ฟังก์ชันแสดง popup modal สำหรับยกเลิกการทำเครื่องหมายเอกสารใช้งานไม่ได้
        function showCancelInvalidModal() {
            return new Promise((resolve) => {
                const modalHtml = `
                    <div id="cancelInvalidModal" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 10002; display: flex; align-items: center; justify-content: center; animation: fadeIn 0.3s ease-out;">
                        <div style="background: #1e293b; padding: 30px; border-radius: 12px; max-width: 450px; width: 90%; box-shadow: 0 10px 30px rgba(0,0,0,0.5); animation: slideUp 0.3s ease-out;">
                            <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 20px;">
                                <div style="font-size: 2.5em;">ℹ️</div>
                                <div>
                                    <h3 style="color: #fafafa; margin: 0; font-size: 1.3em; font-weight: 600;">ยกเลิกการทำเครื่องหมาย</h3>
                                    <p style="color: #94a3b8; margin: 5px 0 0 0; font-size: 0.95em;">เอกสารนี้ถูกทำเครื่องหมายว่าใช้งานไม่ได้แล้ว</p>
                                </div>
                            </div>
                            
                            <div style="background: #0f172a; padding: 20px; border-radius: 8px; margin-bottom: 25px; border: 1px solid #334155;">
                                <p style="color: #cbd5e1; font-size: 0.95em; margin: 0; line-height: 1.6;">
                                    คุณต้องการยกเลิกการทำเครื่องหมายเอกสารใช้งานไม่ได้หรือไม่?
                                </p>
                            </div>
                            
                            <div style="display: flex; gap: 10px; justify-content: flex-end;">
                                <button id="cancelCancelBtn" style="padding: 12px 24px; background: #334155; color: #fafafa; border: none; border-radius: 6px; cursor: pointer; font-size: 0.95em; font-weight: 600; transition: all 0.3s;" onmouseover="this.style.background='#475569';" onmouseout="this.style.background='#334155';">
                                    ยกเลิก
                                </button>
                                <button id="confirmCancelBtn" style="padding: 12px 24px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.95em; font-weight: 600; transition: all 0.3s;" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(16, 185, 129, 0.4)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';">
                                    ยืนยัน
                                </button>
                            </div>
                        </div>
                    </div>
                `;
                
                document.body.insertAdjacentHTML('beforeend', modalHtml);
                
                const modal = document.getElementById('cancelInvalidModal');
                const cancelBtn = document.getElementById('cancelCancelBtn');
                const confirmBtn = document.getElementById('confirmCancelBtn');
                
                // ปิด modal เมื่อคลิกปุ่มยกเลิกหรือคลิกนอก modal
                const closeModal = (result) => {
                    modal.style.animation = 'fadeOut 0.3s ease-in';
                    setTimeout(() => {
                        modal.remove();
                        resolve(result);
                    }, 300);
                };
                
                cancelBtn.addEventListener('click', () => closeModal(false));
                confirmBtn.addEventListener('click', () => closeModal(true));
                
                modal.addEventListener('click', (e) => {
                    if (e.target.id === 'cancelInvalidModal') {
                        closeModal(false);
                    }
                });
                
                // ปิด modal เมื่อกด ESC
                const handleEsc = (e) => {
                    if (e.key === 'Escape') {
                        closeModal(false);
                        document.removeEventListener('keydown', handleEsc);
                    }
                };
                document.addEventListener('keydown', handleEsc);
            });
        }
        
        // ฟังก์ชันส่งออก Excel
        async function exportToExcel() {
            console.log('📊 Exporting to Excel...');
            
            // แสดง loading
            const loadingHtml = `
                <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 10000; display: flex; align-items: center; justify-content: center;" id="exportLoadingOverlay">
                    <div style="background: #1e293b; padding: 30px; border-radius: 12px; text-align: center;">
                        <div class="spinner" style="border: 4px solid #334155; border-top: 4px solid #10b981; border-radius: 50%; width: 50px; height: 50px; animation: spin 1s linear infinite; margin: 0 auto 15px;"></div>
                        <div style="color: #fafafa; font-size: 1.1em;">กำลังสร้างรายงาน Excel...</div>
                    </div>
                </div>
            `;
            document.body.insertAdjacentHTML('beforeend', loadingHtml);
            
            try {
                // ดึงค่าจาก form
                const taxMonth = document.getElementById('taxMonth')?.value;
                const taxYear = document.getElementById('taxYear')?.value;
                const company = document.getElementById('companyValue')?.value || document.getElementById('companySelect')?.value;
                
                if (!taxMonth || !taxYear || !company) {
                    document.getElementById('exportLoadingOverlay')?.remove();
                    alert('กรุณาเลือกเดือนภาษีและบริษัทก่อนส่งออกรายงาน');
                    return;
                }
                
                const taxMonthFormatted = `${taxYear}-${taxMonth}`;
                
                // เตรียมข้อมูลส่งไป API (รวมหมายเหตุและ path ของโฟลเดอร์ VAT)
                const exportData = {
                    taxMonth: taxMonthFormatted,
                    company: company,
                    notes: comparisonNotes,
                    vatFolderPath: vatFolderPath,  // ส่ง path ของโฟลเดอร์ VAT
                    ocrDataFromStep2: step4OCRData || [],  // ส่งข้อมูล OCR จาก Step 2
                    invalidDocuments: invalidDocuments,  // ส่งสถานะเอกสารใช้ไม่ได้
                    approvals: comparisonApprovals,  // ส่งข้อมูลการอนุมัติฟิลด์
                    comparisons: allComparisonsData || [],  // ส่งข้อมูล comparisons ที่ถูกกรองแล้ว (รวมรายการที่ลบออกแล้ว)
                    selfCheckMode: selfCheckMode || {}  // ส่งสถานะการกดปุ่ม "ตรวจสอบเพิ่ม"
                };
                
                console.log('📊 Sending export request:', {
                    ...exportData,
                    ocrDataFromStep2: step4OCRData ? `${step4OCRData.length} items` : 'none'
                });
                
                // เรียก API เพื่อสร้าง Excel
                const response = await fetch('/api/auditcheck/export-excel', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(exportData)
                });
                
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({ error: 'Failed to export Excel' }));
                    throw new Error(errorData.error || 'Failed to export Excel');
                }
                
                // รับข้อมูลจาก API (ไม่ใช่ไฟล์)
                const result = await response.json();
                
                document.getElementById('exportLoadingOverlay')?.remove();
                
                if (result.success) {
                    // แสดงข้อความแจ้งเตือนว่าบันทึกไว้ในโฟลเดอร์ ภ.พ.30 แล้ว
                    const filePath = result.filePath || result.pph30FolderPath || result.vatFolderPath || '';
                    const fileName = result.fileName || `รายงานตรวจภาษี_${company}_${taxMonthFormatted}.xlsx`;
                    const pph30FolderPath = result.pph30FolderPath || result.vatFolderPath || '';
                    
                    // แสดง modal แจ้งเตือน
                    const alertHtml = `
                        <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 10001; display: flex; align-items: center; justify-content: center;" id="exportSuccessModal">
                            <div style="background: #1e293b; padding: 30px; border-radius: 12px; max-width: 600px; width: 90%; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
                                <div style="text-align: center; margin-bottom: 20px;">
                                    <div style="font-size: 3em; margin-bottom: 10px;">✅</div>
                                    <h3 style="color: #10b981; margin: 0; font-size: 1.3em;">บันทึกรายงานสำเร็จ</h3>
                                </div>
                                <div style="background: #0f172a; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #334155;">
                                    <div style="color: #cbd5e1; margin-bottom: 10px;">
                                        <strong style="color: #60a5fa;">📁 โฟลเดอร์ ภ.พ.30:</strong><br>
                                        <span style="color: #fafafa; word-break: break-all;">${pph30FolderPath ? pph30FolderPath.replace(/\\/g, '/') : (filePath ? filePath.replace(/\\/g, '/') : 'ไม่พบ path')}</span>
                                    </div>
                                    <div style="color: #cbd5e1; margin-top: 15px;">
                                        <strong style="color: #60a5fa;">📄 ชื่อไฟล์:</strong><br>
                                        <span style="color: #fafafa;">${fileName}</span>
                                    </div>
                                </div>
                                <div style="text-align: center;">
                                    <button onclick="document.getElementById('exportSuccessModal').remove();" style="padding: 12px 30px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 1em; font-weight: 600; transition: all 0.3s;" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(16, 185, 129, 0.4)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';">
                                        ปิด
                                    </button>
                                </div>
                            </div>
                        </div>
                    `;
                    document.body.insertAdjacentHTML('beforeend', alertHtml);
                } else {
                    throw new Error(result.error || 'ไม่สามารถบันทึกรายงานได้');
                }
                
            } catch (error) {
                console.error('❌ Error exporting Excel:', error);
                document.getElementById('exportLoadingOverlay')?.remove();
                alert('เกิดข้อผิดพลาดในการส่งออก Excel: ' + error.message);
            }
        }
        
        function showAlert(type, message) {
            // Remove existing alerts
            const existingAlerts = document.querySelectorAll('.alert');
            existingAlerts.forEach(alert => alert.remove());
            
            // Create new alert
            const alert = document.createElement('div');
            alert.className = `alert ${type}`;
            alert.textContent = message;
            
            // Insert at the top of the form section
            const formSection = document.querySelector('.form-section');
            formSection.insertBefore(alert, formSection.firstChild);
            
            // Auto remove after 5 seconds
            setTimeout(() => {
                alert.remove();
            }, 5000);
        }
        
        // ตัวแปรสำหรับเก็บข้อมูล OCR confirmation
        let ocrConfirmData = null;
        
        // ตัวแปรเก็บข้อมูลโฟลเดอร์ย่อย
        let subfoldersData = [];
        
        function showOCRConfirmModal(taxMonth, companyName, totalFiles, estimatedTime, actualTaxMonth, actualCompany, subfolders = []) {
            console.log('🔍 showOCRConfirmModal called with:', {
                taxMonth,
                companyName,
                totalFiles,
                estimatedTime,
                actualTaxMonth,
                actualCompany,
                subfolders
            });
            
            // เก็บข้อมูลโฟลเดอร์ย่อย
            subfoldersData = subfolders || [];
            
            // เก็บข้อมูลสำหรับใช้เมื่อกดตกลง
            ocrConfirmData = {
                taxMonth: actualTaxMonth,
                company: actualCompany,
                totalFiles: totalFiles,
                estimatedTime: estimatedTime,
                subfolders: subfoldersData
            };
            
            // แสดงข้อมูลใน modal
            const modalTaxMonthEl = document.getElementById('modalTaxMonth');
            const modalCompanyNameEl = document.getElementById('modalCompanyName');
            const modalTotalFilesEl = document.getElementById('modalTotalFiles');
            const modalEstimatedTimeEl = document.getElementById('modalEstimatedTime');
            const modalEl = document.getElementById('ocrConfirmModal');
            const folderSelectionContainer = document.getElementById('folderSelectionContainer');
            const folderCheckboxes = document.getElementById('folderCheckboxes');
            
            if (!modalEl) {
                console.error('❌ Modal element not found!');
                alert('ไม่พบ modal element กรุณารีเฟรชหน้าเว็บ');
                return;
            }
            
            if (modalTaxMonthEl) modalTaxMonthEl.textContent = taxMonth || '-';
            if (modalCompanyNameEl) modalCompanyNameEl.textContent = companyName || '-';
            if (modalTotalFilesEl) modalTotalFilesEl.textContent = totalFiles ? `${totalFiles} ไฟล์` : '-';
            if (modalEstimatedTimeEl) modalEstimatedTimeEl.textContent = estimatedTime || '-';
            
            // แสดงรายการโฟลเดอร์ย่อย
            if (folderSelectionContainer && folderCheckboxes && subfoldersData.length > 0) {
                folderSelectionContainer.style.display = 'block';
                folderCheckboxes.innerHTML = '';
                
                subfoldersData.forEach((folder, index) => {
                    const checkboxId = `folderCheckbox_${index}`;
                    const checkboxHtml = `
                        <label style="display: flex; align-items: center; cursor: pointer; padding: 6px 10px; background: #1e293b; border-radius: 4px; border: 2px solid #334155; transition: all 0.2s; white-space: nowrap; flex: 0 0 auto; min-width: fit-content;" 
                               onmouseover="this.style.borderColor='#3b82f6'; this.style.background='#1e293b';" 
                               onmouseout="this.style.borderColor='#334155'; this.style.background='#1e293b';">
                            <input type="checkbox" id="${checkboxId}" value="${folder.path}" checked 
                                   style="margin-right: 8px; cursor: pointer; width: 16px; height: 16px; flex-shrink: 0;"
                                   onchange="updateSelectedFolders()">
                            <span style="color: #fafafa; font-weight: 600; font-size: 0.85em; margin-right: 8px;">📁 ${folder.name}</span>
                            <span style="color: #94a3b8; font-size: 0.75em;">(${folder.pdf_count} ไฟล์)</span>
                        </label>
                    `;
                    folderCheckboxes.innerHTML += checkboxHtml;
                });
            } else if (folderSelectionContainer) {
                folderSelectionContainer.style.display = 'none';
            }
            
            console.log('📊 Modal elements updated');
            
            // แสดง modal
            modalEl.classList.add('show');
            console.log('📊 Modal shown (class added)');
            
            // ตั้งค่า event listener สำหรับปุ่มตกลง
            const confirmBtn = document.getElementById('modalConfirmBtn');
            if (confirmBtn) {
                // ใช้ closure เพื่อเก็บค่าพารามิเตอร์
                (function(confirmTaxMonth, confirmCompany, confirmTotalFiles, confirmEstimatedTime) {
                    confirmBtn.onclick = async function() {
                        // ใช้ companyValue.value โดยตรงเพื่อให้แน่ใจว่าได้ค่า path ที่ถูกต้อง
                        const actualCompanyForConfirm = document.getElementById('companyValue')?.value || document.getElementById('companySelect')?.value || confirmCompany;
                        console.log('✅ Confirm button clicked');
                        console.log('📊 ocrConfirmData:', ocrConfirmData);
                        console.log('📊 Using parameters:', {
                            taxMonth: confirmTaxMonth,
                            company: confirmCompany,
                            actualCompanyForConfirm: actualCompanyForConfirm,
                            totalFiles: confirmTotalFiles,
                            estimatedTime: confirmEstimatedTime
                        });
                        
                        // ดึงค่า OCR mode ที่เลือก
                        const ocrModeRadio = document.querySelector('input[name="ocrMode"]:checked');
                        const ocrMode = ocrModeRadio ? ocrModeRadio.value : 'new';
                        
                        // ดึงรายการโฟลเดอร์ที่เลือก
                        const checkboxes = document.querySelectorAll('#folderCheckboxes input[type="checkbox"]:checked');
                        const selectedFolders = Array.from(checkboxes).map(cb => cb.value);
                        
                        console.log('📊 Selected OCR Mode:', ocrMode);
                        console.log('📁 Selected Folders:', selectedFolders);
                        
                        // ตรวจสอบว่ามีโฟลเดอร์ถูกเลือกหรือไม่
                        if (selectedFolders.length === 0 && subfoldersData.length > 0) {
                            alert('กรุณาเลือกโฟลเดอร์ที่ต้องการอ่านอย่างน้อย 1 โฟลเดอร์');
                            return;
                        }
                        
                        // เก็บข้อมูลก่อนปิด modal
                        const confirmData = {
                            taxMonth: confirmTaxMonth,
                            company: actualCompanyForConfirm,  // ใช้ actualCompanyForConfirm แทน confirmCompany
                            totalFiles: confirmTotalFiles,
                            estimatedTime: confirmEstimatedTime,
                            ocrMode: ocrMode,  // เพิ่ม OCR mode
                            selectedFolders: selectedFolders.length > 0 ? selectedFolders : null  // เพิ่มรายการโฟลเดอร์ที่เลือก
                        };
                        
                        console.log('📊 Stored confirmData:', confirmData);
                        
                        // ปิด modal
                        closeOCRConfirmModal();
                        
                        // รัน OCR จริงๆ (ใช้ข้อมูลที่เก็บไว้ก่อนปิด modal)
                        if (confirmData && confirmData.taxMonth && confirmData.company) {
                            console.log('🚀 Calling runOCRAfterConfirm with:', confirmData);
                            // เรียก runOCRAfterConfirm โดยไม่ต้อง await (เพราะเป็น async function)
                            runOCRAfterConfirm(confirmData.taxMonth, confirmData.company, confirmData.totalFiles, confirmData.estimatedTime, confirmData.ocrMode, confirmData.selectedFolders).catch(err => {
                                console.error('❌ Error in runOCRAfterConfirm:', err);
                            });
                        } else {
                            console.error('❌ Invalid confirm data!', confirmData);
                            alert('ข้อมูลไม่ครบถ้วน กรุณาลองอีกครั้ง');
                        }
                    };
                })(actualTaxMonth, actualCompany, totalFiles, estimatedTime);
            } else {
                console.error('❌ Confirm button not found!');
            }
        }
        
        // ฟังก์ชันเลือกโฟลเดอร์ทั้งหมด
        function selectAllFolders() {
            const checkboxes = document.querySelectorAll('#folderCheckboxes input[type="checkbox"]');
            checkboxes.forEach(checkbox => {
                checkbox.checked = true;
            });
            console.log('✅ เลือกโฟลเดอร์ทั้งหมด:', checkboxes.length, 'โฟลเดอร์');
        }
        
        // ฟังก์ชันยกเลิกการเลือกโฟลเดอร์ทั้งหมด
        function deselectAllFolders() {
            const checkboxes = document.querySelectorAll('#folderCheckboxes input[type="checkbox"]');
            checkboxes.forEach(checkbox => {
                checkbox.checked = false;
            });
            console.log('❌ ยกเลิกการเลือกโฟลเดอร์ทั้งหมด');
        }
        
        function closeOCRConfirmModal() {
            console.log('🔍 closeOCRConfirmModal called');
            const modalEl = document.getElementById('ocrConfirmModal');
            if (modalEl) {
                modalEl.classList.remove('show');
                console.log('📊 Modal hidden (class removed)');
            }
            ocrConfirmData = null;
            subfoldersData = [];
            
            // กลับไปแสดงตัวเลือกของระบบ OCR เมื่อผู้ใช้กดยกเลิก
            if (step4Data && step4Data.taxMonth && step4Data.company) {
                restoreStep4Options(step4Data.taxMonth, step4Data.company);
            } else {
                // ถ้าไม่มีข้อมูล ให้รีเซ็ตสถานะ Step 4
                const step = document.getElementById('step4');
                const status = document.getElementById('step4Status');
                const details = document.getElementById('step4Details');
                
                if (step && status && details) {
                    step.classList.remove('active', 'completed', 'error');
                    status.textContent = 'รอตรวจสอบ';
                    status.className = 'step-status pending';
                    details.innerHTML = 'รอการตรวจสอบขั้นตอนก่อนหน้า...';
                    console.log('📊 Step 4 status reset to pending');
                }
            }
        }
        
        // ฟังก์ชันสำหรับแสดงตัวเลือกของระบบ OCR อีกครั้ง
        function restoreStep4Options(taxMonth, company) {
            const step = document.getElementById('step4');
            const status = document.getElementById('step4Status');
            const details = document.getElementById('step4Details');
            
            if (!step || !status || !details) {
                console.error('❌ Step 4 elements not found!');
                return;
            }
            
            step.classList.remove('active', 'completed', 'error');
            status.textContent = 'ไม่พบไฟล์ Excel';
            status.className = 'step-status error';
            
            // สร้าง HTML สำหรับแสดงตัวเลือก
            let html = `<div style="margin-bottom: 15px;">`;
            html += `<strong>❌ ไม่พบไฟล์ Excel OCR ในโฟลเดอร์ VAT/vat/Vat สำหรับเดือน ${taxMonth}</strong><br>`;
            html += `<div style="margin-top: 10px; color: #cbd5e1; font-size: 0.9em;">💡 ระบบค้นหาไฟล์ Excel ที่มีคำว่า "ocr" หรือ "invoice_data" ในชื่อไฟล์ภายในโฟลเดอร์ VAT/vat/Vat</div>`;
            
            // เพิ่มตัวเลือกเมื่อไม่พบไฟล์ OCR
            html += `<div style="margin-top: 20px; padding: 20px; background: #1e293b; border-radius: 8px; border: 2px solid #3b82f6;">`;
            html += `<div style="color: #60a5fa; font-weight: 600; margin-bottom: 15px; font-size: 1.1em;">💡 ตัวเลือกการดำเนินการ:</div>`;
            html += `<div style="display: flex; gap: 15px; flex-wrap: wrap;">`;
            
            // ปุ่ม "ใช้ระบบ OCR" - ใช้ companyValue.value โดยตรงเพื่อหลีกเลี่ยงปัญหา escape
            const currentCompany = document.getElementById('companyValue')?.value || document.getElementById('companySelect')?.value || company || '';
            // Escape สำหรับใช้ใน onclick attribute
            const currentCompanyEscaped = currentCompany.replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/"/g, '&quot;');
            html += `<button onclick="runOCRForStep4('${taxMonth}', '${currentCompanyEscaped}')" class="btn" style="flex: 1; min-width: 200px; background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%);">`;
            html += `🤖 ใช้ระบบ OCR<br>`;
            html += `<span style="font-size: 0.85em; opacity: 0.9;">รัน OCR จากไฟล์ PDF และสร้าง Excel</span>`;
            html += `</button>`;
            
            // ปุ่ม "เลือกไฟล์ Excel"
            html += `<button onclick="uploadExcelForStep4('${taxMonth}', '${currentCompanyEscaped}')" class="btn" style="flex: 1; min-width: 200px; background: linear-gradient(90deg, #10b981 0%, #059669 100%);">`;
            html += `📁 เลือกไฟล์ Excel<br>`;
            html += `<span style="font-size: 0.85em; opacity: 0.9;">เลือกไฟล์ Excel ที่มีอยู่แล้ว</span>`;
            html += `</button>`;
            
            html += `</div>`;
            html += `</div>`;
            html += `</div>`;
            
            details.innerHTML = html;
            console.log('📊 Step 4 options restored');
        }
        
        async function runOCRAfterConfirm(taxMonth, company, totalFiles, estimatedTime, ocrMode = 'new', selectedFolders = null) {
            // ใช้ companyValue.value โดยตรงเพื่อให้แน่ใจว่าได้ค่า path ที่ถูกต้อง
            const actualCompany = document.getElementById('companyValue')?.value || document.getElementById('companySelect')?.value || company;
            console.log('🚀 runOCRAfterConfirm called with:', { taxMonth, company, actualCompany, totalFiles, estimatedTime, ocrMode, selectedFolders });
            
            const step = document.getElementById('step4');
            const status = document.getElementById('step4Status');
            const details = document.getElementById('step4Details');
            
            if (!step || !status || !details) {
                console.error('❌ Step 4 elements not found!');
                alert('ไม่พบ elements ของ Step 4 กรุณารีเฟรชหน้าเว็บ');
                return;
            }
            
            // รัน OCR จริงๆ
            step.classList.add('active');
            status.textContent = 'กำลังรัน OCR...';
            status.className = 'step-status checking';
            
            // สร้าง progress indicator แบบ spinner และ countdown
            let currentProgress = 0;
            
            // แปลง estimatedTime เป็นวินาที (format: "1.5 นาที" หรือ "30 วินาที")
            let estimatedSeconds = 0;
            if (estimatedTime) {
                const timeMatch = estimatedTime.match(/([\d.]+)\s*(นาที|วินาที)/);
                if (timeMatch) {
                    const value = parseFloat(timeMatch[1]);
                    const unit = timeMatch[2];
                    if (unit === 'นาที') {
                        estimatedSeconds = Math.ceil(value * 60);
                    } else if (unit === 'วินาที') {
                        estimatedSeconds = Math.ceil(value);
                    }
                }
            }
            // ถ้าไม่สามารถ parse ได้ ให้ใช้ค่า default (30 วินาทีต่อไฟล์)
            if (estimatedSeconds === 0) {
                estimatedSeconds = totalFiles * 30;
            }
            
            // ตัวแปรสำหรับ countdown
            let countdownSeconds = estimatedSeconds;
            var countdownInterval = null;
            
            // ฟังก์ชันสำหรับ format เวลา
            function formatTime(seconds) {
                const mins = Math.floor(seconds / 60);
                const secs = seconds % 60;
                if (mins > 0) {
                    return `${mins}:${secs.toString().padStart(2, '0')}`;
                }
                return `${secs} วินาที`;
            }
            
            const progressHtml = `
                <div id="ocrProgressContainer" style="margin-bottom: 15px;">
                    <div style="color: #60a5fa; font-weight: 600; margin-bottom: 15px; text-align: center;">📊 ความคืบหน้า OCR:</div>
                    <div style="background: #0f172a; padding: 30px; border-radius: 10px; text-align: center;">
                        <!-- Spinner -->
                        <div style="display: inline-block; margin-bottom: 20px;">
                            <div style="border: 4px solid #334155; border-top: 4px solid #3b82f6; border-radius: 50%; width: 60px; height: 60px; animation: spin 1s linear infinite;"></div>
                        </div>
                        <!-- Countdown Timer -->
                        <div style="margin-bottom: 15px;">
                            <div style="color: #fbbf24; font-size: 2em; font-weight: bold; font-family: 'Courier New', monospace;" id="ocrCountdownTimer">${formatTime(countdownSeconds)}</div>
                            <div style="color: #94a3b8; font-size: 0.9em; margin-top: 5px;">เวลาที่เหลือ</div>
                        </div>
                        <!-- Pause Status (แสดงเมื่อระบบกำลังพัก) -->
                        <div id="ocrPauseStatus" style="display: none; margin-bottom: 15px; padding: 15px; background: #1e293b; border-radius: 8px; border-left: 4px solid #fbbf24;">
                            <div style="color: #fbbf24; font-weight: 600; margin-bottom: 8px;">⏸️ ระบบกำลังพัก</div>
                            <div style="color: #cbd5e1; font-size: 0.9em; margin-bottom: 5px;" id="ocrPauseCountdown">รออีก <span id="ocrPauseSeconds">0</span> วินาที</div>
                            <div style="color: #94a3b8; font-size: 0.85em;" id="ocrRemainingInfo">เอกสารที่เหลือ: <span id="ocrRemainingFiles">0</span> ไฟล์, เวลาที่ต้องรอประมาณ: <span id="ocrRemainingMinutes">0</span> นาที</div>
                        </div>
                        <div style="color: #94a3b8; font-size: 0.9em; margin-top: 10px;" id="ocrCurrentFile">กำลังเริ่มต้น...</div>
                        <div style="color: #60a5fa; font-size: 0.85em; margin-top: 10px;" id="ocrCurrentStep"></div>
                    </div>
                </div>
            `;
            const statusMessageHtml = `<div id="ocrStatusMessage" style="color: #cbd5e1; margin-top: 10px; text-align: center;">⏳ กำลังรันระบบ OCR สำหรับ ${totalFiles} ไฟล์ (คาดว่าจะใช้เวลา ${estimatedTime})...</div>`;
            details.innerHTML = progressHtml + statusMessageHtml;
            
            // เริ่ม countdown timer
            const countdownTimerEl = document.getElementById('ocrCountdownTimer');
            countdownInterval = setInterval(() => {
                if (countdownSeconds > 0) {
                    countdownSeconds--;
                    if (countdownTimerEl) {
                        countdownTimerEl.textContent = formatTime(countdownSeconds);
                    }
                } else {
                    // ถ้านับถอยหลังถึง 0 แล้ว แต่ OCR ยังไม่เสร็จ ให้แสดง "กำลังดำเนินการ..."
                    if (countdownTimerEl) {
                        countdownTimerEl.textContent = 'กำลังดำเนินการ...';
                        countdownTimerEl.style.color = '#60a5fa';
                    }
                }
            }, 1000);
            
            try {
                console.log('📤 Sending OCR request:', { taxMonth, company: actualCompany });
                
                const requestBody = {
                    taxMonth: taxMonth,
                    company: actualCompany,  // ใช้ actualCompany แทน company
                    checkOnly: false,  // รัน OCR จริงๆ
                    ocrMode: ocrMode || 'new',  // ส่ง OCR mode (new หรือ continue)
                    include_subfolders: true  // อ่านไฟล์ PDF จากโฟลเดอร์ย่อยด้วย
                };
                
                // ถ้ามีการเลือกโฟลเดอร์เฉพาะ ให้ส่งรายการโฟลเดอร์ที่เลือกไปด้วย
                if (selectedFolders && selectedFolders.length > 0) {
                    requestBody.selectedFolders = selectedFolders;
                }
                
                // ส่ง request (ไม่รอ response ทันที เพื่อให้สามารถ polling ได้ทันที)
                const responsePromise = fetch('/api/auditcheck/run-ocr', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(requestBody)
                });
                
                // เริ่ม polling ทันที (ไม่ต้องรอ response) โดยใช้ sessionId ที่จะได้จาก response
                // แต่เราจะต้องรอ response ก่อนเพื่อให้ได้ sessionId
                // ดังนั้นเราจะเริ่ม polling หลังจากได้ sessionId แล้ว
                
                // รอ response
                const response = await responsePromise;
                console.log('📥 OCR response status:', response.status);
                
                if (!response.ok) {
                    const errorText = await response.text();
                    console.error('❌ OCR response error:', errorText);
                    
                    // หยุด countdown timer
                    if (countdownInterval) {
                        clearInterval(countdownInterval);
                        countdownInterval = null;
                    }
                    
                    // หยุด progress polling
                    if (window.ocrProgressPollInterval) {
                        clearInterval(window.ocrProgressPollInterval);
                        window.ocrProgressPollInterval = null;
                    }
                    
                    throw new Error(`HTTP ${response.status}: ${errorText}`);
                }
                
                // อ่าน response
                const data = await response.json();
                console.log('📊 OCR response data:', data);
                
                // เก็บ sessionId สำหรับ polling progress
                let sessionId = data.sessionId || null;
                let progressPollInterval = null;
                
                // อัพเดท totalFiles จาก response (ถ้ามี) เพื่อให้ตรงกับจำนวนไฟล์จริงที่ OCR จะทำงาน
                if (data.totalFiles !== undefined) {
                    totalFiles = data.totalFiles;
                    console.log('📊 Updated totalFiles from response:', totalFiles);
                    
                    // อัพเดท estimatedSeconds จาก backend ถ้ามี
                    if (data.estimatedSeconds !== undefined) {
                        estimatedSeconds = data.estimatedSeconds;
                        countdownSeconds = estimatedSeconds;
                        console.log('📊 Updated estimatedSeconds from response:', estimatedSeconds);
                        
                        // อัพเดท countdown timer
                        const countdownTimerEl = document.getElementById('ocrCountdownTimer');
                        if (countdownTimerEl) {
                            countdownTimerEl.textContent = formatTime(countdownSeconds);
                        }
                    }
                    
                    // อัพเดท status message
                    const statusMessageEl = document.getElementById('ocrStatusMessage');
                    if (statusMessageEl) {
                        const updatedEstimatedTime = data.estimatedTime || estimatedTime;
                        statusMessageEl.textContent = `⏳ กำลังรันระบบ OCR สำหรับ ${totalFiles} ไฟล์ (คาดว่าจะใช้เวลา ${updatedEstimatedTime})...`;
                    }
                }
                
                // ถ้ามี sessionId ให้เริ่ม polling progress
                if (sessionId) {
                    console.log('🔄 Starting progress polling for session:', sessionId);
                    
                    // ฟังก์ชันสำหรับ polling progress
                    const pollProgress = async () => {
                        try {
                            const progressResponse = await fetch(`/api/auditcheck/ocr-progress/${sessionId}`);
                            if (!progressResponse.ok) {
                                console.warn('⚠️ Failed to fetch progress:', progressResponse.status);
                                return;
                            }
                            
                            const progressData = await progressResponse.json();
                            console.log('📊 Progress data:', progressData);
                            
                            // อัปเดตข้อมูล progress
                            if (progressData.current !== undefined && progressData.total !== undefined) {
                                const currentFileEl = document.getElementById('ocrCurrentFile');
                                if (currentFileEl) {
                                    currentFileEl.textContent = `กำลังประมวลผล: ${progressData.current}/${progressData.total} ไฟล์${progressData.filename ? ` - ${progressData.filename}` : ''}`;
                                }
                            }
                            
                            // อัปเดต current_step และ step_details
                            if (progressData.current_step) {
                                const currentStepEl = document.getElementById('ocrCurrentStep');
                                if (currentStepEl) {
                                    currentStepEl.textContent = progressData.current_step;
                                    if (progressData.step_details) {
                                        currentStepEl.textContent += ` - ${progressData.step_details}`;
                                    }
                                }
                            }
                            
                            // แสดงข้อมูลการพัก (ถ้ากำลังพักอยู่)
                            const pauseStatusEl = document.getElementById('ocrPauseStatus');
                            const isPaused = progressData.is_paused === true;
                            
                            if (isPaused && pauseStatusEl) {
                                pauseStatusEl.style.display = 'block';
                                
                                // อัปเดตเวลาที่เหลือในการพัก
                                const pauseSecondsEl = document.getElementById('ocrPauseSeconds');
                                const pauseCountdownEl = document.getElementById('ocrPauseCountdown');
                                if (pauseSecondsEl && progressData.pause_remaining_seconds !== undefined) {
                                    const remainingSeconds = progressData.pause_remaining_seconds;
                                    pauseSecondsEl.textContent = remainingSeconds;
                                    
                                    // แสดงเป็นนาที:วินาที หรือวินาที
                                    if (pauseCountdownEl) {
                                        if (remainingSeconds >= 60) {
                                            const mins = Math.floor(remainingSeconds / 60);
                                            const secs = remainingSeconds % 60;
                                            pauseCountdownEl.innerHTML = `รออีก <span id="ocrPauseSeconds">${mins}:${secs.toString().padStart(2, '0')}</span> นาที`;
                                        } else {
                                            pauseCountdownEl.innerHTML = `รออีก <span id="ocrPauseSeconds">${remainingSeconds}</span> วินาที`;
                                        }
                                    }
                                }
                                
                                // อัปเดตข้อมูลเอกสารที่เหลือและเวลาที่ต้องรอ
                                const remainingFilesEl = document.getElementById('ocrRemainingFiles');
                                const remainingMinutesEl = document.getElementById('ocrRemainingMinutes');
                                if (remainingFilesEl && progressData.remaining_files !== undefined) {
                                    remainingFilesEl.textContent = progressData.remaining_files;
                                }
                                if (remainingMinutesEl && progressData.estimated_remaining_minutes !== undefined) {
                                    remainingMinutesEl.textContent = progressData.estimated_remaining_minutes.toFixed(1);
                                }
                            } else if (pauseStatusEl) {
                                pauseStatusEl.style.display = 'none';
                            }
                            
                            // ถ้าเสร็จแล้ว ให้หยุด polling
                            if (progressData.status === 'completed' || progressData.status === 'error') {
                                if (progressPollInterval) {
                                    clearInterval(progressPollInterval);
                                    progressPollInterval = null;
                                }
                            }
                        } catch (error) {
                            console.error('❌ Error polling progress:', error);
                        }
                    };
                    
                    // เริ่ม polling ทันทีครั้งแรก
                    pollProgress();
                    
                    // Poll ทุก 1 วินาที (เพื่อให้เห็นการนับถอยหลังของการพัก)
                    progressPollInterval = setInterval(pollProgress, 1000);
                    
                    // เก็บ reference เพื่อสามารถหยุดได้เมื่อเสร็จ
                    window.ocrProgressPollInterval = progressPollInterval;
                }
                
                // ถ้ามี ocrData แสดงว่า OCR เสร็จแล้ว
                if (data.ocrData && Array.isArray(data.ocrData)) {
                    console.log('📊 OCR completed');
                    
                    // หยุด countdown timer
                    if (countdownInterval) {
                        clearInterval(countdownInterval);
                        countdownInterval = null;
                    }
                    
                    // หยุด progress polling
                    if (window.ocrProgressPollInterval) {
                        clearInterval(window.ocrProgressPollInterval);
                        window.ocrProgressPollInterval = null;
                    }
                    
                    // ซ่อน progress container ทันที
                    const progressContainer = document.getElementById('ocrProgressContainer');
                    if (progressContainer) {
                        progressContainer.style.display = 'none';
                    }
                    
                    const statusMessage = document.getElementById('ocrStatusMessage');
                    if (statusMessage) {
                        statusMessage.style.display = 'none';
                    }
                }
                
                // อัปเดต progress เมื่อได้รับข้อมูลสุดท้าย
                if (data.ocrData && data.ocrData.length > 0) {
                    const successCount = data.successCount || data.ocrData.length;
                    
                    // ถ้าเสร็จแล้ว (successCount >= totalFiles) ให้ซ่อน progress container ทันที
                    if (successCount >= totalFiles) {
                        // หยุด countdown timer
                        if (countdownInterval) {
                            clearInterval(countdownInterval);
                            countdownInterval = null;
                        }
                        
                        // หยุด progress polling
                        if (window.ocrProgressPollInterval) {
                            clearInterval(window.ocrProgressPollInterval);
                            window.ocrProgressPollInterval = null;
                        }
                        
                        const progressContainer = document.getElementById('ocrProgressContainer');
                        if (progressContainer) {
                            progressContainer.style.display = 'none';
                        }
                        
                        const statusMessage = document.getElementById('ocrStatusMessage');
                        if (statusMessage) {
                            statusMessage.style.display = 'none';
                        }
                    }
                }
                
                if (data.success) {
                    // เก็บข้อมูล OCR จาก Step 2 เพื่อใช้ใน Step 5
                    step4OCRData = data.ocrData || [];
                    console.log('📊 Stored step4OCRData:', step4OCRData.length, 'items');
                    console.log('📊 First OCR item:', step4OCRData[0]);
                    
                    step.classList.remove('active');
                    step.classList.add('completed');
                    status.textContent = 'รัน OCR สำเร็จ';
                    status.className = 'step-status success';
                    
                    let html = `<div style="margin-bottom: 15px;">`;
                    html += `<strong>✅ รัน OCR สำเร็จ:</strong><br>`;
                    html += `<div style="margin-top: 10px; color: #10b981;">📁 โฟลเดอร์ VAT: ${data.vatFolder || 'N/A'}</div>`;
                    html += `<div style="margin-top: 10px; color: #cbd5e1; font-size: 0.9em;">`;
                    html += `📄 จำนวนไฟล์ PDF ทั้งหมด: ${data.totalPDFFiles || data.totalFiles || 0} ไฟล์<br>`;
                    if (data.estimatedTime) {
                        html += `⏱️ เวลาที่ใช้: ${data.estimatedTime}<br>`;
                    }
                    html += `✅ ประมวลผลสำเร็จ: ${data.successCount || 0} ไฟล์<br>`;
                    html += `❌ ประมวลผลไม่สำเร็จ: ${data.failedCount || 0} ไฟล์<br>`;
                    if (data.cacheHits !== undefined && data.cacheMisses !== undefined) {
                        const cacheHitRate = data.cacheHits + data.cacheMisses > 0 
                            ? ((data.cacheHits / (data.cacheHits + data.cacheMisses)) * 100).toFixed(1) 
                            : 0;
                        html += `<div style="margin-top: 8px; padding: 8px; background: #0f172a; border-radius: 5px; border-left: 3px solid #60a5fa;">`;
                        html += `💾 Cache Statistics:<br>`;
                        html += `   ✅ ใช้ Cache: ${data.cacheHits} ไฟล์<br>`;
                        html += `   🔄 เรียก OCR: ${data.cacheMisses} ไฟล์<br>`;
                        html += `   📊 Cache Hit Rate: ${cacheHitRate}%`;
                        html += `</div>`;
                    }
                    html += `</div>`;
                    
                    // แสดงข้อมูล OCR ที่ได้ (แสดงตัวอย่างบางส่วน)
                    if (data.ocrData && data.ocrData.length > 0) {
                        html += `<div style="margin-top: 15px; padding: 15px; background: #0f172a; border-radius: 5px; max-height: 400px; overflow-y: auto;">`;
                        html += `<div style="color: #60a5fa; font-weight: 600; margin-bottom: 10px;">📋 ข้อมูล OCR ที่ได้ (แสดง ${Math.min(5, data.ocrData.length)} ไฟล์แรก):</div>`;
                        
                        data.ocrData.slice(0, 5).forEach((item, index) => {
                            if (item.success) {
                                html += `<div style="margin-bottom: 15px; padding: 10px; background: #1e293b; border-radius: 5px; border-left: 3px solid #10b981;">`;
                                html += `<div style="color: #10b981; font-weight: 600;">📄 ${item.filename}</div>`;
                                
                                // แสดงรายการสินค้า
                                if (item.items && Array.isArray(item.items) && item.items.length > 0) {
                                    html += `<div style="margin-top: 8px; padding: 8px; background: #0f172a; border-radius: 3px;">`;
                                    html += `<div style="color: #60a5fa; font-size: 0.85em; margin-bottom: 5px;">📦 รายการสินค้า:</div>`;
                                    item.items.forEach((product, idx) => {
                                        const productName = product['รายการ'] || product['description'] || product['รายการสินค้า'] || '-';
                                        const productAmount = product['จำนวนเงิน'] || product['amount'] || '-';
                                        html += `<div style="color: #94a3b8; font-size: 0.8em; margin-left: 10px;">${idx + 1}. ${productName} - ${productAmount}</div>`;
                                    });
                                    html += `</div>`;
                                }
                                html += `<div style="margin-top: 8px; color: #cbd5e1; font-size: 0.9em;">`;
                                if (item.reference_number) html += `🔖 เลขที่เอกสารอ้างอิง: ${item.reference_number}<br>`;
                                if (item.company_name) html += `🏢 ชื่อบริษัท: ${item.company_name}<br>`;
                                if (item.tax_id) html += `🆔 เลขประจำตัวผู้เสียภาษี: ${item.tax_id}<br>`;
                                if (item.document_number) html += `📋 เลขที่เอกสาร: ${item.document_number}<br>`;
                                if (item.date) html += `📅 วันที่: ${item.date}<br>`;
                                if (item.total_amount) html += `💰 ยอดรวม: ${item.total_amount.toLocaleString('th-TH', {minimumFractionDigits: 2, maximumFractionDigits: 2})} บาท<br>`;
                                
                                // แสดงรายการสินค้า
                                if (item.items && Array.isArray(item.items) && item.items.length > 0) {
                                    html += `<div style="margin-top: 8px; padding: 8px; background: #0f172a; border-radius: 3px;">`;
                                    html += `<div style="color: #60a5fa; font-size: 0.85em; margin-bottom: 5px;">📦 รายการสินค้า:</div>`;
                                    item.items.forEach((product, idx) => {
                                        const productName = product['รายการ'] || product['description'] || product['รายการสินค้า'] || '-';
                                        const productAmount = product['จำนวนเงิน'] || product['amount'] || '-';
                                        html += `<div style="color: #94a3b8; font-size: 0.8em; margin-left: 10px;">${idx + 1}. ${productName} - ${productAmount}</div>`;
                                    });
                                    html += `</div>`;
                                }
                                
                                html += `</div>`;
                                html += `</div>`;
                            } else {
                                html += `<div style="margin-bottom: 10px; padding: 10px; background: #1e293b; border-radius: 5px; border-left: 3px solid #ef4444;">`;
                                html += `<div style="color: #ef4444;">❌ ${item.filename}</div>`;
                                html += `<div style="color: #94a3b8; font-size: 0.85em; margin-top: 5px;">${item.error || 'เกิดข้อผิดพลาด'}</div>`;
                                html += `</div>`;
                            }
                        });
                        
                        if (data.ocrData.length > 5) {
                            html += `<div style="color: #94a3b8; font-size: 0.85em; margin-top: 10px;">... และอีก ${data.ocrData.length - 5} ไฟล์</div>`;
                        }
                        
                        html += `</div>`;
                    }
                    
                    html += `</div>`;
                    details.innerHTML = html;
                    
                    // Continue to step 5
                    await checkStep5(taxMonth, company);
                } else {
                    step.classList.remove('active');
                    step.classList.add('error');
                    status.textContent = 'เกิดข้อผิดพลาด';
                    status.className = 'step-status error';
                    details.innerHTML = `❌ เกิดข้อผิดพลาด: ${data.error || 'Unknown error'}`;
                }
            } catch (error) {
                // หยุด countdown timer เมื่อเกิด error
                if (countdownInterval) {
                    clearInterval(countdownInterval);
                    countdownInterval = null;
                }
                
                step.classList.remove('active');
                step.classList.add('error');
                status.textContent = 'เกิดข้อผิดพลาด';
                status.className = 'step-status error';
                details.innerHTML = `❌ เกิดข้อผิดพลาด: ${error.message}`;
            }
        }
        
        // ปิด modal เมื่อคลิกที่ overlay
        document.addEventListener('DOMContentLoaded', function() {
            const modal = document.getElementById('ocrConfirmModal');
            if (modal) {
                modal.addEventListener('click', function(e) {
                    if (e.target === modal) {
                        // เรียก closeOCRConfirmModal() ซึ่งจะรีเซ็ตสถานะ Step 2 ให้อัตโนมัติ
                        closeOCRConfirmModal();
                    }
                });
            }
        });
        
        async function runOCRForStep4(taxMonth, company) {
            // ใช้ companyValue.value โดยตรงเพื่อให้แน่ใจว่าได้ค่า path ที่ถูกต้อง
            const actualCompany = document.getElementById('companyValue')?.value || document.getElementById('companySelect')?.value || company;
            console.log('🚀 runOCRForStep4 called with:', { taxMonth, company, actualCompany });
            
            const step = document.getElementById('step4');
            const status = document.getElementById('step4Status');
            const details = document.getElementById('step4Details');
            
            if (!step || !status || !details) {
                console.error('❌ Step 4 elements not found!');
                alert('ไม่พบ elements ของ Step 4 กรุณารีเฟรชหน้าเว็บ');
                return;
            }
            
            // เก็บข้อมูล Step 4 สำหรับใช้เมื่อกดยกเลิก
            step4Data = {
                taxMonth: taxMonth,
                company: actualCompany
            };
            
            // ขั้นแรก: ตรวจสอบจำนวนไฟล์ PDF และคำนวณเวลา
            step.classList.add('active');
            status.textContent = 'กำลังตรวจสอบไฟล์...';
            status.className = 'step-status checking';
            details.innerHTML = '⏳ กำลังตรวจสอบไฟล์ PDF และคำนวณเวลา...';
            
            try {
                console.log('📤 Sending check request:', { taxMonth, company: actualCompany, checkOnly: true });
                
                // ตรวจสอบจำนวนไฟล์ PDF และคำนวณเวลา
                const checkResponse = await fetch('/api/auditcheck/run-ocr', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        taxMonth: taxMonth,
                        company: actualCompany,  // ใช้ actualCompany แทน company
                        checkOnly: true,  // เพิ่ม flag เพื่อตรวจสอบเท่านั้น
                        include_subfolders: true  // อ่านไฟล์ PDF จากโฟลเดอร์ย่อยด้วย
                    })
                });
                
                console.log('📥 Check response status:', checkResponse.status);
                
                if (!checkResponse.ok) {
                    const errorText = await checkResponse.text();
                    console.error('❌ Check response error:', errorText);
                    throw new Error(`HTTP ${checkResponse.status}: ${errorText}`);
                }
                
                const checkData = await checkResponse.json();
                
                console.log('📊 Check PDF Files Response:', checkData);
                
                if (!checkData.success) {
                    step.classList.remove('active');
                    step.classList.add('error');
                    status.textContent = 'เกิดข้อผิดพลาด';
                    status.className = 'step-status error';
                    details.innerHTML = `❌ เกิดข้อผิดพลาด: ${checkData.error || 'Unknown error'}`;
                    return;
                }
                
                // แสดงข้อมูลจำนวนไฟล์และเวลาที่คาดว่าจะใช้
                const totalFiles = checkData.totalPDFFiles || checkData.totalFiles || 0;
                const estimatedTime = checkData.estimatedTime || '';
                
                console.log('📊 Total Files:', totalFiles, 'Estimated Time:', estimatedTime);
                
                // ดึงชื่อบริษัทจาก input field
                const companyName = document.getElementById('companySelect').value || company || '-';
                
                console.log('📊 Company Name:', companyName, 'Tax Month:', taxMonth);
                
                // แสดง modal/popup แทน confirm dialog
                console.log('📊 Showing OCR Confirm Modal...');
                // ใช้ companyValue.value โดยตรงเพื่อให้แน่ใจว่าได้ค่า path ที่ถูกต้อง
                const actualCompanyForModal = document.getElementById('companyValue')?.value || document.getElementById('companySelect')?.value || company;
                console.log('📊 Using actualCompanyForModal:', actualCompanyForModal);
                const subfolders = checkData.subfolders || [];
                showOCRConfirmModal(taxMonth, companyName, totalFiles, estimatedTime, taxMonth, actualCompanyForModal, subfolders);
                
                // หยุดการทำงานที่นี่ รอให้ผู้ใช้ยืนยันใน modal
                return;
            } catch (error) {
                step.classList.remove('active');
                step.classList.add('error');
                status.textContent = 'เกิดข้อผิดพลาด';
                status.className = 'step-status error';
                details.innerHTML = `❌ เกิดข้อผิดพลาด: ${error.message}`;
            }
        }
        
        function uploadExcelForStep4(taxMonth, company) {
            // ใช้ companyValue.value โดยตรงเพื่อให้แน่ใจว่าได้ค่า path ที่ถูกต้อง
            const actualCompany = document.getElementById('companyValue')?.value || document.getElementById('companySelect')?.value || company;
            console.log('📤 uploadExcelForStep4 called with:', { taxMonth, company, actualCompany });
            
            // สร้าง input element สำหรับเลือกไฟล์
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.xlsx,.xls';
            input.style.display = 'none';
            
            input.onchange = async (event) => {
                const file = event.target.files[0];
                if (!file) {
                    return;
                }
                
                const step = document.getElementById('step4');
                const status = document.getElementById('step4Status');
                const details = document.getElementById('step4Details');
                
                step.classList.add('active');
                status.textContent = 'กำลังอัปโหลด...';
                status.className = 'step-status checking';
                details.innerHTML = `⏳ กำลังอัปโหลดไฟล์: ${file.name}...`;
                
                try {
                    const formData = new FormData();
                    formData.append('file', file);
                    formData.append('taxMonth', taxMonth);
                    formData.append('company', actualCompany);  // ใช้ actualCompany แทน company
                    
                    const response = await fetch('/api/auditcheck/upload-excel', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        step.classList.remove('active');
                        step.classList.add('completed');
                        status.textContent = 'อัปโหลดสำเร็จ';
                        status.className = 'step-status success';
                        
                        let html = `<div style="margin-bottom: 15px;">`;
                        html += `<strong>✅ อัปโหลดไฟล์ Excel สำเร็จ:</strong><br>`;
                        html += `<div style="margin-top: 10px; color: #10b981;">📊 ${data.excelPath || file.name}</div>`;
                        html += `</div>`;
                        details.innerHTML = html;
                        
                        // Continue to step 5
                        await checkStep5(taxMonth, company);
                    } else {
                        step.classList.remove('active');
                        step.classList.add('error');
                        status.textContent = 'เกิดข้อผิดพลาด';
                        status.className = 'step-status error';
                        details.innerHTML = `❌ เกิดข้อผิดพลาด: ${data.error || 'Unknown error'}`;
                    }
                } catch (error) {
                    step.classList.remove('active');
                    step.classList.add('error');
                    status.textContent = 'เกิดข้อผิดพลาด';
                    status.className = 'step-status error';
                    details.textContent = '❌ เกิดข้อผิดพลาด: ' + error.message;
                } finally {
                    document.body.removeChild(input);
                }
            };
            
            document.body.appendChild(input);
            input.click();
        }
