import json
import os
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class StateManager:
    """Manages persistence of processed article URLs/IDs to avoid duplicates."""

    def __init__(self, state_file_path: str = "processed_articles.json"):
        self.state_file_path = state_file_path
        self.data: Dict[str, Any] = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        """Loads state data from JSON file."""
        if not os.path.exists(self.state_file_path):
            logger.info(f"State file {self.state_file_path} not found. Creating new state.")
            return {"processed": {}}
        try:
            with open(self.state_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "processed" not in data:
                    data["processed"] = {}
                return data
        except Exception as e:
            logger.error(f"Error loading state file {self.state_file_path}: {e}. Initializing fresh state.")
            return {"processed": {}}

    def _save_state(self) -> None:
        """Saves current state data to JSON file."""
        try:
            with open(self.state_file_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save state file {self.state_file_path}: {e}")

    def is_processed(self, article_id: str) -> bool:
        """Checks if an article ID or URL has already been processed."""
        return article_id in self.data.get("processed", {})

    def mark_processed(self, article_id: str, title: str = "", blog_post_id: str = "") -> None:
        """Marks an article ID as processed with timestamp metadata."""
        if "processed" not in self.data:
            self.data["processed"] = {}
        self.data["processed"][article_id] = {
            "title": title,
            "processed_at": datetime.utcnow().isoformat(),
            "blog_post_id": blog_post_id
        }
        self._save_state()
        logger.info(f"Marked article '{article_id}' as processed.")
