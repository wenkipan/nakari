# Nakari Docker
param([string]$Command = 'start')

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectRoot

function Show-Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Blue }
function Show-OK($msg) { Write-Host "[OK] $msg" -ForegroundColor Green }
function Show-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Show-Err($msg) { Write-Host "[ERROR] $msg" -ForegroundColor Red }

function Test-DockerReady {
    docker info 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { Show-OK 'Docker ready'; return $true }
    Show-Err 'Docker not running'
    return $false
}

function Test-EnvFile {
    if (-not (Test-Path '.env')) {
        Show-Warn '.env not found'
        if (Test-Path '.env.example') { Copy-Item '.env.example' '.env'; Show-Warn 'Edit .env' }
        else { Show-Err '.env.example not found'; exit 1 }
    }
    Show-OK '.env ready'
}

function Wait-Services {
    Show-Info 'Waiting...'
    for ($i = 0; $i -lt 30; $i++) {
        docker compose exec -T neo4j wget -q --spider http://localhost:7474 2>$null
        if ($LASTEXITCODE -eq 0) { Show-OK 'Neo4j ready'; break }
        Write-Host '.' -NoNewline; Start-Sleep 2
    }
    for ($i = 0; $i -lt 30; $i++) {
        $p = docker compose exec -T redis redis-cli ping 2>$null
        if ($p -match 'PONG') { Show-OK 'Redis ready'; break }
        Write-Host '.' -NoNewline; Start-Sleep 1
    }
}

function Start-Svc {
    if (-not (Test-DockerReady)) { exit 1 }
    Test-EnvFile
    Show-Info 'Starting...'
    docker compose up -d
    Wait-Services
    Write-Host ''
    Show-OK '=== Nakari Started ==='
    Show-Info 'Neo4j: http://localhost:7474 (neo4j/password123)'
    Show-Info 'Demo: .\scripts\docker-start.ps1 demo'
}

function Stop-Svc { Show-Info 'Stopping...'; docker compose down; Show-OK 'Stopped' }
function Show-Logs { docker compose logs -f }
function Enter-Shell { docker compose exec app bash }
function Run-Demo { Show-Info 'Running demo...'; docker compose exec app python scripts/demo_memory.py }
function Run-Tests { Show-Info 'Running tests...'; docker compose exec app pytest tests/ -v }
function Clear-All { docker compose down -v --rmi local }
function Show-Help { Write-Host 'Commands: start stop restart logs shell demo test clean help' }

$c = $Command.ToLower()
if ($c -eq 'start') { Start-Svc }
elseif ($c -eq 'stop') { Stop-Svc }
elseif ($c -eq 'restart') { Stop-Svc; Start-Svc }
elseif ($c -eq 'logs') { Show-Logs }
elseif ($c -eq 'shell') { Enter-Shell }
elseif ($c -eq 'demo') { Run-Demo }
elseif ($c -eq 'test') { Run-Tests }
elseif ($c -eq 'clean') { Clear-All }
elseif ($c -eq 'help') { Show-Help }
else { Start-Svc }
