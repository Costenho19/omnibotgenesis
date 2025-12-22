const QuarantineWidget = {
    container: null,
    headerEl: null,
    
    init() {
        this.container = document.getElementById('quarantine-widget');
        this.headerEl = document.getElementById('quarantine-avoided');
        this.load();
        console.log('QuarantineWidget initialized');
        return true;
    },
    
    async load() {
        try {
            const response = await fetch('/api/system/quarantine');
            const data = await response.json();
            this.render(data);
        } catch (error) {
            console.error('QuarantineWidget error:', error);
            this.renderError();
        }
    },
    
    render(data) {
        const quarantine = data.quarantine || {};
        const assets = quarantine.assets || [];
        const totalAvoided = quarantine.total_loss_avoided || 0;
        const count = quarantine.total_blocked || 0;
        
        if (this.headerEl) {
            this.headerEl.textContent = '$' + totalAvoided.toLocaleString();
        }
        
        if (this.container) {
            let assetsHtml = assets.slice(0, 4).map(asset => `
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <span style="font-weight: 600;">${asset.symbol}</span>
                    <span style="color: var(--accent-green); font-size: 11px;">-$${asset.loss_avoided.toLocaleString()}</span>
                </div>
            `).join('');
            
            this.container.innerHTML = `
                <div class="panel-header" style="margin-top: 0;">
                    <span class="panel-title">🛡️ Asset Quarantine</span>
                    <span class="panel-badge" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%);">ACTIVE</span>
                </div>
                <div style="padding: 8px 0;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <div>
                            <div style="font-size: 20px; font-weight: 700; color: var(--accent-green);">$${totalAvoided.toLocaleString()}</div>
                            <div style="font-size: 10px; color: var(--text-muted);">Losses Avoided</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 20px; font-weight: 700;">${count}</div>
                            <div style="font-size: 10px; color: var(--text-muted);">Assets Blocked</div>
                        </div>
                    </div>
                    <div style="font-size: 11px; margin-top: 8px;">
                        ${assetsHtml}
                    </div>
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
                    <span class="panel-title">🛡️ Asset Quarantine</span>
                </div>
                <div style="color: var(--text-muted); font-size: 11px;">Unable to load</div>
            `;
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    QuarantineWidget.init();
});
