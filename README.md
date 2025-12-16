# FinSightAI - Financial & Insurance Document Intelligence Platform

## Overview
FinSightAI is an API-first, AI-powered financial document intelligence system that performs structured extraction, reasoning, and validation of financial and insurance data, with a special focus on USA insurance plans and claims eligibility.

## Key Features
- **Structured Data Extraction**: Extract entities from policies, claims, and invoices
- **Claims Eligibility Simulation**: Predict claim approval before filing
- **Hybrid Graph + Vector Search**: NebulaGraph + Weaviate for advanced reasoning
- **Fraud Detection**: Identify suspicious patterns and anomalies
- **API-First Design**: RESTful API for easy integration

## Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- OpenAI API Key

### Installation

1. **Clone and navigate to project**
```bash
cd financeAnalysis
```

2. **Create environment file**
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY and other credentials
```

3. **Start services with Docker Compose**
```bash
docker-compose up -d
```

Wait for all services to start (PostgreSQL, NebulaGraph, Weaviate, MinIO, Redis).

4. **Create Python virtual environment**
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Linux/Mac
source venv/bin/activate
```

5. **Install dependencies**
```bash
pip install -r requirements.txt
```

6. **Initialize databases**
```bash
python scripts/setup_databases.py --all
```

7. **Run the application**
```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

### Access Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
financeAnalysis/
├── app/
│   ├── api/v1/           # API endpoints
│   ├── agents/           # LangGraph agents
│   ├── core/             # Security, middleware
│   ├── db/               # Database connections
│   ├── models/           # Data models
│   ├── services/         # Business logic
│   ├── utils/            # Utilities
│   └── workflows/        # LangGraph workflows
├── data/                 # Sample data and rules
├── docs/                 # Documentation
├── scripts/              # Setup scripts
├── tests/                # Test suites
├── docker-compose.yml    # Docker services
├── requirements.txt      # Python dependencies
└── INSTRUCTIONS.md       # Detailed build guide
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT token
- `GET /api/v1/auth/me` - Get current user info

### Documents
- `POST /api/v1/documents/upload` - Upload document
- `GET /api/v1/documents/{id}` - Get document metadata
- `GET /api/v1/documents/` - List documents
- `DELETE /api/v1/documents/{id}` - Delete document

### Extraction
- `POST /api/v1/extraction/extract` - Extract entities from document

### Eligibility
- `POST /api/v1/eligibility/check` - Check claims eligibility
- `GET /api/v1/eligibility/history` - Get eligibility check history

### Policy
- `GET /api/v1/policy/{policy_id}/coverage` - Get policy coverage
- `GET /api/v1/policy/{policy_id}/graph` - Get policy graph

### Fraud Detection
- `POST /api/v1/fraud/analyze` - Analyze claim for fraud

## Development

### Running Tests
```bash
pytest
pytest --cov=app --cov-report=html
```

### Code Quality
```bash
black app/
isort app/
flake8 app/
mypy app/
```

## Architecture

### Components
1. **FastAPI** - API Gateway
2. **LangGraph** - Agent orchestration
3. **PostgreSQL** - Metadata and audit logs
4. **NebulaGraph** - Knowledge graph for policies and claims
5. **Weaviate** - Vector database for semantic search
6. **MinIO** - Object storage
7. **Redis** - Caching and rate limiting

### Data Flow
1. Document uploaded via API
2. OCR and classification
3. Entity extraction with LLMs
4. Storage in Graph + Vector databases
5. Reasoning and decision-making via LangGraph workflows

## Next Steps

Refer to [INSTRUCTIONS.md](INSTRUCTIONS.md) for detailed:
- Database schemas
- RAG optimization strategies
- LangGraph workflow designs
- Agent implementations
- Deployment guidelines

## License
Proprietary - All rights reserved

## Support
For questions and support, please refer to the documentation in the `docs/` directory.
