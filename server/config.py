import json
import os
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

from adalflow import Embedder
from adalflow.components.model_client import (
    OpenAIClient,
    GoogleGenAIClient,
    OllamaClient,
)

from embedder_client import SentenceTransformerClient

BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = Path(os.environ.get("CONFIG_DIR", BASE_DIR / "config"))

EMBEDDER_CLIENTS = {
    "OpenAIClient": OpenAIClient,
    "GoogleGenAIClient": GoogleGenAIClient,
    "OllamaClient": OllamaClient,
    "SentenceTransformerClient": SentenceTransformerClient,
}

GENERATOR_CLIENTS = {
    "GoogleGenAIClient": GoogleGenAIClient,
    "OpenAIClient": OpenAIClient,
    "OllamaClient": OllamaClient,
}

# provider -> client class (openrouter reuses OpenAIClient with custom base_url)
_PROVIDER_TO_CLIENT = {
    "google": GoogleGenAIClient,
    "openai": OpenAIClient,
    "ollama": OllamaClient,
    "openrouter": OpenAIClient,
}




def _load_json_config(filename: str)-> Dict[str, Any]:
    file_path = CONFIG_DIR/filename 

    if not file_path.exists():
        return {}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as  e : 
        return {}



EMBEDDER_CONFIG = _load_json_config("embedder.json")
GENERATOR_CONFIG = _load_json_config("generator.json")
REPO_CONFIG = _load_json_config("repo.json")


def get_embedder_type() -> str:
    return os.environ.get("EMBEDDER_TYPE", "local").lower()


def get_embedder_config() -> Dict[str, Any]:
    return EMBEDDER_CONFIG

def get_embedder(embedder_type = None) -> Embedder:
    provider = embedder_type or os.environ.get("EMBEDDER_TYPE", "openai")
    provider = provider.name.lower() if hasattr(provider, "name") else str(provider).lower()
    key_map = {
        "openai": "embedder",
        "google": "embedder_google",
        "ollama": "embedder_ollama",
        "local": "embedder_local",
    }

    cfg_key = key_map.get(provider, "embedder")
    emb_cfg = EMBEDDER_CONFIG.get(cfg_key, {})

    if not emb_cfg:
        raise ValueError(f"No configuration found for embedder provider: '{provider}'")


    client_name = emb_cfg.get("client_class", "OpenAIClient")
    client_cls = EMBEDDER_CLIENTS.get(client_name)

    if not client_cls:
        raise ValueError(f"Unsupported client class '{client_name}' for provider '{provider}'")

    client_instance = client_cls(**emb_cfg.get("initialize_kwargs", {}))
    embedder = Embedder(
        model_client=client_instance,
        model_kwargs=emb_cfg.get("model_kwargs", {}),
    )

    if "batch_size" in emb_cfg:
        embedder.batch_size = emb_cfg["batch_size"]

    return embedder



def get_generator_config(provider: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve generator/LLM parameters for a specific provider."""
    target_provider = provider or GENERATOR_CONFIG.get("default_provider", "google")
    providers = GENERATOR_CONFIG.get("providers", {})

    if target_provider not in providers:
        target_provider = GENERATOR_CONFIG.get("default_provider", "google")

    return providers.get(target_provider, {})


def _resolve_generator_model_kwargs(provider: str, model: str) -> Dict[str, Any]:
    providers = GENERATOR_CONFIG.get("providers", {})
    provider_cfg = providers.get(provider, {})
    models = provider_cfg.get("models", {})
    model_cfg = models.get(model, {}) or {}

    # ollama stores options nested, others are flat — normalize both
    kwargs: Dict[str, Any] = {"model": model}
    if "options" in model_cfg and isinstance(model_cfg["options"], dict):
        # ollama style: {options: {temperature, ...}}
        kwargs.update(model_cfg["options"])
        # also copy any top-level keys that are not options (rare)
        for k, v in model_cfg.items():
            if k != "options":
                kwargs.setdefault(k, v)
    else:
        kwargs.update(model_cfg)
    return kwargs


def get_generator(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    use_cache: bool = False,
    template: Optional[str] = None,
):
    """
    Provider-agnostic LLM factory (used for QUESTIONS_GENERATOR_PROMPT — 30-40 hypotheses).
    - provider: google | openai | ollama | openrouter (defaults to GENERATOR_CONFIG.default_provider or env LLM_PROVIDER/GENERATOR_TYPE)
    - model: specific model name (defaults to provider's default_model or env LLM_MODEL)
    - template: optional prompt template; if None, Generator uses its default (caller passes QUESTIONS_GENERATOR_PROMPT when generating)
    - Respects env keys: GOOGLE_API_KEY, OPENAI_API_KEY, OPENROUTER_API_KEY, OLLAMA_HOST
    - google is default so a free GOOGLE_API_KEY works out of the box; other devs can set OPENAI_API_KEY etc.
    """
    raw_provider = (
        provider
        or os.getenv("LLM_PROVIDER")
        or os.getenv("GENERATOR_TYPE")
        or GENERATOR_CONFIG.get("default_provider", "google")
    )
    provider = str(raw_provider).lower()
    providers = GENERATOR_CONFIG.get("providers", {})

    if provider not in providers:
        fallback = GENERATOR_CONFIG.get("default_provider", "google")
        provider = fallback if fallback in providers else next(iter(providers), "google")

    provider_cfg = providers.get(provider, {})
    resolved_model = model or os.getenv("LLM_MODEL") or provider_cfg.get("default_model")
    if not resolved_model:
        raise ValueError(f"No model configured for provider '{provider}'")

    model_kwargs = _resolve_generator_model_kwargs(provider, resolved_model)

    # instantiate the correct client; openrouter reuses OpenAIClient with custom base_url
    if provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY must be set for provider 'openrouter'")
        client = OpenAIClient(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            env_api_key_name="OPENROUTER_API_KEY",
        )
    else:
        client_cls = _PROVIDER_TO_CLIENT.get(provider)
        if not client_cls:
            raise ValueError(f"Unsupported generator provider '{provider}'")
        # let the client read its env key (GOOGLE_API_KEY / OPENAI_API_KEY / OLLAMA_HOST)
        client = client_cls()

    # Import here to avoid circular imports at module load
    from adalflow.core.generator import Generator

    kwargs: Dict[str, Any] = dict(model_client=client, model_kwargs=model_kwargs, use_cache=use_cache)
    if template is not None:
        kwargs["template"] = template
    return Generator(**kwargs)


def _normalize_dir_pattern(pattern: str) -> str:
    pattern = pattern.replace("\\", "/")
    while pattern.startswith("./"):
        pattern = pattern[2:]
    return pattern.strip("/")


def _pattern_set(patterns: Optional[List[str]]) -> Set[str]:
    if not patterns:
        return set()
    return {_normalize_dir_pattern(p) for p in patterns}


def iterate_files(
    root_dir: str,
    excluded_dirs: Optional[List[str]] = None,
    excluded_files: Optional[List[str]] = None,
    included_dirs: Optional[List[str]] = None,
    included_files: Optional[List[str]] = None,
) -> List[str]:
    file_filters = REPO_CONFIG.get("file_filters", {})
    code_exts: Set[str] = set(REPO_CONFIG.get("code_extensions", []))
    doc_exts: Set[str] = set(REPO_CONFIG.get("doc_extensions", []))
    allowed_exts: Set[str] = code_exts | doc_exts

    exc_dirs: Set[str] = _pattern_set(file_filters.get("excluded_dirs", []))
    exc_files: Set[str] = set(file_filters.get("excluded_files", []))

    if excluded_dirs:
        exc_dirs |= _pattern_set(excluded_dirs)
    if excluded_files:
        exc_files |= set(excluded_files)

    results: List[str] = []
    root = Path(root_dir)

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        rel = path.relative_to(root)
        parts = rel.parts

        if any(_normalize_dir_pattern(part) in exc_dirs for part in parts):
            continue

        if any(fnmatch(path.name, pattern) for pattern in exc_files):
            continue

        if included_dirs and not any(
            _normalize_dir_pattern(part) in _pattern_set(included_dirs) for part in parts
        ):
            continue

        if included_files and not any(
            fnmatch(path.name, pattern) for pattern in included_files
        ):
            continue

        if path.suffix.lower() in allowed_exts:
            results.append(rel.as_posix())

    return results 

