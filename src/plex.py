import src.logging

logger = src.logging.logging.getLogger("plex")

def create_plex_embed(data):
    try:
        embeds_list = []
        if data and 'embeds' in data:
            embeds = data['embeds']
            for embed in embeds:
                embeds_list.append(embed)
                logger.info(f"Created embed for {embed['title']} event")
            return {'embeds': embeds_list}, 200
        else:
            logger.info("Webhook received, but no events found. Data not saved.")
            return {'message': "Webhook received, but no events found. Data not saved."}, 200
    except Exception as e:
        logger.error(f"Error while processing JSON payload: {str(e)}")
        return {'error': "Internal server error"}, 500