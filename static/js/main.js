/**
 * Face Recognition Attendance System — Main JavaScript
 * Handles camera, form validation, AJAX requests, and UI interactions.
 */

// ─── Camera Manager ─────────────────────────────────────────────
class CameraManager {
    constructor(videoElement, canvasElement) {
        this.video = videoElement;
        this.canvas = canvasElement;
        this.ctx = canvasElement ? canvasElement.getContext('2d') : null;
        this.stream = null;
        this.isActive = false;
    }

    async start() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' }
            });
            this.video.srcObject = this.stream;
            await this.video.play();
            this.isActive = true;
            return true;
        } catch (err) {
            console.error('Camera error:', err);
            showToast('Camera access denied. Please allow camera permissions.', 'danger');
            return false;
        }
    }

    capture() {
        if (!this.isActive || !this.canvas) return null;
        this.canvas.width = this.video.videoWidth;
        this.canvas.height = this.video.videoHeight;
        this.ctx.drawImage(this.video, 0, 0);
        const flash = document.querySelector('.camera-flash');
        if (flash) {
            flash.classList.add('active');
            setTimeout(() => flash.classList.remove('active'), 150);
        }
        return this.canvas.toDataURL('image/jpeg', 0.9);
    }

    stop() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
            this.isActive = false;
        }
    }
}

// Stop camera on page unload
window.addEventListener('beforeunload', () => {
    if (window.camera) window.camera.stop();
});


// ═══════════════════════════════════════════════════════════════
//  FORM VALIDATION
// ═══════════════════════════════════════════════════════════════

// ─── Name: Only alphabets ───────────────────────────────────────
function validateName(input) {
    const errorEl = document.getElementById('name-error');
    const value = input.value.trim();

    if (value && !/^[a-zA-Z\s]+$/.test(value)) {
        input.classList.add('is-invalid');
        if (errorEl) {
            errorEl.textContent = 'Enter only alphabets (e.g., Ram)';
            errorEl.classList.add('visible');
        }
        return false;
    } else {
        input.classList.remove('is-invalid');
        if (errorEl) errorEl.classList.remove('visible');
        return true;
    }
}

// ─── Registration Number: Strict 11-digit format ────────────────
let regValidationTimeout = null;

function validateRegNumber(input) {
    const errorEl = document.getElementById('reg-error');
    const hintEl = document.getElementById('reg-hint');
    const value = input.value.trim();

    // Block non-numeric input
    if (value && !/^\d*$/.test(value)) {
        input.classList.add('is-invalid');
        if (errorEl) {
            errorEl.textContent = 'Enter only numeric value (e.g., 21103135012)';
            errorEl.classList.add('visible');
        }
        return false;
    }

    input.classList.remove('is-invalid');
    if (errorEl) errorEl.classList.remove('visible');

    // Real-time server validation with debounce
    if (regValidationTimeout) clearTimeout(regValidationTimeout);

    if (value.length >= 2) {
        regValidationTimeout = setTimeout(() => {
            validateRegNumberServer(value);
        }, 300);
    } else if (hintEl) {
        hintEl.innerHTML = '<i class="bi bi-info-circle"></i> Format: <strong>YY</strong> + <strong style="color:var(--accent-primary)">BranchCode</strong> + <strong>135</strong> + <strong>RollNo</strong> = 11 digits';
        hintEl.className = 'reg-hint';
    }

    return true;
}

async function validateRegNumberServer(regNumber) {
    const errorEl = document.getElementById('reg-error');
    const hintEl = document.getElementById('reg-hint');
    const branchSelect = document.getElementById('reg-branch');

    try {
        const response = await fetch('/api/validate_reg', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reg_number: regNumber })
        });
        const data = await response.json();

        if (hintEl) {
            if (data.valid) {
                hintEl.innerHTML = `<span style="color: var(--success);"><i class="bi bi-check-circle-fill"></i> ${data.message} Branch: <strong>${data.branch}</strong></span>`;
                hintEl.className = 'reg-hint valid';

                // Auto-select branch
                if (branchSelect && data.branch) {
                    branchSelect.value = data.branch;
                    branchSelect.style.borderColor = 'var(--success)';
                    setTimeout(() => { branchSelect.style.borderColor = ''; }, 2000);
                }
            } else if (data.already_registered) {
                hintEl.innerHTML = `<span style="color: var(--danger);"><i class="bi bi-exclamation-triangle-fill"></i> ${data.message}</span>`;
                hintEl.className = 'reg-hint error';

                // Auto-select branch if detected
                if (branchSelect && data.branch) {
                    branchSelect.value = data.branch;
                }

                const input = document.getElementById('reg-number');
                if (input) input.classList.add('is-invalid');
            } else if (data.message) {
                // Could be partial hint or error
                if (data.message.includes('Invalid') || data.message.includes('Too many')) {
                    hintEl.innerHTML = `<span style="color: var(--danger);"><i class="bi bi-x-circle"></i> ${data.message}</span>`;
                    hintEl.className = 'reg-hint error';
                    const input = document.getElementById('reg-number');
                    if (input) input.classList.add('is-invalid');
                } else {
                    hintEl.innerHTML = `<span style="color: var(--info);"><i class="bi bi-info-circle"></i> ${data.message}</span>`;
                    hintEl.className = 'reg-hint info';

                    // Auto-select branch if detected mid-typing
                    if (branchSelect && data.branch) {
                        branchSelect.value = data.branch;
                    }
                }
            }
        }
    } catch (err) {
        // Silently fail
    }
}

// ─── Phone: Indian format +91, starts with 6/7/8/9 ─────────────
function validatePhone(input, isBlur = false) {
    const errorEl = document.getElementById('phone-error');
    const value = input.value.trim();

    // Block non-numeric
    if (value && !/^\d*$/.test(value)) {
        input.classList.add('is-invalid');
        if (errorEl) {
            errorEl.textContent = 'Enter only numeric digits';
            errorEl.classList.add('visible');
        }
        return false;
    }

    // Check first digit (must be 6, 7, 8, or 9)
    if (value.length >= 1 && !['6', '7', '8', '9'].includes(value[0])) {
        input.classList.add('is-invalid');
        if (errorEl) {
            errorEl.textContent = 'Indian phone numbers must start with 6, 7, 8, or 9';
            errorEl.classList.add('visible');
        }
        return false;
    }

    // On blur, check exact length
    if (isBlur && value && value.length !== 10) {
        input.classList.add('is-invalid');
        if (errorEl) {
            errorEl.textContent = `Phone number must be exactly 10 digits (you entered ${value.length})`;
            errorEl.classList.add('visible');
        }
        return false;
    }

    input.classList.remove('is-invalid');
    if (errorEl) errorEl.classList.remove('visible');
    return true;
}

// ─── DOB: Must be 18+ years old ─────────────────────────────────
function validateDOB(input) {
    const errorEl = document.getElementById('dob-error');
    const value = input.value;

    if (!value) {
        if (errorEl) errorEl.classList.remove('visible');
        return true;
    }

    const dob = new Date(value);
    const today = new Date();
    let age = today.getFullYear() - dob.getFullYear();
    const monthDiff = today.getMonth() - dob.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < dob.getDate())) {
        age--;
    }

    if (dob > today) {
        input.classList.add('is-invalid');
        if (errorEl) {
            errorEl.textContent = 'Date of birth cannot be in the future!';
            errorEl.classList.add('visible');
        }
        return false;
    }

    if (age < 18) {
        input.classList.add('is-invalid');
        if (errorEl) {
            errorEl.textContent = `You must be at least 18 years old to register. Your age: ${age} years.`;
            errorEl.classList.add('visible');
        }
        return false;
    }

    if (age > 100) {
        input.classList.add('is-invalid');
        if (errorEl) {
            errorEl.textContent = 'Invalid date of birth.';
            errorEl.classList.add('visible');
        }
        return false;
    }

    input.classList.remove('is-invalid');
    if (errorEl) errorEl.classList.remove('visible');
    return true;
}


// ═══════════════════════════════════════════════════════════════
//  TOAST / LOADING
// ═══════════════════════════════════════════════════════════════

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const icons = { success: '✓', danger: '✗', warning: '⚠', info: 'ℹ' };
    const toast = document.createElement('div');
    toast.className = `alert-custom alert-${type}`;
    toast.innerHTML = `<span>${icons[type] || 'ℹ'}</span> ${message}`;
    container.innerHTML = '';
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-10px)';
        toast.style.transition = '0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 6000);
}

function showLoading(message = 'Processing...') {
    let overlay = document.getElementById('loading-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'loading-overlay';
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `<div class="spinner-custom"></div><div class="loading-text">${message}</div>`;
        document.body.appendChild(overlay);
    } else {
        overlay.querySelector('.loading-text').textContent = message;
        overlay.style.display = 'flex';
    }
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.style.display = 'none';
}


// ═══════════════════════════════════════════════════════════════
//  REGISTRATION HANDLER
// ═══════════════════════════════════════════════════════════════

async function handleRegistration(event) {
    event.preventDefault();

    const name = document.getElementById('reg-name').value.trim();
    const regNumber = document.getElementById('reg-number').value.trim();
    const dob = document.getElementById('reg-dob').value.trim();
    const phone = document.getElementById('reg-phone').value.trim();
    const branch = document.getElementById('reg-branch').value;

    // Validate all fields
    if (!name || !regNumber || !dob || !phone || !branch) {
        showToast('Please fill in all fields!', 'warning');
        return;
    }

    if (!/^[a-zA-Z\s]+$/.test(name)) {
        showToast('Enter only alphabets in Name (e.g., Ram)', 'danger');
        return;
    }

    if (!/^\d{11}$/.test(regNumber)) {
        showToast('Registration number must be exactly 11 digits (e.g., 21103135012)', 'danger');
        return;
    }

    // DOB age check
    const dobDate = new Date(dob);
    const today = new Date();
    let age = today.getFullYear() - dobDate.getFullYear();
    const md = today.getMonth() - dobDate.getMonth();
    if (md < 0 || (md === 0 && today.getDate() < dobDate.getDate())) age--;
    if (age < 18) {
        showToast(`You must be at least 18 years old. Your age: ${age} years.`, 'danger');
        return;
    }

    // Phone check
    if (!/^\d{10}$/.test(phone) || !['6','7','8','9'].includes(phone[0])) {
        showToast('Enter a valid 10-digit Indian phone number (starting with 6/7/8/9)', 'danger');
        return;
    }

    // Face check
    const faceImage = window.capturedFaceImage;
    if (!faceImage) {
        showToast('Please capture your face before registering!', 'warning');
        return;
    }

    showLoading('Registering student and processing face data...');

    try {
        const response = await fetch('/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name, reg_number: regNumber, dob, phone, branch,
                face_image: faceImage
            })
        });

        const data = await response.json();
        hideLoading();

        if (data.success) {
            showToast(data.message, 'success');
            document.getElementById('registration-form').style.display = 'none';
            document.getElementById('registration-success').style.display = 'block';
            if (window.camera) window.camera.stop();
        } else {
            if (data.already_registered) {
                // Show special "already registered" UI
                showAlreadyRegisteredMessage(data.message);
            } else {
                showToast(data.message, 'danger');
            }
        }
    } catch (err) {
        hideLoading();
        showToast('Network error. Please try again.', 'danger');
    }
}

function showAlreadyRegisteredMessage(message) {
    document.getElementById('registration-form').style.display = 'none';
    const successDiv = document.getElementById('registration-success');
    successDiv.style.display = 'block';
    successDiv.innerHTML = `
        <div class="result-card">
            <div style="width:80px;height:80px;margin:0 auto 1.5rem;background:linear-gradient(135deg,#f59e0b,#d97706);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:2.5rem;color:white;animation:popIn 0.5s cubic-bezier(0.175,0.885,0.32,1.275);">
                <i class="bi bi-person-check"></i>
            </div>
            <h3>Already Registered!</h3>
            <p style="color: var(--text-secondary); margin-bottom: 2rem;">${message}</p>
            <div style="display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;">
                <a href="/student/login" class="btn-primary-custom">
                    <span><i class="bi bi-box-arrow-in-right"></i> Go to Login</span>
                </a>
                <a href="/register" class="btn-secondary-custom">
                    <i class="bi bi-arrow-left"></i> Back
                </a>
            </div>
        </div>
    `;
    if (window.camera) window.camera.stop();
}


// ═══════════════════════════════════════════════════════════════
//  ATTENDANCE HANDLER
// ═══════════════════════════════════════════════════════════════

async function handleAttendance(faceImage) {
    showLoading('Verifying your face...');

    try {
        const response = await fetch('/student/mark_attendance', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ face_image: faceImage })
        });

        const data = await response.json();
        hideLoading();

        if (data.success) {
            document.getElementById('attendance-camera').style.display = 'none';
            const resultDiv = document.getElementById('attendance-result');
            resultDiv.style.display = 'block';
            resultDiv.innerHTML = `
                <div class="result-card">
                    <div class="success-check">✓</div>
                    <h3>Attendance Marked!</h3>
                    <p style="color: var(--text-secondary);">${data.message}</p>
                    <div class="result-info">
                        <div class="result-info-item">
                            <div class="label">Student Name</div>
                            <div class="value">${data.student_name}</div>
                        </div>
                        <div class="result-info-item">
                            <div class="label">Branch</div>
                            <div class="value">${data.branch}</div>
                        </div>
                        <div class="result-info-item">
                            <div class="label">Present Days</div>
                            <div class="value">${data.present_days} / ${data.working_days}</div>
                        </div>
                        <div class="result-info-item">
                            <div class="label">Confidence</div>
                            <div class="value">${data.confidence}%</div>
                        </div>
                    </div>
                </div>
            `;
            if (window.camera) window.camera.stop();
        } else {
            showToast(data.message, 'danger');
        }
    } catch (err) {
        hideLoading();
        showToast('Network error. Please try again.', 'danger');
    }
}


// ═══════════════════════════════════════════════════════════════
//  DELETE CONFIRMATION
// ═══════════════════════════════════════════════════════════════

function confirmDelete(studentId, studentName) {
    const modal = document.getElementById('deleteModal');
    if (modal) {
        document.getElementById('delete-student-name').textContent = studentName;
        document.getElementById('delete-form').action = `/admin/delete/${studentId}`;
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }
}


// ═══════════════════════════════════════════════════════════════
//  DOM READY
// ═══════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    // Name validation
    const nameInput = document.getElementById('reg-name');
    if (nameInput) nameInput.addEventListener('input', () => validateName(nameInput));

    // Registration number validation
    const regInput = document.getElementById('reg-number');
    if (regInput) {
        regInput.addEventListener('input', () => validateRegNumber(regInput));
        regInput.setAttribute('maxlength', '11');
    }

    // Phone validation
    const phoneInput = document.getElementById('reg-phone');
    if (phoneInput) {
        phoneInput.addEventListener('input', () => validatePhone(phoneInput, false));
        phoneInput.addEventListener('blur', () => validatePhone(phoneInput, true));
    }

    // DOB validation
    const dobInput = document.getElementById('reg-dob');
    if (dobInput) {
        dobInput.addEventListener('change', () => validateDOB(dobInput));
        dobInput.addEventListener('blur', () => validateDOB(dobInput));

        // Set max date to 18 years ago
        const maxDate = new Date();
        maxDate.setFullYear(maxDate.getFullYear() - 18);
        dobInput.setAttribute('max', maxDate.toISOString().split('T')[0]);
    }

    // Auto-dismiss flash messages
    const flashMessages = document.querySelectorAll('.alert-custom.flash-message');
    flashMessages.forEach(msg => {
        setTimeout(() => {
            msg.style.opacity = '0';
            msg.style.transform = 'translateY(-10px)';
            msg.style.transition = '0.3s ease';
            setTimeout(() => msg.remove(), 300);
        }, 5000);
    });
});
