FROM bitnami/spark:3.4.0

USER root
WORKDIR /app

COPY processor.py .

# Install any extra Python dependencies if needed
RUN pip install pyspark

CMD ["spark-submit", "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0", "processor.py"]
