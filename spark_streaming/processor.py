from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StringType, IntegerType, TimestampType

# Define the schema matching your producer's output
spotify_event_schema = StructType() \
    .add("timestamp", IntegerType()) \
    .add("track_id", StringType()) \
    .add("track_name", StringType()) \
    .add("artist", StringType()) \
    .add("album", StringType()) \
    .add("duration_ms", IntegerType()) \
    .add("spotify_url", StringType())

spark = SparkSession.builder \
    .appName("SpotifyStreamProcessor") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0") \
    .getOrCreate()

kafka_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:29092") \
    .option("subscribe", "spotify_events") \
    .option("startingOffsets", "latest") \
    .load()

processed_df = kafka_df.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), spotify_event_schema).alias("data")) \
    .select("data.*")

# Output to console for debugging
query = processed_df.writeStream \
    .outputMode("append") \
    .format("console") \
    .option("truncate", "false") \
    .start()

query.awaitTermination()
