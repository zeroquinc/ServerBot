from discord import Embed
import json

def sonarr_embed(data):
    event_type = data.get('eventType', 'Unknown')
    embed = Embed(
        title=f"Sonarr - {event_type}",
        description=data['series']['path'],
        color=0x0099ff
    )

    # Add episode information
    for episode in data['episodes']:
        embed.add_field(
            name=f"Episode {episode['episodeNumber']} - {episode['title']}",
            value=episode['overview'],
            inline=False
        )

    # Add episode file information
    episode_file = data['episodeFile']
    embed.add_field(name="Episode File", value=episode_file['relativePath'], inline=False)

    # Add download information
    embed.add_field(name="Download Client", value=data['downloadClient'], inline=True)
    embed.add_field(name="Download ID", value=data['downloadId'], inline=True)

    # Add custom format information
    custom_formats = ", ".join([cf['name'] for cf in data['customFormatInfo']['customFormats']])
    embed.add_field(name="Custom Formats", value=custom_formats, inline=False)

    # Save the embed as JSON
    json_data = {
        "title": embed.title,
        "description": embed.description,
        "color": embed.color.value,
        "fields": [{"name": field.name, "value": field.value, "inline": field.inline} for field in embed.fields]
    }

    with open(f'json/sonarr/sonarr_{event_type}.json', 'w') as json_file:
        json.dump(json_data, json_file, indent=4)