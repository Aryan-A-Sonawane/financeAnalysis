# 🚀 COMPLETE STARTUP & DATABASE ACCESS GUIDE

## ⚡ Quick Actions After Docker Install

### **STEP 1: Restart Your Computer**
Docker needs a system restart to be available in PATH. After restart, continue below.

---

## 🎯 COMPLETE STARTUP SEQUENCE

### **Open PowerShell and run these commands:**

```powershell
# Navigate to project
cd E:\z.code\financeAnalysis\financeAnalysis

# Verify Docker is ready
docker --version

# Start all services
docker-compose up -d

# Wait for services to initialize (IMPORTANT!)
Start-Sleep -Seconds 60

# Check all services are running
docker-compose ps
```

**Expected Output - All should show "Up":**
```
NAME                STATUS          PORTS
postgres            Up              0.0.0.0:5432->5432/tcp
nebula-metad        Up              
nebula-storaged     Up              
nebula-graphd       Up              0.0.0.0:9669->9669/tcp
weaviate            Up              0.0.0.0:8080->8080/tcp
minio               Up              0.0.0.0:9000-9001->9000-9001/tcp
redis               Up              0.0.0.0:6379->6379/tcp
```

### **Test All Connections:**

```powershell
# Install database clients (if not installed)
pip install psycopg2-binary weaviate-client minio redis

# Run connection tests
python scripts/test_connections.py
```

**Expected: All 6 services should show ✅**

### **Initialize Databases:**

```powershell
# Create all schemas and tables
python scripts/setup_databases.py
```

### **Start the API:**

```powershell
# Start FastAPI server
python -m uvicorn app.main:app --reload --port 8000
```

**API is now running at:** http://localhost:8000/docs

---

## 🗄️ HOW TO ACCESS ALL DATABASES

### **1. PostgreSQL - Relational Database** 🐘

**View data in terminal:**
```powershell
docker exec -it postgres psql -U finsight_user -d finsight
```

**PostgreSQL Commands:**
```sql
-- List all tables
\dt

-- View all documents
SELECT * FROM documents;

-- View all policies  
SELECT * FROM policies;

-- View all claims
SELECT * FROM claims;

-- View users
SELECT * FROM users;

-- Count records
SELECT 
    (SELECT COUNT(*) FROM documents) as documents,
    (SELECT COUNT(*) FROM policies) as policies,
    (SELECT COUNT(*) FROM claims) as claims;

-- Exit
\q
```

**GUI Tools (Recommended):**

**Option A: DBeaver (Best Free Option)**
1. Download: https://dbeaver.io/download/
2. New Connection → PostgreSQL
3. Settings:
   - **Host**: localhost
   - **Port**: 5432
   - **Database**: finsight
   - **Username**: finsight_user
   - **Password**: secure_password
4. Click "Test Connection" → "Finish"

**Option B: VS Code Extension**
1. Install extension: "PostgreSQL" by Chris Kolkman
2. Add connection with above credentials
3. Browse tables directly in VS Code

---

### **2. NebulaGraph - Knowledge Graph** 🕸️

**View graph in terminal:**
```powershell
docker exec -it nebula-graphd nebula-console -addr graphd -port 9669 -u root -p nebula
```

**NebulaGraph Commands:**
```cypher
-- Use our space
USE finsight;

-- Show all entity types (tags)
SHOW TAGS;

-- Show all relationship types (edges)
SHOW EDGES;

-- View all policies
MATCH (p:Policy) RETURN p LIMIT 10;

-- View all claims
MATCH (c:Claim) RETURN c LIMIT 10;

-- View all coverages
MATCH (cov:Coverage) RETURN cov LIMIT 10;

-- Find policy coverage relationships
MATCH (p:Policy)-[r:COVERS]->(c:Coverage) 
RETURN p.policyNumber, c.serviceName, c.coveragePercentage 
LIMIT 10;

-- Find eligibility paths
MATCH path = (claim:Claim)-[:REFERENCES]->(policy:Policy)-[:COVERS]->(coverage:Coverage)
RETURN path LIMIT 5;

-- Count all entities
MATCH (n) RETURN labels(n) as type, COUNT(n) as count;

-- Exit
:exit
```

**GUI Tool: Nebula Studio** 🎨
```powershell
# Start Nebula Studio
docker run -d -p 7001:7001 --name nebula-studio vesoft/nebula-graph-studio:latest
```

**Access at:** http://localhost:7001
- **Host**: 127.0.0.1:9669
- **Username**: root
- **Password**: nebula
- **Space**: finsight

**Features:**
- Visual graph exploration
- Click on nodes to see relationships
- Run queries with autocomplete
- Export graph visualizations

---

### **3. Weaviate - Vector Database** 🔍

**Query via Python:**
```powershell
python
```

```python
import weaviate

# Connect
client = weaviate.Client("http://localhost:8080")

# Check connection
print("Connected:", client.is_ready())

# View schema
schema = client.schema.get()
for cls in schema['classes']:
    print(f"Class: {cls['class']}")

# Query documents
result = client.query.get(
    "Document", 
    ["content", "documentType", "metadata"]
).with_limit(10).do()
print(result)

# Semantic search
result = client.query.get(
    "Document", 
    ["content", "documentType"]
).with_near_text({
    "concepts": ["medical claim surgery"]
}).with_limit(5).do()

for item in result['data']['Get']['Document']:
    print(item)

# Count objects
result = client.query.aggregate("Document").with_meta_count().do()
print("Total documents:", result)
```

**Query via REST API:**
```powershell
# View schema
curl http://localhost:8080/v1/schema | ConvertFrom-Json | ConvertTo-Json -Depth 10

# Count documents
curl http://localhost:8080/v1/objects?class=Document | ConvertFrom-Json

# Get specific document
curl http://localhost:8080/v1/objects/Document/{uuid} | ConvertFrom-Json
```

**Weaviate Console:**

Access at: http://localhost:8080/v1/console

Or install Weaviate Cloud Console and connect to localhost:8080

---

### **4. MinIO - Document Storage** 📦

**Access Web Console:**

**URL**: http://localhost:9001

**Login:**
- **Username**: minioadmin
- **Password**: minioadmin

**What you can do:**
- Browse all uploaded documents
- View buckets (should see `finsight-documents`)
- Download files
- Upload test files
- Check storage usage
- Manage access policies

**CLI Access:**
```powershell
# List all buckets
docker exec -it minio mc ls local/

# List files in bucket
docker exec -it minio mc ls local/finsight-documents/

# Download a file
docker exec -it minio mc cp local/finsight-documents/filename.pdf ./downloads/
```

---

### **5. Redis - Cache** ⚡

**View cache data:**
```powershell
docker exec -it redis redis-cli
```

**Redis Commands:**
```redis
# View all keys
KEYS *

# Get a cached value
GET some_key

# View cache statistics
INFO stats

# View memory usage
INFO memory

# Monitor real-time commands
MONITOR

# Clear all cache (⚠️ careful!)
FLUSHALL

# Exit
exit
```

**GUI Tool: RedisInsight**

1. Download: https://redis.com/redis-enterprise/redis-insight/
2. Add database:
   - **Host**: localhost
   - **Port**: 6379
   - **Name**: FinSightAI Cache

---

## 🎮 HOW TO RUN THE PROJECT

### **Method 1: Swagger UI (Easiest)** 📚

**URL**: http://localhost:8000/docs

**Features:**
- Interactive API documentation
- Try all endpoints directly in browser
- No coding required
- See request/response schemas
- Built-in authentication

**Steps:**
1. Open http://localhost:8000/docs
2. Click "Authorize" button (top right)
3. Get token from `/auth/login` endpoint
4. Paste token in authorization dialog
5. Try any endpoint!

---

### **Method 2: HTTP Test Files** 🧪

**Prerequisites:**
```powershell
# Install REST Client extension in VS Code
code --install-extension humao.rest-client
```

**Test Files:**

```powershell
# General API tests
code API_TESTS.http

# Workflow tests (document processing, eligibility)
code WORKFLOW_TESTS.http

# Vector & graph search tests
code VECTOR_GRAPH_TESTS.http
```

**How to use:**
1. Open any `.http` file in VS Code
2. You'll see `Send Request` above each HTTP request
3. Click it to execute
4. Response appears in new tab
5. Tests include authentication, upload, processing, search

---

### **Method 3: Python Script** 🐍

**Create test script:**
```powershell
code test_api.py
```

```python
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# 1. Login
response = requests.post(f"{BASE_URL}/auth/login", json={
    "username": "admin",
    "password": "admin123"
})
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print(f"✅ Logged in, token: {token[:20]}...")

# 2. Upload document
with open("data/samples/sample_claim.txt", "rb") as f:
    files = {"file": f}
    response = requests.post(
        f"{BASE_URL}/documents/upload",
        headers=headers,
        files=files
    )
doc = response.json()
print(f"✅ Uploaded document: {doc['document_id']}")

# 3. Process document with workflow
response = requests.post(
    f"{BASE_URL}/workflows/process-document",
    headers=headers,
    json={
        "document_id": doc['document_id'],
        "workflow_type": "document_processing"
    }
)
workflow = response.json()
print(f"✅ Started workflow: {workflow['workflow_id']}")

# 4. Semantic search
response = requests.post(
    f"{BASE_URL}/search/semantic",
    headers=headers,
    json={
        "query": "medical claim for surgery",
        "limit": 5
    }
)
results = response.json()
print(f"✅ Found {len(results['results'])} similar documents")

# 5. Fraud detection
response = requests.post(
    f"{BASE_URL}/fraud/analyze",
    headers=headers,
    json={
        "claim_id": doc['document_id']
    }
)
fraud = response.json()
print(f"✅ Fraud analysis: {fraud['fraud_score']}/100 risk")

print("\n🎉 All tests passed!")
```

**Run it:**
```powershell
python test_api.py
```

---

### **Method 4: cURL Commands** 💻

```powershell
# Login
$response = curl -X POST http://localhost:8000/api/v1/auth/login `
  -H "Content-Type: application/json" `
  -d '{"username":"admin","password":"admin123"}' | ConvertFrom-Json

$token = $response.access_token

# Upload document
curl -X POST http://localhost:8000/api/v1/documents/upload `
  -H "Authorization: Bearer $token" `
  -F "file=@data/samples/sample_claim.txt"

# Semantic search
curl -X POST http://localhost:8000/api/v1/search/semantic `
  -H "Authorization: Bearer $token" `
  -H "Content-Type: application/json" `
  -d '{"query":"medical claim","limit":5}'
```

---

## 🎯 ACCESS POINTS FOR ALL FEATURES

### **1. Document Processing** 📄

**Where to access:**
- **Upload**: POST `/api/v1/documents/upload` (Swagger UI)
- **View in DB**: PostgreSQL `documents` table
- **View in Storage**: MinIO console http://localhost:9001
- **Search**: POST `/api/v1/search/semantic`

**Features:**
- ✅ OCR extraction (Tesseract + PaddleOCR)
- ✅ Document classification (5 types)
- ✅ Entity extraction
- ✅ Storage in MinIO

---

### **2. AI Agent Workflows** 🤖

**Where to access:**
- **Start workflow**: POST `/api/v1/workflows/process-document`
- **Check status**: GET `/api/v1/workflows/{id}`
- **View results**: PostgreSQL + NebulaGraph

**Available workflows:**
- ✅ **Document Processing**: Full 7-agent pipeline
- ✅ **Eligibility Check**: Policy + claim analysis

**7 AI Agents:**
1. Document Classifier
2. Invoice Extractor
3. Policy Parser
4. Claims/Benefits Analyzer
5. Eligibility Reasoner
6. Fraud Detector
7. Compliance Validator

---

### **3. Vector Search** 🔍

**Where to access:**
- **Semantic search**: POST `/api/v1/search/semantic`
- **Hybrid search**: POST `/api/v1/search/hybrid`
- **Similar docs**: POST `/api/v1/search/similar`
- **View data**: Weaviate python client or REST API

**Features:**
- ✅ OpenAI embeddings (1536 dimensions)
- ✅ Semantic similarity search
- ✅ Hybrid (vector + keyword) search
- ✅ Similar document discovery

---

### **4. Knowledge Graph** 🕸️

**Where to access:**
- **View relationships**: GET `/api/v1/search/graph/relationships/{id}`
- **Coverage paths**: POST `/api/v1/search/graph/coverage-path`
- **Similar claims**: POST `/api/v1/search/graph/similar-claims`
- **Graph stats**: GET `/api/v1/search/graph/stats`
- **Explore**: NebulaGraph console or Studio

**Features:**
- ✅ Entity extraction with LLM
- ✅ Relationship mapping
- ✅ Coverage reasoning paths
- ✅ Similar claim detection

---

### **5. Fraud Detection** 🚨

**Where to access:**
- **Analyze**: POST `/api/v1/fraud/analyze`
- **Patterns**: GET `/api/v1/fraud/patterns`
- **View in DB**: PostgreSQL `claims` table

**Features:**
- ✅ Pattern-based detection
- ✅ Risk scoring (0-100)
- ✅ Fraud indicators
- ✅ Historical comparison

---

### **6. Eligibility Checking** ✅

**Where to access:**
- **Check eligibility**: POST `/api/v1/eligibility/check`
- **Cost estimate**: POST `/api/v1/eligibility/estimate`
- **Workflow**: POST `/api/v1/workflows/check-eligibility`

**Features:**
- ✅ Policy coverage validation
- ✅ Graph-based reasoning
- ✅ Coverage path analysis
- ✅ Cost estimation

---

### **7. Policy Management** 📋

**Where to access:**
- **Parse policy**: POST `/api/v1/policy/parse`
- **Get policy**: GET `/api/v1/policy/{id}`
- **Check coverage**: POST `/api/v1/policy/coverage`
- **View in DB**: PostgreSQL `policies` table + NebulaGraph

---

## 🔗 Complete URL Reference

| Feature | URL | Access Method |
|---------|-----|---------------|
| **API Documentation** | http://localhost:8000/docs | Browser |
| **API Alternative Docs** | http://localhost:8000/redoc | Browser |
| **PostgreSQL GUI** | localhost:5432 | DBeaver/pgAdmin |
| **NebulaGraph Studio** | http://localhost:7001 | Browser (after starting) |
| **NebulaGraph Console** | localhost:9669 | Terminal |
| **Weaviate API** | http://localhost:8080 | REST/Python |
| **MinIO Console** | http://localhost:9001 | Browser |
| **Redis** | localhost:6379 | redis-cli/RedisInsight |

---

## 📊 View Data After Processing

### **After uploading a document:**

**1. Check PostgreSQL:**
```sql
-- View document metadata
SELECT * FROM documents ORDER BY created_at DESC LIMIT 5;

-- View extracted entities
SELECT * FROM entities WHERE document_id = 'your-doc-id';
```

**2. Check NebulaGraph:**
```cypher
USE finsight;

-- View document as node
MATCH (d:Document {documentId: 'your-doc-id'}) RETURN d;

-- View all relationships
MATCH (d:Document {documentId: 'your-doc-id'})-[r]->(n) RETURN d, r, n;
```

**3. Check Weaviate:**
```python
# Search for your document
result = client.query.get("Document", ["content"]) \
    .with_where({"path": ["documentId"], "operator": "Equal", "valueText": "your-doc-id"}) \
    .do()
print(result)
```

**4. Check MinIO:**
- Open http://localhost:9001
- Navigate to `finsight-documents` bucket
- See your uploaded file

---

## ✅ Quick Verification Checklist

After startup, verify everything works:

```powershell
# 1. Services running
docker-compose ps  # All should be "Up"

# 2. Connections work
python scripts/test_connections.py  # 6/6 should be green

# 3. API responds
curl http://localhost:8000/health | ConvertFrom-Json

# 4. Can access UIs
# - http://localhost:8000/docs (API)
# - http://localhost:9001 (MinIO)

# 5. Databases initialized
docker exec -it postgres psql -U finsight_user -d finsight -c "\dt"
```

---

## 🎉 YOU'RE READY!

Your complete FinSightAI platform is now running with:
- ✅ All databases accessible
- ✅ Multiple access methods (GUI, CLI, API)
- ✅ 30+ API endpoints ready
- ✅ 7 AI agents operational
- ✅ Complete document processing pipeline

**Start processing documents now!** 🚀
