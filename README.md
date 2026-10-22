# Docker Desktop, Portainer и мониторинговый Stack

Автор: Сунгатуллин Саид Рустамович
Группа: М3О-226СВ-25
МАИ, Институт №3, кафедра №307

## Состав

- `01_nginx_portainer_report.pdf` — отчёт по Portainer и nginx.
- `01_nginx_portainer_report.docx` — редактируемая версия первого отчёта.
- `02_monitoring_stack_report.pdf` — отчёт по Grafana Alloy, VictoriaMetrics и Grafana OSS.
- `stack/` — Docker Compose, конфигурация Alloy и provisioning Grafana.
- `esp8266_exporter/` — скетч ESP8266 для публикации температуры и влажности в формате Prometheus.
- `scripts/` — автоматический запуск Docker-стека для Windows и Linux с параметром IP ESP8266.
- `START.md` — краткая инструкция запуска после клонирования репозитория.
- `smartctl_exporter_build/` — Dockerfile и исходный бинарный релиз exporter.
- `screenshots/` — доказательства работы сервисов.
- `image-manifest.txt` — версии, ID и digest образов.
- `email_draft.txt` — текст сопроводительного письма.

## Запуск

Используйте `START.md` и скрипт под свою операционную систему. Скрипт проверяет ESP8266, создаёт Docker-сеть, запускает VictoriaMetrics, Alloy и Grafana и выводит адрес Grafana.

Windows:

```powershell
.\scripts\start-monitoring.ps1 -EspIp 10.175.10.230 -OpenBrowser
```

Linux:

```bash
./scripts/start-monitoring.sh --esp-ip 10.175.10.230 --open-browser
```

Если IP не указать, используется `10.175.10.230`.

## Фактическая проверка

Подтверждены HTTP 200 для exporter, VictoriaMetrics, Alloy и Grafana. Запрос `up` в VictoriaMetrics вернул значение 1, `smartctl_devices` — 5. Температурная метрика `smartctl_device_temperature` в Docker Desktop не появилась; это ограничение доступа Linux VM к физическим дискам, а не подставленные тестовые данные.

## Безопасность

Порты Stack привязаны к `127.0.0.1`. Пароли в учебной конфигурации предназначены только для локальной лаборатории; перед публикацией сервисов необходимо заменить их и включить штатную защиту.
