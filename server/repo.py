from collections.abc import Callable
from enum import Enum, auto
from functools import wraps
import os 
from pathlib import Path 
import re 
import subprocess
from urllib.parse import quote, urlparse, urlunparse
from git import Repo as GitRepo, GIT_OK, GitCommandError

def get_root_path() -> str:
    return str(Path(__file__).resolve().parent)

CLONE_PATH = os.path.join(get_root_path(), "repos", "repo")

class RepoType(Enum):
    GITHUB = auto() 
    GITLAB = auto() 
    BITBUCKET = auto()


def _exception_cleanup(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (subprocess.CalledProcessError, GitCommandError) as e:
            raw_err = getattr(e, "stderr", None) or str(e)
            if isinstance(raw_err, bytes):
                error_msg = raw_err.decode("utf-8")
            else:
                error_msg = str(raw_err)

            token = kwargs.get("access_token", None)
            if token:
                token_mask = "***TOKEN***"
                error_msg = error_msg.replace(token, token_mask)
                encoded_token = quote(token, safe="")
                error_msg = error_msg.replace(encoded_token, token_mask)
            raise ValueError(error_msg) from e
    return wrapper 


@_exception_cleanup
def _clone_from_github(remote_url: str, local_path: str, *, access_token: str | None = None, **kwargs) -> GitRepo: 
    if access_token:
        parsed = urlparse(remote_url)
        remote_url = urlunparse(
            (
                parsed.scheme,
                f"{access_token}@{parsed.netloc}",
                parsed.path,
                "", "", ""
            )
        )
    return GitRepo.clone_from(url=remote_url, to_path=local_path, **kwargs)  


def _is_path_url(path: str) -> bool:
    if not isinstance(path, str):
        return False 
    if re.match(r"^[\w-]+@[\w.-]+:[\w.-]+/.+", path):
        return True
    try: 
        result = urlparse(path)
        return result.scheme in {"http", "https", "ftp", "git"} and bool(result.netloc)
    except Exception:
        return False 


class Repo:
    def __init__(self, repo_url: str, repo_type: RepoType, access_token: str | None = None):
        self.repo_url = repo_url 
        self.repo_type = repo_type
        self.access_token = access_token

        os.makedirs(CLONE_PATH, exist_ok=True)
        self.root_path = CLONE_PATH

    @staticmethod
    def get_repo_name(repo_url: str, repo_type: RepoType) -> str | None:
        if not _is_path_url(repo_url):
            return None

        url_parts = repo_url.rstrip("/").split("/")
        
        if repo_type in {RepoType.GITHUB, RepoType.GITLAB, RepoType.BITBUCKET} and len(url_parts) >= 5:
            owner = url_parts[-2]
            repo = url_parts[-1].replace(".git", "")
            return f"{owner}_{repo}"

        return url_parts[-1].replace(".git", "")

    @property 
    def name(self) -> str | None:
        return self.get_repo_name(self.repo_url, self.repo_type)

    def download(self) -> None:
        if not self.is_downloaded():
            os.makedirs(self.save_path, exist_ok=True)
            if not GIT_OK:
                raise RuntimeError("Missing `git` in current environment")

            kwargs = {
                "remote_url": self.repo_url, 
                "local_path": self.save_path, 
                "access_token": self.access_token, 
                "multi_options": ["--depth=1", "--single-branch"],
            } 

            if self.repo_type == RepoType.GITHUB:
                _clone_from_github(**kwargs)
            elif self.repo_type == RepoType.GITLAB:
                pass 
            else:
                raise NotImplementedError(f"Unsupported repo type: {self.repo_type}")

    @property
    def save_path(self) -> str:
        if not self.name:
            raise ValueError("Invalid repository URL: cannot compute save path")
        return os.path.join(self.root_path, self.name)

    def is_downloaded(self) -> bool:
        return self.name is not None and os.path.exists(self.save_path) and bool(os.listdir(self.save_path))

    def __repr__(self) -> str:
        return f"{self.repo_type.name}: {self.name}"