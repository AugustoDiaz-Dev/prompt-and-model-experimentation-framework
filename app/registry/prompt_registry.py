from __future__ import annotations

import difflib
import logging
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Prompt

logger = logging.getLogger(__name__)


class PromptRegistry:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def register(
        self,
        *,
        name: str,
        content: str,
        author: str,
        tags: dict | None = None,
    ) -> uuid.UUID:
        # Get latest version for this prompt name
        stmt = select(Prompt).where(Prompt.name == name).order_by(Prompt.version.desc()).limit(1)
        result = await self._session.execute(stmt)
        latest = result.scalar_one_or_none()

        next_version = 1 if latest is None else latest.version + 1

        prompt = Prompt(
            name=name,
            version=next_version,
            content=content,
            author=author,
            tags=tags or {},
        )
        self._session.add(prompt)
        await self._session.flush()

        logger.info(
            "prompt_registered",
            extra={"prompt_id": str(prompt.id), "prompt_name": name, "version": next_version},
        )
        return prompt.id

    async def get_latest(self, name: str) -> Prompt | None:
        stmt = select(Prompt).where(Prompt.name == name).order_by(Prompt.version.desc()).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_version(self, name: str, version: int) -> Prompt | None:
        stmt = select(Prompt).where(Prompt.name == name, Prompt.version == version)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Prompt]:
        stmt = select(Prompt).order_by(Prompt.name, Prompt.version.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def compare(self, name: str, version_a: int, version_b: int) -> dict:
        """Enhanced prompt comparison with diff, token counts, and similarity score."""
        prompt_a = await self.get_by_version(name, version_a)
        prompt_b = await self.get_by_version(name, version_b)

        if not prompt_a or not prompt_b:
            raise ValueError("One or both prompt versions not found")

        content_a = prompt_a.content
        content_b = prompt_b.content

        # Character-level unified diff
        diff_lines = list(
            difflib.unified_diff(
                content_a.splitlines(keepends=True),
                content_b.splitlines(keepends=True),
                fromfile=f"v{version_a}",
                tofile=f"v{version_b}",
                lineterm="",
            )
        )
        unified_diff = "".join(diff_lines)

        # Similarity ratio (0.0 – 1.0)
        similarity = difflib.SequenceMatcher(None, content_a, content_b).ratio()

        # Simple token counts (whitespace split)
        tokens_a = len(content_a.split())
        tokens_b = len(content_b.split())

        # Line counts
        lines_a = len(content_a.splitlines())
        lines_b = len(content_b.splitlines())

        # Added / removed / changed lines
        added = sum(1 for l in diff_lines if l.startswith("+") and not l.startswith("+++"))
        removed = sum(1 for l in diff_lines if l.startswith("-") and not l.startswith("---"))

        return {
            "name": name,
            "version_a": version_a,
            "version_b": version_b,
            "content_a": content_a,
            "content_b": content_b,
            # Enhanced fields
            "similarity_ratio": round(similarity, 4),
            "unified_diff": unified_diff,
            "lines_added": added,
            "lines_removed": removed,
            "tokens_a": tokens_a,
            "tokens_b": tokens_b,
            "token_delta": tokens_b - tokens_a,
            "lines_a": lines_a,
            "lines_b": lines_b,
            "line_delta": lines_b - lines_a,
            "char_delta": len(content_b) - len(content_a),
            "tags_a": prompt_a.tags,
            "tags_b": prompt_b.tags,
        }

