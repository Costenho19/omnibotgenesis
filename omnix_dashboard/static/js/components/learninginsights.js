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

    function formatPnl(value) {
        const prefix = value >= 0 ? '+' : '';
        return `${prefix}${formatCapital(Math.abs(value))}`;
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

    function getInterpretationClass(interpretation) {
        if (interpretation === 'PROTECTING') return 'status-positive';
        if (interpretation === 'TOO_STRICT') return 'status-warning';
        return 'status-neutral';
    }

    function getRecommendationBadge(recommendation) {
        const badges = {
            'KEEP_CONSERVATIVE': { text: 'Keep', class: 'rec-keep' },
            'TEST_LOWER': { text: 'Evaluate Adjustment', class: 'rec-test' },
            'CONTINUE_MONITORING': { text: 'Monitoring', class: 'rec-monitor' }
        };
        return badges[recommendation] || { text: recommendation, class: 'rec-monitor' };
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

    function renderOpportunityTracker(tracker) {
        if (!tracker) return '';
        
        const missed = tracker.missed || {};
        const avoided = tracker.avoided || {};
        const net = tracker.net || {};
        const dayProgress = tracker.day_progress || {};
        const recommendation = tracker.recommendation || 'CONTINUE_MONITORING';
        
        const recBadge = getRecommendationBadge(recommendation);
        const interpClass = getInterpretationClass(net.interpretation);
        const netSign = net.value >= 0 ? '+' : '';
        
        return `
            <div class="opportunity-tracker">
                <div class="tracker-header">
                    <span class="tracker-icon">🎯</span>
                    <span class="tracker-title">Opportunity Tracker</span>
                    <span class="tracker-day">Day ${dayProgress.current_day || 1}/30</span>
                </div>
                
                <div class="tracker-balance">
                    <div class="balance-card missed">
                        <div class="card-icon">💎</div>
                        <div class="card-label">MISSED</div>
                        <div class="card-value">${formatPnl(missed.est_profit || 0)}</div>
                        <div class="card-count">${missed.count || 0} trades</div>
                    </div>
                    
                    <div class="balance-vs">
                        <div class="vs-icon">⚖️</div>
                        <div class="vs-text">VS</div>
                    </div>
                    
                    <div class="balance-card avoided">
                        <div class="card-icon">✅</div>
                        <div class="card-label">AVOIDED</div>
                        <div class="card-value">-${formatCapital(avoided.est_loss || 0)}</div>
                        <div class="card-count">${avoided.count || 0} trades</div>
                    </div>
                </div>
                
                <div class="tracker-net ${interpClass}">
                    <span class="net-label">NET:</span>
                    <span class="net-value">${netSign}${formatCapital(Math.abs(net.value || 0))}</span>
                    <span class="net-text">= ${net.interpretation_text || 'Calculando...'}</span>
                </div>
                
                <div class="tracker-footer">
                    <span class="review-date">📅 Review: ${dayProgress.review_date_display || 'Feb 14, 2026'}</span>
                    <span class="rec-badge ${recBadge.class}">${recBadge.text}</span>
                </div>
                
                <div class="tracker-methodology" title="Estimate based on average adverse move × position size. Conservative lower bound. Same methodology for missed opportunities and avoided losses.">
                    <span class="methodology-icon">ℹ️</span>
                    <span class="methodology-text">Est. based on avg adverse move × position size</span>
                </div>
                
                ${tracker.near_miss ? `
                <div class="near-miss-indicator">
                    <span class="near-miss-icon">👀</span>
                    <span class="near-miss-text">Near-miss candidates: ${tracker.near_miss.count || 0}</span>
                </div>
                ` : ''}
            </div>
        `;
    }

    function renderLearningInsights(data) {
        const container = document.getElementById('learning-insights-widget');
        if (!container) return;

        const summary = data.summary || {};
        const vetoEffectiveness = data.veto_effectiveness || [];
        const recommendations = data.recommendations || [];
        const topSymbols = data.top_vetoed_symbols || [];
        const opportunityTracker = data.opportunity_tracker || null;

        const trackerHtml = renderOpportunityTracker(opportunityTracker);

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
            symbolsHtml = '<div class="top-symbols"><span class="symbols-label">Blocked:</span>';
            topSymbols.slice(0, 3).forEach(s => {
                symbolsHtml += `<span class="symbol-chip">${s.symbol} (${s.veto_count})</span>`;
            });
            symbolsHtml += '</div>';
        }

        container.innerHTML = `
            <div class="learning-header">
                <span class="widget-icon">🧠</span>
                <span class="widget-title">Opportunity Tracker</span>
                <span class="widget-badge">ADR-008</span>
            </div>
            <div class="learning-body">
                ${trackerHtml}
                <div class="learning-summary">
                    <div class="summary-stat">
                        <span class="stat-value">${(summary.total_vetos_7d || 0).toLocaleString()}</span>
                        <span class="stat-label">Vetoes 7D</span>
                    </div>
                    <div class="summary-stat" title="Est. based on ~2.5% avg adverse move × position size, capped at 10% of virtual capital ($100K max)">
                        <span class="stat-value" style="color: var(--accent-green);">${formatCapital((opportunityTracker?.avoided?.est_loss) || 0)}</span>
                        <span class="stat-label">Est. Loss Avoided*</span>
                    </div>
                    <div class="summary-stat" title="Number of active risk governance filters (veto types)">
                        <span class="stat-value">${summary.veto_types_active || 0}</span>
                        <span class="stat-label">Filters</span>
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
        console.log('OpportunityTrackerWidget initialized');
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
