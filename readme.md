# FewQuestions

Get few questions about a repo that can be tested to actively understand a codebase rather than
reading theory about it .


- **Client:** React + Vite + Tailwind CSS (`client/`)
- **Server:** FastAPI + adalflow RAG (`server/`)

## Requirements

- Node.js 18+
- Python 3.11+

## Setup

```bash
# Client
cd client
npm install
npm run dev            # http://localhost:5173

# Server
cd server
python -m venv venv
venv\Scripts\activate  
pip install -r requirements.txt
python -m uvicorn main:app --reload  # http://localhost:8000
```

