import os
import shutil
import requests
from nanomock.modules.nl_parse_config import ConfigReadWrite
from .snippet_manager import SnippetManager
from nanolab.command.command_validator import CommandValidator
from nanolab.src.utils import wait_for_file


class TestcaseConfig:

    def __init__(self,
                 snippet_manager: SnippetManager,
                 config_path: str = None):
        self.default_command_executor = "NodeInteraction"
        self.conf_rw = ConfigReadWrite()
        self.config = self._load_config(config_path)
        self.snippet_manager = snippet_manager

    def _load_resolved_path(self, config_path, env_var, default_path) -> dict:
        config_path = config_path if config_path else os.environ.get(
            env_var, default_path)

        # Wait for the file to be written completely.
        wait_for_file(config_path, timeout=1)

        return self.conf_rw.read_json(config_path)

    def _load_config(self, config_path: str) -> dict:
        return self._load_resolved_path(config_path, "CONFIG_FILE",
                                        'config.example.json')

    def apply_globals(self):
        testcase_name = self.config["testcase"]
        global_variables = self.config.get("global", {})

        # Handle downloading or copying global files
        for key, value in global_variables.items():
            global_variables[key] = self._handle_path_or_url(
                testcase_name, value)

        # Replace global variables in the commands section
        for command in self.config["commands"]:
            self._apply_variables_to_command(global_variables, command)

    def _set_default_class(self, command):
        if command.get("type") in ["python"]:
            command.setdefault("class", self.default_command_executor)

    def _handle_path_or_url(self, testcase_name: str, value: str) -> str:
        if value.startswith("http://") or value.startswith("https://"):
            destination = self._download_url(testcase_name, value)
        else:
            destination = self._copy_path(testcase_name, value)
        return destination

    def complete_config(self):
        for command in self.config["commands"]:
            self._set_default_class(command)

            if command.get("type") == "threaded":
                for python_command in command["commands"]:
                    self._set_default_class(python_command)

            if command.get("type") == "snippet":
                snippet = self.snippet_manager.get_snippet_by_key(
                    command["key"])
                for python_command in snippet["commands"]:
                    self._set_default_class(python_command)

    # Add your existing _set_default_class and _load_snippet_by_key methods here

    def validate_config(self):
        if "commands" not in self.config:
            raise ValueError(
                "The 'commands' key is missing in the config file.")

        for idx, command in enumerate(self.config["commands"]):
            command_type = command.get("type")
            if command_type not in ["bash", "snippet", "python", "threaded"]:
                raise ValueError(
                    f"Invalid command type '{command_type}' at index {idx} in 'commands'"
                )
            if command_type in ("python", "threaded"):
                CommandValidator.validate_command(
                    command, self.snippet_manager.get_snippets())
            elif command_type == "snippet":
                if "key" not in command:
                    raise ValueError(
                        f"Missing 'key' for snippet command at index {idx} in 'commands'"
                    )

    def _download_url(self, testcase_name: str, url: str) -> str:
        url = url.strip()
        filename = os.path.basename(url)
        destination = f"./resources/{testcase_name}/{filename}"
        print("DEBUG", destination, url)
        os.makedirs(os.path.dirname(destination), exist_ok=True)

        if not os.path.exists(destination):
            response = requests.get(url)
            with open(destination, "wb") as f:
                f.write(response.content)

        return destination

    def _copy_path(self, testcase_name: str, path: str) -> str:
        filename = os.path.basename(path)
        destination = f"./resources/{testcase_name}/{filename}"
        os.makedirs(os.path.dirname(destination), exist_ok=True)

        if not os.path.exists(destination):
            shutil.copy(path, destination)
        return destination

    def _apply_variables_to_command(self, global_variables: dict,
                                    command: dict):
        for key, value in command.get("variables", {}).items():
            if isinstance(value, str):
                command["variables"][key] = self._replace_global_variables(
                    global_variables, value)
            elif isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, str):
                        value[sub_key] = self._replace_global_variables(
                            global_variables, sub_value)

    def _replace_global_variables(self, global_variables: dict,
                                  value: str) -> str:
        for global_key, global_value in global_variables.items():
            value = value.replace(f"{{{global_key}}}", global_value)
        return value