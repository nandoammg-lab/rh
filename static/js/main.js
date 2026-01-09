/**
 * RENOVO HR Management System - JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Tabs
    initTabs();

    // Initialize Modals
    initModals();

    // Initialize Search
    initTableSearch();

    // Auto-hide alerts after 5 seconds
    initAutoHideAlerts();
});

/**
 * Tabs functionality
 */
function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const tabId = this.dataset.tab;
            const tabContainer = this.closest('.tabs');

            // Remove active from all tabs
            tabContainer.querySelectorAll('.tab-btn').forEach(t => t.classList.remove('active'));
            tabContainer.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

            // Add active to clicked tab
            this.classList.add('active');
            tabContainer.querySelector(`#${tabId}`).classList.add('active');
        });
    });
}

/**
 * Modal functionality
 */
function initModals() {
    // Open modal buttons
    document.querySelectorAll('[data-modal]').forEach(btn => {
        btn.addEventListener('click', function() {
            const modalId = this.dataset.modal;
            openModal(modalId);
        });
    });

    // Close modal buttons
    document.querySelectorAll('.modal-close, [data-dismiss="modal"]').forEach(btn => {
        btn.addEventListener('click', function() {
            closeModal(this.closest('.modal-overlay'));
        });
    });

    // Close on overlay click
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', function(e) {
            if (e.target === this) {
                closeModal(this);
            }
        });
    });
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modal) {
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

/**
 * Table search functionality
 */
function initTableSearch() {
    const searchInputs = document.querySelectorAll('.table-search input');

    searchInputs.forEach(input => {
        input.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const table = this.closest('.table-container').querySelector('table');
            const rows = table.querySelectorAll('tbody tr');

            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });
    });
}

/**
 * Auto-hide alerts
 */
function initAutoHideAlerts() {
    const alerts = document.querySelectorAll('.messages .alert');

    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });
}

/**
 * Format CPF
 */
function formatCPF(cpf) {
    cpf = cpf.replace(/\D/g, '');
    return cpf.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
}

/**
 * Format CNPJ
 */
function formatCNPJ(cnpj) {
    cnpj = cnpj.replace(/\D/g, '');
    return cnpj.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
}

/**
 * Format Phone
 */
function formatPhone(phone) {
    phone = phone.replace(/\D/g, '');
    if (phone.length === 11) {
        return phone.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
    }
    return phone.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3');
}

/**
 * Format Date (DD/MM/YYYY)
 */
function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR');
}

/**
 * Format Currency (R$)
 */
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

/**
 * Confirm dialog
 */
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

/**
 * Photo preview on upload
 */
function previewPhoto(input, previewId) {
    const preview = document.getElementById(previewId);
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.src = e.target.result;
        };
        reader.readAsDataURL(input.files[0]);
    }
}

/**
 * Toggle inactive employees visibility
 */
function toggleInativos() {
    const btn = document.getElementById('btn-toggle-inativos');
    const rows = document.querySelectorAll('tbody tr.inactive');
    const isShowing = btn.dataset.showing === 'true';

    rows.forEach(row => {
        row.style.display = isShowing ? 'none' : '';
    });

    btn.dataset.showing = !isShowing;
    btn.textContent = isShowing ? 'Ver Inativos' : 'Ocultar Inativos';
    btn.classList.toggle('btn-warning', !isShowing);
    btn.classList.toggle('btn-outline', isShowing);
}
