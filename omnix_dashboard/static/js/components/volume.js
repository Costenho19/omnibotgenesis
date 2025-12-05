/**
 * OMNIX Dashboard V6.5.3 - Volume Bars Component
 */

const OmnixVolume = (function() {
    'use strict';

    function render(containerId, volumes) {
        const container = document.getElementById(containerId);
        if (!container) return;

        if (!volumes || volumes.length === 0) {
            container.innerHTML = '<div style="color: var(--text-muted); font-size: 11px;">Loading volume data...</div>';
            return;
        }

        const maxVol = Math.max(...volumes.map(v => v.volume_usd));

        container.innerHTML = volumes.map(v => {
            const pct = (v.volume_usd / maxVol * 100).toFixed(0);
            const volStr = formatVolume(v.volume_usd);
            return `
                <div class="volume-bar">
                    <div class="volume-fill" style="width: ${pct}%;"></div>
                    <span class="volume-label">${v.symbol}</span>
                    <span class="volume-value">${volStr}</span>
                </div>
            `;
        }).join('');
    }

    function formatVolume(value) {
        if (value >= 1e9) {
            return `$${(value / 1e9).toFixed(1)}B`;
        } else if (value >= 1e6) {
            return `$${(value / 1e6).toFixed(0)}M`;
        } else if (value >= 1e3) {
            return `$${(value / 1e3).toFixed(0)}K`;
        }
        return `$${value.toFixed(0)}`;
    }

    async function update(containerId) {
        try {
            const data = await OmnixAPI.getVolume();
            if (data.success && data.volumes.length > 0) {
                render(containerId, data.volumes);
            }
        } catch (error) {
            console.error('Volume update error:', error);
        }
    }

    return {
        render,
        update,
        formatVolume
    };
})();

if (typeof window !== 'undefined') {
    window.OmnixVolume = OmnixVolume;
}
