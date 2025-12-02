/**
 * OMNIX Dashboard V6.5 - Chart Components
 * Plotly chart wrappers
 */

const OmnixCharts = (function() {
    'use strict';

    const chartConfig = {
        responsive: true,
        displayModeBar: false
    };

    const terminalColors = {
        green: '#00ff88',
        red: '#ff3366',
        blue: '#00aaff',
        cyan: '#00ffff',
        grid: '#222233',
        text: '#888899'
    };

    const dashboardColors = {
        green: '#22c55e',
        red: '#ef4444',
        blue: '#3b82f6',
        purple: '#8b5cf6',
        grid: 'rgba(255, 255, 255, 0.03)',
        text: '#64748b'
    };

    function candlestick(containerId, candles, options = {}) {
        const { theme = 'terminal' } = options;
        const colors = theme === 'terminal' ? terminalColors : dashboardColors;

        if (!candles || candles.length === 0) {
            return renderEmpty(containerId, 'No chart data available');
        }

        const trace = {
            x: candles.map(c => new Date(c.time * 1000)),
            open: candles.map(c => c.open),
            high: candles.map(c => c.high),
            low: candles.map(c => c.low),
            close: candles.map(c => c.close),
            type: 'candlestick',
            increasing: { line: { color: colors.green }, fillcolor: colors.green },
            decreasing: { line: { color: colors.red }, fillcolor: colors.red }
        };

        const layout = {
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            margin: { l: 50, r: 20, t: 20, b: 30 },
            xaxis: {
                gridcolor: colors.grid,
                color: colors.text,
                tickfont: { size: 10, family: 'JetBrains Mono' },
                rangeslider: { visible: false }
            },
            yaxis: {
                gridcolor: colors.grid,
                color: colors.text,
                tickfont: { size: 10, family: 'JetBrains Mono' },
                tickprefix: '$',
                side: 'right'
            }
        };

        Plotly.newPlot(containerId, [trace], layout, chartConfig);
    }

    function equityCurve(containerId, data, options = {}) {
        const { theme = 'dashboard' } = options;
        const colors = theme === 'terminal' ? terminalColors : dashboardColors;

        if (!data || data.length < 2) {
            return renderEmpty(containerId, 'Waiting for trading data...');
        }

        const trace = {
            x: data.map(d => d.date),
            y: data.map(d => d.equity),
            type: 'scatter',
            mode: 'lines',
            fill: 'tozeroy',
            line: { color: colors.green, width: 2, shape: 'spline' },
            fillcolor: `rgba(${theme === 'terminal' ? '0, 255, 136' : '34, 197, 94'}, 0.1)`
        };

        const layout = {
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            margin: { l: 50, r: 20, t: 10, b: 30 },
            xaxis: {
                showgrid: false,
                color: colors.text,
                tickfont: { size: 9, family: 'JetBrains Mono' }
            },
            yaxis: {
                showgrid: true,
                gridcolor: colors.grid,
                color: colors.text,
                tickfont: { size: 9, family: 'JetBrains Mono' },
                tickprefix: '$'
            },
            hovermode: 'x unified'
        };

        Plotly.newPlot(containerId, [trace], layout, chartConfig);
    }

    function pie(containerId, data, options = {}) {
        const { labels = [], colors: customColors = null, hole = 0.65, centerText = '' } = options;
        const defaultColors = [dashboardColors.purple, dashboardColors.blue];

        const total = data.reduce((sum, val) => sum + val, 0);

        if (total === 0) {
            return renderEmpty(containerId, '0');
        }

        const trace = {
            values: data,
            labels: labels,
            type: 'pie',
            hole: hole,
            marker: { colors: customColors || defaultColors },
            textinfo: 'percent',
            textfont: { color: '#fff', size: 10, family: 'JetBrains Mono' },
            hoverinfo: 'label+value+percent'
        };

        const layout = {
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            margin: { l: 10, r: 10, t: 10, b: 10 },
            showlegend: false,
            annotations: [{
                text: centerText || `${total}`,
                x: 0.5,
                y: 0.5,
                font: { size: 18, color: '#f8fafc', family: 'JetBrains Mono' },
                showarrow: false
            }]
        };

        Plotly.newPlot(containerId, [trace], layout, chartConfig);
    }

    function renderEmpty(containerId, message) {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = `
                <div style="display: flex; align-items: center; justify-content: center; height: 100%; color: var(--text-muted); font-size: 11px;">
                    ${message}
                </div>
            `;
        }
    }

    function resize(containerId) {
        Plotly.Plots.resize(containerId);
    }

    return {
        candlestick,
        equityCurve,
        pie,
        renderEmpty,
        resize,
        terminalColors,
        dashboardColors
    };
})();

if (typeof window !== 'undefined') {
    window.OmnixCharts = OmnixCharts;
}
