import json
import os
import re
from pathlib import Path
from typing import List, Dict, Any

from repo import Repo, RepoType
from rag.pipeline import RepoManager, get_repo_questions_path
from prompts import QUESTIONS_GENERATOR_PROMPT
from config import get_generator

_LANG_NAMES = {
    "en": "English",
}


def _language_name(code: str) -> str:
    c = (code or "en").lower().strip()
    return _LANG_NAMES.get(c, c.capitalize())


def _build_context(docs: List[Any], max_chars: int = 12000) -> str:
    parts = []
    total = 0
    for d in docs:
        path = ""
        if getattr(d, "meta_data", None):
            path = d.meta_data.get("file_path", "") or d.meta_data.get("title", "") or ""
        text = getattr(d, "text", "") or ""
        # keep it readable but not huge
        if len(text) > 2000:
            text = text[:2000]
        chunk = f"File: {path}\n{text}"
        if total + len(chunk) > max_chars:
            break
        parts.append(chunk)
        total += len(chunk)
    return "\n\n---\n\n".join(parts)


def _parse_questions(raw: str) -> List[Dict[str, Any]]:
    # strip markdown fences if LLM wrapped JSON in ```json
    t = raw.strip()
    if "```" in t:
        # extract first ``` ... ``` block
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", t)
        if m:
            t = m.group(1).strip()
    # sometimes LLM prefixes with text before array
    start = t.find("[")
    end = t.rfind("]")
    if start != -1 and end != -1:
        t = t[start : end + 1]
    data = json.loads(t)
    if not isinstance(data, list):
        raise ValueError("Questions output is not a JSON array")
    # light validation — keep only items with required keys
    out = []
    for i, item in enumerate(data, 1):
        if not isinstance(item, dict):
            continue
        q = item.get("question") or item.get("hypothesis") or ""
        if not q:
            continue
        out.append(
            {
                "id": item.get("id", i),
                "question": q,
                "target_files": item.get("target_files", []),
                "target_functions": item.get("target_functions", []),
            }
        )
    return out


def load_cached_questions(repo: Repo, language: str = "en") -> List[Dict[str, Any]] | None:
    path = get_repo_questions_path(repo, language)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list) and len(data) >= 20:
            return data
    except Exception as e:
        print(f"[questions] failed to load cache {path}: {e}")
    return None


def save_questions(repo: Repo, language: str, questions: List[Dict[str, Any]]) -> str:
    path = get_repo_questions_path(repo, language)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    return path


def get_questions(
    repo_url: str,
    repo_type: RepoType = RepoType.GITHUB,
    language: str = "en",
    provider: str | None = None,
    model: str | None = None,
    force_regenerate: bool = False,
) -> List[Dict[str, Any]]:
    """
    Simple flow: enter repo -> index (or use cached index) -> if questions cached, return those -> else generate 30-40 via LLM -> save as JSON file -> return.
    No DB, no auth — file is the DB.
    """
    repo = Repo(repo_url=repo_url, repo_type=repo_type)
    if not repo.name:
        raise ValueError(f"Invalid repo_url: {repo_url}")

    # check questions cache first (skip generation if exists) — respects language
    if not force_regenerate:
        cached = load_cached_questions(repo, language)
        if cached is not None:
            return cached

    # ensure index exists (uses existing RepoManager index cache: .pkl)
    rm = RepoManager()
    rm.create_repo(repo_url, repo_type)
    docs = rm.prepare_db_index()
    if not docs:
        raise ValueError("No docs to generate questions from")

    context = _build_context(docs)
    language_name = _language_name(language)
    repo_name = repo.name or repo_url

    # provider-agnostic LLM (google default = free)
    generator = get_generator(provider=provider, model=model, template=QUESTIONS_GENERATOR_PROMPT)

    prompt_kwargs = {
        "repo_type": repo_type.name.lower() if hasattr(repo_type, "name") else str(repo_type),
        "repo_url": repo_url,
        "repo_name": repo_name,
        "language_name": language_name,
        "context_str": context,
    }

    out = generator(prompt_kwargs=prompt_kwargs)
    raw = out.data if out.data is not None else (out.raw_response or "")
    if not raw:
        raise ValueError(f"LLM returned empty output (error={out.error})")
    if out.error:
        # still try to parse raw, but surface error if parse fails
        pass

    questions = _parse_questions(raw)
    if len(questions) < 20:
        print(f"[questions] warning: only {len(questions)} hypotheses parsed, expected 30-40")

    save_questions(repo, language, questions)
    return questions
