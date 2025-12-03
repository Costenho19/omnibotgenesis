/**
 * OMNIX Dashboard V6.5.2 - API Client
 * Centralized API communication layer with retry/backoff
 */

const OmnixAPI = (function() {
    'use strict';

    const API_BASE = '';
    
    const DEFAULT_RETRY_OPTIONS = {
        maxRetries: 3,
        baseDelay: 1000,
        maxDelay: 10000,
        backoffFactor: 2
    };

    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    function calculateDelay(attempt, options) {
        const delay = Math.min(
            options.baseDelay * Math.pow(options.backoffFactor, attempt),
            options.maxDelay
        );
        const jitter = delay * 0.2 * Math.random();
        return delay + jitter;
    }

    async function fetchWithRetry(url, options = {}, retryOptions = {}) {
        const opts = { ...DEFAULT_RETRY_OPTIONS, ...retryOptions };
        let lastError;

        for (let attempt = 0; attempt <= opts.maxRetries; attempt++) {
            try {
                const response = await fetch(url, {
                    ...options,
                    signal: AbortSignal.timeout(15000)
                });

                if (!response.ok) {
                    if (response.status >= 500 && attempt < opts.maxRetries) {
                        throw new Error(`Server error: ${response.status}`);
                    }
                    throw new Error(`HTTP error: ${response.status}`);
                }

                return await response.json();
            } catch (error) {
                lastError = error;
                
                if (error.name === 'AbortError') {
                    console.warn(`[API] Request timeout for ${url}`);
                }

                if (attempt < opts.maxRetries) {
                    const delay = calculateDelay(attempt, opts);
                    console.log(`[API] Retry ${attempt + 1}/${opts.maxRetries} for ${url} in ${Math.round(delay)}ms`);
                    await sleep(delay);
                }
            }
        }

        console.error(`[API] All retries failed for ${url}:`, lastError);
        return { success: false, error: lastError.message, retryExhausted: true };
    }

    async function get(endpoint, retryOptions = {}) {
        return fetchWithRetry(`${API_BASE}${endpoint}`, {}, retryOptions);
    }

    async function post(endpoint, data, retryOptions = {}) {
        return fetchWithRetry(`${API_BASE}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        }, retryOptions);
    }

    async function safeGet(endpoint, fallback = null) {
        const result = await get(endpoint);
        if (result.success === false || result.error) {
            return fallback;
        }
        return result;
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
        post,
        safeGet,
        fetchWithRetry
    };
})();

if (typeof window !== 'undefined') {
    window.OmnixAPI = OmnixAPI;
}
