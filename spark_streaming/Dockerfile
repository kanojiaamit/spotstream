FROM bitnami/spark:3.4.0

USER root
WORKDIR /app

# Install curl and download PostgreSQL JDBC driver
RUN apt-get update && \
    apt-get install -y curl && \
    curl -L https://jdbc.postgresql.org/download/postgresql-42.6.0.jar -o /opt/bitnami/spark/jars/postgresql-42.6.0.jar && \
    rm -rf /var/lib/apt/lists/*

# Create checkpoint directories
RUN mkdir -p /tmp/checkpoint/cassandra /tmp/checkpoint/postgres && \
    chmod -R 777 /tmp/checkpoint

COPY processor.py .

# Install any extra Python dependencies if needed
RUN pip install pyspark

CMD ["spark-submit", \
     "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0,com.datastax.spark:spark-cassandra-connector_2.12:3.4.0,org.postgresql:postgresql:42.6.0", \
     "--conf", "spark.sql.extensions=com.datastax.spark.connector.CassandraSparkExtensions", \
     "--conf", "spark.cassandra.connection.host=cassandra", \
     "--conf", "spark.cassandra.connection.port=9042", \
     "processor.py"]
