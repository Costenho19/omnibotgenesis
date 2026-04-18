#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNIX V6.0 ULTRA - Kraken Historical Data Downloader
Descarga datos históricos OHLCV de Kraken API con cache local
Professional-grade data acquisition system
"""

import os
import json
import time
import logging
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class KrakenDataDownloader:
    """
    Professional data downloader for Kraken Exchange
    
    Features:
    - Automatic data caching (avoid repeated API calls)
    - Rate limiting compliance (Kraken: 1 req/sec public API)
    - Multiple timeframes support (1m, 5m, 15m, 1h, 4h, 1d)
    - Data validation and cleaning
    - Progress tracking for large downloads
    """
    
    KRAKEN_API_URL = "https://api.kraken.com/0/public/OHLC"
    
    # Kraken pair name mapping (user-friendly → Kraken format)
    PAIR_ALIASES = {
        'XBTUSD': 'XXBTZUSD',
        'BTC/USD': 'XXBTZUSD',
        'BTCUSD': 'XXBTZUSD',
        'ETHUSD': 'XETHZUSD',
        'ETH/USD': 'XETHZUSD',
        'SOLUSD': 'SOLUSD',
        'SOL/USD': 'SOLUSD',
        'ADAUSD': 'ADAUSD',
        'ADA/USD': 'ADAUSD',
        'DOTUSD': 'DOTUSD',
        'DOT/USD': 'DOTUSD'
    }
    
    # Kraken interval mapping (minutes)
    INTERVALS = {
        '1m': 1,
        '5m': 5,
        '15m': 15,
        '30m': 30,
        '1h': 60,
        '4h': 240,
        '1d': 1440,
        '1w': 10080
    }
    
    def __init__(self, cache_dir: str = "omnix_testing/data_cache"):
        """
        Initialize Kraken Data Downloader
        
        Args:
            cache_dir: Directory to store cached data
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"🔧 Kraken Data Downloader inicializado")
        logger.info(f"   📂 Cache directory: {self.cache_dir}")
    
    def download_ohlcv(
        self,
        pair: str = "XBTUSD",
        interval: str = "1h",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Download OHLCV data from Kraken
        
        Args:
            pair: Trading pair (e.g., 'XBTUSD', 'BTC/USD', 'ETHUSD')
            interval: Timeframe ('1m', '5m', '15m', '1h', '4h', '1d')
            start_date: Start datetime (default: 6 months ago)
            end_date: End datetime (default: now)
            use_cache: Use cached data if available
            
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        # Convert pair to Kraken format
        kraken_pair = self.PAIR_ALIASES.get(pair.upper(), pair)
        
        if not start_date:
            start_date = datetime.now() - timedelta(days=180)  # 6 months
        if not end_date:
            end_date = datetime.now()
        
        logger.info("=" * 70)
        logger.info(f"📊 Descargando datos históricos de Kraken")
        logger.info(f"   Par: {pair} → {kraken_pair}")
        logger.info(f"   Intervalo: {interval}")
        logger.info(f"   Periodo: {start_date.date()} → {end_date.date()}")
        logger.info("=" * 70)
        
        # Check cache first
        if use_cache:
            cached_df = self._load_from_cache(kraken_pair, interval, start_date, end_date)
            if cached_df is not None:
                logger.info(f"✅ Datos cargados desde cache ({len(cached_df)} candles)")
                return cached_df
        
        # Download from Kraken API
        df = self._download_from_api(kraken_pair, interval, start_date, end_date)
        
        # Save to cache
        if use_cache and df is not None and len(df) > 0:
            self._save_to_cache(df, kraken_pair, interval)
        
        logger.info(f"✅ Descarga completada: {len(df)} candles")
        return df
    
    def _download_from_api(
        self,
        pair: str,
        interval: str,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """Download data from Kraken API with rate limiting"""
        
        if interval not in self.INTERVALS:
            raise ValueError(f"Interval no soportado: {interval}. Opciones: {list(self.INTERVALS.keys())}")
        
        interval_minutes = self.INTERVALS[interval]
        since = int(start_date.timestamp())
        end_timestamp = int(end_date.timestamp())
        
        all_data = []
        total_candles = 0
        requests_count = 0
        
        logger.info(f"🔄 Descargando desde Kraken API...")
        
        while since < end_timestamp:
            # Kraken API request
            params = {
                'pair': pair,
                'interval': interval_minutes,
                'since': since
            }
            
            try:
                response = requests.get(self.KRAKEN_API_URL, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if data.get('error') and len(data['error']) > 0:
                    logger.error(f"❌ Kraken API error: {data['error']}")
                    break
                
                # Extract OHLC data - Kraken returns pair key in result
                result = data.get('result', {})
                pair_data = None
                
                # Find the pair data (key might not be exactly what we sent)
                for key, value in result.items():
                    if key != 'last' and isinstance(value, list):
                        pair_data = value
                        break
                
                if not pair_data or len(pair_data) == 0:
                    logger.warning("⚠️ No hay más datos disponibles")
                    break
                
                all_data.extend(pair_data)
                total_candles += len(pair_data)
                
                # Update since to last timestamp
                last_timestamp = int(result.get('last', 0))
                
                # Break if no new data or reached end
                if last_timestamp <= since or last_timestamp >= end_timestamp:
                    break
                
                since = last_timestamp
                requests_count += 1
                
                # Progress log every 5 requests
                if requests_count % 5 == 0:
                    logger.info(f"   📈 Progreso: {total_candles} candles descargadas...")
                
                # Rate limiting: Kraken allows 1 req/sec for public API
                time.sleep(1.1)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Error en request: {e}")
                time.sleep(2)
                continue
            except Exception as e:
                logger.error(f"❌ Error inesperado: {e}")
                break
        
        # Convert to DataFrame
        if len(all_data) == 0:
            logger.warning("⚠️ No se descargaron datos")
            return pd.DataFrame()
        
        df = pd.DataFrame(all_data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'count'
        ])
        
        # Data cleaning and type conversion
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)
        
        # Filter by date range
        df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]
        
        # Sort by timestamp
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['timestamp'])
        
        logger.info(f"   ✅ {len(df)} candles procesadas y validadas")
        
        return df
    
    def _load_from_cache(
        self,
        pair: str,
        interval: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """Load data from cache if available and fresh"""
        
        cache_filename = f"{pair}_{interval}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.parquet"
        cache_path = self.cache_dir / cache_filename
        
        if not cache_path.exists():
            return None
        
        # Check if cache is fresh (max 24 hours old)
        cache_age = time.time() - cache_path.stat().st_mtime
        if cache_age > 86400:  # 24 hours
            logger.info("⚠️ Cache antiguo (>24h) - re-descargando datos frescos")
            return None
        
        try:
            df = pd.read_parquet(cache_path)
            logger.info(f"📦 Datos cargados desde cache: {cache_filename}")
            return df
        except Exception as e:
            logger.warning(f"⚠️ Error cargando cache: {e}")
            return None
    
    def _save_to_cache(self, df: pd.DataFrame, pair: str, interval: str) -> None:
        """Save DataFrame to cache"""
        
        if df is None or len(df) == 0:
            return
        
        start_date = df['timestamp'].min()
        end_date = df['timestamp'].max()
        
        cache_filename = f"{pair}_{interval}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.parquet"
        cache_path = self.cache_dir / cache_filename
        
        try:
            df.to_parquet(cache_path, compression='snappy')
            logger.info(f"💾 Datos guardados en cache: {cache_filename}")
        except Exception as e:
            logger.warning(f"⚠️ Error guardando cache: {e}")
    
    def get_multiple_pairs(
        self,
        pairs: List[str],
        interval: str = "1h",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Download data for multiple pairs
        
        Args:
            pairs: List of trading pairs
            interval: Timeframe
            start_date: Start datetime
            end_date: End datetime
            
        Returns:
            Dictionary {pair: DataFrame}
        """
        logger.info(f"📊 Descargando {len(pairs)} pares: {pairs}")
        
        results = {}
        for i, pair in enumerate(pairs, 1):
            logger.info(f"\n[{i}/{len(pairs)}] Procesando {pair}...")
            try:
                df = self.download_ohlcv(pair, interval, start_date, end_date)
                results[pair] = df
                time.sleep(1)  # Rate limiting between pairs
            except Exception as e:
                logger.error(f"❌ Error descargando {pair}: {e}")
                results[pair] = pd.DataFrame()
        
        return results
    
    def get_summary(self, df: pd.DataFrame) -> Dict:
        """Get data summary statistics"""
        if df is None or len(df) == 0:
            return {}
        
        return {
            'total_candles': len(df),
            'start_date': df['timestamp'].min().strftime('%Y-%m-%d %H:%M'),
            'end_date': df['timestamp'].max().strftime('%Y-%m-%d %H:%M'),
            'days_covered': (df['timestamp'].max() - df['timestamp'].min()).days,
            'price_min': df['low'].min(),
            'price_max': df['high'].max(),
            'avg_volume': df['volume'].mean(),
            'total_volume': df['volume'].sum()
        }


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    
    downloader = KrakenDataDownloader()
    
    start = datetime(2024, 5, 1)
    end = datetime(2024, 11, 21)
    
    df = downloader.download_ohlcv(
        pair="XBTUSD",
        interval="1h", 
        start_date=start,
        end_date=end
    )
    
    print("\n" + "=" * 70)
    print("📊 DATA SUMMARY:")
    print("=" * 70)
    summary = downloader.get_summary(df)
    for key, value in summary.items():
        print(f"  {key}: {value}")
    print("=" * 70)
