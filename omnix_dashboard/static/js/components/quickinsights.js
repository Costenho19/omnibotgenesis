var QuickInsightsWidget = (function() {
    'use strict';
    
    var containerId = null;
    var isInitialized = false;
    
    function init(id) {
        containerId = id || 'quick-insights-widget';
        isInitialized = true;
        console.log('QuickInsightsWidget initialized');
        refresh();
    }
    
    function refresh() {
        if (!isInitialized) return Promise.resolve();
        
        return OmnixAPI.get('/api/system/quick-insights')
            .then(function(data) {
                if (data && data.success) {
                    render(data);
                } else {
                    renderError('Unable to load insights');
                }
            })
            .catch(function(err) {
                console.error('QuickInsights error:', err);
                renderError('Connection error');
            });
    }
    
    function render(data) {
        var container = document.getElementById(containerId);
        if (!container) return;
        
        var insights = data.insights || [];
        
        if (insights.length === 0) {
            container.innerHTML = 
                '<div class="quick-insights-container">' +
                    '<div class="quick-insights-header">' +
                        '<span class="insights-title">Quick Insights</span>' +
                    '</div>' +
                    '<div class="insights-empty">No insights available</div>' +
                '</div>';
            return;
        }
        
        var insightsHtml = insights.map(function(insight) {
            var typeClass = getTypeClass(insight.type);
            var icon = getIcon(insight.icon);
            
            return '<div class="insight-item ' + typeClass + '">' +
                '<div class="insight-icon">' + icon + '</div>' +
                '<div class="insight-content">' +
                    '<div class="insight-title">' + (insight.title || '') + '</div>' +
                    '<div class="insight-message">' + (insight.message || '') + '</div>' +
                '</div>' +
            '</div>';
        }).join('');
        
        container.innerHTML = 
            '<div class="quick-insights-container">' +
                '<div class="quick-insights-header">' +
                    '<span class="insights-title">Quick Insights</span>' +
                    '<span class="insights-count">' + insights.length + '</span>' +
                '</div>' +
                '<div class="insights-list">' + insightsHtml + '</div>' +
            '</div>';
    }
    
    function renderError(message) {
        var container = document.getElementById(containerId);
        if (!container) return;
        
        container.innerHTML = 
            '<div class="quick-insights-container error">' +
                '<div class="quick-insights-header">' +
                    '<span class="insights-title">Quick Insights</span>' +
                '</div>' +
                '<div class="insights-error">' + message + '</div>' +
            '</div>';
    }
    
    function getTypeClass(type) {
        var classes = {
            'SUCCESS': 'success',
            'WARNING': 'warning',
            'CAUTION': 'caution',
            'INFO': 'info',
            'PROGRESS': 'progress'
        };
        return classes[type] || 'info';
    }
    
    function getIcon(iconName) {
        var icons = {
            'check-circle': '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
            'trending-up': '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>',
            'alert-triangle': '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
            'alert-circle': '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>',
            'star': '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
            'clock': '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
            'shield': '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>'
        };
        return icons[iconName] || icons['clock'];
    }
    
    return {
        init: init,
        refresh: refresh
    };
})();
