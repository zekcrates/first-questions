import asyncio
import os
from collections import defaultdict
from collections.abc import Sized
from uuid import uuid4

import adalflow as adal
from adalflow.components.retriever.faiss_retriever import FAISSRetriever
from adalflow.core.types import (
    AssistantResponse,
    DialogTurn,
    Document,
    RetrieverOutput,
    UserQuery,
)
from config import EMBEDDER_CONFIG, get_embedder, get_embedder_type
from repo import RepoType
from rag.pipeline import RepoManager 

_RAG_PREPARE_SEMAPHORE: asyncio.Semaphore | None = None


def _get_rag_semaphore() -> asyncio.Semaphore:
    global _RAG_PREPARE_SEMAPHORE
    if _RAG_PREPARE_SEMAPHORE is None:
        _RAG_PREPARE_SEMAPHORE = asyncio.Semaphore(
            int(os.environ.get("DEEPWIKI_MAX_CONCURRENT_RAG", "4"))
        )
    assert isinstance(_RAG_PREPARE_SEMAPHORE, asyncio.Semaphore)
    return _RAG_PREPARE_SEMAPHORE


def ollama_model_exists(model_name: str, ollama_host: str | None = None )-> bool :
    import httpx 
    import ollama 
    if ollama_host is None:
        ollama_host = os.getenv("OLLAMA_HOST",  "http://localhost:11434")

    try:
        ollama_host = ollama_host.removesuffix("/api")
        ret: ollama.ListResponse = ollama.Client(host=ollama_host, timeout=5).list()
        is_available = any(model_name == model.model for model in ret.models)
        return is_available
    except (httpx.ConnectTimeout, ConnectionError) as e:
        return False 
    except Exception as e :
        return False 


def _get_document_vector_size(document: Document)-> int :
    embedding_size = None 
    if hasattr(document.vector, "shape"):

        embedding_size = (
            document.vector.shape[0]
            if len(document.vector.shape) == 1
            else document.vector.shape[-1]
        )
    elif isinstance(document.vector, Sized):
        embedding_size =len(document.vector )


    return embedding_size 

class RAG(adal.Component):
    def __init__(self, provider="google", model=None):  
        self.provider = provider 
        self.model = model 
        self.embedder_type = get_embedder_type()
        self.embedder = get_embedder(embedder_type=self.embedder_type)
        self.initialize_repo_manager()

    def initialize_repo_manager(self):
        self.repo_manager = RepoManager()
        self.transformed_docs = []

    @staticmethod
    def _validate_documents(documents: list[Document]) -> list[Document]:
        if not documents:
            return []

        docs_embeddings = defaultdict(list)
        valid_docs_with_sizes = []
        for doc in documents:
            if not isinstance(doc, Document):
                continue
            embed_size = _get_document_vector_size(doc)
            if embed_size:
                valid_docs_with_sizes.append((doc, embed_size))

        for doc, embed_size in valid_docs_with_sizes:
            docs_embeddings[embed_size].append(doc)


        if not docs_embeddings:
            return []
        target_size = max(docs_embeddings, key=lambda x: len(docs_embeddings[x]))
        valid_docs = docs_embeddings.pop(target_size)
        return valid_docs
    def prepare_retriever(
        self,
        repo_url: str,
        repo_type: RepoType = RepoType.GITHUB,
        access_token: str | None = None,
        excluded_dirs: list[str] | None = None,
        excluded_files: list[str] | None = None,
        included_dirs: list[str] | None = None,
        included_files: list[str] | None = None,
    ):
        self.initialize_repo_manager()
        self.repo_url = repo_url
        self.transformed_docs = self.repo_manager.prepare_database(
            repo_url,
            repo_type,
            access_token,
            embedder_type=self.embedder_type,
            excluded_dirs=excluded_dirs,
            excluded_files=excluded_files,
            included_dirs=included_dirs,
            included_files=included_files,
        )

        self.transformed_docs = self._validate_documents(
            self.transformed_docs
        )
        if not self.transformed_docs:
            raise ValueError("No docs to index")

        try:
            self.retriever = FAISSRetriever(
                **EMBEDDER_CONFIG["retriever"],
                embedder=self.embedder,
                documents=self.transformed_docs,
                document_map_func=lambda doc: doc.vector,
            )

        except Exception as e:
            raise ValueError(f"Failed to build retriever: {e}") from e
    async def aprepare_retriever(
        self,
        repo_url: str,
        repo_type: RepoType = RepoType.GITHUB,
        access_token: str | None = None,
        excluded_dirs: list[str] | None = None,
        excluded_files: list[str] | None = None,
        included_dirs: list[str] | None = None,
        included_files: list[str] | None = None,
    ):
        async with _get_rag_semaphore():
            return await asyncio.to_thread(
                self.prepare_retriever,
                repo_url,
                repo_type=repo_type,
                access_token=access_token,
                excluded_dirs=excluded_dirs,
                excluded_files=excluded_files,
                included_dirs=included_dirs,
                included_files=included_files,
            )

    async def acall(self, query: str, language: str = "en") -> list[RetrieverOutput]:
        """Async version of the original `call` method."""
        return await asyncio.to_thread(self.call, query, language)

    def call(
        self, query: str | list[str], language: str = "en"
    ) -> list[RetrieverOutput]:
        try:
            retrieved_documents = self.retriever(query)

            retrieved_documents[0].documents = [
                self.transformed_docs[doc_index]
                for doc_index in retrieved_documents[0].doc_indices
            ]

            return retrieved_documents

        except Exception:
            return []