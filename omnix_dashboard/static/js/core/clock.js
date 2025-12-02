/**
 * OMNIX Dashboard V6.5 - Real-time Clock
 */

const OmnixClock = (function() {
    'use strict';

    let animationFrameId = null;
    let lastSecond = -1;
    const timezoneInfo = Intl.DateTimeFormat().resolvedOptions().timeZone;
    const tzShort = timezoneInfo.split('/').pop().replace('_', ' ');

    function start(config = {}) {
        const {
            timeId = 'clock-time',
            dateId = 'clock-date',
            timezoneId = null
        } = config;

        function update() {
            const now = new Date();
            const currentSecond = now.getSeconds();

            if (currentSecond !== lastSecond) {
                lastSecond = currentSecond;

                const timeEl = document.getElementById(timeId);
                const dateEl = document.getElementById(dateId);
                const tzEl = timezoneId ? document.getElementById(timezoneId) : null;

                if (timeEl) {
                    timeEl.textContent = now.toLocaleTimeString('en-US', { hour12: false });
                }

                if (dateEl) {
                    dateEl.textContent = now.toLocaleDateString('en-US', { 
                        weekday: 'short', 
                        month: 'short', 
                        day: 'numeric' 
                    });
                }

                if (tzEl) {
                    tzEl.textContent = tzShort;
                }
            }

            animationFrameId = requestAnimationFrame(update);
        }

        update();
    }

    function stop() {
        if (animationFrameId) {
            cancelAnimationFrame(animationFrameId);
            animationFrameId = null;
        }
    }

    function getTimezone() {
        return timezoneInfo;
    }

    function getTimezoneShort() {
        return tzShort;
    }

    return {
        start,
        stop,
        getTimezone,
        getTimezoneShort
    };
})();

if (typeof window !== 'undefined') {
    window.OmnixClock = OmnixClock;
}
