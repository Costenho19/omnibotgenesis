/**
 * OMNIX Dashboard V6.5.3 - Trading Signals Component
 */

const OmnixSignals = (function() {
    'use strict';

    function render(containerId, signals) {
        const container = document.getElementById(containerId);
        if (!container) return;

        if (!signals || signals.length === 0) {
            container.innerHTML = '<div style="color: var(--text-muted); font-size: 11px;">No active signals</div>';
            return;
        }

        container.innerHTML = signals.map(s => {
            const signalClass = getSignalClass(s.signal);
            return `
                <div class="signal-item signal-${signalClass}">
                    <div class="signal-info">
                        <div class="signal-strategy">${s.strategy}</div>
                        <div class="signal-pair">${s.symbol} | ${s.confidence}%</div>
                    </div>
                    <span class="signal-badge badge-${signalClass}">${s.signal}</span>
                </div>
            `;
        }).join('');
    }

    function getSignalClass(signal) {
        switch (signal?.toUpperCase()) {
            case 'BULLISH':
            case 'LONG':
            case 'BUY':
                return 'bullish';
            case 'BEARISH':
            case 'SHORT':
            case 'SELL':
                return 'bearish';
            default:
                return 'neutral';
        }
    }

    async function update(containerId) {
        try {
            const data = await OmnixAPI.getActiveSignals();
            if (data.success) {
                render(containerId, data.signals);
            }
        } catch (error) {
            console.error('Signals update error:', error);
        }
    }

    return {
        render,
        update,
        getSignalClass
    };
})();

if (typeof window !== 'undefined') {
    window.OmnixSignals = OmnixSignals;
}
