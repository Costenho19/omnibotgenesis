var LiveStatusWidget = (function() {
    'use strict';
    
    var containerId = null;
    var isInitialized = false;
    
    function init(id) {
        containerId = id || 'live-status-widget';
        isInitialized = true;
        console.log('LiveStatusWidget initialized');
        refresh();
    }
    
    function refresh() {
        if (!isInitialized) return Promise.resolve();
        
        return OmnixAPI.get('/api/system/live-status')
            .then(function(data) {
                if (data && data.success) {
                    render(data);
                } else {
                    renderError('Unable to load status');
                }
            })
            .catch(function(err) {
                console.error('LiveStatus error:', err);
                renderError('Connection error');
            });
    }
    
    function render(data) {
        var container = document.getElementById(containerId);
        if (!container) return;
        
        var activity = data.current_activity || {};
        var lastAction = data.last_action;
        var systemState = data.system_state || {};
        
        var statusClass = getStatusClass(activity.status);
        var statusIcon = getStatusIcon(activity.status);
        
        var lastActionHtml = '';
        if (lastAction) {
            var timeAgo = formatTimeAgo(lastAction.time);
            var resultClass = lastAction.result === 'WIN' ? 'positive' : lastAction.result === 'LOSS' ? 'negative' : 'neutral';
            lastActionHtml = '<div class="live-status-last-action">' +
                '<span class="last-action-label">Last:</span> ' +
                '<span class="last-action-symbol">' + (lastAction.symbol || 'N/A') + '</span> ' +
                '<span class="last-action-side ' + (lastAction.side || '').toLowerCase() + '">' + (lastAction.side || '') + '</span> ' +
                '<span class="last-action-result ' + resultClass + '">' + (lastAction.result || '') + '</span> ' +
                '<span class="last-action-time">' + timeAgo + '</span>' +
            '</div>';
        }
        
        var stateHtml = '<div class="live-status-state">' +
            '<div class="state-item">' +
                '<span class="state-icon veto-' + (systemState.veto_active ? 'on' : 'off') + '"></span>' +
                '<span class="state-label">Veto: ' + (systemState.veto_active ? 'ON' : 'OFF') + '</span>' +
            '</div>' +
            '<div class="state-item">' +
                '<span class="state-label">Regime: ' + (systemState.market_regime || 'N/A') + '</span>' +
            '</div>' +
            '<div class="state-item">' +
                '<span class="state-label">Open: ' + (systemState.open_positions || 0) + '</span>' +
            '</div>' +
        '</div>';
        
        container.innerHTML = 
            '<div class="live-status-container">' +
                '<div class="live-status-header">' +
                    '<div class="live-status-badge ' + statusClass + '">' +
                        '<span class="status-dot"></span>' +
                        '<span class="status-text">' + (activity.status || 'UNKNOWN') + '</span>' +
                    '</div>' +
                    '<span class="live-indicator">LIVE</span>' +
                '</div>' +
                '<div class="live-status-detail">' + (activity.detail || 'System operational') + '</div>' +
                lastActionHtml +
                stateHtml +
            '</div>';
    }
    
    function renderError(message) {
        var container = document.getElementById(containerId);
        if (!container) return;
        
        container.innerHTML = 
            '<div class="live-status-container error">' +
                '<div class="live-status-header">' +
                    '<div class="live-status-badge error">' +
                        '<span class="status-dot"></span>' +
                        '<span class="status-text">OFFLINE</span>' +
                    '</div>' +
                '</div>' +
                '<div class="live-status-detail">' + message + '</div>' +
            '</div>';
    }
    
    function getStatusClass(status) {
        var classes = {
            'EXECUTING': 'executing',
            'ANALYZING': 'analyzing',
            'MONITORING': 'monitoring',
            'IDLE': 'idle',
            'ERROR': 'error'
        };
        return classes[status] || 'analyzing';
    }
    
    function getStatusIcon(status) {
        var icons = {
            'EXECUTING': 'bolt',
            'ANALYZING': 'chart-line',
            'MONITORING': 'eye',
            'IDLE': 'pause'
        };
        return icons[status] || 'activity';
    }
    
    function formatTimeAgo(timestamp) {
        if (!timestamp) return '';
        
        try {
            var date = new Date(timestamp);
            var now = new Date();
            var diff = Math.floor((now - date) / 1000);
            
            if (diff < 60) return diff + 's ago';
            if (diff < 3600) return Math.floor(diff / 60) + 'm ago';
            if (diff < 86400) return Math.floor(diff / 3600) + 'h ago';
            return Math.floor(diff / 86400) + 'd ago';
        } catch (e) {
            return '';
        }
    }
    
    return {
        init: init,
        refresh: refresh
    };
})();
