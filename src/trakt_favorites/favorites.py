import requests
from datetime import datetime, timedelta

from src.globals import load_dotenv, TRAKT_URL_FAVORITES, TRAKT_CLIENT_ID, TRAKT_USERNAME, TMDB_API_KEY, user_link

from src.logging import logger_trakt

processed_embeds = set()

def format_show_embed(show):
    trakt_link = f'[Trakt](https://trakt.tv/shows/{show["show"]["ids"]["trakt"]})'
    imdb_link = f'[IMDb](https://www.imdb.com/title/{show["show"]["ids"]["imdb"]})'
    tmdb_details = get_tmdb_details('tv', show["show"]["ids"]["tmdb"])
    if tmdb_details:
        thumbnail = f'https://image.tmdb.org/t/p/w500/{tmdb_details["poster_path"]}'
    else:
        thumbnail = ''
    notes = show["notes"]
    fields = [
        {'name': 'Links', 'value': f'{trakt_link} / {imdb_link}', 'inline': True}
    ]
    if notes:
        fields.append({'name': 'Comment', 'value': notes, 'inline': False})
    return {
        'title': f'{show["show"]["title"]}',
        'description': f'{user_link} just favorited a show on Trakt!',
        'color': 3313406,
        'thumbnail': {'url': thumbnail},
        'fields': fields
    }

def format_movie_embed(movie):
    trakt_link = f'[Trakt](https://trakt.tv/movies/{movie["movie"]["ids"]["trakt"]})'
    imdb_link = f'[IMDb](https://www.imdb.com/title/{movie["movie"]["ids"]["imdb"]})'
    tmdb_details = get_tmdb_details('movie', movie["movie"]["ids"]["tmdb"])
    if tmdb_details:
        thumbnail = f'https://image.tmdb.org/t/p/w500/{tmdb_details["poster_path"]}'
    else:
        thumbnail = ''
    notes = movie["notes"]
    fields = [
        {'name': 'Links', 'value': f'{trakt_link} / {imdb_link}', 'inline': True}
    ]
    if notes:
        fields.append({'name': 'Comment', 'value': notes, 'inline': False})
    return {
        'title': f'{movie["movie"]["title"]} ({movie["movie"]["year"]})',
        'description': f'{user_link} just favorited a movie on Trakt!',
        'color': 15892745,
        'thumbnail': {'url': thumbnail},
        'fields': fields
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
        logger_trakt.info(f'Failed to fetch Trakt favorites: {str(e)}')
        return []

def get_tmdb_details(media_type, tmdb_id):
    url = f'https://api.themoviedb.org/3/{media_type}/{tmdb_id}?api_key={TMDB_API_KEY}'
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger_trakt.info(f'Failed to fetch TMDB details: {str(e)}')
        return None

def get_tmdb_season_details(tmdb_id, season_number):
    url = f'https://api.themoviedb.org/3/tv/{tmdb_id}/season/{season_number}?api_key={TMDB_API_KEY}'
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger_trakt.info(f'Failed to fetch TMDB season details: {str(e)}')
        return None

def get_tmdb_episode_details(tmdb_id, season_number, episode_number):
    url = f'https://api.themoviedb.org/3/tv/{tmdb_id}/season/{season_number}/episode/{episode_number}?api_key={TMDB_API_KEY}'
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger_trakt.info(f'Failed to fetch TMDB episode details: {str(e)}')
        return None

def process_favorites(favorites):
    embeds = []
    current_time = datetime.utcnow()
    time_limit = current_time - timedelta(minutes=60)

    sorted_favorites = sorted(favorites, key=lambda x: x['listed_at'])

    for favorite in reversed(sorted_favorites):
        listed_at = datetime.strptime(favorite['listed_at'], '%Y-%m-%dT%H:%M:%S.%fZ')

        if listed_at < time_limit:
            break

        if len(embeds) >= 10:
            # Maximum number of embeds reached, send the current embeds and reset the list
            embeds = embeds[::-1]  # Reverse the order of embeds
            data = {
                'embeds': embeds
            }
            return data

        if favorite['type'] == 'show':
            if favorite['show']['ids']['trakt'] not in processed_embeds:
                embed = format_show_embed(favorite)
                embeds.append(embed)
                processed_embeds.add(favorite['show']['ids']['trakt'])
        elif favorite['type'] == 'movie':
            if favorite['movie']['ids']['trakt'] not in processed_embeds:
                embed = format_movie_embed(favorite)
                embeds.append(embed)
                processed_embeds.add(favorite['movie']['ids']['trakt'])

    if embeds:
        embeds = embeds[::-1]  # Reverse the order of embeds
        data = {
            'embeds': embeds
        }
        return data

def trakt_favorites():
    while True:
        try:
            favorites = fetch_trakt_favorites()
            result = process_favorites(favorites)
            if result is not None:
                logger_trakt.info("A new Embed has been sent to the Bot:")
                logger_trakt.info(result)
            return result
        except Exception as e:
            logger_trakt.info(f'Error occurred: {str(e)}')