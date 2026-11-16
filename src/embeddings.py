"""Real embedding model via sentence-transformers (runs locally, no API key).

The same model, normalization and query handling are used for every strategy.
There is NO fallback to mock/random vectors: if the model cannot load, this raises.
"""
from typing import Protocol

from sentence_transformers import SentenceTransformer


class Embedder(Protocol):
    model_name: str
    dimensions: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text, in the same order."""
        ...

    def embed_query(self, question: str) -> list[float]:
        """Return a query vector compatible with the stored document vectors."""
        ...


# Query instruction recommended by the model authors for short-query -> passage retrieval.
# Documents are embedded without a prefix.
QUERY_PREFIXES = {
    "BAAI/bge-small-en-v1.5": "Represent this sentence for searching relevant passages: ",
}


class MyEmbedder:
    """Local sentence-transformers adapter. Vectors are L2-normalized (cosine-ready)."""

    def __init__(self, model_name: str, batch_size: int = 32, device: str | None = None) -> None:
        if not model_name:
            raise ValueError("EMBEDDING_MODEL is empty: set it in starter/.env")
        self.model_name = model_name
        self.model = SentenceTransformer(model_name, device=device)
        get_dim = getattr(self.model, "get_embedding_dimension", None) or \
            self.model.get_sentence_embedding_dimension  # renamed in newer sentence-transformers
        self.dimensions = int(get_dim())
        self.max_seq_length = int(self.model.max_seq_length)
        self.query_prefix = QUERY_PREFIXES.get(model_name, "")
        self.batch_size = batch_size

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = self.model.encode(texts, batch_size=self.batch_size, normalize_embeddings=True,
                                    convert_to_numpy=True, show_progress_bar=len(texts) > 64)
        return vectors.tolist()

    def embed_query(self, question: str) -> list[float]:
        vector = self.model.encode(self.query_prefix + question, normalize_embeddings=True,
                                   convert_to_numpy=True)
        return vector.tolist()

    def count_tokens(self, texts: list[str]) -> list[int]:
        """Token count per text (incl. special tokens) to detect truncation at max_seq_length."""
        tokenizer = self.model.tokenizer
        return [len(tokenizer(t, add_special_tokens=True)["input_ids"]) for t in texts]

    def info(self) -> dict:
        import sentence_transformers
        import torch
        return {"provider": "sentence-transformers (local)", "model": self.model_name,
                "dimensions": self.dimensions, "max_seq_length": self.max_seq_length,
                "normalize_embeddings": True, "query_prefix": self.query_prefix,
                "document_prefix": "", "device": str(self.model.device),
                "sentence_transformers_version": sentence_transformers.__version__,
                "torch_version": torch.__version__}