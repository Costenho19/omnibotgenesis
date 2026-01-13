const RecommendedActionsWidget = (function() {
    'use strict';
    
    let containerId = null;
    
    function init(id) {
        containerId = id;
        refresh();
        console.log('RecommendedActionsWidget initialized');
    }
    
    async function refresh() {
        if (!containerId) return;
        
        try {
            const response = await fetch('/api/system/recommended-actions');
            const data = await response.json();
            
            if (data.success) {
                render(data);
            } else {
                renderError('Unable to load recommendations');
            }
        } catch (error) {
            console.error('RecommendedActions error:', error);
            renderError('Connection error');
        }
    }
    
    function render(data) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        const actions = data.actions || [];
        
        const getPriorityColor = (priority) => {
            switch (priority) {
                case 'high': return '#ff6b6b';
                case 'medium': return '#ffc107';
                case 'low': return '#00d4aa';
                default: return '#6c757d';
            }
        };
        
        const getPriorityLabel = (priority) => {
            switch (priority) {
                case 'high': return 'HIGH';
                case 'medium': return 'MEDIUM';
                case 'low': return 'LOW';
                default: return 'INFO';
            }
        };
        
        const getIcon = (iconName) => {
            const icons = {
                'database': '🗄️',
                'trending-up': '📈',
                'percent': '💰',
                'rocket': '🚀',
                'shield': '🛡️',
                'flag': '🏁',
                'target': '🎯',
                'activity': '📊'
            };
            return icons[iconName] || '📌';
        };
        
        const actionsHtml = actions.map(action => `
            <div class="ra-action-item" style="border-left: 3px solid ${getPriorityColor(action.priority)}">
                <div class="ra-action-header">
                    <span class="ra-action-icon">${getIcon(action.icon)}</span>
                    <span class="ra-action-title">${action.title}</span>
                    <span class="ra-priority-badge" style="background: ${getPriorityColor(action.priority)}20; color: ${getPriorityColor(action.priority)}">
                        ${getPriorityLabel(action.priority)}
                    </span>
                </div>
                <div class="ra-action-description">${action.description}</div>
                <div class="ra-action-reason">${action.reason}</div>
            </div>
        `).join('');
        
        container.innerHTML = `
            <div class="ra-container">
                <div class="ra-header">
                    <span class="ra-header-icon">💡</span>
                    <span class="ra-header-title">Recommended Actions</span>
                    <span class="ra-count-badge">${actions.length}</span>
                </div>
                <div class="ra-actions-list">
                    ${actionsHtml}
                </div>
            </div>
        `;
    }
    
    function renderError(message) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        container.innerHTML = `
            <div class="ra-container ra-error">
                <div class="ra-header">
                    <span class="ra-header-icon">💡</span>
                    <span class="ra-header-title">Recommended Actions</span>
                </div>
                <div class="ra-error-message">${message}</div>
            </div>
        `;
    }
    
    return {
        init,
        refresh
    };
})();

window.RecommendedActionsWidget = RecommendedActionsWidget;
