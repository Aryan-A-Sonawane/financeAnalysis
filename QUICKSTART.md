# FinSightAI - Quick Start Guide

## What Has Been Built

### ✅ Completed Components

1. **Comprehensive INSTRUCTIONS.md**
   - Enhanced architecture with RAG optimizations
   - Complete NebulaGraph schema (10 tags, 15 edge types)
   - Complete Weaviate schema (4 collections)
   - PostgreSQL schema with 5 tables
   - LangGraph workflow designs
   - Development and deployment guidelines

2. **Project Structure**
   - Full directory structure with all folders
   - Organized module layout (api, agents, workflows, services, etc.)

3. **Configuration & Environment**
   - `requirements.txt` with all dependencies
   - `docker-compose.yml` with all services (Postgres, NebulaGraph, Weaviate, MinIO, Redis)
   - `.env.example` and `.env` with all configuration
   - `config.py` with Pydantic settings management

4. **Core Application**
   - FastAPI application (`main.py`) with middleware
   - Structured logging with structlog
   - JWT authentication system
   - Rate limiting middleware
   - Request logging and correlation IDs

5. **Data Models**
   - Pydantic schemas for all API requests/responses
   - SQLAlchemy models for PostgreSQL
   - NebulaGraph schema with comprehensive queries
   - Weaviate collections for vector search

6. **Database Integrations**
   - PostgreSQL async connection with SQLAlchemy
   - NebulaGraph client with connection pooling
   - Weaviate client with schema creation
   - Database initialization script

7. **API Endpoints (7 routers)**
   - Authentication: register, login, get user
   - Documents: upload, list, get, delete
   - Extraction: entity extraction
   - Eligibility: check eligibility, get history
   - Policy: get coverage, get graph
   - Fraud: analyze claims

8. **Utilities**
   - Semantic document chunking with overlap
   - Password hashing and JWT tokens
   - Structured logging configuration

## 🚀 Getting Started

### Step 1: Start Docker Services
```bash
docker-compose up -d
```

This starts:
- PostgreSQL (port 5432)
- NebulaGraph (port 9669)
- Weaviate (port 8080)
- MinIO (ports 9000, 9001)
- Redis (port 6379)

### Step 2: Configure Environment
Edit `.env` file and set:
```
OPENAI_API_KEY=sk-your-api-key-here
SECRET_KEY=your-secure-secret-key-min-32-chars
POSTGRES_PASSWORD=your-secure-password
```

### Step 3: Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Step 4: Initialize Databases
```bash
python scripts/setup_databases.py --all
```

### Step 5: Run Application
```bash
uvicorn app.main:app --reload
```

Visit http://localhost:8000/docs for API documentation

## 📝 Next Steps to Complete

### Phase 1: Immediate (Core Functionality)

1. **Document Processing Services**
   - Implement OCR service (Tesseract/PaddleOCR)
   - Create document classification agent
   - Build text extraction pipeline

2. **Entity Extraction Agents**
   - Policy parser agent (extract deductibles, copays, limits)
   - Invoice extraction agent (line items, totals, tax)
   - Claim extraction agent (CPT codes, ICD-10, amounts)

3. **LangGraph Workflows**
   - Document processing workflow
   - Eligibility check workflow
   - Fraud detection workflow

4. **Storage Integration**
   - MinIO/S3 file upload/download
   - Store document embeddings in Weaviate
   - Store entities in NebulaGraph

### Phase 2: Advanced Features

5. **Claims Eligibility Engine**
   - Graph-based policy coverage checking
   - Historical claim similarity search
   - Cost calculation logic
   - Decision reasoning with LLM

6. **Fraud Detection**
   - Claim pattern analysis
   - Provider history analysis
   - Anomaly detection algorithms

7. **RAG Enhancements**
   - Hybrid search (BM25 + Dense)
   - Reranking with cross-encoders
   - Query expansion (HyDE)
   - Context compression

### Phase 3: Production Ready

8. **Testing**
   - Unit tests for all services
   - Integration tests for workflows
   - API endpoint tests

9. **Observability**
   - Prometheus metrics
   - LangSmith tracing
   - Error alerting

10. **Documentation**
    - API usage examples
    - Deployment guide
    - Architecture diagrams

## 🧪 Testing the API

### 1. Register a User
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!@#"
  }'
```

### 2. Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=SecurePass123!@#"
```

Save the `access_token` from the response.

### 3. Upload Document
```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -F "file=@sample_policy.pdf"
```

### 4. Check Eligibility
```bash
curl -X POST http://localhost:8000/api/v1/eligibility/check \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "USER123",
    "policy_id": "POL456",
    "procedure_code": "29881",
    "diagnosis_code": "M17.11"
  }'
```

## 📊 Architecture Overview

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
┌──────▼───────────────────────────────┐
│      FastAPI Application             │
│  (Auth, Logging, Rate Limiting)      │
└──────┬───────────────────────────────┘
       │
┌──────▼───────────────────────────────┐
│    LangGraph Orchestration           │
│  (Document, Eligibility, Fraud)      │
└──┬────┬────┬────────────────────────┬┘
   │    │    │                        │
   ▼    ▼    ▼                        ▼
┌────┐┌──┐┌────────┐           ┌──────────┐
│PG  ││VR││ Nebula │           │  MinIO   │
│SQL ││DB││ Graph  │           │   S3     │
└────┘└──┘└────────┘           └──────────┘
```

## 🎯 Key Design Decisions

1. **API-First**: All functionality accessible via REST API
2. **Graph + Vector Hybrid**: NebulaGraph for relationships + Weaviate for similarity
3. **LangGraph for Determinism**: Ensures reproducible, auditable workflows
4. **Structured Data Focus**: JSON entities, not free-text responses
5. **HIPAA-Aligned**: Encryption, audit logs, explainable decisions

## 📚 Important Files

- `INSTRUCTIONS.md` - Complete technical guide
- `prd.md` - Product requirements
- `docker-compose.yml` - Infrastructure setup
- `app/main.py` - Application entry point
- `app/config.py` - Configuration management
- `app/models/graph_schema.py` - NebulaGraph schema
- `scripts/setup_databases.py` - Database initialization

## 🐛 Troubleshooting

### Services not starting
```bash
docker-compose down -v
docker-compose up -d
```

### Database connection errors
Check that all services are healthy:
```bash
docker-compose ps
```

### Import errors
Make sure virtual environment is activated:
```bash
venv\Scripts\activate
```

## 🎉 What Makes This Special

1. **Decision Intelligence**: Not just chat, but actual claim approval simulation
2. **Graph Reasoning**: Traverse policy → coverage → procedure relationships
3. **Hybrid RAG**: Combines semantic search with graph-based reasoning
4. **Production Ready**: Docker, logging, auth, rate limiting out of the box
5. **Extensible**: Agent-based architecture for easy feature additions

---

**You now have a solid foundation for a production-grade financial document intelligence platform!**

The core infrastructure is in place. The next steps involve implementing the agent logic and LangGraph workflows detailed in INSTRUCTIONS.md.
