from dotenv import load_dotenv

load_dotenv()

import asyncio
import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from repo import Repo, RepoType
from rag.pipeline import RepoManager, get_repo_questions_path
from rag.questions import get_questions, load_cached_questions

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class PrepareRequest(BaseModel):
    repo_url: str
    language: str = "en"
    access_token: Optional[str] = None


class QuestionsRequest(BaseModel):
    repo_url: str
    language: str = "en"
    provider: Optional[str] = None
    model: Optional[str] = None
    force: bool = False
    access_token: Optional[str] = None


@app.get("/api/hello")
async def hello():
    return {"message": "Hello from FastAPI server!"}


@app.get("/api/repos")
async def list_repos():
    """List already indexed/cached repos (file DB) for Home one-click access."""
    from pathlib import Path

    try:
        # scan clone dir + databases
        base = Path(Repo(repo_url="https://github.com/x/y", repo_type=RepoType.GITHUB).root_path)
        if not base.exists():
            return {"repos": []}
        repos = []
        for entry in base.iterdir():
            if not entry.is_dir():
                continue
            name = entry.name  # owner_repo
            # need at least an index pkl or questions json to be considered a repo
            db = base / "databases" / f"{name}.pkl"
            has_questions = any((base / "databases").glob(f"{name}__*.questions.json"))
            if not db.exists() and not has_questions:
                continue
            # split owner_repo -> owner, repo
            if "_" in name:
                owner, repo_name = name.split("_", 1)
            else:
                owner, repo_name = "unknown", name
            repos.append(
                {
                    "owner": owner,
                    "name": repo_name,
                    "repo_url": f"https://github.com/{owner}/{repo_name}",
                    "slug": f"{owner}/{repo_name}",
                    "indexed": db.exists(),
                    "has_questions": bool(has_questions),
                }
            )

        def _sort_key(r):
            # most recent by pkl mtime
            try:
                p = base / "databases" / f"{r['owner']}_{r['name']}.pkl"
                return p.stat().st_mtime if p.exists() else 0
            except Exception:
                return 0

        repos.sort(key=_sort_key, reverse=True)
        return {"repos": repos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/prepare")
async def prepare(req: PrepareRequest):
    repo_url = (req.repo_url or "").strip()
    if not repo_url:
        raise HTTPException(status_code=400, detail="repo_url is required")

    # simple validation — we only support GitHub for now
    repo_type = RepoType.GITHUB
    try:
        repo = Repo(repo_url=repo_url, repo_type=repo_type)
        if not repo.name:
            raise ValueError("Invalid repo_url")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # check if already indexed (cached .pkl)
    already_indexed = os.path.exists(
        os.path.join(repo.root_path, "databases", f"{repo.name}.pkl")
    )

    try:
        # clone + embed is blocking (local torch + FAISS) — run in thread
        def _do_prepare():
            rm = RepoManager()
            rm.prepare_database(repo_url, repo_type, access_token=req.access_token)
            return rm

        await asyncio.to_thread(_do_prepare)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "status": "ready",
        "repo_name": repo.name,
        "cached": already_indexed,
        "message": "Index ready (cached)" if already_indexed else "Index built",
    }


@app.post("/api/questions")
async def questions(req: QuestionsRequest):
    repo_url = (req.repo_url or "").strip()
    if not repo_url:
        raise HTTPException(status_code=400, detail="repo_url is required")

    language = (req.language or "en").lower().strip() or "en"
    repo_type = RepoType.GITHUB

    try:
        repo = Repo(repo_url=repo_url, repo_type=repo_type)
        if not repo.name:
            raise ValueError("Invalid repo_url")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # fast path — file is our DB: if .questions.json exists, return it (no LLM call)
    cached = await asyncio.to_thread(load_cached_questions, repo, language)
    if cached is not None and not req.force:
        return {"questions": cached, "cached": True, "repo_name": repo.name}

    # cache miss — generate 30-40 hypotheses (blocking: FAISS + LLM)
    try:
        def _do_gen():
            return get_questions(
                repo_url=repo_url,
                repo_type=repo_type,
                language=language,
                provider=req.provider,
                model=req.model,
                force_regenerate=req.force,
            )

        qs = await asyncio.to_thread(_do_gen)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # surface LLM / embed errors clearly (e.g. missing GOOGLE_API_KEY)
        raise HTTPException(status_code=500, detail=str(e))

    # was it cached or freshly generated? check if file now exists and we didn't force
    was_cached = cached is not None and not req.force
    return {"questions": qs, "cached": was_cached, "repo_name": repo.name}