// Main JavaScript for Cheque Management System

$(document).ready(function() {
    // Initialize tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    
    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        $('.alert:not(.alert-permanent)').fadeOut('slow');
    }, 5000);
    
    // Confirm delete actions
    $('.btn-delete, .btn-danger[data-bs-toggle="modal"]').click(function(e) {
        const message = $(this).data('confirm') || 'Êtes-vous sûr de vouloir supprimer cet élément ?';
        if (!$(this).data('bs-toggle')) {
            if (!confirm(message)) {
                e.preventDefault();
                return false;
            }
        }
    });
    
    // Form validation enhancements
    $('form').on('submit', function() {
        const submitBtn = $(this).find('button[type="submit"]');
        submitBtn.addClass('btn-loading').prop('disabled', true);
        
        // Re-enable button after 3 seconds to prevent permanent disable on validation errors
        setTimeout(function() {
            submitBtn.removeClass('btn-loading').prop('disabled', false);
        }, 3000);
    });
    
    // Format currency inputs
    $('input[step="0.01"]').on('input', function() {
        let value = $(this).val();
        // Remove any non-numeric characters except decimal point
        value = value.replace(/[^0-9.]/g, '');
        // Ensure only one decimal point
        const parts = value.split('.');
        if (parts.length > 2) {
            value = parts[0] + '.' + parts.slice(1).join('');
        }
        // Limit to 2 decimal places
        if (parts[1] && parts[1].length > 2) {
            value = parts[0] + '.' + parts[1].substring(0, 2);
        }
        $(this).val(value);
    });
    
    // Date input helpers
    $('.date-today').click(function() {
        const today = new Date().toISOString().split('T')[0];
        $($(this).data('target')).val(today);
    });
    
    // Status change confirmation
    $('.dropdown-item[data-status]').click(function(e) {
        const newStatus = $(this).data('status');
        const statusText = $(this).text();
        
        if (!confirm(`Changer le statut vers "${statusText}" ?`)) {
            e.preventDefault();
            return false;
        }
    });
    
    // Search form auto-submit delay
    let searchTimeout;
    $('input[name="search"]').on('input', function() {
        clearTimeout(searchTimeout);
        const form = $(this).closest('form');
        
        searchTimeout = setTimeout(function() {
            if (form.find('input[name="search"]').val().length >= 3 || form.find('input[name="search"]').val().length === 0) {
                form.submit();
            }
        }, 500);
    });
    
    // File upload preview
    $('input[type="file"]').change(function() {
        const file = this.files[0];
        const preview = $(this).siblings('.file-preview');
        
        if (file) {
            const fileName = file.name;
            const fileSize = (file.size / 1024 / 1024).toFixed(2); // Size in MB
            
            if (preview.length === 0) {
                $(this).after(`
                    <div class="file-preview mt-2">
                        <small class="text-muted">
                            <i class="fas fa-file me-1"></i>
                            <span class="file-name">${fileName}</span>
                            <span class="file-size">(${fileSize} MB)</span>
                        </small>
                    </div>
                `);
            } else {
                preview.find('.file-name').text(fileName);
                preview.find('.file-size').text(`(${fileSize} MB)`);
            }
            
            // Validate file size (16MB limit)
            if (file.size > 16 * 1024 * 1024) {
                alert('Le fichier est trop volumineux. Taille maximale: 16MB');
                $(this).val('');
                preview.remove();
            }
        } else {
            preview.remove();
        }
    });
    
    // Dynamic form field updates
    $('.client-type-radio').change(function() {
        updateClientFormFields();
    });
    
    function updateClientFormFields() {
        const selectedType = $('input[name="type"]:checked').val();
        
        if (selectedType === 'personne') {
            $('#nameLabel').text('Nom et prénom');
            $('#clientNameLabel').text('Nom et prénom');
            $('#clientIdLabel').text('CIN');
            $('#clientVatLabel').text('IF');
            $('.id-number-label').text('CIN (Carte d\'Identité Nationale)');
            $('.vat-number-label').text('IF (Identifiant Fiscal)');
        } else if (selectedType === 'entreprise') {
            $('#nameLabel').text('Raison sociale');
            $('#clientNameLabel').text('Raison sociale');
            $('#clientIdLabel').text('RC');
            $('#clientVatLabel').text('ICE');
            $('.id-number-label').text('RC (Registre de Commerce)');
            $('.vat-number-label').text('ICE (Identifiant Commun de l\'Entreprise)');
        }
    }
    
    // Initialize on page load
    updateClientFormFields();
    
    // Numeric input formatting
    $('.currency-input').on('input', function() {
        formatCurrency(this);
    });
    
    function formatCurrency(input) {
        let value = $(input).val().replace(/[^\d.]/g, '');
        let parts = value.split('.');
        
        // Format the integer part with thousands separators
        parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        
        // Limit decimal places to 2
        if (parts[1]) {
            parts[1] = parts[1].substring(0, 2);
        }
        
        $(input).val(parts.join('.'));
    }
    
    // Copy to clipboard functionality
    $('.copy-to-clipboard').click(function() {
        const text = $(this).data('text') || $(this).text();
        
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(function() {
                showToast('Copié dans le presse-papiers', 'success');
            });
        } else {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            showToast('Copié dans le presse-papiers', 'success');
        }
    });
    
    // Show toast notifications
    function showToast(message, type = 'info') {
        const toast = $(`
            <div class="toast align-items-center text-white bg-${type} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `);
        
        if ($('.toast-container').length === 0) {
            $('body').append('<div class="toast-container position-fixed bottom-0 end-0 p-3"></div>');
        }
        
        $('.toast-container').append(toast);
        const bsToast = new bootstrap.Toast(toast[0]);
        bsToast.show();
        
        // Remove from DOM after hiding
        toast.on('hidden.bs.toast', function() {
            $(this).remove();
        });
    }
    
    // Print functionality
    $('.btn-print').click(function() {
        window.print();
    });
    
    // Export form validation
    $('form[action*="export"]').on('submit', function(e) {
        const dateFrom = $(this).find('input[name="date_from"]').val();
        const dateTo = $(this).find('input[name="date_to"]').val();
        
        if (dateFrom && dateTo && new Date(dateFrom) > new Date(dateTo)) {
            e.preventDefault();
            alert('La date de début doit être antérieure à la date de fin.');
            return false;
        }
        
        const submitBtn = $(this).find('button[type="submit"]');
        submitBtn.addClass('btn-loading').prop('disabled', true);
        
        // Show loading message
        showToast('Génération en cours...', 'info');
        
        // Re-enable button after 10 seconds for exports
        setTimeout(function() {
            submitBtn.removeClass('btn-loading').prop('disabled', false);
        }, 10000);
    });
    
    // Auto-refresh for dashboard (every 5 minutes)
    if (window.location.pathname === '/' || window.location.pathname.includes('dashboard')) {
        setInterval(function() {
            if (document.visibilityState === 'visible') {
                // Only refresh if page is visible
                window.location.reload();
            }
        }, 5 * 60 * 1000); // 5 minutes
    }
    
    // Keyboard shortcuts
    $(document).keydown(function(e) {
        // Ctrl+N for new entries
        if (e.ctrlKey && e.keyCode === 78) {
            e.preventDefault();
            const newButton = $('.btn-primary[href*="new"]').first();
            if (newButton.length) {
                window.location.href = newButton.attr('href');
            }
        }
        
        // Escape to close modals
        if (e.keyCode === 27) {
            $('.modal.show').modal('hide');
        }
    });
    
    // Smooth scrolling for anchor links
    $('a[href^="#"]').click(function(e) {
        e.preventDefault();
        const target = $($(this).attr('href'));
        
        if (target.length) {
            $('html, body').animate({
                scrollTop: target.offset().top - 70
            }, 500);
        }
    });
    
    // Table row click to edit (if data-edit-url is present)
    $('tr[data-edit-url]').click(function() {
        window.location.href = $(this).data('edit-url');
    });
    
    // Initialize any other components
    initializeComponents();
});

// Initialize additional components
function initializeComponents() {
    // Initialize any date pickers if using a library
    if (typeof flatpickr !== 'undefined') {
        flatpickr('input[type="date"]', {
            dateFormat: 'Y-m-d',
            locale: 'fr'
        });
    }
    
    // Initialize any other third-party components
    if (typeof Choices !== 'undefined') {
        const selects = document.querySelectorAll('select.form-select');
        selects.forEach(select => {
            new Choices(select, {
                searchEnabled: false,
                itemSelectText: '',
            });
        });
    }
}

// Utility functions
window.ChequeManager = {
    formatCurrency: function(amount, currency = 'MAD') {
        return new Intl.NumberFormat('fr-FR', {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 2
        }).format(amount);
    },
    
    formatDate: function(date) {
        return new Intl.DateTimeFormat('fr-FR').format(new Date(date));
    },
    
    showConfirm: function(message, callback) {
        if (confirm(message)) {
            callback();
        }
    },
    
    showAlert: function(message, type = 'info') {
        const alertDiv = $(`
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `);
        
        $('.container').first().prepend(alertDiv);
        
        // Auto-hide after 5 seconds
        setTimeout(function() {
            alertDiv.fadeOut();
        }, 5000);
    }
};
