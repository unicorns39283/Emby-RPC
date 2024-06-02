from typing import Optional
import requests as req

class EmbyAPI:
    def __init__(self, url, api_key):
        self.url = url
        self.api_key = api_key
        self.headers = {
            'X-Emby-Token': self.api_key
        }
        
    def get_users(self):
        url = f'{self.url}/emby/Users'
        return req.get(url, headers=self.headers).json()
        
    def get_user_id(self, username):
        url = f'{self.url}/emby/Users'
        response = req.get(url, headers=self.headers).json()
        for user in response:
            if user['Name'].lower() == username.lower():
                return user['Id']
        return {'error': 'User not found', 'username': username}
    
    def get_current_media(self, user_id: Optional[str] = None, username: Optional[str] = None):
        if user_id is None and username is None:
            return {'error': 'Please provide either user_id or username'}
        
        if user_id is None:
            user_id = self.get_user_id(username)
            if 'error' in user_id:
                return user_id
            
        url = f'{self.url}/emby/Sessions'
        response = req.get(url, headers=self.headers).json()
        
        for session in response:
            if session.get('UserId') == user_id:
                if 'NowPlayingItem' in session:
                    current_media = {
                        'NowPlayingItem': session['NowPlayingItem'],
                        'PlayState': session.get('PlayState', {}),
                        'debug_full_response': session,
                    }
                    return current_media
                else:
                    return {'message': 'No media currently playing'}
        return {'error': 'User not found'}
    
    def get_current_media_info(self, user_id: Optional[str] = None, username: Optional[str] = None):
        if user_id is None and username is None: return {'error': 'Please provide either user_id or username'}
        if user_id is None:
            user_id = self.get_user_id(username)
            if 'error' in user_id: return user_id
        current_media = self.get_current_media(user_id)
        if 'error' in current_media: return current_media
        if 'message' in current_media: return current_media
        now_playing_item, playstate = current_media.get('NowPlayingItem', {}), current_media.get('PlayState', {})
        position_ticks = playstate.get('PositionTicks', 0)
        position_seconds = position_ticks // 10000000
        hours, remainder = divmod(position_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        position_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        imdb_url, imdb_id, tvdb_id = '', '', ''
        external_urls = now_playing_item.get('ExternalUrls', [])
        for url_info in external_urls:
            if url_info.get('Name') == 'IMDb':
                imdb_url = url_info.get('Url', '')
                imdb_id = imdb_url.split('/')[-1]
            elif url_info.get('Name') == 'TheTVDB':
                tvdb_id = url_info.get('Url', '').split('=')[-1]
        media_info = {
            'name': now_playing_item.get('Name', ''),
            'id': now_playing_item.get('Id', ''),
            'path': now_playing_item.get('Path', ''),
            'overview': now_playing_item.get('Overview', ''),
            'production_year': now_playing_item.get('ProductionYear', ''),
            'series_name': now_playing_item.get('SeriesName', ''),
            'season_name': now_playing_item.get('SeasonName', ''),
            'media_type': now_playing_item.get('MediaType', ''),
            'width': now_playing_item.get('Width', 0),
            'height': now_playing_item.get('Height', 0),
            'runtimeticks': now_playing_item.get('RunTimeTicks', 0),
            'ispaused': playstate.get('IsPaused', False),
            'position_ticks': position_ticks,
            'position_seconds': position_seconds,
            'position_time': position_time,
            'imdb_url': imdb_url,
            'imdb_id': imdb_id,
            'tvdb_id': tvdb_id,
        }
        return media_info
