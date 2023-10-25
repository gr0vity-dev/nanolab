from nanomock.modules.nl_parse_config import ConfigReadWrite
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SnippetManager:

    def __init__(self, snippet_folder: Path):
        self.conf_rw = ConfigReadWrite()
        self.snippet_folder = snippet_folder
        self.snippets = {}
        self._load_snippets()

    def _load_snippets(self):
        snippet_files = list(self.snippet_folder.glob("*.json"))

        for snippet_file in snippet_files:
            try:
                snippets = self.conf_rw.read_json(snippet_file)
                for snippet_key, snippet_value in snippets.items():
                    self.snippets[snippet_key] = snippet_value
            except Exception as exc:
                logger.info(f"Failed to load snippets from {snippet_file}")

    def get_snippets(self):
        return self.snippets

    def get_snippet_by_key(self, snippet_by_key):
        return self.snippets[snippet_by_key]
