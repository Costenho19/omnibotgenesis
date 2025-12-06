/**
 * OMNIX Dashboard V6.5.4 - Price Ticker Component
 */

const OmnixTicker = (function() {
    'use strict';

    function renderTerminal(containerId, prices) {
        const container = document.getElementById(containerId);
        if (!container || !prices || prices.length === 0) return;

        container.innerHTML = prices.map(c => {
            const changeClass = c.is_positive ? 'positive' : 'negative';
            const arrow = c.is_positive ? '▲' : '▼';
            let price = formatPrice(c.price);

            return `
                <div class="ticker-item">
                    <div class="ticker-symbol">${c.symbol}/USD</div>
                    <div class="ticker-price ${changeClass}">${price}</div>
                    <div class="ticker-change ${changeClass}">${arrow} ${Math.abs(c.change_24h).toFixed(2)}%</div>
                </div>
            `;
        }).join('');
    }

    function renderDashboard(containerId, prices) {
        const container = document.getElementById(containerId);
        if (!container || !prices || prices.length === 0) return;

        container.innerHTML = prices.map(crypto => {
            const changeClass = crypto.is_positive ? 'stat-positive' : 'stat-negative';
            const borderClass = crypto.is_positive ? 'positive' : 'negative';
            const changePrefix = crypto.is_positive ? '+' : '';
            let priceFormatted = formatPrice(crypto.price);

            return `
                <div class="ticker-item ${borderClass}">
                    <div class="flex items-center justify-between mb-1">
                        <span class="font-semibold text-sm">${crypto.symbol}</span>
                        <span class="text-[10px] ${changeClass}">${changePrefix}${crypto.change_24h.toFixed(2)}%</span>
                    </div>
                    <div class="font-bold mono ${changeClass}">${priceFormatted}</div>
                </div>
            `;
        }).join('');
    }

    function formatPrice(price) {
        if (price >= 1000) {
            return '$' + price.toLocaleString('en-US', { maximumFractionDigits: 0 });
        } else if (price >= 1) {
            return '$' + price.toFixed(2);
        } else {
            return '$' + price.toFixed(4);
        }
    }

    async function update(containerId, style = 'terminal') {
        try {
            const data = await OmnixAPI.getCryptoPrices();
            if (data.success && data.prices.length > 0) {
                if (style === 'terminal') {
                    renderTerminal(containerId, data.prices);
                } else {
                    renderDashboard(containerId, data.prices);
                }
            }
        } catch (error) {
            console.error('Ticker update error:', error);
        }
    }

    return {
        renderTerminal,
        renderDashboard,
        update,
        formatPrice
    };
})();

if (typeof window !== 'undefined') {
    window.OmnixTicker = OmnixTicker;
}
