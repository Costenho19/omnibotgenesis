/**
 * OMNIX Dashboard V6.5 - API Client
 * Centralized API communication layer
 */

const OmnixAPI = (function() {
    'use strict';

    const API_BASE = '';

    async function get(endpoint) {
        try {
            const response = await fetch(`${API_BASE}${endpoint}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`API Error [${endpoint}]:`, error);
            return { success: false, error: error.message };
        }
    }

    async function post(endpoint, data) {
        try {
            const response = await fetch(`${API_BASE}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`API Error [${endpoint}]:`, error);
            return { success: false, error: error.message };
        }
    }

    return {
        getMetrics: () => get('/api/metrics'),
        getTrades: () => get('/api/trades'),
        getPositions: () => get('/api/positions'),
        getEquityCurve: () => get('/api/equity-curve'),
        getActiveSignals: () => get('/api/signals/active'),
        getCryptoPrices: () => get('/api/market/crypto'),
        getVolume: () => get('/api/market/volume'),
        getOHLC: (symbol) => get(`/api/market/ohlc/${symbol}`),
        getFearGreed: () => get('/api/market/fear-greed'),
        getNews: () => get('/api/news'),
        getFinnhubNews: (category = 'crypto') => get(`/api/market/finnhub-news?category=${category}`),
        getSystemStatus: () => get('/api/system/status'),
        getHealth: () => get('/api/health'),
        get,
        post
    };
})();

if (typeof window !== 'undefined') {
    window.OmnixAPI = OmnixAPI;
}
