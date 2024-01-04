import src.logging
from src.globals import DISCORD_THUMBNAIL, PLEX_ICON_URL

logger = src.logging.logging.getLogger("plex")

def plex_play(data):
    try:
        if data and 'source_metadata_details' in data and 'stream_details' in data and 'server_info' in data:
            source_metadata = data['source_metadata_details']
            stream_details = data['stream_details']
            server_info = data['server_info']
            
            media_type = source_metadata.get('media_type', '').capitalize()
            title = source_metadata.get('title', '')
            
            if media_type == 'Movie':
                title = f"{title} ({source_metadata.get('year')})"
            elif media_type == 'Episode':
                title = f"{title} (S{source_metadata.get('season_num00')}E{source_metadata.get('episode_num00')})"
            
            embed = {
                'color': 32768,
                'author': {'name': f"Plex - Streaming {media_type}", 'icon_url': PLEX_ICON_URL},
                'thumbnail': {'url': source_metadata.get('poster_url', '')},
                'title': title,
                'timestamp': server_info.get('utctime'),
                'url': source_metadata.get('imdb_url', ''),
                'footer': {
                    'text': f"{server_info.get('server_name')} | {stream_details.get('username')} | {stream_details.get('product')} | {stream_details.get('video_decision', '').title()}"
                },
                'image': {'url': DISCORD_THUMBNAIL},
                'fields': [
                    {
                        'name': ':arrow_forward: Now Streaming',
                        'value': f"{stream_details.get('remaining_time', '')[3:]} remaining" if stream_details.get('remaining_time', '').startswith("00:") else f"{stream_details.get('remaining_time', '')} remaining",
                        'inline': True
                    }
                ]
            }
            logger.info(f"Created Play Start embed for {media_type} event")
            return {'embeds': [embed]}, 200
        else:
            logger.info("Webhook received, but no Source Metadata Details or Stream Details found. Data not saved.")
            return {'message': "Webhook received, but no Source Metadata Details or Stream Details found. Data not saved."}, 200
    except Exception as e:
        logger.error(f"Error while processing JSON payload: {str(e)}")
        return {'error': "Internal server error"}, 500
    
def plex_resume(data):
    try:
        if data and 'source_metadata_details' in data and 'stream_details' in data and 'server_info' in data:
            source_metadata = data['source_metadata_details']
            stream_details = data['stream_details']
            server_info = data['server_info']
            
            media_type = source_metadata.get('media_type', '').capitalize()
            title = source_metadata.get('title', '')
            if media_type == 'Movie':
                title = f"{title} ({source_metadata.get('year')})"
            elif media_type == 'Episode':
                title = f"{title} (S{source_metadata.get('season_num00')}E{source_metadata.get('episode_num00')})"
            
            embed = {
                'color': 17613,
                'author': {'name': f"Plex - Streaming {media_type}", 'icon_url': PLEX_ICON_URL},
                'thumbnail': {'url': source_metadata.get('poster_url', '')},
                'title': title,
                'timestamp': server_info.get('utctime'),
                'url': source_metadata.get('imdb_url', ''),
                'footer': {
                    'text': f"{server_info.get('server_name')} | {stream_details.get('username')} | {stream_details.get('product')} | {stream_details.get('video_decision', '').title()}"
                },
                'image': {'url': DISCORD_THUMBNAIL},
                'fields': [
                    {
                        'name': ':play_pause: Resumed Streaming',
                        'value': f"{stream_details.get('remaining_time', '')[3:]} remaining" if stream_details.get('remaining_time', '').startswith("00:") else f"{stream_details.get('remaining_time', '')} remaining",
                        'inline': True
                    }
                ]
            }
            logger.info(f"Created Play Resumed embed for {media_type} event")
            return {'embeds': [embed]}, 200
        else:
            logger.info("Webhook received, but no Source Metadata Details or Stream Details found. Data not saved.")
            return {'message': "Webhook received, but no Source Metadata Details or Stream Details found. Data not saved."}, 200
    except Exception as e:
        logger.error(f"Error while processing JSON payload: {str(e)}")
        return {'error': "Internal server error"}, 500

def plex_episode_content(data):
    try:
        if data and 'source_metadata_details' in data and 'server_info' in data:
            source_metadata = data['source_metadata_details']
            server_info = data['server_info']

            if source_metadata.get('media_type') == 'episode':
                embed = {
                    'title': f"{source_metadata.get('title')} (S{source_metadata.get('season_num00')}E{source_metadata.get('episode_num00')})",
                    'description': source_metadata.get('summary', ''),
                    'url': source_metadata.get('plex_url', ''),
                    'color': 16776960,
                    'fields': [
                        {'name': 'Quality', 'value': source_metadata.get('video_full_resolution', ''), 'inline': True},
                        {'name': 'Season/Episode', 'value': f"S{source_metadata.get('season_num00')} - E{source_metadata.get('episode_num00')}", 'inline': True},
                        {'name': 'Air date', 'value': source_metadata.get('air_date', ''), 'inline': True},
                        {'name': 'Genres', 'value': source_metadata.get('genres', ''), 'inline': True},
                        {'name': 'Details', 'value': f"📺 [TVDB]({source_metadata.get('thetvdb_url', '')})", 'inline': True},
                        {'name': 'Runtime', 'value': source_metadata.get('duration_time', '')[3:] if source_metadata.get('duration_time', '').startswith("00:") else source_metadata.get('duration_time', ''), 'inline': True}
                    ],
                    'author': {'name': 'Plex - New Episode', 'icon_url': PLEX_ICON_URL},
                    'footer': {'text': server_info.get('server_name', '')},
                    'timestamp': server_info.get('utctime', ''),
                    'thumbnail': {'url': source_metadata.get('poster_url', '')},
                    'image': {'url': DISCORD_THUMBNAIL}
                }
                return {'embeds': [embed]}, 200
            else:
                logger.info("Webhook received, but no episode details found. Data not saved.")
                return {'message': "Webhook received, but no episode details found. Data not saved."}, 200
        else:
            logger.info("Webhook received, but no Source Metadata Details found. Data not saved.")
            return {'message': "Webhook received, but no Source Metadata Details found. Data not saved."}, 200
    except Exception as e:
        logger.error(f"Error while processing JSON payload: {str(e)}")
        return {'error': "Internal server error"}, 500
    
def plex_season_content(data):
    try:
        if data and 'source_metadata_details' in data and 'server_info' in data:
            source_metadata = data['source_metadata_details']
            server_info = data['server_info']

            if source_metadata.get('media_type') == 'season':
                embed = {
                    'title': source_metadata.get('title'),
                    'description': source_metadata.get('summary', ''),
                    'url': source_metadata.get('plex_url', ''),
                    'color': 16711680,
                    'fields': [
                        {'name': 'Season', 'value': source_metadata.get('season_num00'), 'inline': True},
                        {'name': 'Episodes', 'value': source_metadata.get('episode_count'), 'inline': True},
                        {'name': 'Details', 'value': f"[IMDb]({source_metadata.get('imdb_url')})", 'inline': True}
                    ],
                    'author': {'name': 'Plex - New Season', 'icon_url': PLEX_ICON_URL},
                    'footer': {'text': server_info.get('server_name', '')},
                    'timestamp': server_info.get('utctime', ''),
                    'thumbnail': {'url': source_metadata.get('poster_url', '')},
                    'image': {'url': DISCORD_THUMBNAIL}
                }
                return {'embeds': [embed]}, 200
            else:
                logger.info("Webhook received, but no Season details found. Data not saved.")
                return {'message': "Webhook received, but no Season details found. Data not saved."}, 200
        else:
            logger.info("Webhook received, but no Source Metadata Details found. Data not saved.")
            return {'message': "Webhook received, but no Source Metadata Details found. Data not saved."}, 200
    except Exception as e:
        logger.error(f"Error while processing JSON payload: {str(e)}")
        return {'error': "Internal server error"}, 500
    
def plex_movie_content(data):
    try:
        if data and 'source_metadata_details' in data and 'server_info' in data:
            source_metadata = data['source_metadata_details']
            server_info = data['server_info']

            if source_metadata.get('media_type') == 'movie':
                embed = {
                    'title': f"{source_metadata.get('title')} ({source_metadata.get('year')})",
                    'description': source_metadata.get('summary', ''),
                    'url': source_metadata.get('plex_url', ''),
                    'color': 15402759,
                    'fields': [
                        {'name': 'Quality', 'value': source_metadata.get('video_full_resolution', ''), 'inline': True},
                        {'name': 'Genres', 'value': source_metadata.get('genres', ''), 'inline': True},
                        {'name': 'Release date', 'value': source_metadata.get('release_date', ''), 'inline': True},
                        {'name': 'Rotten Tomatoes', 'value': f":popcorn: {source_metadata.get('rating')}", 'inline': True},
                        {'name': 'Details', 'value': f"[IMDb]({source_metadata.get('imdb_url')})", 'inline': True},
                        {'name': 'Runtime', 'value': source_metadata.get('duration_time', '')[3:] if source_metadata.get('duration_time', '').startswith("00:") else source_metadata.get('duration_time', ''), 'inline': True}
                    ],
                    'author': {'name': 'Plex - New Movie', 'icon_url': f'{PLEX_ICON_URL}'},
                    'footer': {'text': server_info.get('server_name', '')},
                    'timestamp': server_info.get('utctime', ''),
                    'thumbnail': {'url': source_metadata.get('poster_url', '')},
                    'image': {'url': f'{DISCORD_THUMBNAIL}'}
                }
                return {'embeds': [embed]}, 200
            else:
                logger.info("Webhook received, but no Movie details found. Data not saved.")
                return {'message': "Webhook received, but no Movie details found. Data not saved."}, 200
        else:
            logger.info("Webhook received, but no Source Metadata Details found. Data not saved.")
            return {'message': "Webhook received, but no Source Metadata Details found. Data not saved."}, 200
    except Exception as e:
        logger.error(f"Error while processing JSON payload: {str(e)}")
        return {'error': "Internal server error"}, 500