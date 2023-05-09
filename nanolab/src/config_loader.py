import os
import shutil
import requests
from nanomock.modules.nl_parse_config import ConfigReadWrite
from .snippet_manager import SnippetManager
from nanolab.command.command_validator import CommandValidator


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

        return self.conf_rw.read_json(config_path)

    def _load_config(self, config_path: str) -> dict:
        return self._load_resolved_path(config_path, "CONFIG_FILE",
                                        'config.example.json')

    def apply_globals(self):
        testcase_name = self.config["testcase"]
        global_variables = self.config.get("global", {})

        # Replace global variables in the commands section
        for command in self.config["commands"]:
            self._apply_variables_to_command(global_variables, command)

    def _set_default_class(self, command):
        if command.get("type") in ["python"]:
            command.setdefault("class", self.default_command_executor)

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

    def _apply_variables_to_command(self, global_variables: dict,
                                    command: dict):
        if isinstance(command, dict):
            for key, value in command.items():
                if isinstance(value, str):
                    command[key] = self._replace_global_variables(
                        global_variables, value)
                else:
                    self._apply_variables_to_command(global_variables, value)
        elif isinstance(command, list):
            for item in command:
                self._apply_variables_to_command(global_variables, item)

    def _replace_global_variables(self, global_variables: dict,
                                  value: str) -> str:
        for global_key, global_value in global_variables.items():
            value = value.replace(f"{{{global_key}}}", global_value)
        return value