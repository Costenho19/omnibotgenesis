/**
 * OMNIX Dashboard V6.5.4 - Common Functions
 * Shared refresh logic with independent error handling
 */

const OmnixCommon = (function() {
    'use strict';

    const widgetStatus = {};

    async function executeWidget(name, fn, options = {}) {
        const { silent = false, timeout = 30000 } = options;
        
        try {
            const timeoutPromise = new Promise((_, reject) => {
                setTimeout(() => reject(new Error('Widget timeout')), timeout);
            });

            await Promise.race([fn(), timeoutPromise]);
            
            widgetStatus[name] = { status: 'ok', lastUpdate: Date.now(), error: null };
            return { success: true };
        } catch (error) {
            widgetStatus[name] = { status: 'error', lastUpdate: Date.now(), error: error.message };
            
            if (!silent) {
                console.warn(`[Widget:${name}] Error:`, error.message);
            }
            
            return { success: false, error: error.message };
        }
    }

    async function refreshWidgets(widgets, options = {}) {
        const { parallel = true, onProgress = null } = options;
        const results = {};
        const startTime = Date.now();

        if (parallel) {
            const promises = widgets.map(async ({ name, fn }) => {
                const result = await executeWidget(name, fn);
                results[name] = result;
                if (onProgress) onProgress(name, result);
                return result;
            });

            await Promise.allSettled(promises);
        } else {
            for (const { name, fn } of widgets) {
                const result = await executeWidget(name, fn);
                results[name] = result;
                if (onProgress) onProgress(name, result);
            }
        }

        const elapsed = Date.now() - startTime;
        const successful = Object.values(results).filter(r => r.success).length;
        const failed = Object.values(results).filter(r => !r.success).length;

        console.log(`[Refresh] ${successful}/${widgets.length} widgets OK, ${failed} failed (${elapsed}ms)`);

        return {
            results,
            elapsed,
            successful,
            failed,
            total: widgets.length
        };
    }

    function getWidgetStatus(name) {
        return widgetStatus[name] || { status: 'unknown', lastUpdate: null, error: null };
    }

    function getAllWidgetStatus() {
        return { ...widgetStatus };
    }

    function updateTimestamp(elementId) {
        const el = document.getElementById(elementId);
        if (el) {
            el.textContent = new Date().toLocaleTimeString('en-US', { hour12: false });
        }
    }

    function showWidgetError(containerId, message = 'Failed to load') {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = `
                <div class="widget-error" style="display: flex; align-items: center; justify-content: center; height: 100%; color: #ef4444; font-size: 11px; opacity: 0.7;">
                    <span style="margin-right: 6px;">⚠️</span> ${message}
                </div>
            `;
        }
    }

    function showWidgetLoading(containerId, message = 'Loading...') {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = `
                <div class="widget-loading" style="display: flex; align-items: center; justify-content: center; height: 100%; color: var(--text-muted); font-size: 11px;">
                    ${message}
                </div>
            `;
        }
    }

    let refreshTimer = null;

    function startAutoRefresh(refreshFn, intervalMs = 10000) {
        stopAutoRefresh();
        refreshFn();
        refreshTimer = setInterval(refreshFn, intervalMs);
        console.log(`[AutoRefresh] Started with ${intervalMs}ms interval`);
    }

    function stopAutoRefresh() {
        if (refreshTimer) {
            clearInterval(refreshTimer);
            refreshTimer = null;
            console.log('[AutoRefresh] Stopped');
        }
    }

    function isAutoRefreshActive() {
        return refreshTimer !== null;
    }

    return {
        executeWidget,
        refreshWidgets,
        getWidgetStatus,
        getAllWidgetStatus,
        updateTimestamp,
        showWidgetError,
        showWidgetLoading,
        startAutoRefresh,
        stopAutoRefresh,
        isAutoRefreshActive
    };
})();

if (typeof window !== 'undefined') {
    window.OmnixCommon = OmnixCommon;
}

/**
 * OMNIX Security: HTML escape utility.
 * Use escHtml(value) instead of raw ${value} in all innerHTML templates
 * to prevent stored XSS via API data injection.
 * Example: container.innerHTML = `<span>${escHtml(data.status)}</span>`;
 */
(function() {
    'use strict';
    const _div = document.createElement('div');
    function escHtml(val) {
        if (val === null || val === undefined) return '';
        _div.textContent = String(val);
        return _div.innerHTML;
    }
    if (typeof window !== 'undefined') {
        window.escHtml = escHtml;
    }
})();
