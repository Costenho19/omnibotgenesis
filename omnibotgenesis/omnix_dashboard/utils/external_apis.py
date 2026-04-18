"""
OMNIX Dashboard - External API Utilities
ThreadPoolExecutor-based API calls with timeout and fallback
"""

import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

logger = logging.getLogger(__name__)

API_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="api_fetch")


def fetch_with_timeout(func, timeout=10, fallback=None):
    """Execute a function with timeout using ThreadPoolExecutor.
    
    Args:
        func: Callable to execute
        timeout: Timeout in seconds (default 10)
        fallback: Value to return on timeout/error
    
    Returns:
        Result of func() or fallback on timeout/error
    """
    try:
        future = API_EXECUTOR.submit(func)
        return future.result(timeout=timeout)
    except FuturesTimeoutError:
        logger.warning(f"Timeout after {timeout}s calling external API")
        return fallback
    except Exception as e:
        logger.error(f"Error in fetch_with_timeout: {e}")
        return fallback


def http_get_with_timeout(url, headers=None, timeout=10, fallback=None):
    """HTTP GET request with ThreadPoolExecutor timeout and fallback.
    
    Args:
        url: URL to fetch
        headers: Optional headers dict
        timeout: Timeout in seconds (default 10)
        fallback: Value to return on timeout/error (default None)
    
    Returns:
        Response JSON or fallback on error
    """
    import requests
    
    def do_request():
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    
    try:
        future = API_EXECUTOR.submit(do_request)
        return future.result(timeout=timeout + 2)
    except FuturesTimeoutError:
        logger.warning(f"Timeout after {timeout}s fetching {url}")
        return fallback
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return fallback


def shutdown_executor():
    """Shutdown the API executor gracefully"""
    API_EXECUTOR.shutdown(wait=False)
