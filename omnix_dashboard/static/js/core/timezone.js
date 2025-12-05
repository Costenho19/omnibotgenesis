/**
 * OMNIX Dashboard V6.5.3 - Unified Timezone Management
 * Provides centralized formatting for all timestamps across the dashboard
 */

const OmnixTime = (function() {
    'use strict';

    const STORAGE_KEY = 'omnix_timezone_preference';
    const DEFAULT_TIMEZONE = Intl.DateTimeFormat().resolvedOptions().timeZone;
    
    let _timezone = DEFAULT_TIMEZONE;
    let _use24Hour = true;
    let _locale = 'en-US';

    function init() {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved) {
            try {
                const prefs = JSON.parse(saved);
                _timezone = prefs.timezone || DEFAULT_TIMEZONE;
                _use24Hour = prefs.use24Hour !== false;
                _locale = prefs.locale || 'en-US';
            } catch (e) {
                console.warn('[OmnixTime] Failed to parse saved preferences');
            }
        }
    }

    function savePreferences() {
        localStorage.setItem(STORAGE_KEY, JSON.stringify({
            timezone: _timezone,
            use24Hour: _use24Hour,
            locale: _locale
        }));
    }

    function setTimezone(tz) {
        _timezone = tz;
        savePreferences();
    }

    function getTimezone() {
        return _timezone;
    }

    function getTimezoneShort() {
        return _timezone.split('/').pop().replace(/_/g, ' ');
    }

    function set24Hour(enabled) {
        _use24Hour = enabled;
        savePreferences();
    }

    function setLocale(locale) {
        _locale = locale;
        savePreferences();
    }

    function formatTime(date, options = {}) {
        const d = date instanceof Date ? date : new Date(date);
        if (isNaN(d.getTime())) return '--:--:--';
        
        const defaultOpts = {
            timeZone: _timezone,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: !_use24Hour
        };
        
        return d.toLocaleTimeString(_locale, { ...defaultOpts, ...options });
    }

    function formatDate(date, options = {}) {
        const d = date instanceof Date ? date : new Date(date);
        if (isNaN(d.getTime())) return '--';
        
        const defaultOpts = {
            timeZone: _timezone,
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        };
        
        return d.toLocaleDateString(_locale, { ...defaultOpts, ...options });
    }

    function formatDateTime(date, options = {}) {
        const d = date instanceof Date ? date : new Date(date);
        if (isNaN(d.getTime())) return '--';
        
        const defaultOpts = {
            timeZone: _timezone,
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: !_use24Hour
        };
        
        return d.toLocaleString(_locale, { ...defaultOpts, ...options });
    }

    function formatRelative(date) {
        const d = date instanceof Date ? date : new Date(date);
        if (isNaN(d.getTime())) return '--';
        
        const now = new Date();
        const diffMs = now - d;
        const diffSec = Math.floor(diffMs / 1000);
        const diffMin = Math.floor(diffSec / 60);
        const diffHour = Math.floor(diffMin / 60);
        const diffDay = Math.floor(diffHour / 24);
        
        if (diffSec < 60) return 'Just now';
        if (diffMin < 60) return `${diffMin}m ago`;
        if (diffHour < 24) return `${diffHour}h ago`;
        if (diffDay < 7) return `${diffDay}d ago`;
        
        return formatDate(d);
    }

    function formatTimestamp(isoString) {
        if (!isoString) return '--';
        return formatDateTime(new Date(isoString));
    }

    function formatTradeTime(isoString) {
        if (!isoString) return '--';
        const d = new Date(isoString);
        return formatTime(d, { second: undefined });
    }

    function formatShortDate(isoString) {
        if (!isoString) return '--';
        const d = new Date(isoString);
        return d.toLocaleDateString(_locale, {
            timeZone: _timezone,
            month: 'numeric',
            day: 'numeric'
        });
    }

    function now() {
        return new Date().toLocaleString(_locale, {
            timeZone: _timezone,
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: !_use24Hour
        });
    }

    function getAvailableTimezones() {
        return [
            { value: 'America/New_York', label: 'New York (ET)' },
            { value: 'America/Chicago', label: 'Chicago (CT)' },
            { value: 'America/Denver', label: 'Denver (MT)' },
            { value: 'America/Los_Angeles', label: 'Los Angeles (PT)' },
            { value: 'Europe/London', label: 'London (GMT/BST)' },
            { value: 'Europe/Paris', label: 'Paris (CET)' },
            { value: 'Europe/Madrid', label: 'Madrid (CET)' },
            { value: 'Asia/Tokyo', label: 'Tokyo (JST)' },
            { value: 'Asia/Singapore', label: 'Singapore (SGT)' },
            { value: 'Asia/Hong_Kong', label: 'Hong Kong (HKT)' },
            { value: 'Australia/Sydney', label: 'Sydney (AEST)' },
            { value: 'UTC', label: 'UTC' }
        ];
    }

    init();

    return {
        init,
        setTimezone,
        getTimezone,
        getTimezoneShort,
        set24Hour,
        setLocale,
        formatTime,
        formatDate,
        formatDateTime,
        formatRelative,
        formatTimestamp,
        formatTradeTime,
        formatShortDate,
        now,
        getAvailableTimezones
    };
})();

if (typeof window !== 'undefined') {
    window.OmnixTime = OmnixTime;
}
