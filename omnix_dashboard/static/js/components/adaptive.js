const AdaptiveEngine = (function() {
    'use strict';

    const REGIME_COLORS = {
        'TRENDING': '#00d4aa',
        'RANGING': '#ffc107',
        'VOLATILE': '#ff6b6b'
    };

    const REGIME_ICONS = {
        'TRENDING': '📈',
        'RANGING': '↔️',
        'VOLATILE': '⚡'
    };

    function renderRegimeBadge(regime, confidence) {
        const color = REGIME_COLORS[regime] || '#6c757d';
        const icon = REGIME_ICONS[regime] || '❓';
        const confidencePct = Math.round(confidence * 100);
        
        return `
            <div class="adaptive-regime-badge" style="border-color: ${color}">
                <span class="regime-icon">${icon}</span>
                <span class="regime-name" style="color: ${color}">${regime}</span>
                <span class="regime-confidence">${confidencePct}%</span>
            </div>
        `;
    }

    function renderMainDriver(mainDriver) {
        if (!mainDriver || !mainDriver.name) {
            return '';
        }

        const isQuantum = mainDriver.is_quantum;
        const icon = isQuantum ? '⚛️' : '🧠';
        const color = isQuantum ? '#00d4aa' : '#ffc107';
        const weightPct = Math.round(mainDriver.weight * 100);
        
        return `
            <div class="main-driver-section" style="margin-bottom: 12px;">
                <div class="main-driver-badge" style="
                    background: linear-gradient(135deg, ${color}22 0%, ${color}11 100%);
                    border: 1px solid ${color};
                    border-radius: 8px;
                    padding: 10px 14px;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                ">
                    <span class="driver-icon" style="font-size: 24px;">${icon}</span>
                    <div class="driver-info">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span class="driver-name" style="
                                font-weight: 700;
                                color: ${color};
                                font-size: 13px;
                            ">${mainDriver.name.replace(/_/g, ' ')}</span>
                            <span class="driver-badge" style="
                                background: ${color};
                                color: #000;
                                padding: 2px 8px;
                                border-radius: 4px;
                                font-size: 9px;
                                font-weight: 700;
                                letter-spacing: 0.5px;
                            ">MAIN DRIVER</span>
                            <span class="driver-weight" style="
                                color: #fff;
                                font-weight: 600;
                            ">${weightPct}%</span>
                        </div>
                        <div class="driver-description" style="
                            font-size: 10px;
                            color: #888;
                            margin-top: 4px;
                        " title="${mainDriver.description}">${mainDriver.description}</div>
                    </div>
                </div>
            </div>
        `;
    }

    function renderStrategyMatrix(strategies) {
        if (!strategies || Object.keys(strategies).length === 0) {
            return '<div class="no-data">No strategy data</div>';
        }

        let html = '<div class="strategy-matrix">';
        
        for (const [name, data] of Object.entries(strategies)) {
            const weight = data.weight || 0;
            const winRate = data.win_rate || 0;
            const trades = data.trades_24h || 0;
            const status = data.status || 'UNKNOWN';
            
            const barWidth = Math.round(weight * 100);
            const statusClass = status === 'ACTIVE' ? 'status-active' : 'status-reduced';
            const displayName = name.replace(/_/g, ' ').substring(0, 15);
            
            html += `
                <div class="strategy-row">
                    <div class="strategy-name" title="${name}">${displayName}</div>
                    <div class="strategy-bar-container">
                        <div class="strategy-bar" style="width: ${barWidth}%"></div>
                    </div>
                    <div class="strategy-weight">${(weight * 100).toFixed(0)}%</div>
                    <div class="strategy-status ${statusClass}">${status}</div>
                </div>
            `;
        }
        
        html += '</div>';
        return html;
    }

    function renderKernelParams(params) {
        if (!params) {
            return '<div class="no-data">No kernel params</div>';
        }

        return `
            <div class="kernel-params">
                <div class="param-item">
                    <span class="param-label">τ (tau)</span>
                    <span class="param-value">${params.tau}h</span>
                </div>
                <div class="param-item">
                    <span class="param-label">ε (epsilon)</span>
                    <span class="param-value">${params.epsilon}</span>
                </div>
                <div class="param-item">
                    <span class="param-label">Ω (omega)</span>
                    <span class="param-value">${params.omega}</span>
                </div>
                <div class="param-item">
                    <span class="param-label">Window</span>
                    <span class="param-value">${params.memory_window}h</span>
                </div>
            </div>
        `;
    }

    function renderCalibrationStatus(calibration) {
        if (!calibration) {
            return '<div class="no-data">No calibration data</div>';
        }

        const autoStatus = calibration.auto_calibration ? 'AUTO' : 'MANUAL';
        const autoClass = calibration.auto_calibration ? 'auto-enabled' : 'auto-disabled';

        return `
            <div class="calibration-status">
                <div class="calib-row">
                    <span class="calib-label">Mode</span>
                    <span class="calib-value ${autoClass}">${autoStatus}</span>
                </div>
                <div class="calib-row">
                    <span class="calib-label">Strategies</span>
                    <span class="calib-value">${calibration.strategies_calibrated}</span>
                </div>
            </div>
        `;
    }

    function renderMetrics(metrics) {
        if (!metrics) {
            return '<div class="no-data">No metrics</div>';
        }

        return `
            <div class="adaptive-metrics">
                <div class="metric-card">
                    <div class="metric-value">${(metrics.signal_quality_avg * 100).toFixed(0)}%</div>
                    <div class="metric-label">Signal Quality</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${(metrics.regime_accuracy_7d * 100).toFixed(0)}%</div>
                    <div class="metric-label">Regime Accuracy</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${(metrics.calibration_success_rate * 100).toFixed(0)}%</div>
                    <div class="metric-label">Calib Success</div>
                </div>
            </div>
        `;
    }

    function render(containerId, data) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.warn('AdaptiveEngine: Container not found:', containerId);
            return;
        }

        if (!data || !data.success) {
            container.innerHTML = `
                <div class="adaptive-widget adaptive-error">
                    <div class="widget-header">
                        <span class="widget-icon">🧠</span>
                        <span class="widget-title">ADAPTIVE ENGINE ${data?.adaptive?.version || 'V6.5'}</span>
                        <span class="widget-status error">ERROR</span>
                    </div>
                    <div class="widget-body">
                        <div class="error-message">Unable to load adaptive engine data</div>
                    </div>
                </div>
            `;
            return;
        }

        const adaptive = data.adaptive;
        const regime = adaptive.regime || {};
        const calibration = adaptive.calibration || {};
        const strategies = adaptive.strategy_weights || {};
        const kernelParams = adaptive.kernel_params || {};
        const metrics = adaptive.performance_metrics || {};
        const mainDriver = adaptive.main_driver || null;

        container.innerHTML = `
            <div class="adaptive-widget">
                <div class="widget-header">
                    <span class="widget-icon">🧠</span>
                    <span class="widget-title">ADAPTIVE ENGINE ${adaptive.version || 'V6.5'}</span>
                    <span class="widget-status ${adaptive.status === 'ACTIVE' ? 'active' : 'inactive'}">${adaptive.status || 'UNKNOWN'}</span>
                </div>
                
                ${renderMainDriver(mainDriver)}
                
                <div class="widget-section">
                    <div class="section-title">Trading Regime <span class="section-hint" title="Based on system win rate. Different from 'Market Trend' which measures price direction.">(Performance)</span></div>
                    ${renderRegimeBadge(regime.current, regime.confidence)}
                </div>
                
                <div class="widget-section">
                    <div class="section-title">Strategy Weights</div>
                    ${renderStrategyMatrix(strategies)}
                </div>
                
                <div class="widget-row">
                    <div class="widget-col">
                        <div class="section-title">Kernel Parameters</div>
                        ${renderKernelParams(kernelParams)}
                    </div>
                    <div class="widget-col">
                        <div class="section-title">Calibration</div>
                        ${renderCalibrationStatus(calibration)}
                    </div>
                </div>
                
                <div class="widget-section">
                    <div class="section-title">Performance Metrics</div>
                    ${renderMetrics(metrics)}
                </div>
                
                <div class="widget-footer">
                    <span class="source-badge">${adaptive.source || 'Unknown'}</span>
                    <span class="timestamp">${new Date(adaptive.timestamp).toLocaleTimeString()}</span>
                </div>
            </div>
        `;
    }

    async function refresh(containerId) {
        try {
            const response = await OmnixAPI.fetchWithRetry('/api/system/adaptive');
            render(containerId || 'adaptive-engine-widget', response);
            return response;
        } catch (error) {
            console.error('AdaptiveEngine refresh error:', error);
            render(containerId || 'adaptive-engine-widget', { success: false });
            throw error;
        }
    }

    function init(containerId) {
        console.log('AdaptiveEngine widget initialized');
        refresh(containerId);
    }

    return {
        init: init,
        refresh: refresh,
        render: render
    };
})();

if (typeof window !== 'undefined') {
    window.AdaptiveEngine = AdaptiveEngine;
}
