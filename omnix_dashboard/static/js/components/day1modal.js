/**
 * OMNIX Day 1 Welcome Modal & Day 30 Countdown
 * Shows transparency statement on first visit
 */

const Day1Modal = {
    STORAGE_KEY: 'omnix_day1_accepted',
    DAY30_DATE: new Date('2026-02-14T00:00:00Z'),
    
    init() {
        if (!this.hasAccepted()) {
            this.show();
        }
        this.updateCountdown();
        setInterval(() => this.updateCountdown(), 60000);
    },
    
    hasAccepted() {
        return localStorage.getItem(this.STORAGE_KEY) === 'true';
    },
    
    show() {
        const modal = document.getElementById('day1-modal');
        if (modal) {
            modal.style.display = 'flex';
        }
    },
    
    hide() {
        const modal = document.getElementById('day1-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    },
    
    accept() {
        localStorage.setItem(this.STORAGE_KEY, 'true');
        this.hide();
    },
    
    updateCountdown() {
        const now = new Date();
        const trackRecordStart = new Date('2026-01-15T00:00:00Z');
        const diff = this.DAY30_DATE - now;
        const daysRemaining = Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
        
        const daysSinceStart = Math.ceil((now - trackRecordStart) / (1000 * 60 * 60 * 24));
        const currentDay = Math.max(1, Math.min(30, daysSinceStart));
        
        const el = document.getElementById('current-day');
        if (el) {
            el.textContent = currentDay;
        }
        
        const container = document.getElementById('day30-countdown');
        if (container) {
            if (daysRemaining === 0) {
                container.querySelector('.day30-text').innerHTML = 'Day <strong>30</strong>/30';
                container.style.borderColor = '#00ff88';
                container.style.background = 'rgba(0, 255, 136, 0.1)';
            } else if (daysRemaining <= 7) {
                container.style.borderColor = '#ff5722';
                container.style.background = 'rgba(255, 87, 34, 0.1)';
            }
        }
    },
    
    reset() {
        localStorage.removeItem(this.STORAGE_KEY);
        this.show();
    }
};

document.addEventListener('DOMContentLoaded', () => {
    Day1Modal.init();
});
