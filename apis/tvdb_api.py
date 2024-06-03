import tempfile
from urllib.parse import urljoin
from typing import Any, Optional
import requests_cache
from exceptions.exceptions import TVDBError
import requests

class AuthToken:
    def __init__(self, apikey, pin: Optional[str] = ""):
        self.apikey = apikey
        self.pin = pin
    
    def get_token(self):
        url = "https://api4.thetvdb.com/v4/login"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.apikey}",
            "Content-Type": "application/json"
        }
        data = {
            "apikey": self.apikey,
            "pin": self.pin
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()['data']['token']
        else:
            raise TVDBError(code=response.status_code, message="Failed to get token.")

class TempCachedSession(requests_cache.CachedSession):
    def __init__(self, cache_name=None, **kwargs):
        self.temp_dir = tempfile.TemporaryDirectory()
        cache_name = cache_name or f"{self.temp_dir.name}/http_cache"
        super().__init__(cache_name=cache_name, **kwargs)
 
    def __del__(self):
        self.temp_dir.cleanup()

class Request:
    def __init__(self, base_url: str, headers: dict, timeout: int = 10, cache_name: str = 'http_cache', cache_expire_after: int = 300) -> None:
        self.base_url = base_url
        self.headers = headers
        self.timeout = timeout
        self.session = TempCachedSession(cache_name, expire_after=cache_expire_after)
    
    def construct_url(self, endpoint: str, **kwargs: Any) -> str:
        url = urljoin(self.base_url, endpoint)
        sanitized_kwargs = {key: value for key, value in kwargs.items() if key.isalnum()}
        if sanitized_kwargs:
            url += '?'
            url += '&'.join(f"{key}={value}" for key, value in sanitized_kwargs.items())
        return url
    
    def get(self, endpoint: str, **kwargs: Any) -> dict:
        url = self.construct_url(endpoint, **kwargs)
        try:
            response = self.session.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise TVDBError(code=500, message="Network error occurred during GET request.") from e
    
    def post(self, endpoint: str, data: Optional[dict] = None, **kwargs: Any) -> dict:
        url = self.construct_url(endpoint, **kwargs)
        try:
            response = self.session.post(url, headers=self.headers, json=data, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise TVDBError(code=500, message="Network error occurred during POST request.") from e
    
    def clear_cache(self):
        self.session.cache.clear()

class TVDBAPI:
    def __init__(self, api_key: str, timeout: Optional[int]):
        self.timeout = timeout if timeout is not None else 10
        self.base_url = "https://api4.thetvdb.com/v4/"
        
        auth = AuthToken(apikey=api_key)
        self.token = auth.get_token()
        
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f"Bearer {self.token}"
        }
        
        self.request = Request(base_url=self.base_url, headers=self.headers, timeout=self.timeout)

    def search(self, query: str, **kwargs: Any) -> dict:
        return self.request.get("search", query=query, **kwargs)

    def get_thumbnail_from_search(self, query: str) -> dict:
        response = self.search(query)
        if response['data']:
            return response['data'][0]['thumbnail']
        else:
            return {'error': 'No results found.'}