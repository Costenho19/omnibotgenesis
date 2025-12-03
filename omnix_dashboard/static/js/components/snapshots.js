/**
 * OMNIX Dashboard V6.5.2 - Audited Snapshots Component
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
        console.log('AuditedSnapshots widget initialized');
    }

    async function refresh() {
        try {
            const [snapshotsRes, chainRes] = await Promise.all([
                OmnixAPI.fetchWithRetry('/api/snapshots?limit=10'),
                OmnixAPI.fetchWithRetry('/api/snapshots/chain/verify')
            ]);

            if (snapshotsRes.success) {
                _snapshots = snapshotsRes.snapshots || [];
            }

            if (chainRes.success) {
                _chainStatus = chainRes;
            }

            render();
        } catch (error) {
            console.error('AuditedSnapshots refresh error:', error);
            renderError();
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

    function renderError() {
        const container = document.getElementById(_containerId);
        if (!container) return;

        container.innerHTML = `
            <div class="snapshots-header">
                <div class="snapshots-title">
                    <span class="snapshots-icon">📋</span>
                    <span>AUDITED SNAPSHOTS</span>
                </div>
            </div>
            <div class="snapshots-error">
                Unable to load snapshots. Check database connection.
            </div>
        `;
    }

    async function createSnapshot() {
        try {
            const response = await fetch('/api/snapshots/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type: 'daily' })
            });
            const data = await response.json();
            
            if (data.success) {
                console.log('Snapshot created:', data.checksum);
                await refresh();
            } else {
                console.error('Failed to create snapshot:', data.error);
            }
        } catch (error) {
            console.error('Create snapshot error:', error);
        }
    }

    async function verify(snapshotId) {
        try {
            const response = await OmnixAPI.fetchWithRetry(`/api/snapshots/${snapshotId}/verify`);
            if (response.success) {
                console.log('Verification result:', response.verification_status);
                await refresh();
            }
        } catch (error) {
            console.error('Verify snapshot error:', error);
        }
    }

    async function verifyAll() {
        try {
            const response = await OmnixAPI.fetchWithRetry('/api/snapshots/chain/verify');
            if (response.success) {
                _chainStatus = response;
                render();
            }
        } catch (error) {
            console.error('Verify chain error:', error);
        }
    }

    function formatDate(dateStr) {
        if (typeof OmnixTime !== 'undefined') {
            return OmnixTime.formatDate(new Date(dateStr));
        }
        return new Date(dateStr).toLocaleDateString();
    }

    function formatNumber(num) {
        if (num === null || num === undefined) return '0';
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
