"""
OMNIX V6.0 ULTRA - Exchange Latency Monitor
============================================
Real-time latency monitoring for multi-exchange trading.

Measures and tracks API response times in milliseconds
for institutional-grade execution analysis.

Author: OMNIX Team
Version: 1.0.0
"""

import time
import asyncio
import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
import logging
import aiohttp
import requests

logger = logging.getLogger(__name__)


class LatencyGrade(Enum):
    """Latency quality grades"""
    EXCELLENT = ("excellent", 50, "⚡")
    GOOD = ("good", 100, "✅")
    ACCEPTABLE = ("acceptable", 200, "🔶")
    SLOW = ("slow", 500, "⚠️")
    CRITICAL = ("critical", float('inf'), "🔴")
    
    def __init__(self, grade_name: str, max_ms: float, icon: str):
        self.grade_name = grade_name
        self.max_ms = max_ms
        self.icon = icon


@dataclass
class LatencyMeasurement:
    """Single latency measurement"""
    exchange: str
    endpoint: str
    latency_ms: float
    timestamp: datetime
    success: bool
    error: Optional[str] = None
    
    @property
    def grade(self) -> LatencyGrade:
        """Get latency grade based on response time"""
        for grade in LatencyGrade:
            if self.latency_ms <= grade.max_ms:
                return grade
        return LatencyGrade.CRITICAL


@dataclass
class ExchangeLatencyStats:
    """Aggregated latency statistics for an exchange"""
    exchange: str
    measurements: int
    avg_ms: float
    min_ms: float
    max_ms: float
    median_ms: float
    p95_ms: float
    p99_ms: float
    std_dev_ms: float
    success_rate: float
    last_updated: datetime
    
    @property
    def grade(self) -> LatencyGrade:
        """Overall grade based on average latency"""
        for grade in LatencyGrade:
            if self.avg_ms <= grade.max_ms:
                return grade
        return LatencyGrade.CRITICAL
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for reporting"""
        return {
            'exchange': self.exchange,
            'measurements': self.measurements,
            'latency': {
                'avg_ms': round(self.avg_ms, 2),
                'min_ms': round(self.min_ms, 2),
                'max_ms': round(self.max_ms, 2),
                'median_ms': round(self.median_ms, 2),
                'p95_ms': round(self.p95_ms, 2),
                'p99_ms': round(self.p99_ms, 2),
                'std_dev_ms': round(self.std_dev_ms, 2)
            },
            'success_rate': f"{self.success_rate:.1f}%",
            'grade': f"{self.grade.icon} {self.grade.grade_name.upper()}",
            'last_updated': self.last_updated.isoformat()
        }


class ExchangeConfig:
    """Exchange API endpoints for latency testing"""
    
    ENDPOINTS = {
        'kraken': {
            'name': 'Kraken',
            'rest_url': 'https://api.kraken.com/0/public/Time',
            'ws_url': 'wss://ws.kraken.com',
            'type': 'primary'
        },
        'binance': {
            'name': 'Binance',
            'rest_url': 'https://api.binance.com/api/v3/time',
            'ws_url': 'wss://stream.binance.com:9443/ws',
            'type': 'secondary'
        },
        'coinbase': {
            'name': 'Coinbase',
            'rest_url': 'https://api.exchange.coinbase.com/time',
            'ws_url': 'wss://ws-feed.exchange.coinbase.com',
            'type': 'secondary'
        },
        'bybit': {
            'name': 'Bybit',
            'rest_url': 'https://api.bybit.com/v5/market/time',
            'ws_url': 'wss://stream.bybit.com/v5/public/spot',
            'type': 'secondary'
        },
        'okx': {
            'name': 'OKX',
            'rest_url': 'https://www.okx.com/api/v5/public/time',
            'ws_url': 'wss://ws.okx.com:8443/ws/v5/public',
            'type': 'secondary'
        }
    }


class LatencyMonitor:
    """
    Real-time Exchange Latency Monitor
    
    Features:
    - REST API latency measurement
    - WebSocket connection latency
    - Statistical analysis (avg, median, p95, p99)
    - Quality grading (Excellent/Good/Acceptable/Slow/Critical)
    - Historical tracking with rolling window
    """
    
    def __init__(self, history_size: int = 1000):
        """
        Initialize latency monitor
        
        Args:
            history_size: Number of measurements to keep per exchange
        """
        self.history_size = history_size
        self.measurements: Dict[str, deque] = {}
        self.last_check: Dict[str, datetime] = {}
        
        for exchange in ExchangeConfig.ENDPOINTS:
            self.measurements[exchange] = deque(maxlen=history_size)
        
        logger.info(f"⚡ Latency Monitor initialized for {len(ExchangeConfig.ENDPOINTS)} exchanges")
    
    def measure_rest_latency(self, exchange: str) -> LatencyMeasurement:
        """
        Measure REST API latency for an exchange
        
        Args:
            exchange: Exchange identifier (e.g., 'kraken')
        
        Returns:
            LatencyMeasurement with timing data
        """
        config = ExchangeConfig.ENDPOINTS.get(exchange)
        if not config:
            return LatencyMeasurement(
                exchange=exchange,
                endpoint="unknown",
                latency_ms=9999.0,
                timestamp=datetime.now(),
                success=False,
                error=f"Unknown exchange: {exchange}"
            )
        
        url = config['rest_url']
        start_time = time.perf_counter()
        
        try:
            response = requests.get(url, timeout=5)
            end_time = time.perf_counter()
            
            latency_ms = (end_time - start_time) * 1000
            
            measurement = LatencyMeasurement(
                exchange=exchange,
                endpoint=url,
                latency_ms=latency_ms,
                timestamp=datetime.now(),
                success=response.status_code == 200,
                error=None if response.status_code == 200 else f"HTTP {response.status_code}"
            )
            
        except requests.exceptions.Timeout:
            measurement = LatencyMeasurement(
                exchange=exchange,
                endpoint=url,
                latency_ms=5000,
                timestamp=datetime.now(),
                success=False,
                error="Timeout (>5s)"
            )
        except Exception as e:
            measurement = LatencyMeasurement(
                exchange=exchange,
                endpoint=url,
                latency_ms=9999.0,
                timestamp=datetime.now(),
                success=False,
                error=str(e)
            )
        
        self.measurements[exchange].append(measurement)
        self.last_check[exchange] = datetime.now()
        
        return measurement
    
    async def measure_rest_latency_async(self, exchange: str) -> LatencyMeasurement:
        """Async version of REST latency measurement"""
        config = ExchangeConfig.ENDPOINTS.get(exchange)
        if not config:
            return LatencyMeasurement(
                exchange=exchange,
                endpoint="unknown",
                latency_ms=9999.0,
                timestamp=datetime.now(),
                success=False,
                error=f"Unknown exchange: {exchange}"
            )
        
        url = config['rest_url']
        start_time = time.perf_counter()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    end_time = time.perf_counter()
                    latency_ms = (end_time - start_time) * 1000
                    
                    measurement = LatencyMeasurement(
                        exchange=exchange,
                        endpoint=url,
                        latency_ms=latency_ms,
                        timestamp=datetime.now(),
                        success=response.status == 200,
                        error=None if response.status == 200 else f"HTTP {response.status}"
                    )
        except asyncio.TimeoutError:
            measurement = LatencyMeasurement(
                exchange=exchange,
                endpoint=url,
                latency_ms=5000,
                timestamp=datetime.now(),
                success=False,
                error="Timeout (>5s)"
            )
        except Exception as e:
            measurement = LatencyMeasurement(
                exchange=exchange,
                endpoint=url,
                latency_ms=9999.0,
                timestamp=datetime.now(),
                success=False,
                error=str(e)
            )
        
        self.measurements[exchange].append(measurement)
        self.last_check[exchange] = datetime.now()
        
        return measurement
    
    async def measure_all_exchanges(self) -> Dict[str, LatencyMeasurement]:
        """Measure latency for all configured exchanges concurrently"""
        tasks = [
            self.measure_rest_latency_async(exchange)
            for exchange in ExchangeConfig.ENDPOINTS
        ]
        
        results = await asyncio.gather(*tasks)
        
        return {
            m.exchange: m for m in results
        }
    
    def get_exchange_stats(self, exchange: str) -> Optional[ExchangeLatencyStats]:
        """
        Get statistical summary for an exchange
        
        Args:
            exchange: Exchange identifier
        
        Returns:
            ExchangeLatencyStats or None if no data
        """
        measurements = list(self.measurements.get(exchange, []))
        
        if not measurements:
            return None
        
        latencies = [m.latency_ms for m in measurements if m.success and m.latency_ms > 0]
        
        if not latencies:
            return ExchangeLatencyStats(
                exchange=exchange,
                measurements=len(measurements),
                avg_ms=9999.0,
                min_ms=9999.0,
                max_ms=9999.0,
                median_ms=9999.0,
                p95_ms=9999.0,
                p99_ms=9999.0,
                std_dev_ms=0.0,
                success_rate=0.0,
                last_updated=measurements[-1].timestamp
            )
        
        sorted_latencies = sorted(latencies)
        n = len(sorted_latencies)
        
        p95_idx = int(n * 0.95)
        p99_idx = int(n * 0.99)
        
        success_count = sum(1 for m in measurements if m.success)
        success_rate = (success_count / len(measurements)) * 100
        
        return ExchangeLatencyStats(
            exchange=exchange,
            measurements=len(measurements),
            avg_ms=statistics.mean(latencies),
            min_ms=min(latencies),
            max_ms=max(latencies),
            median_ms=statistics.median(latencies),
            p95_ms=sorted_latencies[min(p95_idx, n-1)],
            p99_ms=sorted_latencies[min(p99_idx, n-1)],
            std_dev_ms=statistics.stdev(latencies) if len(latencies) > 1 else 0,
            success_rate=success_rate,
            last_updated=measurements[-1].timestamp
        )
    
    def get_all_stats(self) -> Dict[str, ExchangeLatencyStats]:
        """Get statistics for all exchanges"""
        stats = {}
        for exchange in ExchangeConfig.ENDPOINTS:
            exchange_stats = self.get_exchange_stats(exchange)
            if exchange_stats:
                stats[exchange] = exchange_stats
        return stats
    
    def get_fastest_exchange(self) -> Optional[Tuple[str, float]]:
        """Get the exchange with lowest average latency"""
        stats = self.get_all_stats()
        if not stats:
            return None
        
        fastest = min(stats.items(), key=lambda x: x[1].avg_ms if x[1].avg_ms > 0 else float('inf'))
        return (fastest[0], fastest[1].avg_ms)
    
    def get_latency_comparison(self) -> List[Dict]:
        """
        Get comparative latency data for all exchanges
        
        Returns:
            List of dicts sorted by average latency
        """
        stats = self.get_all_stats()
        
        comparison = []
        for exchange, stat in stats.items():
            config = ExchangeConfig.ENDPOINTS[exchange]
            comparison.append({
                'exchange': config['name'],
                'type': config['type'],
                'avg_ms': round(stat.avg_ms, 2),
                'median_ms': round(stat.median_ms, 2),
                'p95_ms': round(stat.p95_ms, 2),
                'grade': f"{stat.grade.icon} {stat.grade.grade_name.upper()}",
                'success_rate': f"{stat.success_rate:.1f}%",
                'samples': stat.measurements
            })
        
        comparison.sort(key=lambda x: x['avg_ms'] if x['avg_ms'] > 0 else float('inf'))
        
        return comparison
    
    def get_investor_report(self) -> Dict:
        """
        Generate investor-friendly latency report
        
        Returns:
            Dict with formatted latency data
        """
        comparison = self.get_latency_comparison()
        fastest = self.get_fastest_exchange()
        
        return {
            'summary': {
                'exchanges_monitored': len(ExchangeConfig.ENDPOINTS),
                'fastest_exchange': fastest[0] if fastest else 'N/A',
                'fastest_latency_ms': f"{fastest[1]:.1f}ms" if fastest else 'N/A'
            },
            'latency_by_exchange': comparison,
            'thresholds': {
                'excellent': '<50ms',
                'good': '50-100ms',
                'acceptable': '100-200ms',
                'slow': '200-500ms',
                'critical': '>500ms'
            },
            'timestamp': datetime.now().isoformat()
        }


def demo_latency_monitor():
    """Demonstrate Latency Monitor capabilities"""
    print("=" * 60)
    print("⚡ EXCHANGE LATENCY MONITOR - INSTITUTIONAL DEMO")
    print("=" * 60)
    
    monitor = LatencyMonitor()
    
    print("\n📡 Measuring latency for all exchanges...")
    print("-" * 40)
    
    for exchange in ['kraken', 'binance', 'coinbase', 'bybit', 'okx']:
        measurement = monitor.measure_rest_latency(exchange)
        status = "✅" if measurement.success else "❌"
        config = ExchangeConfig.ENDPOINTS[exchange]
        print(f"   {config['name']:12} | {measurement.latency_ms:7.1f}ms | {measurement.grade.icon} {measurement.grade.grade_name:10} {status}")
    
    print("\n📊 Latency Comparison:")
    print("-" * 40)
    comparison = monitor.get_latency_comparison()
    print(f"   {'Exchange':<12} | {'Avg':>8} | {'Median':>8} | {'P95':>8} | Grade")
    print("   " + "-" * 55)
    for item in comparison:
        print(f"   {item['exchange']:<12} | {item['avg_ms']:>6.1f}ms | {item['median_ms']:>6.1f}ms | {item['p95_ms']:>6.1f}ms | {item['grade']}")
    
    fastest = monitor.get_fastest_exchange()
    if fastest:
        print(f"\n🏆 Fastest Exchange: {fastest[0]} ({fastest[1]:.1f}ms)")
    
    print("\n✅ Latency Monitor ready for institutional use")
    return monitor


if __name__ == "__main__":
    demo_latency_monitor()
