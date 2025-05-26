from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, to_timestamp
from pyspark.sql.types import StructType, StringType, IntegerType, TimestampType
import time

# Define the schema matching your producer's output
spotify_event_schema = StructType() \
    .add("track_id", StringType()) \
    .add("track_name", StringType()) \
    .add("artist", StringType()) \
    .add("album", StringType()) \
    .add("duration_ms", IntegerType()) \
    .add("spotify_url", StringType()) \
    .add("timestamp", IntegerType())

spark = SparkSession.builder \
   .appName("SpotifyStreamProcessor") \
   .config("spark.jars.packages",
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0," +  # Kafka connector
            "com.datastax.spark:spark-cassandra-connector_2.12:3.4.0," + # Cassandra connector
            "org.postgresql:postgresql:42.6.0"  # PostgreSQL JDBC driver
           ) \
   .config("spark.cassandra.connection.host", "cassandra") \
   .config("spark.cassandra.connection.port", "9042") \
   .config("spark.cassandra.auth.username", "cassandra") \
   .config("spark.cassandra.auth.password", "cassandra") \
   .config("spark.sql.extensions", "com.datastax.spark.connector.CassandraSparkExtensions") \
   .config("spark.driver.extraClassPath", "/opt/bitnami/spark/jars/postgresql-42.6.0.jar") \
   .config("spark.streaming.stopGracefullyOnShutdown", "true") \
   .getOrCreate()

# Register PostgreSQL JDBC driver
spark.sparkContext._jvm.Class.forName("org.postgresql.Driver")

# Read from Kafka
kafka_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "spotify_events") \
    .option("startingOffsets", "latest") \
    .option("failOnDataLoss", "false") \
    .load()

# Process the data
processed_df = kafka_df.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), spotify_event_schema).alias("data")) \
    .select("data.*") \
    .withColumn("timestamp", to_timestamp(col("timestamp")))

# Write to Cassandra with error handling
def write_to_cassandra(df, epoch_id):
    try:
        df.write \
            .format("org.apache.spark.sql.cassandra") \
            .mode("append") \
            .options(table="spotify_events", keyspace="spotify_data") \
            .save()
    except Exception as e:
        print(f"Error writing to Cassandra: {str(e)}")

cassandra_query = processed_df.writeStream \
    .foreachBatch(write_to_cassandra) \
    .option("checkpointLocation", "/tmp/checkpoint/cassandra") \
    .start()

# Write to PostgreSQL with error handling
def write_to_postgres(df, epoch_id):
    try:
        if not df.isEmpty():
            df.write \
                .format("jdbc") \
                .option("url", "jdbc:postgresql://postgres:5432/spotifydb") \
                .option("dbtable", "spotify_events") \
                .option("user", "admin") \
                .option("password", "admin") \
                .option("driver", "org.postgresql.Driver") \
                .mode("append") \
                .save()
    except Exception as e:
        print(f"Error writing to PostgreSQL: {str(e)}")

postgres_query = processed_df.writeStream \
    .foreachBatch(write_to_postgres) \
    .option("checkpointLocation", "/tmp/checkpoint/postgres") \
    .start()

# Write to console for debugging
console_query = processed_df.writeStream \
    .outputMode("append") \
    .format("console") \
    .option("truncate", "false") \
    .start()

try:
    # Keep the streaming queries running
    while True:
        time.sleep(5)  # Sleep to prevent CPU overuse
        if not all(query.isActive for query in [cassandra_query, postgres_query, console_query]):
            # If any query is not active, exit
            print("One or more queries have stopped. Shutting down...")
            break
except KeyboardInterrupt:
    print("Shutting down gracefully...")
finally:
    # Stop all queries gracefully
    for query in [cassandra_query, postgres_query, console_query]:
        try:
            query.stop()
        except:
            pass
    spark.stop()
