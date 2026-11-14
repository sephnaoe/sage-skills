"""Content-addressable cache for semantic analysis.

Cache keys are based on content hashes, not file paths.
This ensures cache invalidation when content changes.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class SemanticCache:
    """Content-addressable cache for AI-generated descriptions and labels."""

    def __init__(self, cache_dir: Path | None = None):
        self.cache_dir = cache_dir or Path(__file__).resolve().parents[3] / "var" / "state" / "semantic-cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _key_path(self, key: str) -> Path:
        # Use first 2 chars as subdirectory for filesystem efficiency
        return self.cache_dir / key[:2] / f"{key}.json"

    def get(self, key: str) -> dict[str, Any] | None:
        """Get cached value by key. Returns None if not found or expired."""
        path = self._key_path(key)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            # Check if cache entry has expired (optional TTL)
            if "expires_at" in data:
                import time
                if time.time() > data["expires_at"]:
                    path.unlink(missing_ok=True)
                    return None
            return data.get("value")
        except (json.JSONDecodeError, Exception):
            return None

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        """Set cached value by key."""
        path = self._key_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {"value": value}
        if ttl_seconds:
            import time
            data["expires_at"] = time.time() + ttl_seconds
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def invalidate(self, key: str) -> None:
        """Invalidate a cached value."""
        path = self._key_path(key)
        path.unlink(missing_ok=True)

    def clear(self) -> None:
        """Clear all cached values."""
        for f in self.cache_dir.rglob("*.json"):
            f.unlink(missing_ok=True)

    @staticmethod
    def make_key(content: str, prompt_version: str = "v1") -> str:
        """Create a content-addressable cache key."""
        combined = f"{prompt_version}:{content}"
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()