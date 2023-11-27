from calendar import weekday
import discord
import requests
import json
import re
import os
from datetime import datetime, timedelta

from src.globals import load_dotenv, TRAKT_CLIENT_ID, TMDB_API_KEY, TRAKT_USERNAME, TRAKT_URL_RATINGS, TRAKT_URL_FAVORITES, TMDB_API_KEY, user_link

import src.logging

logger = src.logging.logging.getLogger("trakt")

# START OF WEEKLY USER EMBED
def create_weekly_user_embed():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    previous_week = end_date - timedelta(days=7)
    week_number = previous_week.isocalendar()[1]
    year = previous_week.isocalendar()[0]
    start_date_str = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    end_date_str = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    headers = {
        "Content-Type": "application/json",
        "trakt-api-version": "2",
        "trakt-api-key": TRAKT_CLIENT_ID
    }
    page = 1
    all_history_data = []
    while True:
        history_url = f"https://api.trakt.tv/users/{TRAKT_USERNAME}/history"
        params = {
            "start_at": start_date_str,
            "end_at": end_date_str,
            "page": page,
            "limit": 100
        }
        history_response = requests.get(history_url, headers=headers, params=params)
        history_data = json.loads(history_response.text)
        if not history_data:
            break
        all_history_data.extend(history_data)
        page += 1
    sorted_history_data = sorted(all_history_data, key=lambda x: x['watched_at'])
    movie_count = 0
    for item in sorted_history_data:
        if item['type'] == 'movie':
            movie_count += 1
    movies_embed = discord.Embed(
        title=f"{movie_count} Movie{'s' if movie_count != 1 else ''} :clapper:", 
        color=0xFEA232
    )
    movies_embed.url = f"https://trakt.tv/users/{TRAKT_USERNAME}/history/movies/added?start_at={start_date_str}&end_at={end_date_str}"
    movies_embed.set_author(
        name=f"Trakt - Movies watched by {TRAKT_USERNAME} in Week {week_number}",
        icon_url='https://i.imgur.com/tvnkxAY.png'
    )
    timestamp_start = start_date.strftime('%a %b %d %Y')
    timestamp_end = end_date.strftime('%a %b %d %Y')
    timestamp = f"{timestamp_start} to {timestamp_end}"
    movies_embed.timestamp = datetime.now()
    movies_embed.set_footer(text=timestamp)
    movies_embed.set_image(url='https://imgur.com/a/D3MxSNM')
    if movie_count > 0:
        for item in sorted_history_data:
            if item['type'] == 'movie':
                movie_title = item['movie']['title']
                year = item['movie']['year'] if item['movie'].get('year') else ""
                watched_date = datetime.strptime(item['watched_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
                search_url = "https://api.themoviedb.org/3/search/multi"
                search_params = {
                    "api_key": TMDB_API_KEY,
                    "query": movie_title
                }
                search_response = requests.get(search_url, params=search_params)
                search_data = json.loads(search_response.text)
                if len(search_data["results"]) > 0:
                    poster_path = search_data["results"][0]["poster_path"]
                    if poster_path:
                        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
                    else:
                        poster_url = None
                else:
                    poster_url = None
                movies_embed.add_field(
                    name=f"{movie_title} ({year})",
                    value="",
                    inline=False
                )
                if poster_url:
                    movies_embed.set_thumbnail(url=poster_url)
    else:
        movies_embed.description = "No movies watched this week."
    episode_counts = {}
    for item in sorted_history_data:
        if item['type'] == 'episode':
            show_title = item['show']['title']
            year = item['show']['year'] if item['show'].get('year') else ""
            episode_counts[show_title] = {
                'count': episode_counts.get(show_title, {}).get('count', 0) + 1,
                'year': year
            }
    total_episode_count = sum(item['count'] for item in episode_counts.values())
    episodes_embed = discord.Embed(
        title=f"{total_episode_count} Episode{'s' if total_episode_count != 1 else ''} :tv:",
        color=0x328efe
    )
    episodes_embed.url = f"https://trakt.tv/users/{TRAKT_USERNAME}/history/episodes/added?start_at={start_date_str}&end_at={end_date_str}"
    episodes_embed.set_author(
        name=f"Trakt - Episodes watched by {TRAKT_USERNAME} in Week {week_number}",
        icon_url='https://i.imgur.com/tvnkxAY.png'
    )
    episodes_embed.timestamp = datetime.now()
    episodes_embed.set_footer(text=timestamp)
    episodes_embed.set_image(url='https://imgur.com/a/D3MxSNM')
    if total_episode_count > 0:
        for show_title, data in episode_counts.items():
            episode_count = data['count']
            year = data['year']
            search_url = "https://api.themoviedb.org/3/search/tv"
            search_params = {
                "api_key": TMDB_API_KEY,
                "query": show_title
            }
            search_response = requests.get(search_url, params=search_params)
            search_data = json.loads(search_response.text)
            if len(search_data["results"]) > 0:
                poster_path = search_data["results"][0]["poster_path"]
                if poster_path:
                    poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
                else:
                    poster_url = None
            else:
                poster_url = None
            episodes_embed.add_field(
                name=f"{show_title} ({year})",
                value=f"{episode_count} episode{'s' if episode_count != 1 else ''}",
                inline=False
            )
            if poster_url:
                episodes_embed.set_thumbnail(url=poster_url)
    else:
        episodes_embed.description = "No episodes watched this week."
    sorted_movie_fields = sorted(movies_embed.fields, key=lambda field: field.name)
    movies_embed.clear_fields()
    for field in sorted_movie_fields:
        movies_embed.add_field(name=field.name, value=field.value, inline=field.inline)
    sorted_episode_fields = sorted(episodes_embed.fields, key=lambda field: int(field.value.split()[0]), reverse=True)
    episodes_embed.clear_fields()
    for field in sorted_episode_fields:
        episodes_embed.add_field(name=field.name, value=field.value, inline=field.inline)
    data = {
        'embeds': [movies_embed.to_dict(), episodes_embed.to_dict()]
    }
    logger.info(f"Created embed for {TRAKT_USERNAME} weekly event")
    return data

# START OF WEEKLY GLOBAL EMBED
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
    movie_response = requests.get(movie_url, headers=headers)
    movies = sorted(movie_response.json(), key=lambda x: x['watcher_count'], reverse=True)
    show_response = requests.get(show_url, headers=headers)
    shows = sorted(show_response.json(), key=lambda x: x['watcher_count'], reverse=True)

    def fetch_image(item_type, item_id):
        if item_type == 'movie':
            url = f'https://api.themoviedb.org/3/movie/{item_id}?api_key={TMDB_API_KEY}&language=en-US'
        elif item_type == 'show':
            url = f'https://api.themoviedb.org/3/tv/{item_id}?api_key={TMDB_API_KEY}&language=en-US'
        else:
            return ''
        response = requests.get(url)
        if response.ok:
            data = response.json()
            poster_path = data.get('poster_path', '')
            if poster_path:
                return f'https://image.tmdb.org/t/p/w500/{poster_path}'
        return ''
    today = datetime.utcnow()
    previous_week_start = today - timedelta(days=7)
    previous_week_end = today - timedelta(days=1)
    footer_text = f"{previous_week_start.strftime('%a %b %d %Y')} to {previous_week_end.strftime('%a %b %d %Y')}"
    _, iso_week, _ = previous_week_start.isocalendar()
    movie_embed = {
        "color": 0xFEA232,
        "fields": [],
        "timestamp": datetime.utcnow().isoformat(),
        "thumbnail": {
            "url": "",
        },
        "author": {
            "name": f"Trakt - Top Movies in Week {iso_week}",
            "icon_url": "https://i.imgur.com/tvnkxAY.png"
        },
        "footer": {
            "text": footer_text
        }
    }
    for i, movie in enumerate(movies[:9]):
        watcher_count = "{:,}".format(movie['watcher_count'])
        image_url = fetch_image('movie', movie['movie']['ids']['tmdb'])
        trakt_url = f"https://trakt.tv/movies/{movie['movie']['ids']['slug']}"
        ranking_emoji = ranking_emojis.get(i + 1, "")
        ranking_text = "" if i < 3 else f"{i+1}. "
        if not movie_embed["thumbnail"]["url"] and image_url:
            movie_embed["thumbnail"]["url"] = image_url
        movie_embed["fields"].append({
            "name": f"{ranking_emoji} {ranking_text}{movie['movie']['title']} ({movie['movie']['year']})",
            "value": f"[{watcher_count} watchers]({trakt_url})",
            "inline": True
        })
    show_embed = {
        "color": 0x328efe,
        "fields": [],
        "timestamp": datetime.utcnow().isoformat(),
        "thumbnail": {
        "url": "",
        },
        "author": {
            "name": f"Trakt - Top Shows in Week {iso_week}",
            "icon_url": "https://i.imgur.com/tvnkxAY.png"
        },
        "footer": {
            "text": footer_text
        }
    }
    for i, show in enumerate(shows[:9]):
        watcher_count = "{:,}".format(show['watcher_count'])
        image_url = fetch_image('show', show['show']['ids']['tmdb'])
        trakt_url = f"https://trakt.tv/shows/{show['show']['ids']['slug']}"
        ranking_emoji = ranking_emojis.get(i + 1, "")
        ranking_text = f"{i+1}. " if i >= 3 else ""
        if not show_embed["thumbnail"]["url"] and image_url:
            show_embed["thumbnail"]["url"] = image_url
        show_embed["fields"].append({
            "name": f"{ranking_emoji} {ranking_text}{show['show']['title']} ({show['show']['year']})",
            "value": f"[{watcher_count} watchers]({trakt_url})",
            "inline": True
        })
    combined_embeds = [movie_embed, show_embed]
    data = {
        "embeds": combined_embeds
    }
    logger.info(f"Created embed for global weekly event")
    return data

# START OF TRAKT RATINGS
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
        {'name': 'User', 'value': user_link, 'inline': True},
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
            'icon_url': 'https://i.imgur.com/tvnkxAY.png'
        },
        'color': color,
        'fields': fields,
        'image': {'url': 'https://imgur.com/a/D3MxSNM'},
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
        {'name': 'User', 'value': user_link, 'inline': True},
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
            'icon_url': 'https://i.imgur.com/tvnkxAY.png'
        },
        'thumbnail': {'url': thumbnail},
        'color': color,
        'fields': fields,
        'image': {'url': 'https://imgur.com/a/D3MxSNM'},
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
        {'name': 'User', 'value': user_link, 'inline': True},
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
            'icon_url': 'https://i.imgur.com/tvnkxAY.png'
        },
        'thumbnail': {'url': thumbnail},
        'color': color,
        'fields': fields,
        'image': {'url': 'https://imgur.com/a/D3MxSNM'},
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
        {'name': 'User', 'value': user_link, 'inline': True},
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
            'icon_url': 'https://i.imgur.com/tvnkxAY.png'
        },
        'thumbnail': {'url': thumbnail},
        'color': color,
        'fields': fields,
        'image': {'url': 'https://imgur.com/a/D3MxSNM'},
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
    embeds = []
    current_time = datetime.utcnow()
    time_limit = current_time - timedelta(minutes=60)
    sorted_ratings = sorted(ratings, key=lambda x: x['rated_at'])
    for rating in reversed(sorted_ratings):
        rated_at = datetime.strptime(rating['rated_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
        if rated_at < time_limit:
            break
        if len(embeds) >= 10:
            embeds = embeds[::-1]
            data = {
                'embeds': embeds
            }
            save_rating_processed_embeds()
            return data
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
        embeds = embeds[::-1]  # Reverse the order of embeds
        data = {
            'embeds': embeds
        }
        save_rating_processed_embeds()
        return data
    return None

def trakt_ratings():
    load_rating_processed_embeds()
    try:
        ratings = fetch_trakt_ratings()
        result = process_ratings(ratings)
        if result:
            logger.info(f'Found {len(result["embeds"])} new ratings')
        return result
    except Exception as e:
        logger.error(f'Error occurred: {str(e)}')
        
# START OF TRAKT USER FAVORITES
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
        {'name': 'Links', 'value': f'{trakt_link} / {imdb_link}', 'inline': True}
    ]
    if notes:
        fields.append({'name': 'Comment', 'value': notes, 'inline': False})
    return {
        'title': f'{show["show"]["title"]}',
        'color': 3313406,
        'thumbnail': {'url': thumbnail},
        'fields': fields,
        'timestamp': timestamp,
        'image': {'url': 'https://imgur.com/a/D3MxSNM'},
        'author': {
            'name': f'Trakt - Show Favorited',
            'icon_url': 'https://i.imgur.com/tvnkxAY.png'
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
        {'name': 'Links', 'value': f'{trakt_link} / {imdb_link}', 'inline': True}
    ]
    if notes:
        fields.append({'name': 'Comment', 'value': notes, 'inline': False})
    return {
        'title': f'{movie["movie"]["title"]} ({movie["movie"]["year"]})',
        'color': 15892745,
        'thumbnail': {'url': thumbnail},
        'fields': fields,
        'timestamp': timestamp,
        'image': {'url': 'https://imgur.com/a/D3MxSNM'},
        'author': {
            'name': f'Trakt - Movie Favorited',
            'icon_url': 'https://i.imgur.com/tvnkxAY.png'
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
    embeds = []
    current_time = datetime.utcnow()
    time_limit = current_time - timedelta(hours=24)
    sorted_favorites = sorted(favorites, key=lambda x: x['listed_at'])
    for favorite in reversed(sorted_favorites):
        listed_at = datetime.strptime(favorite['listed_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
        if listed_at < time_limit:
            break
        if len(embeds) >= 10:
            embeds = embeds[::-1]
            data = {
                'embeds': embeds
            }
            save_favorite_processed_embeds()
            return data
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
    load_favorite_processed_embeds()
    try:
        favorites = fetch_trakt_favorites()
        result = process_favorites(favorites)
        if result:
            logger.info(f'Found {len(result["embeds"])} new favorites')
        return result
    except Exception as e:
        logger.error(f'Error occurred: {str(e)}')