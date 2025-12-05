/**
 * OMNIX Dashboard V6.5.3 - Utility Functions
 */

const OmnixUtils = (function() {
    'use strict';

    function formatCurrency(value, options = {}) {
        const { 
            prefix = '$', 
            decimals = 2, 
            showSign = false,
            abbreviate = false 
        } = options;

        if (value === null || value === undefined || isNaN(value)) {
            return `${prefix}0.00`;
        }

        const absValue = Math.abs(value);
        let formatted;

        if (abbreviate) {
            if (absValue >= 1e9) {
                formatted = `${(absValue / 1e9).toFixed(1)}B`;
            } else if (absValue >= 1e6) {
                formatted = `${(absValue / 1e6).toFixed(1)}M`;
            } else if (absValue >= 1e3) {
                formatted = `${(absValue / 1e3).toFixed(1)}K`;
            } else {
                formatted = absValue.toFixed(decimals);
            }
        } else if (absValue >= 1000) {
            formatted = absValue.toLocaleString('en-US', {
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
            });
        } else if (absValue >= 1) {
            formatted = absValue.toFixed(decimals);
        } else {
            formatted = absValue.toFixed(4);
        }

        const sign = showSign && value >= 0 ? '+' : (value < 0 ? '-' : '');
        return `${sign}${prefix}${formatted}`;
    }

    function formatPercent(value, options = {}) {
        const { decimals = 2, showSign = false } = options;
        
        if (value === null || value === undefined || isNaN(value)) {
            return '0%';
        }

        const sign = showSign && value >= 0 ? '+' : (value < 0 ? '-' : '');
        return `${sign}${Math.abs(value).toFixed(decimals)}%`;
    }

    function formatNumber(value, decimals = 2) {
        if (value === null || value === undefined || isNaN(value)) {
            return '0';
        }
        return value.toLocaleString('en-US', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        });
    }

    function formatTime(date, options = {}) {
        if (typeof OmnixTime !== 'undefined') {
            return OmnixTime.formatTime(date, options);
        }
        const { hour12 = false } = options;
        return date.toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit', 
            second: '2-digit',
            hour12 
        });
    }

    function formatDate(date, options = {}) {
        if (typeof OmnixTime !== 'undefined') {
            return OmnixTime.formatDate(date, options);
        }
        const { style = 'short' } = options;
        
        if (style === 'long') {
            return date.toLocaleDateString('en-US', { 
                weekday: 'long',
                year: 'numeric',
                month: 'long', 
                day: 'numeric' 
            });
        }
        
        return date.toLocaleDateString('en-US', { 
            weekday: 'short',
            month: 'short', 
            day: 'numeric' 
        });
    }

    function formatDateTime(date) {
        if (typeof OmnixTime !== 'undefined') {
            return OmnixTime.formatDateTime(date);
        }
        return `${formatDate(date)} ${formatTime(date)}`;
    }

    function formatRelative(date) {
        if (typeof OmnixTime !== 'undefined') {
            return OmnixTime.formatRelative(date);
        }
        const now = new Date();
        const diffMs = now - new Date(date);
        const diffMin = Math.floor(diffMs / 60000);
        if (diffMin < 60) return `${diffMin}m ago`;
        const diffHour = Math.floor(diffMin / 60);
        if (diffHour < 24) return `${diffHour}h ago`;
        return formatDate(new Date(date));
    }

    function getPnlClass(value) {
        if (value > 0) return 'positive';
        if (value < 0) return 'negative';
        return 'neutral';
    }

    function getStatClass(value) {
        if (value > 0) return 'stat-positive';
        if (value < 0) return 'stat-negative';
        return 'stat-neutral';
    }

    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    function throttle(func, limit) {
        let inThrottle;
        return function executedFunction(...args) {
            if (!inThrottle) {
                func(...args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    function setElement(id, value, options = {}) {
        const el = document.getElementById(id);
        if (!el) return;
        
        el.textContent = value;
        
        if (options.className) {
            el.className = options.className;
        }
    }

    return {
        formatCurrency,
        formatPercent,
        formatNumber,
        formatTime,
        formatDate,
        formatDateTime,
        formatRelative,
        getPnlClass,
        getStatClass,
        debounce,
        throttle,
        setElement
    };
})();

if (typeof window !== 'undefined') {
    window.OmnixUtils = OmnixUtils;
}
