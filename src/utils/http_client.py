# src/utils/http_client.py
"""
Robust HTTP client with retry logic and rate limiting.
"""

import time
import requests
from typing import Optional, Dict, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

logger = logging.getLogger(__name__)


class HttpClient:
    """
    HTTP client with:
    - Automatic retries
    - Rate limiting
    - Session reuse
    - Timeout handling
    """
    
    def __init__(
        self,
        rate_limit: float = 1.0,
        max_retries: int = 3,
        timeout: int = 30
    ):
        self.rate_limit = rate_limit
        self.max_retries = max_retries
        self.timeout = timeout
        self.last_request_time = 0
        
        # Create session with retry strategy
        self.session = requests.Session()
        
        # Retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Default headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/html',
            'Accept-Language': 'de,en-US;q=0.9,en;q=0.8'
        })
    
    def _wait_for_rate_limit(self):
        """Enforce rate limiting"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self.last_request_time = time.time()
    
    def get(self, url: str, params: Optional[Dict] = None, **kwargs) -> requests.Response:
        """GET request with rate limiting"""
        self._wait_for_rate_limit()
        
        try:
            response = self.session.get(
                url,
                params=params,
                timeout=kwargs.get('timeout', self.timeout),
                **kwargs
            )
            
            # Log slow requests
            if response.elapsed.total_seconds() > 5:
                logger.warning(f"Slow request: {response.elapsed.total_seconds():.2f}s - {url}")
            
            return response
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout: {url}")
            raise
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error: {url}")
            raise
        except Exception as e:
            logger.error(f"Request error: {url} - {e}")
            raise
    
    def post(self, url: str, data: Optional[Dict] = None, **kwargs) -> requests.Response:
        """POST request with rate limiting"""
        self._wait_for_rate_limit()
        return self.session.post(url, data=data, timeout=kwargs.get('timeout', self.timeout), **kwargs)