(function() {
    'use strict';

    const RiskGuardian = {
        containerId: null,
        lastData: null,

        init: function(containerId) {
            this.containerId = containerId;
            console.log('RiskGuardian widget initialized');
        },

        refresh: async function() {
            try {
                const response = await OmnixAPI.fetchWithRetry('/api/system/status');
                if (response.success && response.status) {
                    this.lastData = response.status;
                    this.render(response.status);
                }
            } catch (error) {
                console.error('RiskGuardian refresh error:', error);
                this.renderError();
            }
        },

        render: function(status) {
            const container = document.getElementById(this.containerId);
            if (!container) return;

            const rg = status.risk_guardian || {};
            const protection = status.protection || {};

            const riskLevel = rg.risk_level || 'LOW';
            const riskColors = {
                'LOW': { bg: '#00ff8820', border: '#00ff88', text: '#00ff88' },
                'MEDIUM': { bg: '#ffaa0020', border: '#ffaa00', text: '#ffaa00' },
                'HIGH': { bg: '#ff660020', border: '#ff6600', text: '#ff6600' },
                'CRITICAL': { bg: '#ff444420', border: '#ff4444', text: '#ff4444' }
            };
            const colors = riskColors[riskLevel] || riskColors['LOW'];

            const circuitBreaker = rg.circuit_breaker || {};
            const overtrading = rg.overtrading_protection || {};
            const revenge = rg.revenge_trading || {};
            const capital = rg.capital_protection || {};

            container.innerHTML = `
                <div class="rg-header">
                    <div class="rg-title">
                        <span class="rg-icon">🛡️</span>
                        <span>AI RISK GUARDIAN ${rg.version || 'V5.4'}</span>
                    </div>
                    <div class="rg-status" style="background: ${colors.bg}; border-color: ${colors.border}; color: ${colors.text}">
                        ${rg.status || 'ACTIVE'}
                    </div>
                </div>

                <div class="rg-risk-level" style="background: ${colors.bg}; border: 1px solid ${colors.border}">
                    <div class="rg-risk-label">RISK LEVEL</div>
                    <div class="rg-risk-value" style="color: ${colors.text}">${riskLevel}</div>
                    <div class="rg-risk-bar">
                        <div class="rg-risk-fill" style="width: ${this.getRiskWidth(riskLevel)}%; background: ${colors.text}"></div>
                    </div>
                </div>

                <div class="rg-grid">
                    ${this.renderProtectionCard('CIRCUIT BREAKER', circuitBreaker.active ? '🔴 ACTIVE' : '🟢 READY', !circuitBreaker.active)}
                    ${this.renderProtectionCard('OVERTRADING', overtrading.blocked ? '🔴 BLOCKED' : '🟢 OK', !overtrading.blocked, `${overtrading.trades_today || 0}/${overtrading.max_trades_per_day || 20}`)}
                    ${this.renderProtectionCard('REVENGE TRADE', revenge.blocked ? '🔴 BLOCKED' : '🟢 OK', !revenge.blocked)}
                    ${this.renderProtectionCard('CAPITAL PROTECT', capital.enabled ? '🟢 ACTIVE' : '⚪ OFF', capital.enabled, `${(capital.current_daily_loss_pct || 0).toFixed(1)}%/${capital.max_daily_loss_pct || 5}%`)}
                </div>

                <div class="rg-drawdown">
                    <div class="rg-drawdown-header">
                        <span>DRAWDOWN TIER</span>
                        <span class="rg-tier" style="color: ${colors.text}">${protection.drawdown_tier || 'NORMAL'}</span>
                    </div>
                    <div class="rg-drawdown-details">
                        <div class="rg-detail">
                            <span>Position Size</span>
                            <span>${((protection.position_size_factor || 1) * 100).toFixed(0)}%</span>
                        </div>
                        <div class="rg-detail">
                            <span>Ramp-up</span>
                            <span>${protection.ramp_up_pct || 100}%</span>
                        </div>
                    </div>
                </div>
            `;
        },

        renderProtectionCard: function(title, status, isOk, detail) {
            var detailHtml = detail ? '<div class="rg-card-detail">' + detail + '</div>' : '';
            return '<div class="rg-protection-card ' + (isOk ? 'rg-ok' : 'rg-alert') + '">' +
                '<div class="rg-card-title">' + title + '</div>' +
                '<div class="rg-card-status">' + status + '</div>' +
                detailHtml +
            '</div>';
        },

        getRiskWidth: function(level) {
            const widths = { 'LOW': 25, 'MEDIUM': 50, 'HIGH': 75, 'CRITICAL': 100 };
            return widths[level] || 25;
        },

        renderError: function() {
            const container = document.getElementById(this.containerId);
            if (!container) return;

            container.innerHTML = `
                <div class="rg-error">
                    <span class="rg-icon">🔄</span>
                    <span>Updating...</span>
                </div>
            `;
        },

        destroy: function() {
            const container = document.getElementById(this.containerId);
            if (container) {
                container.innerHTML = '';
            }
        }
    };

    window.RiskGuardian = RiskGuardian;
})();
