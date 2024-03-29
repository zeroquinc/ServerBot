import requests
import discord
from discord.utils import utcnow
from datetime import datetime, timedelta
import collections
import time
from dateutil.parser import parse

from .globals import (
    DISCORD_THUMBNAIL,
    RETRO_USERNAME,
    RETRO_API_KEY,
    RETRO_TARGET_USERNAMES,
    RETRO_TIMEFRAME
)

from .custom_logger import logger

'''
Start of utility functions
'''

# Function to create human friendly date strings
def ordinal(n):
    return str(n) + ('th' if 4<=n%100<=20 else {1:'st',2:'nd',3:'rd'}.get(n%10, 'th'))

# Function to get the color based on the username
def get_color(username):
    if username == 'Desiler':
        return discord.Color.red()
    elif username == 'Lipperdie':
        return discord.Color.blue()
    else:
        return discord.Color.green()

# Function to set the footer text and image based on the username    
def set_footer(embed, username, text):
    if username == 'Desiler':
        embed.set_footer(text=text, icon_url='https://i.imgur.com/mJvWGe1.png')
    elif username == 'Lipperdie':
        embed.set_footer(text=text, icon_url='https://i.imgur.com/TA9LKKW.png')
    else:
        embed.set_footer(text=text)

'''
Start of functions to fetch data from the RetroAchievements API
'''

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

# Fetch daily overview for a user
def create_daily_overview(username):
    logger.debug(f"Fetching daily overview for {username}")
    now = int(time.time())
    yesterday = now - 24*60*60
    url = f"https://retroachievements.org/API/API_GetAchievementsEarnedBetween.php?u={username}"
    params = {'z': RETRO_USERNAME, 'y': RETRO_API_KEY, 'f': yesterday, 't': now}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        achievements = response.json()
        daily_points = 0
        max_points = 0
        max_achievement = None
        for achievement in achievements:
            points = achievement['Points']
            daily_points += points
            if points > max_points:
                max_points = points
                max_achievement = achievement
        logger.debug(f"Daily points: {daily_points}")
        
        # Fetch user profile
        total_points, total_retropoints = get_user_profile(username)
        if total_points is not None and total_retropoints is not None:
            embed = create_daily_overview_embed(username, daily_points, total_points, total_retropoints, achievements, max_achievement)
            logger.debug(f"Embed created: {embed.to_dict()}")
            return embed
    else:
        logger.error(f"Error fetching daily overview: {response.status_code}")
        return None

# Fetch Total Points and Total True Points for a user
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

# Function to fetch the number of hardcore completions for a user
def fetch_completed_games(username):
    url = 'https://retroachievements.org/API/API_GetUserCompletionProgress.php'
    params = {'z': RETRO_USERNAME, 'y': RETRO_API_KEY, 'u': username}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        completion_progress = response.json()
        logger.debug(f'Completion Progress: {completion_progress}')
        mastered_games = sum(1 for game in completion_progress['Results'] if game['NumAwardedHardcore'] == game['MaxPossible'] or game['HighestAwardKind'] == 'mastered')
        return mastered_games
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
    
def fetch_game_data(game_id):
    url = "https://retroachievements.org/API/API_GetGameExtended.php"
    params = {'z': RETRO_USERNAME, 'y': RETRO_API_KEY, 'i': game_id}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        logger.debug(f'Error: {response.status_code}')
        return None
    
# Function to check if a game has been completed
def check_game_completion(username, completion, achievement):
    game_id = achievement['GameID']
    if game_id in completion:
        game_details = completion[game_id]
        num_awarded = int(game_details['NumAwarded'])
        max_possible = int(game_details['MaxPossible'])
        highest_award_date = game_details['HighestAwardDate']
        if num_awarded == max_possible:
            completed_games_count = fetch_completed_games(username)
            game_data = fetch_game_data(game_id)
            if game_data is not None:
                points_earned = game_data['points_total']
            achievements_earned = max_possible
            return create_embed_if_game_completed(username, completed_games_count, game_id, achievement, highest_award_date, achievements_earned, points_earned)
    return None

'''
Start of functions to create embed messages
'''

# Function to create an embed message for a daily overview
def create_daily_overview_embed(username, daily_points, total_points, total_retropoints, achievements, max_achievement):
    color = get_color(username)

    # The timestamp is set to the previous day
    yesterday = datetime.now() - timedelta(days=1)
    timestamp = f"{ordinal(yesterday.day)} of {yesterday.strftime('%B, %Y')}"

    embed = discord.Embed(
        description=f"{username} has earned {daily_points} points on the {timestamp}.",
        color=color
    )
    embed.set_author(name=f"Daily Overview for {username}", icon_url="https://i.imgur.com/P0nEGGs.png")
    embed.set_image(url=DISCORD_THUMBNAIL)

    # Set the thumbnail to the BadgeURL of the max_achievement
    if max_achievement is not None:
        embed.set_thumbnail(url=f"https://media.retroachievements.org{max_achievement['BadgeURL']}")

    # Set the footer text and image based on the username
    footer_text = f"Total Points: {total_points} | Total RetroPoints: {total_retropoints}"
    set_footer(embed, username, footer_text)

    # Add the best achievement only if there are achievements
    if max_achievement is not None:
        achievement_url = f"https://retroachievements.org/Achievement/{max_achievement['AchievementID']}"
        embed.add_field(name="Best Achievement Earned", 
                        value=f"[{max_achievement['Title']}]({achievement_url}) ({max_achievement['Points']})", 
                        inline=True)
        
    # Add the count of achievements earned only if there are achievements
    if achievements:
        embed.add_field(name="Achievements Earned", value=len(achievements), inline=True)

    return embed

# Function to create an embed message for a new achievement
def create_embed(achievement, completion_cache, new_achievements_count, username):
    color = get_color(username)

    embed = discord.Embed(
        title=achievement['GameTitle'],
        color=color
    )
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
    footer_text = f"Earned on {friendly_date}"
    set_footer(embed, username, footer_text)

    return embed

# Function to create an embed message for a completed game
def create_embed_if_game_completed(username, completed_games_count, game_id, achievement, highest_award_date, achievements_earned, points_earned):
    if completed_games_count is not None:
        if highest_award_date:
            highest_award_date = parse(highest_award_date)
            highest_award_date = "Mastered on the {} of {} at {}".format(ordinal(highest_award_date.day), highest_award_date.strftime("%B %Y"), highest_award_date.strftime("%H:%M"))
        else:
            highest_award_date = "Date not available"

        embed = discord.Embed(
            description=f"{username}'s {completed_games_count}th mastery! Congratulations!",
            color=discord.Color.gold()
        )
        embed.url = f"https://retroachievements.org/game/{game_id}"
        embed.set_author(name=f"Mastered by {username}", icon_url="https://i.imgur.com/fFBx91U.png")
        embed.set_image(url=DISCORD_THUMBNAIL)
        embed.set_thumbnail(url=f"https://media.retroachievements.org{achievement['GameIcon']}")

        # Add the game title as a field
        embed.add_field(name="Game Mastered", value=achievement['GameTitle'], inline=False)

        # Add the Achievements earned as a field
        embed.add_field(name="Achievements Earned", value=str(achievements_earned), inline=False)

        # Add the points earned as a field
        embed.add_field(name="Points Earned", value=str(points_earned), inline=False)
        
        # Set the footer text and image based on the username
        footer_text = highest_award_date
        set_footer(embed, username, footer_text)

        return embed
    return None