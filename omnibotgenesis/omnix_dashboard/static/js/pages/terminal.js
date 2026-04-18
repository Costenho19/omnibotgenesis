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
            const sm = OmnixUtils.safeMetric;
            const rv = OmnixUtils.renderMetricValue;

            const pnl = sm(m.total_pnl);
            const pnlEl = document.getElementById('total-pnl');
            pnlEl.textContent = rv(pnl, v => `${v >= 0 ? '+' : ''}$${v.toFixed(2)}`);
            pnlEl.className = `header-stat-value ${pnl !== null && pnl >= 0 ? 'positive' : pnl !== null ? 'negative' : ''}`;

            const winRateDir = sm(m.win_rate_directional);
            const winRateNet = sm(m.win_rate_net) !== null ? sm(m.win_rate_net) : sm(m.win_rate);
            OmnixUtils.setElement('win-rate-dir', rv(winRateDir, v => `${v.toFixed(1)}%`));
            OmnixUtils.setElement('win-rate-net', rv(winRateNet, v => `${v.toFixed(1)}%`));
            if (document.getElementById('win-rate')) {
                OmnixUtils.setElement('win-rate', rv(sm(m.win_rate), v => `${v.toFixed(1)}%`));
            }
            OmnixUtils.setElement('trades-count', rv(sm(m.total_trades), v => v));
            OmnixUtils.setElement('max-dd', rv(sm(m.max_drawdown), v => `${v.toFixed(1)}%`));
            OmnixUtils.setElement('sharpe', rv(sm(m.sharpe_ratio), v => v.toFixed(2)));
            OmnixUtils.setElement('sortino', rv(sm(m.sortino_ratio), v => v.toFixed(2)));
            OmnixUtils.setElement('profit-factor', rv(sm(m.profit_factor), v => v.toFixed(2)));
            OmnixUtils.setElement('expectancy', rv(sm(m.expectancy), v => `$${v.toFixed(2)}`));
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
            { name: 'equitycomparison', fn: async () => { if (window.EquityComparison) await EquityComparison.refresh(); } },
            { name: 'healthscore', fn: async () => { if (window.HealthScoreWidget) await HealthScoreWidget.refresh(); } },
            { name: 'livestatus', fn: async () => { if (window.LiveStatusWidget) await LiveStatusWidget.refresh(); } },
            { name: 'quickinsights', fn: async () => { if (window.QuickInsightsWidget) await QuickInsightsWidget.refresh(); } },
            { name: 'calibrationprogress', fn: async () => { if (window.CalibrationProgressWidget) await CalibrationProgressWidget.refresh(); } },
            { name: 'recommendedactions', fn: async () => { if (window.RecommendedActionsWidget) await RecommendedActionsWidget.refresh(); } }
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
        
        if (window.HealthScoreWidget) {
            HealthScoreWidget.init('health-score-widget');
        }
        
        if (window.LiveStatusWidget) {
            LiveStatusWidget.init('live-status-widget');
        }
        
        if (window.QuickInsightsWidget) {
            QuickInsightsWidget.init('quick-insights-widget');
        }
        
        if (window.CalibrationProgressWidget) {
            CalibrationProgressWidget.init('calibration-progress-widget');
        }
        
        if (window.RecommendedActionsWidget) {
            RecommendedActionsWidget.init('recommended-actions-widget');
        }

        OmnixCommon.startAutoRefresh(refreshAll, 10000);

        console.log('OMNIX Decision Governance | Trading Terminal Active');
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
