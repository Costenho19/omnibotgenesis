const EquityComparison = (function() {
    'use strict';

    let _comparison = null;

    async function fetchComparison() {
        try {
            const response = await OmnixAPI.fetchWithRetry('/api/system/equity');
            
            if (response && response.success && response.equity) {
                _comparison = response.equity.comparison;
                return response.equity;
            }
            return null;
        } catch (error) {
            console.error('[EquityComparison] Error:', error);
            return null;
        }
    }

    function renderAlphaBadge() {
        if (!_comparison) return;

        const container = document.getElementById('equity-panel-header');
        if (!container) return;

        const existingBadge = container.querySelector('.alpha-badge');
        if (existingBadge) {
            existingBadge.remove();
        }

        const alpha = _comparison.alpha;
        const isPositive = alpha >= 0;
        const color = isPositive ? '#00d4aa' : '#ff6b6b';
        const sign = isPositive ? '+' : '';
        
        const badgeHTML = `
            <div class="alpha-badge" style="
                display: flex;
                align-items: center;
                gap: 12px;
                margin-left: auto;
                padding-right: 8px;
            ">
                <div class="comparison-item" style="text-align: center;">
                    <div style="font-size: 11px; font-weight: 600; color: #00d4aa;">OMNIX</div>
                    <div style="font-size: 13px; font-weight: 700; color: ${_comparison.omnix_return >= 0 ? '#00d4aa' : '#ff6b6b'};">
                        ${_comparison.omnix_return >= 0 ? '+' : ''}${_comparison.omnix_return}%
                    </div>
                </div>
                <div style="color: #666; font-size: 10px;">vs</div>
                <div class="comparison-item" style="text-align: center;">
                    <div style="font-size: 11px; font-weight: 600; color: #F7931A;">BTC Hold</div>
                    <div style="font-size: 13px; font-weight: 700; color: ${_comparison.btc_return >= 0 ? '#00d4aa' : '#ff6b6b'};">
                        ${_comparison.btc_return >= 0 ? '+' : ''}${_comparison.btc_return}%
                    </div>
                </div>
                <div class="alpha-value" style="
                    background: ${isPositive ? 'linear-gradient(135deg, #00d4aa22 0%, #00d4aa11 100%)' : 'linear-gradient(135deg, #ff6b6b22 0%, #ff6b6b11 100%)'};
                    border: 1px solid ${color};
                    border-radius: 6px;
                    padding: 6px 10px;
                    text-align: center;
                ">
                    <div style="font-size: 9px; color: #888; letter-spacing: 0.5px;">ALPHA</div>
                    <div style="font-size: 14px; font-weight: 700; color: ${color};">
                        ${sign}${alpha.toFixed(2)}%
                    </div>
                </div>
            </div>
        `;

        const titleDiv = container.querySelector('.equity-panel__title');
        if (titleDiv) {
            titleDiv.insertAdjacentHTML('afterend', badgeHTML);
        } else {
            container.insertAdjacentHTML('beforeend', badgeHTML);
        }
    }

    async function refresh() {
        await fetchComparison();
        renderAlphaBadge();
        return _comparison;
    }

    function init() {
        console.log('EquityComparison widget initialized');
        refresh();
    }

    function getComparison() {
        return _comparison;
    }

    return {
        init: init,
        refresh: refresh,
        getComparison: getComparison
    };
})();

if (typeof window !== 'undefined') {
    window.EquityComparison = EquityComparison;
}
