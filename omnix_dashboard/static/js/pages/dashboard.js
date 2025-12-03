/**
 * OMNIX Dashboard V6.5.2 - Dashboard Page Controller
 * With independent error handling per widget
 */

const DashboardApp = (function() {
    'use strict';

    let allTrades = [];
    let openPositions = [];

    async function fetchMetrics() {
        const data = await OmnixAPI.getMetrics();
        if (data.success) {
            updateMetricsUI(data.metrics);
            updateAssetsUI(data.assets);
            updateStrategiesUI(data.strategies);
            updateConnectionStatus(data.db_connected);
        }
    }

    function updateConnectionStatus(connected) {
        const statusEl = document.getElementById('db-status');
        const dotEl = document.getElementById('connection-dot');

        if (connected) {
            statusEl.textContent = 'LIVE DATA';
            statusEl.className = 'text-xs text-green-400 mono';
            dotEl.className = 'w-2 h-2 rounded-full bg-green-500 pulse-live';
        } else {
            statusEl.textContent = 'OFFLINE';
            statusEl.className = 'text-xs text-red-400 mono';
            dotEl.className = 'w-2 h-2 rounded-full bg-red-500';
        }
    }

    function updateMetricsUI(metrics) {
        const pnl = metrics.total_pnl || 0;
        const pnlEl = document.getElementById('total-pnl');
        pnlEl.textContent = OmnixUtils.formatCurrency(pnl, { showSign: true });
        pnlEl.className = `text-2xl lg:text-3xl font-bold mono ${OmnixUtils.getStatClass(pnl)}`;

        const winRate = metrics.win_rate || 0;
        const winRateEl = document.getElementById('win-rate');
        winRateEl.textContent = `${winRate.toFixed(1)}%`;
        winRateEl.className = `text-2xl lg:text-3xl font-bold mono ${winRate >= 50 ? 'stat-positive' : winRate > 0 ? 'text-yellow-500' : 'stat-neutral'}`;

        OmnixUtils.setElement('wins-losses', `${metrics.winning_trades || 0}W / ${metrics.losing_trades || 0}L`);
        OmnixUtils.setElement('sharpe-ratio', (metrics.sharpe_ratio || 0).toFixed(2));
        OmnixUtils.setElement('max-drawdown', `${(metrics.max_drawdown || 0).toFixed(1)}%`);
        OmnixUtils.setElement('profit-factor', (metrics.profit_factor || 0).toFixed(2));
        OmnixUtils.setElement('sortino-ratio', (metrics.sortino_ratio || 0).toFixed(2));
        OmnixUtils.setElement('avg-win', OmnixUtils.formatCurrency(metrics.avg_win || 0, { showSign: true }));
        OmnixUtils.setElement('avg-loss', OmnixUtils.formatCurrency(-(metrics.avg_loss || 0)));
        OmnixUtils.setElement('best-trade', OmnixUtils.formatCurrency(metrics.best_trade || 0, { showSign: true }));
        OmnixUtils.setElement('worst-trade', OmnixUtils.formatCurrency(metrics.worst_trade || 0));
        OmnixUtils.setElement('expectancy', OmnixUtils.formatCurrency(metrics.expectancy || 0, { showSign: true }));
    }

    function updateAssetsUI(assets) {
        const crypto = assets?.crypto || { trades: 0, pnl: 0, win_rate: 0 };
        const stocks = assets?.stocks || { trades: 0, pnl: 0, win_rate: 0 };

        const cryptoPnlEl = document.getElementById('crypto-pnl');
        cryptoPnlEl.textContent = OmnixUtils.formatCurrency(crypto.pnl, { showSign: true });
        cryptoPnlEl.className = `text-xl font-bold mono mb-1 ${OmnixUtils.getStatClass(crypto.pnl)}`;
        OmnixUtils.setElement('crypto-trades', `${crypto.trades} trades`);
        OmnixUtils.setElement('crypto-winrate', `${crypto.win_rate}% WR`);

        const stocksPnlEl = document.getElementById('stocks-pnl');
        stocksPnlEl.textContent = OmnixUtils.formatCurrency(stocks.pnl, { showSign: true });
        stocksPnlEl.className = `text-xl font-bold mono mb-1 ${OmnixUtils.getStatClass(stocks.pnl)}`;
        OmnixUtils.setElement('stocks-trades', `${stocks.trades} trades`);
        OmnixUtils.setElement('stocks-winrate', `${stocks.win_rate}% WR`);

        OmnixCharts.pie('market-chart', [crypto.trades || 0, stocks.trades || 0], {
            labels: ['Crypto', 'Stocks'],
            centerText: `${(crypto.trades || 0) + (stocks.trades || 0)}`
        });
    }

    function updateStrategiesUI(strategies) {
        const container = document.getElementById('strategy-list');
        if (!container) return;

        if (!strategies || Object.keys(strategies).length === 0) {
            container.innerHTML = '<div class="text-slate-600 text-xs text-center py-6 uppercase tracking-wider">No strategies yet</div>';
            return;
        }

        const sorted = Object.entries(strategies).sort((a, b) => b[1].pnl - a[1].pnl);

        container.innerHTML = sorted.map(([name, data]) => `
            <div class="flex items-center justify-between p-3 rounded-lg bg-slate-800/30 hover:bg-slate-800/50 transition border border-slate-700/30">
                <div>
                    <div class="font-medium text-sm">${name}</div>
                    <div class="text-[10px] text-slate-500 uppercase tracking-wider">${data.trades} trades | ${data.win_rate}% WR</div>
                </div>
                <div class="text-right">
                    <div class="font-semibold mono ${OmnixUtils.getStatClass(data.pnl)}">
                        ${OmnixUtils.formatCurrency(data.pnl, { showSign: true })}
                    </div>
                </div>
            </div>
        `).join('');
    }

    async function fetchTrades() {
        const data = await OmnixAPI.getTrades();
        if (data.success) {
            allTrades = data.trades || [];
            renderCombinedTable();
        }
    }

    async function fetchPositions() {
        const data = await OmnixAPI.getPositions();
        if (data.success) {
            openPositions = data.positions || [];
            renderCombinedTable();
        }
    }

    function renderCombinedTable() {
        const tbody = document.getElementById('trades-table');
        const closedTrades = allTrades.filter(t => t.closed !== null);

        OmnixUtils.setElement('open-count', `${openPositions.length} Open`);
        OmnixUtils.setElement('closed-count', `${closedTrades.length} Closed`);

        if (openPositions.length === 0 && closedTrades.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="py-12 text-center text-slate-600 text-xs uppercase tracking-wider">
                        No trading activity yet. Execute trades to see them here.
                    </td>
                </tr>
            `;
            return;
        }

        let html = '';

        if (openPositions.length > 0) {
            html += renderOpenPositionsSection();
        }

        if (closedTrades.length > 0) {
            html += renderClosedTradesSection(closedTrades);
        }

        tbody.innerHTML = html;
    }

    function renderOpenPositionsSection() {
        let html = `
            <tr>
                <td colspan="8" class="section-header section-open">
                    <span class="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
                    Open Positions (${openPositions.length})
                </td>
            </tr>
        `;

        html += openPositions.map(pos => {
            const pnlClass = OmnixUtils.getStatClass(pos.unrealized_pnl);
            const pnlPct = pos.unrealized_pnl_pct || 0;
            const date = pos.opened_at ? new Date(pos.opened_at).toLocaleDateString() : '--';

            return `
                <tr>
                    <td class="font-medium text-blue-300">${pos.symbol}</td>
                    <td><span class="text-green-400 uppercase text-xs font-semibold">${pos.side}</span></td>
                    <td>$${pos.entry_price.toLocaleString('en-US', {minimumFractionDigits: 2})}</td>
                    <td><span class="status-badge status-open">OPEN</span></td>
                    <td class="${pnlClass} font-semibold">${OmnixUtils.formatCurrency(pos.unrealized_pnl, { showSign: true })}</td>
                    <td class="${pnlClass}">${OmnixUtils.formatPercent(pnlPct, { showSign: true })}</td>
                    <td class="text-slate-500">${pos.strategy || 'Manual'}</td>
                    <td class="text-slate-600">${date}</td>
                </tr>
            `;
        }).join('');

        return html;
    }

    function renderClosedTradesSection(closedTrades) {
        let html = `
            <tr>
                <td colspan="8" class="section-header section-closed">
                    <span class="w-2 h-2 rounded-full bg-green-500"></span>
                    Closed Trades (${closedTrades.length})
                </td>
            </tr>
        `;

        html += closedTrades.map(trade => {
            const pnl = trade.pnl || 0;
            const pnlPct = trade.pnl_pct || 0;
            const pnlClass = OmnixUtils.getStatClass(pnl);
            const date = trade.closed ? new Date(trade.closed).toLocaleDateString() : '--';

            return `
                <tr>
                    <td class="font-medium">${trade.symbol}</td>
                    <td><span class="${trade.side === 'buy' ? 'text-green-400' : 'text-red-400'} uppercase text-xs font-semibold">${trade.side}</span></td>
                    <td>$${trade.entry.toLocaleString('en-US', {minimumFractionDigits: 2})}</td>
                    <td>$${trade.exit.toLocaleString('en-US', {minimumFractionDigits: 2})}</td>
                    <td class="${pnlClass} font-semibold">${OmnixUtils.formatCurrency(pnl, { showSign: true })}</td>
                    <td class="${pnlClass}">${OmnixUtils.formatPercent(pnlPct, { showSign: true })}</td>
                    <td class="text-slate-500">${trade.strategy || 'Manual'}</td>
                    <td class="text-slate-600">${date}</td>
                </tr>
            `;
        }).join('');

        return html;
    }

    async function fetchEquityCurve() {
        const data = await OmnixAPI.getEquityCurve();
        if (data.success && data.data && data.data.length > 1) {
            OmnixCharts.equityCurve('equity-chart', data.data, { theme: 'dashboard' });
        } else {
            OmnixCharts.renderEmpty('equity-chart', 'Waiting for trading data...');
        }
    }

    async function fetchSystemStatus() {
        const data = await OmnixAPI.getSystemStatus();
        if (data.success) {
            const status = data.status;
            OmnixUtils.setElement('protection-status', status.protection.drawdown_tier);
            OmnixUtils.setElement('rampup-status', status.protection.ramp_up_pct + '%');
            OmnixUtils.setElement('active-pairs', status.trading.pairs_active.map(p => p.replace('/USD', '')).join(' '));
            OmnixUtils.setElement('brand-trades-today', status.trading.trades_today);
        }
    }

    function getWidgets() {
        return [
            { name: 'metrics', fn: fetchMetrics },
            { name: 'trades', fn: fetchTrades },
            { name: 'positions', fn: fetchPositions },
            { name: 'equity', fn: fetchEquityCurve },
            { name: 'ticker', fn: () => OmnixTicker.update('crypto-ticker', 'dashboard') },
            { name: 'news', fn: () => OmnixNews.update('news-feed', 'news-source') },
            { name: 'system', fn: fetchSystemStatus },
            { name: 'riskguardian', fn: async () => { if (window.RiskGuardian) await RiskGuardian.refresh(); } },
            { name: 'adaptive', fn: async () => { if (window.AdaptiveEngine) await AdaptiveEngine.refresh(); } }
        ];
    }

    async function refreshAllData() {
        await OmnixCommon.refreshWidgets(getWidgets());
        OmnixCommon.updateTimestamp('last-update');
    }

    function init() {
        OmnixClock.start({
            timeId: 'live-time',
            dateId: 'live-date',
            timezoneId: 'timezone-badge'
        });

        if (window.RiskGuardian) {
            RiskGuardian.init('risk-guardian-widget');
        }
        
        if (window.AdaptiveEngine) {
            AdaptiveEngine.init('adaptive-engine-widget');
        }

        OmnixCommon.startAutoRefresh(refreshAllData, 10000);

        console.log('OMNIX Dashboard V6.5.2 INSTITUTIONAL+ | Performance Dashboard Active');
    }

    function destroy() {
        OmnixClock.stop();
        OmnixCommon.stopAutoRefresh();
        if (window.OmnixCharts && typeof OmnixCharts.destroyAll === 'function') {
            OmnixCharts.destroyAll();
        }
    }

    return {
        init,
        destroy,
        refreshAllData
    };
})();

function updateEquityCurve(days) {
    DashboardApp.refreshAllData();
}

document.addEventListener('DOMContentLoaded', DashboardApp.init);

if (typeof window !== 'undefined') {
    window.DashboardApp = DashboardApp;
    window.updateEquityCurve = updateEquityCurve;
}
