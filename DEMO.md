# Quick Demo Guide - FinSightAI Platform

## Prerequisites Check

```powershell
# Check Python version (need 3.10+)
python --version

# Check Docker
docker --version
docker-compose --version
```

## Step 1: Set Up Environment

```powershell
# Navigate to project directory
cd E:\z.code\financeAnalysis\financeAnalysis

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configure Environment Variables

Create a `.env` file with these minimal settings:

```env
# Database
POSTGRES_PASSWORD=your_secure_password_here
DATABASE_URL=postgresql+asyncpg://finsight_user:your_secure_password_here@localhost:5432/finsight

# OpenAI (REQUIRED)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Security
SECRET_KEY=your-super-secret-jwt-key-change-this-in-production-min-32-chars
```

## Step 3: Start Infrastructure Services

```powershell
# Start all backend services (PostgreSQL, NebulaGraph, Weaviate, MinIO, Redis)
docker-compose up -d

# Wait 30 seconds for services to initialize
Start-Sleep -Seconds 30

# Check service status
docker-compose ps
```

Expected output - all services should show "Up":
```
NAME                          STATUS
financeanalysis-graphd-1      Up
financeanalysis-metad-1       Up  
financeanalysis-minio-1       Up
financeanalysis-postgres-1    Up
financeanalysis-redis-1       Up
financeanalysis-storaged-1    Up
financeanalysis-weaviate-1    Up
```

## Step 4: Initialize Databases

```powershell
# Run database setup script
python scripts/setup_databases.py
```

Expected output:
```
✓ PostgreSQL tables created
✓ NebulaGraph space and schema created
✓ Weaviate collections created
```

## Step 5: Start FastAPI Application

```powershell
# Start the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

## Step 6: Test the API

### Option A: Using Browser

1. Open browser: http://localhost:8000/docs
2. You'll see interactive Swagger UI with all endpoints

### Option B: Using PowerShell (Detailed Testing)

Open a **NEW PowerShell window** and run:

```powershell
# Test 1: Health Check
curl http://localhost:8000/health

# Test 2: Register a User
$registerBody = @{
    email = "demo@example.com"
    password = "SecurePassword123!"
    full_name = "Demo User"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/register" `
    -Method POST `
    -Body $registerBody `
    -ContentType "application/json"

Write-Host "User registered: $($response.email)"

# Test 3: Login and Get Token
$loginBody = @{
    username = "demo@example.com"
    password = "SecurePassword123!"
} | ConvertTo-Json

$loginResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" `
    -Method POST `
    -Body $loginBody `
    -ContentType "application/json"

$token = $loginResponse.access_token
Write-Host "Access Token: $token"

# Test 4: Upload a Document (create a test file first)
# Create a simple test PDF
Add-Content -Path "test_invoice.txt" -Value @"
INVOICE

Invoice Number: INV-2024-001
Date: December 16, 2024
Due Date: January 15, 2025

Bill To:
John Doe
123 Main Street
New York, NY 10001

Provider:
ABC Medical Center
456 Health Ave
New York, NY 10002
Tax ID: 12-3456789

Services:
- Office Visit (99213): $150.00
- Lab Test (80053): $75.00
- X-Ray (71020): $200.00

Subtotal: $425.00
Tax (8%): $34.00
Total: $459.00
Amount Paid: $0.00
Balance Due: $459.00
"@

# Upload the document
$headers = @{
    "Authorization" = "Bearer $token"
}

$uploadResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/documents/upload" `
    -Method POST `
    -Headers $headers `
    -Form @{
        file = Get-Item "test_invoice.txt"
    }

Write-Host "`n=== DOCUMENT PROCESSED ==="
Write-Host "Document ID: $($uploadResponse.document_id)"
Write-Host "Type: $($uploadResponse.message)"
Write-Host "Status: $($uploadResponse.status)"
```

## Step 7: View Results in Services

### PostgreSQL Database
```powershell
# Connect to PostgreSQL
docker exec -it financeanalysis-postgres-1 psql -U finsight_user -d finsight

# View documents
SELECT document_id, filename, document_type, classification_confidence, processing_status FROM documents;

# View extracted entities (pretty print)
SELECT document_id, filename, jsonb_pretty(extracted_entities) FROM documents;

# Exit
\q
```

### MinIO Storage UI
1. Open browser: http://localhost:9001
2. Login with:
   - Username: `minioadmin`
   - Password: `minioadmin`
3. Browse to `finsight-documents` bucket
4. You'll see your uploaded files organized by user ID

### Weaviate UI
1. Open browser: http://localhost:8080/v1/schema
2. You'll see JSON schema for collections

### NebulaGraph Studio
1. Open browser: http://localhost:7001
2. Connect with:
   - Host: `127.0.0.1:9669`
   - Username: `root`
   - Password: `nebula`
3. Select space: `finsight`

## Demo Flow for Your Meeting

### 1. **Show API Documentation** (30 seconds)
- Open http://localhost:8000/docs
- Scroll through endpoints: Auth, Documents, Extraction, Eligibility, Fraud

### 2. **Register & Login** (1 minute)
- Use Swagger UI "Try it out" buttons
- Register endpoint: `/api/v1/auth/register`
- Login endpoint: `/api/v1/auth/login`
- Copy the access token

### 3. **Upload Document** (2 minutes)
- Click "Authorize" button (top right, green lock icon)
- Paste token, click "Authorize"
- Use `/api/v1/documents/upload` endpoint
- Upload a sample insurance document or invoice
- Show the response with extracted entities

### 4. **Show Database Results** (1 minute)
- Open MinIO UI - show uploaded file
- Run PostgreSQL query - show extracted data
- Demonstrate data persistence

## Stopping Services

```powershell
# Stop FastAPI (Ctrl+C in the terminal)

# Stop all Docker services
docker-compose down

# Or stop without removing containers
docker-compose stop
```

## Troubleshooting

### Services not starting?
```powershell
# Check logs
docker-compose logs postgres
docker-compose logs weaviate

# Restart specific service
docker-compose restart postgres
```

### Port already in use?
```powershell
# Check what's using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID)
taskkill /PID <PID> /F
```

### Database connection errors?
- Ensure `.env` has correct `POSTGRES_PASSWORD`
- Wait 30 seconds after `docker-compose up` before running the app
- Check: `docker-compose logs postgres`

### OpenAI API errors?
- Verify `OPENAI_API_KEY` in `.env` is valid
- Check you have API credits: https://platform.openai.com/usage

## Quick Architecture Overview for Meeting

**Tech Stack:**
- **API:** FastAPI + Python 3.10+
- **Databases:** PostgreSQL (metadata), NebulaGraph (knowledge graph), Weaviate (vector search)
- **Storage:** MinIO (S3-compatible)
- **AI:** OpenAI GPT-4 (extraction), Tesseract/PaddleOCR (OCR)
- **Orchestration:** LangGraph (coming in next phase)

**Current Capabilities:**
✅ Document upload (PDF, DOCX, images)
✅ OCR text extraction (digital + scanned)
✅ Document classification (5 types: policy, claim, EOB, invoice, receipt)
✅ Entity extraction (policy details, claim info, invoice line items)
✅ Medical code extraction (ICD-10, CPT, HCPCS)
✅ Secure storage with JWT authentication

**Coming Next:**
- LangGraph agent workflows
- Claims eligibility reasoning
- Fraud detection
- Graph-based policy coverage analysis
