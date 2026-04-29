const LatencyWidget = {
    headerEl: null,
    
    init() {
        this.headerEl = document.getElementById('latency-value');
        if (!this.headerEl) return false;
        this.load();
        setInterval(() => this.load(), 30000);
        return true;
    },
    
    async load() {
        try {
            const start = performance.now();
            const response = await fetch('/api/system/latency');
            const clientLatency = performance.now() - start;
            const data = await response.json();
            this.render(data, clientLatency);
        } catch (error) {
            console.error('LatencyWidget error:', error);
            this.renderError();
        }
    },
    
    render(data, clientLatency) {
        const latency = data.latency || {};
        const dbMs = latency.database_ms || 0;
        const cacheMs = latency.cache_ms || 0;
        const avgMs = latency.avg_ms || dbMs || cacheMs;
        
        if (this.headerEl) {
            const displayLatency = avgMs > 0 ? avgMs : Math.round(clientLatency);
            this.headerEl.textContent = displayLatency.toFixed(1) + 'ms';
            
            if (displayLatency < 10) {
                this.headerEl.className = 'header-stat-value positive';
            } else if (displayLatency < 50) {
                this.headerEl.className = 'header-stat-value';
            } else {
                this.headerEl.className = 'header-stat-value negative';
            }
        }
    },
    
    renderError() {
        if (this.headerEl) {
            this.headerEl.textContent = '--';
            this.headerEl.className = 'header-stat-value';
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    LatencyWidget.init();
});
