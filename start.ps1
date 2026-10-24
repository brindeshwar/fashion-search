<#
.SYNOPSIS
    One-command start for Fashion Search (Windows): sets up whatever is missing, then serves.

.DESCRIPTION
    Each step is skipped when its result already exists, so after the first run this just
    starts the server. Steps: Python venv + packages, web build, search index, server.

.PARAMETER WithTryOn
    Also install virtual try-on and download its weights (~3.2 GB, needs an NVIDIA GPU).

.PARAMETER Port
    Port for the web app (default 8000).

.PARAMETER SetupOnly
    Do the setup steps, then exit without starting the server.

.EXAMPLE
    .\start.ps1
    .\start.ps1 -WithTryOn
    .\start.ps1 -SetupOnly
#>
param(
    [switch]$WithTryOn,
    [int]$Port = 8000,
    [switch]$SetupOnly
)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

function Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Need($cmd, $hint) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) { throw "$cmd not found. $hint" }
}
# Windows PowerShell's 'Stop' preference ignores native programs, so check exit codes.
function Run {
    $exe, $rest = $args
    & $exe @rest
    if ($LASTEXITCODE -ne 0) { throw "Failed (exit $LASTEXITCODE): $exe $rest" }
}
function PortInUse($p) {
    $c = New-Object System.Net.Sockets.TcpClient
    try { $c.Connect('127.0.0.1', $p); $true } catch { $false } finally { $c.Close() }
}

# A running server locks .venv\Scripts\fashion-search.exe, which breaks reinstalls.
if (PortInUse $Port) {
    throw "Port $Port is already in use. Is Mirror already running? Stop it first, or use -Port."
}

$py = '.venv\Scripts\python.exe'
$cli = '.venv\Scripts\fashion-search.exe'

if (-not (Test-Path $py)) {
    Need 'python' 'Install Python 3.10+ from https://www.python.org/downloads/'
    Step 'Creating Python environment (.venv)'
    Run python -m venv .venv
    Run $py -m pip install --upgrade pip
    # Pick the PyTorch build: CUDA if an NVIDIA GPU is present, otherwise CPU.
    $torchIndex = if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) { 'cu126' } else { 'cpu' }
    Step "Installing PyTorch ($torchIndex)"
    Run $py -m pip install torch torchvision --index-url "https://download.pytorch.org/whl/$torchIndex"
    Step 'Installing fashion-search'
    Run $py -m pip install -e .
}

if ($WithTryOn) {
    $check = 'from fashion_search import tryon, garment; print(tryon.is_available() and garment.weights_ready())'
    $tryonReady = (& $py -c $check 2>$null) -eq 'True'
    if (-not $tryonReady) {
        Step 'Installing virtual try-on and downloading weights (~3.2 GB)'
        Run $py -m pip install -e '.[tryon]'
        Run $cli tryon-download
    }
}

if (-not (Test-Path 'web\dist\index.html')) {
    Need 'npm' 'Install Node.js 20+ from https://nodejs.org/'
    Step 'Building the web app'
    Run npm --prefix web ci
    Run npm --prefix web run build
}

if (-not (Test-Path 'artifacts\index\embeddings.npy')) {
    $photos = Get-ChildItem 'data\shirts' -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension -match '^\.(jpe?g|png|webp|bmp)$' }
    if (-not $photos) {
        throw "No garment photos found. Put JPG/PNG/WEBP photos in data\shirts\ (see data\README.md), then run this again."
    }
    Step "Indexing $($photos.Count) photos"
    Run $cli index
}

if ($SetupOnly) { Step 'Setup complete'; exit 0 }

Step "Starting Mirror on http://127.0.0.1:$Port  (Ctrl+C to stop)"
Start-Job { Start-Sleep 3; Start-Process "http://127.0.0.1:$using:Port" } | Out-Null
& $cli serve --port $Port
