"""Versioned JSON storage for backtest-derived model statistics."""

from __future__ import annotations

import json
from pathlib import Path

from .models import BacktestArtifact


class BacktestArtifactRepository:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = (
            Path(path)
            if path
            else Path(__file__).resolve().parent / "signal_statistics.json"
        )

    def load(self) -> BacktestArtifact:
        if not self.path.exists():
            return BacktestArtifact()
        with self.path.open("r", encoding="utf-8") as handle:
            return BacktestArtifact.from_dict(json.load(handle))

    def save(self, artifact: BacktestArtifact) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(artifact.to_dict(), handle, ensure_ascii=False, indent=2)


__all__ = ["BacktestArtifactRepository"]
