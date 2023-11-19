# Discord.py Bot

This is a Discord.py bot created for learning Python and for fun.

## Purpose

- Learning Python
- Use it myself for my Media Server
- Enjoy building a Discord bot

## Usage

- Make a .env and fill in these variables and save it in the root folder

```
# Discord Configuration
DISCORD_SERVER_ID =
DISCORD_TOKEN =

# Test Discord Token
DISCORD_TOKEN_TEST =

# Trakt API Configuration
TRAKT_CLIENT_ID =
TRAKT_CLIENT_SECRET =
TRAKT_USERNAME =

# The Movie Database (TMDb) API Key
TMDB_API_KEY =

# Tautulli Configuration
TAUTULLI_API_URL =
TAUTULLI_API_KEY =
TAUTULLI_USER_ID =
TAUTULLI_SCRIPTS_FOLDER =

# Discord Channel IDs
CHANNEL_PLEX_CONTENT =
CHANNEL_PLEX_PLAYING =
CHANNEL_RADARR_GRABS =
CHANNEL_SONARR_GRABS =
```

Make a bash script like this and then run the file

```
#!/bin/bash
set -e
cd /path/to/folder
source venv/bin/activate
python3 main.py & 
wait
```

## Contact

If you have any questions or suggestions, feel free to contact me
