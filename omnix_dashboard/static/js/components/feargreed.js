/**
 * OMNIX Dashboard V6.5.3 - Fear & Greed Index Component
 */

const OmnixFearGreed = (function() {
    'use strict';

    function render(data, config = {}) {
        const {
            valueId = 'fng-value',
            labelId = 'fng-label',
            markerId = 'fng-marker',
            recommendationId = 'fng-recommendation',
            statusId = 'fng-status'
        } = config;

        if (!data) {
            setStatus(statusId, false);
            return;
        }

        const valueEl = document.getElementById(valueId);
        const labelEl = document.getElementById(labelId);
        const markerEl = document.getElementById(markerId);
        const recEl = document.getElementById(recommendationId);

        if (valueEl) {
            valueEl.textContent = data.value;
            valueEl.style.color = data.color || 'var(--accent-yellow)';
        }

        if (labelEl) {
            labelEl.textContent = data.classification || 'N/A';
        }

        if (markerEl) {
            markerEl.style.left = `${data.value}%`;
        }

        if (recEl) {
            recEl.textContent = data.recommendation || 'Market sentiment indicator';
        }

        setStatus(statusId, true);
    }

    function setStatus(statusId, isActive) {
        const statusEl = document.getElementById(statusId);
        if (!statusEl) return;

        if (isActive) {
            statusEl.className = 'intelligence-badge intel-active';
            statusEl.textContent = 'LIVE';
        } else {
            statusEl.className = 'intelligence-badge intel-inactive';
            statusEl.textContent = 'OFFLINE';
        }
    }

    function getColor(value) {
        if (value <= 20) return '#ff3366';
        if (value <= 40) return '#ff9933';
        if (value <= 60) return '#ffff00';
        if (value <= 80) return '#99ff33';
        return '#00ff88';
    }

    function getClassification(value) {
        if (value <= 20) return 'Extreme Fear';
        if (value <= 40) return 'Fear';
        if (value <= 60) return 'Neutral';
        if (value <= 80) return 'Greed';
        return 'Extreme Greed';
    }

    async function update(config = {}) {
        try {
            const data = await OmnixAPI.getFearGreed();
            if (data.success && data.data) {
                render(data.data, config);
            } else {
                setStatus(config.statusId || 'fng-status', false);
            }
        } catch (error) {
            console.error('Fear & Greed error:', error);
            setStatus(config.statusId || 'fng-status', false);
        }
    }

    return {
        render,
        update,
        getColor,
        getClassification,
        setStatus
    };
})();

if (typeof window !== 'undefined') {
    window.OmnixFearGreed = OmnixFearGreed;
}
