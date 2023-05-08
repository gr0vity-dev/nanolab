#!./venv_py/bin/python

import os
import argparse
import logging
from nanolab.src.config_loader import TestcaseConfig
from nanolab.src.snippet_manager import SnippetManager
from nanolab.command.command import Command
from pathlib import Path
from nanolab.src.utils import extract_packaged_data_to_disk

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Load configuration and snippets files")
    parser.add_argument('--config',
                        type=str,
                        help='Path to the configuration file')
    return parser.parse_args()


def execute_command(command_config, snippet_manager: SnippetManager):
    if command_config.get('skip', False):
        return

    command = Command(command_config, snippet_manager)
    command.validate()
    command.execute()


def load_and_validate_configs(args):

    sinppet_manager = SnippetManager(Path.cwd() / "nanolab" / "snippets")
    config_loader = TestcaseConfig(sinppet_manager, config_path=args.config)

    config_loader.apply_globals()
    config_loader.complete_config()
    config_loader.validate_config()

    return config_loader


def execute_commands(config_loader: TestcaseConfig):

    for docker_tag in config_loader.config["docker_tags"]:
        os.environ["docker_tag"] = docker_tag
        for command_config in config_loader.config["commands"]:
            execute_command(command_config, config_loader.snippet_manager)


def main(args=None):
    args = args or parse_args()
    config_loader = load_and_validate_configs(args)
    execute_commands(config_loader)


if __name__ == "__main__":
    extract_packaged_data_to_disk()
    main()
