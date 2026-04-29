/**
 * OMNIX Execution Boundary Integrity Protocol (EBIP) Widget
 * ADR-045 | March 2026
 *
 * Displays real-time status of the 4-component execution integrity layer:
 * ACV — Admissibility Consistency Validator
 * ECP — Execution Commitment Protocol
 * NPM — Navigation Pattern Monitor
 * CP  — Concentration Predictor
 */

const ExecutionIntegrityWidget = (function () {
    'use strict';

    let containerId = 'execution-integrity-widget';
    let lastData = null;

    const ALERT_COLORS = {
        NOMINAL:  { color: '#00d4aa', bg: 'rgba(0,212,170,0.12)',  border: 'rgba(0,212,170,0.3)',  label: 'NOMINAL'  },
        WATCH:    { color: '#ffc107', bg: 'rgba(255,193,7,0.12)',   border: 'rgba(255,193,7,0.3)',   label: 'WATCH'    },
        CAUTION:  { color: '#ff9800', bg: 'rgba(255,152,0,0.12)',   border: 'rgba(255,152,0,0.3)',   label: 'CAUTION'  },
        CRITICAL: { color: '#ff4444', bg: 'rgba(255,68,68,0.12)',   border: 'rgba(255,68,68,0.3)',   label: 'CRITICAL' },
        NOMINAL_DEFAULT: { color: '#00d4aa', bg: 'rgba(0,212,170,0.12)', border: 'rgba(0,212,170,0.3)', label: 'NOMINAL' },
    };

    const RISK_COLORS = {
        LOW:               '#00d4aa',
        MEDIUM:            '#ffc107',
        HIGH:              '#ff9800',
        CRITICAL:          '#ff4444',
        INSUFFICIENT_DATA: '#6b7280',
        UNKNOWN:           '#6b7280',
    };

    function init(id) {
        containerId = id || containerId;
    }

    async function refresh() {
        try {
            const response = await fetch('/api/governance/execution-integrity', {
                headers: { 'Cache-Control': 'no-cache' }
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const json = await response.json();
            if (json.execution_integrity) {
                lastData = json.execution_integrity;
                render(json.execution_integrity);
            }
        } catch (error) {
            renderError();
        }
    }

    function render(data) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const score = data.overall_execution_integrity ?? 100;
        const nav   = data.navigation_health || {};
        const cp    = data.concentration_prediction || {};
        const alertLevel = nav.alert_level || 'NOMINAL';
        const alertCfg   = ALERT_COLORS[alertLevel] || ALERT_COLORS.NOMINAL_DEFAULT;
        const riskLevel  = cp.predicted_risk || 'INSUFFICIENT_DATA';
        const riskColor  = RISK_COLORS[riskLevel] || '#6b7280';
        const violations = data.recent_consistency_violations_24h != null ? data.recent_consistency_violations_24h : 0;
        const dist       = nav.distribution || {};
        const total      = nav.total_decisions != null ? nav.total_decisions : 0;

        const scoreColor = score >= 90 ? '#00d4aa' : score >= 70 ? '#ffc107' : '#ff4444';
        const circumference = 2 * Math.PI * 38;
        const offset = circumference - (score / 100) * circumference;

        const approvedPct = dist.approved_pct ?? (total > 0 ? ((dist.approved || 0) / total * 100) : 0);
        const blockedPct  = dist.blocked_pct  ?? (total > 0 ? ((dist.blocked  || 0) / total * 100) : 0);
        const holdPct     = dist.hold_pct     ?? (total > 0 ? ((dist.hold     || 0) / total * 100) : 0);

        container.innerHTML = `
            <div class="panel-header">
                <span class="panel-title">Execution Integrity</span>
                <span class="ebip-badge" style="background:${alertCfg.bg}; color:${alertCfg.color}; border:1px solid ${alertCfg.border};">
                    <span class="ebip-dot" style="background:${alertCfg.color};"></span>
                    ${alertCfg.label}
                </span>
            </div>

            <div class="ebip-main">
                <!-- Score ring -->
                <div class="ebip-ring-wrap">
                    <svg viewBox="0 0 84 84" class="ebip-ring-svg">
                        <circle cx="42" cy="42" r="38" fill="none" stroke="#1a1f2e" stroke-width="7"/>
                        <circle cx="42" cy="42" r="38" fill="none" stroke="${scoreColor}" stroke-width="7"
                                stroke-dasharray="${circumference.toFixed(2)}" stroke-dashoffset="${offset.toFixed(2)}"
                                stroke-linecap="round" transform="rotate(-90 42 42)"
                                style="transition: stroke-dashoffset 0.6s ease;"/>
                    </svg>
                    <div class="ebip-ring-label">
                        <div class="ebip-score-num" style="color:${scoreColor};">${Math.round(score)}</div>
                        <div class="ebip-score-sub">/ 100</div>
                    </div>
                </div>

                <!-- Right side metrics -->
                <div class="ebip-right">
                    <div class="ebip-components">
                        ${renderComponent('ACV', 'Consistency Validator', violations === 0)}
                        ${renderComponent('ECP', 'Commitment Protocol', true)}
                        ${renderComponent('NPM', 'Navigation Monitor', alertLevel === 'NOMINAL' || alertLevel === 'WATCH')}
                        ${renderComponent('CP',  'Concentration Predictor', riskLevel === 'LOW' || riskLevel === 'INSUFFICIENT_DATA')}
                    </div>
                </div>
            </div>

            <!-- Navigation distribution -->
            ${total > 0 ? `
            <div class="ebip-nav-section">
                <div class="ebip-nav-header">
                    <span class="ebip-nav-title">Navigation Pattern (24h)</span>
                    <span class="ebip-nav-total">${total} decisions</span>
                </div>
                <div class="ebip-bars">
                    ${renderNavBar('APPROVED', approvedPct, '#00d4aa')}
                    ${renderNavBar('BLOCKED',  blockedPct,  '#ff6b6b')}
                    ${renderNavBar('HOLD',     holdPct,     '#ffc107')}
                </div>
            </div>` : `
            <div class="ebip-nav-section">
                <div class="ebip-nav-empty">Awaiting navigation data — no decisions recorded in last 24h</div>
            </div>`}

            <!-- Bottom row -->
            <div class="ebip-bottom">
                <div class="ebip-stat">
                    <div class="ebip-stat-label">Concentration Risk</div>
                    <div class="ebip-stat-val" style="color:${riskColor};">${riskLevel.replace('_', ' ')}</div>
                </div>
                <div class="ebip-stat">
                    <div class="ebip-stat-label">Consistency Violations (24h)</div>
                    <div class="ebip-stat-val" style="color:${violations > 0 ? '#ff9800' : '#00d4aa'};">${violations}</div>
                </div>
                <div class="ebip-stat">
                    <div class="ebip-stat-label">EBIP Protocol</div>
                    <div class="ebip-stat-val" style="color:#818cf8;">v${data.ebip_version || '1.0'}</div>
                </div>
            </div>
        `;
    }

    function renderComponent(code, label, healthy) {
        const color = healthy ? '#00d4aa' : '#ffc107';
        const icon  = healthy ? '✓' : '⚠';
        return `
            <div class="ebip-comp">
                <span class="ebip-comp-icon" style="color:${color};">${icon}</span>
                <span class="ebip-comp-code" style="color:${color};">${code}</span>
                <span class="ebip-comp-label">${label}</span>
            </div>
        `;
    }

    function renderNavBar(label, pct, color) {
        const pctSafe = Math.max(0, Math.min(100, pct || 0));
        return `
            <div class="ebip-bar-row">
                <div class="ebip-bar-label">${label}</div>
                <div class="ebip-bar-track">
                    <div class="ebip-bar-fill" style="width:${pctSafe}%; background:${color}; transition: width 0.5s ease;"></div>
                </div>
                <div class="ebip-bar-pct" style="color:${color};">${pctSafe.toFixed(1)}%</div>
            </div>
        `;
    }

    function renderError() {
        const container = document.getElementById(containerId);
        if (!container) return;
        container.innerHTML = `
            <div class="panel-header">
                <span class="panel-title">Execution Integrity</span>
                <span class="ebip-badge" style="background:rgba(0,212,170,0.12);color:#00d4aa;border:1px solid rgba(0,212,170,0.3);">
                    <span class="ebip-dot" style="background:#00d4aa;"></span>NOMINAL
                </span>
            </div>
            <div style="text-align:center;padding:24px 0;color:#4b5563;font-size:0.75rem;">
                4 components active — data loading
            </div>
        `;
    }

    return { init, refresh };
})();

if (typeof window !== 'undefined') {
    window.ExecutionIntegrityWidget = ExecutionIntegrityWidget;
}
