<?php
$servername = "192.185.48.158";
$username = "bisublar_lehydrosys";
$password = "lehydrosys";
$database = "bisublar_lehydrosys";

// Create connection
$conn = new mysqli($servername, $username, $password, $database);
if ($conn->connect_error) {
    die(json_encode(["error" => "❌ Connection failed: " . $conn->connect_error]));
}

// 📌 Securely Get "action" Parameter
$action = filter_input(INPUT_GET, "action", FILTER_SANITIZE_STRING);

// 📥 **Handle Sensor Data Upload**
if ($_SERVER["REQUEST_METHOD"] == "POST" && $action === "upload") {
    // Read JSON Payload
    $json = file_get_contents("php://input");
    $data = json_decode($json, true);

    // 🔍 Validate JSON Format
    if ($data === null) {
        echo json_encode(["error" => "❌ Invalid JSON format"]);
        exit;
    }

    // 🔍 Ensure All Required Fields Exist
    $required_fields = ["air_temp", "humidity", "water_temp", "water_level", "ph", "tds"];
    foreach ($required_fields as $field) {
        if (!isset($data[$field]) || $data[$field] === null) {
            echo json_encode(["error" => "❌ Missing or NULL value for '$field'"]);
            exit;
        }
    }

    // Assign Values After Validation
    $air_temp = $data["air_temp"];
    $humidity = $data["humidity"];
    $water_temp = $data["water_temp"];
    $water_level = $data["water_level"];
    $ph = $data["ph"];
    $tds = $data["tds"];

    // 📌 **Use Prepared Statement for Security**
    $stmt = $conn->prepare("INSERT INTO sensor_readings (air_temp, humidity, water_temp, water_level, ph, tds) VALUES (?, ?, ?, ?, ?, ?)");
    $stmt->bind_param("dddddd", $air_temp, $humidity, $water_temp, $water_level, $ph, $tds);

    // Execute Query & Return Response
    if ($stmt->execute()) {
        echo json_encode(["message" => "✅ Sensor data saved successfully"]);
    } else {
        echo json_encode(["error" => "❌ Database error: " . $stmt->error]);
    }
    $stmt->close();
}

// 📤 **Fetch Latest Sensor Data**
elseif ($_SERVER["REQUEST_METHOD"] == "GET" && $action === "latest_data") {
    $sql = "SELECT air_temp, humidity, water_temp, water_level, ph, tds, timestamp FROM sensor_readings ORDER BY id DESC LIMIT 1";
    $result = $conn->query($sql);

    if ($result->num_rows > 0) {
        echo json_encode($result->fetch_assoc());
    } else {
        echo json_encode(["error" => "❌ No data found"]);
    }
}

// 🚫 Invalid Request Handling
else {
    echo json_encode(["error" => "❌ Invalid request"]);
}

// Close Connection
$conn->close();
?>
