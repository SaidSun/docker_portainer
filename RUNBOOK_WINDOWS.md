# Запуск ESP8266 exporter и monitoring stack в Windows

Инструкция рассчитана на проект `docker_portainer_tasks`, Arduino IDE и Docker Desktop.

Схема работы:

```text
ESP8266 -> HTTP /metrics -> Grafana Alloy -> VictoriaMetrics -> VMUI
```

## 1. Подготовить ESP8266

Подключение DHT22 к NodeMCU:

| Датчик | NodeMCU |
|---|---|
| VCC | 3V3 |
| DATA | D2 / GPIO4 |
| GND | GND |

Если используется отдельный 4-контактный DHT22 без встроенного резистора, поставить резистор 4.7–10 кОм между DATA и 3V3.

В Arduino IDE открыть `esp8266_exporter/esp8266_exporter.ino`, выбрать:

- Board: `NodeMCU 1.0 (ESP-12E Module)`;
- правильный COM-порт;
- Serial Monitor: `115200 baud`.

После прошивки в Serial Monitor должны появиться:

```text
WiFi connected
IP address: 10.175.10.230
HTTP server started
Metrics endpoint: http://10.175.10.230/metrics
Sensor: 26.70 C, 37.00 % RH
```

IP-адрес нужно брать именно из Serial Monitor: после перезагрузки он может измениться.

## 2. Проверить ESP8266 напрямую

Открыть PowerShell и выполнить:

```powershell
$espIp = "10.175.10.230"

$r = Invoke-WebRequest -UseBasicParsing "http://$espIp/metrics"
$r.StatusCode
$r.Headers["Content-Type"]
$r.Content
```

Ожидается HTTP-код `200` и метрики:

```text
esp8266_temperature_celsius
esp8266_humidity_ratio
esp8266_sensor_read_success 1
```

Проверка TCP-порта:

```powershell
Test-NetConnection $espIp -Port 80
```

Ожидаемый результат:

```text
TcpTestSucceeded : True
```

Компьютер и ESP8266 должны быть в одной сети. Например, если ESP получил адрес `10.175.10.230`, компьютер должен иметь доступ к сети `10.175.10.0/24`. Адрес компьютера `192.168.1.x` без маршрута к сети ESP не подойдёт.

## 3. Запустить Docker Compose

Запустить Docker Desktop и дождаться, пока Docker станет доступен.

В PowerShell:

```powershell
cd F:\scripts\HW\docker_portainer_tasks
docker version
```

Compose использует внешнюю Docker-сеть. Создать её один раз:

```powershell
docker network inspect observability_net *> $null
if ($LASTEXITCODE -ne 0) {
    docker network create observability_net
}
```

Запустить стек:

```powershell
cd .\stack
docker compose up -d
docker compose ps
```

Ожидаются контейнеры:

```text
alloy              Up
grafana            Up
victoria-metrics   Up (healthy)
```

В текущем `docker-compose.yml` запускаются VictoriaMetrics, Alloy и Grafana. `smartctl-exporter` является отдельным старым компонентом проекта и для ESP8266 не нужен.

## 4. Проверить Alloy

Посмотреть логи:

```powershell
docker compose logs --tail=100 alloy
```

В логах должно быть сообщение наподобие:

```text
Alloy is running
```

Веб-интерфейс Alloy:

```text
http://localhost:12345
```

Цель ESP задаётся в файле `stack/alloy/config.alloy`:

```alloy
"__address__" = "10.175.10.230:80"
```

Если IP изменился, отредактировать строку и пересоздать Alloy:

```powershell
docker compose up -d --force-recreate alloy
```

## 5. Проверить данные в VictoriaMetrics

Alloy опрашивает ESP каждые 15 секунд. Подождать немного:

```powershell
Start-Sleep -Seconds 30
```

Проверить доступность цели:

```powershell
Invoke-RestMethod `
  "http://127.0.0.1:8428/api/v1/query?query=up%7Bjob%3D%22esp8266%22%7D" |
  ConvertTo-Json -Depth 10
```

В результате должно быть значение `"1"`.

Проверить метрики датчика:

```powershell
Invoke-RestMethod `
  "http://127.0.0.1:8428/api/v1/query?query=esp8266_temperature_celsius" |
  ConvertTo-Json -Depth 10

Invoke-RestMethod `
  "http://127.0.0.1:8428/api/v1/query?query=esp8266_humidity_ratio" |
  ConvertTo-Json -Depth 10

Invoke-RestMethod `
  "http://127.0.0.1:8428/api/v1/query?query=esp8266_sensor_read_success" |
  ConvertTo-Json -Depth 10
```

Проверка состояния VictoriaMetrics:

```powershell
curl.exe http://127.0.0.1:8428/health
```

Ожидается `OK`.

## 6. Проверить через WebUI VictoriaMetrics

Открыть:

```text
http://localhost:8428/vmui
```

Ввести по очереди следующие PromQL-запросы:

```promql
up{job="esp8266"}
```

```promql
esp8266_temperature_celsius
```

```promql
esp8266_humidity_ratio
```

```promql
esp8266_sensor_read_success
```

Нормальный результат: `up = 1`, температура примерно `26.7`, влажность `0.37`, `sensor_read_success = 1`.

## 7. Диагностика

Если прямой запрос к ESP не проходит:

```powershell
Invoke-WebRequest -UseBasicParsing http://10.175.10.230/metrics
```

Проверить Wi-Fi-сеть, IP-адрес из Serial Monitor и сетевой маршрут.

Если прямой запрос проходит, но `up` равен `0`:

```powershell
docker compose logs --tail=100 alloy
docker compose restart alloy
Start-Sleep -Seconds 30
```

Если ESP отвечает HTTP `503`, проверить модель датчика, питание, DATA и сообщения об ошибке в Serial Monitor.

## 8. Остановить и повторно запустить стек

Остановить контейнеры:

```powershell
docker compose down
```

Данные VictoriaMetrics сохраняются. Повторный запуск:

```powershell
docker compose up -d
```
