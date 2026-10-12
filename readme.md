# FewQuestions

FewQuestions helps you understand a codebase by giving you hypotheses to investigate.

The LLM creates some testable claims about the repository. Each claim may be true or false. Your goal is to inspect the code, run tests, and investigate until you can confirm or reject the hypothesis.

## Why this approach?


```text
hypothesis → inspect the code → run tests or trace the flow → confirm or reject it
```

This makes understanding a repository active instead of passive. You are not just reading an AI summary and hoping it is correct. You are building your own understanding by checking the claim against the source code.

That is the main product idea behind FewQuestions: a focused investigation loop for unfamiliar codebases, useful for onboarding, code review, debugging assumptions, and exploring open-source projects.

For example:

> **Hypothesis:** If a repository already has cached hypotheses, the API returns them without calling the AI again.
>
> **Files to check:** `server/main.py`, `server/rag/questions.py`
>
> **Functions to check:** `questions()`, `load_cached_questions()`, `get_questions()`

You can test this hypothesis by following the `cached` check in `server/main.py` and seeing whether `get_questions()` is called only when the cache is missing or regeneration is forced. The hypothesis may be true or false—the goal is to investigate the code and find out.

## How it works

1. Enter a GitHub repository URL in the web app.
2. The server clones the repository locally.
3. It reads useful source and documentation files.
4. It splits the files into smaller pieces and creates embeddings for them.
5. The embeddings are saved locally so the repository does not need to be processed again.
6. An AI model reads a sample of the indexed code and creates 30–40 hypotheses.
7. The hypotheses are saved locally and shown in the browser.

The first run can take a few minutes because the repository must be cloned and embedded. Later visits are faster because the index and hypotheses are cached.

## Project structure

```text
client/                 React web application
  src/App.jsx           Main user interface
  src/api/              Functions for calling the server
  vite.config.js        Development server and API proxy

server/                 Python backend
  main.py               FastAPI routes
  repo.py               GitHub cloning and repository names
  config.py             Provider and file-filter configuration
  prompts.py            Prompt used to generate hypotheses
  embedder_client.py    Local SentenceTransformer embedder
  rag/
    pipeline.py         File reading, splitting, embedding, and caching
    questions.py        Hypothesis generation and caching
    rag.py              FAISS retrieval component for future use
  config/                JSON configuration files
```


## Where data is stored

Downloaded repositories and generated cache files are stored under:

```text
server/repos/repo/
server/repos/repo/databases/
```

For a repository such as `owner/repository`, the cache contains files similar to:

```text
owner_repository/                  Cloned repository
databases/owner_repository.pkl     Indexed and embedded code
databases/owner_repository__en.questions.json
```

There is no external database. The local files are the database for now.

## Supported providers

The project can also be configured to use:

- Google Gemini
- OpenAI
- Ollama
- OpenRouter

Embeddings can use:

- A local SentenceTransformer model (the default)
- OpenAI
- Google
- Ollama

Provider and model settings are in `server/config/generator.json` and `server/config/embedder.json`.

Set the required API key or provider settings in `server/.env`. For example:

```env
GOOGLE_API_KEY=your_key_here
```

Do not commit `.env` files or API keys.

## Requirements

- Node.js 18 or newer
- Python 3.11 or newer
- An API key for the selected AI provider, unless using local/Ollama models

## Running locally

Open two terminals.

### Terminal 1: backend

```bash
cd server
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
# source venv/bin/activate

pip install -r requirements.txt
python -m uvicorn main:app --reload
```

The backend runs at `http://localhost:8000`.

### Terminal 2: frontend

```bash
cd client
npm install
npm run dev
```

The frontend runs at `http://localhost:5173`.

The Vite development server forwards `/api` requests to the backend.

## Current status

FewQuestions is still an early experiment. The active-hypothesis approach is the core idea, and the implementation will continue to improve as we learn which kinds of hypotheses are most useful for developers.

## You can use this approach without AI

You do not need an AI model to explore a repository this way.

Open a repository, get a basic understanding of its folders and entry points, then write down a few claims about how it works. Check the relevant files, trace the code, or run tests to confirm or reject each claim.

FewQuestions simply helps you create the first set of hypotheses faster. You will need hypotheses created by your own mind later. 

