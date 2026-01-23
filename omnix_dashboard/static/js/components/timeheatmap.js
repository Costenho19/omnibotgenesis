(function() {
    'use strict';

    const REFRESH_INTERVAL = 60000;
    const API_KEY = 'omnix-dashboard-2024';

    const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

    function getColor(pnl, maxPnl, minPnl) {
        if (pnl === 0) return 'rgba(100, 100, 100, 0.3)';
        if (pnl > 0) {
            const intensity = Math.min(1, pnl / Math.max(1, maxPnl));
            return `rgba(16, 185, 129, ${0.3 + intensity * 0.7})`;
        } else {
            const intensity = Math.min(1, Math.abs(pnl) / Math.max(1, Math.abs(minPnl)));
            return `rgba(239, 68, 68, ${0.3 + intensity * 0.7})`;
        }
    }

    function formatPnl(value) {
        if (value >= 0) return `+$${value.toFixed(0)}`;
        return `-$${Math.abs(value).toFixed(0)}`;
    }

    async function fetchTimeHeatmap() {
        try {
            const response = await fetch('/api/metrics/time-heatmap', {
                headers: { 'X-API-Key': API_KEY }
            });
            const data = await response.json();
            if (data.success) {
                renderTimeHeatmap(data);
            }
        } catch (error) {
            console.error('Time heatmap fetch error:', error);
        }
    }

    function renderTimeHeatmap(data) {
        const container = document.getElementById('time-heatmap-widget');
        if (!container) return;

        const heatmap = data.heatmap || [];
        const maxPnl = Math.max(...heatmap.map(h => h.pnl), 1);
        const minPnl = Math.min(...heatmap.map(h => h.pnl), -1);

        const grid = {};
        heatmap.forEach(h => {
            if (!grid[h.day]) grid[h.day] = {};
            grid[h.day][h.hour] = h;
        });

        const hours = [0, 3, 6, 9, 12, 15, 18, 21];

        let gridHtml = '<div class="heatmap-grid">';
        gridHtml += '<div class="heatmap-row header"><div class="heatmap-cell label"></div>';
        hours.forEach(h => {
            gridHtml += `<div class="heatmap-cell header">${h}h</div>`;
        });
        gridHtml += '</div>';

        for (let day = 0; day < 7; day++) {
            gridHtml += `<div class="heatmap-row"><div class="heatmap-cell label">${dayNames[day]}</div>`;
            hours.forEach(hour => {
                const cell = grid[day] && grid[day][hour];
                const pnl = cell ? cell.pnl : 0;
                const trades = cell ? cell.trades : 0;
                const winRate = cell ? cell.win_rate : 0;
                const color = getColor(pnl, maxPnl, minPnl);
                const tooltip = `${dayNames[day]} ${hour}:00\nP&L: ${formatPnl(pnl)}\nTrades: ${trades}\nWin Rate: ${winRate}%`;
                gridHtml += `<div class="heatmap-cell data" style="background:${color}" title="${tooltip}">${trades > 0 ? trades : ''}</div>`;
            });
            gridHtml += '</div>';
        }
        gridHtml += '</div>';

        const best = data.best_time || {};
        const worst = data.worst_time || {};

        container.innerHTML = `
            <div class="time-heatmap-header">
                <span class="widget-icon">🕐</span>
                <span class="widget-title">Time Heatmap</span>
                <span class="widget-badge">P&L by Hour</span>
            </div>
            <div class="time-heatmap-body">
                ${gridHtml}
                <div class="heatmap-insights">
                    <div class="insight best">
                        <span class="insight-label">Best</span>
                        <span class="insight-value">${best.day || '-'} ${best.hour || '-'}</span>
                        <span class="insight-pnl positive">${formatPnl(best.pnl || 0)}</span>
                    </div>
                    <div class="insight worst">
                        <span class="insight-label">Worst</span>
                        <span class="insight-value">${worst.day || '-'} ${worst.hour || '-'}</span>
                        <span class="insight-pnl negative">${formatPnl(worst.pnl || 0)}</span>
                    </div>
                </div>
            </div>
        `;
    }

    function init() {
        fetchTimeHeatmap();
        setInterval(fetchTimeHeatmap, REFRESH_INTERVAL);
        console.log('TimeHeatmapWidget initialized');
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
