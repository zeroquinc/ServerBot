from flask import Flask, request, jsonify
import os
import json
from datetime import datetime

from sonarr import sonarr_embed

app = Flask(__name__)

script_directory = os.path.dirname(os.path.abspath(__file__))
content_directory = os.path.join(script_directory, 'json', 'content')
playing_directory = os.path.join(script_directory, 'json', 'playing')
sonarr_directory = os.path.join(script_directory, 'json', 'sonarr')

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        
        # Handle Sonarr-related events here
        if data and 'eventType' in data:
            data = sonarr_embed()
            app.logger.info(f"Event saved!")
            
            # Handle Plex-related events here
            if "author" in data:
                author_name = data['author']['name']
                if "has resumed playing" in author_name:
                    filename = os.path.join(playing_directory, 'plex_resuming.json')
                elif "has finished playing" in author_name:
                    filename = os.path.join(playing_directory, 'plex_finished.json')
                elif "has started playing" in author_name:
                    filename = os.path.join(playing_directory, 'plex_started.json')
                elif "added" in author_name:
                    filename = os.path.join(content_directory, 'plex_new_content.json')
                with open(filename, 'w') as f:
                    f.write(json.dumps(data, indent=4))
                app.logger.info(f"Plex Event saved as {filename}")
                
            return "Webhook received and events saved successfully!", 200
        else:
            # If no 'eventType' is found, save the whole data to a JSON file with the current date and time
            now = datetime.now()
            current_time = now.strftime("%Y-%m-%d_%H-%M-%S")
            filename = os.path.join(script_directory, f'no_event_type_{current_time}.json')
            with open(filename, 'w') as f:
                f.write(json.dumps(data, indent=4))
            app.logger.info(f"Webhook data saved as {filename}")
            return "Webhook received, but no eventType found. Data saved to a file.", 200
    except Exception as e:
        app.logger.error(f"Error while processing JSON payload: {str(e)}")
        return "Internal server error", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1337, debug=True)