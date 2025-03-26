from flask import Flask, request, jsonify
import mysql.connector
import paho.mqtt.client as mqtt
import os
import time
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

# MQTT Configuration
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
MQTT_TOPIC_SENSOR = "iot/sensor"
MQTT_TOPIC_COMMAND = "iot/control"

# Function to create a new database connection
def connect_db():
    while True:
        try:
            db = mysql.connector.connect(**DB_CONFIG, connection_timeout=10)
            print("✅ Connected to MySQL")
            return db
        except mysql.connector.Error as err:
            print(f"🔴 Database Connection Error: {err}. Retrying in 5s...")
            time.sleep(5)

# MQTT Client Setup
mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT Broker")
        client.subscribe(MQTT_TOPIC_SENSOR)
    else:
        print(f"🔴 MQTT Connection Failed with Code {rc}")


def on_message(client, userdata, msg):
    payload = msg.payload.decode().strip()
    print(f"📩 Received MQTT Data: {payload}")

    try:
        air_temp, humidity, water_temp, water_level, ph, tds = map(float, payload.split(","))

        # Create a new MySQL connection for every request
        db = connect_db()
        cursor = db.cursor()
        query = "INSERT INTO sensor_data (air_temp, humidity, water_temp, water_level, ph, tds) VALUES (%s, %s, %s, %s, %s, %s)"
        cursor.execute(query, (air_temp, humidity, water_temp, water_level, ph, tds))
        db.commit()
        cursor.close()
        db.close()  # Close the connection after inserting data
        print("✅ Data stored in database")
    except Exception as e:
        print(f"🔴 Error processing MQTT data: {e}")

# Function to connect to MQTT broker with auto-reconnect
def connect_mqtt():
    while True:
        try:
            mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            print("✅ Connected to MQTT Broker")
            return
        except Exception as e:
            print(f"🔴 MQTT Connection Failed: {e}. Retrying in 5s...")
            time.sleep(5)

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
connect_mqtt()
mqtt_client.loop_start()  # Starts MQTT loop in background

# ------------------ API ENDPOINTS ------------------

# 📌 Fetch sensor data for Android app
@app.route('/get_sensor_data', methods=['GET'])
def get_sensor_data():
    try:
        db = connect_db()  # Create a new database connection
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM sensor_data ORDER BY id DESC LIMIT 50")
        data = cursor.fetchall()
        cursor.close()
        db.close()  # Close connection after use
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": f"Failed to fetch data: {e}"}), 500

# 📌 Send ON/OFF Command to IoT System via MQTT
@app.route('/send_command', methods=['POST'])
def send_command():
    data = request.json
    command = data.get("command", "").lower()  # Convert to lowercase

    valid_commands = ["relay1_on", "relay2_on"]
    
    if command in valid_commands:
        mqtt_client.publish(MQTT_TOPIC_COMMAND, command)
        print(f"📤 Sent MQTT Command: {command}")
        return jsonify({"message": f"Command '{command}' sent!"}), 200
    
    return jsonify({"error": "Invalid command"}), 400

# 📌 Health Check API to Monitor Server Status
@app.route('/health', methods=['GET'])
def health_check():
    try:
        db = connect_db()
        cursor = db.cursor()
        cursor.execute("SELECT 1")  # Test MySQL connection
        cursor.close()
        db.close()
        return jsonify({"status": "running", "database": "connected", "mqtt": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "error", "database": "failed", "mqtt": "connected", "error": str(e)}), 500

# Start the Flask Web Server
if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=5000)
