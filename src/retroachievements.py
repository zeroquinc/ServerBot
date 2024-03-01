import requests
import discord
from discord.utils import utcnow
from datetime import datetime, timedelta
import collections
import time

from .globals import (
    DISCORD_THUMBNAIL,
    RETRO_USERNAME,
    RETRO_API_KEY,
    RETRO_TARGET_USERNAMES,
    RETRO_TIMEFRAME
)

from .custom_logger import logger

from datetime import datetime

def ordinal(n):
    return str(n) + ('th' if 4<=n%100<=20 else {1:'st',2:'nd',3:'rd'}.get(n%10, 'th'))

def create_daily_overview_embed(username, total_points, cumul_score):
    embed = discord.Embed(
        description=f"{username} earned {total_points} points and {cumul_score} RetroPoints in the last 24 hours.",
        color=discord.Color.blue()
    )
    embed.set_author(name=f"Daily Overview for {username}", icon_url="https://i.imgur.com/P0nEGGs.png")
    # The timestamp is set to the current date
    now = datetime.now()
    timestamp = f"{ordinal(now.day)} of {now.strftime('%B %Y')}"
    embed.set_image(url=DISCORD_THUMBNAIL)
    # Set the footer text and image based on the username
    if username == 'Desiler':
        embed.set_footer(text=timestamp, icon_url='https://i.imgur.com/mJvWGe1.png')
    elif username == 'Lipperdie':
        embed.set_footer(text=timestamp, icon_url='https://i.imgur.com/TA9LKKW.png')
    else:
        embed.set_footer(text=timestamp, icon_url=None)
    return embed

def get_user_profile(username):
    url = f"https://retroachievements.org/API/API_GetUserProfile.php?u={username}"
    params = {'z': RETRO_USERNAME, 'y': RETRO_API_KEY}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        user_profile = response.json()
        total_points = user_profile['TotalPoints']
        total_true_points = user_profile['TotalTruePoints']
        return total_points, total_true_points
    else:
        logger.error(f"Error fetching user profile: {response.status_code}")
        return None, None

def create_daily_overview(username):
    logger.debug(f"Fetching daily overview for {username}")
    now = int(time.time())
    yesterday = now - 24*60*60
    url = f"https://retroachievements.org/API/API_GetAchievementsEarnedBetween.php?u={username}"
    params = {'z': RETRO_USERNAME, 'y': RETRO_API_KEY, 'f': yesterday, 't': now}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        achievements = response.json()
        total_points = 0
        cumul_score = 0
        max_points = 0
        max_achievement = None
        for achievement in achievements:
            points = achievement['Points']
            total_points += points
            cumul_score += achievement['CumulScore']
            if points > max_points:
                max_points = points
                max_achievement = achievement
        logger.debug(f"Total points: {total_points}, Cumulative score: {cumul_score}")
        embed = create_daily_overview_embed(username, total_points, cumul_score)
        if max_achievement is not None:
            achievement_url = f"https://retroachievements.org/Achievement/{max_achievement['AchievementID']}"
            embed.add_field(name="Best Achievement in the last 24h", value=f"[{max_achievement['Title']}]({achievement_url}) with {max_points} points", inline=False)
        
        # Fetch user profile
        total_points, total_true_points = get_user_profile(username)
        if total_points is not None and total_true_points is not None:
            embed.add_field(name="Total Points Overall", value=total_points, inline=True)
            embed.add_field(name="Total RetroPoints Overall", value=total_true_points, inline=True)
        
        logger.debug(f"Embed created: {embed.to_dict()}")
        return embed
    else:
        logger.error(f"Error fetching daily overview: {response.status_code}")
        return None

# Main function to fetch the recent achievements for all target usernames
def fetch_recent_achievements(completion_cache, username):
    data = fetch_data(username)
    if data is not None:
        new_achievements_count = collections.defaultdict(int)
        embeds = []
        game_completion_checked = set()
        for achievement in data:
            game_id = achievement['GameID']
            if username not in completion_cache:
                completion_cache[username] = {}
            if game_id not in completion_cache[username]:
                completion_cache[username][game_id] = fetch_completion(username)
            embed = create_embed(achievement, completion_cache[username][game_id], new_achievements_count[game_id], username)
            new_achievements_count[game_id] += 1

            # Add the achievement embed
            achievement_time = datetime.strptime(achievement['Date'], '%Y-%m-%d %H:%M:%S')
            embeds.append((achievement_time, embed))

            # Check if the game is completed, but only if it hasn't been checked before
            if game_id not in game_completion_checked:
                completion_embed = check_game_completion(username, completion_cache[username][game_id], achievement)
                if completion_embed is not None:
                    # Add a small delay to the completion time to ensure it's always after the last achievement
                    completion_time = achievement_time + timedelta(seconds=1)
                    embeds.append((completion_time, completion_embed))
                game_completion_checked.add(game_id)

        embeds.sort(key=lambda x: x[0])
        return [embed.to_dict() for _, embed in embeds]
    else:
        return None

# Function to fetch the number of hardcore completions for a user
def fetch_completed_games(username):
    url = 'https://retroachievements.org/API/API_GetUserCompletedGames.php'
    params = {'z': RETRO_USERNAME, 'y': RETRO_API_KEY, 'u': username}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        completed_games = response.json()
        logger.debug(f'Completed games: {completed_games}')
        hardcore_completions = sum(1 for game in completed_games if game['HardcoreMode'] == '1' and game['PctWon'] == '1.0000')
        return hardcore_completions
    else:
        logger.debug(f'Error: {response.status_code}')
        return None

# Function to fetch the completion status of a user for a specific game
def fetch_completion(username):
    url = 'https://retroachievements.org/API/API_GetUserCompletionProgress.php'
    params = {'z': RETRO_USERNAME, 'y': RETRO_API_KEY, 'u': username}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return {game['GameID']: game for game in response.json()['Results']}
    else:
        logger.debug(f'Error: {response.status_code}')
        return None

# Function to fetch the recent achievements for a user
def fetch_data(username):
    url = 'https://retroachievements.org/API/API_GetUserRecentAchievements.php'
    params = {'z': RETRO_USERNAME, 'y': RETRO_API_KEY, 'u': username, 'm': RETRO_TIMEFRAME}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        logger.debug(f'Data fetched successfully: {response.json()}')
        return response.json()
    else:
        logger.debug(f'Error: {response.status_code}')
        return None

# Function to create an embed message for a new achievement
def create_embed(achievement, completion_cache, new_achievements_count, username):
    embed = discord.Embed(
        title=achievement['GameTitle'],
        color=discord.Color.blue()
    )
    #timestamp = utcnow()
    #embed.timestamp = timestamp
    embed.url = f"https://retroachievements.org/game/{achievement['GameID']}"
    embed.set_author(name="Achievement Unlocked", icon_url=f"https://media.retroachievements.org{achievement['GameIcon']}")

    # Check if the achievement type is "Missable"
    suffix = " (m)" if achievement['Type'] == 'missable' else ""
    # Add the achievement link to the embed
    achievement_link = f"[{achievement['Title']}](https://retroachievements.org/achievement/{achievement['AchievementID']})"
    embed.add_field(name="Achievement", value=f"{achievement_link}{suffix}", inline=True)

    embed.add_field(name="Points", value=achievement['Points'], inline=True)

    # Hardcore mode is a boolean, so we need to convert it to a string
    hardcore_value = "Yes" if achievement['HardcoreMode'] == 1 else "No"
    embed.add_field(name="Hardcore", value=hardcore_value, inline=True)

    embed.add_field(name="Description", value=f"```{achievement['Description']}```", inline=False)

    # Fetch the completion status of the game
    completion = completion_cache.get(achievement['GameID'])
    if completion is not None:
        num_awarded = int(completion['NumAwarded']) - new_achievements_count
        max_possible = int(completion['MaxPossible'])
        percentage = (num_awarded / max_possible) * 100
        embed.add_field(name="Set Completion", value=f"```{num_awarded}/{max_possible} ({percentage:.2f}%)```", inline=False)

    # Convert the date to a more friendly format
    date = datetime.strptime(achievement['Date'], '%Y-%m-%d %H:%M:%S')
    friendly_date = date.strftime('%d/%m/%Y at %H:%M:%S')

    embed.add_field(name="User", value=f"[{username}](https://retroachievements.org/user/{username})", inline=True)
    embed.add_field(name="Console", value=achievement['ConsoleName'], inline=True)

    embed.set_image(url=DISCORD_THUMBNAIL)
    embed.set_thumbnail(url=f"https://media.retroachievements.org{achievement['BadgeURL']}")

    # Set the footer text and image based on the username
    if username == 'Desiler':
        embed.set_footer(text=f"Earned on {friendly_date}", icon_url='https://i.imgur.com/mJvWGe1.png')
    elif username == 'Lipperdie':
        embed.set_footer(text=f"Earned on {friendly_date}", icon_url='https://i.imgur.com/TA9LKKW.png')
    else:
        embed.set_footer(text=f"Earned on {friendly_date}")

    return embed

# Function to create an embed message for a completed game
def create_embed_if_game_completed(username, completed_games_count, game_id, achievement):
    if completed_games_count is not None:
        # Create a new embed message for the completed game
        embed = discord.Embed(
            description=f"This is {username}'s {completed_games_count}th mastery! :trophy:",
            color=discord.Color.gold()
        )
        embed.url = f"https://retroachievements.org/game/{game_id}"
        embed.set_author(name=f"Mastered {achievement['GameTitle']}", icon_url=f"https://media.retroachievements.org{achievement['GameIcon']}")
        embed.set_image(url=DISCORD_THUMBNAIL)
        embed.set_thumbnail(url=f"https://i.imgur.com/rXH9hOd.png")
        # Set the footer text and image based on the username
        if username == 'Desiler':
            embed.set_footer(text=f"Congratulations!", icon_url='https://i.imgur.com/mJvWGe1.png')
        elif username == 'Lipperdie':
            embed.set_footer(text=f"Congratulations!", icon_url='https://i.imgur.com/TA9LKKW.png')
        else:
            embed.set_footer(text=f"Congratulations!")
        return embed
    return None

# Function to check if a game has been completed
def check_game_completion(username, completion, achievement):
    game_id = achievement['GameID']
    if game_id in completion:
        game_details = completion[game_id]
        num_awarded = int(game_details['NumAwarded'])
        max_possible = int(game_details['MaxPossible'])
        if num_awarded == max_possible:
            completed_games_count = fetch_completed_games(username)
            return create_embed_if_game_completed(username, completed_games_count, game_id, achievement)
    return None