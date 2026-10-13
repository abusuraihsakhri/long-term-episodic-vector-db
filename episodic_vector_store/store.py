"""Dependency-free, exact cosine-similarity storage for user-supplied embeddings.

This is a linear-scan vector store, NOT an HNSW index or embedding model.
Data stays on the configured local filesystem; no external service is called.
"""
from __future__ import annotations

import json
import math
import os
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path


class VectorStore:
    """Small persistent collection of episodes with fixed-dimensional vectors."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path is not None else None
        self._lock = threading.RLock()
        self._records: dict[str, dict] = {}
        self.dimension: int | None = None
        if self.path is not None and self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if data.get("version") != 1 or not isinstance(data.get("episodes"), list):
                raise ValueError("Unsupported or malformed vector-store file")
            for episode in data["episodes"]:
                if not isinstance(episode, dict):
                    raise ValueError("Malformed episode in vector-store file")
                self._put(
                    episode.get("id"),
                    episode.get("embedding"),
                    episode.get("text"),
                    episode.get("metadata"),
                    timestamp=episode.get("timestamp"),
                    persist=False,
                )
            if data.get("dimension") != self.dimension:
                raise ValueError("Stored vector dimension does not match the episodes")

    @staticmethod
    def _normalize(values):
        if not isinstance(values, (list, tuple)) or not 1 <= len(values) <= 4096:
            raise ValueError("Embedding must be a list of 1–4096 finite numbers")
        if any(isinstance(x, bool) or not isinstance(x, (int, float)) for x in values):
            raise ValueError("Embedding must contain only numbers")
        vector = [float(x) for x in values]
        if not all(math.isfinite(x) for x in vector):
            raise ValueError("Embedding must contain only finite numbers")
        # hypot avoids overflow/underflow on many otherwise valid input vectors.
        norm = math.hypot(*vector)
        if norm == 0 or not math.isfinite(norm):
            raise ValueError("Embedding must have a finite, nonzero magnitude")
        return [x / norm for x in vector]

    def _put(self, episode_id, embedding, text, metadata, *, timestamp=None, persist=True):
        if not isinstance(episode_id, str) or not episode_id.strip() or len(episode_id) > 128:
            raise ValueError("Episode ID must contain 1–128 non-whitespace characters")
        if not isinstance(text, str):
            raise ValueError("Episode text must be a string")
        if not isinstance(metadata, dict):
            raise ValueError("Metadata must be a JSON object")
        metadata = json.loads(json.dumps(metadata, allow_nan=False))
        vector = self._normalize(embedding)
        if self.dimension is not None and len(vector) != self.dimension:
            raise ValueError(f"Expected {self.dimension} dimensions, received {len(vector)}")
        if timestamp is not None and not isinstance(timestamp, str):
            raise ValueError("Invalid episode timestamp")
        with self._lock:
            if self.dimension is None:
                self.dimension = len(vector)
            self._records[episode_id] = {
                "id": episode_id, "text": text, "embedding": vector,
                "metadata": metadata,
                "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
            }
            if persist:
                self._save()
            return json.loads(json.dumps(self._records[episode_id]))

    def put(self, episode_id: str, embedding: list[float], text: str = "",
            metadata: dict | None = None) -> dict:
        """Insert or replace an episode by ID."""
        return self._put(episode_id, embedding, text, {} if metadata is None else metadata)

    def search(self, embedding: list[float], top_k: int = 5,
               min_similarity: float = -1.0) -> list[dict]:
        vector = self._normalize(embedding)
        if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= 100:
            raise ValueError("top_k must be an integer between 1 and 100")
        if not isinstance(min_similarity, (int, float)) or not math.isfinite(min_similarity) or not -1 <= min_similarity <= 1:
            raise ValueError("min_similarity must lie between -1 and 1")
        with self._lock:
            if self.dimension is not None and len(vector) != self.dimension:
                raise ValueError(f"Expected {self.dimension} dimensions, received {len(vector)}")
            matches = []
            for episode in self._records.values():
                score = max(-1.0, min(1.0, math.fsum(a * b for a, b in zip(vector, episode["embedding"]))))
                if score >= min_similarity:
                    matches.append({**episode, "similarity": score})
            matches.sort(key=lambda e: (-e["similarity"], e["id"]))
            return json.loads(json.dumps(matches[:top_k]))

    def list_episodes(self) -> list[dict]:
        with self._lock:
            return json.loads(json.dumps(sorted(self._records.values(), key=lambda e: e["id"])))

    def delete(self, episode_id: str) -> bool:
        with self._lock:
            if episode_id not in self._records:
                return False
            del self._records[episode_id]
            if not self._records:
                self.dimension = None
            self._save()
            return True

    def _save(self):
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", dir=self.path.parent,
                prefix=".episodes-", suffix=".tmp", delete=False,
            ) as handle:
                temp_path = handle.name
                os.chmod(temp_path, 0o600)
                json.dump({
                    "version": 1, "dimension": self.dimension,
                    "episodes": list(self._records.values()),
                }, handle, ensure_ascii=False, allow_nan=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, self.path)
        finally:
            if temp_path is not None and os.path.exists(temp_path):
                os.unlink(temp_path)
