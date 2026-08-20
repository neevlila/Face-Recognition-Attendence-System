/**
 * FaceAttend - 6-Shot Step-by-Step Face Capture & Dataset Studio
 */

let activeStudentId = null;
let currentTargetSlot = 1;

const POSE_INSTRUCTIONS = [
    { title: "Shot 1 of 6: Frontal Neutral", desc: "Look directly at the camera with a neutral expression" },
    { title: "Shot 2 of 6: Slight Right", desc: "Turn head slightly (~15°) to your RIGHT" },
    { title: "Shot 3 of 6: Slight Left", desc: "Turn head slightly (~15°) to your LEFT" },
    { title: "Shot 4 of 6: Natural Smile", desc: "Look straight at the camera with a natural SMILE" },
    { title: "Shot 5 of 6: Slight Upward", desc: "Tilt your head slightly UPWARDS (~10°)" },
    { title: "Shot 6 of 6: Slight Downward", desc: "Tilt your head slightly DOWNWARDS (~10°)" }
];

function startFaceCapture(studentId, slot = null) {
    activeStudentId = studentId;
    currentTargetSlot = slot ? parseInt(slot) : 1;
    openModal('captureModal');

    const feedImg = document.getElementById('capture-video-feed');
    if (feedImg) {
        feedImg.src = `/capture_feed/${studentId}?t=${Date.now()}`;
    }

    refreshCaptureStudio(studentId);
}

async function refreshCaptureStudio(studentId) {
    try {
        const res = await fetch(`/api/capture_status/${studentId}`);
        const data = await res.json();
        
        const count = data.count || 0;
        const target = data.target || 6;
        const samples = data.samples || [];

        // Auto-select next missing slot if not in explicit retake mode
        if (currentTargetSlot <= count && count < target) {
            currentTargetSlot = count + 1;
        } else if (count >= target && currentTargetSlot > target) {
            currentTargetSlot = target;
        }

        updateStudioUI(count, target, samples);
    } catch (e) {
        console.error('Error refreshing capture studio:', e);
    }
}

function updateStudioUI(count, target, samples) {
    const titleEl = document.getElementById('capture-pose-title');
    const descEl = document.getElementById('capture-pose-desc');
    const btnCapture = document.getElementById('btn-capture-shot');
    const btnRetrain = document.getElementById('btn-studio-train');
    const slotsContainer = document.getElementById('capture-slots-tray');
    const progressEl = document.getElementById('capture-progress-text');

    const pose = POSE_INSTRUCTIONS[currentTargetSlot - 1] || POSE_INSTRUCTIONS[0];

    if (titleEl) titleEl.innerText = pose.title;
    if (descEl) descEl.innerText = pose.desc;
    if (progressEl) progressEl.innerText = `${count} / ${target} Images`;

    if (btnCapture) {
        btnCapture.innerText = `📸 Capture Shot #${currentTargetSlot}`;
        btnCapture.disabled = false;
    }

    if (btnRetrain) {
        if (count >= target) {
            btnRetrain.disabled = false;
            btnRetrain.classList.remove('btn-secondary');
            btnRetrain.classList.add('btn-success');
            btnRetrain.innerText = '✓ Complete & Train Face Model';
        } else {
            btnRetrain.disabled = true;
            btnRetrain.classList.remove('btn-success');
            btnRetrain.classList.add('btn-secondary');
            btnRetrain.innerText = `Capture All 6 to Train (${count}/6)`;
        }
    }

    // Render 6 Visual Slots
    if (slotsContainer) {
        let html = '';
        for (let i = 1; i <= target; i++) {
            const formattedNum = String(i).padStart(3, '0');
            const matchingFile = samples.find(f => f.startsWith(formattedNum));
            const isSelected = i === currentTargetSlot;

            if (matchingFile) {
                const imgUrl = `/students/dataset_image/${activeStudentId}/${matchingFile}?t=${Date.now()}`;
                html += `
                    <div class="slot-card filled ${isSelected ? 'active-slot' : ''}" onclick="selectSlotForRetake(${i})">
                        <img src="${imgUrl}" alt="Slot ${i}" class="slot-thumb">
                        <div class="slot-badge">#${i} ✓</div>
                        <div class="slot-actions-overlay">
                            <span title="Retake Slot #${i}">🔄 Retake</span>
                        </div>
                    </div>
                `;
            } else {
                html += `
                    <div class="slot-card empty ${isSelected ? 'active-slot' : ''}" onclick="selectSlotForRetake(${i})">
                        <div class="slot-placeholder">
                            <span style="font-size: 1.2rem;">📷</span>
                            <span style="font-size: 0.7rem; font-weight: 600;">Slot #${i}</span>
                        </div>
                    </div>
                `;
            }
        }
        slotsContainer.innerHTML = html;
    }
}

function selectSlotForRetake(slotNum) {
    currentTargetSlot = slotNum;
    refreshCaptureStudio(activeStudentId);
    showToast(`Selected Slot #${slotNum} to capture/retake`, 'info', 1500);
}

async function captureManualShot() {
    if (!activeStudentId) return;

    const btn = document.getElementById('btn-capture-shot');
    if (btn) btn.disabled = true;

    // Shutter flash visual feedback
    const frameBox = document.querySelector('.video-frame-box');
    if (frameBox) {
        frameBox.style.filter = 'brightness(2.2)';
        setTimeout(() => { frameBox.style.filter = 'none'; }, 120);
    }

    try {
        const res = await fetch(`/api/capture_manual_sample/${activeStudentId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ slot: currentTargetSlot })
        });
        const result = await res.json();

        if (result.success) {
            showToast(`✓ Image #${currentTargetSlot} captured!`, 'success');
            
            // Advance to next slot if below 6
            if (currentTargetSlot < 6) {
                currentTargetSlot += 1;
            }
            
            await refreshCaptureStudio(activeStudentId);

            // If 6/6 reached
            if (result.count >= 6) {
                showToast('🎉 All 6 face samples captured! Click "Complete & Train Model" to activate.', 'success', 3500);
            }
        } else {
            showToast(result.message || 'Capture failed - ensure face is centered', 'warning');
        }
    } catch (e) {
        console.error('Error capturing snapshot:', e);
        showToast('Camera capture error. Try again.', 'danger');
    } finally {
        if (btn) btn.disabled = false;
    }
}

async function deleteSample(studentId, filename) {
    if (!confirm(`Are you sure you want to delete face sample ${filename}?`)) return;

    try {
        const res = await fetch(`/api/delete_sample_image/${studentId}/${filename}`, { method: 'POST' });
        const result = await res.json();
        if (result.success) {
            showToast(`Sample ${filename} deleted`, 'info');
            window.location.reload();
        } else {
            showToast('Failed to delete sample image', 'danger');
        }
    } catch (e) {
        console.error('Delete error:', e);
    }
}

async function resetCaptureSession(studentId) {
    if (!confirm('Are you sure you want to reset all 6 face samples for this student?')) return;
    try {
        await fetch(`/api/reset_capture/${studentId}`, { method: 'POST' });
        showToast('Dataset reset. Ready for 6 fresh shots.', 'info');
        currentTargetSlot = 1;
        refreshCaptureStudio(studentId);
    } catch (e) {
        showToast('Failed to reset dataset.', 'danger');
    }
}
