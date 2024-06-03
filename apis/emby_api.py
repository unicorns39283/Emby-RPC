from typing import Any, Optional
from urllib.parse import urljoin
import requests as req

from exceptions.exceptions import EmbyError

class Request:
    def __init__(self, base_url: str, headers: dict, timeout: int = 10) -> None:
        self.base_url = base_url
        self.headers = headers
        self.timeout = timeout
        self.session = req.Session()
    
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
        except req.exceptions.RequestException as e:
            raise EmbyError(code=500, message="Network error occurred during GET request.") from e
    
    def post(self, endpoint: str, data: Optional[dict] = None, **kwargs: Any) -> dict:
        url = self.construct_url(endpoint, **kwargs)
        try:
            response = self.session.post(url, headers=self.headers, json=data, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except req.exceptions.RequestException as e:
            raise EmbyError(code=500, message="Network error occurred during POST request.") from e
    
    def clear_cache(self):
        self.session.cache.clear()


class EmbyAPI:
    def __init__(self, url, api_key):
        self.url = url
        self.api_key = api_key
        self.headers = {
            'X-Emby-Token': self.api_key
        }
        self.request = Request(self.url, self.headers)
        
    def get_users(self):
        url = f'/emby/Users'
        return self.request.get(url)
        
    def get_user_id(self, username):
        url = f'{self.url}/emby/Users'
        response = self.request.get(url, headers=self.headers)
        for user in response:
            if user['Name'].lower() == username.lower():
                return user['Id']
        return {'error': 'User not found', 'username': username}
    
    def get_current_media(self, user_id: Optional[str] = None, username: Optional[str] = None):
        assert user_id is not None or username is not None, 'Please provide either user_id or username'
        user_id = user_id or self.get_user_id(username)
        sessions = self.request.get('/emby/Sessions')
        for session in sessions:
            if session.get('UserId') == user_id:
                if 'NowPlayingItem' in session:
                    return {
                        'NowPlayingItem': session['NowPlayingItem'],
                        'PlayState': session.get('PlayState', {}),
                        'debug_full_session': session
                    }
                return {'message': 'No media is currently playing.'}
        raise EmbyError(404, f"User with ID '{user_id}' not found")
    
    def get_current_media_info(self, user_id: Optional[str] = None, username: Optional[str] = None):
        media = self.get_current_media(user_id=user_id, username=username)
        if 'message' in media: return media
        item = media['NowPlayingItem']
        state = media['PlayState']
        ticks = state.get("PositionTicks", 0)
        seconds = ticks // 10_000_000
        position = f"{seconds//3600:02d}:{seconds%3600//60:02d}:{seconds%60:02d}"
        imdb_url = next((url['Url'] for url in item.get('ExternalUrls', []) if url['Name'] == 'IMDb'), '')
        tvdb_id = next((url['Url'].split('=')[-1] for url in item.get('ExternalUrls', []) if url['Name'] == 'TheTVDB'), '')
        return {
            'name': item.get('Name', ''),
            'id': item.get('Id', ''),
            'path': item.get('Path', ''),
            'overview': item.get('Overview', ''),
            'production_year': item.get('ProductionYear', ''),
            'series_name': item.get('SeriesName', ''),
            'season_name': item.get('SeasonName', ''),
            'media_type': item.get('MediaType', ''),
            'width': item.get('Width', 0),
            'height': item.get('Height', 0),
            'runtimeticks': item.get('RunTimeTicks', 0),
            'ispaused': state.get('IsPaused', False),
            'position_ticks': ticks,
            'position_seconds': seconds,
            'position_time': position,
            'imdb_url': imdb_url,
            'imdb_id': imdb_url.split('/')[-1],
            'tvdb_id': tvdb_id,
        }