(function() {
    'use strict';
    
    const REFRESH_INTERVAL = 30000;
    
    function formatCurrency(value) {
        if (value === null || value === undefined) return 'N/A';
        const sign = value >= 0 ? '+' : '';
        const colorClass = value >= 0 ? 'pnl-positive' : 'pnl-negative';
        return `<span class="${colorClass}">${sign}$${Math.abs(value).toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 0})}</span>`;
    }
    
    function formatPercent(value) {
        if (value === null || value === undefined) return 'N/A';
        return `${value.toFixed(1)}%`;
    }
    
    function getBarWidth(pnl, maxAbsPnl) {
        if (maxAbsPnl === 0) return 0;
        return Math.min(100, (Math.abs(pnl) / maxAbsPnl) * 100);
    }
    
    function renderPnlBreakdown(data) {
        const container = document.getElementById('pnl-breakdown-widget');
        if (!container) return;
        
        if (!data.success || !data.breakdown) {
            container.innerHTML = `
                <div class="pnl-breakdown-widget">
                    <div class="pnl-breakdown-header">
                        <span class="pnl-breakdown-title">P&L Breakdown</span>
                    </div>
                    <div class="pnl-loading">No trade data available yet</div>
                </div>
            `;
            return;
        }
        
        const { by_symbol, by_cause, summary } = data.breakdown;
        
        const maxAbsPnl = Math.max(...by_symbol.map(s => Math.abs(s.pnl)), 1);
        
        let symbolBarsHtml = '';
        by_symbol.slice(0, 6).forEach(item => {
            const barWidth = getBarWidth(item.pnl, maxAbsPnl);
            const barClass = item.pnl >= 0 ? 'bar-positive' : 'bar-negative';
            const symbol = item.symbol.replace('/USD', '');
            
            symbolBarsHtml += `
                <div class="pnl-bar-row">
                    <span class="pnl-bar-label">${symbol}</span>
                    <div class="pnl-bar-container">
                        <div class="pnl-bar ${barClass}" style="width: ${barWidth}%"></div>
                    </div>
                    <span class="pnl-bar-value">${formatCurrency(item.pnl)}</span>
                </div>
            `;
        });
        
        let causeBarsHtml = '';
        by_cause.forEach(item => {
            const typeClass = item.type === 'success' ? 'cause-success' : 
                              item.type === 'warning' ? 'cause-warning' : 'cause-danger';
            
            causeBarsHtml += `
                <div class="cause-item ${typeClass}">
                    <div class="cause-header">
                        <span class="cause-name">${item.cause}</span>
                        <span class="cause-count">${item.count}</span>
                    </div>
                    <div class="cause-bar-container">
                        <div class="cause-bar" style="width: ${item.pct}%"></div>
                    </div>
                    <span class="cause-pct">${formatPercent(item.pct)}</span>
                </div>
            `;
        });
        
        container.innerHTML = `
            <div class="pnl-breakdown-widget">
                <div class="pnl-breakdown-header">
                    <span class="pnl-breakdown-title">P&L Breakdown</span>
                    <span class="pnl-total ${summary.total_pnl >= 0 ? 'pnl-positive' : 'pnl-negative'}">
                        ${summary.total_pnl >= 0 ? '+' : ''}$${Math.abs(summary.total_pnl).toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 0})}
                    </span>
                </div>
                
                <div class="pnl-section">
                    <div class="pnl-section-title">By Symbol</div>
                    <div class="pnl-bars">
                        ${symbolBarsHtml}
                    </div>
                </div>
                
                <div class="pnl-section">
                    <div class="pnl-section-title">Trade Outcomes</div>
                    <div class="cause-breakdown">
                        ${causeBarsHtml}
                    </div>
                </div>
                
                <div class="pnl-footer">
                    <span class="pnl-stat">
                        <span class="stat-label">Directional Accuracy</span>
                        <span class="stat-value">${formatPercent(summary.directional_accuracy)}</span>
                    </span>
                    <span class="pnl-stat">
                        <span class="stat-label">Total Trades</span>
                        <span class="stat-value">${summary.total_trades}</span>
                    </span>
                </div>
            </div>
        `;
    }
    
    async function fetchPnlBreakdown() {
        try {
            const response = await fetch('/api/metrics/pnl-breakdown', {
                headers: { 'X-API-Key': 'omnix-dashboard-2024' }
            });
            const data = await response.json();
            renderPnlBreakdown(data);
        } catch (error) {
            console.error('Failed to fetch P&L breakdown:', error);
        }
    }
    
    function init() {
        fetchPnlBreakdown();
        setInterval(fetchPnlBreakdown, REFRESH_INTERVAL);
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
