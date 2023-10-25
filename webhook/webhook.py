from flask import Flask, request, jsonify
import os
import json
import logging

app = Flask(__name__)
app.debug = True

script_directory = os.path.dirname(os.path.abspath(__file__))

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        if data and 'embeds' in data:
            embeds = data['embeds']
            for i, embed in enumerate(embeds):
                author_name = embed['author']['name']
                if "has resumed playing" in author_name:
                    filename = os.path.join(script_directory, 'plex_resuming.json')
                elif "has finished playing" in author_name:
                    filename = os.path.join(script_directory, 'plex_finished.json')
                elif "has started playing" in author_name:
                    filename = os.path.join(script_directory, 'plex_started.json')
                else:
                    filename = os.path.join(script_directory, f'event_{i}.json')

                with open(filename, 'w') as f:
                    f.write(json.dumps(embed, indent=4))
                app.logger.info(f"Event saved as {filename}")
            return "Webhook received and events saved successfully!", 200
        else:
            app.logger.info("Webhook received, but no events found.")
            return "Webhook received, but no events found.", 200
    except Exception as e:
        app.logger.error(f"Error while processing JSON payload: {str(e)}")
        return "Internal server error", 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=1337)