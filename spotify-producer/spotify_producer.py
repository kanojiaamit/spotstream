import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
from dotenv import load_dotenv
import time
from kafka import KafkaProducer
import json
import logging
import sys
from kafka.errors import KafkaError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Spotify authentication (Client Credentials Flow)
client_id = os.getenv('SPOTIPY_CLIENT_ID')
client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
if not client_id or not client_secret:
    logger.error("Spotify credentials not found in environment variables.")
    raise ValueError("Spotify credentials not found in environment variables.")

logger.info("Initializing Spotify client...")
auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(auth_manager=auth_manager)

# Kafka configuration
kafka_broker = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
topic_name = 'spotify_events'

logger.info("Connecting to Kafka broker at %s...", kafka_broker)
retries = 0
max_retries = 5
retry_interval = 5

while retries < max_retries:
    try:
        producer = KafkaProducer(
            bootstrap_servers=[kafka_broker],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            api_version=(3, 7),
            retries=5,
            request_timeout_ms=30000,
            max_block_ms=20000,
            security_protocol='PLAINTEXT',
            client_id='spotify-producer',
            connections_max_idle_ms=60000,
            metadata_max_age_ms=300000,
            reconnect_backoff_ms=1000,
            reconnect_backoff_max_ms=10000
        )
        # Test the connection
        producer.bootstrap_connected()
        logger.info("Successfully connected to Kafka")
        break
    except KafkaError as e:
        retries += 1
        if retries < max_retries:
            logger.warning("Failed to connect to Kafka (attempt %d/%d): %s. Retrying in %d seconds...",
                         retries, max_retries, str(e), retry_interval)
            time.sleep(retry_interval)
        else:
            logger.error("Failed to connect to Kafka after %d attempts: %s",
                        max_retries, str(e))
            raise

def fetch_and_produce_track(track_name):
    """Searches for a public track and sends its data to Kafka."""
    try:
        logger.info("Searching for track: %s", track_name)
        results = sp.search(q=f'track:{track_name}', type='track', limit=1)
        if not results['tracks']['items']:
            logger.warning("No results found for '%s'", track_name)
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

        logger.info("Sending track data to Kafka: %s by %s", data['track_name'], data['artist'])
        future = producer.send(topic_name, value=data)
        record_metadata = future.get(timeout=10)
        logger.info("Successfully sent to Kafka - Topic: %s, Partition: %s, Offset: %s",
                   record_metadata.topic, record_metadata.partition, record_metadata.offset)
        producer.flush()
    except Exception as e:
        logger.error("Error in fetch_and_produce_track: %s", str(e), exc_info=True)

if __name__ == '__main__':
    logger.info("Starting Spotify Producer...")
    TRACK_TO_SEARCH = 'Bohemian Rhapsody'
    
    try:
        while True:
            fetch_and_produce_track(TRACK_TO_SEARCH)
            time.sleep(15)  # Wait 15 seconds before next search/produce
    except KeyboardInterrupt:
        logger.info("Shutting down producer...")
        producer.close()
        logger.info("Producer closed successfully")
    except Exception as e:
        logger.error("Fatal error: %s", str(e), exc_info=True)
        producer.close()
        raise
