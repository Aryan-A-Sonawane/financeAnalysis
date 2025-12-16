# Product Requirements Document (PRD)

## 1. Product Overview

### Product Name (Working)
**FinSightAI – Financial & Insurance Document Intelligence Platform**

### Vision
Build an **API-first, AI-powered financial document intelligence system** that goes beyond Q&A to **extract, normalize, reason over, and validate financial and insurance data**, with a special focus on **USA insurance plans and claims eligibility**. The system should reduce manual analysis, improve accuracy, and provide **actionable decisions**, not just answers.

### Key Differentiator (Novelty)
Unlike typical RAG-based document chat systems, FinSightAI:
- Performs **structured extraction + reasoning + eligibility simulation**
- Uses a **Graph + Vector hybrid memory** (NebulaGraph + Weaviate)
- Includes **claims benefit approval & scenario simulation**
- Detects **policy conflicts, missing coverage, fraud patterns**
- Is **API-first**, embeddable into insurer, fintech, hospital, and HR platforms

---

## 2. Target Users & Use Cases

### Primary Users
1. **Insurance Policyholders (USA)** – Want to know if a claim will be approved before filing
2. **Insurance Agents & Brokers** – Need fast policy comparison & eligibility checks
3. **Healthcare Providers** – Pre-validate insurance coverage
4. **Fintech & Insurtech Companies** – Integrate via API
5. **Auditors & Compliance Teams** – Detect anomalies and fraud

### Example Use Cases
- "Is knee surgery covered under my PPO plan if deductible is partially met?"
- "Extract all deductible, copay, and out-of-pocket limits from these 5 policy PDFs"
- "Compare 3 insurance plans for a diabetic patient scenario"
- "Detect suspicious invoice patterns across claims"

---

## 3. Existing Tools Research (Baseline)

### Existing Solutions
| Tool | Capability | Gap |
|----|----|----|
| Rossum | Invoice extraction | No reasoning, no insurance logic |
| Veryfi | Receipt OCR | No eligibility or graph logic |
| Hyperscience | Document automation | Enterprise-heavy, not API-flexible |
| Azure Form Recognizer | Extraction only | No policy reasoning |
| ChatGPT-style RAG | Q&A over docs | No structured decision-making |

### Opportunity for Novelty
- No mainstream tool **simulates insurance claim approval**
- No popular system combines **vector similarity + graph reasoning**
- Very limited **policy conflict & coverage gap detection**

---

## 4. Core Features

### 4.1 Document Ingestion (Multi-format)
Supported formats:
- PDF (scanned & digital)
- Images (JPEG, PNG)
- DOCX
- EDI / CSV
- Email-based invoices

Processing Pipeline:
1. OCR (Tesseract / PaddleOCR)
2. Layout parsing (DocTR / LayoutLM)
3. Classification (Invoice / Policy / Receipt / Claim / EOB)

---

### 4.2 LangGraph-Based Agent Architecture (MANDATORY)

#### Agents
1. **Document Classifier Agent**
2. **Invoice Extraction Agent**
3. **Insurance Policy Parser Agent**
4. **Claims & Benefits Agent**
5. **Eligibility Reasoning Agent**
6. **Fraud Detection Agent**
7. **Compliance Validation Agent**

LangGraph ensures:
- Deterministic workflows
- Retryable nodes
- Auditability (critical for finance & insurance)

---

### 4.3 Structured Extraction (Not QnA)

Extracted Entities:
- Policy: premium, deductible, copay, coinsurance, exclusions
- Claim: CPT codes, ICD-10, billed amount, allowed amount
- Invoice: vendor, tax, line items
- Dates, thresholds, coverage limits

Output is **JSON + Graph entities**, not free text.

---

### 4.4 Graph Database – NebulaGraph

#### Why Graph?
Insurance is **relationship-heavy**:
- Policy → Coverage → Condition → Claim → Approval

#### Graph Schema (Example)
- Nodes: Policy, Claim, Procedure, Diagnosis, Provider, User
- Edges: COVERS, EXCLUDES, APPLIES_TO, CLAIMED_UNDER

Use cases:
- Detect coverage gaps
- Multi-policy overlap detection
- Rule-based eligibility traversal

---

### 4.5 Vector Database – Weaviate

Stored Embeddings:
- Policy clauses
- Claim histories
- Invoice line items

Use Cases:
- Similar policy matching
- Fraud pattern similarity
- Duplicate / inflated invoice detection

Hybrid search = Graph filter + Vector similarity

---

### 4.6 Claims Benefit Approval Engine (CORE NOVEL FEATURE)

#### Inputs
- User scenario (procedure, diagnosis, provider, location)
- Policy graph
- Historical approvals

#### Output
- Eligibility: Approved / Conditionally Approved / Rejected
- Confidence score
- Explanation graph path
- Missing requirements (e.g., pre-authorization)

This is **decision intelligence**, not chat.

---

### 4.7 Fraud & Anomaly Detection

Signals:
- Repeated similar invoices (Weaviate)
- Unusual claim-provider relationships (NebulaGraph)
- Amount deviation from norm

Output:
- Fraud risk score
- Similar historical cases

---

## 5. API-First Design (MANDATORY)

### API Types
- REST (FastAPI)
- GraphQL (for complex queries)

### Core APIs
- POST /ingest/document
- POST /extract/entities
- POST /claims/eligibility
- GET /policy/graph
- POST /fraud/analyze

### Response Style
- Machine-readable JSON
- Explanation paths included

---

## 6. System Architecture

```
Frontend (Web Dashboard)
       |
FastAPI Gateway (Auth, Rate-limit)
       |
LangGraph Orchestrator
  |        |
Weaviate  NebulaGraph
  |
Object Storage (S3)
```

---

## 7. Tech Stack

| Layer | Tech |
|----|----|
| Backend | FastAPI |
| Agents | LangGraph |
| Vector DB | Weaviate |
| Graph DB | NebulaGraph |
| LLM | Claude / GPT |
| OCR | Tesseract / PaddleOCR |
| Auth | OAuth2 / JWT |

---

## 8. Security & Compliance

- HIPAA-aligned design
- Encryption at rest & transit
- Audit logs for every decision
- Explainable AI paths

---

## 9. KPIs

- Extraction accuracy > 95%
- Claim eligibility precision > 90%
- Manual processing time reduced by 70%
- API latency < 800ms

---

## 10. Roadmap

### Phase 1
- Document ingestion
- Basic extraction

### Phase 2
- Claims eligibility engine
- Graph reasoning

### Phase 3
- Fraud detection
- Enterprise integrations

---

# Instructions for Claude Code Agent

## Role
You are a **Senior AI Systems Engineer** building an **API-first financial & insurance intelligence platform**.

## Non-negotiables
- No pure Q&A systems
- Use LangGraph, FastAPI, Weaviate, NebulaGraph
- Every response must be structured & explainable

## Tasks
1. Design LangGraph workflows for each agent
2. Implement schema for NebulaGraph
3. Implement vector schema in Weaviate
4. Build FastAPI endpoints
5. Implement eligibility reasoning logic
6. Add audit & explanation tracing

## Coding Guidelines
- Modular services
- Deterministic workflows
- Strong typing (Pydantic)
- No hardcoded business rules – config-driven

## Success Criteria
- Can ingest real US insurance PDFs
- Can simulate claim approval
- Can be embedded via API
- Produces explainable decisions

---

## Final Note
This project is not a chatbot. It is a **decision intelligence system for financial & insurance documents**.

