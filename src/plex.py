import src.logging

logger = src.logging.logging.getLogger("plex")

def create_plex_embed(data):
    try:
        embeds_list = []
        if data and 'embeds' in data:
            embeds = data['embeds']
            for i, embed in enumerate(embeds):
                embeds[i] = process_embed_fields(embed)
                embeds_list.append(embeds[i])
                logger.info(f"Created embed for {embeds[i]['title']} event")
            return {'embeds': embeds_list}, 200
        else:
            logger.info("Webhook received, but no events found. Data not saved.")
            return {'message': "Webhook received, but no events found. Data not saved."}, 200
    except Exception as e:
        logger.error(f"Error while processing JSON payload: {str(e)}")
        return {'error': "Internal server error"}, 500

def process_embed_fields(embed):
    if 'fields' in embed:
        for field in embed['fields']:
            process_field_name(field)
    return embed

def process_field_name(field):
    if 'name' in field and (field['name'].endswith('Now Streaming') or field['name'].endswith('Streaming Resumed')):
        if 'value' in field and field['value'].startswith('00:'):
            field['value'] = field['value'][3:]