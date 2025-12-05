/**
 * OMNIX Dashboard V6.5.3 - News Feed Component
 */

const OmnixNews = (function() {
    'use strict';

    function renderTerminal(containerId, news, sourceId = null) {
        const container = document.getElementById(containerId);
        if (!container) return;

        if (!news || news.length === 0) {
            container.innerHTML = '<div style="color: var(--text-muted); font-size: 11px;">No news available</div>';
            return;
        }

        container.innerHTML = news.map(n => `
            <div class="news-item">
                <div class="news-title">${n.headline || n.title}</div>
                <div class="news-source">${n.source} | ${formatTime(n.datetime)}</div>
            </div>
        `).join('');
    }

    function renderDashboard(containerId, news) {
        const container = document.getElementById(containerId);
        if (!container) return;

        if (!news || news.length === 0) {
            container.innerHTML = '<div class="text-slate-600 text-xs text-center py-6 uppercase tracking-wider">No news available</div>';
            return;
        }

        container.innerHTML = news.map(item => `
            <div class="news-item">
                <div class="flex items-start gap-2">
                    <span class="text-blue-400 text-xs mt-0.5">●</span>
                    <div class="flex-1">
                        <div class="text-sm font-medium mb-1 line-clamp-2">${item.headline || item.title}</div>
                        <div class="text-[10px] text-slate-500 uppercase">${item.source}</div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    function formatTime(datetime) {
        if (!datetime) return '';
        const timestamp = typeof datetime === 'number' ? datetime * 1000 : new Date(datetime).getTime();
        const date = new Date(timestamp);
        if (typeof OmnixTime !== 'undefined') {
            return OmnixTime.formatRelative(date);
        }
        return date.toLocaleTimeString();
    }

    async function updateFinnhub(containerId, sourceId = null, maxItems = 6) {
        try {
            const data = await OmnixAPI.getFinnhubNews();
            if (data.success && data.data && data.data.length > 0) {
                const news = data.data.slice(0, maxItems);
                renderTerminal(containerId, news);
                if (sourceId) {
                    const sourceEl = document.getElementById(sourceId);
                    if (sourceEl) sourceEl.textContent = 'FINNHUB';
                }
            }
        } catch (error) {
            console.error('Finnhub news error:', error);
        }
    }

    async function update(containerId, sourceId = null) {
        try {
            const data = await OmnixAPI.getNews();
            if (data.success && data.news.length > 0) {
                renderTerminal(containerId, data.news);
                if (sourceId) {
                    const sourceEl = document.getElementById(sourceId);
                    if (sourceEl) sourceEl.textContent = data.source;
                }
            }
        } catch (error) {
            console.error('News update error:', error);
        }
    }

    return {
        renderTerminal,
        renderDashboard,
        update,
        updateFinnhub
    };
})();

if (typeof window !== 'undefined') {
    window.OmnixNews = OmnixNews;
}
