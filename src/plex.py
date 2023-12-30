import src.logging

logger = src.logging.logging.getLogger("plex")

def plex_play(data):
    try:
        embeds_list = []
        if data and 'source_metadata_details' in data and 'stream_details' in data and 'server_info' in data:
            source_metadata = data['source_metadata_details']
            stream_details = data['stream_details']
            server_info = data['server_info']
            
            author_name = f"Plex - Streaming {source_metadata.get('media_type', '')}"
            
            if source_metadata.get('media_type') == 'movie':
                title = f"{source_metadata.get('title')} ({source_metadata.get('year')})"
            elif source_metadata.get('media_type') == 'episode':
                title = f"{source_metadata.get('title')} (S{source_metadata.get('season_num00')}E{source_metadata.get('episode_num00')})"
            else:
                title = source_metadata.get('title', '')
            
            embed = {
                'color': 16556313,
                'author': {
                    'name': author_name,
                    'icon_url': 'https://i.imgur.com/ZuFghbX.png'
                },
                'thumbnail': {
                    'url': source_metadata.get('poster_url', '')
                },
                'title': title,
                'timestamp': source_metadata.get('utctime'),
                'url': source_metadata.get('imdb_url', ''),
                'footer': {
                    'text': f"{server_info.get('server_name')} | {stream_details.get('username')} | {server_info.get('product')} | {stream_details.get('video_decision', '')}"
                },
                'image': {
                    'url': 'https://imgur.com/a/D3MxSNM'
                },
                'fields': [
                    {
                        'name': ':arrow_forward: Now Streaming',
                        'value': f"{stream_details.get('remaining_time', '')[3:]} remaining" if stream_details.get('remaining_time', '').startswith("00:") else stream_details.get('remaining_time', ''),
                        'inline': True
                    }
                ]
            }
            embeds_list.append(embed)
            logger.info(f"Created Play embed for {source_metadata.get('media_type')} event")
            return {'embeds': embeds_list}, 200
        else:
            logger.info("Webhook received, but no Source Metadata Details or Stream Details found. Data not saved.")
            return {'message': "Webhook received, but no Source Metadata Details or Stream Details found. Data not saved."}, 200
    except Exception as e:
        logger.error(f"Error while processing JSON payload: {str(e)}")
        return {'error': "Internal server error"}, 500

def plex_episode_content(data):
    try:
        embeds_list = []
        if data and 'source_metadata_details' in data:
            source_metadata = data['source_metadata_details']

            if source_metadata.get('media_type') == 'episode':
                embed = {
                    'title': f"{source_metadata.get('title')} (S{source_metadata.get('season_num00')}E{source_metadata.get('episode_num00')})",
                    'description': source_metadata.get('summary', ''),
                    'url': source_metadata.get('plex_url', ''),
                    'color': 519138,
                    'fields': [
                        {
                            'name': 'Quality',
                            'value': source_metadata.get('video_full_resolution', ''),
                            'inline': True
                        },
                        {
                            'name': 'Season/Episode',
                            'value': f"S{source_metadata.get('season_num00')} - E{source_metadata.get('episode_num00')}",
                            'inline': True
                        },
                        {
                            'name': 'Air date',
                            'value': source_metadata.get('air_date', ''),
                            'inline': True
                        },
                        {
                            'name': 'Genres',
                            'value': source_metadata.get('genres', ''),
                            'inline': True
                        },
                        {
                            'name': 'Details',
                            'value': f"📺 [TVDB]({source_metadata.get('thetvdb_url', '')})",
                            'inline': True
                        },
                        {
                            'name': 'Runtime',
                            'value': source_metadata.get('duration_time', ''),
                            'inline': True
                        }
                    ],
                    'author': {
                        'name': 'Plex - New Episode',
                        'icon_url': 'https://i.imgur.com/ZuFghbX.png'
                    },
                    'footer': {
                        'text': source_metadata.get('server_name', '')
                    },
                    'timestamp': source_metadata.get('utctime', ''),
                    'thumbnail': {
                        'url': source_metadata.get('poster_url', '')
                    },
                    'image': {
                        'url': 'https://imgur.com/a/D3MxSNM'
                    }
                }
                embeds_list.append(embed)
                logger.info("Created embed for episode event")
                return {'embeds': embeds_list}, 200
            else:
                logger.info("Webhook received, but no episode details found. Data not saved.")
                return {'message': "Webhook received, but no episode details found. Data not saved."}, 200
        else:
            logger.info("Webhook received, but no Source Metadata Details found. Data not saved.")
            return {'message': "Webhook received, but no Source Metadata Details found. Data not saved."}, 200
    except Exception as e:
        logger.error(f"Error while processing JSON payload: {str(e)}")
        return {'error': "Internal server error"}, 500