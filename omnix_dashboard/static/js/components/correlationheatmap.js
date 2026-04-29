(function() {
    'use strict';

    const REFRESH_INTERVAL = 60000;
    const API_KEY = 'omnix-dashboard-2024';

    function getCorrelationColor(corr) {
        if (corr === null || corr === undefined) return 'rgba(100, 100, 100, 0.3)';
        if (corr > 0) {
            const intensity = Math.abs(corr);
            return `rgba(16, 185, 129, ${0.2 + intensity * 0.8})`;
        } else {
            const intensity = Math.abs(corr);
            return `rgba(239, 68, 68, ${0.2 + intensity * 0.8})`;
        }
    }

    function getStrengthClass(strength) {
        if (strength === 'HIGH') return 'strength-high';
        if (strength === 'MEDIUM') return 'strength-medium';
        return 'strength-low';
    }

    async function fetchCorrelation() {
        try {
            const response = await fetch('/api/metrics/correlation', {
                headers: { 'X-API-Key': API_KEY }
            });
            const data = await response.json();
            if (data.success) {
                renderCorrelation(data);
            }
        } catch (error) {
            console.error('Correlation fetch error:', error);
        }
    }

    function renderCorrelation(data) {
        const container = document.getElementById('correlation-heatmap-widget');
        if (!container) return;

        const symbols = data.symbols || [];
        const correlations = data.correlations || [];

        let symbolsHtml = '';
        symbols.slice(0, 6).forEach(s => {
            const pnlClass = s.pnl >= 0 ? 'positive' : 'negative';
            const pnlStr = s.pnl >= 0 ? `+$${s.pnl.toFixed(0)}` : `-$${Math.abs(s.pnl).toFixed(0)}`;
            symbolsHtml += `
                <div class="corr-symbol">
                    <span class="symbol-name">${s.symbol}</span>
                    <span class="symbol-trades">${s.trades} trades</span>
                    <span class="symbol-wr">${s.win_rate}% WR</span>
                    <span class="symbol-pnl ${pnlClass}">${pnlStr}</span>
                </div>
            `;
        });

        let matrixHtml = '';
        if (correlations.length > 0) {
            matrixHtml = '<div class="corr-matrix">';
            correlations.slice(0, 8).forEach(c => {
                const color = getCorrelationColor(c.correlation);
                const strengthClass = getStrengthClass(c.strength);
                matrixHtml += `
                    <div class="corr-pair ${strengthClass}">
                        <div class="pair-names">${c.pair_a} / ${c.pair_b}</div>
                        <div class="pair-value" style="background: ${color}">${(c.correlation * 100).toFixed(0)}%</div>
                    </div>
                `;
            });
            matrixHtml += '</div>';
        } else {
            matrixHtml = '<div class="no-data">Insufficient data for correlation</div>';
        }

        container.innerHTML = `
            <div class="correlation-header">
                <span class="widget-icon">🔗</span>
                <span class="widget-title">Asset Correlation</span>
                <span class="widget-badge">${data.total_pairs || 0} pairs</span>
            </div>
            <div class="correlation-body">
                <div class="symbols-list">${symbolsHtml}</div>
                ${matrixHtml}
            </div>
        `;
    }

    function init() {
        fetchCorrelation();
        setInterval(fetchCorrelation, REFRESH_INTERVAL);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
