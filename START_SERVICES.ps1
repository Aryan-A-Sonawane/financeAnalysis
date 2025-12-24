# FinSightAI Service Startup Script
# This script starts all required services and tests connections

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  FinSightAI - Starting All Services" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "🔍 Checking Docker status..." -ForegroundColor Yellow
try {
    docker info | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    Write-Host "   Download from: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "🚀 Starting database and service containers..." -ForegroundColor Yellow
docker-compose up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Services started successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to start services" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "⏳ Waiting for services to be ready (30 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

Write-Host ""
Write-Host "🔍 Checking service status..." -ForegroundColor Yellow
docker-compose ps

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  Service URLs:" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  PostgreSQL:     localhost:5432" -ForegroundColor White
Write-Host "  NebulaGraph:    localhost:9669" -ForegroundColor White
Write-Host "  Weaviate:       http://localhost:8080" -ForegroundColor White
Write-Host "  MinIO:          http://localhost:9000" -ForegroundColor White
Write-Host "  MinIO Console:  http://localhost:9001" -ForegroundColor White
Write-Host "  Redis:          localhost:6379" -ForegroundColor White
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📊 Running connection tests..." -ForegroundColor Yellow
python scripts/health_check.py

Write-Host ""
Write-Host "🎉 Setup complete! You can now start the API server:" -ForegroundColor Green
Write-Host "   python -m uvicorn app.main:app --reload" -ForegroundColor Yellow
Write-Host ""
