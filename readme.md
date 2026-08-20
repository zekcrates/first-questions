# FewQuestions

Ask questions about a GitHub repo to actively understand it — instead of passively reading the code.

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

