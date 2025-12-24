# LangGraph AI Workflows

FinSightAI implements advanced AI workflows using **LangGraph** to orchestrate multiple specialized agents for comprehensive document processing and insurance eligibility determination.

## Overview

The platform uses **7 specialized AI agents** working together through LangGraph state machines to provide:
- Intelligent document classification and extraction
- Fraud pattern detection
- Regulatory compliance validation
- Insurance eligibility determination with detailed reasoning

## Architecture

### Agent System

All agents inherit from `BaseAgent` and use structured Pydantic models for consistent outputs:

```python
class BaseAgent:
    - create_prompt() → str
    - process(state: AgentState) → Dict
    - should_continue(state: AgentState) → bool
    - run(state: AgentState) → AgentState
```

### The 7 AI Agents

#### 1. **Document Classifier Agent**
**Purpose**: Classify financial/insurance documents into 5 types

**Output**: 
- `document_type`: policy | claim_form | invoice | eob | receipt
- `confidence`: 0.0 - 1.0
- `reasoning`: Classification logic
- `key_indicators`: Document features used

**Use Cases**:
- Route documents to appropriate extraction agents
- Auto-categorize uploaded documents
- Quality assurance for manual classifications

#### 2. **Invoice Extraction Agent**
**Purpose**: Extract structured data from medical invoices

**Output**:
- Invoice metadata (number, dates, provider)
- Line items with CPT/HCPCS codes
- Financial totals (subtotal, tax, total)
- Payment terms

**Use Cases**:
- Automated invoice processing
- Claims submission preparation
- Cost analysis and reporting

#### 3. **Policy Parser Agent**
**Purpose**: Parse insurance policy documents

**Output**:
- Policy details (number, holder, company)
- Financial terms (premium, deductible, OOP max)
- Coverage list with limits
- Exclusions list
- Network type and beneficiaries

**Use Cases**:
- Policy database population
- Coverage verification
- Eligibility determination

#### 4. **Claims & Benefits Agent**
**Purpose**: Analyze insurance claims with benefit calculations

**Output**:
- Claim details and dates
- Diagnosis codes (ICD-10)
- Procedure codes (CPT/HCPCS)
- Financial breakdown
  - Total charged
  - Insurance paid
  - Patient responsibility
  - Deductible/coinsurance/copay applied
- Coverage analysis
- Recommendations

**Use Cases**:
- Claims adjudication
- Patient billing
- Coverage dispute resolution

#### 5. **Eligibility Reasoning Agent**
**Purpose**: Determine coverage eligibility with detailed reasoning

**Output**:
- `is_eligible`: boolean decision
- `confidence`: 0.0 - 1.0
- `coverage_percentage`: Expected coverage %
- Policy coverage assessment
- Medical necessity evaluation
- Network status verification
- Financial estimates
  - Estimated cost
  - Insurance payment
  - Patient payment
  - Deductible impact
- Prior authorization requirements
- Documentation needed
- Decision reasoning
- Coverage limitations
- Alternative options
- Next steps

**Use Cases**:
- Pre-authorization decisions
- Coverage verification
- Patient cost estimates
- Appeals support

#### 6. **Fraud Detection Agent**
**Purpose**: Detect fraud patterns in claims and billing

**Output**:
- `fraud_risk_score`: 0-100
- `risk_level`: none | low | medium | high | critical
- Fraud indicators with severity
- Pattern analysis
  - Billing patterns (duplicate, excessive)
  - Coding issues (upcoding, unbundling)
  - Temporal patterns (unusual timing)
  - Provider red flags
- Duplicate claim detection
- Upcoding risks
- Unbundling risks
- Medical necessity concerns
- Investigation recommendation
- Recommended actions

**Use Cases**:
- Claims review automation
- Fraud investigation prioritization
- Provider auditing
- Risk scoring

#### 7. **Compliance Validation Agent**
**Purpose**: Validate regulatory compliance

**Output**:
- `is_compliant`: boolean
- `compliance_score`: 0-100
- Regulatory checks
  - HIPAA compliance
  - ACA compliance
  - State regulations
  - Medical coding standards
- Validation by category
  - Privacy & security
  - Consent & authorization
  - Documentation requirements
  - Coding accuracy
  - Billing practices
  - Network adequacy
  - Contract compliance
- Issues list with severity
- Critical actions needed
- Risk assessment

**Use Cases**:
- Regulatory audits
- Compliance monitoring
- Risk management
- Policy enforcement

## Workflows

### 1. Document Processing Workflow

**Graph Structure**:
```
START 
  ↓
classify_document (Agent 1)
  ↓
[Conditional Routing]
  ├─ invoice → extract_invoice (Agent 2)
  ├─ policy → parse_policy (Agent 3)
  └─ claim/eob → analyze_claim (Agent 4)
  ↓
detect_fraud (Agent 6)
  ↓
validate_compliance (Agent 7)
  ↓
END
```

**API Endpoint**: `POST /api/v1/workflows/process-document`

**Request**:
```json
{
  "document_id": "doc-123",
  "document_text": "extracted text...",
  "run_fraud_detection": true,
  "run_compliance_check": true
}
```

**Response**:
```json
{
  "success": true,
  "workflow_id": "wf-456",
  "processing_time": 3.45,
  "result": {
    "classification": {...},
    "extraction": {...},
    "fraud_analysis": {...},
    "compliance": {...}
  }
}
```

### 2. Eligibility Check Workflow

**Graph Structure**:
```
START
  ↓
check_eligibility (Agent 5)
  ↓
detect_fraud (Agent 6)
  ↓
validate_compliance (Agent 7)
  ↓
END
```

**API Endpoint**: `POST /api/v1/workflows/check-eligibility`

**Request**:
```json
{
  "policy_info": {
    "policy_number": "POL-123",
    "deductible": 2000,
    "coinsurance": 0.8,
    ...
  },
  "service_info": {
    "procedure_code": "99214",
    "estimated_cost": 250,
    ...
  },
  "patient_info": {
    "patient_name": "John Doe",
    "current_deductible_met": 500,
    ...
  }
}
```

**Response**:
```json
{
  "success": true,
  "workflow_id": "wf-789",
  "processing_time": 2.1,
  "result": {
    "eligibility": {
      "is_eligible": true,
      "confidence": 0.95,
      "coverage_percentage": 80,
      "estimated_cost": 250,
      "insurance_payment": 200,
      "patient_payment": 50,
      ...
    },
    "fraud_analysis": {...},
    "compliance": {...}
  }
}
```

## Integration with Document Upload

Documents can be processed through workflows during upload:

```bash
POST /api/v1/documents/upload?use_workflow=true
Content-Type: multipart/form-data

[file data]
```

When `use_workflow=true`:
1. Document is uploaded and OCR is performed
2. Text is extracted
3. **DocumentProcessingWorkflow** is triggered
4. All 7 agents process the document
5. Results are stored in database
6. Comprehensive analysis is returned

## Workflow Management

### Check Workflow Status
```bash
GET /api/v1/workflows/status/{workflow_id}
```

### Get Workflow History
```bash
GET /api/v1/workflows/history?limit=10&status=completed
```

### Clear History
```bash
DELETE /api/v1/workflows/clear-history
```

## Configuration

Workflows use GPT-4 with low temperature for deterministic outputs:

```python
# app/agents/base_agent.py
self.llm = ChatOpenAI(
    model="gpt-4",
    temperature=0.1,  # Low for consistency
    max_tokens=2000
)
```

### Environment Variables
```bash
OPENAI_API_KEY=sk-...
```

## Error Handling

All agents include comprehensive error handling:

```python
try:
    result = agent.run(state)
except Exception as e:
    logger.error("Agent failed", agent=agent.name, error=str(e))
    state.errors.append({
        "agent": agent.name,
        "error": str(e),
        "timestamp": datetime.utcnow()
    })
```

Workflows continue even if individual agents fail, collecting errors in the state.

## Testing

See [WORKFLOW_TESTS.http](./WORKFLOW_TESTS.http) for comprehensive API tests including:
- Invoice processing
- Policy parsing
- Claims analysis
- Eligibility determination
- Fraud detection scenarios
- Compliance validation tests

## Performance

Typical workflow execution times:
- Document Classification: ~2-3 seconds
- Full Document Processing: ~10-15 seconds
- Eligibility Check: ~5-8 seconds

Parallelization opportunities:
- Fraud detection and compliance can run in parallel
- Multiple documents can be processed concurrently
- Agent responses can be cached for similar documents

## Future Enhancements

1. **Async Processing**: Background job queue for long-running workflows
2. **Workflow Persistence**: Store workflow state in database
3. **Human-in-the-Loop**: Approval steps for high-risk decisions
4. **Custom Workflows**: User-defined workflow graphs
5. **A/B Testing**: Compare agent performance with different prompts/models
6. **Monitoring**: Real-time workflow metrics and dashboards
7. **Cost Optimization**: Smart routing to use smaller models when appropriate

## Dependencies

```txt
langchain==1.2.0
langchain-openai==1.0.15
langgraph==1.0.5
pydantic==2.12.5
openai==1.61.0
```

## See Also

- [INSTRUCTIONS.md](./INSTRUCTIONS.md) - Complete project setup
- [API_TESTS.http](./API_TESTS.http) - API endpoint tests
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Common issues and solutions
