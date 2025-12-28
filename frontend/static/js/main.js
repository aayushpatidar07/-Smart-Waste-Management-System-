/*
============================================
Smart Waste Management System - Main JavaScript
============================================
*/

// Global utility functions
const WasteManagement = {
    
    /**
     * Format date to readable string
     */
    formatDate: function(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    },
    
    /**
     * Format datetime to readable string
     */
    formatDateTime: function(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },
    
    /**
     * Get relative time (e.g., "2 hours ago")
     */
    getRelativeTime: function(dateString) {
        if (!dateString) return 'Unknown';
        
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
        if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
        if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
        
        return this.formatDate(dateString);
    },
    
    /**
     * Get status badge class
     */
    getStatusClass: function(status) {
        const statusMap = {
            'active': 'success',
            'inactive': 'secondary',
            'maintenance': 'warning',
            'pending': 'warning',
            'completed': 'success',
            'cancelled': 'danger',
            'resolved': 'success',
            'acknowledged': 'info',
            'available': 'success',
            'on-route': 'primary',
            'offline': 'secondary'
        };
        
        return statusMap[status.toLowerCase()] || 'secondary';
    },
    
    /**
     * Get waste level color
     */
    getWasteLevelClass: function(level) {
        if (level >= 90) return 'danger';
        if (level >= 80) return 'warning';
        if (level >= 60) return 'info';
        return 'success';
    },
    
    /**
     * Get priority badge class
     */
    getPriorityClass: function(priority) {
        const priorityMap = {
            'critical': 'danger',
            'high': 'warning',
            'medium': 'info',
            'low': 'secondary'
        };
        
        return priorityMap[priority.toLowerCase()] || 'secondary';
    },
    
    /**
     * Show notification
     */
    showNotification: function(message, type = 'info') {
        const alertClass = `alert-${type}`;
        const alert = $(`
            <div class="alert ${alertClass} alert-dismissible fade show position-fixed top-0 end-0 m-3" 
                 role="alert" style="z-index: 9999; min-width: 300px;">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `);
        
        $('body').append(alert);
        
        // Auto dismiss after 5 seconds
        setTimeout(function() {
            alert.alert('close');
        }, 5000);
    },
    
    /**
     * Confirm action
     */
    confirm: function(message, callback) {
        if (window.confirm(message)) {
            callback();
        }
    },
    
    /**
     * API call wrapper
     */
    apiCall: function(url, method = 'GET', data = null) {
        const options = {
            url: url,
            method: method,
            dataType: 'json'
        };
        
        if (data) {
            options.contentType = 'application/json';
            options.data = JSON.stringify(data);
        }
        
        return $.ajax(options);
    },
    
    /**
     * Show loading spinner
     */
    showLoading: function(element) {
        $(element).html('<div class="text-center py-4"><div class="spinner-border text-primary"></div></div>');
    },
    
    /**
     * Create progress bar HTML
     */
    createProgressBar: function(percentage, showLabel = true) {
        const colorClass = this.getWasteLevelClass(percentage);
        const label = showLabel ? `${percentage}%` : '';
        
        return `
            <div class="progress" style="height: 24px;">
                <div class="progress-bar bg-${colorClass}" 
                     role="progressbar" 
                     style="width: ${percentage}%" 
                     aria-valuenow="${percentage}" 
                     aria-valuemin="0" 
                     aria-valuemax="100">
                    ${label}
                </div>
            </div>
        `;
    },
    
    /**
     * Create badge HTML
     */
    createBadge: function(text, type = 'primary') {
        return `<span class="badge bg-${type}">${text}</span>`;
    },
    
    /**
     * Refresh page data
     */
    refreshData: function(callback, interval = 30000) {
        if (typeof callback === 'function') {
            callback();
            setInterval(callback, interval);
        }
    }
};

// Document ready
$(document).ready(function() {
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Smooth scroll for anchor links
    $('a[href^="#"]').on('click', function(e) {
        const target = $(this.getAttribute('href'));
        if (target.length) {
            e.preventDefault();
            $('html, body').stop().animate({
                scrollTop: target.offset().top - 100
            }, 1000);
        }
    });
    
    // Auto-hide alerts
    $('.alert').not('.alert-permanent').delay(5000).fadeOut('slow');
    
    // Confirm delete actions
    $('[data-confirm]').on('click', function(e) {
        if (!confirm($(this).data('confirm'))) {
            e.preventDefault();
        }
    });
    
    // Form validation
    $('form[data-validate]').on('submit', function(e) {
        const form = $(this)[0];
        if (!form.checkValidity()) {
            e.preventDefault();
            e.stopPropagation();
        }
        $(this).addClass('was-validated');
    });
    
    // Table search
    $('.table-search').on('keyup', function() {
        const value = $(this).val().toLowerCase();
        const table = $($(this).data('table'));
        
        table.find('tbody tr').filter(function() {
            $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1);
        });
    });
    
    // Back to top button
    const backToTop = $('<button>')
        .addClass('btn btn-success btn-floating position-fixed bottom-0 end-0 m-3')
        .css({
            'display': 'none',
            'z-index': 999,
            'border-radius': '50%',
            'width': '50px',
            'height': '50px'
        })
        .html('<i class="bi bi-arrow-up"></i>')
        .appendTo('body');
    
    $(window).scroll(function() {
        if ($(this).scrollTop() > 300) {
            backToTop.fadeIn();
        } else {
            backToTop.fadeOut();
        }
    });
    
    backToTop.on('click', function() {
        $('html, body').animate({scrollTop: 0}, 800);
    });
});

// Global error handler
$(document).ajaxError(function(event, jqxhr, settings, thrownError) {
    console.error('AJAX Error:', thrownError);
    
    if (jqxhr.status === 401) {
        WasteManagement.showNotification('Session expired. Please login again.', 'warning');
        setTimeout(function() {
            window.location.href = '/login';
        }, 2000);
    } else if (jqxhr.status === 403) {
        WasteManagement.showNotification('You do not have permission to perform this action.', 'danger');
    } else if (jqxhr.status === 500) {
        WasteManagement.showNotification('Server error. Please try again later.', 'danger');
    }
});

// Export for use in other scripts
window.WM = WasteManagement;
