(function () {
    'use strict';

    const REFRESH_INTERVAL = 20000;

    const INTEGRITY = {
        'OK':             { label: 'VERIFIED',    cls: 'avm-ok',      icon: '✓' },
        'TAMPERED':       { label: 'TAMPERED',    cls: 'avm-danger',  icon: '✗' },
        'LEGACY_NO_HASH': { label: 'LEGACY',      cls: 'avm-warn',    icon: '!' },
        'NO_SNAPSHOT':    { label: 'NO BASELINE', cls: 'avm-danger',  icon: '✗' },
        'UNKNOWN':        { label: 'UNKNOWN',     cls: 'avm-warn',    icon: '?' },
    };

    const DRIFT = {
        'STABLE':   { label: 'STABLE',   cls: 'avm-ok',     dot: 'dot-green' },
        'DRIFTING': { label: 'DRIFTING', cls: 'avm-warn',   dot: 'dot-yellow' },
        'STALE':    { label: 'STALE',    cls: 'avm-danger', dot: 'dot-red' },
        'UNKNOWN':  { label: 'UNKNOWN',  cls: 'avm-muted',  dot: 'dot-gray' },
    };

    function render(data) {
        const el = document.getElementById('avm-governance-widget');
        if (!el) return;

        if (!data.success) {
            el.innerHTML = `<div class="avm-wrap"><div class="avm-sys-header avm-sys-degraded">
                <div class="avm-sys-title">🛡 OMNIX GOVERNANCE</div>
                <div class="avm-sys-badges"><span class="avm-pill avm-danger">ERROR</span></div>
            </div><div class="avm-error-msg">${data.error || 'Failed to load governance status'}</div></div>`;
            return;
        }

        const ok    = !data.degraded_mode;
        const fcl   = data.fail_closed;
        const total = data.decisions_blocked_total || 0;
        const ld    = data.last_decision;

        // ── System header ───────────────────────────────────────────
        const sysClass  = ok ? 'avm-sys-ok' : 'avm-sys-degraded';
        const sysLabel  = ok ? 'ACTIVE'     : 'DEGRADED';
        const sysIcon   = ok ? '✓'          : '⚠';
        const intLabel  = ok ? 'VERIFIED'   : 'ALERT';
        const intClass  = ok ? 'avm-ok'     : 'avm-danger';
        const modeLabel = fcl ? 'FAIL-CLOSED' : 'PASS-THROUGH';
        const modeClass = fcl ? 'avm-danger'  : 'avm-muted';

        // ── Last blocked decision ────────────────────────────────────
        let decisionHtml = '';
        if (ld) {
            decisionHtml = `
                <div class="avm-decision-block">
                    <div class="avm-decision-header">
                        <span class="avm-decision-title">LAST GOVERNANCE DECISION</span>
                        <span class="avm-decision-time">${ld.time || '—'}</span>
                    </div>
                    <div class="avm-decision-body">
                        <div class="avm-decision-row">
                            <span class="avm-decision-key">DOMAIN</span>
                            <span class="avm-decision-val">${ld.domain}</span>
                        </div>
                        <div class="avm-decision-row">
                            <span class="avm-decision-key">INPUT</span>
                            <span class="avm-decision-val">${ld.input}</span>
                        </div>
                        <div class="avm-decision-row">
                            <span class="avm-decision-key">AMOUNT</span>
                            <span class="avm-decision-val">${ld.amount}</span>
                        </div>
                        <div class="avm-decision-row">
                            <span class="avm-decision-key">RESULT</span>
                            <span class="avm-decision-val avm-blocked-result">❌ BLOCKED</span>
                        </div>
                        <div class="avm-decision-row">
                            <span class="avm-decision-key">REASON</span>
                            <span class="avm-decision-val avm-reason-text">${ld.reason}</span>
                        </div>
                    </div>
                </div>`;
        } else {
            decisionHtml = `
                <div class="avm-decision-block avm-decision-empty">
                    <div class="avm-decision-header">
                        <span class="avm-decision-title">LAST GOVERNANCE DECISION</span>
                    </div>
                    <div class="avm-decision-empty-msg">No blocked decisions on record</div>
                </div>`;
        }

        // ── Per-domain rows ──────────────────────────────────────────
        const domainRows = (data.domains || []).map(d => {
            const ig  = INTEGRITY[d.integrity]  || INTEGRITY['UNKNOWN'];
            const dr  = DRIFT[d.drift_status]   || DRIFT['UNKNOWN'];
            const dv  = d.drift_score !== null && d.drift_score !== undefined
                        ? `${d.drift_score}%` : '—';
            const blk = d.blocked_24h > 0
                        ? `<span class="avm-pill avm-danger">${d.blocked_24h} BLOCKED</span>`
                        : '';

            return `
                <div class="avm-domain-row${d.integrity === 'TAMPERED' ? ' row-tampered' : ''}">
                    <div class="avm-dom-name">${d.label}
                        <span class="avm-dom-ver">v${d.version || 1}</span>
                    </div>
                    <div class="avm-dom-hash" title="SHA-256 baseline hash">${d.hash}</div>
                    <div class="avm-dom-integrity">
                        <span class="avm-pill ${ig.cls}">${ig.icon} ${ig.label}</span>
                    </div>
                    <div class="avm-dom-drift">
                        <span class="avm-dot ${dr.dot}"></span>
                        <span class="avm-drift-lbl ${dr.cls}">${dr.label}</span>
                        <span class="avm-drift-pct">${dv}</span>
                    </div>
                    <div class="avm-dom-action">${blk}</div>
                </div>`;
        }).join('');

        // ── DB + mode footer ─────────────────────────────────────────
        const dbStat = data.db_available
            ? '<span class="avm-db avm-ok">● PostgreSQL</span>'
            : '<span class="avm-db avm-danger">● DB OFFLINE</span>';

        el.innerHTML = `
            <div class="avm-wrap">

                <!-- System header -->
                <div class="avm-sys-header ${sysClass}">
                    <div class="avm-sys-title">🛡 OMNIX GOVERNANCE STATUS</div>
                    <div class="avm-sys-badges">
                        <span class="avm-pill ${ok ? 'avm-ok' : 'avm-danger'}">${sysIcon} SYSTEM: ${sysLabel}</span>
                        <span class="avm-pill ${intClass}">INTEGRITY: ${intLabel}</span>
                        <span class="avm-pill ${modeClass}">MODE: ${modeLabel}</span>
                    </div>
                </div>

                <!-- Blocked counter banner -->
                <div class="avm-counter-bar${total > 0 ? ' counter-active' : ' counter-clear'}">
                    ${total > 0
                        ? `<span class="avm-counter-icon">🚫</span>
                           <span class="avm-counter-text">${total} decision${total !== 1 ? 's' : ''} blocked by governance baseline in last 24h</span>`
                        : `<span class="avm-counter-icon">✓</span>
                           <span class="avm-counter-text">All pipelines operating within governance envelope</span>`
                    }
                </div>

                <!-- Last decision (the thing that sells) -->
                ${decisionHtml}

                <!-- Domain baseline grid -->
                <div class="avm-domains-section">
                    <div class="avm-domains-title">BASELINE INTEGRITY · 4 DOMAINS</div>
                    <div class="avm-domains-grid">
                        <div class="avm-grid-header">
                            <span>Domain</span>
                            <span>Hash</span>
                            <span>Integrity</span>
                            <span>Drift</span>
                            <span>24h</span>
                        </div>
                        ${domainRows}
                    </div>
                </div>

                <!-- Footer -->
                <div class="avm-footer-bar">
                    ${dbStat}
                    <span class="avm-footer-ts">Updated ${new Date().toLocaleTimeString('en-US', {hour:'2-digit', minute:'2-digit'})}</span>
                </div>

            </div>`;
    }

    function fetchAVM() {
        const key = window.OMNIX_API_KEY || 'omnix-dashboard-2024';
        fetch('/api/governance/avm-status', { headers: { 'X-API-Key': key } })
            .then(r => r.json())
            .then(d => render(d))
            .catch(err => {
                const el = document.getElementById('avm-governance-widget');
                if (el) el.innerHTML = `<div class="avm-wrap">
                    <div class="avm-sys-header avm-sys-degraded">
                        <div class="avm-sys-title">🛡 OMNIX GOVERNANCE STATUS</div>
                        <div class="avm-sys-badges"><span class="avm-pill avm-danger">⚠ OFFLINE</span></div>
                    </div>
                    <div class="avm-error-msg">Connection error — governance data unavailable</div>
                </div>`;
            });
    }

    document.addEventListener('DOMContentLoaded', function () {
        fetchAVM();
        setInterval(fetchAVM, REFRESH_INTERVAL);
    });

    window.refreshAVMGovernance = fetchAVM;
})();
