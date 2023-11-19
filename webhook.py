from flask import Flask, request, jsonify

from src.plex import plex_directories, handle_webhook_data

from src.sonarr import sonarr_directories, sonarr_embed_to_json

from src.radarr import radarr_directories, radarr_embed_to_json

app = Flask(__name__)

@app.route('/plex', methods=['POST'])
def plex_webhook():
    script_directory, content_directory, playing_directory = plex_directories()
    try:
        data = request.get_json()
        response, status_code = handle_webhook_data(data, script_directory, content_directory, playing_directory)
        return response, status_code
    except Exception as e:
        print(f"Error in webhook route: {str(e)}")
        return "Internal server error", 500
    
@app.route('/sonarr', methods=['POST'])
def sonarr_webhook():
    script_directory, sonarr_directory = sonarr_directories()
    try:
        data = request.get_json()
        response, status_code = sonarr_embed_to_json(data, script_directory, sonarr_directory)
        return response, status_code
    except Exception as e:
        print(f"Error in webhook route: {str(e)}")
        return "Internal server error", 500
    
@app.route('/radarr', methods=['POST'])
def radarr_webhook():
    script_directory, radarr_directory = radarr_directories()
    try:
        data = request.get_json()
        response, status_code = radarr_embed_to_json(data, script_directory, radarr_directory)
        return response, status_code
    except Exception as e:
        print(f"Error in webhook route: {str(e)}")
        return "Internal server error", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1337, debug=True, use_reloader=False)