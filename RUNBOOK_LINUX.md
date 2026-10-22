# Запуск ESP8266 exporter и monitoring stack в Linux

Инструкция рассчитана на проект docker_portainer_tasks, Arduino IDE или Arduino CLI, Docker Engine и Docker Compose Plugin.

Схема работы:

~~~text
ESP8266 -> HTTP /metrics -> Grafana Alloy -> VictoriaMetrics -> VMUI
~~~

## 1. Подготовить ESP8266

Подключение DHT22 к NodeMCU:

| Датчик | NodeMCU |
|---|---|
| VCC | 3V3 |
| DATA | D2 / GPIO4 |
| GND | GND |

Если используется отдельный 4-контактный DHT22 без встроенного резистора, поставить резистор 4.7–10 кОм между DATA и 3V3.

В Arduino IDE открыть esp8266_exporter/esp8266_exporter.ino и выбрать:

- Board: NodeMCU 1.0 (ESP-12E Module);
- порт платы, обычно /dev/ttyUSB0 или /dev/ttyACM0;
- Serial Monitor: 115200 baud.

Для доступа к USB-порту текущего пользователя обычно требуется группа dialout:

~~~bash
sudo usermod -aG dialout "$USER"
~~~

После выполнения команды нужно выйти из Linux-сеанса и войти снова.

После прошивки в Serial Monitor должны появиться:

~~~text
WiFi connected
IP address: 10.175.10.230
HTTP server started
Metrics endpoint: http://10.175.10.230/metrics
Sensor: 26.70 C, 37.00 % RH
~~~

IP-адрес нужно брать именно из Serial Monitor: после перезагрузки он может измениться.

## 2. Проверить ESP8266 напрямую

~~~bash
ESP_IP=10.175.10.230
curl -i --connect-timeout 3 --max-time 10 "http://$ESP_IP/metrics"
~~~

Ожидается HTTP-код 200, заголовок Content-Type: text/plain; version=0.0.4 и метрики:

~~~text
esp8266_temperature_celsius
esp8266_humidity_ratio
esp8266_sensor_read_success 1
~~~

Проверка TCP-порта:

~~~bash
nc -vz -w 3 "$ESP_IP" 80
~~~

Если nc не установлен, достаточно выполнить curl из предыдущего шага.

Компьютер и ESP8266 должны быть в одной сети. Проверить адреса и маршрут:

~~~bash
ip -br addr
ip route get "$ESP_IP"
~~~

## 3. Запустить Docker Compose

Проверить Docker:

~~~bash
docker version
docker compose version
~~~

Перейти в проект. Например:

~~~bash
cd ~/docker_portainer_tasks
~~~

Создать внешнюю Docker-сеть один раз:

~~~bash
docker network inspect observability_net >/dev/null 2>&1 || \
  docker network create observability_net
~~~

Запустить стек:

~~~bash
docker compose -f stack/docker-compose.yml up -d
docker compose -f stack/docker-compose.yml ps
~~~

Ожидаются контейнеры:

~~~text
alloy              Up
grafana            Up
victoria-metrics   Up (healthy)
~~~

В текущем docker-compose.yml запускаются VictoriaMetrics, Alloy и Grafana. smartctl-exporter является отдельным старым компонентом проекта и для ESP8266 не нужен.

## 4. Проверить Alloy

~~~bash
docker compose -f stack/docker-compose.yml logs --tail=100 alloy
~~~

В логах должно быть сообщение Alloy is running.

Веб-интерфейс Alloy:

~~~text
http://localhost:12345
~~~

Цель ESP задаётся в файле stack/alloy/config.alloy:

~~~alloy
"__address__" = "10.175.10.230:80"
~~~

Если IP изменился, отредактировать файл:

~~~bash
nano stack/alloy/config.alloy
~~~

После изменения пересоздать Alloy:

~~~bash
docker compose -f stack/docker-compose.yml up -d --force-recreate alloy
~~~

## 5. Проверить данные в VictoriaMetrics

Alloy опрашивает ESP каждые 15 секунд. Подождать:

~~~bash
sleep 30
~~~

Проверить доступность цели:

~~~bash
curl -G \
  --data-urlencode 'query=up{job="esp8266"}' \
  http://127.0.0.1:8428/api/v1/query
~~~

В результате должно быть значение "1".

Проверить метрики датчика:

~~~bash
curl -G \
  --data-urlencode 'query=esp8266_temperature_celsius' \
  http://127.0.0.1:8428/api/v1/query

curl -G \
  --data-urlencode 'query=esp8266_humidity_ratio' \
  http://127.0.0.1:8428/api/v1/query

curl -G \
  --data-urlencode 'query=esp8266_sensor_read_success' \
  http://127.0.0.1:8428/api/v1/query
~~~

Проверить состояние VictoriaMetrics:

~~~bash
curl http://127.0.0.1:8428/health
~~~

Ожидается OK.

## 6. Проверить через WebUI VictoriaMetrics

Открыть:

~~~text
http://localhost:8428/vmui
~~~

Ввести по очереди:

~~~promql
up{job="esp8266"}
~~~

~~~promql
esp8266_temperature_celsius
~~~

~~~promql
esp8266_humidity_ratio
~~~

~~~promql
esp8266_sensor_read_success
~~~

Нормальный результат: up = 1, температура примерно 26.7, влажность 0.37, sensor_read_success = 1.

## 7. Диагностика

Если прямой запрос к ESP не проходит:

~~~bash
curl -v --connect-timeout 3 --max-time 10 http://10.175.10.230/metrics
~~~

Проверить Wi-Fi-сеть, IP-адрес из Serial Monitor и маршрут командой ip route get.

Если прямой запрос проходит, но up равен 0:

~~~bash
docker compose -f stack/docker-compose.yml logs --tail=100 alloy
docker compose -f stack/docker-compose.yml restart alloy
sleep 30
~~~

Если ESP отвечает HTTP 503, проверить модель датчика, питание, DATA и сообщения об ошибке в Serial Monitor.

## 8. Остановить и повторно запустить стек

Остановить контейнеры:

~~~bash
docker compose -f stack/docker-compose.yml down
~~~

Данные VictoriaMetrics сохраняются. Повторный запуск:

~~~bash
docker compose -f stack/docker-compose.yml up -d
~~~
