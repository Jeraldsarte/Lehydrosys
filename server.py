from flask import Flask, request, jsonify
import mysql.connector
import os
from flask_cors import CORS

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

# Function to Create a New Database Connection
def connect_db():
    try:
        db = mysql.connector.connect(**DB_CONFIG)
        print("✅ Connected to MySQL")
        return db
    except mysql.connector.Error as err:
        print(f"🔴 Database Connection Error: {err}")
        return None

# 📌 HTTP POST Endpoint for Sensor Data
@app.route('/sensor_data', methods=['POST'])
def receive_sensor_data():
    try:
        data = request.json  # Receive JSON Data from ESP32
        air_temp = data.get("air_temp")
        humidity = data.get("humidity")
        water_temp = data.get("water_temp")
        water_level = data.get("water_level")
        ph = data.get("ph")
        tds = data.get("tds")

        if None in [air_temp, humidity, water_temp, water_level, ph, tds]:
            return jsonify({"error": "Missing data fields"}), 400

        # Store Data in MySQL
        db = connect_db()
        if db:
            cursor = db.cursor()
            query = "INSERT INTO sensor_data (air_temp, humidity, water_temp, water_level, ph, tds) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(query, (air_temp, humidity, water_temp, water_level, ph, tds))
            db.commit()
            cursor.close()
            db.close()
            print(f"✅ Data Stored: {data}")
            return jsonify({"message": "Sensor data received and stored"}), 200
        else:
            return jsonify({"error": "Database connection failed"}), 500

    except Exception as e:
        print(f"🔴 Error: {e}")
        return jsonify({"error": "Failed to process request"}), 500

# 📌 HTTP GET Endpoint for Fetching Sensor Data
@app.route('/get_sensor_data', methods=['GET'])
def get_sensor_data():
    try:
        db = connect_db()
        if db:
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM sensor_data ORDER BY id DESC LIMIT 50")
            data = cursor.fetchall()
            cursor.close()
            db.close()
            return jsonify(data), 200
        else:
            return jsonify({"error": "Database connection failed"}), 500
    except Exception as e:
        return jsonify({"error": f"Failed to fetch data: {e}"}), 500

# Start Flask Server
if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=5000)
