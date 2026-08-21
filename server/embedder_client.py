import asyncio
from typing import Any, Dict, List, Optional

import torch  # noqa: F401
from sentence_transformers import SentenceTransformer

from adalflow.core.model_client import ModelClient
from adalflow.core.types import EmbedderOutput, Embedding, ModelType


class SentenceTransformerClient(ModelClient):
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: Optional[str] = None,
        normalize_embeddings: bool = True,
    ) -> None:
        super().__init__()
        self.model_name = model_name
        self.device = device
        self.normalize_embeddings = normalize_embeddings
        self._model: Optional[SentenceTransformer] = None

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self.model_name, device=self.device)
        return self._model

    def convert_inputs_to_api_kwargs(
        self,
        input: Any,
        model_kwargs: Dict = {},
        model_type: ModelType = ModelType.UNDEFINED,
    ) -> Dict[str, Any]:
        if model_type != ModelType.EMBEDDER:
            raise ValueError(f"model_type {model_type} is not supported")

        final_model_kwargs = dict(model_kwargs)
        final_model_kwargs["model"] = final_model_kwargs.get("model") or self.model_name
        final_model_kwargs["input"] = input
        return final_model_kwargs

    def call(
        self, api_kwargs: Dict = {}, model_type: ModelType = ModelType.UNDEFINED
    ):
        if model_type != ModelType.EMBEDDER:
            raise ValueError(f"model_type {model_type} is not supported")

        input = api_kwargs.get("input")
        if input is None:
            raise ValueError("input must be specified in api_kwargs")

        if isinstance(input, str):
            input = [input]

        model = self._get_model()
        embeddings = model.encode(
            input,
            normalize_embeddings=self.normalize_embeddings,
            convert_to_numpy=True,
        )
        return embeddings.tolist()

    async def acall(
        self, api_kwargs: Dict = {}, model_type: ModelType = ModelType.UNDEFINED
    ):
        return await asyncio.to_thread(self.call, api_kwargs, model_type)

    def parse_embedding_response(self, response: Any) -> EmbedderOutput:
        embeddings: List[Embedding] = []
        for idx, emb in enumerate(response):
            vector = emb.tolist() if hasattr(emb, "tolist") else list(emb)
            embeddings.append(Embedding(index=idx, embedding=vector))
        return EmbedderOutput(data=embeddings)

    def parse_chat_completion(self, completion: Any):
        raise NotImplementedError("SentenceTransformerClient only supports embeddings")

    def track_completion_usage(self, *args, **kwargs):
        return None