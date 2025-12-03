var OmnixStatusBar = (function() {
    'use strict';
    
    var config = {
        healthEndpoint: '/api/health',
        refreshInterval: 15000,
        elements: {
            botStatus: null,
            dbStatus: null,
            krakenStatus: null,
            connectionDot: null
        }
    };
    
    function init() {
        config.elements.botStatus = document.getElementById('status-bot');
        config.elements.dbStatus = document.getElementById('status-db');
        config.elements.krakenStatus = document.getElementById('status-kraken');
        config.elements.connectionDot = document.getElementById('connection-dot');
        
        if (config.elements.botStatus || config.elements.dbStatus || config.elements.krakenStatus) {
            fetchHealthStatus();
            setInterval(fetchHealthStatus, config.refreshInterval);
        }
    }
    
    function fetchHealthStatus() {
        fetch(config.healthEndpoint)
            .then(function(response) {
                return response.json();
            })
            .then(function(data) {
                updateStatusBar(data);
            })
            .catch(function(error) {
                console.error('Health check failed:', error);
                setAllOffline();
            });
    }
    
    function updateStatusBar(data) {
        var isHealthy = data.status === 'healthy';
        var dbConnected = data.db_connected === true;
        
        if (config.elements.botStatus) {
            updateStatusItem(config.elements.botStatus, isHealthy, 'BOT');
        }
        
        if (config.elements.dbStatus) {
            updateStatusItem(config.elements.dbStatus, dbConnected, 'DATABASE');
        }
        
        if (config.elements.krakenStatus) {
            updateStatusItem(config.elements.krakenStatus, true, 'KRAKEN');
        }
        
        if (config.elements.connectionDot) {
            if (isHealthy && dbConnected) {
                config.elements.connectionDot.className = 'w-2 h-2 rounded-full bg-green-500 pulse-live';
            } else if (dbConnected) {
                config.elements.connectionDot.className = 'w-2 h-2 rounded-full bg-yellow-500';
            } else {
                config.elements.connectionDot.className = 'w-2 h-2 rounded-full bg-red-500';
            }
        }
        
        var dbStatusText = document.getElementById('db-status');
        if (dbStatusText) {
            if (dbConnected) {
                dbStatusText.textContent = 'DB CONNECTED';
                dbStatusText.className = 'text-xs text-green-400 mono';
            } else {
                dbStatusText.textContent = 'DB OFFLINE';
                dbStatusText.className = 'text-xs text-red-400 mono';
            }
        }
    }
    
    function updateStatusItem(element, isOnline, label) {
        var dot = element.querySelector('.status-dot');
        var text = element.querySelector('span:last-child');
        
        if (dot) {
            if (isOnline) {
                dot.className = 'status-dot status-online';
            } else {
                dot.className = 'status-dot status-offline';
            }
        }
        
        if (text && label) {
            text.textContent = label + (isOnline ? ' ONLINE' : ' OFFLINE');
        }
    }
    
    function setAllOffline() {
        if (config.elements.botStatus) {
            updateStatusItem(config.elements.botStatus, false, 'BOT');
        }
        if (config.elements.dbStatus) {
            updateStatusItem(config.elements.dbStatus, false, 'DATABASE');
        }
        if (config.elements.krakenStatus) {
            updateStatusItem(config.elements.krakenStatus, false, 'KRAKEN');
        }
        
        if (config.elements.connectionDot) {
            config.elements.connectionDot.className = 'w-2 h-2 rounded-full bg-red-500';
        }
        
        var dbStatusText = document.getElementById('db-status');
        if (dbStatusText) {
            dbStatusText.textContent = 'OFFLINE';
            dbStatusText.className = 'text-xs text-red-400 mono';
        }
    }
    
    return {
        init: init,
        refresh: fetchHealthStatus
    };
})();

document.addEventListener('DOMContentLoaded', function() {
    OmnixStatusBar.init();
});
