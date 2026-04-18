(function() {
    'use strict';
    
    const REFRESH_INTERVAL = 30000;
    
    function formatPercent(value, showSign = true, neutralIfZero = false) {
        if (value === null || value === undefined) return '<span class="metric-na">N/A</span>';
        const sign = showSign && value > 0 ? '+' : '';
        let colorClass = value >= 0 ? 'metric-positive' : 'metric-negative';
        if (neutralIfZero && value === 0) colorClass = 'metric-neutral';
        return `<span class="${colorClass}">${sign}${value.toFixed(1)}%</span>`;
    }
    
    function formatNumber(value) {
        if (value === null || value === undefined) return '<span class="metric-na">N/A</span>';
        if (value === 0) return '<span class="metric-neutral">0</span>';
        return value.toLocaleString();
    }
    
    function renderComparativeMetrics(data) {
        const container = document.getElementById('comparative-metrics-widget');
        if (!container) return;
        
        if (!data.success || !data.comparison) {
            container.innerHTML = `
                <div class="comparative-metrics-widget">
                    <div class="comparative-metrics-header">
                        <span class="comparative-metrics-title">📊 Strategy Comparison</span>
                    </div>
                    <div class="comparative-loading">No trade data available yet</div>
                </div>
            `;
            return;
        }
        
        const { comparison, insights, period } = data;
        const omnix = comparison.omnix;
        const btc = comparison.btc_hold;
        const avg = comparison.avg_bot;
        
        const getBestClass = (omnixVal, btcVal, avgVal, higherIsBetter = true) => {
            const values = [
                { name: 'omnix', val: omnixVal },
                { name: 'btc', val: btcVal },
                { name: 'avg', val: avgVal }
            ].filter(v => v.val !== null && v.val !== undefined);
            
            if (values.length === 0) return {};
            
            const best = higherIsBetter 
                ? values.reduce((a, b) => a.val > b.val ? a : b)
                : values.reduce((a, b) => a.val > b.val ? a : b);
            
            return { [best.name]: 'metric-best' };
        };
        
        const preservedBest = getBestClass(omnix.capital_preserved_pct, btc.capital_preserved_pct, avg.capital_preserved_pct, true);
        // FIX: For Max DD, higher (closer to 0) is better - less negative = better
        const ddBest = getBestClass(omnix.max_drawdown_pct, btc.max_drawdown_pct, avg.max_drawdown_pct, true);
        
        let insightsHtml = '';
        if (insights && insights.length > 0) {
            insightsHtml = `
                <div class="comparative-insights">
                    ${insights.map(i => `
                        <div class="insight-item">
                            <div class="insight-icon ${i.type}">${i.type === 'success' ? '✓' : 'ℹ'}</div>
                            <div class="insight-message">${i.message}</div>
                        </div>
                    `).join('')}
                </div>
            `;
        }
        
        container.innerHTML = `
            <div class="comparative-metrics-widget">
                <div class="comparative-metrics-header">
                    <span class="comparative-metrics-title">📊 Strategy Comparison</span>
                    <span class="comparative-metrics-badge">INVESTOR INSIGHT</span>
                </div>
                
                <table class="comparative-table">
                    <thead>
                        <tr>
                            <th>Strategy</th>
                            <th>Return</th>
                            <th>Preserved</th>
                            <th>Max DD</th>
                            <th>Win Rate</th>
                            <th>Risk Blocked</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>
                                <div class="strategy-name omnix">
                                    <div class="strategy-icon omnix">O</div>
                                    OMNIX
                                </div>
                            </td>
                            <td>${formatPercent(omnix.return_pct, true, true)}</td>
                            <td class="${preservedBest.omnix || ''}">${formatPercent(omnix.capital_preserved_pct, false)}</td>
                            <td class="${ddBest.omnix || ''}">${formatPercent(omnix.max_drawdown_pct)}</td>
                            <td>${omnix.win_rate !== null ? omnix.win_rate + '%' : '<span class="metric-na">N/A</span>'}</td>
                            <td><span class="metric-positive">${formatNumber(omnix.risk_blocked)}</span></td>
                        </tr>
                        <tr>
                            <td>
                                <div class="strategy-name btc">
                                    <div class="strategy-icon btc">₿</div>
                                    BTC HOLD
                                </div>
                            </td>
                            <td>${formatPercent(btc.return_pct)}</td>
                            <td class="${preservedBest.btc || ''}">${formatPercent(btc.capital_preserved_pct, false)}</td>
                            <td class="${ddBest.btc || ''}">${formatPercent(btc.max_drawdown_pct)}</td>
                            <td><span class="metric-na">N/A</span></td>
                            <td><span class="metric-neutral">0</span></td>
                        </tr>
                        <tr>
                            <td>
                                <div class="strategy-name avg">
                                    <div class="strategy-icon avg">⚙</div>
                                    AVG BOT
                                </div>
                            </td>
                            <td>${formatPercent(avg.return_pct)}</td>
                            <td class="${preservedBest.avg || ''}">${formatPercent(avg.capital_preserved_pct, false)}</td>
                            <td class="${ddBest.avg || ''}">${formatPercent(avg.max_drawdown_pct)}</td>
                            <td>${avg.win_rate}%</td>
                            <td><span class="metric-neutral">0</span></td>
                        </tr>
                    </tbody>
                </table>
                
                ${insightsHtml}
                
                <div class="comparative-period">
                    Period: ${period || 'Last 30 days'}
                    ${omnix.official_trades === 0 ? '<br><span style="font-size: 9px; color: #9ca3af;">Note: Win Rate shows N/A - Official Track Record has 0 trades yet</span>' : ''}
                </div>
            </div>
        `;
    }
    
    function fetchComparativeMetrics() {
        const apiKey = window.OMNIX_API_KEY || 'omnix-dashboard-2024';
        
        fetch('/api/metrics/comparative', {
            headers: {
                'X-API-Key': apiKey
            }
        })
        .then(response => response.json())
        .then(data => {
            renderComparativeMetrics(data);
        })
        .catch(error => {
            console.error('Error fetching comparative metrics:', error);
            const container = document.getElementById('comparative-metrics-widget');
            if (container) {
                container.innerHTML = `
                    <div class="comparative-metrics-widget">
                        <div class="comparative-metrics-header">
                            <span class="comparative-metrics-title">📊 Strategy Comparison</span>
                        </div>
                        <div class="comparative-error">Error loading comparison data</div>
                    </div>
                `;
            }
        });
    }
    
    document.addEventListener('DOMContentLoaded', function() {
        fetchComparativeMetrics();
        setInterval(fetchComparativeMetrics, REFRESH_INTERVAL);
    });
    
    window.refreshComparativeMetrics = fetchComparativeMetrics;
})();
