# FinSightAI - Quick Setup Guide

## ✅ Current Status

Your OpenAI API key has been configured in `.env` file.

## 📋 Next Steps to Get the System Running

### Step 1: Install Docker Desktop (Required)

**Download and install Docker Desktop:**
- **Windows**: https://www.docker.com/products/docker-desktop/
- After installation, **restart your computer**
- Start Docker Desktop - it will run in the background

### Step 2: Start All Services

Once Docker is running, execute:

```powershell
# Start all database and service containers
docker-compose up -d

# Wait 30-60 seconds for services to initialize
Start-Sleep -Seconds 45

# Check service status
docker-compose ps
```

### Step 3: Verify Connections

```powershell
# Run the connection test script
python scripts/test_connections.py
```

Expected output:
```
✅ PostgreSQL      [OK]   Connected - PostgreSQL 15.x
✅ Redis           [OK]   Connected - Redis 7.x
✅ Weaviate        [OK]   Connected - Weaviate 1.22.x
✅ NebulaGraph     [OK]   Connected - NebulaGraph cluster active
✅ MinIO           [OK]   Connected - Bucket 'finsight-documents' created
✅ OpenAI API      [OK]   Connected - Embedding dimension: 1536

✅ All services are healthy! (6/6)
```

### Step 4: Initialize Databases

```powershell
# Create database schemas and graph spaces
python scripts/setup_databases.py
```

### Step 5: Start the API Server

```powershell
# Start the FastAPI server
python -m uvicorn app.main:app --reload
```

Then open: **http://localhost:8000/docs**

---

## 🗃️ Service Information

| Service | URL | Credentials |
|---------|-----|-------------|
| **PostgreSQL** | `localhost:5432` | User: `finsight_user`<br>Password: `secure_password`<br>Database: `finsight` |
| **NebulaGraph** | `localhost:9669` | User: `root`<br>Password: `nebula`<br>Space: `finsight` |
| **Weaviate** | `http://localhost:8080` | No auth required |
| **MinIO** | `http://localhost:9000`<br>Console: `http://localhost:9001` | Access Key: `minioadmin`<br>Secret Key: `minioadmin`<br>Bucket: `finsight-documents` |
| **Redis** | `localhost:6379` | No auth required |
| **OpenAI** | API | Configured in `.env` |

---

## 🧪 Testing the System

### Quick API Test

```powershell
# Test document upload endpoint
curl -X POST "http://localhost:8000/api/v1/documents/upload" `
  -H "Authorization: Bearer demo-token" `
  -F "file=@data/samples/sample_claim.txt"
```

### Run Full Test Suite

```powershell
# Test workflows
code WORKFLOW_TESTS.http

# Test vector & graph features
code VECTOR_GRAPH_TESTS.http
```

Use the **REST Client** extension in VS Code to execute HTTP tests.

---

## 🔍 Troubleshooting

### Docker not found
```powershell
docker : The term 'docker' is not recognized...
```
**Solution**: Install Docker Desktop and restart your computer.

### Services not starting
```powershell
docker-compose up -d  # Check for errors
docker-compose logs   # View service logs
```

### Port conflicts
If ports are already in use, modify `docker-compose.yml`:
```yaml
ports:
  - "5433:5432"  # Change host port
```

### OpenAI API errors
- Verify key in `.env` file
- Check API quota: https://platform.openai.com/usage
- Test key: https://platform.openai.com/playground

---

## 📊 System Architecture Overview

```
┌─────────────────┐
│   FastAPI App   │  ← Your application
└────────┬────────┘
         │
    ┌────┴─────────────────────────────┐
    │                                  │
┌───▼────────┐                  ┌──────▼─────────┐
│ Databases  │                  │   AI Services  │
├────────────┤                  ├────────────────┤
│ PostgreSQL │ ← Metadata       │ OpenAI GPT-4   │ ← LLM
│ NebulaGraph│ ← Knowledge Graph│ text-embed-3   │ ← Embeddings
│ Weaviate   │ ← Vector Search  └────────────────┘
│ MinIO      │ ← Document Storage
│ Redis      │ ← Caching
└────────────┘
```

---

## 🚀 Next Steps After Setup

1. **Upload a test document**: Use the `/api/v1/documents/upload` endpoint
2. **Run document processing workflow**: `/api/v1/workflows/process-document`
3. **Test semantic search**: `/api/v1/search/semantic`
4. **Explore knowledge graph**: `/api/v1/search/graph/relationships`
5. **Check fraud detection**: `/api/v1/fraud/analyze`

---

## 📚 Documentation

- **Complete Instructions**: [INSTRUCTIONS.md](INSTRUCTIONS.md)
- **Workflow Guide**: [WORKFLOWS.md](WORKFLOWS.md)
- **Vector & Graph Integration**: [VECTOR_GRAPH_INTEGRATION.md](VECTOR_GRAPH_INTEGRATION.md)
- **API Documentation**: http://localhost:8000/docs (when server is running)

---

## 🔧 Environment Configuration

All credentials are in `.env` file. Current settings:

```env
✅ OPENAI_API_KEY=sk-proj-... (configured)
✅ POSTGRES_PASSWORD=secure_password
✅ NEBULA_PASSWORD=nebula
✅ MINIO_ACCESS_KEY=minioadmin
✅ REDIS (no password required)
```

To change any credentials, edit `.env` and restart services:
```powershell
docker-compose down
docker-compose up -d
```

---

## 💡 Quick Commands Cheat Sheet

```powershell
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Restart a specific service
docker-compose restart postgres

# Check service health
python scripts/test_connections.py

# Start API server
python -m uvicorn app.main:app --reload

# Run demo mode (no Docker needed)
python app/demo.py
```

---

## 🎯 Current Implementation Status

✅ **Complete** (13,000+ lines of code):
- Core services (OCR, document processing, extraction)
- 7 LangGraph AI agents
- 2 orchestrated workflows
- Vector store integration (Weaviate)
- Knowledge graph extraction (NebulaGraph)
- Search APIs (semantic, hybrid, graph queries)
- Complete API with authentication

⏸️ **Waiting for Docker**:
- Database connections
- End-to-end testing
- Document upload flow

---

**Need Help?** Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues and solutions.
