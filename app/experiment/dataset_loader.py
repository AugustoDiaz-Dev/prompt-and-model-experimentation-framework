import json
import logging
from pathlib import Path
from typing import TypedDict, Optional, List

logger = logging.getLogger(__name__)

class TestCase(TypedDict):
    id: str
    input: str
    expected: str
    context: Optional[str]
    category: Optional[str]

class DatasetLoader:
    @staticmethod
    def load_json(dataset_path: str | Path) -> List[TestCase]:
        """Loads a JSON dataset and returns a list of test cases."""
        path = Path(dataset_path)
        if not path.exists():
            logger.error(f"Dataset not found: {path}")
            return []
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [TestCase(**item) for item in data]
        except Exception as e:
            logger.error(f"Failed to load dataset from {path}: {e}")
            return []
