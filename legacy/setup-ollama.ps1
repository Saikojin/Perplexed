# Ollama Quick Setup Script for Windows
# This script sets up Ollama for Riddle Master

Write-Host ""
Write-Host "╔═══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                                           ║" -ForegroundColor Cyan
Write-Host "║         🤖  OLLAMA SETUP  🤖             ║" -ForegroundColor Cyan
Write-Host "║                                           ║" -ForegroundColor Cyan
Write-Host "║     AI Riddle Generation Setup            ║" -ForegroundColor Cyan
Write-Host "║                                           ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check Docker
Write-Host "Checking Docker..." -ForegroundColor Yellow
$dockerRunning = docker ps 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Docker is not running" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and run this script again" -ForegroundColor Yellow
    exit 1
}
Write-Host "✓ Docker is running" -ForegroundColor Green

# Stop existing Ollama container if running
Write-Host ""
Write-Host "Checking for existing Ollama container..." -ForegroundColor Yellow
$existing = docker ps -a --filter "name=riddle-ollama" --format "{{.Names}}" 2>$null
if ($existing -eq "riddle-ollama") {
    Write-Host "Stopping and removing existing container..." -ForegroundColor Yellow
    docker stop riddle-ollama 2>$null | Out-Null
    docker rm riddle-ollama 2>$null | Out-Null
    Write-Host "✓ Removed existing container" -ForegroundColor Green
}

# Start Ollama container
Write-Host ""
Write-Host "Starting Ollama container..." -ForegroundColor Yellow
docker run -d --name riddle-ollama -p 11434:11434 ollama/ollama:latest 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to start Ollama container" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Ollama container started" -ForegroundColor Green

# Wait for Ollama to be ready
Write-Host ""
Write-Host "Waiting for Ollama to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Verify Ollama is responding
$retries = 0
$maxRetries = 10
$ollamaReady = $false

while ($retries -lt $maxRetries -and -not $ollamaReady) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $ollamaReady = $true
        }
    } catch {
        $retries++
        Start-Sleep -Seconds 2
    }
}

if (-not $ollamaReady) {
    Write-Host "✗ Ollama is not responding" -ForegroundColor Red
    Write-Host "Check Docker logs: docker logs riddle-ollama" -ForegroundColor Yellow
    exit 1
}
Write-Host "✓ Ollama is ready" -ForegroundColor Green

# Pull neural-chat model
Write-Host ""
Write-Host "Pulling neural-chat model (this may take 2-5 minutes)..." -ForegroundColor Yellow
Write-Host "Model size: ~3.8 GB" -ForegroundColor Cyan

docker exec riddle-ollama ollama pull neural-chat
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to pull model" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Model downloaded successfully" -ForegroundColor Green

# Verify model is available
Write-Host ""
Write-Host "Verifying model installation..." -ForegroundColor Yellow
$models = docker exec riddle-ollama ollama list 2>$null
if ($models -match "neural-chat") {
    Write-Host "✓ Neural-chat model is ready" -ForegroundColor Green
} else {
    Write-Host "✗ Model verification failed" -ForegroundColor Red
    exit 1
}

# Test generation
Write-Host ""
Write-Host "Testing riddle generation..." -ForegroundColor Yellow
Write-Host "(This may take 5-10 seconds on first run)" -ForegroundColor Cyan

$testPrompt = @"
Generate a simple riddle.

Format your response EXACTLY as follows:
RIDDLE: [the riddle question here]
ANSWER: [the one-word or short phrase answer here]

Example:
RIDDLE: I speak without a mouth and hear without ears. What am I?
ANSWER: echo

Now generate a new riddle:
"@

$payload = @{
    model = "neural-chat"
    prompt = $testPrompt
    stream = $false
    options = @{
        temperature = 0.8
        max_tokens = 200
    }
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "http://localhost:11434/api/generate" -Method Post -Body $payload -ContentType "application/json" -TimeoutSec 30
    $generatedText = $response.response
    
    if ($generatedText -match "RIDDLE:" -and $generatedText -match "ANSWER:") {
        Write-Host "✓ Test generation successful!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Sample output:" -ForegroundColor Cyan
        Write-Host $generatedText -ForegroundColor White
    } else {
        Write-Host "! Generation succeeded but format may need adjustment" -ForegroundColor Yellow
    }
} catch {
    Write-Host "✗ Test generation failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Backend will use fallback LLM if Ollama fails" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host "✓ Ollama Setup Complete!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "Container: riddle-ollama" -ForegroundColor White
Write-Host "Port: 11434" -ForegroundColor White
Write-Host "Model: neural-chat" -ForegroundColor White
Write-Host "Status: Running" -ForegroundColor Green
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Yellow
Write-Host "  Check status:  docker ps | findstr ollama" -ForegroundColor White
Write-Host "  View logs:     docker logs riddle-ollama -f" -ForegroundColor White
Write-Host "  Stop Ollama:   docker stop riddle-ollama" -ForegroundColor White
Write-Host "  Start Ollama:  docker start riddle-ollama" -ForegroundColor White
Write-Host "  List models:   docker exec riddle-ollama ollama list" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Run .\dev.bat to start all services" -ForegroundColor White
Write-Host "  2. Backend will automatically use Ollama for riddle generation" -ForegroundColor White
Write-Host "  3. Check docs\OLLAMA_SETUP.md for more information" -ForegroundColor White
Write-Host ""
