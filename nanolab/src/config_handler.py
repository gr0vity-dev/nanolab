import shutil
from pathlib import Path
from os import environ
from nanomock.modules.nl_parse_config import ConfigReadWrite
from nanolab.src.utils import download_data
from nanolab.src.github import GitHubAPI


class ConfigPathHandler:

    def __init__(self, testcase_alias: str):
        self.conf_rw = ConfigReadWrite()

        self.is_local_path = False
        self.local_config_path = None
        self.base_path = Path(environ.get("NL_PATH") or str(Path.cwd()))
        self.testcase_name = self._set_testcase_name(testcase_alias.strip())
        self.resources_dir = environ.get("NL_RES_DIR", "testcases")
        self.resources_path = self.base_path / self.resources_dir
        self.downloads_path = self.base_path / self.resources_dir / "dowlnoads"
        self.config_copy_file_path = self.resources_path / \
            f"{self.testcase_name}_config.json"
        self.resolved_config_file_path = self.resources_path / "resolved_config.json"
        self.snippets_path = self.base_path / "snippets"

        self.resources_path.mkdir(parents=True, exist_ok=True)
        self.downloads_path.mkdir(parents=True, exist_ok=True)

    def _set_testcase_name(self, testcase_alias):
        # for ease of use we allow alias to be either local path to disk, or downloadable alias
        if testcase_alias.endswith(".json"):
            self.local_config_path = testcase_alias
            config = self.conf_rw.read_json(testcase_alias)
            testcase_name = config.get("testcase", "unknown_testcase")
            self.is_local_path = True
        else:
            testcase_name = testcase_alias

        environ["LAB_TESTCASE"] = testcase_name
        return testcase_name

    def get_testcase_name(self):
        return self.testcase_name

    def get_resources_dir(self):
        return self.resources_dir

    def get_resources_path(self):
        return self.resources_path

    def get_snippets_path(self):
        return self.snippets_path

    def get_resolved_config_path(self):
        return self.resolved_config_file_path

    def _copy_path(self, path: str) -> str:
        filename = Path(path).name
        destination = self.resources_path / filename

        copy_files = environ.get("NL_COPY_FILES", "True")
        if copy_files.lower() == "true" and not destination.exists():
            shutil.copy(path, destination)
        return destination


class ConfigResourceHandler():

    def __init__(self, github_api: GitHubAPI,
                 config_path_handler: ConfigPathHandler):

        self.conf_rw = ConfigReadWrite()
        self.config_path = config_path_handler.get_resources_path()
        self.testcase_name = config_path_handler.testcase_name
        self.github_api = github_api
        self.is_local_path = config_path_handler.is_local_path
        self.local_config_path = config_path_handler.local_config_path

    def download_and_replace_resources(self, config_path: Path,
                                       destination_path: Path):

        config = self.conf_rw.read_json(config_path)
        global_resources = config.get("global", {})

        for key, value in global_resources.items():
            if value.startswith("http://") or value.startswith("https://"):
                # Download the remote file
                downloaded_path = self._download_url(value, destination_path)
                # Replace the URL with the downloaded file path
                global_resources[key] = str(downloaded_path)
            elif environ.get("NL_COPY_FILES") and environ.get(
                    "NL_COPY_FILES").lower() == "true":
                # Copy the local file to the destination
                copied_path = self._copy_path(
                    value, destination_path / Path(value).name)
                # Replace the local path with the copied file path
                global_resources[key] = str(copied_path)

        return config

    def copy_config_file(self, destination: Path):
        if self.is_local_path:
            return self._copy_path(self.local_config_path,
                                   destination,
                                   force_copy=True)
        else:
            return self._download_config_file(destination)

    def _copy_path(self,
                   source_path: str,
                   destination: Path,
                   force_copy=None) -> str:
        source = Path(source_path)

        copy_files = force_copy or environ.get("NL_COPY_FILES", "False")
        if str(copy_files).lower() == "true" or not destination.exists():
            shutil.copy(source, destination)
        return destination

    def _download_url(self, url: str, resource_path: Path) -> Path:
        return download_data(url.strip(), Path(url).name, resource_path)

    def _download_config_file(self, destination: Path) -> Path:
        config_data = self.github_api.get_file_content(
            f"{self.testcase_name}.json")
        return download_data(config_data, destination.name, destination.parent)
