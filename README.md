# ESP8266 и Docker monitoring stack

Учебный проект для сбора температуры и влажности с ESP8266. ESP8266 публикует метрики в формате Prometheus, Grafana Alloy забирает их и отправляет в VictoriaMetrics, а Grafana отображает графики.

## Состав проекта

- `esp8266_exporter/` — скетч ESP8266 и пример конфигурации Wi-Fi и DHT.
- `stack/` — Docker Compose, Alloy, VictoriaMetrics и Grafana.
- `scripts/` — автоматический запуск стека для Windows и Linux.

Перед запуском ESP8266 должен быть прошит и доступен в той же локальной сети, что и компьютер. По умолчанию используется IP `10.175.10.230`.

## Windows

Клонировать или обновить проект:

```powershell
git clone git@github.com:SaidSun/docker_portainer.git
cd docker_portainer
git pull
```

Если PowerShell запрещает запуск скриптов, разрешение действует только для текущего окна:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Запуск с IP ESP8266:

```powershell
.\scripts\start-monitoring.ps1 -EspIp 10.175.10.230 -OpenBrowser
```

Если используется IP по умолчанию, параметр можно не указывать:

```powershell
.\scripts\start-monitoring.ps1 -OpenBrowser
```

## Linux

Клонировать или обновить проект:

```bash
git clone git@github.com:SaidSun/docker_portainer.git
cd docker_portainer
git pull
chmod +x scripts/start-monitoring.sh
```

Запуск с IP ESP8266:

```bash
./scripts/start-monitoring.sh --esp-ip 10.175.10.230 --open-browser
```

При IP по умолчанию параметр можно не указывать:

```bash
./scripts/start-monitoring.sh --open-browser
```

Если ESP8266 временно недоступен, но нужно запустить Docker-стек:

```powershell
.\scripts\start-monitoring.ps1 -SkipEspCheck
```

```bash
./scripts/start-monitoring.sh --skip-esp-check
```

## Адреса и вход

После запуска скрипт выводит адрес Grafana. Обычно это:

- Grafana: `http://localhost:3000`
- VictoriaMetrics: `http://localhost:8428/vmui`
- Alloy: `http://localhost:12345`

В Grafana используются логин `admin` и пароль из `stack/.env` либо значение по умолчанию `grafana-lab-2026`.

Для остановки контейнеров без удаления накопленных данных:

```bash
docker compose -f stack/docker-compose.yml down
```

В Windows используется та же команда в PowerShell.
