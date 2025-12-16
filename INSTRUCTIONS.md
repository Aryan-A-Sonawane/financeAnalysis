# FinSightAI - Build Instructions & Architecture Guide

## Table of Contents
1. [Enhanced Architecture](#enhanced-architecture)
2. [Database Schemas](#database-schemas)
3. [RAG Optimization Strategies](#rag-optimization-strategies)
4. [LangGraph Workflows](#langgraph-workflows)
5. [Project Structure](#project-structure)
6. [Setup Instructions](#setup-instructions)
7. [Development Workflow](#development-workflow)
8. [Testing Strategy](#testing-strategy)
9. [Deployment](#deployment)

---

## 1. Enhanced Architecture

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Frontend Dashboard (Optional)                │
│                    (React/Next.js + TailwindCSS)                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API Gateway (FastAPI)                         │
│  - Authentication (OAuth2/JWT)                                   │
│  - Rate Limiting (Redis)                                         │
│  - Request Validation (Pydantic)                                 │
│  - API Versioning (/v1/)                                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              LangGraph Orchestration Layer                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Document Processing Pipeline                             │  │
│  │  1. Classifier → 2. Parser → 3. Extractor → 4. Validator │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Reasoning Pipeline                                       │  │
│  │  1. Retrieval → 2. Graph Query → 3. LLM Reasoning        │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Eligibility Pipeline                                     │  │
│  │  1. Policy Check → 2. Coverage Match → 3. Decision       │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
            │                    │                    │
            ▼                    ▼                    ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│   Weaviate       │  │  NebulaGraph     │  │  PostgreSQL      │
│  (Vector Store)  │  │  (Knowledge      │  │  (Metadata,      │
│                  │  │   Graph)         │  │   Audit Logs)    │
│  - Embeddings    │  │  - Entities      │  │  - Users         │
│  - Chunks        │  │  - Relations     │  │  - Documents     │
│  - Similarity    │  │  - Rules         │  │  - API Logs      │
└──────────────────┘  └──────────────────┘  └──────────────────┘
            │                    │                    │
            └────────────────────┴────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   Object Storage │
                    │   (MinIO/S3)     │
                    │  - Raw Documents │
                    │  - Processed     │
                    └──────────────────┘
```

### 1.2 Enhanced Components

#### 1.2.1 Document Processing Layer
- **Pre-processing**: Image enhancement, deskewing, noise removal
- **OCR Engine**: Tesseract + PaddleOCR (ensemble for better accuracy)
- **Layout Analysis**: DocTR for table detection, form fields
- **Document Chunking**: Semantic chunking with overlap (500 tokens, 100 overlap)

#### 1.2.2 RAG Enhancement Layer
- **Hybrid Retrieval**: BM25 + Dense Retrieval (score fusion)
- **Reranking**: Cross-encoder for top-k refinement
- **Context Compression**: LLMLingua for token optimization
- **Query Expansion**: HyDE (Hypothetical Document Embeddings)

#### 1.2.3 Graph Reasoning Layer
- **Entity Linking**: Connect extracted entities to graph nodes
- **Path Finding**: Cypher/nGQL queries for eligibility traversal
- **Rule Engine**: Graph-based business rules
- **Conflict Detection**: Identify contradictory policies

#### 1.2.4 Observability Stack
- **Metrics**: Prometheus + Grafana
- **Tracing**: LangSmith / LangFuse
- **Logging**: Structured logging (JSON) with correlation IDs
- **Alerting**: Alert on anomalies, errors, latency spikes

---

## 2. Database Schemas

### 2.1 NebulaGraph Schema

#### 2.1.1 Tag (Node) Definitions

```ngql
-- User/Policyholder
CREATE TAG IF NOT EXISTS User (
  user_id string NOT NULL,
  name string,
  dob date,
  ssn_hash string,  -- Encrypted
  created_at timestamp
);

-- Insurance Policy
CREATE TAG IF NOT EXISTS Policy (
  policy_id string NOT NULL,
  policy_number string NOT NULL,
  policy_type string,  -- HMO, PPO, EPO, POS
  carrier string,
  effective_date date,
  expiration_date date,
  premium decimal,
  deductible_individual decimal,
  deductible_family decimal,
  oop_max_individual decimal,  -- Out-of-pocket max
  oop_max_family decimal,
  coinsurance_rate decimal,
  network_type string,
  created_at timestamp
);

-- Coverage/Benefit
CREATE TAG IF NOT EXISTS Coverage (
  coverage_id string NOT NULL,
  coverage_type string,  -- Medical, Dental, Vision, Rx
  service_category string,  -- Preventive, Emergency, Surgery, etc.
  is_preventive bool,
  requires_preauth bool,
  copay decimal,
  coinsurance decimal,
  annual_limit decimal,
  visit_limit int
);

-- Medical Procedure
CREATE TAG IF NOT EXISTS Procedure (
  procedure_id string NOT NULL,
  cpt_code string,
  hcpcs_code string,
  description string,
  category string,
  avg_cost decimal
);

-- Diagnosis
CREATE TAG IF NOT EXISTS Diagnosis (
  diagnosis_id string NOT NULL,
  icd10_code string NOT NULL,
  description string,
  category string,
  is_chronic bool
);

-- Healthcare Provider
CREATE TAG IF NOT EXISTS Provider (
  provider_id string NOT NULL,
  npi string NOT NULL,  -- National Provider Identifier
  name string,
  specialty string,
  address string,
  network_status string  -- In-Network, Out-of-Network
);

-- Claim
CREATE TAG IF NOT EXISTS Claim (
  claim_id string NOT NULL,
  claim_number string,
  submission_date date,
  service_date date,
  billed_amount decimal,
  allowed_amount decimal,
  paid_amount decimal,
  patient_responsibility decimal,
  status string,  -- Submitted, Processing, Approved, Denied, Paid
  denial_reason string,
  created_at timestamp
);

-- Exclusion/Limitation
CREATE TAG IF NOT EXISTS Exclusion (
  exclusion_id string NOT NULL,
  exclusion_type string,  -- Procedure, Diagnosis, Provider
  description string,
  effective_date date,
  expiration_date date
);

-- Document
CREATE TAG IF NOT EXISTS Document (
  document_id string NOT NULL,
  doc_type string,  -- Policy, Claim, EOB, Invoice
  file_path string,
  upload_date timestamp,
  processed bool
);

-- Invoice/Receipt
CREATE TAG IF NOT EXISTS Invoice (
  invoice_id string NOT NULL,
  invoice_number string,
  vendor string,
  invoice_date date,
  total_amount decimal,
  tax_amount decimal,
  status string
);
```

#### 2.1.2 Edge (Relationship) Definitions

```ngql
-- User -> Policy
CREATE EDGE IF NOT EXISTS HAS_POLICY (
  enrollment_date date,
  status string  -- Active, Inactive, Cancelled
);

-- Policy -> Coverage
CREATE EDGE IF NOT EXISTS PROVIDES_COVERAGE (
  priority int,  -- Primary, Secondary
  conditions string  -- Special conditions
);

-- Coverage -> Procedure
CREATE EDGE IF NOT EXISTS COVERS_PROCEDURE (
  coverage_percentage decimal,
  requires_preauth bool,
  restrictions string
);

-- Coverage -> Diagnosis
CREATE EDGE IF NOT EXISTS COVERS_DIAGNOSIS (
  coverage_percentage decimal,
  limitations string
);

-- Policy -> Exclusion
CREATE EDGE IF NOT EXISTS HAS_EXCLUSION (
  applies_to string
);

-- Exclusion -> Procedure
CREATE EDGE IF NOT EXISTS EXCLUDES_PROCEDURE ();

-- Exclusion -> Diagnosis
CREATE EDGE IF NOT EXISTS EXCLUDES_DIAGNOSIS ();

-- Claim -> Policy
CREATE EDGE IF NOT EXISTS CLAIMED_UNDER (
  deductible_applied decimal,
  coinsurance_applied decimal
);

-- Claim -> Procedure
CREATE EDGE IF NOT EXISTS FOR_PROCEDURE (
  quantity int
);

-- Claim -> Diagnosis
CREATE EDGE IF NOT EXISTS FOR_DIAGNOSIS ();

-- Claim -> Provider
CREATE EDGE IF NOT EXISTS SERVICED_BY (
  is_network bool
);

-- Provider -> Procedure
CREATE EDGE IF NOT EXISTS PERFORMS_PROCEDURE (
  frequency int
);

-- Document -> Policy
CREATE EDGE IF NOT EXISTS DESCRIBES_POLICY ();

-- Document -> Claim
CREATE EDGE IF NOT EXISTS DESCRIBES_CLAIM ();

-- Invoice -> Claim
CREATE EDGE IF NOT EXISTS BILLED_FOR ();

-- Claim -> Claim (for fraud detection)
CREATE EDGE IF NOT EXISTS SIMILAR_TO (
  similarity_score decimal
);
```

#### 2.1.3 Example Queries

```ngql
-- Check if procedure is covered
MATCH (u:User)-[:HAS_POLICY]->(p:Policy)-[:PROVIDES_COVERAGE]->(c:Coverage)-[:COVERS_PROCEDURE]->(pr:Procedure)
WHERE u.user_id == "USER123" AND pr.cpt_code == "29881"
AND NOT EXISTS {
  MATCH (p)-[:HAS_EXCLUSION]->(e:Exclusion)-[:EXCLUDES_PROCEDURE]->(pr)
}
RETURN c, pr

-- Find coverage gaps
MATCH (p:Policy)-[:PROVIDES_COVERAGE]->(c:Coverage)
WHERE p.policy_id == "POL456"
WITH COLLECT(c.service_category) AS covered
MATCH (pr:Procedure)
WHERE NOT pr.category IN covered
RETURN pr.category, COUNT(pr) AS uncovered_procedures

-- Detect fraud patterns
MATCH (c1:Claim)-[:FOR_PROCEDURE]->(pr:Procedure),
      (c1)-[:SERVICED_BY]->(prov:Provider)
WHERE c1.submission_date > date('2024-01-01')
WITH prov, pr, COUNT(c1) AS claim_count, AVG(c1.billed_amount) AS avg_amount
WHERE claim_count > 10 AND avg_amount > 5000
RETURN prov.name, pr.description, claim_count, avg_amount
ORDER BY claim_count DESC
```

### 2.2 Weaviate Schema

#### 2.2.1 Document Chunk Class

```python
{
  "class": "DocumentChunk",
  "description": "Chunked document segments with embeddings",
  "vectorizer": "text2vec-openai",  # or text2vec-cohere, text2vec-huggingface
  "moduleConfig": {
    "text2vec-openai": {
      "model": "text-embedding-3-large",
      "dimensions": 1536
    },
    "generative-openai": {
      "model": "gpt-4"
    }
  },
  "properties": [
    {
      "name": "content",
      "dataType": ["text"],
      "description": "Chunk text content"
    },
    {
      "name": "document_id",
      "dataType": ["string"],
      "description": "Parent document ID"
    },
    {
      "name": "document_type",
      "dataType": ["string"],
      "description": "Policy, Claim, Invoice, EOB"
    },
    {
      "name": "chunk_index",
      "dataType": ["int"],
      "description": "Position in document"
    },
    {
      "name": "metadata",
      "dataType": ["object"],
      "description": "JSON metadata (page, section, etc.)"
    },
    {
      "name": "created_at",
      "dataType": ["date"]
    }
  ]
}
```

#### 2.2.2 Policy Clause Class

```python
{
  "class": "PolicyClause",
  "description": "Extracted policy clauses/provisions",
  "vectorizer": "text2vec-openai",
  "properties": [
    {
      "name": "clause_text",
      "dataType": ["text"],
      "description": "The policy clause content"
    },
    {
      "name": "clause_type",
      "dataType": ["string"],
      "description": "Coverage, Exclusion, Limitation, Condition"
    },
    {
      "name": "policy_id",
      "dataType": ["string"]
    },
    {
      "name": "section",
      "dataType": ["string"]
    },
    {
      "name": "applies_to",
      "dataType": ["string[]"],
      "description": "Service categories"
    },
    {
      "name": "extracted_entities",
      "dataType": ["object"],
      "description": "CPT codes, ICD-10, amounts"
    }
  ]
}
```

#### 2.2.3 Claim Record Class

```python
{
  "class": "ClaimRecord",
  "description": "Historical claim records for similarity matching",
  "vectorizer": "text2vec-openai",
  "properties": [
    {
      "name": "claim_summary",
      "dataType": ["text"],
      "description": "Claim narrative"
    },
    {
      "name": "claim_id",
      "dataType": ["string"]
    },
    {
      "name": "procedure_codes",
      "dataType": ["string[]"]
    },
    {
      "name": "diagnosis_codes",
      "dataType": ["string[]"]
    },
    {
      "name": "provider_npi",
      "dataType": ["string"]
    },
    {
      "name": "outcome",
      "dataType": ["string"],
      "description": "Approved, Denied, Partial"
    },
    {
      "name": "approval_confidence",
      "dataType": ["number"]
    },
    {
      "name": "denial_reason",
      "dataType": ["string"]
    }
  ]
}
```

#### 2.2.4 Invoice Line Item Class

```python
{
  "class": "InvoiceLineItem",
  "description": "Invoice line items for fraud detection",
  "vectorizer": "text2vec-openai",
  "properties": [
    {
      "name": "description",
      "dataType": ["text"]
    },
    {
      "name": "invoice_id",
      "dataType": ["string"]
    },
    {
      "name": "vendor",
      "dataType": ["string"]
    },
    {
      "name": "amount",
      "dataType": ["number"]
    },
    {
      "name": "category",
      "dataType": ["string"]
    },
    {
      "name": "date",
      "dataType": ["date"]
    }
  ]
}
```

### 2.3 PostgreSQL Schema

```sql
-- Users table
CREATE TABLE users (
  user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(50) DEFAULT 'user',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Documents metadata
CREATE TABLE documents (
  document_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(user_id),
  filename VARCHAR(255) NOT NULL,
  file_path TEXT NOT NULL,
  file_size BIGINT,
  mime_type VARCHAR(100),
  document_type VARCHAR(50),
  upload_date TIMESTAMP DEFAULT NOW(),
  processed BOOLEAN DEFAULT FALSE,
  processing_status VARCHAR(50),
  error_message TEXT,
  metadata JSONB
);

-- API audit logs
CREATE TABLE api_logs (
  log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(user_id),
  endpoint VARCHAR(255),
  method VARCHAR(10),
  request_body JSONB,
  response_status INT,
  response_body JSONB,
  latency_ms INT,
  timestamp TIMESTAMP DEFAULT NOW(),
  correlation_id UUID
);

-- Processing jobs
CREATE TABLE processing_jobs (
  job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID REFERENCES documents(document_id),
  job_type VARCHAR(50),
  status VARCHAR(50),
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  result JSONB,
  error_message TEXT
);

-- Eligibility checks
CREATE TABLE eligibility_checks (
  check_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(user_id),
  policy_id VARCHAR(255),
  procedure_code VARCHAR(50),
  diagnosis_code VARCHAR(50),
  result VARCHAR(50),
  confidence_score DECIMAL(5,4),
  explanation JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_type ON documents(document_type);
CREATE INDEX idx_api_logs_user_id ON api_logs(user_id);
CREATE INDEX idx_api_logs_timestamp ON api_logs(timestamp);
CREATE INDEX idx_eligibility_checks_user_id ON eligibility_checks(user_id);
```

---

## 3. RAG Optimization Strategies

### 3.1 Document Chunking Strategy

**Semantic Chunking with Overlap**:
```python
# Configuration
CHUNK_SIZE = 500  # tokens
CHUNK_OVERLAP = 100  # tokens
MIN_CHUNK_SIZE = 100

# Strategy
1. Split on natural boundaries (sections, paragraphs)
2. Preserve table structures
3. Keep related content together (e.g., coverage + limits)
4. Add contextual metadata to each chunk
```

**Metadata Enhancement**:
```python
chunk_metadata = {
  "document_id": "DOC123",
  "document_type": "policy",
  "section": "Coverage Details",
  "page_number": 5,
  "chunk_index": 3,
  "has_table": True,
  "entities": ["deductible", "copay"],
  "parent_context": "Section 3: Medical Benefits"
}
```

### 3.2 Retrieval Enhancement

**Hybrid Search Implementation**:
```python
def hybrid_search(query: str, top_k: int = 10):
    # 1. Dense retrieval (semantic)
    dense_results = weaviate.query(query, limit=top_k*2)
    
    # 2. Sparse retrieval (BM25) - if supported
    sparse_results = bm25_search(query, limit=top_k*2)
    
    # 3. Reciprocal Rank Fusion
    fused_results = rrf_fusion(dense_results, sparse_results, k=60)
    
    # 4. Graph filtering
    graph_filtered = filter_by_graph_context(fused_results, user_context)
    
    # 5. Reranking
    reranked = cross_encoder_rerank(query, graph_filtered, top_k=top_k)
    
    return reranked[:top_k]
```

**Query Expansion (HyDE)**:
```python
def hypothetical_document_expansion(query: str):
    """Generate hypothetical answer to improve retrieval"""
    prompt = f"""Given this question: "{query}"
    Generate a hypothetical answer as it might appear in an insurance policy document."""
    
    hypothetical_answer = llm.generate(prompt)
    
    # Search using both original query and hypothetical answer
    results = hybrid_search(query + " " + hypothetical_answer)
    return results
```

### 3.3 Context Compression

**LLMLingua Integration**:
```python
from llmlingua import PromptCompressor

def compress_context(retrieved_chunks: List[str], query: str, 
                     target_ratio: float = 0.5):
    compressor = PromptCompressor()
    
    combined_context = "\n\n".join(retrieved_chunks)
    
    compressed = compressor.compress_prompt(
        combined_context,
        instruction=query,
        target_token=int(len(combined_context.split()) * target_ratio)
    )
    
    return compressed['compressed_prompt']
```

### 3.4 Answer Generation with Citations

```python
def generate_answer_with_citations(query: str, context: List[Dict]):
    prompt = f"""Using the following context, answer the question.
    Include citations using [1], [2] format.
    
    Context:
    {format_context_with_numbers(context)}
    
    Question: {query}
    
    Answer with citations:"""
    
    answer = llm.generate(prompt)
    
    return {
        "answer": answer,
        "sources": [c['metadata'] for c in context]
    }
```

---

## 4. LangGraph Workflows

### 4.1 Document Processing Workflow

```python
from langgraph.graph import StateGraph, END

class DocumentProcessingState(TypedDict):
    document: bytes
    document_id: str
    document_type: Optional[str]
    extracted_text: Optional[str]
    entities: Optional[Dict]
    graph_entities: Optional[List]
    vector_embeddings: Optional[List]
    errors: List[str]

workflow = StateGraph(DocumentProcessingState)

# Nodes
workflow.add_node("classify", classify_document)
workflow.add_node("ocr", perform_ocr)
workflow.add_node("extract_entities", extract_entities)
workflow.add_node("create_graph_nodes", create_graph_nodes)
workflow.add_node("create_embeddings", create_embeddings)
workflow.add_node("validate", validate_extraction)

# Edges
workflow.add_edge("classify", "ocr")
workflow.add_edge("ocr", "extract_entities")
workflow.add_edge("extract_entities", "validate")

def route_after_validation(state):
    if state["errors"]:
        return "error_handler"
    return "create_graph_nodes"

workflow.add_conditional_edges(
    "validate",
    route_after_validation,
    {"create_graph_nodes": "create_graph_nodes", "error_handler": END}
)

workflow.add_edge("create_graph_nodes", "create_embeddings")
workflow.add_edge("create_embeddings", END)

workflow.set_entry_point("classify")

app = workflow.compile()
```

### 4.2 Claims Eligibility Workflow

```python
class EligibilityState(TypedDict):
    user_id: str
    policy_id: str
    procedure_code: str
    diagnosis_code: str
    provider_npi: Optional[str]
    service_date: date
    
    # Retrieved data
    policy_data: Optional[Dict]
    coverage_data: Optional[List[Dict]]
    historical_claims: Optional[List[Dict]]
    
    # Decision
    eligibility_result: Optional[str]
    confidence_score: Optional[float]
    explanation: Optional[str]
    requirements: Optional[List[str]]
    estimated_cost: Optional[Dict]

eligibility_workflow = StateGraph(EligibilityState)

# Nodes
eligibility_workflow.add_node("retrieve_policy", retrieve_policy_from_graph)
eligibility_workflow.add_node("check_coverage", check_coverage_rules)
eligibility_workflow.add_node("check_exclusions", check_exclusions)
eligibility_workflow.add_node("retrieve_similar_claims", retrieve_similar_claims_from_vector)
eligibility_workflow.add_node("calculate_costs", calculate_patient_costs)
eligibility_workflow.add_node("make_decision", make_eligibility_decision)
eligibility_workflow.add_node("generate_explanation", generate_explanation)

# Conditional routing
def route_after_coverage(state):
    if not state["coverage_data"]:
        return "not_covered"
    return "check_exclusions"

eligibility_workflow.add_edge("retrieve_policy", "check_coverage")
eligibility_workflow.add_conditional_edges(
    "check_coverage",
    route_after_coverage,
    {"check_exclusions": "check_exclusions", "not_covered": "make_decision"}
)

eligibility_workflow.add_edge("check_exclusions", "retrieve_similar_claims")
eligibility_workflow.add_edge("retrieve_similar_claims", "calculate_costs")
eligibility_workflow.add_edge("calculate_costs", "make_decision")
eligibility_workflow.add_edge("make_decision", "generate_explanation")
eligibility_workflow.add_edge("generate_explanation", END)

eligibility_workflow.set_entry_point("retrieve_policy")

eligibility_app = eligibility_workflow.compile()
```

### 4.3 Fraud Detection Workflow

```python
class FraudDetectionState(TypedDict):
    claim_id: str
    claim_data: Dict
    similar_claims: Optional[List[Dict]]
    provider_history: Optional[Dict]
    anomaly_scores: Optional[Dict]
    fraud_risk_score: Optional[float]
    fraud_indicators: Optional[List[str]]
    recommendation: Optional[str]

fraud_workflow = StateGraph(FraudDetectionState)

fraud_workflow.add_node("retrieve_claim", retrieve_claim_details)
fraud_workflow.add_node("find_similar_claims", find_similar_claims_vector)
fraud_workflow.add_node("analyze_provider_pattern", analyze_provider_pattern_graph)
fraud_workflow.add_node("detect_anomalies", detect_anomalies)
fraud_workflow.add_node("calculate_risk", calculate_fraud_risk)
fraud_workflow.add_node("generate_report", generate_fraud_report)

fraud_workflow.add_edge("retrieve_claim", "find_similar_claims")
fraud_workflow.add_edge("find_similar_claims", "analyze_provider_pattern")
fraud_workflow.add_edge("analyze_provider_pattern", "detect_anomalies")
fraud_workflow.add_edge("detect_anomalies", "calculate_risk")
fraud_workflow.add_edge("calculate_risk", "generate_report")
fraud_workflow.add_edge("generate_report", END)

fraud_workflow.set_entry_point("retrieve_claim")

fraud_app = fraud_workflow.compile()
```

---

## 5. Project Structure

```
financeAnalysis/
├── .env.example
├── .env
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── pyproject.toml
├── README.md
├── prd.md
├── INSTRUCTIONS.md
│
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app entry point
│   ├── config.py                    # Configuration management
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── router.py           # Main router
│   │   │   ├── auth.py             # Authentication endpoints
│   │   │   ├── documents.py        # Document ingestion endpoints
│   │   │   ├── extraction.py       # Entity extraction endpoints
│   │   │   ├── eligibility.py      # Claims eligibility endpoints
│   │   │   ├── fraud.py            # Fraud detection endpoints
│   │   │   └── policy.py           # Policy query endpoints
│   │   └── dependencies.py         # Shared dependencies
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py             # JWT, OAuth2 handlers
│   │   ├── rate_limiter.py         # Rate limiting
│   │   └── middleware.py           # Custom middleware
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── schemas.py              # Pydantic models
│   │   ├── database.py             # SQLAlchemy models
│   │   └── graph_schema.py         # NebulaGraph schema definitions
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ocr_service.py          # OCR processing
│   │   ├── document_service.py     # Document management
│   │   ├── extraction_service.py   # Entity extraction
│   │   ├── graph_service.py        # NebulaGraph operations
│   │   ├── vector_service.py       # Weaviate operations
│   │   ├── llm_service.py          # LLM interactions
│   │   └── storage_service.py      # S3/MinIO operations
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py                 # Base agent class
│   │   ├── classifier.py           # Document classifier agent
│   │   ├── invoice_extractor.py   # Invoice extraction agent
│   │   ├── policy_parser.py        # Policy parser agent
│   │   ├── claims_agent.py         # Claims processing agent
│   │   ├── eligibility_agent.py    # Eligibility reasoning agent
│   │   ├── fraud_agent.py          # Fraud detection agent
│   │   └── compliance_agent.py     # Compliance validation agent
│   │
│   ├── workflows/
│   │   ├── __init__.py
│   │   ├── document_processing.py  # LangGraph document workflow
│   │   ├── eligibility_check.py    # LangGraph eligibility workflow
│   │   └── fraud_detection.py      # LangGraph fraud workflow
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── postgres.py             # PostgreSQL connection
│   │   ├── nebula.py               # NebulaGraph connection
│   │   └── weaviate.py             # Weaviate connection
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logger.py               # Logging utilities
│       ├── chunking.py             # Document chunking
│       ├── embeddings.py           # Embedding generation
│       └── validators.py           # Data validators
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_api/
│   ├── test_agents/
│   ├── test_workflows/
│   └── test_services/
│
├── scripts/
│   ├── setup_databases.py          # Initialize DB schemas
│   ├── seed_data.py                # Load sample data
│   └── migrate.py                  # Database migrations
│
├── data/
│   ├── samples/                    # Sample documents
│   └── rules/                      # Business rules config
│
└── docs/
    ├── api_documentation.md
    ├── deployment_guide.md
    └── architecture_diagrams/
```

---

## 6. Setup Instructions

### 6.1 Prerequisites

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15+
- NebulaGraph 3.6+
- Weaviate 1.22+
- MinIO or AWS S3
- OpenAI API Key or Azure OpenAI

### 6.2 Environment Setup

```bash
# Clone repository (if applicable)
git clone <repo-url>
cd financeAnalysis

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your credentials
```

### 6.3 Docker Services

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: finsight
      POSTGRES_USER: finsight_user
      POSTGRES_PASSWORD: secure_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  nebula-graphd:
    image: vesoft/nebula-graphd:v3.6.0
    ports:
      - "9669:9669"
    depends_on:
      - nebula-metad
      - nebula-storaged

  nebula-metad:
    image: vesoft/nebula-metad:v3.6.0
    ports:
      - "9559:9559"

  nebula-storaged:
    image: vesoft/nebula-storaged:v3.6.0
    ports:
      - "9779:9779"

  weaviate:
    image: semitechnologies/weaviate:1.22.0
    ports:
      - "8080:8080"
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      DEFAULT_VECTORIZER_MODULE: 'text2vec-openai'
      ENABLE_MODULES: 'text2vec-openai,generative-openai'
      OPENAI_APIKEY: ${OPENAI_API_KEY}
    volumes:
      - weaviate_data:/var/lib/weaviate

  minio:
    image: minio/minio
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
  weaviate_data:
  minio_data:
```

### 6.4 Database Initialization

```bash
# Start services
docker-compose up -d

# Wait for services to be ready
sleep 30

# Initialize NebulaGraph schema
python scripts/setup_databases.py --nebula

# Initialize Weaviate schema
python scripts/setup_databases.py --weaviate

# Initialize PostgreSQL tables
python scripts/setup_databases.py --postgres

# Load sample data (optional)
python scripts/seed_data.py
```

### 6.5 Environment Variables

```bash
# .env.example
# Application
APP_NAME=FinSightAI
APP_VERSION=1.0.0
DEBUG=true
LOG_LEVEL=INFO

# API
API_V1_PREFIX=/api/v1
SECRET_KEY=your-secret-key-here-min-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database - PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=finsight
POSTGRES_USER=finsight_user
POSTGRES_PASSWORD=secure_password

# Database - NebulaGraph
NEBULA_HOST=localhost
NEBULA_PORT=9669
NEBULA_USER=root
NEBULA_PASSWORD=nebula
NEBULA_SPACE=finsight

# Database - Weaviate
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=

# Storage - MinIO/S3
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=finsight-documents
S3_REGION=us-east-1

# Cache - Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# LLM - OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_EMBEDDING_MODEL=text-embedding-3-large

# OCR
TESSERACT_PATH=/usr/bin/tesseract
PADDLEOCR_LANG=en

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60

# Observability
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=finsight-ai
```

---

## 7. Development Workflow

### 7.1 Running the Application

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 7.2 API Documentation

Once running, access:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

### 7.3 Development Guidelines

**Code Style**:
- Use Black for formatting
- Use isort for imports
- Use mypy for type checking
- Follow PEP 8

**Commit Guidelines**:
- Use conventional commits
- Format: `type(scope): description`
- Types: feat, fix, docs, style, refactor, test, chore

**Testing**:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api/test_eligibility.py
```

---

## 8. Testing Strategy

### 8.1 Unit Tests

```python
# tests/test_services/test_extraction_service.py
import pytest
from app.services.extraction_service import extract_policy_entities

def test_extract_deductible():
    text = "Annual deductible: $1,500 per individual"
    result = extract_policy_entities(text)
    assert result["deductible_individual"] == 1500

def test_extract_cpt_code():
    text = "Procedure code CPT 29881 - Knee arthroscopy"
    result = extract_policy_entities(text)
    assert "29881" in result["cpt_codes"]
```

### 8.2 Integration Tests

```python
# tests/test_workflows/test_eligibility_workflow.py
import pytest
from app.workflows.eligibility_check import eligibility_app

@pytest.mark.integration
async def test_eligibility_workflow_approved():
    initial_state = {
        "user_id": "USER123",
        "policy_id": "POL456",
        "procedure_code": "99213",
        "diagnosis_code": "E11.9"
    }
    
    result = await eligibility_app.ainvoke(initial_state)
    
    assert result["eligibility_result"] == "Approved"
    assert result["confidence_score"] > 0.8
    assert "explanation" in result
```

### 8.3 API Tests

```python
# tests/test_api/test_documents.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_upload_document():
    with open("tests/fixtures/sample_policy.pdf", "rb") as f:
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("policy.pdf", f, "application/pdf")},
            headers={"Authorization": f"Bearer {test_token}"}
        )
    
    assert response.status_code == 200
    assert "document_id" in response.json()
```

---

## 9. Deployment

### 9.1 Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY ./app ./app
COPY ./scripts ./scripts

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 9.2 Kubernetes Deployment (Optional)

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: finsight-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: finsight-api
  template:
    metadata:
      labels:
        app: finsight-api
    spec:
      containers:
      - name: api
        image: finsight-ai:latest
        ports:
        - containerPort: 8000
        env:
        - name: POSTGRES_HOST
          valueFrom:
            secretKeyRef:
              name: finsight-secrets
              key: postgres-host
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
```

### 9.3 Monitoring & Observability

**Prometheus Metrics**:
```python
from prometheus_client import Counter, Histogram

document_processing_counter = Counter(
    'documents_processed_total',
    'Total documents processed',
    ['document_type', 'status']
)

eligibility_check_histogram = Histogram(
    'eligibility_check_duration_seconds',
    'Time spent processing eligibility check'
)
```

**Structured Logging**:
```python
import structlog

logger = structlog.get_logger()

logger.info(
    "eligibility_check_completed",
    user_id=user_id,
    policy_id=policy_id,
    result=result,
    confidence=confidence,
    duration_ms=duration
)
```

---

## 10. Next Steps & Enhancements

### 10.1 Phase 1 Priorities
1. Complete document ingestion pipeline
2. Implement basic extraction agents
3. Set up database schemas
4. Build core API endpoints

### 10.2 Phase 2 Enhancements
1. Advanced eligibility reasoning
2. Graph-based fraud detection
3. Multi-policy comparison
4. Real-time claim status tracking

### 10.3 Future Considerations
- Multi-tenant support
- Real-time streaming processing
- Mobile SDK
- Enterprise SSO integration
- Advanced analytics dashboard
- FHIR integration for healthcare interoperability

---

## Appendix A: Sample API Requests

### Upload Document
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@policy.pdf" \
  -F "document_type=policy"
```

### Check Eligibility
```bash
curl -X POST "http://localhost:8000/api/v1/eligibility/check" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "USER123",
    "policy_id": "POL456",
    "procedure_code": "29881",
    "diagnosis_code": "M17.11",
    "provider_npi": "1234567890"
  }'
```

### Query Policy Graph
```bash
curl -X GET "http://localhost:8000/api/v1/policy/POL456/coverage" \
  -H "Authorization: Bearer $TOKEN"
```

---

**End of Instructions**
