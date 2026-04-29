/**
 * OMNIX Dashboard V6.5.4 - Audited Snapshots Component
 * Displays cryptographically verified snapshots for investor auditing
 */

const AuditedSnapshots = (function() {
    'use strict';

    const STATUS_COLORS = {
        'verified': { bg: '#00ff8820', border: '#00ff88', text: '#00ff88', icon: '✓' },
        'pending': { bg: '#ffaa0020', border: '#ffaa00', text: '#ffaa00', icon: '○' },
        'failed': { bg: '#ff444420', border: '#ff4444', text: '#ff4444', icon: '✗' }
    };

    let _containerId = null;
    let _snapshots = [];
    let _chainStatus = null;

    function init(containerId) {
        _containerId = containerId;
    }

    async function refresh() {
        try {
            const [snapshotsRes, chainRes] = await Promise.allSettled([
                OmnixAPI.fetchWithRetry('/api/snapshots?limit=10'),
                OmnixAPI.fetchWithRetry('/api/snapshots/chain/verify')
            ]);

            let hasErrors = false;
            let errorMessages = [];

            if (snapshotsRes.status === 'fulfilled' && snapshotsRes.value.success) {
                _snapshots = snapshotsRes.value.snapshots || [];
            } else if (snapshotsRes.status === 'rejected') {
                hasErrors = true;
                errorMessages.push('Failed to load snapshots');
                console.error('Snapshots fetch error:', snapshotsRes.reason);
            } else if (snapshotsRes.value && !snapshotsRes.value.success) {
                hasErrors = true;
                errorMessages.push(snapshotsRes.value.error || 'Loading...');
            }

            if (chainRes.status === 'fulfilled' && chainRes.value.success) {
                _chainStatus = chainRes.value;
            } else if (chainRes.status === 'rejected') {
                console.warn('Chain verification unavailable:', chainRes.reason);
            } else if (chainRes.value && !chainRes.value.success) {
                console.warn('Chain verification error:', chainRes.value.error);
            }

            if (hasErrors && _snapshots.length === 0) {
                renderError(errorMessages.join('. '));
            } else {
                render();
            }
        } catch (error) {
            console.error('AuditedSnapshots refresh error:', error);
            renderError('Connection error. Retrying...');
        }
    }

    function render() {
        const container = document.getElementById(_containerId);
        if (!container) return;

        const chainColor = _chainStatus?.chain_valid ? STATUS_COLORS.verified : STATUS_COLORS.failed;
        const chainIcon = _chainStatus?.chain_valid ? '🔗' : '⚠️';

        container.innerHTML = `
            <div class="snapshots-header">
                <div class="snapshots-title">
                    <span class="snapshots-icon">📋</span>
                    <span>AUDITED SNAPSHOTS</span>
                </div>
                <div class="chain-status" style="background: ${chainColor.bg}; border-color: ${chainColor.border}; color: ${chainColor.text}">
                    ${chainIcon} ${_chainStatus?.chain_valid ? 'CHAIN INTACT' : 'CHAIN ISSUE'}
                </div>
            </div>

            <div class="chain-summary">
                <div class="chain-stat">
                    <span class="chain-stat-value">${_chainStatus?.total_snapshots || 0}</span>
                    <span class="chain-stat-label">Total</span>
                </div>
                <div class="chain-stat">
                    <span class="chain-stat-value">${_chainStatus?.verified_count || 0}</span>
                    <span class="chain-stat-label">Verified</span>
                </div>
                <div class="chain-stat">
                    <span class="chain-stat-value" style="color: ${_chainStatus?.chain_valid ? '#00ff88' : '#ff4444'}">
                        ${_chainStatus?.chain_valid ? '100%' : Math.round((_chainStatus?.verified_count / _chainStatus?.total_snapshots) * 100) + '%'}
                    </span>
                    <span class="chain-stat-label">Integrity</span>
                </div>
            </div>

            <div class="snapshots-list">
                ${renderSnapshotsList()}
            </div>

            <div class="snapshots-actions">
                <button class="snapshot-btn" onclick="AuditedSnapshots.createSnapshot()">
                    + Create Snapshot
                </button>
                <button class="snapshot-btn secondary" onclick="AuditedSnapshots.verifyAll()">
                    Verify Chain
                </button>
            </div>
        `;
    }

    function renderSnapshotsList() {
        if (!_snapshots || _snapshots.length === 0) {
            return '<div class="no-snapshots">No snapshots yet. Create one to start auditing.</div>';
        }

        return _snapshots.map(s => {
            const colors = STATUS_COLORS[s.status] || STATUS_COLORS.pending;
            const dateStr = s.date ? formatDate(s.date) : '--';
            
            return `
                <div class="snapshot-item" onclick="AuditedSnapshots.verify(${s.id})">
                    <div class="snapshot-status" style="background: ${colors.bg}; border-color: ${colors.border}; color: ${colors.text}">
                        ${colors.icon}
                    </div>
                    <div class="snapshot-info">
                        <div class="snapshot-date">${dateStr}</div>
                        <div class="snapshot-type">${s.type.toUpperCase()}</div>
                    </div>
                    <div class="snapshot-metrics">
                        <div class="snapshot-equity">$${formatNumber(s.total_equity)}</div>
                        <div class="snapshot-pnl ${s.total_pnl >= 0 ? 'positive' : 'negative'}">
                            ${s.total_pnl >= 0 ? '+' : ''}$${formatNumber(s.total_pnl)}
                        </div>
                    </div>
                    <div class="snapshot-chain">
                        ${s.has_chain ? '🔗' : '○'}
                    </div>
                </div>
            `;
        }).join('');
    }

    function renderError(message = 'Unable to load snapshots') {
        const container = document.getElementById(_containerId);
        if (!container) return;

        container.innerHTML = `
            <div class="snapshots-header">
                <div class="snapshots-title">
                    <span class="snapshots-icon">📋</span>
                    <span>AUDITED SNAPSHOTS</span>
                </div>
                <div class="chain-status" style="background: ${STATUS_COLORS.failed.bg}; border-color: ${STATUS_COLORS.failed.border}; color: ${STATUS_COLORS.failed.text}">
                    ⚠️ ERROR
                </div>
            </div>
            <div class="snapshots-error">
                <div class="error-icon">⚠️</div>
                <div class="error-message">${message}</div>
                <div class="error-hint">Check database connection or API key configuration.</div>
                <button class="snapshot-btn retry-btn" onclick="AuditedSnapshots.refresh()">
                    ↻ Retry
                </button>
            </div>
        `;
    }

    async function createSnapshot() {
        showNotification('Creating snapshot...', 'pending');
        try {
            const data = await OmnixAPI.fetchWithRetry('/api/snapshots/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type: 'daily' })
            });
            
            if (data.success) {
                const msg = data.already_exists 
                    ? 'Snapshot already exists for today' 
                    : 'Snapshot created successfully!';
                console.log('Snapshot:', data.checksum);
                showNotification(msg, 'success');
                await refresh();
            } else {
                console.error('Failed to create snapshot:', data.error);
                showNotification(`Failed: ${data.error || 'Unknown error'}`, 'error');
            }
        } catch (error) {
            console.error('Create snapshot error:', error);
            const errorMsg = error.message?.includes('401') 
                ? 'Authentication required' 
                : 'Network error creating snapshot';
            showNotification(errorMsg, 'error');
        }
    }

    async function verify(snapshotId) {
        showNotification('Verifying snapshot...', 'pending');
        try {
            const response = await OmnixAPI.fetchWithRetry(`/api/snapshots/${snapshotId}/verify`);
            if (response.success) {
                const status = response.verification_status;
                const isValid = status === 'verified';
                showNotification(
                    isValid ? 'Snapshot verified successfully!' : 'Verification failed - integrity issue detected',
                    isValid ? 'success' : 'error'
                );
                await refresh();
            } else {
                showNotification(`Verification error: ${response.error}`, 'error');
            }
        } catch (error) {
            console.error('Verify snapshot error:', error);
            showNotification('Network error during verification', 'error');
        }
    }

    async function verifyAll() {
        showNotification('Verifying entire chain...', 'pending');
        try {
            const response = await OmnixAPI.fetchWithRetry('/api/snapshots/chain/verify');
            if (response.success) {
                _chainStatus = response;
                const isValid = response.chain_valid;
                showNotification(
                    isValid 
                        ? `Chain verified: ${response.verified_count} snapshots intact!` 
                        : `Chain issues: ${response.failed_count} snapshot(s) failed verification`,
                    isValid ? 'success' : 'error'
                );
                render();
            } else {
                showNotification(`Chain verification error: ${response.error}`, 'error');
            }
        } catch (error) {
            console.error('Verify chain error:', error);
            showNotification('Network error during chain verification', 'error');
        }
    }

    function showNotification(message, type = 'info') {
        const colors = {
            success: { bg: '#00ff8830', border: '#00ff88', text: '#00ff88' },
            error: { bg: '#ff444430', border: '#ff4444', text: '#ff4444' },
            pending: { bg: '#ffaa0030', border: '#ffaa00', text: '#ffaa00' },
            info: { bg: '#4a90d930', border: '#4a90d9', text: '#4a90d9' }
        };
        const color = colors[type] || colors.info;
        
        let notification = document.querySelector('.snapshots-notification');
        if (!notification) {
            notification = document.createElement('div');
            notification.className = 'snapshots-notification';
            document.body.appendChild(notification);
        }
        
        notification.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 4px;
            background: ${color.bg};
            border: 1px solid ${color.border};
            color: ${color.text};
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            z-index: 9999;
            animation: slideIn 0.3s ease-out;
        `;
        notification.textContent = message;
        
        if (type !== 'pending') {
            setTimeout(() => {
                notification.style.animation = 'fadeOut 0.3s ease-out';
                setTimeout(() => notification.remove(), 300);
            }, 3000);
        }
    }

    function formatDate(dateStr) {
        if (typeof OmnixTime !== 'undefined') {
            return OmnixTime.formatDate(new Date(dateStr));
        }
        return new Date(dateStr).toLocaleDateString();
    }

    function formatNumber(num) {
        if (num === null || num === undefined || isNaN(num)) return 'N/A';
        return Math.abs(num).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    return {
        init,
        refresh,
        createSnapshot,
        verify,
        verifyAll
    };
})();

if (typeof window !== 'undefined') {
    window.AuditedSnapshots = AuditedSnapshots;
}
