"""
OMNIX Backtest Phase 0 — Step 1: Fetch Historical OHLCV
Fetches hourly OHLCV data from Kraken public API for Jul 6 – Aug 18, 2025.

Uses only Kraken's public endpoints (no API key required).
Data stored in backtest_phase0_ohlcv table.
"""

import os
import time
import requests
import psycopg2
from datetime import datetime, timezone

DATABASE_URL = os.environ['DATABASE_URL']

PAIRS = {
    'BTC': 'XBTUSD',
    'ETH': 'XETHZUSD',
    'SOL': 'SOLUSD',
    'AVAX': 'AVAXUSD',
}

INTERVAL = 60  # minutes (hourly candles)

# Jul 6 2025 00:00 UTC
SINCE_TIMESTAMP = int(datetime(2025, 7, 6, 0, 0, 0, tzinfo=timezone.utc).timestamp())

# Aug 19 2025 00:00 UTC (one day past end to capture Aug 18)
END_TIMESTAMP = int(datetime(2025, 8, 19, 0, 0, 0, tzinfo=timezone.utc).timestamp())

KRAKEN_BASE = "https://api.kraken.com/0/public/OHLC"


def fetch_ohlcv(kraken_pair: str, since: int) -> list:
    """Fetch OHLCV candles from Kraken public API."""
    url = f"{KRAKEN_BASE}?pair={kraken_pair}&interval={INTERVAL}&since={since}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    
    if data.get('error'):
        raise ValueError(f"Kraken API error: {data['error']}")
    
    result_key = [k for k in data['result'].keys() if k != 'last'][0]
    candles = data['result'][result_key]
    return candles, data['result']['last']


def main():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    total_inserted = 0
    
    for asset, kraken_pair in PAIRS.items():
        print(f"\n=== Fetching {asset} ({kraken_pair}) ===")
        
        since = SINCE_TIMESTAMP
        asset_count = 0
        
        while True:
            try:
                candles, last = fetch_ohlcv(kraken_pair, since)
            except Exception as e:
                print(f"  ERROR fetching {asset}: {e}")
                break
            
            if not candles:
                print(f"  No more candles for {asset}")
                break
            
            batch = []
            for c in candles:
                ts = int(c[0])
                if ts >= END_TIMESTAMP:
                    continue
                candle_dt = datetime.fromtimestamp(ts, tz=timezone.utc).replace(tzinfo=None)
                batch.append((
                    asset,
                    candle_dt,
                    float(c[1]),  # open
                    float(c[2]),  # high
                    float(c[3]),  # low
                    float(c[4]),  # close
                    float(c[6]),  # volume
                ))
            
            if batch:
                cur.executemany("""
                    INSERT INTO backtest_phase0_ohlcv
                        (asset, candle_time, open, high, low, close, volume)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (asset, candle_time) DO NOTHING
                """, batch)
                conn.commit()
                asset_count += len(batch)
            
            # Kraken paginates by 'last' cursor
            if last >= END_TIMESTAMP or last == since:
                break
            since = last
            time.sleep(1.2)  # Respect Kraken rate limits
        
        print(f"  {asset}: {asset_count} candles inserted")
        total_inserted += asset_count
        time.sleep(2)
    
    # Verify
    cur.execute("""
        SELECT asset, COUNT(*), MIN(candle_time)::date, MAX(candle_time)::date
        FROM backtest_phase0_ohlcv
        GROUP BY asset ORDER BY asset
    """)
    print("\n=== VERIFICATION ===")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]} candles | {row[2]} → {row[3]}")
    
    print(f"\nTotal inserted: {total_inserted}")
    cur.close()
    conn.close()
    print("DONE — 01_fetch_ohlcv.py complete")


if __name__ == '__main__':
    main()
