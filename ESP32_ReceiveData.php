<?php
// Set the Content-Type header to JSON (optional)
header('Content-Type: application/json');

// Get the raw POST data
$data = file_get_contents('php://input');

// Decode the JSON data into a PHP array
$decodedData = json_decode($data, true);

// Check if the decoding was successful
if ($decodedData === null) {
    // If decoding fails, send an error response
    echo json_encode(["status" => "error", "message" => "Invalid JSON data received"]);
    exit;
}

// Retrieve values from the decoded data array
$dht22_temperature = $decodedData['dht22_temperature'] ?? null;
$dht22_humidity = $decodedData['dht22_humidity'] ?? null;
$ultrasonic_distance = $decodedData['ultrasonic_distance'] ?? null;
$ph_value = $decodedData['ph_value'] ?? null;
$tds_value = $decodedData['tds_value'] ?? null;
$ds18b20_temperature = $decodedData['ds18b20_temperature'] ?? null;

// If any required field is missing, return an error
if ($dht22_temperature === null || $dht22_humidity === null || $ultrasonic_distance === null || 
    $ph_value === null || $tds_value === null || $ds18b20_temperature === null) {
    echo json_encode(["status" => "error", "message" => "Missing required sensor data"]);
    exit;
}

// Here, you can handle the data, e.g., save it to a database
// For this example, we'll just return a success response

// Example: Print received values (you can save them to a database here)
echo json_encode([
    "status" => "success",
    "message" => "Data received successfully",
    "data" => [
        "dht22_temperature" => $dht22_temperature,
        "dht22_humidity" => $dht22_humidity,
        "ultrasonic_distance" => $ultrasonic_distance,
        "ph_value" => $ph_value,
        "tds_value" => $tds_value,
        "ds18b20_temperature" => $ds18b20_temperature
    ]
]);

?>
