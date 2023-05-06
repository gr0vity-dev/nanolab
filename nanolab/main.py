#!./venv_py/bin/python

import json
import os
import subprocess
import threading
from collections import defaultdict
import inspect
import argparse
from nanolab import pycmd
import logging

default_class = "NodeInteraction"

logger = logging.getLogger(__name__)


def load_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Load configuration and snippets files")
    parser.add_argument('--config',
                        type=str,
                        help='Path to the configuration file')
    parser.add_argument('--snippets',
                        type=str,
                        help='Path to the snippets file')
    return parser.parse_args()


def load_resolved_path(arg_value, env_var, default_path):
    config_path = arg_value if arg_value else os.environ.get(
        env_var, default_path)
    logger.info("path is %s", config_path)
    return load_json(config_path)


#Use {default_class} if "class" is missing from python commands to reduce config complexity
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


def get_completed_variables(config):
    variables = config.get('variables', {})

    #add global variables
    variables["docker_tag"] = os.environ["docker_tag"]
    return variables


def get_method_parameters(method):
    signature = inspect.signature(method)
    return [param.name for param in signature.parameters.values()]


def get_filtered_variables(method, variables):
    method_parameters = get_method_parameters(method)
    return {
        key: value
        for key, value in variables.items() if key in method_parameters
    }


def execute_snippet(command_config, snippets):
    snippet = load_snippet_by_key(snippets, command_config["key"])

    validate_mandatory_vars(snippet, command_config)

    for snippet_command in snippet["commands"]:
        snippet_command["variables"] = get_completed_variables(command_config)
        execute_command(snippet_command, snippets)


def execute_python(command_config):
    class_name = command_config.get("class", default_class)
    cls = getattr(pycmd, class_name)
    instance = cls(**command_config.get('constructor_params', {}))

    method = getattr(instance, command_config['method'])
    variables = get_completed_variables(command_config)
    #filter variables that are not in the method signature (e.g. global variables like docker_tag)
    filtered_variables = get_filtered_variables(method, variables)

    method(**filtered_variables)


def get_formatted_command(command_config):
    variables = get_completed_variables(command_config)
    command = command_config['command']
    if variables: command = command.format(**variables)
    return command


def print_output(process):
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output.strip())


def print_errors(process, command):
    stderr = process.stderr.read()
    if process.returncode != 0:
        print(f"Error executing command: {command}\nError: {stderr.strip()}")


def execute_bash(command_config):
    command = get_formatted_command(command_config)

    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,  # Decode the output as text
        bufsize=1)  # Set bufsize to 1 for line buffering

    # Print the output in real-time
    print_output(process)
    print_errors(process, command)


def execute_command_sequence(commands):
    for command_config in commands:
        if command_config['type'] == 'python':
            execute_python(command_config)
        elif command_config['type'] == 'bash':
            execute_bash(command_config)
        else:
            raise ValueError(
                f"{command_config['type']} not supported for sequenced execution"
            )


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


def load_and_validate_configs(args):

    default_config_path = 'config.example.json'
    default_snippets_path = 'nanolab/snippets.json'

    config = load_resolved_path(args.config, "CONFIG_FILE",
                                default_config_path)
    snippets = load_resolved_path(args.snippets, "SNIPPET_FILE",
                                  default_snippets_path)

    complete_config(config, snippets)
    validate_config(config)

    return config, snippets


def execute_commands(config, snippets):

    #Easily allow for comparison between docker_tags
    for docker_tag in config["docker_tags"]:
        os.environ["docker_tag"] = docker_tag
        for command_config in config["commands"]:
            execute_command(command_config, snippets)


def main():
    args = parse_args()
    config, snippets = load_and_validate_configs(args)
    execute_commands(config, snippets)


if __name__ == "__main__":
    main()
