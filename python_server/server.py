from fastapi import FastAPI, HTTPException
import pymysql
import requests
import paho.mqtt.client as mqtt
import os

# FastAPI app
app = FastAPI()

# Load environment variables
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS"),
    "database": os.getenv("DB_NAME"),
}

MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "esp32/relay")

mqtt_client = mqtt.Client()

# 📌 Connect to MySQL Database
def db_connect():
    return pymysql.connect(**DB_CONFIG)

# 📥 **Receive Data from ESP32**
@app.post("/upload_data")
async def upload_data(air_temp: float, humidity: float, water_temp: float, water_level: float, ph: float, tds: float):
    try:
        conn = db_connect()
        cursor = conn.cursor()
        query = """
        INSERT INTO sensor_readings (air_temp, humidity, water_temp, water_level, ph, tds)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (air_temp, humidity, water_temp, water_level, ph, tds))
        conn.commit()
        conn.close()
        return {"message": "✅ Data saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# 📤 **Fetch Latest Sensor Data (for Android App)**
@app.get("/latest_data")
async def latest_data():
    try:
        conn = db_connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT * FROM sensor_readings ORDER BY id DESC LIMIT 1")
        data = cursor.fetchone()
        conn.close()
        if data:
            return data
        else:
            raise HTTPException(status_code=404, detail="❌ No data found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# 📡 **Send ON/OFF Command to ESP32 (via HTTP)**
@app.get("/control_relay")
async def control_relay(state: str):
    if state not in ["on", "off"]:
        raise HTTPException(status_code=400, detail="Invalid state. Use 'on' or 'off'.")

    esp32_url = f"http://{os.getenv('ESP32_IP')}/control?relay={state}"
    try:
        response = requests.get(esp32_url)
        return {"message": f"✅ Relay turned {state}", "response": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending command to ESP32: {str(e)}")

# 📡 **Send ON/OFF Command to ESP32 (via MQTT)**
@app.get("/mqtt_control")
async def mqtt_control(state: str):
    if state not in ["on", "off"]:
        raise HTTPException(status_code=400, detail="Invalid state. Use 'on' or 'off'.")

    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.publish(MQTT_TOPIC, state)
        mqtt_client.disconnect()
        return {"message": f"✅ MQTT Command Sent: {state}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending MQTT command: {str(e)}")

# Run FastAPI server: `uvicorn server:app --host 0.0.0.0 --port 8000`
