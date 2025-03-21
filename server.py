from flask import Flask, request, jsonify
import mysql.connector
import paho.mqtt.client as mqtt

# Flask App
app = Flask(__name__)

# Enable CORS (for Android app requests)
from flask_cors import CORS

CORS(app)

# MySQL Database Connection
db = mysql.connector.connect(
    host="192.185.48.158",  # Example: localhost
    user="bisublar_bibic",
    password="bisublar_bibic",
    database="bisublar_bibic"
)

cursor = db.cursor()

# MQTT Settings
MQTT_BROKER = "broker.hivemq.com"  # Public broker (or your own)
MQTT_PORT = 1883
MQTT_TOPIC = "iot/control"

mqtt_client = mqtt.Client()
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)


# ------------------ API ENDPOINTS ------------------

# 📌 1. Receive sensor data from ESP32
@app.route('/send_data', methods=['POST'])
def receive_sensor_data():
    data = request.json
    air_temp = data.get('air_temp', 0.0)
    humidity = data.get('humidity', 0.0)
    water_temp = data.get('water_temp', 0.0)
    water_level = data.get('water_level', 0.0)
    ph = data.get('ph', 0.0)
    tds = data.get('tds', 0.0)

    query = "INSERT INTO sensor_data (air_temp, humidity, water_temp, water_level, ph, tds) VALUES (%s, %s, %s, %s, %s, %s)"
    values = (air_temp, humidity, water_temp, water_level, ph, tds)

    cursor.execute(query, values)
    db.commit()

    return jsonify({"message": "Data received and stored"}), 200


# 📌 2. Fetch sensor data for the Android app (GraphActivity)
@app.route('/get_sensor_data', methods=['GET'])
def get_sensor_data():
    cursor.execute("SELECT * FROM sensor_data ORDER BY id DESC LIMIT 50")
    rows = cursor.fetchall()

    sensor_list = []
    for row in rows:
        sensor_list.append({
            "id": row[0],
            "air_temp": row[1],
            "humidity": row[2],
            "water_temp": row[3],
            "water_level": row[4],
            "ph": row[5],
            "tds": row[6],
            "timestamp": row[7]
        })

    return jsonify(sensor_list)


# 📌 3. Receive ON/OFF commands from Android and send to IoT via MQTT
@app.route('/send_command', methods=['POST'])
def send_command():
    data = request.json
    command = data.get('command', 'OFF')  # Default to OFF

    if command in ["ON", "OFF"]:
        mqtt_client.publish(MQTT_TOPIC, command)
        return jsonify({"message": f"Command '{command}' sent via MQTT"}), 200
    else:
        return jsonify({"error": "Invalid command"}), 400


# Run the Flask server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
