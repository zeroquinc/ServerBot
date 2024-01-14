from calendar import weekday
import requests
from datetime import datetime, timedelta

from .globals import (
    TRAKT_CLIENT_ID,
    TMDB_API_KEY,
    TRAKT_ICON_URL,
    TMDB_IMAGE_URL,
    TMDB_MOVIE_URL,
    TMDB_SHOW_URL
)
from .custom_logger import logger

image_cache = {}

EMBED_COLOR_MOVIE = 0xFEA232
EMBED_COLOR_SHOW = 0x328efe

def get_data_from_url(url, headers):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return []
    return sorted(response.json(), key=lambda x: x['watcher_count'], reverse=True)

def fetch_image(item_type, item_id):
    if item_type not in image_cache:
        image_cache[item_type] = {}
    if item_id in image_cache[item_type]:
        return image_cache[item_type][item_id]
    
    url = f'{TMDB_MOVIE_URL if item_type == "movie" else TMDB_SHOW_URL}{item_id}?api_key={TMDB_API_KEY}&language=en-US'
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return ''
    
    data = response.json()
    poster_path = data.get('poster_path', '')
    if poster_path:
        image_url = f'{TMDB_IMAGE_URL}{poster_path}'
        image_cache[item_type][item_id] = image_url
        return image_url
    return ''

def create_embed(color, author_name, footer_text):
    return {
        "color": color,
        "fields": [],
        "thumbnail": {
            "url": "",
        },
        "author": {
            "name": author_name,
            "icon_url": TRAKT_ICON_URL
        },
        "footer": {
            "text": footer_text
        }
    }

def add_fields_to_embed(embed, items, item_type, ranking_emojis):
    for i, item in enumerate(items[:9]):
        watcher_count = "{:,}".format(item['watcher_count'])
        image_url = fetch_image(item_type, item[item_type]['ids']['tmdb'])
        trakt_url = f"https://trakt.tv/{item_type}s/{item[item_type]['ids']['slug']}"
        ranking_emoji = ranking_emojis.get(i + 1, "")
        ranking_text = "" if i < 3 else f"{i+1}. "
        if not embed["thumbnail"]["url"] and image_url:
            embed["thumbnail"]["url"] = image_url
        embed["fields"].append({
            "name": f"{ranking_emoji} {ranking_text}{item[item_type]['title']} ({item[item_type]['year']})",
            "value": f"[{watcher_count} watchers]({trakt_url})",
            "inline": True
        })
    return embed

def create_weekly_global_embed(): 
    movie_url = 'https://api.trakt.tv/movies/watched/period=weekly'
    show_url = 'https://api.trakt.tv/shows/watched/period=weekly'
    headers = {
        'Content-Type': 'application/json',
        'trakt-api-version': '2',
        "trakt-api-key": TRAKT_CLIENT_ID
    }
    ranking_emojis = {
        1: ":first_place:",
        2: ":second_place:",
        3: ":third_place:"
    }
    movies = get_data_from_url(movie_url, headers)
    shows = get_data_from_url(show_url, headers)

    today = datetime.utcnow()
    previous_week_start = today - timedelta(days=7)
    previous_week_end = today - timedelta(days=1)
    footer_text = f"{previous_week_start.strftime('%a %b %d %Y')} to {previous_week_end.strftime('%a %b %d %Y')}"
    _, iso_week, _ = previous_week_start.isocalendar()

    movie_embed = create_embed(EMBED_COLOR_MOVIE, f"Trakt - Top Movies in Week {iso_week}", footer_text)
    movie_embed = add_fields_to_embed(movie_embed, movies, 'movie', ranking_emojis)

    show_embed = create_embed(EMBED_COLOR_SHOW, f"Trakt - Top Shows in Week {iso_week}", footer_text)
    show_embed = add_fields_to_embed(show_embed, shows, 'show', ranking_emojis)

    combined_embeds = [movie_embed, show_embed]
    data = {
        "embeds": combined_embeds
    }
    logger.info("Created embed for global weekly event")
    return data