from flask import Flask, request, jsonify

from src.plex import setup_directories, handle_webhook_data

from src.sonarr import setup_directories, dump_embed_to_json

app = Flask(__name__)

@app.route('/plex', methods=['POST'])
def plex_webhook():
    script_directory, content_directory, playing_directory = setup_directories()
    try:
        data = request.get_json()
        response, status_code = handle_webhook_data(data, script_directory, content_directory, playing_directory)
        return response, status_code
    except Exception as e:
        print(f"Error in webhook route: {str(e)}")
        return "Internal server error", 500
    
@app.route('/sonarr', methods=['POST'])
def sonarr_webhook():
    script_directory, sonarr_directory = setup_directories()
    try:
        data = request.get_json()
        response, status_code = dump_embed_to_json(data, script_directory, sonarr_directory)
        return response, status_code
    except Exception as e:
        print(f"Error in webhook route: {str(e)}")
        return "Internal server error", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1337, debug=True)