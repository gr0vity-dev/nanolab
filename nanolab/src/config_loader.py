import os
from nanomock.modules.nl_parse_config import ConfigReadWrite
from .snippet_manager import SnippetManager
from nanolab.command.command import Command
from copy import deepcopy


class ConfigLoader:

    def __init__(self, snippet_manager: SnippetManager):
        self.snippet_manager = snippet_manager
        self.conf_rw = ConfigReadWrite()
        self.default_command_executor = "NodeInteraction"

    def read_config(self, config_path: str):
        self.conf_rw.read_json(config_path)

    def load_config(self, config: dict):
        config = self._resolve_snippets(config, [])
        config = self._apply_globals(config)
        config = self._complete_config(config)

        return config

    def _apply_globals(self, config):
        global_variables = config.get("global", {})

        for command in config["commands"]:
            self._apply_variables_to_command(global_variables, command)

        return config

    def _set_default_class(self, command):
        if command.get("type") in ["python"]:
            command.setdefault("class", self.default_command_executor)

    def _complete_config(self, config):
        for command in config["commands"]:
            self._set_default_class(command)

            if command.get("type") == "threaded":
                for python_command in command["commands"]:
                    self._set_default_class(python_command)

        return config

    def _resolve_snippets(self, config, breadcrumb=[]):
        config["commands"] = self._resolve_commands(config["commands"],
                                                    breadcrumb)
        return config

    def _resolve_commands(self, commands, breadcrumb):
        resolved_commands = []
        for command in commands:
            if command.get("type") == "snippet":
                resolved_commands.extend(
                    self._resolve_snippet_command(command, breadcrumb))
            else:
                resolved_commands.append(command)
        return resolved_commands

    def _resolve_snippet_command(self, command, breadcrumb):
        key = command["key"]
        if key in breadcrumb:
            raise ValueError(f"Circular snippet reference detected: {key}")

        snippet = deepcopy(self.snippet_manager.get_snippet_by_key(key))
        variables = command.get("variables", {})
        self._check_mandatory_vars(snippet, variables, key)
        resolved_snippet = self._resolve_snippets(snippet, breadcrumb + [key])
        return self._replace_vars_in_commands(resolved_snippet["commands"],
                                              variables)

    def _check_mandatory_vars(self, snippet, variables, key):
        mandatory_vars = snippet.get("mandatory_vars", [])
        for var in mandatory_vars:
            if var not in variables:
                raise KeyError(
                    f"Mandatory variable '{var}' is missing in '{key}'. Variables defined: {list(variables.keys())}"
                )

    def _replace_vars_in_commands(self, commands, variables):
        for command in commands:
            self._replace_vars_in_dict(command, variables)
        return commands

    def _replace_vars_in_dict(self, item, variables):
        if isinstance(item, dict):
            for key, value in item.items():
                if isinstance(value, (dict, list)):
                    self._replace_vars_in_dict(value, variables)
                else:
                    item[key] = self._replace_vars_in_item(value, variables)
        elif isinstance(item, list):
            for i in range(len(item)):
                if isinstance(item[i], (dict, list)):
                    self._replace_vars_in_dict(item[i], variables)
                else:
                    item[i] = self._replace_vars_in_item(item[i], variables)

    def _replace_vars_in_item(self, item, variables):
        if isinstance(item, str):
            for var, var_value in variables.items():
                placeholder = f'{{{var}}}'
                if item == placeholder:  # if the item is exactly equal to the placeholder
                    return var_value  # return the original variable value
                if placeholder in item:  # if the placeholder is part of the string
                    item = item.replace(
                        placeholder, str(var_value)
                    )  # replace it with string representation of variable
        return item

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


class ConfigValidator:

    @staticmethod
    def validate_config(config):
        if "commands" not in config:
            raise ValueError(
                "The 'commands' key is missing in the config file.")

        for idx, command in enumerate(config["commands"]):
            command_type = command.get("type")
            if command_type not in ["bash", "snippet", "python", "threaded"]:
                raise ValueError(
                    f"Invalid command type '{command_type}' at index {idx} in 'commands'"
                )


class ConfigCommandExecutor:

    @staticmethod
    def execute_commands(config):
        for docker_tag in config["docker_tags"]:
            os.environ["docker_tag"] = docker_tag
            for command_config in config["commands"]:
                ConfigCommandExecutor.execute_command(command_config)

    @staticmethod
    def execute_command(command_config):
        command = Command(command_config)
        command.validate()
        command.execute()
