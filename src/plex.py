from src.logging import logger_plex

def create_plex_embed(data):
    try:
        embeds_list = []
        
        if data and 'embeds' in data:
            embeds = data['embeds']
            for embed in embeds:
                embeds_list.append(embed)
                logger_plex.info("Event processed successfully")
            # Return a dictionary with 'embeds' and a success status code
            return {'embeds': embeds_list}, 200
        else:
            # If no 'embeds' are found, return a message and a success status code
            return {'message': "Webhook received, but no events found. Data not saved."}, 200
    except Exception as e:
        logger_plex.error(f"Error while processing JSON payload: {str(e)}")
        # Return a dictionary with an error message and an internal server error status code
        return {'error': "Internal server error"}, 500