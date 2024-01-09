from calendar import weekday
import discord
import requests
import json
from datetime import datetime, timedelta

from src.globals import load_dotenv, TRAKT_CLIENT_ID, TMDB_API_KEY, TRAKT_USERNAME, TMDB_API_KEY
from src.custom_logger import logger

def get_dates():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    previous_week = end_date - timedelta(days=7)
    week_number = previous_week.isocalendar()[1]
    year = previous_week.isocalendar()[0]
    start_date_str = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    end_date_str = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    return start_date, end_date, week_number, year, start_date_str, end_date_str

def get_history_data(headers, start_date_str, end_date_str):
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
    return sorted(all_history_data, key=lambda x: x['watched_at'])

def get_movie_count(sorted_history_data):
    movie_count = 0
    for item in sorted_history_data:
        if item['type'] == 'movie':
            movie_count += 1
    return movie_count

def get_episode_counts(sorted_history_data):
    episode_counts = {}
    for item in sorted_history_data:
        if item['type'] == 'episode':
            show_title = item['show']['title']
            year = item['show']['year'] if item['show'].get('year') else ""
            episode_counts[show_title] = {
                'count': episode_counts.get(show_title, {}).get('count', 0) + 1,
                'year': year
            }
    return episode_counts

def get_poster_url(search_url, search_params):
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
    return poster_url

def add_movie_fields_to_embed(movies_embed, sorted_history_data):
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
            poster_url = get_poster_url(search_url, search_params)
            movies_embed.add_field(
                name=f"{movie_title} ({year})",
                value="",
                inline=False
            )
            if poster_url:
                movies_embed.set_thumbnail(url=poster_url)
    return movies_embed

def add_episode_fields_to_embed(episodes_embed, episode_counts):
    for show_title, data in episode_counts.items():
        episode_count = data['count']
        year = data['year']
        search_url = "https://api.themoviedb.org/3/search/tv"
        search_params = {
            "api_key": TMDB_API_KEY,
            "query": show_title
        }
        poster_url = get_poster_url(search_url, search_params)
        episodes_embed.add_field(
            name=f"{show_title} ({year})",
            value=f"{episode_count} episode{'s' if episode_count != 1 else ''}",
            inline=False
        )
        if poster_url:
            episodes_embed.set_thumbnail(url=poster_url)
    return episodes_embed

def create_movie_embed(sorted_history_data, start_date_str, end_date_str, week_number):
    movie_count = get_movie_count(sorted_history_data)
    movies_embed = discord.Embed(
        title=f"{movie_count} Movie{'s' if movie_count != 1 else ''} :clapper:", 
        color=0xFEA232
    )
    movies_embed.url = f"https://trakt.tv/users/{TRAKT_USERNAME}/history/movies/added?start_at={start_date_str}&end_at={end_date_str}"
    movies_embed.set_author(
        name=f"Trakt - Movies watched by {TRAKT_USERNAME} in Week {week_number}",
        icon_url='https://i.imgur.com/tvnkxAY.png'
    )
    start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M:%SZ')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M:%SZ')
    timestamp_start = start_date.strftime('%a %b %d %Y')
    timestamp_end = end_date.strftime('%a %b %d %Y')
    timestamp = f"{timestamp_start} to {timestamp_end}"
    movies_embed.set_footer(text=timestamp)
    movies_embed.set_image(url='https://imgur.com/a/D3MxSNM')
    if movie_count > 0:
        movies_embed = add_movie_fields_to_embed(movies_embed, sorted_history_data)
    else:
        movies_embed.description = "No movies watched this week."
    return movies_embed

def create_episode_embed(sorted_history_data, start_date_str, end_date_str, week_number):
    episode_counts = get_episode_counts(sorted_history_data)
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
    start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M:%SZ')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M:%SZ')
    timestamp_start = start_date.strftime('%a %b %d %Y')
    timestamp_end = end_date.strftime('%a %b %d %Y')
    timestamp = f"{timestamp_start} to {timestamp_end}"
    episodes_embed.set_footer(text=timestamp)
    episodes_embed.set_image(url='https://imgur.com/a/D3MxSNM')
    if total_episode_count > 0:
        episodes_embed = add_episode_fields_to_embed(episodes_embed, episode_counts)
    else:
        episodes_embed.description = "No episodes watched this week."
    return episodes_embed

def create_weekly_user_embed():
    start_date_str, end_date_str, week_number, year, start_date_str, end_date_str = get_dates()
    headers = {
        "Content-Type": "application/json",
        "trakt-api-version": "2",
        "trakt-api-key": TRAKT_CLIENT_ID
    }
    sorted_history_data = get_history_data(headers, start_date_str, end_date_str)
    movies_embed = create_movie_embed(sorted_history_data, start_date_str, end_date_str, week_number)
    episodes_embed = create_episode_embed(sorted_history_data, start_date_str, end_date_str, week_number)
    data = {
        'embeds': [movies_embed.to_dict(), episodes_embed.to_dict()]
    }
    logger.info(f"Created embed for {TRAKT_USERNAME} weekly event")
    return data