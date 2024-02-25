from discord import Embed

def split_embeds(embeds):
    # Split the embeds into groups of 10
    embed_groups = [embeds[i:i+10] for i in range(0, len(embeds), 10)]
    return embed_groups