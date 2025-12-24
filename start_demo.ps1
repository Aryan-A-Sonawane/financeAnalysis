# Quick Start Script for FinSightAI Demo
# Run this script to start everything and see a working demo

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  FinSightAI Platform - Quick Demo  " -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
if (-Not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Creating .env file from template..." -ForegroundColor Yellow
    
    # Create minimal .env
    @"
# Database
POSTGRES_PASSWORD=finsight_secure_password_123
DATABASE_URL=postgresql+asyncpg://finsight_user:finsight_secure_password_123@localhost:5432/finsight

# OpenAI (YOU MUST SET THIS!)
OPENAI_API_KEY=sk-your-api-key-here

# Security
SECRET_KEY=finsight-super-secret-jwt-key-change-this-in-production-minimum-32-characters
ENCRYPTION_KEY=finsight-encryption-key-32-chars

# MinIO
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin

# Redis
REDIS_PASSWORD=
"@ | Out-File -FilePath ".env" -Encoding UTF8
    
    Write-Host "✅ .env file created!" -ForegroundColor Green
    Write-Host ""
    Write-Host "⚠️  IMPORTANT: Edit .env and add your OPENAI_API_KEY!" -ForegroundColor Red
    Write-Host "    Get your key from: https://platform.openai.com/api-keys" -ForegroundColor Yellow
    Write-Host ""
    $response = Read-Host "Press Enter when you've added your OpenAI API key (or type 'skip' to continue anyway)"
    if ($response -eq 'skip') {
        Write-Host "⚠️  Continuing without OpenAI key - entity extraction won't work!" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Step 1: Starting Docker services..." -ForegroundColor Yellow
Write-Host "This may take 30-60 seconds..." -ForegroundColor Gray

# Start Docker Compose (try both old and new commands)
try {
    docker compose up -d
} catch {
    docker-compose up -d
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start Docker services!" -ForegroundColor Red
    Write-Host "Make sure Docker Desktop is running." -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Docker services started" -ForegroundColor Green

# Wait for services to be ready
Write-Host ""
Write-Host "Step 2: Waiting for services to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Check if Python venv exists
Write-Host ""
Write-Host "Step 3: Checking Python environment..." -ForegroundColor Yellow

if (-Not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Gray
    python -m venv venv
    
    Write-Host "Installing dependencies (this may take 2-3 minutes)..." -ForegroundColor Gray
    .\venv\Scripts\Activate.ps1
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️  Some packages failed to install" -ForegroundColor Yellow
        Write-Host "You may need to install system dependencies for OCR" -ForegroundColor Yellow
    } else {
        Write-Host "✅ Dependencies installed" -ForegroundColor Green
    }
} else {
    Write-Host "✅ Virtual environment exists" -ForegroundColor Green
    .\venv\Scripts\Activate.ps1
}

# Initialize databases
Write-Host ""
Write-Host "Step 4: Initializing databases..." -ForegroundColor Yellow

try {
    python scripts/setup_databases.py
    Write-Host "✅ Databases initialized" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Database initialization had warnings (may be normal if already initialized)" -ForegroundColor Yellow
}

# Check services
Write-Host ""
Write-Host "Step 5: Checking service health..." -ForegroundColor Yellow
python scripts/health_check.py

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  🚀 Ready to Start!  " -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start the API server, run:" -ForegroundColor Yellow
Write-Host "  uvicorn app.main:app --reload" -ForegroundColor White
Write-Host ""
Write-Host "Then open your browser to:" -ForegroundColor Yellow
Write-Host "  http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Sample documents for testing:" -ForegroundColor Yellow
Write-Host "  - data/samples/sample_claim.txt" -ForegroundColor White
Write-Host "  - data/samples/sample_policy.txt" -ForegroundColor White
Write-Host ""
Write-Host "Web UIs available:" -ForegroundColor Yellow
Write-Host "  - MinIO Storage:    http://localhost:9001 (minioadmin/minioadmin)" -ForegroundColor White
Write-Host "  - NebulaGraph:      http://localhost:7001" -ForegroundColor White
Write-Host "  - Weaviate:         http://localhost:8080/v1/schema" -ForegroundColor White
Write-Host ""

$startNow = Read-Host "Start API server now? (y/n)"
if ($startNow -eq 'y' -or $startNow -eq 'Y' -or $startNow -eq '') {
    Write-Host ""
    Write-Host "Starting API server..." -ForegroundColor Green
    Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
    Write-Host ""
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
}
