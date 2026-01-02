// Main JavaScript for Sports Management System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize all popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            if (!alert.classList.contains('alert-permanent')) {
                var bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        });
    }, 5000);

    // Form validation
    var forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function (form) {
        form.addEventListener('submit', function (event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Confirmation dialogs for delete actions
    var deleteButtons = document.querySelectorAll('[data-confirm]');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            var message = this.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // Show/hide loading spinner on AJAX requests
    let spinnerTimeout;
    document.addEventListener('ajaxStart', function() {
        spinnerTimeout = setTimeout(function() {
            showLoadingSpinner();
        }, 300); // Only show spinner if request takes longer than 300ms
    });

    document.addEventListener('ajaxStop', function() {
        clearTimeout(spinnerTimeout);
        hideLoadingSpinner();
    });

    // Password strength indicator for registration
    var passwordInput = document.getElementById('password');
    if (passwordInput) {
        passwordInput.addEventListener('input', function() {
            var strength = checkPasswordStrength(this.value);
            updatePasswordStrengthIndicator(strength);
        });
    }

    // Match time conversion to local timezone
    var matchTimes = document.querySelectorAll('.match-time');
    matchTimes.forEach(function(element) {
        var utcTime = element.getAttribute('data-utc');
        if (utcTime) {
            var localTime = new Date(utcTime).toLocaleString();
            element.textContent = localTime;
        }
    });

    // Datepicker initialization
    if (typeof $.fn.datepicker !== 'undefined') {
        $('.date-picker').datepicker({
            format: 'yyyy-mm-dd',
            autoclose: true,
            todayHighlight: true
        });
    }

    // File upload preview
    document.querySelectorAll('input[type="file"]').forEach(function(input) {
        input.addEventListener('change', function() {
            var preview = document.getElementById(this.id + '_preview');
            if (!preview) return;
            
            var file = this.files[0];
            var reader = new FileReader();
            
            reader.onloadend = function() {
                preview.src = reader.result;
            };
            
            if (file) {
                reader.readAsDataURL(file);
            } else {
                preview.src = preview.getAttribute('data-default');
            }
        });
    });
});

// Password strength checker
function checkPasswordStrength(password) {
    var strength = 0;
    
    // Length check
    if (password.length >= 8) strength += 1;
    if (password.length >= 12) strength += 1;
    
    // Character variety checks
    if (password.match(/[a-z]/)) strength += 1;
    if (password.match(/[A-Z]/)) strength += 1;
    if (password.match(/[0-9]/)) strength += 1;
    if (password.match(/[^a-zA-Z0-9]/)) strength += 1;
    
    return strength;
}

// Update password strength indicator
function updatePasswordStrengthIndicator(strength) {
    var indicator = document.getElementById('password-strength');
    if (!indicator) return;
    
    var text, className;
    if (strength <= 2) {
        text = 'Weak';
        className = 'text-danger';
    } else if (strength <= 4) {
        text = 'Medium';
        className = 'text-warning';
    } else {
        text = 'Strong';
        className = 'text-success';
    }
    
    indicator.textContent = text;
    indicator.className = className;
}

// Show loading spinner
function showLoadingSpinner() {
    var spinner = document.createElement('div');
    spinner.className = 'spinner-overlay';
    spinner.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
    document.body.appendChild(spinner);
}

// Hide loading spinner
function hideLoadingSpinner() {
    var spinner = document.querySelector('.spinner-overlay');
    if (spinner) {
        spinner.remove();
    }
}

// Dynamic form field adding
function addFormField(button, templateId) {
    var template = document.getElementById(templateId);
    if (!template) return;
    
    var clone = template.content.cloneNode(true);
    var container = button.closest('.form-group').querySelector('.dynamic-fields');
    if (!container) return;
    
    container.appendChild(clone);
}

// Remove dynamic form field
function removeFormField(button) {
    var field = button.closest('.dynamic-field');
    if (field) {
        field.remove();
    }
}

// Chart initialization (if using Chart.js)
function initializeChart(canvasId, chartData) {
    var canvas = document.getElementById(canvasId);
    if (!canvas || typeof Chart === 'undefined') return;
    
    return new Chart(canvas, chartData);
}

// Table sorting
function sortTable(tableId, column, type = 'string') {
    var table = document.getElementById(tableId);
    if (!table) return;
    
    var tbody = table.tBodies[0];
    var rows = Array.from(tbody.rows);
    
    rows.sort((a, b) => {
        var aValue = a.cells[column].textContent.trim();
        var bValue = b.cells[column].textContent.trim();
        
        if (type === 'number') {
            return parseFloat(aValue) - parseFloat(bValue);
        } else if (type === 'date') {
            return new Date(aValue) - new Date(bValue);
        } else {
            return aValue.localeCompare(bValue);
        }
    });
    
    // Re-append sorted rows
    rows.forEach(row => tbody.appendChild(row));
    
    // Update sort indicators
    updateSortIndicators(table, column);
}

// Update table sort indicators
function updateSortIndicators(table, sortedColumn) {
    var headers = table.querySelectorAll('th');
    headers.forEach((header, index) => {
        if (index === sortedColumn) {
            header.classList.add('sorted');
            header.classList.toggle('sorted-asc');
        } else {
            header.classList.remove('sorted', 'sorted-asc');
        }
    });
}