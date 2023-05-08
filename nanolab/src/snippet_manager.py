from nanomock.modules.nl_parse_config import ConfigReadWrite
from pathlib import Path


class SnippetManager:

    def __init__(self, snippet_folder: Path):
        self.conf_rw = ConfigReadWrite()
        self.snippet_folder = snippet_folder
        self.snippets = {}
        self._load_snippets()

    def _load_snippets(self):
        snippet_files = list(self.snippet_folder.glob("*.json"))

        for snippet_file in snippet_files:
            snippets = self.conf_rw.read_json(snippet_file)
            for snippet_key, snippet_value in snippets.items():
                self.snippets[snippet_key] = snippet_value

    def get_snippets(self):
        return self.snippets

    def get_snippet_by_key(self, snippet_by_key):
        return self.snippets[snippet_by_key]
