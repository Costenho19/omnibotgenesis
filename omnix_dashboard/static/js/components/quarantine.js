const QuarantineWidget = {
    container: null,
    headerEl: null,
    opportunityData: null,
    
    init() {
        this.container = document.getElementById('quarantine-widget');
        this.headerEl = document.getElementById('quarantine-avoided');
        this.load();
        console.log('QuarantineWidget initialized');
        return true;
    },
    
    async load() {
        try {
            const [quarantineRes, opportunityRes] = await Promise.all([
                fetch('/api/system/quarantine'),
                fetch('/api/learning/insights').catch(() => null)
            ]);
            const data = await quarantineRes.json();
            
            if (opportunityRes && opportunityRes.ok) {
                const oppData = await opportunityRes.json();
                this.opportunityData = oppData.opportunity_tracker || null;
            }
            
            this.render(data);
        } catch (error) {
            console.error('QuarantineWidget error:', error);
            this.renderError();
        }
    },
    
    formatNumber(num) {
        if (num >= 1000000) return '$' + (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return '$' + (num / 1000).toFixed(1) + 'K';
        return '$' + num.toFixed(0);
    },
    
    render(data) {
        const quarantine = data.quarantine || {};
        const assets = quarantine.assets || [];
        const totalAvoided = quarantine.total_loss_avoided || 0;
        const count = quarantine.total_blocked || 0;
        
        const vetoes = data.vetoes || {};
        const capitalProtected = data.capital_protected || {};
        
        const veto48h = vetoes['48h'] || {};
        const veto7d = vetoes['7d'] || {};
        
        const grandTotal = capitalProtected.grand_total || totalAvoided;
        const dynamic48h = capitalProtected.dynamic_48h || 0;
        const dynamic7d = capitalProtected.dynamic_7d || 0;
        
        const notional7d = veto7d.notional_blocked || 0;
        const notionalTotal = notional7d > 0 ? notional7d : grandTotal;
        
        if (this.headerEl) {
            this.headerEl.textContent = this.formatNumber(notionalTotal);
        }
        
        if (this.container) {
            let vetoBreakdownHtml = '';
            const vetoTypes = veto48h.by_type || {};
            
            if (Object.keys(vetoTypes).length > 0) {
                const vetoColors = {
                    'COHERENCE_GATE': '#f59e0b',
                    'MC_NEG_ER': '#ef4444',
                    'MC_VAR_TOO_HIGH': '#ef4444',
                    'BLACK_SWAN': '#8b5cf6',
                    'RMS': '#06b6d4'
                };
                
                const vetoLabels = {
                    'COHERENCE_GATE': 'Coherence',
                    'MC_NEG_ER': 'MC -EV',
                    'MC_VAR_TOO_HIGH': 'MC VaR',
                    'BLACK_SWAN': 'Black Swan',
                    'RMS': 'RMS'
                };
                
                vetoBreakdownHtml = Object.entries(vetoTypes).slice(0, 4).map(([type, stats]) => `
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 2px 0;">
                        <span style="font-size: 10px; color: ${vetoColors[type] || '#9ca3af'};">${vetoLabels[type] || type}</span>
                        <span style="font-size: 10px; color: var(--text-muted);">${stats.count}x / ${this.formatNumber(stats.blocked)}</span>
                    </div>
                `).join('');
            }
            
            let assetsHtml = assets.slice(0, 3).map(asset => `
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 2px 0;">
                    <span style="font-weight: 600; font-size: 11px;">${asset.symbol}</span>
                    <span style="color: var(--accent-green); font-size: 10px;">-$${asset.loss_avoided.toLocaleString()}</span>
                </div>
            `).join('');
            
            const notionalTooltip = 'Position sizes of blocked trades. Est. loss avoided calculated using avg adverse price movement (1.5-2.5%).';
            
            this.container.innerHTML = `
                <div class="panel-header" style="margin-top: 0;">
                    <span class="panel-title">Capital Protected</span>
                    <span class="panel-badge" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%);">ACTIVE</span>
                </div>
                <div style="padding: 8px 0;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <div>
                            <div style="font-size: 18px; font-weight: 700; color: var(--accent-green);" title="Total notional value of blocked trades (7 days)">${this.formatNumber(notionalTotal)}</div>
                            <div style="font-size: 9px; color: var(--text-muted);">Notional Blocked (7d)</div>
                        </div>
                        <div style="text-align: center;" title="${notionalTooltip}">
                            <div style="font-size: 14px; font-weight: 600; color: #6b7280;">${this.formatNumber(grandTotal)}</div>
                            <div style="font-size: 9px; color: var(--text-muted);">Total (All Time)</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 14px; font-weight: 600;">${count}</div>
                            <div style="font-size: 9px; color: var(--text-muted);">Trades</div>
                        </div>
                    </div>
                    ${vetoBreakdownHtml ? `
                    <div style="border-top: 1px solid rgba(255,255,255,0.05); padding-top: 6px; margin-top: 4px;">
                        <div style="font-size: 9px; color: var(--text-muted); margin-bottom: 4px;">VETO BREAKDOWN (48h)</div>
                        ${vetoBreakdownHtml}
                    </div>
                    ` : ''}
                    ${assetsHtml ? `
                    <div style="border-top: 1px solid rgba(255,255,255,0.05); padding-top: 6px; margin-top: 4px;">
                        <div style="font-size: 9px; color: var(--text-muted); margin-bottom: 4px;">PERMANENT EXCLUSIONS</div>
                        ${assetsHtml}
                    </div>
                    ` : ''}
                </div>
            `;
        }
    },
    
    renderError() {
        if (this.headerEl) {
            this.headerEl.textContent = '--';
        }
        if (this.container) {
            this.container.innerHTML = `
                <div class="panel-header">
                    <span class="panel-title">Capital Protected</span>
                </div>
                <div style="color: var(--text-muted); font-size: 11px;">Unable to load</div>
            `;
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    QuarantineWidget.init();
});
