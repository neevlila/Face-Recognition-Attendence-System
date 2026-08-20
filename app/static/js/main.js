/**
 * FaceAttend - Main UI & Global Utilities
 */

document.addEventListener('DOMContentLoaded', () => {
    initToasts();
    initMobileNav();
    initCustomSelects();
    initThemeToggle();
    initDateRangeConstraints();
});

// Date Range Constraints (Prevents To Date from being earlier than From Date)
function initDateRangeConstraints() {
    const startInputs = document.querySelectorAll('.date-range-start, input[name="start_date"]');
    const endInputs = document.querySelectorAll('.date-range-end, input[name="end_date"]');

    startInputs.forEach((startInput, idx) => {
        const endInput = endInputs[idx] || document.querySelector('.date-range-end, input[name="end_date"]');
        if (!startInput || !endInput) return;

        function syncDates() {
            if (startInput.value) {
                // To Date can only be the same day or future days after From Date
                endInput.min = startInput.value;

                // If To Date is currently earlier than From Date, auto-adjust to From Date
                if (endInput.value && endInput.value < startInput.value) {
                    endInput.value = startInput.value;
                }
            }
        }

        // Initialize on load
        syncDates();

        // Sync on changes
        startInput.addEventListener('change', syncDates);
        startInput.addEventListener('input', syncDates);
    });
}


// Theme Switcher Controller (Light / Dark Mode)
function initThemeToggle() {
    const toggleBtn = document.getElementById('theme-toggle-btn');
    const labelText = document.getElementById('theme-label-text');
    
    // Get initial theme
    const currentTheme = localStorage.getItem('faceattend_theme') || 'dark';
    applyTheme(currentTheme, false);

    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            const activeTheme = document.documentElement.getAttribute('data-theme') || 'dark';
            const nextTheme = activeTheme === 'dark' ? 'light' : 'dark';
            applyTheme(nextTheme, true);
        });
    }

    function applyTheme(theme, notify = false) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('faceattend_theme', theme);

        if (labelText) {
            labelText.textContent = theme === 'light' ? 'Light Mode' : 'Dark Mode';
        }

        // Dispatch custom event for charts or dynamic components
        window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme } }));

        if (notify) {
            showToast(`Switched to ${theme === 'light' ? 'Light ☀️' : 'Dark 🌙'} Mode`, 'info', 1800);
        }
    }
}



// Custom Select Component Initializer
function initCustomSelects() {
    const selects = document.querySelectorAll('select.form-select');
    
    selects.forEach(select => {
        // Prevent double initialization
        if (select.closest('.custom-select-wrapper')) return;

        const wrapper = document.createElement('div');
        wrapper.className = 'custom-select-wrapper';
        
        // Find selected or first option
        const selectedOption = select.options[select.selectedIndex] || select.options[0];
        const selectedText = selectedOption ? selectedOption.text : 'Select...';
        const isPlaceholder = selectedOption && selectedOption.value === '';

        // Create Trigger
        const trigger = document.createElement('div');
        trigger.className = 'custom-select-trigger';
        trigger.innerHTML = `
            <span class="selected-text ${isPlaceholder ? 'placeholder' : ''}">${selectedText}</span>
            <svg class="chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
        `;

        // Create Options Container
        const optionsList = document.createElement('div');
        optionsList.className = 'custom-select-options';

        Array.from(select.options).forEach((opt, idx) => {
            const customOpt = document.createElement('div');
            customOpt.className = 'custom-option' + (idx === select.selectedIndex ? ' selected' : '');
            customOpt.dataset.value = opt.value;
            customOpt.textContent = opt.text;

            customOpt.addEventListener('click', (e) => {
                e.stopPropagation();
                
                // Update select element value
                select.selectedIndex = idx;
                select.value = opt.value;

                // Update UI text
                const textSpan = trigger.querySelector('.selected-text');
                textSpan.textContent = opt.text;
                if (opt.value === '') {
                    textSpan.classList.add('placeholder');
                } else {
                    textSpan.classList.remove('placeholder');
                }

                // Update selected classes
                optionsList.querySelectorAll('.custom-option').forEach(o => o.classList.remove('selected'));
                customOpt.classList.add('selected');

                // Close dropdown
                wrapper.classList.remove('open');

                // Dispatch native change event
                select.dispatchEvent(new Event('change', { bubbles: true }));
            });

            optionsList.appendChild(customOpt);
        });

        // Insert wrapper into DOM
        select.parentNode.insertBefore(wrapper, select);
        wrapper.appendChild(select);
        wrapper.appendChild(trigger);
        wrapper.appendChild(optionsList);

        // Toggle Open/Close on Trigger click
        trigger.addEventListener('click', (e) => {
            e.stopPropagation();
            
            const isOpen = wrapper.classList.contains('open');

            // Close all other open custom selects
            document.querySelectorAll('.custom-select-wrapper.open').forEach(w => {
                if (w !== wrapper) {
                    w.classList.remove('open');
                    w.classList.remove('open-upward');
                }
            });

            if (!isOpen) {
                // Check available space below vs above
                const rect = trigger.getBoundingClientRect();
                const spaceBelow = window.innerHeight - rect.bottom;
                const spaceAbove = rect.top;

                if (spaceBelow < 260 && spaceAbove > spaceBelow) {
                    wrapper.classList.add('open-upward');
                } else {
                    wrapper.classList.remove('open-upward');
                }

                wrapper.classList.add('open');

                // Scroll selected option into visible area
                const sel = optionsList.querySelector('.custom-option.selected');
                if (sel) {
                    sel.scrollIntoView({ block: 'nearest' });
                }
            } else {
                wrapper.classList.remove('open');
                wrapper.classList.remove('open-upward');
            }
        });

    });

    // Close when clicking anywhere outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.custom-select-wrapper')) {
            document.querySelectorAll('.custom-select-wrapper.open').forEach(w => {
                w.classList.remove('open');
            });
        }
    });

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.custom-select-wrapper.open').forEach(w => {
                w.classList.remove('open');
            });
        }
    });
}


// Toast Notification Manager
function showToast(message, type = 'info', duration = 4000) {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let icon = '🔔';
    if (type === 'success') icon = '✓';
    else if (type === 'danger' || type === 'error') icon = '✕';
    else if (type === 'warning') icon = '⚠';

    toast.innerHTML = `
        <span style="font-size: 1.1rem;">${icon}</span>
        <span style="flex: 1; font-size: 0.875rem;">${message}</span>
        <button onclick="this.parentElement.remove()" style="background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 1rem;">×</button>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(20px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

function initToasts() {
    // Check for flash messages rendered in data attributes
    const flashElements = document.querySelectorAll('.flash-message-data');
    flashElements.forEach(el => {
        const msg = el.getAttribute('data-message');
        const cat = el.getAttribute('data-category') || 'info';
        if (msg) showToast(msg, cat);
    });
}

function initMobileNav() {
    const toggleBtn = document.getElementById('sidebar-toggle');
    const sidebar = document.querySelector('.app-sidebar');
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
    }
}

// Modal Helper
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('show');
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('show');
    }
}

// Global Training Trigger
async function triggerGlobalModelTraining(btnElement) {
    if (btnElement) {
        btnElement.disabled = true;
        btnElement.innerHTML = `<span class="spinner"></span> Training Model...`;
    }
    
    showToast('Starting face recognition model training...', 'info');

    try {
        const response = await fetch('/api/train', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            showToast(`Training complete! Enrolled ${data.students_count} students (${data.samples_count} samples).`, 'success');
            setTimeout(() => window.location.reload(), 1500);
        } else {
            showToast(`Training failed: ${data.message}`, 'danger');
            if (btnElement) {
                btnElement.disabled = false;
                btnElement.innerHTML = `Train Recognition Model`;
            }
        }
    } catch (err) {
        showToast(`Network error during training: ${err.message}`, 'danger');
        if (btnElement) {
            btnElement.disabled = false;
            btnElement.innerHTML = `Train Recognition Model`;
        }
    }
}
