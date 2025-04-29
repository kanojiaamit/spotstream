import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Authenticate using Client Credentials Flow
client_id = os.getenv('SPOTIPY_CLIENT_ID')
client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')

if not client_id or not client_secret:
    raise ValueError("Spotify credentials not found in environment variables.")

auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(auth_manager=auth_manager)

def get_track_details(track_name):
    """Get public track details without user authentication"""
    try:
        results = sp.search(q=f'track:{track_name}', type='track', limit=1)
        if not results['tracks']['items']:
            print(f"No results found for '{track_name}'")
            return None
            
        track = results['tracks']['items'][0]
        print(f"Track: {track['name']}")
        print(f"Artist: {track['artists'][0]['name']}")
        print(f"Album: {track['album']['name']}")
        print(f"Duration: {track['duration_ms']/1000} seconds")
        print(f"Spotify URL: {track['external_urls']['spotify']}")
        
        return track
        
    except Exception as e:
        print(f"Error: {e}")
        return None

# Example usage with public data
if __name__ == '__main__':
    get_track_details('Bohemian Rhapsody')
