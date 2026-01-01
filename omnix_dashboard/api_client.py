"""
OMNIX INSTITUTIONAL+ PREMIUM - API Client
API Client for Streamlit Dashboard

Cliente para consumir métricas desde el API Flask principal.
Usado por el dashboard Streamlit para mantener separación de servicios.
"""

import os
import logging
import requests
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

API_BASE_URL = os.environ.get('OMNIX_API_URL', 'http://localhost:5000')
API_KEY = os.environ.get('DASHBOARD_API_KEY', '')


class OmnixAPIClient:
    """
    Cliente API para el Dashboard Streamlit.
    Consume métricas desde el servicio Flask principal.
    """
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = base_url or API_BASE_URL
        self.api_key = api_key or API_KEY
        self.timeout = 30
        self.headers: Dict[str, str] = {}
        if self.api_key:
            self.headers['X-API-Key'] = self.api_key
        logger.info(f"📡 OmnixAPIClient inicializado - Base URL: {self.base_url}")
    
    def _request(self, endpoint: str, method: str = 'GET', params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            logger.error(f"Timeout calling {url}")
            return {'success': False, 'error': 'Request timeout'}
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error calling {url}")
            return {'success': False, 'error': 'Connection failed - API not running'}
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error calling {url}: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error calling {url}: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_health(self) -> Dict[str, Any]:
        return self._request('/api/health')
    
    def get_metrics(self) -> Dict[str, Any]:
        return self._request('/api/metrics')
    
    def get_institutional_metrics(self) -> Dict[str, Any]:
        return self._request('/api/metrics/institutional')
    
    def get_trades_history(self) -> Dict[str, Any]:
        return self._request('/api/trades/history')
    
    def get_equity_curve(self) -> Dict[str, Any]:
        return self._request('/api/equity-curve')
    
    def get_adaptive_engine(self) -> Dict[str, Any]:
        return self._request('/api/system/adaptive')
    
    def get_fear_greed(self) -> Dict[str, Any]:
        return self._request('/api/market/fear-greed')
    
    def get_calibration(self) -> Dict[str, Any]:
        return self._request('/api/system/calibration')
    
    def get_quarantine(self) -> Dict[str, Any]:
        return self._request('/api/system/quarantine')
    
    def get_segmented_expectancy(self) -> Dict[str, Any]:
        """Operación Lucidez: Get expectancy segmented by HMM regime + coherence bucket"""
        return self._request('/api/metrics/expectancy')
    
    def download_pdf_report(self) -> Optional[bytes]:
        url = f"{self.base_url}/api/report/pdf"
        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=60
            )
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"Error downloading PDF: {e}")
            return None


_client_instance: Optional[OmnixAPIClient] = None


def get_api_client() -> OmnixAPIClient:
    global _client_instance
    if _client_instance is None:
        _client_instance = OmnixAPIClient()
    return _client_instance
