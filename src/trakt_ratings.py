from calendar import weekday
import requests
import json
import re
import os
from datetime import datetime, timedelta

from src.globals import load_dotenv, TRAKT_CLIENT_ID, TMDB_API_KEY, TRAKT_USERNAME, TRAKT_URL_RATINGS, TRAKT_URL_USER, TRAKT_ICON_URL, DISCORD_THUMBNAIL
from .custom_logger import logger

processed_rating_embeds = set()

def load_rating_processed_embeds():
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'json', 'processed_rating_embeds.json')
    try:
        with open(file_path, 'r') as f:
            processed_rating_embeds.update(json.load(f))
            logger.info(f"Successfully loaded data from {file_path}")
    except FileNotFoundError:
        logger.info(f"File {file_path} not found. Skipping loading.")

def save_rating_processed_embeds():
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'json', 'processed_rating_embeds.json')
    with open(file_path, 'w') as f:
        json.dump(list(processed_rating_embeds), f)
    logger.info(f"Successfully saved data to {file_path}")

def convert_spoiler_tags(comment):
    spoiler_patterns = [
        r'\[spoiler\](.*?)\[/spoiler\]',
        r'\[spoiler\](.*?)\[\\/spoiler\]',
        r'\[spoiler\](.*?)\[\\/spoiler\]',
        r'\[spoiler\](.*?)\[\/spoiler\]',
        r'\[spoiler\](.*?)\[\=\/spoiler\]',
    ]

    def spoiler_replacement(match):
        return f'||{match.group(1)}||'
    for pattern in spoiler_patterns:
        comment = re.sub(pattern, spoiler_replacement, comment)
    return comment

def format_rating_show_embed(show):
    trakt_link = f'[Trakt](https://trakt.tv/shows/{show["show"]["ids"]["trakt"]})'
    imdb_link = f'[IMDb](https://www.imdb.com/title/{show["show"]["ids"]["imdb"]})'
    tmdb_details = get_tmdb_details('tv', show["show"]["ids"]["tmdb"])
    if tmdb_details:
        thumbnail = f'https://image.tmdb.org/t/p/w500/{tmdb_details["poster_path"]}'
    else:
        thumbnail = ''
    rating = show["rating"]
    color = get_color_from_rating(rating)
    timestamp = datetime.utcnow().isoformat()
    fields = [
        {'name': 'Rating', 'value': f'{rating} :star:', 'inline': True},
        {'name': 'User', 'value': TRAKT_URL_USER, 'inline': True},
        {'name': 'Links', 'value': f'{trakt_link} • {imdb_link}', 'inline': True}
    ]
    user_comment = get_user_comment(TRAKT_USERNAME, show["show"]["ids"]["trakt"], 'show')
    if user_comment:
        converted_comment = convert_spoiler_tags(user_comment['comment'])
        fields.append({'name': 'Comment', 'value': converted_comment, 'inline': False})
    return {
        'title': f'{show["show"]["title"]}',
        'thumbnail': {'url': thumbnail},
        'author': {
            'name': 'Trakt - Show Rated',
            'icon_url': TRAKT_ICON_URL
        },
        'color': color,
        'fields': fields,
        'image': {'url': DISCORD_THUMBNAIL},
        'timestamp': timestamp
    }

def format_rating_episode_embed(episode):
    trakt_link = f'[Trakt](https://trakt.tv/shows/{episode["show"]["ids"]["trakt"]}/seasons/{episode["episode"]["season"]}/episodes/{episode["episode"]["number"]})'
    imdb_link = f'[IMDb](https://www.imdb.com/title/{episode["episode"]["ids"]["imdb"]})' if episode["episode"]["ids"]["imdb"] else ''
    tmdb_details = get_tmdb_details('tv', episode["show"]["ids"]["tmdb"])
    if tmdb_details:
        season_number = episode["episode"]["season"]
        episode_number = episode["episode"]["number"]
        episode_tmdb_details = get_tmdb_episode_details(episode["show"]["ids"]["tmdb"], season_number, episode_number)
        if episode_tmdb_details:
            thumbnail = f'https://image.tmdb.org/t/p/w500/{tmdb_details["poster_path"]}'
    else:
        thumbnail = ''
    rating = episode["rating"]
    color = get_color_from_rating(rating)
    timestamp = datetime.utcnow().isoformat()
    fields = [
        {'name': 'Rating', 'value': f'{rating} :star:', 'inline': True},
        {'name': 'User', 'value': TRAKT_URL_USER, 'inline': True},
        {'name': 'Links', 'value': f'{trakt_link} • {imdb_link}' if imdb_link else trakt_link, 'inline': True}
    ]
    user_comment = get_user_comment(TRAKT_USERNAME, episode["episode"]["ids"]["trakt"], 'episode')
    if user_comment:
        converted_comment = convert_spoiler_tags(user_comment['comment'])
        fields.append({'name': 'Comment', 'value': converted_comment, 'inline': False})
    return {
        'title': f'{episode["show"]["title"]} - {episode["episode"]["title"]} (S{season_number:02d}E{episode_number:02d})',
        'author': {
            'name': 'Trakt - Episode Rated',
            'icon_url': TRAKT_ICON_URL
        },
        'thumbnail': {'url': thumbnail},
        'color': color,
        'fields': fields,
        'image': {'url': DISCORD_THUMBNAIL},
        'timestamp': timestamp
    }

def format_rating_season_embed(season):
    trakt_link = f'[Trakt](https://trakt.tv/shows/{season["show"]["ids"]["trakt"]}/seasons/{season["season"]["number"]})'
    tmdb_details = get_tmdb_details('tv', season["show"]["ids"]["tmdb"])
    if tmdb_details:
        if 'seasons' in tmdb_details:
            season_offset = tmdb_details.get('season_number_offset', 0)
            season_number = season["season"]["number"] - season_offset
            if season_number >= 0 and season_number < len(tmdb_details['seasons']):
                season_tmdb = tmdb_details['seasons'][season_number]
                thumbnail = f'https://image.tmdb.org/t/p/w500/{season_tmdb["poster_path"]}'
            else:
                thumbnail = ''
        else:
            thumbnail = ''
    else:
        thumbnail = ''
    rating = season["rating"]
    color = get_color_from_rating(rating)
    timestamp = datetime.utcnow().isoformat()
    fields = [
        {'name': 'Rating', 'value': f'{rating} :star:', 'inline': True},
        {'name': 'User', 'value': TRAKT_URL_USER, 'inline': True},
        {'name': 'Links', 'value': trakt_link, 'inline': True}
    ]
    user_comment = get_user_comment(TRAKT_USERNAME, season["season"]["ids"]["trakt"], 'season')
    if user_comment:
        converted_comment = convert_spoiler_tags(user_comment['comment'])
        fields.append({'name': 'Comment', 'value': converted_comment, 'inline': False})
    return {
        'title': f'{season["show"]["title"]} - Season {season["season"]["number"]}',
        'author': {
            'name': 'Trakt - Season Rated',
            'icon_url': TRAKT_ICON_URL
        },
        'thumbnail': {'url': thumbnail},
        'color': color,
        'fields': fields,
        'image': {'url': DISCORD_THUMBNAIL},
        'timestamp': timestamp
    }

def format_rating_movie_embed(movie):
    trakt_link = f'[Trakt](https://trakt.tv/movies/{movie["movie"]["ids"]["trakt"]})'
    imdb_link = f'[IMDb](https://www.imdb.com/title/{movie["movie"]["ids"]["imdb"]})'
    tmdb_details = get_tmdb_details('movie', movie["movie"]["ids"]["tmdb"])
    if tmdb_details:
        thumbnail = f'https://image.tmdb.org/t/p/w500/{tmdb_details["poster_path"]}'
    else:
        thumbnail = ''
    rating = movie["rating"]
    color = get_color_from_rating(rating)
    timestamp = datetime.utcnow().isoformat()
    fields = [
        {'name': 'Rating', 'value': f'{rating} :star:', 'inline': True},
        {'name': 'User', 'value': TRAKT_URL_USER, 'inline': True},
        {'name': 'Links', 'value': f'{trakt_link} • {imdb_link}', 'inline': True}
    ]
    user_comment = get_user_comment(TRAKT_USERNAME, movie["movie"]["ids"]["trakt"], 'movie')
    if user_comment:
        converted_comment = convert_spoiler_tags(user_comment['comment'])
        fields.append({'name': 'Comment', 'value': converted_comment, 'inline': False})
    return {
        'title': f'{movie["movie"]["title"]} ({movie["movie"]["year"]})',
        'author': {
            'name': 'Trakt - Movie Rated',
            'icon_url': TRAKT_ICON_URL
        },
        'thumbnail': {'url': thumbnail},
        'color': color,
        'fields': fields,
        'image': {'url': DISCORD_THUMBNAIL},
        'timestamp': timestamp
    }
    
def get_user_comment(username, content_id, content_type):
    comments_url = f'https://api.trakt.tv/users/{username}/comments'
    headers = {
        'Content-Type': 'application/json',
        'trakt-api-version': '2',
        'trakt-api-key': TRAKT_CLIENT_ID
    }
    response = requests.get(comments_url, headers=headers)
    if response.status_code == 200:
        comments = response.json()
        for comment in comments:
            if comment['type'] == content_type and comment[content_type]['ids']['trakt'] == content_id:
                return comment['comment']
    else:
        logger.error(f'Request to {comments_url} returned status code {response.status_code}')
    return None

def get_color_from_rating(rating):
    if rating == 1:
        return 0xFF5733  # Orange Red
    elif rating == 2:
        return 0x00BFFF  # Deep Sky Blue
    elif rating == 3:
        return 0x32CD32  # Lime Green
    elif rating == 4:
        return 0xFF1493  # Deep Pink
    elif rating == 5:
        return 0x5D6F31  # Orange
    elif rating == 6:
        return 0x8A2BE2  # Blue Violet
    elif rating == 7:
        return 0xE9967A  # Dark Salmon
    elif rating == 8:
        return 0x8A2BE2  # Sea Green
    elif rating == 9:
        return 0xACE5EE  # Tomato
    elif rating == 10:
        return 0xFFD700  # Gold
    else:
        return 0x808080  # Default color

def fetch_trakt_ratings():
    headers = {
        'Content-Type': 'application/json',
        'trakt-api-version': '2',
        'trakt-api-key': TRAKT_CLIENT_ID
    }
    response = requests.get(TRAKT_URL_RATINGS, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f'Failed to fetch Trakt ratings: {response.status_code}')
        return []
        
def get_tmdb_details(media_type, tmdb_id):
    url = f'https://api.themoviedb.org/3/{media_type}/{tmdb_id}?api_key={TMDB_API_KEY}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f'Failed to fetch TMDB details: {response.status_code}')
        return None

def get_tmdb_season_details(tmdb_id, season_number):
    url = f'https://api.themoviedb.org/3/tv/{tmdb_id}/season/{season_number}?api_key={TMDB_API_KEY}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f'Failed to fetch TMDB season details: {response.status_code}')
        return None
        
def get_tmdb_episode_details(tmdb_id, season_number, episode_number):
    url = f'https://api.themoviedb.org/3/tv/{tmdb_id}/season/{season_number}/episode/{episode_number}?api_key={TMDB_API_KEY}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f'Failed to fetch TMDB episode details: {response.status_code}')
        return None

def process_ratings(ratings):
    current_time = datetime.utcnow()
    time_limit = current_time - timedelta(minutes=60)
    sorted_ratings = sorted(ratings, key=lambda x: x['rated_at'])

    # Check if there are any new ratings
    new_ratings = [rating for rating in reversed(sorted_ratings) if datetime.strptime(rating['rated_at'], '%Y-%m-%dT%H:%M:%S.%fZ') >= time_limit]
    if not new_ratings:
        return None  # No new ratings, so return None

    # There are new ratings, so load the processed embeds
    load_rating_processed_embeds()

    embeds = []
    for rating in new_ratings:
        if len(embeds) >= 10:
            break
        if rating['type'] == 'show':
            if rating['show']['ids']['trakt'] not in processed_rating_embeds:
                embed = format_rating_show_embed(rating)
                embeds.append(embed)
                processed_rating_embeds.add(rating['show']['ids']['trakt'])
        elif rating['type'] == 'episode':
            if rating['episode']['ids']['trakt'] not in processed_rating_embeds:
                embed = format_rating_episode_embed(rating)
                embeds.append(embed)
                processed_rating_embeds.add(rating['episode']['ids']['trakt'])
        elif rating['type'] == 'season':
            if rating['season']['ids']['trakt'] not in processed_rating_embeds:
                embed = format_rating_season_embed(rating)
                embeds.append(embed)
                processed_rating_embeds.add(rating['season']['ids']['trakt'])
        elif rating['type'] == 'movie':
            if rating['movie']['ids']['trakt'] not in processed_rating_embeds:
                embed = format_rating_movie_embed(rating)
                embeds.append(embed)
                processed_rating_embeds.add(rating['movie']['ids']['trakt'])
    if embeds:
        embeds = embeds[::-1]
        data = {
            'embeds': embeds
        }
        save_rating_processed_embeds()
        return data
    return None

def trakt_ratings():
    try:
        ratings = fetch_trakt_ratings()
        result = process_ratings(ratings)
        if result:
            logger.info(f'Found {len(result["embeds"])} new ratings')
        return result
    except Exception as e:
        logger.error(f'Error occurred: {str(e)}')