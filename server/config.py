import json
import os
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from adalflow import Embedder
from adalflow.components.model_client import (
    OpenAIClient,
    GoogleGenAIClient,
    OllamaClient,
)

BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = Path(os.environ.get("CONFIG_DIR", BASE_DIR / "config"))

EMBEDDER_CLIENTS = {
    "OpenAIClient": OpenAIClient,
    "GoogleGenAIClient": GoogleGenAIClient,
    "OllamaClient": OllamaClient,
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
    return os.environ.get("EMBEDDER_TYPE", "google").lower()


def get_embedder_config() -> Dict[str, Any]:
    return EMBEDDER_CONFIG

def get_embedder(embedder_type = None) -> Embedder:
    provider = embedder_type or os.environ.get("EMBEDDER_TYPE", "openai")
    provider = provider.name.lower() if hasattr(provider, "name") else str(provider).lower()
    key_map = {
        "openai": "embedder",
        "google": "embedder_google",
        "ollama": "embedder_ollama",
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

