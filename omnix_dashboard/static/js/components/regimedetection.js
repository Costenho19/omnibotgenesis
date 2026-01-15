(function() {
    'use strict';
    
    const REFRESH_INTERVAL = 15000;
    
    function formatNumber(num) {
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
        return num.toFixed(0);
    }
    
    function renderRegimeDashboard(data) {
        const container = document.getElementById('regime-detection-widget');
        if (!container) return;
        
        if (!data.success) {
            container.innerHTML = `
                <div class="regime-widget regime-error">
                    <div class="regime-error-icon">⚠️</div>
                    <div class="regime-error-text">${data.error || 'Failed to load regime data'}</div>
                </div>
            `;
            return;
        }
        
        const regime = data.current_regime;
        const status = data.system_status;
        const vetos = data.veto_summary['24h'] || [];
        const signals = data.regime_performance || [];
        const transitions = data.transitions || [];
        
        const regimeConfig = {
            'BULLISH': { icon: '📈', color: 'var(--accent-green)', name: 'BULLISH' },
            'BEARISH': { icon: '📉', color: 'var(--accent-red)', name: 'BEARISH' },
            'RANGING': { icon: '📊', color: 'var(--accent-yellow)', name: 'RANGING' },
            'UNKNOWN': { icon: '❓', color: 'var(--text-muted)', name: 'UNKNOWN' }
        };
        
        const config = regimeConfig[regime.type] || regimeConfig['UNKNOWN'];
        
        const statusConfig = {
            'DEFENSIVE': { text: 'DEFENSIVO', class: 'regime-badge-warning' },
            'ANALYZING': { text: 'ANALIZANDO', class: 'regime-badge-success' },
            'PROTECTIVE': { text: 'PROTECTIVO', class: 'regime-badge-danger' },
            'MONITORING': { text: 'MONITOREANDO', class: 'regime-badge-info' }
        };
        
        const statusCfg = statusConfig[status.status] || statusConfig['MONITORING'];
        
        const vetoIcons = {
            'BLACK_SWAN': '🦢',
            'COHERENCE_GATE': '🚧',
            'MC_VETO': '🎲',
            'RMS_VETO': '⚠️'
        };
        
        const totalEvents = signals.reduce((sum, s) => sum + (s.events_24h || 0), 0);
        
        let vetosHtml = '';
        if (vetos.length > 0) {
            // ADR-010: Est. Loss Avoided = Notional × 0.6%
            const estLossAvoided = (status.capital_protected_24h || 0) * 0.006;
            vetosHtml = `
                <div class="regime-veto-summary">
                    <div class="regime-veto-total">
                        <span class="regime-veto-total-value">${status.total_vetos_24h.toLocaleString()}</span>
                        <span class="regime-veto-total-label">Vetos Totales</span>
                    </div>
                    <div class="regime-veto-capital" title="Pérdida estimada evitada (0.6% del notional bloqueado)">
                        <span class="regime-veto-capital-value">$${formatNumber(estLossAvoided)}</span>
                        <span class="regime-veto-capital-label">Est. Pérdida Evitada*</span>
                    </div>
                </div>
                <div class="regime-veto-list">
                    ${vetos.map(v => `
                        <div class="regime-veto-item">
                            <div class="regime-veto-icon">${vetoIcons[v.type] || '🛡️'}</div>
                            <div class="regime-veto-info">
                                <div class="regime-veto-type">${(v.type || 'UNKNOWN').replace(/_/g, ' ')}</div>
                                <div class="regime-veto-count">${v.count.toLocaleString()} bloqueos</div>
                            </div>
                            <div class="regime-veto-capital">$${formatNumber(v.capital_blocked)}</div>
                        </div>
                    `).join('')}
                </div>
            `;
        } else {
            vetosHtml = '<div class="regime-empty">Sin vetos en 24h</div>';
        }
        
        let signalsHtml = '';
        if (signals.length > 0) {
            signalsHtml = signals.map(s => {
                const pct = totalEvents > 0 ? (s.events_24h / totalEvents * 100) : 0;
                const color = s.regime === 'BULLISH' ? 'var(--accent-green)' : 
                              (s.regime === 'BEARISH' ? 'var(--accent-red)' : 'var(--accent-yellow)');
                return `
                    <div class="regime-signal-bar-item">
                        <div class="regime-signal-bar-header">
                            <span class="regime-signal-name">${s.regime}</span>
                            <span class="regime-signal-pct">${pct.toFixed(1)}%</span>
                        </div>
                        <div class="regime-signal-bar-track">
                            <div class="regime-signal-bar-fill" style="width: ${pct}%; background: ${color};"></div>
                        </div>
                        <div class="regime-signal-bar-stats">
                            <span>${(s.events_24h || 0).toLocaleString()} eventos</span>
                            <span>EMA: ${(s.avg_ema_score || 0).toFixed(1)}</span>
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            signalsHtml = '<div class="regime-empty">Sin señales recientes</div>';
        }
        
        let transitionsHtml = '';
        if (transitions.length > 0) {
            transitionsHtml = transitions.map(t => {
                const time = t.timestamp ? new Date(t.timestamp).toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' }) : '--:--';
                return `
                    <div class="regime-transition-item">
                        <span class="regime-transition-from">${t.from}</span>
                        <span class="regime-transition-arrow">→</span>
                        <span class="regime-transition-to">${t.to}</span>
                        <span class="regime-transition-time">${time}</span>
                    </div>
                `;
            }).join('');
        } else {
            transitionsHtml = '<div class="regime-empty">Sin transiciones en 24h</div>';
        }
        
        container.innerHTML = `
            <div class="regime-widget">
                <div class="regime-header">
                    <div class="regime-title">
                        <span class="regime-icon">🎯</span>
                        <span>Tendencia de Mercado</span>
                        <span class="regime-subtitle" title="Basado en señales EMA y flujo de capital. Diferente del 'Trading Regime' que mide nuestro performance.">(EMA Signals)</span>
                    </div>
                    <div class="regime-badge ${statusCfg.class}">${statusCfg.text}</div>
                </div>
                
                <div class="regime-current">
                    <div class="regime-type-display">
                        <div class="regime-type-icon" style="background: ${config.color};">${config.icon}</div>
                        <div class="regime-type-info">
                            <div class="regime-type-name" style="color: ${config.color};">${config.name}</div>
                            <div class="regime-type-label">${regime.label}</div>
                        </div>
                    </div>
                    <div class="regime-metrics">
                        <div class="regime-metric">
                            <div class="regime-metric-value">${regime.confidence_pct}%</div>
                            <div class="regime-metric-label">Confianza</div>
                        </div>
                        <div class="regime-metric">
                            <div class="regime-metric-value">${regime.coherence_score}%</div>
                            <div class="regime-metric-label">Coherencia</div>
                        </div>
                        <div class="regime-metric">
                            <div class="regime-metric-value">${regime.ema_score.toFixed(1)}</div>
                            <div class="regime-metric-label">EMA Score</div>
                        </div>
                    </div>
                </div>

                <div class="regime-message">
                    <div class="regime-message-icon">💡</div>
                    <div class="regime-message-text">${status.message}</div>
                </div>

                <div class="regime-section">
                    <div class="regime-section-title">Actividad de Vetos (24h)</div>
                    <div class="regime-vetos">${vetosHtml}</div>
                </div>

                <div class="regime-section">
                    <div class="regime-section-title">Distribución de Señales (24h)</div>
                    <div class="regime-signals">
                        <div class="regime-signal-bars">${signalsHtml}</div>
                    </div>
                </div>

                <div class="regime-section">
                    <div class="regime-section-title">Transiciones Recientes</div>
                    <div class="regime-transitions">
                        <div class="regime-transition-list">${transitionsHtml}</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    function fetchRegimeDashboard() {
        const apiKey = window.OMNIX_API_KEY || 'omnix-dashboard-2024';
        
        fetch('/api/regime/dashboard', {
            headers: {
                'X-API-Key': apiKey
            }
        })
        .then(response => response.json())
        .then(data => {
            renderRegimeDashboard(data);
        })
        .catch(error => {
            console.error('Error fetching regime dashboard:', error);
            const container = document.getElementById('regime-detection-widget');
            if (container) {
                container.innerHTML = `
                    <div class="regime-widget regime-error">
                        <div class="regime-error-icon">⚠️</div>
                        <div class="regime-error-text">Error loading regime data</div>
                    </div>
                `;
            }
        });
    }
    
    document.addEventListener('DOMContentLoaded', function() {
        fetchRegimeDashboard();
        setInterval(fetchRegimeDashboard, REFRESH_INTERVAL);
    });
    
    window.refreshRegimeDashboard = fetchRegimeDashboard;
})();
