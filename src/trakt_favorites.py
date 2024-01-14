from calendar import weekday
import requests
import json
import os
from datetime import datetime, timedelta

from src.globals import (
    TRAKT_CLIENT_ID, 
    TMDB_API_KEY, 
    TRAKT_USERNAME, 
    TRAKT_URL_FAVORITES, 
    TMDB_API_KEY, 
    TRAKT_ICON_URL, 
    DISCORD_THUMBNAIL
)

from .custom_logger import logger

processed_favorite_embeds = set()

def load_favorite_processed_embeds():
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'json', 'processed_favorite_embeds.json')
    try:
        with open(file_path, 'r') as f:
            processed_favorite_embeds.update(json.load(f))
            logger.info(f"Successfully loaded data from {file_path}")
    except FileNotFoundError:
        logger.info(f"File {file_path} not found. Skipping loading.")

def save_favorite_processed_embeds():
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'json', 'processed_favorite_embeds.json')
    with open(file_path, 'w') as f:
        json.dump(list(processed_favorite_embeds), f)
    logger.info(f"Successfully saved data to {file_path}")

def format_favorite_show_embed(show):
    trakt_link = f'[Trakt](https://trakt.tv/shows/{show["show"]["ids"]["trakt"]})'
    imdb_link = f'[IMDb](https://www.imdb.com/title/{show["show"]["ids"]["imdb"]})'
    tmdb_details = get_tmdb_details('tv', show["show"]["ids"]["tmdb"])
    if tmdb_details:
        thumbnail = f'https://image.tmdb.org/t/p/w500/{tmdb_details["poster_path"]}'
    else:
        thumbnail = ''
    notes = show["notes"]
    timestamp = datetime.utcnow().isoformat()
    fields = [
        {'name': 'User', 'value': TRAKT_USERNAME, 'inline': True},
        {'name': 'Links', 'value': f'{trakt_link} • {imdb_link}', 'inline': True}
    ]
    if notes:
        fields.append({'name': 'Comment', 'value': notes, 'inline': False})
    return {
        'title': f'{show["show"]["title"]}',
        'color': 3313406,
        'thumbnail': {'url': thumbnail},
        'fields': fields,
        'timestamp': timestamp,
        'image': {'url': DISCORD_THUMBNAIL},
        'author': {
            'name': 'Trakt - Show Favorited',
            'icon_url': TRAKT_ICON_URL
        }
    }

def format_favorite_movie_embed(movie):
    trakt_link = f'[Trakt](https://trakt.tv/movies/{movie["movie"]["ids"]["trakt"]})'
    imdb_link = f'[IMDb](https://www.imdb.com/title/{movie["movie"]["ids"]["imdb"]})'
    tmdb_details = get_tmdb_details('movie', movie["movie"]["ids"]["tmdb"])
    if tmdb_details:
        thumbnail = f'https://image.tmdb.org/t/p/w500/{tmdb_details["poster_path"]}'
    else:
        thumbnail = ''
    notes = movie["notes"]
    timestamp = datetime.utcnow().isoformat()
    fields = [
        {'name': 'User', 'value': TRAKT_USERNAME, 'inline': True},
        {'name': 'Links', 'value': f'{trakt_link} • {imdb_link}', 'inline': True}
    ]
    if notes:
        fields.append({'name': 'Comment', 'value': notes, 'inline': False})
    return {
        'title': f'{movie["movie"]["title"]} ({movie["movie"]["year"]})',
        'color': 15892745,
        'thumbnail': {'url': thumbnail},
        'fields': fields,
        'timestamp': timestamp,
        'image': {'url': DISCORD_THUMBNAIL},
        'author': {
            'name': 'Trakt - Movie Favorited',
            'icon_url': TRAKT_ICON_URL
        }
    }

def fetch_trakt_favorites():
    headers = {
        'Content-Type': 'application/json',
        'trakt-api-version': '2',
        'trakt-api-key': TRAKT_CLIENT_ID
    }
    try:
        response = requests.get(TRAKT_URL_FAVORITES, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.info(f'Failed to fetch Trakt favorites: {str(e)}')
        return []

def get_tmdb_details(media_type, tmdb_id):
    url = f'https://api.themoviedb.org/3/{media_type}/{tmdb_id}?api_key={TMDB_API_KEY}'
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.info(f'Failed to fetch TMDB details: {str(e)}')
        return None

def get_tmdb_season_details(tmdb_id, season_number):
    url = f'https://api.themoviedb.org/3/tv/{tmdb_id}/season/{season_number}?api_key={TMDB_API_KEY}'
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.info(f'Failed to fetch TMDB season details: {str(e)}')
        return None

def get_tmdb_episode_details(tmdb_id, season_number, episode_number):
    url = f'https://api.themoviedb.org/3/tv/{tmdb_id}/season/{season_number}/episode/{episode_number}?api_key={TMDB_API_KEY}'
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.info(f'Failed to fetch TMDB episode details: {str(e)}')
        return None

def process_favorites(favorites):
    current_time = datetime.utcnow()
    time_limit = current_time - timedelta(hours=24)
    sorted_favorites = sorted(favorites, key=lambda x: x['listed_at'])

    # Check if there are any new favorites
    new_favorites = [favorite for favorite in reversed(sorted_favorites) if datetime.strptime(favorite['listed_at'], '%Y-%m-%dT%H:%M:%S.%fZ') >= time_limit]
    if not new_favorites:
        return None  # No new favorites, so return None

    # There are new favorites, so load the processed embeds
    load_favorite_processed_embeds()

    embeds = []
    for favorite in new_favorites:
        if len(embeds) >= 10:
            break
        if favorite['type'] == 'show':
            if favorite['show']['ids']['trakt'] not in processed_favorite_embeds:
                embed = format_favorite_show_embed(favorite)
                embeds.append(embed)
                processed_favorite_embeds.add(favorite['show']['ids']['trakt'])
        elif favorite['type'] == 'movie':
            if favorite['movie']['ids']['trakt'] not in processed_favorite_embeds:
                embed = format_favorite_movie_embed(favorite)
                embeds.append(embed)
                processed_favorite_embeds.add(favorite['movie']['ids']['trakt'])
    if embeds:
        embeds = embeds[::-1]
        data = {
            'embeds': embeds
        }
        save_favorite_processed_embeds()
        return data
    return None

def trakt_favorites():
    try:
        favorites = fetch_trakt_favorites()
        result = process_favorites(favorites)
        if result:
            logger.info(f'Found {len(result["embeds"])} new favorites')
        return result
    except Exception as e:
        logger.error(f'Error occurred: {str(e)}')