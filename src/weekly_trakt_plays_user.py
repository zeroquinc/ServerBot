from calendar import weekday
import discord
import requests
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

def create_weekly_embed():
    # Determine the path to the parent directory (one level up from the current script's location)
    parent_directory = os.path.dirname(os.path.dirname(__file__))
    env_file_path = os.path.join(parent_directory, '.env')

    # Load the .env file from the parent directory
    load_dotenv(env_file_path)

    # Access the environment variables from the .env file
    trakt_client_id = os.getenv("TRAKT_CLIENT_ID")
    trakt_client_secret = os.getenv("TRAKT_CLIENT_SECRET")
    tmdb_api_key = os.getenv("TMDB_API_KEY")
    trakt_username = os.getenv("TRAKT_USERNAME")

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
        "trakt-api-key": trakt_client_id
    }

    # Fetch all user's history from Trakt API for the last 7 days (with pagination)
    page = 1
    all_history_data = []

    while True:
        history_url = f"https://api.trakt.tv/users/{trakt_username}/history"
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
    movies_embed.url = f"https://trakt.tv/users/desiler/history/movies/added?start_at={start_date_str}&end_at={end_date_str}"

    # Set the author name
    movies_embed.set_author(name=f"Movies watched by Desiler in Week {week_number}")

    # Add timestamp with date range to the embed
    timestamp_start = start_date.strftime('%a %b %d %Y')
    timestamp_end = end_date.strftime('%a %b %d %Y')
    timestamp = f"{timestamp_start} to {timestamp_end}"
    movies_embed.timestamp = datetime.now()
    movies_embed.set_footer(text=timestamp)

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
                    "api_key": tmdb_api_key,
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
    episodes_embed.url = f"https://trakt.tv/users/desiler/history/episodes/added?start_at={start_date_str}&end_at={end_date_str}"

    # Set the author name
    episodes_embed.set_author(name=f"Episodes watched by Desiler in Week {week_number}")

    # Add timestamp with date range to the embed
    episodes_embed.timestamp = datetime.now()
    episodes_embed.set_footer(text=timestamp)

    # Check if there are episodes found
    if total_episode_count > 0:
        # Add the episode information as fields
        for show_title, data in episode_counts.items():
            episode_count = data['count']
            year = data['year']

            # Search for the show by title
            search_url = "https://api.themoviedb.org/3/search/tv"
            search_params = {
                "api_key": tmdb_api_key,
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