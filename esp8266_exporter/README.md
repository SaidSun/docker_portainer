# ESP8266 Prometheus exporter

Скетч прошивает NodeMCU 1.0 и запускает HTTP-сервер на ESP8266. Адреса `/` и `/metrics` возвращают метрики температуры и влажности в текстовом формате Prometheus.

## Что установить

1. Arduino IDE 1.x или 2.x.
2. В `File → Preferences → Additional Board Manager URLs` добавить:

   `https://arduino.esp8266.com/stable/package_esp8266com_index.json`

3. В Boards Manager установить пакет `esp8266`.
4. В Library Manager установить:
   - `DHT sensor library` от Adafruit;
   - `Adafruit Unified Sensor`, если Arduino IDE не установила зависимость автоматически.

## Подготовка конфигурации

1. Открыть `config.h`.
2. Заменить `YOUR_WIFI_SSID` и `YOUR_WIFI_PASSWORD`.
3. Проверить маркировку датчика:
   - `DHT11` — использовать `#define DHT_SENSOR_TYPE DHT11`;
   - `DHT22` или `AM2302` — использовать `#define DHT_SENSOR_TYPE DHT22`.
4. По умолчанию DATA подключается к NodeMCU `D2` (`GPIO4`).

Файл `config.h` содержит локальные настройки и не должен отправляться вместе с реальными паролями. Для передачи проекта используйте `config.example.h`.

## Подключение DHT

Для обычного 4-контактного датчика:

| DHT | NodeMCU |
|---|---|
| VCC | 3V3 |
| DATA | D2 / GPIO4 |
| GND | GND |

Между DATA и 3V3 нужен подтягивающий резистор примерно 4.7–10 кОм, если его нет на модуле датчика. Не подключайте 5-вольтовый сигнал DATA к ESP8266.

## Прошивка

1. Открыть `esp8266_exporter.ino` в Arduino IDE.
2. Выбрать `Tools → Board → ESP8266 Boards → NodeMCU 1.0 (ESP-12E Module)`.
3. Выбрать COM-порт платы.
4. Нажать Upload.
5. Открыть Serial Monitor на скорости `115200`.

Ожидаемые сообщения:

```text
Connecting to Wi-Fi: YOUR_WIFI_SSID
.....
WiFi connected
IP address: 192.168.1.123
HTTP server started
Metrics endpoint: http://192.168.1.123/metrics
```

## Проверка endpoint

Компьютер и ESP8266 должны находиться в одной локальной сети. В PowerShell выполнить:

```powershell
Invoke-WebRequest http://192.168.1.123/metrics
```

Замените IP на адрес из Serial Monitor. Успешный ответ содержит, например:

```text
# HELP esp8266_temperature_celsius Air temperature measured by the sensor.
# TYPE esp8266_temperature_celsius gauge
esp8266_temperature_celsius 23.40
# HELP esp8266_humidity_ratio Relative humidity as a ratio from 0 to 1.
# TYPE esp8266_humidity_ratio gauge
esp8266_humidity_ratio 0.4500
# HELP esp8266_sensor_read_success Whether the latest sensor read succeeded.
# TYPE esp8266_sensor_read_success gauge
esp8266_sensor_read_success 1
```

Влажность экспортируется как ratio от 0 до 1: `0.45` означает 45 процентов.

## Ошибки

- HTTP 503 и `esp8266_sensor_read_success 0` означают, что последнее чтение датчика не удалось.
- Проверьте модель датчика в `config.h`, питание 3.3 V, общий GND, DATA и подтягивающий резистор.
- Если ESP8266 не подключается, проверьте SSID, пароль и что сеть работает в диапазоне 2.4 GHz.
- Датчик DHT не следует опрашивать чаще, чем примерно раз в 2 секунды; скетч использует интервал 2.5 секунды.

Интеграция с Grafana Alloy и VictoriaMetrics в этом этапе не выполняется.
