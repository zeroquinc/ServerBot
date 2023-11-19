from src.logging import logger_plex

def create_plex_embed(data):
    try:
        embeds_list = []

        if data and 'embeds' in data:
            embeds = data['embeds']
            for i, embed in enumerate(embeds):
                # Your existing logic for determining the filename
                author_name = embed['author']['name']

                # Append the embed to the list
                embeds_list.append(embed)
                logger_plex.info("Event processed successfully")

            # Return the embeds list and a success status code
            return embeds_list, 200
        else:
            # If no 'embeds' are found, return a message and a success status code
            return "Webhook received, but no events found. Data not saved.", 200
    except Exception as e:
        logger_plex.error(f"Error while processing JSON payload: {str(e)}")
        # Return an error message and an internal server error status code
        return "Internal server error", 500