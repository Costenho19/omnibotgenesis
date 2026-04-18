const HealthScoreWidget = (function() {
    'use strict';

    let containerId = 'health-score-widget';
    let lastData = null;

    function init(id) {
        containerId = id || containerId;
        console.log('HealthScoreWidget initialized');
    }

    async function refresh() {
        try {
            const response = await OmnixAPI.fetchWithRetry('/api/system/health-score');
            if (response.success) {
                lastData = response;
                render(response);
            }
        } catch (error) {
            console.error('HealthScore refresh error:', error);
            renderError();
        }
    }

    function render(data) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const { health_score, status, color, components } = data;
        const circumference = 2 * Math.PI * 45;
        const offset = circumference - (health_score / 100) * circumference;

        container.innerHTML = `
            <div class="panel-header">
                <span class="panel-title">System Health</span>
                <span class="panel-badge" style="background: ${color}20; color: ${color}; border: 1px solid ${color};">${status}</span>
            </div>
            <div class="health-score-container">
                <div class="health-score-circle">
                    <svg viewBox="0 0 100 100" class="health-svg">
                        <circle cx="50" cy="50" r="45" fill="none" stroke="#1a1f2e" stroke-width="8"/>
                        <circle cx="50" cy="50" r="45" fill="none" stroke="${color}" stroke-width="8"
                                stroke-dasharray="${circumference}" stroke-dashoffset="${offset}"
                                stroke-linecap="round" transform="rotate(-90 50 50)"
                                style="transition: stroke-dashoffset 0.5s ease;"/>
                    </svg>
                    <div class="health-score-value" style="color: ${color};">
                        <span class="score-number">${Math.round(health_score)}</span>
                        <span class="score-label">/ 100</span>
                    </div>
                </div>
                <div class="health-components">
                    ${renderComponent(components.risk_controls)}
                    ${renderComponent(components.data_quality)}
                    ${renderComponent(components.win_rate)}
                    ${renderComponent(components.uptime)}
                </div>
            </div>
        `;
    }

    function renderComponent(comp) {
        const barColor = comp.score >= 80 ? '#00d4aa' : comp.score >= 60 ? '#ffc107' : '#ff6b6b';
        return `
            <div class="health-component">
                <div class="component-header">
                    <span class="component-label">${comp.label}</span>
                    <span class="component-score" style="color: ${barColor};">${comp.score.toFixed(0)}%</span>
                </div>
                <div class="component-bar">
                    <div class="component-bar-fill" style="width: ${comp.score}%; background: ${barColor};"></div>
                </div>
                <div class="component-detail">${comp.detail}</div>
            </div>
        `;
    }

    function renderError() {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = `
            <div class="panel-header">
                <span class="panel-title">System Health</span>
                <span class="panel-badge" style="background: #ff6b6b20; color: #ff6b6b;">OFFLINE</span>
            </div>
            <div style="padding: 20px; text-align: center; color: var(--text-muted);">
                Unable to calculate health score
            </div>
        `;
    }

    return {
        init,
        refresh,
        render,
        getData: () => lastData
    };
})();

if (typeof window !== 'undefined') {
    window.HealthScoreWidget = HealthScoreWidget;
}
