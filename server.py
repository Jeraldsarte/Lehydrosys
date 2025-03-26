from flask import Flask, request, jsonify
import mysql.connector
import os
import time
import threading
from flask_cors import CORS
from mysql.connector import pooling

# Flask App Setup
app = Flask(__name__)
CORS(app)

# Load Database Configuration from Environment Variables
DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST"),
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE"),
}

# 🔹 Connection Pooling for Faster Queries
db_pool = pooling.MySQLConnectionPool(pool_name="mypool", pool_size=5, **DB_CONFIG)

def get_db_connection():
    return db_pool.get_connection()

# ------------------ API ENDPOINTS ------------------

# 📌 Receive Sensor Data (ESP32 sends data here)
@app.route('/sensor_data', methods=['POST'])
def receive_sensor_data():
    try:
        data = request.json  
        if not data or any(value is None for value in data.values()):
            return jsonify({"error": "Missing or invalid data fields"}), 400

        # Run Database Insert in a Separate Thread (Non-Blocking)
        threading.Thread(target=store_sensor_data, args=(data,)).start()

        return jsonify({"message": "Sensor data received, storing in background"}), 200

    except Exception as e:
        print(f"🔴 Error processing sensor data: {e}")
        return jsonify({"error": "Failed to process request"}), 500

# 🔹 Background Function to Store Data
def store_sensor_data(data):
    try:
        db = get_db_connection()
        cursor = db.cursor()
        query = """INSERT INTO sensor_data (air_temp, humidity, water_temp, water_level, ph, tds) 
                   VALUES (%s, %s, %s, %s, %s, %s)"""
        cursor.execute(query, (data["air_temp"], data["humidity"], data["water_temp"], 
                               data["water_level"], data["ph"], data["tds"]))
        db.commit()
        cursor.close()
        db.close()
        print(f"✅ Data Stored: {data}")
    except Exception as e:
        print(f"🔴 Error inserting sensor data: {e}")

# 📌 Fetch Sensor Data for Android App
@app.route('/get_sensor_data', methods=['GET'])
def get_sensor_data():
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM sensor_data ORDER BY id DESC LIMIT 50")
        data = cursor.fetchall()
        cursor.close()
        db.close()
        return jsonify(data), 200
    except Exception as e:
        print(f"🔴 Failed to fetch data: {e}")
        return jsonify({"error": "Failed to fetch data"}), 500

# 📌 Send ON/OFF Command to IoT System via HTTP POST
@app.route('/send_command', methods=['POST'])
def send_command():
    try:
        data = request.json
        command = data.get("command", "").lower()

        valid_commands = ["relay1_on", "relay1_off", "relay2_on", "relay2_off"]
        if command in valid_commands:
            print(f"📤 Received Command: {command}")
            return jsonify({"message": f"Command '{command}' received!"}), 200
        return jsonify({"error": "Invalid command"}), 400

    except Exception as e:
        print(f"🔴 Error processing command: {e}")
        return jsonify({"error": "Failed to process command"}), 500

# 📌 Health Check API
@app.route('/health', methods=['GET'])
def health_check():
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT 1")  # Test MySQL connection
        cursor.close()
        db.close()
        return jsonify({"status": "running", "database": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "error", "database": "failed", "error": str(e)}), 500

# Start the Flask Web Server
if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=5000)
