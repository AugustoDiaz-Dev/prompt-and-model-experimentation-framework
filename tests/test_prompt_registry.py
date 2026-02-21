import pytest
from app.registry.prompt_registry import PromptRegistry
from unittest.mock import AsyncMock
from app.db.models import Prompt

@pytest.mark.asyncio
async def test_prompt_compare():
    session = AsyncMock()
    registry = PromptRegistry(session)

    p1 = Prompt(id="1", name="test", version=1, content="Hello World", author="test")
    p2 = Prompt(id="2", name="test", version=2, content="Hello Beautiful World", author="test")

    async def get_by_version(name, version):
        return p1 if version == 1 else p2

    registry.get_by_version = get_by_version

    result = await registry.compare("test", 1, 2)
    assert result["version_a"] == 1
    assert result["version_b"] == 2
    assert "diff_length" not in result  # Replaced by detailed fields
    assert result["similarity_ratio"] < 1.0
    assert result["lines_added"] >= 0
    assert result["char_delta"] == len(p2.content) - len(p1.content)
