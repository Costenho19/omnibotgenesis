/**
 * OMNIX Dashboard - Terminal Page Controller
 * With independent error handling per widget
 * Version: Synced with omnix_config.VERSION_BANNER
 */

const TerminalApp = (function() {
    'use strict';

    let currentSymbol = 'BTC';

    async function fetchMetrics() {
        const data = await OmnixAPI.getMetrics();
        if (data.success) {
            const m = data.metrics;
            const pnlEl = document.getElementById('total-pnl');
            pnlEl.textContent = `${m.total_pnl >= 0 ? '+' : ''}$${m.total_pnl.toFixed(2)}`;
            pnlEl.className = `header-stat-value ${m.total_pnl >= 0 ? 'positive' : 'negative'}`;

            const winRateDir = m.win_rate_directional || 0;
            const winRateNet = m.win_rate_net || m.win_rate || 0;
            OmnixUtils.setElement('win-rate-dir', `${winRateDir.toFixed(1)}%`);
            OmnixUtils.setElement('win-rate-net', `${winRateNet.toFixed(1)}%`);
            if (document.getElementById('win-rate')) {
                OmnixUtils.setElement('win-rate', `${m.win_rate.toFixed(1)}%`);
            }
            OmnixUtils.setElement('trades-count', m.total_trades);
            OmnixUtils.setElement('max-dd', `${m.max_drawdown.toFixed(1)}%`);
            OmnixUtils.setElement('sharpe', m.sharpe_ratio.toFixed(2));
            OmnixUtils.setElement('sortino', m.sortino_ratio.toFixed(2));
            OmnixUtils.setElement('profit-factor', m.profit_factor.toFixed(2));
            OmnixUtils.setElement('expectancy', `$${m.expectancy.toFixed(2)}`);
        }
    }

    async function loadChart(symbol) {
        currentSymbol = symbol;
        const data = await OmnixAPI.getOHLC(symbol);
        if (data.success && data.candles && data.candles.length > 0) {
            OmnixCharts.candlestick('candlestick-chart', data.candles, { theme: 'terminal' });
            const titleEl = document.querySelector('.panel-title');
            if (titleEl) {
                titleEl.innerHTML = `📈 ${symbol}/USD - 1H Candlestick`;
            }
        }
    }

    async function fetchEquityCurve() {
        const data = await OmnixAPI.getEquityCurve();
        if (data.success && data.data && data.data.length > 1) {
            OmnixCharts.equityCurve('equity-chart', data.data, { theme: 'terminal' });
        } else {
            OmnixCharts.renderEmpty('equity-chart', 'Accumulating data...');
        }
    }

    function getWidgets() {
        return [
            { name: 'metrics', fn: fetchMetrics },
            { name: 'chart', fn: () => loadChart(currentSymbol) },
            { name: 'equity', fn: fetchEquityCurve },
            { name: 'ticker', fn: () => OmnixTicker.update('ticker-row', 'terminal') },
            { name: 'signals', fn: () => OmnixSignals.update('signals-list') },
            { name: 'volume', fn: () => OmnixVolume.update('volume-bars') },
            { name: 'news', fn: () => OmnixNews.update('news-feed', 'news-source') },
            { name: 'finnhub', fn: () => OmnixNews.updateFinnhub('news-feed', 'news-source') },
            { name: 'feargreed', fn: () => OmnixFearGreed.update() },
            { name: 'riskguardian', fn: async () => { if (window.RiskGuardian) await RiskGuardian.refresh(); } },
            { name: 'adaptive', fn: async () => { if (window.AdaptiveEngine) await AdaptiveEngine.refresh(); } },
            { name: 'tradehistory', fn: async () => { if (window.TradeHistoryWidget) await TradeHistoryWidget.refresh(); } },
            { name: 'sessions', fn: async () => { if (window.SessionsWidget) await SessionsWidget.refresh(); } },
            { name: 'equitycomparison', fn: async () => { if (window.EquityComparison) await EquityComparison.refresh(); } }
        ];
    }

    async function refreshAll() {
        await OmnixCommon.refreshWidgets(getWidgets());
        OmnixCommon.updateTimestamp('last-update');
    }

    function init() {
        OmnixClock.start({
            timeId: 'clock-time',
            dateId: 'clock-date'
        });

        if (window.RiskGuardian) {
            RiskGuardian.init('risk-guardian-widget');
        }
        
        if (window.AdaptiveEngine) {
            AdaptiveEngine.init('adaptive-engine-widget');
        }
        
        if (window.BenchmarkOverlay) {
            BenchmarkOverlay.init('equity-chart', 'equity-panel-header');
        }
        
        if (window.TradeHistoryWidget) {
            TradeHistoryWidget.init();
        }
        
        if (window.SessionsWidget) {
            SessionsWidget.init();
        }
        
        if (window.EquityComparison) {
            EquityComparison.init();
        }

        OmnixCommon.startAutoRefresh(refreshAll, 10000);

        console.log('OMNIX Terminal V6.5.4d INSTITUTIONAL+ | Trading Terminal Active');
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
        loadChart,
        refreshAll
    };
})();

document.addEventListener('DOMContentLoaded', TerminalApp.init);

if (typeof window !== 'undefined') {
    window.TerminalApp = TerminalApp;
    window.loadChart = TerminalApp.loadChart;
}
