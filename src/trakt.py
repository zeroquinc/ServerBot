from calendar import weekday
import discord
import requests
import json
from datetime import datetime, timedelta

from src.globals import load_dotenv, TRAKT_CLIENT_ID, TMDB_API_KEY, TRAKT_USERNAME

def create_weekly_user_embed():
    # Calculate the date range for the last 7 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    # Calculate the week number and year for the previous week
    previous_week = end_date - timedelta(days=7)
    week_number = previous_week.isocalendar()[1]
    year = previous_week.isocalendar()[0]

    # Convert dates to ISO 8601 format
    start_date_str = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    end_date_str = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')

    # Set up headers for API requests
    headers = {
        "Content-Type": "application/json",
        "trakt-api-version": "2",
        "trakt-api-key": TRAKT_CLIENT_ID
    }

    # Fetch all user's history from Trakt API for the last 7 days (with pagination)
    page = 1
    all_history_data = []

    while True:
        history_url = f"https://api.trakt.tv/users/{TRAKT_USERNAME}/history"
        params = {
            "start_at": start_date_str,
            "end_at": end_date_str,
            "page": page,
            "limit": 100  # Maximum items per page
        }

        history_response = requests.get(history_url, headers=headers, params=params)
        history_data = json.loads(history_response.text)

        if not history_data:
            break

        all_history_data.extend(history_data)
        page += 1
        

    # Sort all history data by watched_at in ascending order
    sorted_history_data = sorted(all_history_data, key=lambda x: x['watched_at'])

    # Process each item in the sorted history data
    movie_count = 0

    # Process each item in the sorted history data
    for item in sorted_history_data:
        if item['type'] == 'movie':
            movie_count += 1

    # Create embedded message for Movies
    movies_embed = discord.Embed(
        title=f"{movie_count} Movie{'s' if movie_count != 1 else ''} :clapper:", 
        color=0xFEA232
    )
    movies_embed.url = f"https://trakt.tv/users/{TRAKT_USERNAME}/history/movies/added?start_at={start_date_str}&end_at={end_date_str}"

# Set the author name and icon URL
    movies_embed.set_author(
        name=f"Trakt - Movies watched by {TRAKT_USERNAME} in Week {week_number}",
        icon_url='https://i.imgur.com/tvnkxAY.png'
    )

    # Add timestamp with date range to the embed
    timestamp_start = start_date.strftime('%a %b %d %Y')
    timestamp_end = end_date.strftime('%a %b %d %Y')
    timestamp = f"{timestamp_start} to {timestamp_end}"
    movies_embed.timestamp = datetime.now()
    movies_embed.set_footer(text=timestamp)
    
    movies_embed.set_image(url='https://imgur.com/a/D3MxSNM')

    # Check if there are movies found
    if movie_count > 0:
        # Add the movie information as fields
        for item in sorted_history_data:
            if item['type'] == 'movie':
                # Get the movie title and year
                movie_title = item['movie']['title']
                year = item['movie']['year'] if item['movie'].get('year') else ""

                # Get the date when it was watched
                watched_date = datetime.strptime(item['watched_at'], '%Y-%m-%dT%H:%M:%S.%fZ')

                # Search for the movie by title
                search_url = "https://api.themoviedb.org/3/search/multi"
                search_params = {
                    "api_key": TMDB_API_KEY,
                    "query": movie_title
                }
                search_response = requests.get(search_url, params=search_params)
                search_data = json.loads(search_response.text)

                # Get the poster URL if available
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
        # Add a description when no movies are found
        movies_embed.description = "No movies watched this week."

    # Create a dictionary to store the episode count for each show and its corresponding year
    episode_counts = {}

    # Process each item in the sorted history data for episodes
    for item in sorted_history_data:
        if item['type'] == 'episode':
            # Get the show title
            show_title = item['show']['title']
            year = item['show']['year'] if item['show'].get('year') else ""

            # Increment the episode count for the show
            episode_counts[show_title] = {
                'count': episode_counts.get(show_title, {}).get('count', 0) + 1,
                'year': year
            }

    # Calculate the total episode count
    total_episode_count = sum(item['count'] for item in episode_counts.values())

    # Create embedded message for Episodes with the total episode count in the title
    episodes_embed = discord.Embed(
        title=f"{total_episode_count} Episode{'s' if total_episode_count != 1 else ''} :tv:",
        color=0x328efe
    )
    episodes_embed.url = f"https://trakt.tv/users/{TRAKT_USERNAME}/history/episodes/added?start_at={start_date_str}&end_at={end_date_str}"

    # Set the author name and icon URL
    episodes_embed.set_author(
        name=f"Trakt - Episodes watched by {TRAKT_USERNAME} in Week {week_number}",
        icon_url='https://i.imgur.com/tvnkxAY.png'
    )

    # Add timestamp with date range to the embed
    episodes_embed.timestamp = datetime.now()
    episodes_embed.set_footer(text=timestamp)
    
    episodes_embed.set_image(url='https://imgur.com/a/D3MxSNM')

    # Check if there are episodes found
    if total_episode_count > 0:
        # Add the episode information as fields
        for show_title, data in episode_counts.items():
            episode_count = data['count']
            year = data['year']

            # Search for the show by title
            search_url = "https://api.themoviedb.org/3/search/tv"
            search_params = {
                "api_key": TMDB_API_KEY,
                "query": show_title
            }
            search_response = requests.get(search_url, params=search_params)
            search_data = json.loads(search_response.text)

            # Get the poster URL if available
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
        # Add a description when no episodes are found
        episodes_embed.description = "No episodes watched this week."

    # Sort the movie fields alphabetically by name
    sorted_movie_fields = sorted(movies_embed.fields, key=lambda field: field.name)

    # Clear the existing fields in the movies_embed
    movies_embed.clear_fields()

    # Add the sorted movie fields back to the movies_embed
    for field in sorted_movie_fields:
        movies_embed.add_field(name=field.name, value=field.value, inline=field.inline)

    # Sort the episode fields by the number of episodes watched (in descending order)
    sorted_episode_fields = sorted(episodes_embed.fields, key=lambda field: int(field.value.split()[0]), reverse=True)

    # Clear the existing fields in the episodes_embed
    episodes_embed.clear_fields()

    # Add the sorted episode fields back to the episodes_embed
    for field in sorted_episode_fields:
        episodes_embed.add_field(name=field.name, value=field.value, inline=field.inline)

    # Send the content message
    data = {
        'embeds': [movies_embed.to_dict(), episodes_embed.to_dict()]
    }
    return data

def create_weekly_global_embed(): 
    # Trakt API endpoints
    movie_url = 'https://api.trakt.tv/movies/watched/period=weekly'
    show_url = 'https://api.trakt.tv/shows/watched/period=weekly'

    # Trakt API headers
    headers = {
        'Content-Type': 'application/json',
        'trakt-api-version': '2',
        "trakt-api-key": TRAKT_CLIENT_ID
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
            "name": f"Trakt - Top Movies in Week {iso_week}",
            "icon_url": "https://i.imgur.com/tvnkxAY.png"
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
            "name": f"Trakt - Top Shows in Week {iso_week}",
            "icon_url": "https://i.imgur.com/tvnkxAY.png"
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