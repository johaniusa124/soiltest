from flask import Flask, request, jsonify
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Connects to database (DomeData)
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT")),
        ssl_disabled=False 
    )

# Post data
@app.route('/data', methods=['POST'])
def receive_data():
    data = request.json

    temperature = data.get("temperature")
    humidity = data.get("humidity")
    location = data.get("location")
    timestamp = data.get("timestamp")

    if temperature is None or humidity is None or location is None or timestamp is None:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        db = get_db_connection()
        cursor = db.cursor()

        query = """
        INSERT INTO weather_data (temperature, humidity, location)#, created_at)
        VALUES (%s, %s, %s)#, %s)
        """
        cursor.execute(query, (temperature, humidity, location))#, timestamp))

        db.commit()
        cursor.close()
        db.close()

        return jsonify({"status": "success"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Optional: get latest data
@app.route('/data', methods=['GET'])
def get_data():
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM weather_data ORDER BY created_at DESC LIMIT 10")
        rows = cursor.fetchall()

        cursor.close()
        db.close()

        return jsonify(rows), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return "Weather API is running!"


def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS weather_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            temperature FLOAT,
            humidity FLOAT,
            location INT,
            #timestamp TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.commit()
        cursor.close()
        conn.close()

        print("Table created successfully")

    except Exception as e:
        print("Error creating table:", e)


if __name__ == "__main__":
    # init_db()
    app.run(host='0.0.0.0', port=8080)

