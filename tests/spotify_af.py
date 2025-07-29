import spotipy
from spotipy.oauth2 import SpotifyOAuth

CLIENT_ID = "4a6c84249f5c45e0ae8c373f937883b6"
CLIENT_SECRET = "9ff55afc97c64ef392b9cbc0aac52f33"
REDIRECT_URI = "http://127.0.0.1:8888/callback"

SCOPE = "user-read-private playlist-read-private user-library-read playlist-modify-private"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE,
    open_browser=True
))

track_id = "11dFghVXANMlKmJXsNCbNl"
features = sp.audio_features([track_id])[0]
print(features)
