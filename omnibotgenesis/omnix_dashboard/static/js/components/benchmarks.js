/**
 * OMNIX Benchmark Overlay V6.5
 * Toggle overlay for BTC and SPY benchmarks on equity chart.
 * Uses Plotly.react() for efficient delta updates.
 */
const BenchmarkOverlay = (function() {
    'use strict';

    let _chartId = null;
    let _btcEnabled = false;
    let _spyEnabled = false;
    let _btcData = null;
    let _spyData = null;
    let _isLoading = false;

    const COLORS = {
        btc: '#F7931A',
        spy: '#4A90D9'
    };

    async function fetchBenchmarks(days = 30) {
        if (_isLoading) return null;
        _isLoading = true;

        try {
            const response = await OmnixAPI.fetchWithRetry('/api/benchmarks?days=' + days);
            if (response && response.success) {
                _btcData = response.benchmarks.btc || [];
                _spyData = response.benchmarks.spy || [];
                return response;
            }
            return null;
        } catch (error) {
            console.error('[BenchmarkOverlay] Error fetching benchmarks:', error);
            return null;
        } finally {
            _isLoading = false;
        }
    }

    function buildTrace(data, name, color) {
        if (!data || data.length === 0) return null;

        return {
            x: data.map(d => d.date),
            y: data.map(d => d.pct_change),
            type: 'scatter',
            mode: 'lines',
            name: name,
            line: {
                color: color,
                width: 2,
                dash: 'dot'
            },
            yaxis: 'y2',
            hovertemplate: '%{y:.2f}%<extra>' + name + '</extra>'
        };
    }

    function updateChart() {
        if (!_chartId) return;

        const chartDiv = document.getElementById(_chartId);
        if (!chartDiv || !chartDiv.data) return;

        const portfolioTrace = chartDiv.data.find(trace => trace.name === 'Portfolio');
        if (!portfolioTrace) {
            console.warn('[BenchmarkOverlay] No Portfolio trace found in chart');
            return;
        }

        const newTraces = [portfolioTrace];

        if (_btcEnabled && _btcData && _btcData.length > 0) {
            const btcTrace = buildTrace(_btcData, 'BTC', COLORS.btc);
            if (btcTrace) newTraces.push(btcTrace);
        }

        if (_spyEnabled && _spyData && _spyData.length > 0) {
            const spyTrace = buildTrace(_spyData, 'SPY', COLORS.spy);
            if (spyTrace) newTraces.push(spyTrace);
        }

        const needsSecondAxis = _btcEnabled || _spyEnabled;
        const layout = Object.assign({}, chartDiv.layout);

        if (needsSecondAxis) {
            layout.yaxis2 = {
                title: 'Benchmark %',
                overlaying: 'y',
                side: 'right',
                showgrid: false,
                zeroline: true,
                zerolinecolor: 'rgba(255,255,255,0.2)',
                tickformat: '.1f',
                ticksuffix: '%',
                font: { color: '#888' }
            };
            layout.legend = {
                x: 0,
                y: 1.1,
                orientation: 'h',
                font: { size: 10, color: '#888' }
            };
        } else {
            delete layout.yaxis2;
        }

        Plotly.react(_chartId, newTraces, layout);
    }

    async function toggleBTC(enabled) {
        _btcEnabled = enabled;

        if (enabled && (!_btcData || _btcData.length === 0)) {
            await fetchBenchmarks();
        }

        updateChart();
        updateToggleUI('btc', enabled);
    }

    async function toggleSPY(enabled) {
        _spyEnabled = enabled;

        if (enabled && (!_spyData || _spyData.length === 0)) {
            await fetchBenchmarks();
        }

        updateChart();
        updateToggleUI('spy', enabled);
    }

    function updateToggleUI(type, enabled) {
        const toggle = document.getElementById('benchmark-toggle-' + type);
        if (toggle) {
            toggle.classList.toggle('active', enabled);
            toggle.setAttribute('aria-checked', enabled);
        }
    }

    function createToggleHTML() {
        return `
            <div class="benchmark-toggles" style="display: flex; gap: 6px; margin-left: 8px;">
                <button id="benchmark-toggle-btc" 
                        class="benchmark-toggle" 
                        aria-checked="false"
                        title="Overlay BTC performance">
                    <span class="toggle-indicator" style="background: ${COLORS.btc}"></span>
                    <span class="toggle-label">BTC</span>
                </button>
                <button id="benchmark-toggle-spy" 
                        class="benchmark-toggle" 
                        aria-checked="false"
                        title="Overlay SPY performance">
                    <span class="toggle-indicator" style="background: ${COLORS.spy}"></span>
                    <span class="toggle-label">SPY</span>
                </button>
            </div>
        `;
    }

    function attachEventListeners() {
        const btcToggle = document.getElementById('benchmark-toggle-btc');
        const spyToggle = document.getElementById('benchmark-toggle-spy');

        if (btcToggle) {
            btcToggle.addEventListener('click', function() {
                toggleBTC(!_btcEnabled);
            });
        }

        if (spyToggle) {
            spyToggle.addEventListener('click', function() {
                toggleSPY(!_spyEnabled);
            });
        }
    }

    function init(chartId, containerId) {
        _chartId = chartId;

        const container = document.getElementById(containerId);
        if (container) {
            const existingToggles = container.querySelector('.benchmark-toggles');
            if (!existingToggles) {
                const flexContainer = container.querySelector('.flex') || container.querySelector('div[class*="flex"]');
                if (flexContainer) {
                    flexContainer.insertAdjacentHTML('beforeend', createToggleHTML());
                } else {
                    container.insertAdjacentHTML('beforeend', createToggleHTML());
                }
                attachEventListeners();
            }
        }

        console.log('[BenchmarkOverlay] Initialized for chart:', chartId);
    }

    async function refresh() {
        if (_btcEnabled || _spyEnabled) {
            await fetchBenchmarks();
            updateChart();
        }
    }

    return {
        init: init,
        refresh: refresh,
        toggleBTC: toggleBTC,
        toggleSPY: toggleSPY,
        isEnabled: function() { return _btcEnabled || _spyEnabled; }
    };
})();

if (typeof window !== 'undefined') {
    window.BenchmarkOverlay = BenchmarkOverlay;
}
