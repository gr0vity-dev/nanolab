# nanolab/command/argparse_commands.py

from os import environ
from .github import GitHubAPI
import argparse
from nanolab.src.config_handler import ConfigPathHandler, ConfigResourceHandler
from nanomock.modules.nl_parse_config import ConfigReadWrite
from nanolab.src.utils import extract_packaged_data_to_disk
from nanolab.src.config_loader import TestcaseConfig
from nanolab.src.snippet_manager import SnippetManager
from nanolab.command.command import Command


def parse_args():
    parser = argparse.ArgumentParser(
        description="Load configuration and snippets files")

    subparsers = parser.add_subparsers(dest="command")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run a testcase")
    run_parser.add_argument('-t', '--testcase', type=str, help='Testcase name')
    run_parser.add_argument('-i', '--image', type=str, help='Docker image')
    run_parser.add_argument('--gh-user',
                            type=str,
                            default='gr0vity-dev',
                            help='GitHub user (default: gr0vity-dev)')
    run_parser.add_argument(
        '--gh-repo',
        type=str,
        default='nanolab-configs',
        help='GitHub repository (default: nanolab-configs)')
    run_parser.add_argument(
        '--gh-path',
        type=str,
        default='default',
        help='Path to testcases within the repository (default: default)')

    # List command
    list_parser = subparsers.add_parser("list", help="List testcases")
    list_parser.add_argument('--gh-user',
                             type=str,
                             default='gr0vity-dev',
                             help='GitHub user (default: gr0vity-dev)')
    list_parser.add_argument(
        '--gh-repo',
        type=str,
        default='nanolab-configs',
        help='GitHub repository (default: nanolab-configs)')
    list_parser.add_argument(
        '--gh-path',
        type=str,
        default='default',
        help='Path to testcases within the repository (default: default)')

    return parser.parse_args()


def _load_and_validate_configs(snippet_path, config_path):

    sinppet_manager = SnippetManager(snippet_path)
    config_loader = TestcaseConfig(sinppet_manager, config_path=config_path)

    config_loader.apply_globals()
    config_loader.complete_config()
    config_loader.validate_config()

    return config_loader


def _execute_command(command_config, snippet_manager: SnippetManager):
    if command_config.get('skip', False):
        return

    command = Command(command_config, snippet_manager)
    command.validate()
    command.execute()


def _execute_commands(config_loader: TestcaseConfig):

    for docker_tag in config_loader.config["docker_tags"]:
        environ["docker_tag"] = docker_tag
        for command_config in config_loader.config["commands"]:
            _execute_command(command_config, config_loader.snippet_manager)


class ArgParseHandler:

    def __init__(self, args=None):
        self.args = args or parse_args()
        self.conf_rw = ConfigReadWrite()
        self.github_api = GitHubAPI(self.args.gh_user, self.args.gh_repo,
                                    self.args.gh_path)

    def run(self):
        path_handler = ConfigPathHandler(self.args.testcase)
        resource_handler = ConfigResourceHandler(self.github_api, path_handler)

        #
        extract_packaged_data_to_disk(path_handler.get_snippets_path())

        #copy config to disk
        config_path = resource_handler.copy_config_file(
            path_handler.config_copy_file_path)

        #resolve and downlaod resources defiend in the config
        resolved_config = resource_handler.download_and_replace_resources(
            config_path, path_handler.downloads_path)

        self.conf_rw.write_json(path_handler.resolved_config_file_path,
                                resolved_config)

        config_loader = _load_and_validate_configs(
            path_handler.get_snippets_path(),
            path_handler.get_resolved_config_path())
        _execute_commands(config_loader)

    def list_testcases(self):
        files = self.github_api.get_files()

        if files:
            for file in files:
                if file["name"].endswith(".json"):
                    print(file["name"][:-5])

    def get_args(self):
        return self.args
