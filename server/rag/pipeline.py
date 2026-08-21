from enum import Enum, auto
import os 
from pathlib import Path 

import  adalflow as adal 
import tiktoken
from adalflow.components.data_process import TextSplitter, ToEmbeddings
from adalflow.core.db import LocalDB
from adalflow.core.types import Document, List

from repo import Repo, RepoType
from config import (
    EMBEDDER_CONFIG,
    REPO_CONFIG,
    get_embedder,
    get_embedder_config,
    get_embedder_type,
    iterate_files,
)
MAX_EMBEDDING_TOKENS = 8192

class EmbedderType(Enum):
    OLLAMA = auto() 
    OPENAI = auto()
    ANTHROPIC = auto() 
    GOOGLE = auto()
    LOCAL = auto()

def count_tokens(text: str, embedder_type: EmbedderType| None = None ):
    try:
        if embedder_type is None:
            # get embedded from config 
            pass 
        SAME_ENCODINGS = {EmbedderType.OLLAMA, EmbedderType.GOOGLE, EmbedderType.ANTHROPIC, EmbedderType.LOCAL}

        if embedder_type in SAME_ENCODINGS:
            encoding = tiktoken.get_encoding("cl100k_base")
        else:
            encoding = tiktoken.encoding_for_model("text-embedding-3-small")

        return len(encoding.encode(text))

    except Exception as e:
        return len(text)//4


def get_repo_db(repo: Repo)-> str:
    if not repo.root_path :
        raise ValueError(f"Repo root path is empty: {repo}")
    save_db_file = os.path.join(repo.root_path, "databases", f"{repo.name}.pkl")
    return save_db_file


def get_repo_questions_path(repo: Repo, language: str = "en") -> str:
    if not repo.root_path:
        raise ValueError(f"Repo root path is empty: {repo}")
    if not repo.name:
        raise ValueError(f"Repo name is empty: {repo}")
    lang = (language or "en").lower().strip() or "en"
    # same databases folder as the index — file is our DB (no real DB needed)
    return os.path.join(repo.root_path, "databases", f"{repo.name}__{lang}.questions.json")


class LineTrackingTextSplitter(TextSplitter):
    def call(self, documents):
        parent_text = {doc.id  : (doc.text or "") for doc in documents}
        split_docs = super().call(documents)
        chunks_by_parent = {}

        for chunk in split_docs:
            chunks_by_parent.setdefault(chunk.parent_doc_id, []).append(chunk)

        for parent_id, chunks in chunks_by_parent.items():
            text = parent_text.get(parent_id, "")
            cursor = 0
            for chunk in sorted(chunks, key=lambda c : c.order):
                chunk.meta_data = dict(chunk.meta_data or {})
                pos = text.find(chunk.text, cursor)
                if pos == -1:
                    pos = text.find(chunk.text) 
                if pos == -1:
                    continue
                start_line = text.count("\n", 0, pos) + 1
                end_line = start_line + chunk.text.count("\n")
                chunk.meta_data["start_line"] = start_line
                chunk.meta_data["end_line"] = end_line
                cursor = pos + 1
        return split_docs

def repo_index_exist(repo: Repo) -> bool:
    return os.path.exists(get_repo_db(repo))

def prepare_data_pipeline(embedder_type: EmbedderType | None = None) -> adal.Sequential:
    embedder_type = embedder_type or get_embedder_type()
    embedder_config = get_embedder_config()

    splitter = LineTrackingTextSplitter(**EMBEDDER_CONFIG["text_splitter"])
    embedder = get_embedder(embedder_type=embedder_type)
    batch_size = embedder_config.get("batch_size", 500)

    emb_transformer = ToEmbeddings(embedder=embedder, batch_size=batch_size)
    return adal.Sequential(splitter,emb_transformer)


def read_all_documents(
    path: str,
    embedder_type: str = None,
    excluded_dirs: list[str] | None = None,
    excluded_files: list[str] | None = None,
    included_dirs: list[str] | None = None,
    included_files: list[str] | None = None,
):
    documents = []    
    code_extensions = set(REPO_CONFIG.get("code_extensions", []))

    for relative_path in iterate_files(
        path,
        excluded_dirs=excluded_dirs,
        excluded_files=excluded_files,
        included_dirs=included_dirs,
        included_files=included_files,
    ):

        file_path = Path(path) / relative_path
        try:
            with open(file_path, "r", encoding="utf-8") as f :
                content = f.read() 

            token_count = count_tokens(content, embedder_type)
            if token_count > MAX_EMBEDDING_TOKENS* 10:
                continue

            file_ext = file_path.suffix.lower() 
            is_code_file = file_ext in code_extensions


            if is_code_file:
                is_normal_code = (not relative_path.startswith("test_") and not 
                                  relative_path.startswith("app_")
                                  and "test" not in relative_path.lower())
            else:
                is_normal_code = False 


            doc =Document(
                text=content, 
                meta_data={
                    "file_path": relative_path,
                    "type": file_ext,
                    "is_code_file": is_code_file,
                    "is_normal_code": is_normal_code,
                    "title": relative_path,
                    "token_count": token_count,
                },
            )

            documents.append(doc)

        except Exception as e :
            print(e)

    return documents


def transform_documents_and_save_to_db(
    documents: List[Document],
    db_path: str,
    embedder_type: str = None,
) -> LocalDB:
    data_transformer = prepare_data_pipeline(embedder_type)
    db = LocalDB()
    db.register_transformer(transformer=data_transformer, key="split_and_embed")
    db.load(documents)
    db.transform(key="split_and_embed")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    db.save_state(filepath=db_path)
    return db

    
class RepoManager:
    def __init__(self):
        self.db = None 
        self.repo_url = None 
        self.saved_repo_paths = None 
    def reset_database(self):
        self.db = None 
        self.repo_url = None 
        self.saved_repo_paths = None 


    def create_repo(self, repo_url: str , repo_type: RepoType, access_token: str | None = None) -> None :
        try:
            repo_url = repo_url.strip() 
            repo = Repo(
                repo_url=repo_url, repo_type=repo_type, access_token=access_token
            )
            if not repo.is_downloaded():
                repo.download()

            final_db_file_path = get_repo_db(repo)
            os.makedirs(os.path.dirname(final_db_file_path), exist_ok=True)

            self.saved_repo_paths = {
                "save_repo_dir": repo.save_path,
                "save_db_file": final_db_file_path,
            }
            self.repo_url = repo_url

        except : 
            raise ValueError("Something went wrong when creating repo")



    def prepare_database(
        self,
        repo_url: str,
        repo_type: RepoType,
        access_token: str = None,
        embedder_type: EmbedderType | None = None,
        excluded_dirs: List[str] = None,
        excluded_files: List[str] = None,
        included_dirs: List[str] = None,
        included_files: List[str] = None,
    ) -> List[Document]:

        self.reset_database()
        self.create_repo(repo_url, repo_type, access_token)
        return self.prepare_db_index(
            embedder_type=embedder_type,
            excluded_dirs=excluded_dirs,
            excluded_files=excluded_files,
            included_dirs=included_dirs,
            included_files=included_files,
        )


    def prepare_db_index(
        self,
        embedder_type: EmbedderType = None,
        excluded_dirs: List[str] = None,
        excluded_files: List[str] = None,
        included_dirs: List[str] = None,
        included_files: List[str] = None,
    ) -> List[Document]:


        cached_docs = self.load_cached_index() 
        if cached_docs:
            return cached_docs

        #cache miss 
        return self.build_and_save_index(
            embedder_type=embedder_type,
            excluded_dirs=excluded_dirs,
            excluded_files=excluded_files,
            included_dirs=included_dirs,
            included_files=included_files,
        )

    def load_cached_index(self) -> List[Document] | None :
        db_path = self.saved_repo_paths.get("save_db_file") if self.saved_repo_paths else None

        if not db_path or not os.path.exists(db_path):
            return None

        try: 
            self.db = LocalDB.load_state(db_path)
            documents = self.db.get_transformed_data(key="split_and_embed")
            if documents and any(getattr(doc, "vector", None) is not None for doc in documents):
                return documents
        except Exception as e:
            print(f"Failed to load cached index: {e}")

        return None 

    def build_and_save_index(
        self,
        embedder_type: EmbedderType | None = None,
        excluded_dirs: List[str] | None = None,
        excluded_files: List[str] | None = None,
        included_dirs: List[str] | None = None,
        included_files: List[str] | None = None,
    ) -> List[Document]:

        repo_dir = self.saved_repo_paths.get("save_repo_dir") if self.saved_repo_paths else None
        if not repo_dir or not os.path.exists(repo_dir):
            raise FileNotFoundError(f"Source repository directory missing at: {repo_dir}")

        documents = read_all_documents(
            repo_dir,
            embedder_type=embedder_type,
            excluded_dirs=excluded_dirs,
            excluded_files=excluded_files,
            included_dirs=included_dirs,
            included_files=included_files,
        )
        db_path = self.saved_repo_paths["save_db_file"]
        self.db = transform_documents_and_save_to_db(documents, db_path, embedder_type=embedder_type)
        return self.db.get_transformed_data(key="split_and_embed")