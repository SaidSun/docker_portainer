#pragma once

// Copy this file to config.h and replace the Wi-Fi placeholders.
#define WIFI_SSID "YOUR_WIFI_SSID"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"

// NodeMCU D2 is GPIO4.
#define DHT_PIN D2

// Select exactly one sensor type after checking the sensor marking.
// #define DHT_SENSOR_TYPE DHT11
#define DHT_SENSOR_TYPE DHT22
