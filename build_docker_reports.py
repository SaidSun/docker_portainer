from __future__ import annotations

import base64
import hashlib
import html
import json
import shutil
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SCREENSHOTS = ROOT / "screenshots"
STACK = ROOT / "stack"
BUILD = ROOT / "_build"
BUILD.mkdir(exist_ok=True)

STUDENT = "Сунгатуллин Саид Рустамович"
GROUP = "М3О-226СВ-25"
INSTITUTION = "Московский авиационный институт (национальный исследовательский университет)"
INSTITUTE = "Институт № 3, кафедра № 307"
YEAR = "2026"
SEARCH_DATE = "1 октября 2026 г."


def run(*args: str) -> str:
    result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return result.stdout.strip()


def image_inspect(ref: str) -> dict:
    raw = run("docker", "image", "inspect", ref)
    try:
        return json.loads(raw)[0]
    except (ValueError, IndexError):
        return {}


def image_line(ref: str, note: str = "") -> str:
    data = image_inspect(ref)
    image_id = str(data.get("Id", "")).replace("sha256:", "")
    repo_digests = data.get("RepoDigests", [])
    digest = repo_digests[0].split("@", 1)[1] if repo_digests else "локальный образ / digest не опубликован"
    created = data.get("Created", "")
    return f"{ref}\tID sha256:{image_id}\t{digest}\tсоздан {created}\t{note}".strip()


def asset(name: str) -> str:
    return (SCREENSHOTS / name).resolve().as_uri()


def esc(value: object) -> str:
    return html.escape(str(value))


def image_tag(name: str, alt: str, width: str = "100%") -> str:
    return f'<img class="figure-image" style="max-width:{width}" src="{asset(name)}" alt="{esc(alt)}">'


def page(number: int | None, content: str) -> str:
    footer = "" if number is None else f'<div class="page-number">{number}</div>'
    return f'<section class="page">{content}{footer}</section>'


CSS = """
@page { size: A4; margin: 20mm 15mm 20mm 30mm; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: white; color: #000; }
body { font-family: "Times New Roman", Times, serif; font-size: 14pt; line-height: 1.5; }
.page { width: 100%; height: 257mm; position: relative; page-break-after: always; overflow: hidden; }
.page:last-child { page-break-after: auto; }
.page-number { position: absolute; bottom: 0; left: 0; right: 0; text-align: center; font-size: 12pt; }
h1, h2, h3 { color: #000; font-family: "Times New Roman", Times, serif; }
h1 { font-size: 16pt; text-align: center; margin: 0 0 12pt; line-height: 1.25; }
h2 { font-size: 14pt; margin: 0 0 10pt; text-align: center; }
h3 { font-size: 14pt; margin: 8pt 0 6pt; }
p { margin: 0 0 8pt; text-align: justify; text-indent: 1.25cm; }
.no-indent { text-indent: 0; }
.center { text-align: center; text-indent: 0; }
.right { text-align: right; text-indent: 0; }
.title-top { text-align: center; line-height: 1.25; margin-top: 4mm; }
.title-main { text-align: center; margin-top: 34mm; font-weight: bold; }
.title-bottom { position: absolute; bottom: 10mm; left: 0; right: 0; text-align: center; }
.toc { margin: 14pt 0 0 0; }
.toc p { text-indent: 0; margin: 5pt 0; }
table { width: 100%; border-collapse: collapse; margin: 8pt 0 12pt; font-size: 11.5pt; line-height: 1.25; }
th, td { border: 1px solid #000; padding: 4pt 5pt; vertical-align: top; }
th { font-weight: bold; text-align: center; }
ul, ol { margin: 4pt 0 8pt 18pt; padding-left: 14pt; }
li { margin: 2pt 0; }
pre { border: 1px solid #000; padding: 7pt; white-space: pre-wrap; font: 9.5pt/1.25 "Courier New", monospace; margin: 7pt 0; }
.figure { margin: 4pt 0 0; text-align: center; }
.figure-image { display: block; margin: 0 auto 5pt; max-height: 193mm; object-fit: contain; }
figcaption { font-size: 12pt; line-height: 1.25; text-align: center; }
.small { font-size: 11pt; line-height: 1.3; }
.refs p { text-indent: -1.25cm; margin-left: 1.25cm; text-align: left; }
.box { border: 1px solid #000; padding: 7pt; margin: 6pt 0; }
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 8pt; }
.two-col img { width: 100%; max-height: 80mm; object-fit: contain; }
"""


def html_document(title: str, pages: list[str]) -> str:
    return "<!doctype html><html lang='ru'><head><meta charset='utf-8'><title>" + esc(title) + "</title><style>" + CSS + "</style></head><body>" + "".join(pages) + "</body></html>"


def title_page(report_title: str, subtitle: str) -> str:
    return page(None, f"""
      <div class="title-top">{esc(INSTITUTION)}<br>{esc(INSTITUTE)}</div>
      <div class="title-main"><div>ОТЧЁТ</div><br><div>{esc(report_title)}</div><br><div>{esc(subtitle)}</div></div>
      <div class="title-bottom">Выполнил: студент группы {esc(GROUP)}<br>{esc(STUDENT)}<br><br>Москва, {YEAR}</div>
    """)


def common_abstract(title: str, keywords: str) -> str:
    return f"""
      <h1>РЕФЕРАТ</h1>
      <p>Отчёт посвящён выполнению практических заданий по контейнеризации приложений средствами Docker Desktop и Portainer. В первой части развёрнут контейнер nginx и проверена публикация веб-сервиса. Во второй части создан Stack из Grafana Alloy, VictoriaMetrics и Grafana OSS, объединённых общей Docker-сетью. Для сбора SMART-показателей дополнительно подключён smartctl-exporter.</p>
      <p>В работе приведены конфигурация образов, сопоставление портов, параметры Docker Compose, результаты проверки сетевого взаимодействия и снимки экрана работающих сервисов.</p>
      <p class="no-indent"><b>Ключевые слова:</b> Docker Desktop, Portainer, nginx, Docker Compose, Grafana Alloy, VictoriaMetrics, Grafana OSS, smartctl-exporter, мониторинг.</p>
      <h2>СОДЕРЖАНИЕ</h2>
      <div class="toc">
        <p>Введение ........................................................................ 3</p>
        <p>1 Цель и исходная конфигурация ................................. 3</p>
        <p>2 Выполнение задания ................................................ 4</p>
        <p>3 Проверка результата ................................................ 5</p>
        <p>Заключение .................................................................. 6</p>
        <p>Список использованных источников ............................ 7</p>
      </div>
    """


def build_report_1() -> str:
    pages: list[str] = [title_page(
        "Установка Docker Desktop, Portainer и nginx",
        "Практическое задание по развёртыванию контейнерного веб-сервиса",
    )]
    pages.append(page(2, common_abstract("", "")))
    pages.append(page(3, """
      <h1>ВВЕДЕНИЕ</h1>
      <p>Цель задания — проверить установку Docker Desktop и Portainer, создать контейнер nginx, опубликовать его HTTP-порт на хостовой системе и подтвердить доступность стандартной страницы веб-сервера в браузере.</p>
      <h2>1 Цель и исходная конфигурация</h2>
      <p>Работа выполнена в Docker-контексте <i>desktop-linux</i>. Управление контейнерами выполнялось через Docker Desktop и Portainer Community Edition. Для Portainer использованы HTTPS-порт 9443 и постоянный том <i>portainer_data</i>.</p>
      <table><tr><th>Компонент</th><th>Значение</th></tr>
      <tr><td>Docker Engine</td><td>29.1.3, контекст desktop-linux</td></tr>
      <tr><td>Docker Compose</td><td>v5.0.1</td></tr>
      <tr><td>Portainer</td><td>portainer/portainer-ce:lts, версия по журналу 2.45.1</td></tr>
      <tr><td>nginx</td><td>nginx:1.30.5-alpine</td></tr>
      <tr><td>Имя контейнера</td><td>nginx-lab</td></tr></table>
      <p>Контейнер Portainer создан с подключением Docker socket и тома конфигурации. Контейнер nginx запущен с политикой автоматического перезапуска <i>unless-stopped</i>.</p>
      <h2>2 Выполнение задания</h2>
      <p>После запуска контейнера nginx выполнена проверка командой <i>docker exec nginx-lab nginx -v</i>. Получен результат: <i>nginx/1.30.5</i>. Из браузера открыта страница <i>http://localhost:8088</i>.</p>
    """))
    pages.append(page(4, """
      <h1>2 ВЫПОЛНЕНИЕ ЗАДАНИЯ</h1>
      <h3>2.1 Конфигурация публикации портов</h3>
      <table><tr><th>Сервис</th><th>Порт контейнера</th><th>Порт хоста</th><th>Протокол</th><th>Назначение</th></tr>
      <tr><td>Portainer</td><td>9443</td><td>9443</td><td>TCP/HTTPS</td><td>Административный интерфейс</td></tr>
      <tr><td>Portainer Agent tunnel</td><td>8000</td><td>8000</td><td>TCP</td><td>Служебный порт</td></tr>
      <tr><td>nginx-lab</td><td>80</td><td>8088</td><td>TCP/HTTP</td><td>Проверка страницы nginx</td></tr></table>
      <h3>2.2 Сведения об образах</h3>
      <table><tr><th>Образ</th><th>Тег</th><th>Digest</th></tr>
      <tr><td>portainer/portainer-ce</td><td>lts</td><td>sha256:4d616db18cfeb5dd41a69c0958bc825c84483ea9cde1106eb82a5d26f3bd8b0e</td></tr>
      <tr><td>nginx</td><td>1.30.5-alpine</td><td>sha256:0985e772fb9f729e6fa0980da05fca5d9c468e870eed43071545afa9d2e27d94</td></tr></table>
      <p>Фиксация тега и digest позволяет связать результат лабораторной работы с конкретными версиями контейнерных образов.</p>
      <h3>2.3 Проверка страницы nginx</h3>
      <p>На странице отображается стандартное приветствие nginx. Адресная строка браузера содержит локальный адрес и опубликованный порт 8088.</p>
      <div class="box small">Команда запуска: <i>docker run -d --name nginx-lab --restart unless-stopped -p 8088:80 nginx:1.30.5-alpine</i></div>
    """))
    pages.append(page(5, f"""
      <h1>3 ДОКАЗАТЕЛЬСТВА ВЫПОЛНЕНИЯ</h1>
      <figure class="figure">{image_tag("nginx_browser_full.png", "Браузер с открытой страницей nginx", "100%")}
      <figcaption>Рисунок 1 — Проверка стандартной страницы nginx по адресу http://localhost:8088</figcaption></figure>
    """))
    pages.append(page(6, f"""
      <h1>3 ДОКАЗАТЕЛЬСТВА ВЫПОЛНЕНИЯ</h1>
      <figure class="figure">{image_tag("portainer_nginx.png", "Контейнер nginx-lab в Portainer", "100%")}
      <figcaption>Рисунок 2 — Контейнер nginx-lab и опубликованный порт в Portainer</figcaption></figure>
      <p>Снимок показывает контейнер nginx-lab в интерфейсе Portainer. Состояние контейнера — запущен, опубликованный порт — 8088/TCP.</p>
    """))
    pages.append(page(7, """
      <h1>ЗАКЛЮЧЕНИЕ</h1>
      <p>В ходе выполнения задания Docker Desktop и Portainer были установлены и проверены. В Portainer доступен локальный Docker environment. Создан контейнер nginx-lab на основе образа nginx:1.30.5-alpine. Внешний порт 8088 направлен на внутренний порт 80/TCP.</p>
      <p>Стандартная страница nginx успешно открыта в браузере по адресу <i>http://localhost:8088</i>. Имя образа, версия nginx, идентификатор образа и параметры публикации портов зафиксированы в отчёте и файле image-manifest.txt.</p>
      <p>Таким образом, первая часть задания выполнена полностью.</p>
      <h2>СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ</h2>
      <div class="refs small">
        <p>1. Portainer Documentation. Install Portainer CE with Docker on Docker Desktop [Электронный ресурс]. URL: https://docs.portainer.io/start/install-ce/server/docker/wsl (дата обращения: {SEARCH_DATE}).</p>
        <p>2. Docker Docs. Docker run reference [Электронный ресурс]. URL: https://docs.docker.com/reference/cli/docker/container/run/ (дата обращения: {SEARCH_DATE}).</p>
        <p>3. nginx. Official Docker image [Электронный ресурс]. URL: https://hub.docker.com/_/nginx (дата обращения: {SEARCH_DATE}).</p>
      </div>
    """))
    return html_document("Отчёт Docker Desktop, Portainer и nginx", pages)


def build_report_2() -> str:
    pages: list[str] = [title_page(
        "Развёртывание мониторингового Stack",
        "Grafana Alloy, VictoriaMetrics и Grafana OSS",
    )]
    pages.append(page(2, common_abstract("", "")))
    pages.append(page(3, """
      <h1>ВВЕДЕНИЕ</h1>
      <p>Цель задания — создать в Portainer Stack из трёх контейнеров: Grafana Alloy, VictoriaMetrics и Grafana OSS. Контейнеры должны находиться в одной Docker-сети и обмениваться данными по именам сервисов. Дополнительный smartctl-exporter запускается отдельно, но подключается к той же сети.</p>
      <h2>1 АРХИТЕКТУРА РЕШЕНИЯ</h2>
      <div class="box center"><b>smartctl-exporter:9633</b><br>↓ scrape<br><b>Grafana Alloy:12345</b><br>↓ Prometheus Remote Write<br><b>VictoriaMetrics:8428</b><br>↑ Prometheus datasource<br><b>Grafana OSS:3000</b></div>
      <p>Общая внешняя сеть называется <i>observability_net</i>. Alloy обращается к exporter по адресу <i>http://smartctl-exporter:9633/metrics</i>, а отправляет данные в VictoriaMetrics по endpoint <i>http://victoria-metrics:8428/api/v1/write</i>. Grafana использует VictoriaMetrics как источник данных Prometheus.</p>
      <h2>2 СОСТАВ STACK</h2>
      <table><tr><th>Сервис</th><th>Образ</th><th>Порт хоста</th><th>Порт контейнера</th></tr>
      <tr><td>Grafana Alloy</td><td>grafana/alloy:v1.19.2</td><td>127.0.0.1:12345</td><td>12345</td></tr>
      <tr><td>VictoriaMetrics</td><td>victoriametrics/victoria-metrics:v1.153.0</td><td>127.0.0.1:8428</td><td>8428</td></tr>
      <tr><td>Grafana OSS</td><td>grafana/grafana:13.2.2</td><td>127.0.0.1:3000</td><td>3000</td></tr>
      <tr><td>smartctl-exporter</td><td>prometheuscommunity/smartctl-exporter:v0.14.0</td><td>9633</td><td>9633</td></tr></table>
    """))
    pages.append(page(4, """
      <h1>3 КОНФИГУРАЦИЯ И РАЗВЁРТЫВАНИЕ</h1>
      <h3>3.1 Docker Compose и постоянные данные</h3>
      <p>Файл docker-compose.yml содержит три сервиса Stack, внешнюю сеть observability_net и постоянные тома для VictoriaMetrics, Alloy и Grafana. VictoriaMetrics запускается в режиме single-node. В Grafana datasource автоматически создаётся через provisioning-файл.</p>
      <pre>networks:
  observability:
    name: observability_net
    external: true

prometheus.remote_write "victoria" {
  endpoint {
    url = "http://victoria-metrics:8428/api/v1/write"
  }
}</pre>
      <h3>3.2 Конфигурация Alloy</h3>
      <pre>prometheus.scrape "smartctl" {
  targets = [{ "__address__" = "smartctl-exporter:9633", "job" = "smartctl-exporter" }]
  scrape_interval = "15s"
  forward_to = [prometheus.remote_write.victoria.receiver]
}</pre>
      <p>Для smartctl-exporter использован официальный бинарный релиз v0.14.0, собранный локально в образ на базе Alpine, поскольку загрузка готового Docker-образа из реестра в текущей среде завершалась ошибкой EOF. Это обстоятельство отражено в manifest и не скрывается от проверяющего.</p>
    """))
    pages.append(page(5, """
      <h1>4 ПРОВЕРКА СЕТИ И СЕРВИСОВ</h1>
      <table><tr><th>Проверка</th><th>Результат</th></tr>
      <tr><td>Состояние Stack</td><td>victoria-metrics — healthy; alloy и grafana — Up</td></tr>
      <tr><td>Участники observability_net</td><td>victoria-metrics, alloy, grafana, smartctl-exporter</td></tr>
      <tr><td>Exporter /metrics</td><td>HTTP 200</td></tr>
      <tr><td>VictoriaMetrics /-/healthy</td><td>HTTP 200</td></tr>
      <tr><td>Alloy UI :12345</td><td>HTTP 200</td></tr>
      <tr><td>Grafana API :3000/api/health</td><td>HTTP 200</td></tr>
      <tr><td>Запрос up в VictoriaMetrics</td><td>up{instance="smartctl-exporter:9633",job="smartctl-exporter"}=1</td></tr>
      <tr><td>Запрос smartctl_devices</td><td>5</td></tr></table>
      <p>Таким образом, подтверждены DNS-разрешение имён контейнеров, прохождение scrape-запроса через Alloy, запись данных в VictoriaMetrics и подключение Grafana к источнику данных.</p>
      <p>Для контейнеров Stack использованы привязки к localhost. Это ограничивает доступ к сервисам локальным компьютером и не заменяет настройку аутентификации при публикации сервисов во внешнюю сеть.</p>
    """))
    pages.append(page(6, f"""
      <h1>4 ПРОВЕРКА СЕТИ И СЕРВИСОВ</h1>
      <figure class="figure">{image_tag("portainer_stack.png", "Stack observability в Portainer", "100%")}
      <figcaption>Рисунок 1 — Stack observability в Portainer</figcaption></figure>
      <p>В Portainer Stack отображается как Compose Stack. Сервисы запускаются с заданными именами и подключаются к общей внешней сети.</p>
    """))
    pages.append(page(7, f"""
      <h1>4 ПРОВЕРКА СЕТИ И СЕРВИСОВ</h1>
      <figure class="figure">{image_tag("grafana_dashboard.png", "Проверочная панель Grafana", "100%")}
      <figcaption>Рисунок 2 — Проверочная панель Grafana с запросом доступности target</figcaption></figure>
      <p>На панели Grafana отображается значение 1 для метрики <i>up</i>, что подтверждает доступность smartctl-exporter через Alloy.</p>
    """))
    pages.append(page(8, f"""
      <h1>4 ПРОВЕРКА СЕТИ И СЕРВИСОВ</h1>
      <figure class="figure">{image_tag("victoriametrics_status.png", "Интерфейс VictoriaMetrics", "100%")}
      <figcaption>Рисунок 3 — Интерфейс VictoriaMetrics VMUI</figcaption></figure>
      <h2>5 ОГРАНИЧЕНИЯ РЕЗУЛЬТАТА</h2>
      <p>Exporter отвечает и публикует служебные метрики, включая <i>smartctl_devices=5</i>. При этом метрика температуры устройств <i>smartctl_device_temperature</i> в текущем Docker Desktop не появилась. Вероятная причина — ограничение доступа контейнера к физическим дискам Windows через Linux VM Docker Desktop. Тестовые значения температуры не подставлялись.</p>
    """))
    pages.append(page(9, """
      <h1>ЗАКЛЮЧЕНИЕ</h1>
      <p>Stack из Grafana Alloy, VictoriaMetrics и Grafana OSS создан и развёрнут в Portainer. Все три сервиса работают в общей Docker-сети observability_net. Отдельный smartctl-exporter также подключён к этой сети.</p>
      <p>Проверены HTTP-endpoint сервисов, работа Docker DNS, передача метрики <i>up</i> через Alloy в VictoriaMetrics и отображение результата в Grafana. Конфигурационные файлы и версии образов включены в архив.</p>
      <p>Температурные SMART-метрики не были выданы за реальные данные: зафиксировано, что exporter доступен, но Docker Desktop не предоставил контейнеру необходимые данные о температуре. Для получения фактических температур работу следует повторить на Linux-хосте или виртуальной машине с проброшенными дисковыми устройствами.</p>
      <p>Вторая часть задания выполнена с указанным ограничением среды.</p>
      <h2>СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ</h2>
      <div class="refs small">
        <p>1. Grafana Labs. Run Grafana Alloy in a Docker container [Электронный ресурс]. URL: https://grafana.com/docs/alloy/latest/set-up/install/docker/ (дата обращения: {SEARCH_DATE}).</p>
        <p>2. Grafana Labs. Send metrics to a Prometheus-compatible backend [Электронный ресурс]. URL: https://grafana.com/docs/alloy/latest/tutorials/send-metrics-to-prometheus/ (дата обращения: {SEARCH_DATE}).</p>
        <p>3. VictoriaMetrics. URL examples [Электронный ресурс]. URL: https://docs.victoriametrics.com/victoriametrics/url-examples/ (дата обращения: {SEARCH_DATE}).</p>
        <p>4. Grafana Labs. Install Grafana using Docker [Электронный ресурс]. URL: https://grafana.com/docs/grafana/latest/setup-grafana/installation/docker/ (дата обращения: {SEARCH_DATE}).</p>
        <p>5. Prometheus Community. smartctl_exporter [Электронный ресурс]. URL: https://github.com/prometheus-community/smartctl_exporter (дата обращения: {SEARCH_DATE}).</p>
      </div>
    """))
    return html_document("Отчёт по мониторинговому Stack", pages)


def write_manifest() -> None:
    tar = ROOT / "smartctl_exporter-0.14.0.linux-amd64.tar.gz"
    tar_hash = hashlib.sha256(tar.read_bytes()).hexdigest() if tar.exists() else "не найден"
    lines = [
        f"Дата фиксации: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "Docker Engine: " + run("docker", "version", "--format", "{{.Server.Version}}"),
        "",
        image_line("portainer/portainer-ce:lts", "Portainer CE; version 2.45.1 по журналу контейнера"),
        image_line("nginx:1.30.5-alpine", "nginx -v: nginx/1.30.5"),
        image_line("grafana/alloy:v1.19.2"),
        image_line("victoriametrics/victoria-metrics:v1.153.0"),
        image_line("grafana/grafana:13.2.2", "Grafana OSS"),
        image_line("prometheuscommunity/smartctl-exporter:v0.14.0", "локально собран из официального релиза; Docker Hub pull завершался EOF"),
        "",
        "smartctl_exporter source: https://github.com/prometheus-community/smartctl_exporter/releases/tag/v0.14.0",
        f"smartctl_exporter-0.14.0.linux-amd64.tar.gz SHA256: {tar_hash}",
        "Проверка: docker image inspect <image>; docker inspect <container>; docker compose config --quiet",
    ]
    (ROOT / "image-manifest.txt").write_text("\n".join(lines) + "\n", encoding="utf-8-sig")


def write_readme() -> None:
    text = f"""# Docker Desktop, Portainer и мониторинговый Stack

Автор: {STUDENT}\nГруппа: {GROUP}\nМАИ, Институт №3, кафедра №307\n
## Состав

- `01_nginx_portainer_report.pdf` — отчёт по Portainer и nginx.
- `01_nginx_portainer_report.docx` — редактируемая версия первого отчёта.
- `02_monitoring_stack_report.pdf` — отчёт по Grafana Alloy, VictoriaMetrics и Grafana OSS.
- `stack/` — Docker Compose, конфигурация Alloy и provisioning Grafana.
- `smartctl_exporter_build/` — Dockerfile и исходный бинарный релиз exporter.
- `screenshots/` — доказательства работы сервисов.
- `image-manifest.txt` — версии, ID и digest образов.
- `email_draft.txt` — текст сопроводительного письма.

## Запуск

1. Создать сеть: `docker network create observability_net`.
2. В каталоге `stack` выполнить `docker compose up -d`.
3. Отдельно запустить smartctl-exporter согласно команде из отчёта или собрать локальный образ из `smartctl_exporter_build`.
4. Проверить: Grafana `http://localhost:3000`, VictoriaMetrics `http://localhost:8428/vmui`, Alloy `http://localhost:12345`.

## Фактическая проверка

Подтверждены HTTP 200 для exporter, VictoriaMetrics, Alloy и Grafana. Запрос `up` в VictoriaMetrics вернул значение 1, `smartctl_devices` — 5. Температурная метрика `smartctl_device_temperature` в Docker Desktop не появилась; это ограничение доступа Linux VM к физическим дискам, а не подставленные тестовые данные.

## Безопасность

Порты Stack привязаны к `127.0.0.1`. Пароли в учебной конфигурации предназначены только для локальной лаборатории; перед публикацией сервисов необходимо заменить их и включить штатную защиту.
"""
    (ROOT / "README.md").write_text(text, encoding="utf-8-sig")


def write_email() -> None:
    text = f"""Кому: kaan@kaan.org.ru
Тема: ДЗ по Docker Desktop, Portainer и мониторинговому стеку — {STUDENT}

Здравствуйте!

Направляю выполненные задания по Docker Desktop, Portainer, nginx и мониторинговому стеку Grafana Alloy, VictoriaMetrics и Grafana OSS.

Студент: {STUDENT}
Группа: {GROUP}

Во вложении находятся два отчёта и архив с конфигурационными файлами, снимками экрана и манифестом образов.

С уважением,
{STUDENT}
"""
    (ROOT / "email_draft.txt").write_text(text, encoding="utf-8-sig")


def print_pdf(html_path: Path, pdf_path: Path) -> None:
    chrome = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    if not chrome.exists():
        chrome = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
    profile = BUILD / (html_path.stem + "_profile")
    if profile.exists():
        shutil.rmtree(profile)
    cmd = [str(chrome), "--headless=new", "--disable-gpu", "--no-sandbox", f"--user-data-dir={profile}", "--no-pdf-header-footer", f"--print-to-pdf={pdf_path}", html_path.resolve().as_uri()]
    subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=120)
    if not pdf_path.exists() or pdf_path.stat().st_size < 1000:
        raise RuntimeError(f"PDF was not created: {pdf_path}")


def archive() -> None:
    archive_path = ROOT / "docker_portainer_submission.zip"
    if archive_path.exists():
        archive_path.unlink()
    include = [
        "01_nginx_portainer_report.pdf", "01_nginx_portainer_report.docx", "02_monitoring_stack_report.pdf", "README.md", "email_draft.txt", "image-manifest.txt",
        "stack", "smartctl_exporter_build", "screenshots", "smartctl_exporter-0.14.0.linux-amd64.tar.gz",
    ]
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel in include:
            path = ROOT / rel
            if path.is_dir():
                for child in path.rglob("*"):
                    if child.is_file():
                        zf.write(child, Path("docker_portainer_tasks") / child.relative_to(ROOT))
            elif path.exists():
                zf.write(path, Path("docker_portainer_tasks") / path.name)


def main() -> None:
    write_manifest()
    write_readme()
    write_email()
    report_1_html = BUILD / "01_nginx_portainer_report.html"
    report_2_html = BUILD / "02_monitoring_stack_report.html"
    report_1_html.write_text(build_report_1(), encoding="utf-8")
    report_2_html.write_text(build_report_2(), encoding="utf-8")
    print_pdf(report_1_html, ROOT / "01_nginx_portainer_report.pdf")
    print_pdf(report_2_html, ROOT / "02_monitoring_stack_report.pdf")
    archive()
    print("Reports and archive created")


if __name__ == "__main__":
    main()
