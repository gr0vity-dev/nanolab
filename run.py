import json
import os
import subprocess
import threading
from collections import defaultdict
from app import pycmd
import time

default_class = "NodeCommands"


def load_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)


#Use {default_class} is class is misisng from config to reduce config complexity
def set_default_class(command):
    if command.get("type") in ["python"]:
        command.setdefault("class", default_class)


def complete_config(config, snippets):
    for command in config["commands"]:
        set_default_class(command)

        if command.get("type") == "threaded":
            for python_command in command["commands"]:
                set_default_class(python_command)

        if command.get("type") == "snippet":
            snippet = load_snippet_by_key(snippets, command["key"])
            for python_command in snippet["commands"]:
                set_default_class(python_command)


def validate_config(config):

    if "commands" not in config:
        raise ValueError("The 'commands' key is missing in the config file.")

    for idx, command in enumerate(config["commands"]):
        command_type = command.get("type")
        if command_type not in ["bash", "snippet", "python", "threaded"]:
            raise ValueError(
                f"Invalid command type '{command_type}' at index {idx} in 'commands'"
            )
        if command_type == "python":
            validate_python_command(idx, command)
        elif command_type == "threaded":
            validate_threaded_command(idx, command)
        elif command_type == "snippet":
            if "key" not in command:
                raise ValueError(
                    f"Missing 'key' for snippet command at index {idx} in 'commands'"
                )


def validate_mandatory_vars(snippet, command_config):
    missing_vars = set(snippet.get("mandatory_vars", set())) - set(
        command_config.get("variables", {}).keys())
    if missing_vars:
        raise KeyError(
            f"Missing value(s) for mandatory variable(s): {', '.join(missing_vars)}"
        )


def validate_python_command(idx, command):
    if "method" not in command:
        raise ValueError(f"Python command {idx}: 'method' is required.")

    method_name = command["method"]

    if "class" in command:
        cls = getattr(pycmd, command["class"])
        if not cls:
            raise ValueError(
                f"Python command {idx}: Class '{command['class']}' not found.")
        if not hasattr(cls, method_name):
            raise ValueError(
                f"Python command {idx}: Method '{method_name}' not found in class '{command['class']}'."
            )
    else:
        if method_name not in globals():
            raise ValueError(
                f"Python command {idx}: Method '{method_name}' not found in the current module."
            )


def validate_threaded_command(idx, commands):

    for i, python_command in enumerate(commands["commands"]):
        validate_python_command(f"{idx}-method-{i}", python_command)


def load_snippet_by_key(snippets, snippet_by_key):
    return snippets[snippet_by_key]


def execute_snippet(command_config, snippets):
    snippet = load_snippet_by_key(snippets, command_config["key"])

    validate_mandatory_vars(snippet, command_config)

    for snippet_command in snippet["commands"]:
        snippet_command["variables"] = command_config.get("variables")
        execute_command(snippet_command, snippets)


def execute_python(command_config):
    class_name = command_config.get("class", "NodeCommands")
    cls = getattr(pycmd, class_name)
    instance = cls(**command_config.get('constructor_params', {}))

    method = getattr(instance, command_config['method'])
    variables = command_config.get('variables', {})

    method(**variables)


def execute_bash(command_config):
    variables = command_config.get("variables")
    command = command_config['command']
    if variables: command = command.format(**variables)
    process = subprocess.Popen(command,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        print(
            f"Error executing command: {command}\nError: {stderr.decode('utf-8')}"
        )
    else:
        print(stdout.decode('utf-8'))


def execute_command_sequence(commands):
    for command_config in commands:
        if command_config['type'] == 'python':
            execute_python(command_config)


def execute_threaded(commands):
    threads = []
    command_groups = defaultdict(list)

    for command_config in commands:
        group = command_config.get("group")
        if group:
            command_groups[group].append(command_config)
        else:
            thread = threading.Thread(target=execute_python,
                                      args=(command_config, ))
            threads.append(thread)

    for group_commands in command_groups.values():
        thread = threading.Thread(target=execute_command_sequence,
                                  args=(group_commands, ))
        threads.append(thread)

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()


def execute_command(command_config, snippets):

    if command_config.get('skip', False):
        return

    if command_config['type'] == 'bash':
        execute_bash(command_config)
    elif command_config['type'] == 'snippet':
        execute_snippet(command_config, snippets)
    elif command_config['type'] == 'python':
        execute_python(command_config)
    elif command_config['type'] == 'threaded':
        execute_threaded(command_config['commands'])


def main():
    config_file_path = 'config.json'
    snippets_file_path = 'snippets.json'

    config_data = load_json(os.environ.get("CONFIG_FILE", config_file_path))
    snippets_data = load_json(
        os.environ.get("SNIPPET_FILE", snippets_file_path))

    complete_config(config_data, snippets_data)
    validate_config(config_data)

    for docker_tag in config_data["docker_tags"]:
        os.environ["docker_tag"] = docker_tag
        for command_config in config_data["commands"]:
            execute_command(command_config, snippets_data)


if __name__ == "__main__":
    main()
