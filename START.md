# Запуск проекта из Git

Проект рассчитан на запуск из корня репозитория. ESP8266 должен быть включён, а компьютер должен находиться в той же сети, что и ESP.

## Windows

Требования:

- Git;
- Docker Desktop в режиме Linux containers;
- PowerShell;
- прошитый ESP8266.

Клонирование:

~~~powershell
git clone git@github.com:SaidSun/docker_portainer.git
cd .\docker_portainer
~~~

Если PowerShell блокирует запуск локального скрипта, разрешить его только для текущего окна:

~~~powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
~~~

Запуск с IP по умолчанию:

~~~powershell
.\scripts\start-monitoring.ps1
~~~

Запуск с IP ESP8266:

~~~powershell
.\scripts\start-monitoring.ps1 -EspIp 10.175.10.230
~~~

Запуск с автоматическим открытием Grafana:

~~~powershell
.\scripts\start-monitoring.ps1 -EspIp 10.175.10.230 -OpenBrowser
~~~

Если нужно поднять Docker даже при недоступном ESP:

~~~powershell
.\scripts\start-monitoring.ps1 -SkipEspCheck
~~~

Скрипт выводит адреса:

~~~text
Grafana:          http://localhost:3000
VictoriaMetrics:  http://localhost:8428/vmui
Alloy:            http://localhost:12345
~~~

Последняя строка вывода — URL Grafana:

~~~text
http://localhost:3000
~~~

## Linux

Требования:

- Git;
- Docker Engine и Docker Compose Plugin;
- curl;
- прошитый ESP8266.

Клонирование:

~~~bash
git clone git@github.com:SaidSun/docker_portainer.git
cd docker_portainer
~~~

Разрешить запуск скрипта:

~~~bash
chmod +x scripts/start-monitoring.sh
~~~

Запуск с IP по умолчанию:

~~~bash
./scripts/start-monitoring.sh
~~~

Запуск с IP ESP8266:

~~~bash
./scripts/start-monitoring.sh --esp-ip 10.175.10.230
~~~

Запуск с автоматическим открытием Grafana:

~~~bash
./scripts/start-monitoring.sh --esp-ip 10.175.10.230 --open-browser
~~~

Если нужно поднять Docker даже при недоступном ESP:

~~~bash
./scripts/start-monitoring.sh --skip-esp-check
~~~

Скрипт выводит адреса:

~~~text
Grafana:          http://localhost:3000
VictoriaMetrics:  http://localhost:8428/vmui
Alloy:            http://localhost:12345
~~~

## Если нужно перепрошить ESP8266

Файл прошивки:

~~~text
esp8266_exporter/esp8266_exporter.ino
~~~

Файл config.h намеренно не хранится в Git, потому что содержит Wi-Fi-настройки. После нового клонирования:

~~~text
esp8266_exporter/config.example.h -> esp8266_exporter/config.h
~~~

После заполнения config.h открыть .ino в Arduino IDE, выбрать NodeMCU 1.0 (ESP-12E Module), COM-порт и прошить плату.

## Остановка

Windows:

~~~powershell
cd .\stack
docker compose down
~~~

Linux:

~~~bash
docker compose -f stack/docker-compose.yml down
~~~

Остановка без флага -v сохраняет данные VictoriaMetrics и Grafana.
