#!/usr/bin/env bash
set -Eeuo pipefail

ESP_IP="\${ESP8266_IP:-10.175.10.230}"
SKIP_ESP_CHECK=0
OPEN_BROWSER=0

usage() {
    cat <<'USAGE'
Usage:
  ./scripts/start-monitoring.sh [options]

Options:
  --esp-ip ADDRESS       ESP8266 IPv4 address (default: 10.175.10.230)
  --skip-esp-check       Start Docker even when ESP cannot be reached
  --open-browser         Open Grafana after the stack becomes ready
  -h, --help             Show this help
USAGE
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --esp-ip)
            [[ $# -ge 2 ]] || { echo "Missing value for --esp-ip" >&2; exit 2; }
            ESP_IP="$2"
            shift 2
            ;;
        --skip-esp-check)
            SKIP_ESP_CHECK=1
            shift
            ;;
        --open-browser)
            OPEN_BROWSER=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

if [[ ! "$ESP_IP" =~ ^[0-9]{1,3}(\.[0-9]{1,3}){3}$ ]]; then
    echo "ESP_IP must be an IPv4 address, for example 10.175.10.230" >&2
    exit 2
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "\${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
COMPOSE_DIR="$REPO_ROOT/stack"

if ! command -v docker >/dev/null 2>&1; then
    echo "Docker was not found. Install Docker Engine and Docker Compose first." >&2
    exit 1
fi

echo "Checking Docker Engine..."
if ! docker info >/dev/null 2>&1; then
    echo "Docker Engine is not running. Start Docker and run this script again." >&2
    exit 1
fi

if (( ! SKIP_ESP_CHECK )); then
    echo "Checking ESP8266 at http://$ESP_IP/metrics ..."
    response="$(curl -fsS --connect-timeout 3 --max-time 5 "http://$ESP_IP/metrics")" || {
        echo "ESP8266 is not reachable at $ESP_IP. Check Wi-Fi/IP or use --skip-esp-check." >&2
        exit 1
    }
    if ! grep -q "esp8266_temperature_celsius" <<<"$response"; then
        echo "ESP8266 response does not contain temperature metrics." >&2
        exit 1
    fi
    echo "ESP8266 exporter is reachable."
fi

export ESP8266_IP="$ESP_IP"

echo "Checking Docker network observability_net..."
if ! docker network inspect observability_net >/dev/null 2>&1; then
    docker network create observability_net >/dev/null
fi

echo "Starting VictoriaMetrics, Alloy and Grafana..."
(
    cd "$COMPOSE_DIR"
    docker compose up -d
)

deadline=$((SECONDS + 90))
health=""
while (( SECONDS < deadline )); do
    health="$(docker inspect -f '{{.State.Health.Status}}' victoria-metrics 2>/dev/null || true)"
    if [[ "$health" == "healthy" ]]; then
        break
    fi
    sleep 2
done

if [[ "$health" != "healthy" ]]; then
    docker compose -f "$COMPOSE_DIR/docker-compose.yml" ps
    echo "VictoriaMetrics did not become healthy within 90 seconds." >&2
    exit 1
fi

echo
echo "Stack is ready."
echo "Grafana:          http://localhost:3000"
echo "VictoriaMetrics:  http://localhost:8428/vmui"
echo "Alloy:            http://localhost:12345"
echo

if (( OPEN_BROWSER )) && command -v xdg-open >/dev/null 2>&1; then
    xdg-open "http://localhost:3000" >/dev/null 2>&1 &
fi

printf '%s\n' "http://localhost:3000"
