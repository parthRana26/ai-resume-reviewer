# AI Resume Reviewer Backend

This is the production-ready Python FastAPI backend for the AI Resume Reviewer application. It features a multi-agent analysis pipeline implemented in LangGraph, semantic search using ChromaDB RAG, and is powered by the Groq Llama 3.3 70B LLM.

## Features

- **Asynchronous Processing**: Fast file uploads and background analysis tasks to prevent API request timeout.
- **Multi-Agent Architecture**: Custom agents (Parser, RAG, Analysis, Feedback, Report) written in LangGraph to separate concerns and ensure structured, reliable outputs.
- **Semantic Retrieval (RAG)**: Indexes and stores resume text in ChromaDB, retrieving role-specific resume contexts.
- **SQL Metadata DB**: Local SQLite database for tracking upload files, analysis task status, and compiled report storage.
- **Robust Schema Verification**: Request-response validations implemented through Pydantic.

## Directory Structure

```text
ai-resume-reviewer/
└── backend/
    ├── src/
    │   ├── agents/      # LangGraph nodes, agents, and state graph
    │   ├── routers/     # API route controllers (health, resume, analysis)
    │   ├── services/    # VectorStore and indexing integrations
    │   ├── models/      # SQLite CRUD handlers
    │   ├── schemas/     # Pydantic schemas for REST exchange
    │   ├── core/        # App configs, logging configuration, and DB helpers
    │   ├── utils/       # PDF and DOCX file parsers
    │   ├── prompts/     # Base LLM prompt templates
    │   └── main.py      # Uvicorn entry point
    │
    ├── uploads/         # Saved upload resumes (automatically created)
    ├── vectorstore/     # ChromaDB and SQLite DB files (automatically created)
    ├── requirements.txt # Python project dependencies
    ├── .env             # Active environment settings
    ├── .env.example     # Configuration templates
    └── README.md        # Operations manual
```

---

## Quick Start Guide

Follow these steps to run the backend application:

### 1. Prerequisites
Ensure you have **Python 3.10+** installed on your system.

### 2. Set Up Virtual Environment
Navigate to the `backend` directory and create/activate a virtual environment:

**On Windows (PowerShell):**
```powershell
cd ai-resume-reviewer/backend
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On macOS/Linux:**
```bash
cd ai-resume-reviewer/backend
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
Run:
```bash
pip install -r requirements.txt
```

### 4. Configure Environmental Variables
Modify the `.env` file generated at the root of the `backend` directory:
- Paste your **Groq API Key** in `GROQ_API_KEY=`. You can fetch an API key from the [Groq Console](https://console.groq.com/).

### 5. Launch the Server
Execute:
```bash
python -m uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
```
Upon launching:
- The server will run at `http://127.0.0.1:8000`.
- The SQLite metadata database is automatically bootstrapped at `vectorstore/metadata.db`.
- The HuggingFace embedding model (`sentence-transformers/all-MiniLM-L6-v2`) will be downloaded locally automatically on the first run (~90MB).

---

## API Documentation

FastAPI automatically serves interactive Swagger documentation:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### Endpoint Summary

#### 1. System Health
- **Route**: `GET /health`
- **Description**: Verifies API availability.
- **Example Response**:
  ```json
  {
    "status": "healthy",
    "uptime_seconds": 12.34,
    "version": "1.0.0"
  }
  ```

#### 2. Upload Resume
- **Route**: `POST /upload-resume`
- **Content-Type**: `multipart/form-data`
- **Request Form**: `file` (Supports `.pdf` and `.docx` only)
- **Example Response**:
  ```json
  {
    "resume_id": "8c4bc622-cbe2-475c-ad8d-ee7b8f362da5",
    "filename": "my_resume.pdf",
    "message": "Resume uploaded and registered successfully."
  }
  ```

#### 3. Analyze Resume
- **Route**: `POST /analyze-resume`
- **Content-Type**: `application/json`
- **Request Body**:
  ```json
  {
    "resume_id": "8c4bc622-cbe2-475c-ad8d-ee7b8f362da5",
    "job_role": "AI Engineer"
  }
  ```
  *(Supported Roles: `AI Engineer`, `GenAI Engineer`, `Machine Learning Engineer`, `Data Scientist`, `Software Engineer`, `Quantitative Researcher`, `Quantitative Developer`)*
- **Example Response (202 Accepted)**:
  ```json
  {
    "analysis_id": "fe94d3f2-1a40-4da2-9b48-356df1e158cb",
    "resume_id": "8c4bc622-cbe2-475c-ad8d-ee7b8f362da5",
    "job_role": "AI Engineer",
    "status": "processing"
  }
  ```

#### 4. Fetch Analysis Report
- **Route**: `GET /analysis/{analysis_id}`
- **Example Response (While Processing)**:
  ```json
  {
    "analysis_id": "fe94d3f2-1a40-4da2-9b48-356df1e158cb",
    "resume_id": "8c4bc622-cbe2-475c-ad8d-ee7b8f362da5",
    "job_role": "AI Engineer",
    "status": "processing",
    "report": null,
    "error": null
  }
  ```
- **Example Response (When Completed)**:
  ```json
  {
    "analysis_id": "fe94d3f2-1a40-4da2-9b48-356df1e158cb",
    "resume_id": "8c4bc622-cbe2-475c-ad8d-ee7b8f362da5",
    "job_role": "AI Engineer",
    "status": "completed",
    "report": {
      "job_role": "AI Engineer",
      "overall_score": 82,
      "ats_score": 75,
      "skills_score": 88,
      "experience_score": 80,
      "project_score": 85,
      "education_score": 78,
      "strengths": [
        "Strong experience building deep learning pipelines in PyTorch.",
        "Demonstrated project relevance building custom NLP transformers."
      ],
      "weaknesses": [
        "Resume layout uses dual columns which can confuse older ATS scanners.",
        "Work experience bullet points lack quantitative metrics."
      ],
      "missing_skills": [
        "Kubernetes",
        "Triton Inference Server",
        "LangGraph"
      ],
      "recommendations": [
        {
          "issue": "Lack of quantitative metrics in job experience.",
          "why_it_matters": "Recruiters and hiring managers search for concrete business impact and quantifiable successes.",
          "improvement": "Rewrite experience items to include metrics like latencies, cost savings, or accuracy gains.",
          "example_content": "Before: 'Improved models.' After: 'Optimized transformer inference latencies by 35% using TensorRT, saving $12k/month in cloud compute.'"
        }
      ],
      "final_feedback": "Overall, the candidate demonstrates robust Python and Deep Learning competence. Focusing on layout simplify, adding clear quantifiers to project results, and acquiring cloud serving/orchestration tools will significantly optimize their competitiveness."
    },
    "error": null
  }
  ```
