import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

# Discord.py stuff
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!",intents=intents, activity = discord.Activity(type=discord.ActivityType.watching, name="127.0.0.1"))

# DotEnv
load_dotenv()

# Discord Globals
DISCORD_SERVER_ID = os.getenv("DISCORD_SERVER_ID")
TOKEN = os.environ["DISCORD_TOKEN"]
TEST_TOKEN = os.environ["DISCORD_TOKEN_TEST"]
allowed_roles = "Captain"

# Channel Globals
CHANNEL_PLEX_CONTENT = int(os.getenv("CHANNEL_PLEX_CONTENT"))
CHANNEL_PLEX_PLAYING = int(os.getenv("CHANNEL_PLEX_PLAYING"))
CHANNEL_RADARR_GRABS = int(os.getenv("CHANNEL_RADARR_GRABS"))
CHANNEL_SONARR_GRABS = int(os.getenv("CHANNEL_SONARR_GRABS"))

# Trakt Globals
TRAKT_USERNAME = os.getenv("TRAKT_USERNAME")
TRAKT_URL_FAVORITES = f'https://api.trakt.tv/users/{TRAKT_USERNAME}/favorites'
TRAKT_URL_RATINGS = f'https://api.trakt.tv/users/{TRAKT_USERNAME}/ratings'
TRAKT_CLIENT_ID = os.getenv("TRAKT_CLIENT_ID")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
user_link = f'[{TRAKT_USERNAME}](https://trakt.tv/users/{TRAKT_USERNAME})'

# Tautulli Globals
TAUTULLI_API_URL = os.getenv("TAUTULLI_API_URL")
TAUTULLI_API_KEY = os.getenv("TAUTULLI_API_KEY")
TAUTULLI_USER_ID = os.getenv("TAUTULLI_USER_ID")