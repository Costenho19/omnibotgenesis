var CalibrationProgressWidget = (function() {
    'use strict';
    
    var containerId = null;
    var isInitialized = false;
    
    function init(id) {
        containerId = id || 'calibration-progress-widget';
        isInitialized = true;
        console.log('CalibrationProgressWidget initialized');
        refresh();
    }
    
    function refresh() {
        if (!isInitialized) return Promise.resolve();
        
        return OmnixAPI.get('/api/system/calibration-progress')
            .then(function(data) {
                if (data && data.success) {
                    render(data);
                } else {
                    renderError('Unable to load calibration data');
                }
            })
            .catch(function(err) {
                console.error('CalibrationProgress error:', err);
                renderError('Connection error');
            });
    }
    
    function render(data) {
        var container = document.getElementById(containerId);
        if (!container) return;
        
        var phases = data.phases || [];
        var overallProgress = data.overall_progress || 0;
        var status = data.status || 'CALIBRATING';
        var currentPhase = data.current_phase || 1;
        
        var statusClass = status === 'READY' ? 'ready' : 'calibrating';
        
        var phasesHtml = phases.map(function(phase) {
            var phaseClass = phase.complete ? 'complete' : (phase.id === currentPhase ? 'active' : 'pending');
            var icon = getIcon(phase.icon, phase.complete);
            
            return '<div class="calibration-phase ' + phaseClass + '">' +
                '<div class="phase-header">' +
                    '<div class="phase-icon">' + icon + '</div>' +
                    '<div class="phase-info">' +
                        '<div class="phase-name">' + phase.name + '</div>' +
                        '<div class="phase-desc">' + phase.description + '</div>' +
                    '</div>' +
                    '<div class="phase-pct">' + Math.round(phase.progress) + '%</div>' +
                '</div>' +
                '<div class="phase-bar">' +
                    '<div class="phase-bar-fill" style="width: ' + phase.progress + '%"></div>' +
                '</div>' +
            '</div>';
        }).join('');
        
        container.innerHTML = 
            '<div class="calibration-container">' +
                '<div class="calibration-header">' +
                    '<div class="calibration-title">' +
                        '<span class="title-text">System Calibration</span>' +
                        '<span class="status-badge ' + statusClass + '">' + status + '</span>' +
                    '</div>' +
                    '<div class="overall-progress">' +
                        '<span class="overall-pct">' + Math.round(overallProgress) + '%</span>' +
                        '<span class="overall-label">Overall</span>' +
                    '</div>' +
                '</div>' +
                '<div class="calibration-phases">' + phasesHtml + '</div>' +
            '</div>';
    }
    
    function renderError(message) {
        var container = document.getElementById(containerId);
        if (!container) return;
        
        container.innerHTML = 
            '<div class="calibration-container error">' +
                '<div class="calibration-header">' +
                    '<span class="title-text">System Calibration</span>' +
                '</div>' +
                '<div class="calibration-error">' + message + '</div>' +
            '</div>';
    }
    
    function getIcon(iconName, complete) {
        if (complete) {
            return '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>';
        }
        
        var icons = {
            'database': '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>',
            'cpu': '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/></svg>',
            'sliders': '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/></svg>',
            'rocket': '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/><path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/></svg>'
        };
        return icons[iconName] || icons['database'];
    }
    
    return {
        init: init,
        refresh: refresh
    };
})();
