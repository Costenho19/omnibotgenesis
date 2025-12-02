/**
 * OMNIX Dashboard V6.5 - Terminal Page Controller
 */

const TerminalApp = (function() {
    'use strict';

    let currentSymbol = 'BTC';
    let refreshInterval = null;

    async function fetchMetrics() {
        try {
            const data = await OmnixAPI.getMetrics();
            if (data.success) {
                const m = data.metrics;
                const pnlEl = document.getElementById('total-pnl');
                pnlEl.textContent = `${m.total_pnl >= 0 ? '+' : ''}$${m.total_pnl.toFixed(2)}`;
                pnlEl.className = `header-stat-value ${m.total_pnl >= 0 ? 'positive' : 'negative'}`;

                OmnixUtils.setElement('win-rate', `${m.win_rate.toFixed(1)}%`);
                OmnixUtils.setElement('trades-count', m.total_trades);
                OmnixUtils.setElement('max-dd', `${m.max_drawdown.toFixed(1)}%`);
                OmnixUtils.setElement('sharpe', m.sharpe_ratio.toFixed(2));
                OmnixUtils.setElement('sortino', m.sortino_ratio.toFixed(2));
                OmnixUtils.setElement('profit-factor', m.profit_factor.toFixed(2));
                OmnixUtils.setElement('expectancy', `$${m.expectancy.toFixed(2)}`);
            }
        } catch (error) {
            console.error('Metrics error:', error);
        }
    }

    async function loadChart(symbol) {
        currentSymbol = symbol;
        try {
            const data = await OmnixAPI.getOHLC(symbol);
            if (data.success && data.candles.length > 0) {
                OmnixCharts.candlestick('candlestick-chart', data.candles, { theme: 'terminal' });
                const titleEl = document.querySelector('.panel-title');
                if (titleEl) {
                    titleEl.innerHTML = `📈 ${symbol}/USD - 1H Candlestick`;
                }
            }
        } catch (error) {
            console.error('Chart error:', error);
        }
    }

    async function fetchEquityCurve() {
        try {
            const data = await OmnixAPI.getEquityCurve();
            if (data.success && data.data.length > 1) {
                OmnixCharts.equityCurve('equity-chart', data.data, { theme: 'terminal' });
            } else {
                OmnixCharts.renderEmpty('equity-chart', 'Accumulating data...');
            }
        } catch (error) {
            console.error('Equity curve error:', error);
        }
    }

    function updateLastRefresh() {
        const el = document.getElementById('last-update');
        if (el) {
            el.textContent = new Date().toLocaleTimeString('en-US', { hour12: false });
        }
    }

    async function refreshAll() {
        await Promise.all([
            OmnixTicker.update('ticker-row', 'terminal'),
            OmnixSignals.update('signals-list'),
            OmnixVolume.update('volume-bars'),
            OmnixNews.update('news-feed', 'news-source'),
            OmnixNews.updateFinnhub('news-feed', 'news-source'),
            OmnixFearGreed.update(),
            fetchMetrics(),
            fetchEquityCurve(),
            loadChart(currentSymbol)
        ]);
        updateLastRefresh();
    }

    function init() {
        OmnixClock.start({
            timeId: 'clock-time',
            dateId: 'clock-date'
        });

        refreshAll();
        refreshInterval = setInterval(refreshAll, 10000);

        console.log('OMNIX Terminal V6.4 INSTITUTIONAL+ | Trading Terminal Active');
    }

    function destroy() {
        OmnixClock.stop();
        if (refreshInterval) {
            clearInterval(refreshInterval);
            refreshInterval = null;
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
