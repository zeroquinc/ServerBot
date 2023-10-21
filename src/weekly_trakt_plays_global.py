import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

def create_weekly_embed():
    # Determine the path to the parent directory (one level up from the current script's location)
    parent_directory = os.path.dirname(os.path.dirname(__file__))
    env_file_path = os.path.join(parent_directory, '.env')

    # Load the .env file from the parent directory
    load_dotenv(env_file_path)
    
    # Access the environment variables from the .env file
    trakt_client_id = os.getenv("TRAKT_CLIENT_ID")
    tmdb_api_key = os.getenv("TMDB_API_KEY")
    
    # Trakt API endpoints
    movie_url = 'https://api.trakt.tv/movies/watched/period=weekly'
    show_url = 'https://api.trakt.tv/shows/watched/period=weekly'

    # Trakt API headers
    headers = {
        'Content-Type': 'application/json',
        'trakt-api-version': '2',
        "trakt-api-key": trakt_client_id
    }

    # Define a dictionary to map ranking numbers to emojis
    ranking_emojis = {
        1: ":first_place:",
        2: ":second_place:",
        3: ":third_place:"
    }

    # Get top 10 most played movies and their play time
    movie_response = requests.get(movie_url, headers=headers)
    movies = sorted(movie_response.json(), key=lambda x: x['watcher_count'], reverse=True)

    # Get top 10 most played shows and their play time
    show_response = requests.get(show_url, headers=headers)
    shows = sorted(show_response.json(), key=lambda x: x['watcher_count'], reverse=True)

    # Fetch poster image from TMDB API
    def fetch_image(item_type, item_id):
        if item_type == 'movie':
            url = f'https://api.themoviedb.org/3/movie/{item_id}?api_key={tmdb_api_key}&language=en-US'
        elif item_type == 'show':
            url = f'https://api.themoviedb.org/3/tv/{item_id}?api_key={tmdb_api_key}&language=en-US'
        else:
            return ''
        response = requests.get(url)
        if response.ok:
            data = response.json()
            poster_path = data.get('poster_path', '')
            if poster_path:
                return f'https://image.tmdb.org/t/p/w500/{poster_path}'
        return ''

    # Calculate dates for footer_text
    today = datetime.utcnow()
    previous_week_start = today - timedelta(days=7)
    previous_week_end = today - timedelta(days=1)
    footer_text = f"{previous_week_start.strftime('%a %b %d %Y')} to {previous_week_end.strftime('%a %b %d %Y')}"

    # Calculate the ISO week number for the previous week
    _, iso_week, _ = previous_week_start.isocalendar()

    # Create embed JSON for movies
    movie_embed = {
        "color": 0xFEA232,
        "fields": [],
        "timestamp": datetime.utcnow().isoformat(),
        "thumbnail": {
            "url": "",
        },
        "author": {
            "name": f"Top Movies from Trakt in Week {iso_week}",
            "icon_url": "https://i.imgur.com/fjWQwef.png"
        },
        "footer": {
            "text": footer_text
        }
    }

    # Add movies and their play count to movie embed JSON
    for i, movie in enumerate(movies[:9]):
        watcher_count = "{:,}".format(movie['watcher_count'])
        image_url = fetch_image('movie', movie['movie']['ids']['tmdb'])
        trakt_url = f"https://trakt.tv/movies/{movie['movie']['ids']['slug']}"
        ranking_emoji = ranking_emojis.get(i + 1, "")  # Get the emoji for the ranking, or empty string if not in top 3
        ranking_text = "" if i < 3 else f"{i+1}. "  # Remove ranking number for top 3 items
        if not movie_embed["thumbnail"]["url"] and image_url:
            movie_embed["thumbnail"]["url"] = image_url
        movie_embed["fields"].append({
            "name": f"{ranking_emoji} {ranking_text}{movie['movie']['title']} ({movie['movie']['year']})",
            "value": f"[{watcher_count} watchers]({trakt_url})",
            "inline": True
        })

    # Create embed JSON for shows
    show_embed = {
        "color": 0x328efe,
        "fields": [],
        "timestamp": datetime.utcnow().isoformat(),
        "thumbnail": {
        "url": "",
        },
        "author": {
            "name": f"Top Shows from Trakt in Week {iso_week}",
            "icon_url": "https://i.imgur.com/poGtHrf.png"
        },
        "footer": {
            "text": footer_text
        }
    }

    # Add shows and their play count to show embed JSON
    for i, show in enumerate(shows[:9]):
        watcher_count = "{:,}".format(show['watcher_count'])
        image_url = fetch_image('show', show['show']['ids']['tmdb'])
        trakt_url = f"https://trakt.tv/shows/{show['show']['ids']['slug']}"
        ranking_emoji = ranking_emojis.get(i + 1, "")  # Get the emoji for the ranking, or empty string if not in top 3
        ranking_text = f"{i+1}. " if i >= 3 else ""  # Display ranking number for non-top 3 items
        if not show_embed["thumbnail"]["url"] and image_url:
            show_embed["thumbnail"]["url"] = image_url
        show_embed["fields"].append({
            "name": f"{ranking_emoji} {ranking_text}{show['show']['title']} ({show['show']['year']})",
            "value": f"[{watcher_count} watchers]({trakt_url})",
            "inline": True
        })

    # Combine the two embeds into one dictionary
    combined_embeds = [movie_embed, show_embed]

    # Create a dictionary for the combined message
    data = {
        "embeds": combined_embeds
    }
    return data