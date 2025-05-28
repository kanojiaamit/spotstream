# Spotstream: Real-Time Spotify Data Pipeline

🚀 Spotstream is an end-to-end real-time data pipeline that captures data from the Spotify API, processes it in real-time using Apache Spark Streaming, and stores the results in both Apache Cassandra (NoSQL) and PostgreSQL (SQL) databases. The entire environment is containerized using Docker and Docker Compose, with Apache Kafka (in KRaft mode) serving as the message broker. Apache Airflow is included for environment initialization and potential workflow management.

This project demonstrates a modern data engineering stack and showcases skills in data ingestion, stream processing, data storage in multiple database paradigms, and containerization.

## ✨ Features

*   **Real-time Data Ingestion:** Fetches track data from the Spotify API using a Python producer.
*   **Scalable Messaging:** Uses Apache Kafka (KRaft mode) for robust and scalable message queuing.
*   **Stream Processing:** Leverages Apache Spark Streaming for real-time data transformation and processing.
*   **Dual Database Storage:** Persists processed data into:
    *   **Apache Cassandra:** For high-volume, scalable NoSQL storage.
    *   **PostgreSQL:** For structured, relational data storage.
*   **Containerized Environment:** Fully containerized with Docker and Docker Compose for easy setup and reproducibility.
*   **Orchestration Ready:** Includes Apache Airflow for initialization and potential future workflow orchestration.
*   **Robust Configuration:** Demonstrates configuration of Kafka listeners, Spark package dependencies, and inter-service networking within Docker.

## 🏗️ Architecture

The data flows through the pipeline as follows:

1.  **Spotify API (`spotify-producer` service):** A Python script (using Spotipy) fetches track data (e.g., "Bohemian Rhapsody") from the Spotify API.
2.  **Apache Kafka (`kafka` service):** The Python producer sends the fetched data as JSON messages to a Kafka topic named `spotify_events`.
3.  **Apache Spark Streaming (`spark_processor` service):** A Spark Streaming application consumes messages from the `spotify_events` Kafka topic.
    *   It parses the JSON data.
    *   It performs transformations (e.g., schema definition, timestamp conversion).
    *   It writes the processed data to two sinks:
        *   An `spotify_events` table in an Apache Cassandra keyspace (`spotify_data`).
        *   An `spotify_events` table in a PostgreSQL database (`spotifydb`).
4.  **Databases (`cassandra` & `postgres` services):** Store the final processed data.
5.  **Apache Airflow (`airflow-scheduler`, `airflow-webserver`, `airflow-init` services):** Used for initializing the Airflow environment and database. Can be extended to orchestrate other tasks.


All services are managed and networked by Docker Compose.

## 🛠️ Technology Stack

*   **Data Source:** Spotify Web API
*   **Programming Language:** Python 3.x
*   **Messaging Broker:** Apache Kafka 3.7.0 (KRaft mode)
*   **Stream Processing:** Apache Spark 3.4.0 (Streaming)
*   **Databases:**
    *   Apache Cassandra 4.1 (NoSQL)
    *   PostgreSQL 15 (SQL)
*   **Containerization:** Docker, Docker Compose
*   **Orchestration (Initialization):** Apache Airflow 2.8.1
*   **Python Libraries:**
    *   `spotipy` (Spotify API client)
    *   `kafka-python` (Kafka producer client)
    *   `pyspark` (Spark Python API)
    *   `python-dotenv` (Environment variable management)