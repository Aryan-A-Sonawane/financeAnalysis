# Quick Fix & Setup Guide

## Current Issue
**Docker is not installed** - The project requires Docker Desktop to run database services (PostgreSQL, NebulaGraph, Weaviate, MinIO, Redis).

## Quick Demo (Without Docker)

Run the simplified demo version:

```powershell
C:/Users/Aryan/AppData/Local/Programs/Python/Python314/python.exe app/demo.py
```

Then open: http://localhost:8000/docs

This will show you:
- ✅ API structure and documentation
- ✅ Health endpoints
- ✅ Project information
- ⚠️  Database features disabled (need Docker)

## Full Installation (Recommended for Meeting)

### Step 1: Install Docker Desktop

1. Download: https://www.docker.com/products/docker-desktop
2. Install and restart your computer
3. Start Docker Desktop
4. Wait for "Docker Desktop is running" status

### Step 2: Start Services

```powershell
# Start all database services
docker compose up -d

# Wait 30 seconds
Start-Sleep -Seconds 30

# Check services are running
docker compose ps
```

Expected output - all should show "Up":
```
NAME                          STATUS
finsight-postgres             Up
finsight-nebula-metad         Up  
finsight-nebula-storaged      Up
finsight-nebula-graphd        Up
finsight-weaviate             Up
finsight-minio                Up
finsight-redis                Up
```

### Step 3: Set OpenAI API Key

Edit `.env` file and add your OpenAI API key:
```env
OPENAI_API_KEY=sk-your-real-api-key-here
```

Get your key from: https://platform.openai.com/api-keys

### Step 4: Initialize Databases

```powershell
C:/Users/Aryan/AppData/Local/Programs/Python/Python314/python.exe scripts/setup_databases.py
```

### Step 5: Start Full API

```powershell
C:/Users/Aryan/AppData/Local/Programs/Python/Python314/python.exe -m uvicorn app.main:app --reload
```

Then open: http://localhost:8000/docs

## Test the API (Full Version with Docker)

1. **Register User**: POST `/api/v1/auth/register`
   ```json
   {
     "email": "demo@example.com",
     "password": "SecurePass123!",
     "full_name": "Demo User"
   }
   ```

2. **Login**: POST `/api/v1/auth/login`
   - Copy the `access_token`

3. **Authorize**: Click green lock icon, paste token

4. **Upload Document**: POST `/api/v1/documents/upload`
   - Upload: `data/samples/sample_claim.txt`
   - See extracted entities!

## If Docker Install Fails

Use the demo mode to show:
- API documentation structure
- Endpoint organization
- Authentication flow
- Request/response schemas

For your meeting, you can explain:
- "Here's the API structure (show Swagger UI)"
- "These are the 40+ endpoints we've built"
- "Here's how document processing works (explain flow)"
- "Docker services provide the backend (show docker-compose.yml)"

## Troubleshooting

### "Docker command not found"
- Install Docker Desktop first
- Restart PowerShell after installation

### "Port already in use"
```powershell
# Find what's using port 8000
netstat -ano | findstr :8000

# Kill it (replace PID)
taskkill /PID <PID> /F
```

### "Module not found" errors
```powershell
# Reinstall dependencies
C:/Users/Aryan/AppData/Local/Programs/Python/Python314/python.exe -m pip install -r requirements.txt
```

## What's Working Right Now

✅ Python environment configured  
✅ All dependencies installed  
✅ Demo API ready to run  
✅ Code structure complete  
✅ Sample documents created  
⚠️  Need Docker for full functionality  

## Quick Command Reference

```powershell
# Run demo API (no Docker needed)
C:/Users/Aryan/AppData/Local/Programs/Python/Python314/python.exe app/demo.py

# Start Docker services (when Docker installed)
docker compose up -d

# Stop Docker services
docker compose down

# Check service status
docker compose ps

# View service logs
docker compose logs <service-name>

# Run full API (needs Docker)
C:/Users/Aryan/AppData/Local/Programs/Python/Python314/python.exe -m uvicorn app.main:app --reload
```
