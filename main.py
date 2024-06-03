import json
import time
import threading
from apis.tvdb_api import TVDBAPI
from apis.emby_api import EmbyAPI
from pypresence import Presence

def update_rpc_presence(media_info, rpc, tvdb):
    print("Updating Discord RPC presence...")
    if media_info.get('tvdb_id'):
        url = tvdb.get_thumbnail_from_search(media_info.get('series_name'))
        image_url = url
    else:
        print("No TVDB ID found.")
    large_text = media_info.get('overview', '')
    if len(large_text) > 128:
        large_text = large_text[:125] + '...'
    runtime_seconds = media_info.get('runtimeticks', 0) // 10000000
    position_seconds = media_info.get('position_seconds', 0)
    remaining_seconds = runtime_seconds - position_seconds
    activity = {
        'details': f"{media_info.get('series_name', '')} - {media_info.get('season_name', '')}",
        'state': media_info.get('name', ''),
        'large_text': large_text,
        'large_image': image_url,
    }
    if media_info.get('is_paused'):
        activity['small_image'] = 'pause'
        activity['small_text'] = 'Paused'
    else:
        activity['start'] = time.time() - position_seconds
        activity['end'] = time.time() + remaining_seconds
    rpc.update(**activity)
    print("Discord RPC presence updated successfully.")

def main():
    print("Starting Discord RPC program...")
    data = open('config.json', 'r').read()
    config = json.loads(data)   
    emby_api = EmbyAPI(config['EMBY_URL'], config['EMBY_API_KEY'])
    tvdb_api = TVDBAPI(api_key=config['TVDB_API_KEY'], timeout=10)
    
    rpc = Presence(config['CLIENT_ID'])
    rpc.connect()
    print("Connected to Discord RPC.")
    
    while True:
        print("Retrieving current media information from Emby...")
        media_info = emby_api.get_current_media_info(username=config['EMBY_USERNAME'])
        if 'error' not in media_info and 'message' not in media_info:
            print("Media information retrieved successfully.")
            update_rpc_presence(media_info, rpc, tvdb_api)
        else:
            print("No media is currently playing. Clearing Discord RPC presence.")
            rpc.clear()

        print("Waiting for 5 seconds before the next update...")
        time.sleep(1)

    rpc.close()
    print("Disconnected from Discord RPC.")


if __name__ == '__main__':
    main()