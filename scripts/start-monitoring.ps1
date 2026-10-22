[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$EspIp = "10.175.10.230",

    [switch]$SkipEspCheck,

    [switch]$OpenBrowser
)

$ErrorActionPreference = "Stop"

if ($EspIp -notmatch '^\d{1,3}(\.\d{1,3}){3}$') {
    throw "EspIp must be an IPv4 address, for example 10.175.10.230"
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$composeDir = Join-Path $repoRoot "stack"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker command was not found. Install and start Docker Desktop first."
}

Write-Host "Checking Docker Desktop..." -ForegroundColor Cyan
docker info *> $null
if ($LASTEXITCODE -ne 0) {
    throw "Docker Engine is not running. Start Docker Desktop and run this script again."
}

if (-not $SkipEspCheck) {
    Write-Host "Checking ESP8266 at http://$EspIp/metrics ..." -ForegroundColor Cyan
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri "http://$EspIp/metrics" -TimeoutSec 5
        if ($response.StatusCode -ne 200 -or $response.Content -notmatch "esp8266_temperature_celsius") {
            throw "The response does not contain ESP8266 temperature metrics."
        }
        Write-Host "ESP8266 exporter is reachable." -ForegroundColor Green
    }
    catch {
        throw "ESP8266 is not reachable at $EspIp. Check Wi-Fi/IP or use -SkipEspCheck. $($_.Exception.Message)"
    }
}

$env:ESP8266_IP = $EspIp

Write-Host "Checking Docker network observability_net..." -ForegroundColor Cyan
docker network inspect observability_net *> $null
if ($LASTEXITCODE -ne 0) {
    docker network create observability_net | Out-Host
}

Push-Location $composeDir
try {
    Write-Host "Starting VictoriaMetrics, Alloy and Grafana..." -ForegroundColor Cyan
    docker compose up -d
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose failed to start the stack."
    }

    $deadline = (Get-Date).AddSeconds(90)
    $health = ""
    while ((Get-Date) -lt $deadline) {
        $health = (docker inspect -f "{{.State.Health.Status}}" victoria-metrics 2>$null) -join ""
        if ($health -eq "healthy") {
            break
        }
        Start-Sleep -Seconds 2
    }

    if ($health -ne "healthy") {
        docker compose ps
        throw "VictoriaMetrics did not become healthy within 90 seconds."
    }

    Write-Host ""
    Write-Host "Stack is ready." -ForegroundColor Green
    Write-Host "Grafana:          http://localhost:3000"
    Write-Host "VictoriaMetrics:  http://localhost:8428/vmui"
    Write-Host "Alloy:            http://localhost:12345"
    Write-Host ""

    if ($OpenBrowser) {
        Start-Process "http://localhost:3000"
    }

    Write-Output "http://localhost:3000"
}
finally {
    Pop-Location
}
