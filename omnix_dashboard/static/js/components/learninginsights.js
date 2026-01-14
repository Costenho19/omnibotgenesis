(function() {
    'use strict';

    const REFRESH_INTERVAL = 30000;
    const API_KEY = 'omnix-dashboard-2024';

    function formatCapital(value) {
        if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`;
        if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
        if (value >= 1e3) return `$${(value / 1e3).toFixed(1)}K`;
        return `$${value.toFixed(0)}`;
    }

    function getPriorityClass(priority) {
        if (priority === 'HIGH') return 'priority-high';
        if (priority === 'MEDIUM') return 'priority-medium';
        return 'priority-low';
    }

    function getVetoIcon(type) {
        const icons = {
            'BLACK_SWAN': '🦢',
            'COHERENCE_GATE': '🚧',
            'MC': '🎲',
            'RMS': '🛡️',
            'UNKNOWN': '❓'
        };
        return icons[type] || '⚠️';
    }

    async function fetchLearningInsights() {
        try {
            const response = await fetch('/api/learning/insights', {
                headers: { 'X-API-Key': API_KEY }
            });
            const data = await response.json();
            if (data.success) {
                renderLearningInsights(data);
            }
        } catch (error) {
            console.error('Learning insights fetch error:', error);
        }
    }

    function renderLearningInsights(data) {
        const container = document.getElementById('learning-insights-widget');
        if (!container) return;

        const summary = data.summary || {};
        const vetoEffectiveness = data.veto_effectiveness || [];
        const recommendations = data.recommendations || [];
        const topSymbols = data.top_vetoed_symbols || [];

        let vetoHtml = '<div class="veto-list">';
        vetoEffectiveness.slice(0, 4).forEach(v => {
            const icon = getVetoIcon(v.type);
            vetoHtml += `
                <div class="veto-item">
                    <span class="veto-icon">${icon}</span>
                    <span class="veto-type">${v.type}</span>
                    <span class="veto-count">${v.total.toLocaleString()}</span>
                    <span class="veto-capital">${formatCapital(v.total_blocked)}</span>
                </div>
            `;
        });
        vetoHtml += '</div>';

        let recsHtml = '<div class="recommendations-list">';
        recommendations.forEach(r => {
            const priorityClass = getPriorityClass(r.priority);
            recsHtml += `
                <div class="recommendation ${priorityClass}">
                    <div class="rec-header">
                        <span class="rec-title">${r.title}</span>
                        <span class="rec-priority">${r.priority}</span>
                    </div>
                    <div class="rec-message">${r.message}</div>
                </div>
            `;
        });
        recsHtml += '</div>';

        let symbolsHtml = '';
        if (topSymbols.length > 0) {
            symbolsHtml = '<div class="top-symbols"><span class="symbols-label">Más bloqueados:</span>';
            topSymbols.slice(0, 3).forEach(s => {
                symbolsHtml += `<span class="symbol-chip">${s.symbol} (${s.veto_count})</span>`;
            });
            symbolsHtml += '</div>';
        }

        container.innerHTML = `
            <div class="learning-header">
                <span class="widget-icon">🧠</span>
                <span class="widget-title">Learning Engine</span>
                <span class="widget-badge">Shadow Portfolio</span>
            </div>
            <div class="learning-body">
                <div class="learning-summary">
                    <div class="summary-stat">
                        <span class="stat-value">${(summary.total_vetos_7d || 0).toLocaleString()}</span>
                        <span class="stat-label">Vetos 7d</span>
                    </div>
                    <div class="summary-stat">
                        <span class="stat-value">${formatCapital(summary.total_capital_protected || 0)}</span>
                        <span class="stat-label">Protegido</span>
                    </div>
                    <div class="summary-stat">
                        <span class="stat-value">${summary.veto_types_active || 0}</span>
                        <span class="stat-label">Filtros</span>
                    </div>
                </div>
                ${vetoHtml}
                ${symbolsHtml}
                ${recsHtml}
            </div>
        `;
    }

    function init() {
        fetchLearningInsights();
        setInterval(fetchLearningInsights, REFRESH_INTERVAL);
        console.log('LearningInsightsWidget initialized');
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
