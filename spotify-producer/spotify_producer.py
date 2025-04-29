import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
from dotenv import load_dotenv
import time
from kafka import KafkaProducer
import json

# Load environment variables
load_dotenv()

# Spotify authentication (Client Credentials Flow)
client_id = os.getenv('SPOTIPY_CLIENT_ID')
client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
if not client_id or not client_secret:
    raise ValueError("Spotify credentials not found in environment variables.")

auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(auth_manager=auth_manager)

# Kafka configuration
kafka_broker_raw = os.getenv('KAFKA_BROKER_URL', 'kafka:29092')
kafka_broker = kafka_broker_raw.split('#')[0].strip()
topic_name = 'spotify_events'

producer = KafkaProducer(
    bootstrap_servers=[kafka_broker],
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    api_version=(3, 7, 0),
    retries=5,  # Add retries
    request_timeout_ms=15000  # Increase timeout
)

def fetch_and_produce_track(track_name):
    """Searches for a public track and sends its data to Kafka."""
    try:
        results = sp.search(q=f'track:{track_name}', type='track', limit=1)
        if not results['tracks']['items']:
            print(f"No results found for '{track_name}'")
            return

        track = results['tracks']['items'][0]
        data = {
            'track_id': track['id'],
            'track_name': track['name'],
            'artist': track['artists'][0]['name'],
            'album': track['album']['name'],
            'duration_ms': track['duration_ms'],
            'spotify_url': track['external_urls']['spotify'],
            'timestamp': int(time.time() * 1000)
        }

        producer.send(topic_name, value=data)
        producer.flush()
        print(f"Produced to Kafka: {data['track_name']} by {data['artist']}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    # Example: periodically search for a track and produce to Kafka
    TRACK_TO_SEARCH = 'Bohemian Rhapsody'
    while True:
        fetch_and_produce_track(TRACK_TO_SEARCH)
        time.sleep(30)  # Wait 30 seconds before next search/produce
