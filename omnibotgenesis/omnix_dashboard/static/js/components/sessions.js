const SessionsWidget = (function() {
    'use strict';

    async function refresh() {
        try {
            const response = await OmnixAPI.fetchWithRetry('/api/system/sessions');
            
            if (response && response.success) {
                const sessions = response.sessions;
                const container = document.getElementById('sessions-value');
                
                if (container) {
                    container.textContent = sessions.active_count;
                    container.title = `${sessions.architecture} | Capacity: ${sessions.capacity}`;
                    
                    if (sessions.active_count > 0) {
                        container.classList.add('positive');
                    }
                }
            }
            return response;
        } catch (error) {
            console.error('SessionsWidget error:', error);
            const container = document.getElementById('sessions-value');
            if (container) {
                container.textContent = '1';
            }
            return null;
        }
    }

    function init() {
        console.log('SessionsWidget initialized');
        refresh();
    }

    return {
        init: init,
        refresh: refresh
    };
})();

if (typeof window !== 'undefined') {
    window.SessionsWidget = SessionsWidget;
}
