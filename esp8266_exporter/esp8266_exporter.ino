#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <DHT.h>

#include "config.h"

#ifndef WIFI_SSID
#error "Define WIFI_SSID in config.h"
#endif

#ifndef WIFI_PASSWORD
#error "Define WIFI_PASSWORD in config.h"
#endif

#ifndef DHT_PIN
#error "Define DHT_PIN in config.h"
#endif

#ifndef DHT_SENSOR_TYPE
#error "Define DHT_SENSOR_TYPE in config.h as DHT11 or DHT22"
#endif

namespace {

constexpr uint16_t HTTP_PORT = 80;
constexpr unsigned long SENSOR_READ_INTERVAL_MS = 2500;
constexpr unsigned long WIFI_RETRY_INTERVAL_MS = 30000;

ESP8266WebServer server(HTTP_PORT);
DHT dht(DHT_PIN, DHT_SENSOR_TYPE);

float temperatureCelsius = NAN;
float humidityRatio = NAN;
bool sensorReadSuccessful = false;
unsigned long lastSensorReadAt = 0;
unsigned long lastWiFiRetryAt = 0;

const char METRICS_CONTENT_TYPE[] = "text/plain; version=0.0.4";

void connectToWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.print(F("Connecting to Wi-Fi: "));
  Serial.println(WIFI_SSID);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print('.');

    if (millis() - lastWiFiRetryAt >= WIFI_RETRY_INTERVAL_MS) {
      Serial.println();
      Serial.println(F("Wi-Fi connection timeout; retrying..."));
      WiFi.disconnect();
      WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
      lastWiFiRetryAt = millis();
    }
  }

  Serial.println();
  Serial.println(F("WiFi connected"));
  Serial.print(F("IP address: "));
  Serial.println(WiFi.localIP());
}

void updateSensorReading() {
  const float humidityPercent = dht.readHumidity();
  const float temperature = dht.readTemperature();

  if (isnan(humidityPercent) || isnan(temperature) ||
      humidityPercent < 0.0f || humidityPercent > 100.0f) {
    sensorReadSuccessful = false;
    Serial.println(F("DHT read failed; no sensor values exported"));
    return;
  }

  temperatureCelsius = temperature;
  humidityRatio = humidityPercent / 100.0f;
  sensorReadSuccessful = true;

  Serial.print(F("Sensor: "));
  Serial.print(temperatureCelsius, 2);
  Serial.print(F(" C, "));
  Serial.print(humidityPercent, 2);
  Serial.println(F(" % RH"));
}

void updateSensorIfDue() {
  if (lastSensorReadAt == 0 ||
      millis() - lastSensorReadAt >= SENSOR_READ_INTERVAL_MS) {
    lastSensorReadAt = millis();
    updateSensorReading();
  }
}

String failureMetrics() {
  String metrics;
  metrics.reserve(256);
  metrics += F("# HELP esp8266_sensor_read_success Whether the latest sensor read succeeded.\n");
  metrics += F("# TYPE esp8266_sensor_read_success gauge\n");
  metrics += F("esp8266_sensor_read_success 0\n");
  return metrics;
}

String successfulMetrics() {
  String metrics;
  metrics.reserve(512);

  metrics += F("# HELP esp8266_temperature_celsius Air temperature measured by the sensor.\n");
  metrics += F("# TYPE esp8266_temperature_celsius gauge\n");
  metrics += F("esp8266_temperature_celsius ");
  metrics += String(temperatureCelsius, 2);
  metrics += '\n';

  metrics += F("# HELP esp8266_humidity_ratio Relative humidity as a ratio from 0 to 1.\n");
  metrics += F("# TYPE esp8266_humidity_ratio gauge\n");
  metrics += F("esp8266_humidity_ratio ");
  metrics += String(humidityRatio, 4);
  metrics += '\n';

  metrics += F("# HELP esp8266_sensor_read_success Whether the latest sensor read succeeded.\n");
  metrics += F("# TYPE esp8266_sensor_read_success gauge\n");
  metrics += F("esp8266_sensor_read_success 1\n");

  return metrics;
}

void handleMetrics() {
  updateSensorIfDue();

  server.sendHeader("Cache-Control", "no-cache");

  if (!sensorReadSuccessful) {
    server.send(503, METRICS_CONTENT_TYPE, failureMetrics());
    return;
  }

  server.send(200, METRICS_CONTENT_TYPE, successfulMetrics());
}

void handleNotFound() {
  server.send(404, "text/plain; charset=utf-8", "Not found\n");
}

}  // namespace

void setup() {
  Serial.begin(115200);
  delay(100);
  Serial.println();
  Serial.println(F("ESP8266 temperature and humidity Prometheus exporter"));

  dht.begin();
  connectToWiFi();

  server.on("/", HTTP_GET, handleMetrics);
  server.on("/metrics", HTTP_GET, handleMetrics);
  server.onNotFound(handleNotFound);
  server.begin();

  Serial.println(F("HTTP server started"));
  Serial.print(F("Metrics endpoint: http://"));
  Serial.print(WiFi.localIP());
  Serial.println(F("/metrics"));
}

void loop() {
  server.handleClient();
  updateSensorIfDue();

  if (WiFi.status() != WL_CONNECTED &&
      millis() - lastWiFiRetryAt >= WIFI_RETRY_INTERVAL_MS) {
    Serial.println(F("Wi-Fi connection lost; reconnecting..."));
    WiFi.reconnect();
    lastWiFiRetryAt = millis();
  }

  yield();
}
