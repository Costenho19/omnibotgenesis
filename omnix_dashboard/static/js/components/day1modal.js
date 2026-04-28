/**
 * OMNIX Day 1 Welcome Modal & Track Record Timeline
 * Dynamically shows current track record day and milestone status
 */

const Day1Modal = {
    STORAGE_KEY: 'omnix_day1_accepted_v2',
    TRACK_RECORD_START: new Date('2026-01-15T00:00:00Z'),
    DAY30_DATE:  new Date('2026-02-14T00:00:00Z'),
    DAY60_DATE:  new Date('2026-03-16T00:00:00Z'),
    DAY90_DATE:  new Date('2026-04-15T00:00:00Z'),
    DAY120_DATE: new Date('2026-05-15T00:00:00Z'),

    init() {
        this.updateContent();
        if (!this.hasAccepted()) {
            this.show();
        }
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

    getDaysSinceStart() {
        const now = new Date();
        return Math.ceil((now - this.TRACK_RECORD_START) / (1000 * 60 * 60 * 24));
    },

    updateContent() {
        const currentDay = Math.max(1, this.getDaysSinceStart());

        this.updateModalHeader(currentDay);
        this.updateTimeline(currentDay);
        this.updateCountdown(currentDay);
    },

    updateModalHeader(currentDay) {
        const title    = document.getElementById('modal-title');
        const subtitle = document.getElementById('modal-subtitle');
        if (title) {
            title.textContent = 'OMNIX — Day ' + currentDay + ' of Official Track Record';
        }
        if (subtitle) {
            if (currentDay >= 120) {
                subtitle.textContent = 'Day 120 Milestone Reached — Institutional Validation Phase';
            } else if (currentDay >= 90) {
                subtitle.textContent = 'Day 90 Milestone Reached — Institutional Readiness Phase';
            } else if (currentDay >= 60) {
                subtitle.textContent = 'Day 60 Milestone Reached — Optimization Phase';
            } else if (currentDay >= 30) {
                subtitle.textContent = 'Day 30 Review Complete — Track Record Validated';
            } else {
                subtitle.textContent = 'Official Track Record Active';
            }
        }
    },

    updateTimeline(currentDay) {
        const day30El  = document.getElementById('timeline-day30');
        const day60El  = document.getElementById('timeline-day60');
        const day90El  = document.getElementById('timeline-day90');
        const day120El = document.getElementById('timeline-day120');

        if (!day30El || !day60El) return;

        if (currentDay >= 120) {
            day30El.className  = 'day1-timeline-item past';
            day30El.querySelector('.day1-timeline-label').textContent  = 'Day 30 ✓';
            day60El.className  = 'day1-timeline-item past';
            day60El.querySelector('.day1-timeline-label').textContent  = 'Day 60 ✓';
            if (day90El)  { day90El.className  = 'day1-timeline-item past';    day90El.querySelector('.day1-timeline-label').textContent  = 'Day 90 ✓'; }
            if (day120El) { day120El.className = 'day1-timeline-item current'; day120El.querySelector('.day1-timeline-label').textContent = 'Day 120 ✓'; }
        } else if (currentDay >= 90) {
            day30El.className  = 'day1-timeline-item past';
            day30El.querySelector('.day1-timeline-label').textContent  = 'Day 30 ✓';
            day60El.className  = 'day1-timeline-item past';
            day60El.querySelector('.day1-timeline-label').textContent  = 'Day 60 ✓';
            if (day90El)  { day90El.className  = 'day1-timeline-item current'; day90El.querySelector('.day1-timeline-label').textContent  = 'Day 90 ✓'; }
            if (day120El) { day120El.className = 'day1-timeline-item';         day120El.querySelector('.day1-timeline-label').textContent = 'Day 120'; }
        } else if (currentDay >= 60) {
            day30El.className  = 'day1-timeline-item past';
            day30El.querySelector('.day1-timeline-label').textContent  = 'Day 30 ✓';
            day60El.className  = 'day1-timeline-item current';
            day60El.querySelector('.day1-timeline-label').textContent  = 'Day 60 ✓';
            if (day90El)  { day90El.className  = 'day1-timeline-item'; day90El.querySelector('.day1-timeline-label').textContent  = 'Day 90'; }
            if (day120El) { day120El.className = 'day1-timeline-item'; day120El.querySelector('.day1-timeline-label').textContent = 'Day 120'; }
        } else if (currentDay >= 30) {
            day30El.className  = 'day1-timeline-item past';
            day30El.querySelector('.day1-timeline-label').textContent  = 'Day 30 ✓';
            day60El.className  = 'day1-timeline-item current';
            day60El.querySelector('.day1-timeline-label').textContent  = 'Day 60 Target';
            if (day90El)  { day90El.className  = 'day1-timeline-item'; day90El.querySelector('.day1-timeline-label').textContent  = 'Day 90'; }
            if (day120El) { day120El.className = 'day1-timeline-item'; day120El.querySelector('.day1-timeline-label').textContent = 'Day 120'; }
        } else {
            day30El.className  = 'day1-timeline-item current';
            day30El.querySelector('.day1-timeline-label').textContent  = 'Day 30';
            day60El.className  = 'day1-timeline-item';
            day60El.querySelector('.day1-timeline-label').textContent  = 'Day 60';
            if (day90El)  { day90El.className  = 'day1-timeline-item'; day90El.querySelector('.day1-timeline-label').textContent  = 'Day 90'; }
            if (day120El) { day120El.className = 'day1-timeline-item'; day120El.querySelector('.day1-timeline-label').textContent = 'Day 120'; }
        }
    },

    updateCountdown(currentDay) {
        if (currentDay === undefined) {
            currentDay = Math.max(1, this.getDaysSinceStart());
        }

        const el = document.getElementById('current-day');
        if (el) {
            el.textContent = currentDay;
        }

        const container = document.getElementById('day30-countdown');
        if (container) {
            const textEl = container.querySelector('.day30-text');
            if (textEl) {
                textEl.innerHTML = 'Day <strong>' + currentDay + '</strong>';
            }
            container.style.borderColor = '#00ff88';
            container.style.background  = 'rgba(0, 255, 136, 0.1)';

            let tooltip = 'Official Track Record Active (Jan 15, 2026 – Present)';
            if (currentDay >= 90) {
                tooltip = 'Day 90 milestone complete — Institutional Readiness Phase';
            } else if (currentDay >= 60) {
                tooltip = 'Day 60 milestone complete — Optimization Phase active';
            } else if (currentDay >= 30) {
                tooltip = 'Day 30+ milestone complete — Track Record validated';
            }
            container.title = tooltip;
        }
    },

    reset() {
        localStorage.removeItem(this.STORAGE_KEY);
        this.updateContent();
        this.show();
    }
};

document.addEventListener('DOMContentLoaded', () => {
    Day1Modal.init();
});
