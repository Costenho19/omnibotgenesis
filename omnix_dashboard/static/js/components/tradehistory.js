const TradeHistoryWidget = {
    containerId: 'trade-history-container',
    currentMode: 'official',
    
    async refresh() {
        try {
            const url = this.currentMode === 'official' 
                ? '/api/trades/history?telemetry_source=REAL'
                : '/api/trades/history';
            const response = await fetch(url);
            const data = await response.json();
            
            if (!data.success) {
                this.renderError(data.error || 'Failed to load trade history');
                return;
            }
            
            this.render(data);
        } catch (error) {
            console.error('TradeHistory error:', error);
            this.renderError('Connection error');
        }
    },
    
    setMode(mode) {
        this.currentMode = mode;
        
        const buttons = document.querySelectorAll('.telemetry-btn');
        buttons.forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.mode === mode) {
                btn.classList.add('active');
            }
        });
        
        this.refresh();
    },
    
    render(data) {
        const container = document.getElementById(this.containerId);
        if (!container) return;
        
        const { trades, statistics, sample_analysis } = data;
        
        let html = '';
        
        if (this.currentMode === 'official' && (!trades || trades.length === 0)) {
            const trackRecordStart = new Date('2026-01-15T00:00:00Z');
            const now = new Date();
            const daysSinceStart = Math.ceil((now - trackRecordStart) / (1000 * 60 * 60 * 24));
            const currentDay = Math.max(1, daysSinceStart);
            
            html += `
                <div class="official-notice" style="background: rgba(0, 255, 136, 0.05); border: 1px solid rgba(0, 255, 136, 0.2); border-radius: 8px; padding: 16px; margin-bottom: 12px; text-align: center;">
                    <div style="font-size: 14px; color: #00ff88; margin-bottom: 8px;">Official Track Record - Day ${currentDay}</div>
                    <div style="font-size: 12px; color: #888;">
                        No trades executed. System evaluating market conditions.<br>
                        <span style="color: #666; font-style: italic;">Switch to "Full History" to see Learning Baseline trades.</span>
                    </div>
                </div>
            `;
        }
        
        if (this.currentMode === 'full') {
            html += `
                <div class="calibration-notice" style="background: rgba(255, 152, 0, 0.05); border: 1px solid rgba(255, 152, 0, 0.2); border-radius: 8px; padding: 10px; margin-bottom: 12px;">
                    <div style="font-size: 11px; color: #ff9800;">
                        <strong>LEARNING BASELINE</strong> (Nov 2025 - Jan 14, 2026): 119 trades, -$15,198.73 P&L.<br>
                        This data is separated from the Official Track Record and used for system calibration only.
                    </div>
                </div>
            `;
        }
        
        if (sample_analysis && !sample_analysis.is_significant) {
            html += `
                <div class="sample-warning">
                    <span class="sample-warning-icon">&#9888;</span>
                    <span class="sample-warning-text">
                        Statistical Warning: ${sample_analysis.current_sample}/${sample_analysis.minimum_required} trades. 
                        Metrics may vary as more trades are executed.
                    </span>
                    <div class="sample-progress">
                        <div class="sample-progress-bar">
                            <div class="sample-progress-fill" style="width: ${sample_analysis.confidence_level}%"></div>
                        </div>
                        <span class="sample-progress-text">${sample_analysis.confidence_level}%</span>
                    </div>
                </div>
            `;
        }
        
        if (statistics) {
            const significanceBadge = sample_analysis?.is_significant 
                ? '<span class="badge-significant">SIGNIFICANT</span>'
                : '<span class="badge-insufficient">BUILDING SAMPLE</span>';
            
            const modeBadge = this.currentMode === 'official'
                ? '<span class="telemetry-indicator" style="background: rgba(0,255,136,0.1); color: #00ff88;">OFFICIAL</span>'
                : '<span class="telemetry-indicator" style="background: rgba(255,152,0,0.1); color: #ff9800;">FULL</span>';
            
            html += `
                <div class="trade-stats-row">
                    <div class="trade-stat-mini">
                        <span class="trade-stat-mini-label">Trades:</span>
                        <span class="trade-stat-mini-value">${statistics.total_trades}</span>
                    </div>
                    <div class="trade-stat-mini">
                        <span class="trade-stat-mini-label">Wins:</span>
                        <span class="trade-stat-mini-value positive">${statistics.winning_trades}</span>
                    </div>
                    <div class="trade-stat-mini">
                        <span class="trade-stat-mini-label">Losses:</span>
                        <span class="trade-stat-mini-value negative">${statistics.losing_trades}</span>
                    </div>
                    <div class="trade-stat-mini" title="Directional: Price moved as predicted">
                        <span class="trade-stat-mini-label">WR Dir:</span>
                        <span class="trade-stat-mini-value ${statistics.win_rate_directional >= 40 ? 'positive' : ''}">${(statistics.win_rate_directional || 0).toFixed(1)}%</span>
                    </div>
                    <div class="trade-stat-mini" title="Net: Profitable after fees">
                        <span class="trade-stat-mini-label">WR Net:</span>
                        <span class="trade-stat-mini-value ${statistics.win_rate >= 40 ? 'positive' : ''}">${statistics.win_rate}%</span>
                    </div>
                    <div class="trade-stat-mini" title="Trades that won in direction but lost to fees">
                        <span class="trade-stat-mini-label">Fee Eroded:</span>
                        <span class="trade-stat-mini-value negative">${statistics.fee_eroded_trades || 0}</span>
                    </div>
                    <div class="trade-stat-mini">
                        <span class="trade-stat-mini-label">Total P&L:</span>
                        <span class="trade-stat-mini-value ${statistics.total_pnl >= 0 ? 'positive' : 'negative'}">$${statistics.total_pnl.toFixed(2)}</span>
                    </div>
                    <div class="trade-stat-mini">
                        <span class="trade-stat-mini-label">Best:</span>
                        <span class="trade-stat-mini-value positive">+$${statistics.best_trade.toFixed(2)}</span>
                    </div>
                    <div class="trade-stat-mini">
                        <span class="trade-stat-mini-label">Worst:</span>
                        <span class="trade-stat-mini-value negative">$${statistics.worst_trade.toFixed(2)}</span>
                    </div>
                    ${modeBadge}
                    ${significanceBadge}
                </div>
            `;
        }
        
        html += `
            <div class="trade-history-table-wrapper">
                <table class="trade-history-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Symbol</th>
                            <th>Side</th>
                            <th>Entry</th>
                            <th>Exit</th>
                            <th>P&L</th>
                            <th>Result</th>
                            <th>Date</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        if (!trades || trades.length === 0) {
            const message = this.currentMode === 'official' 
                ? 'No official trades yet. Track record starts Jan 15, 2026.'
                : 'No trades yet. Waiting for bot to execute trades...';
            html += `
                <tr>
                    <td colspan="8" style="text-align: center; color: var(--text-muted); padding: 20px;">
                        ${message}
                    </td>
                </tr>
            `;
        } else {
            trades.forEach(trade => {
                const pnlClass = trade.pnl >= 0 ? 'trade-pnl-positive' : 'trade-pnl-negative';
                const resultClass = trade.result === 'WIN' ? 'trade-result-win' : 'trade-result-loss';
                const sideClass = trade.side === 'BUY' ? 'trade-side-buy' : 'trade-side-sell';
                const pnlSign = trade.pnl >= 0 ? '+' : '';
                
                const openDate = trade.opened_at ? new Date(trade.opened_at) : null;
                const closeDate = trade.closed_at ? new Date(trade.closed_at) : null;
                
                const dateStr = closeDate 
                    ? closeDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
                    : (openDate ? 'OPEN' : '-');
                
                const timeStr = closeDate 
                    ? closeDate.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
                    : '';
                
                const legacyBadge = trade.telemetry_source === 'LEGACY_ESTIMATED' 
                    ? '<span style="font-size: 8px; color: #ff9800; margin-left: 4px;">CAL</span>'
                    : '';
                
                html += `
                    <tr>
                        <td><span class="trade-id">#${trade.id}</span>${legacyBadge}</td>
                        <td><span class="trade-symbol">${trade.symbol}</span></td>
                        <td><span class="${sideClass}">${trade.side}</span></td>
                        <td>$${trade.entry_price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                        <td>${trade.exit_price > 0 ? '$' + trade.exit_price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '-'}</td>
                        <td class="${pnlClass}">${pnlSign}$${trade.pnl.toFixed(2)}</td>
                        <td><span class="${resultClass}">${trade.result}</span></td>
                        <td>
                            <div class="trade-date">${dateStr}</div>
                            <div class="trade-date" style="font-size: 9px; opacity: 0.7;">${timeStr}</div>
                        </td>
                    </tr>
                `;
            });
        }
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
        
        container.innerHTML = html;
    },
    
    renderError(message) {
        const container = document.getElementById(this.containerId);
        if (!container) return;
        
        container.innerHTML = `
            <div style="color: var(--accent-red); font-size: 11px; padding: 10px;">
                Error: ${message}
            </div>
        `;
    },
    
    init() {
        console.log('TradeHistory widget initialized');
        this.refresh();
    }
};

if (typeof window !== 'undefined') {
    window.TradeHistoryWidget = TradeHistoryWidget;
}
