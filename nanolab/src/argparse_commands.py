# nanolab/command/argparse_commands.py

from os import environ, listdir
from .github import GitHubAPI
import argparse
from nanolab.src.config_handler import ConfigPathHandler, ConfigResourceHandler
from nanomock.modules.nl_parse_config import ConfigReadWrite
from nanolab.src.utils import extract_packaged_data_to_disk
from nanolab.src.config_loader import ConfigLoader, ConfigValidator, ConfigCommandExecutor
from nanolab.src.snippet_manager import SnippetManager


def parse_args():
    parser = argparse.ArgumentParser(
        description="Load configuration and snippets files")

    subparsers = parser.add_subparsers(dest="command")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run a testcase")
    run_parser.add_argument('-t', '--testcase', type=str, help='Testcase name')
    run_parser.add_argument('-i', '--image', nargs='+', help='Docker image(s)')
    run_parser.add_argument('--gh-user',
                            type=str,
                            default='gr0vity-dev',
                            help='GitHub user (default: gr0vity-dev)')
    run_parser.add_argument('--gh-repo', type=str, default='nanolab-configs',
                            help='GitHub repository (default: nanolab-configs)')
    run_parser.add_argument('--gh-path', type=str, default='default',
                            help='Path to testcases within the repository (default: default)')

    # List command
    list_parser = subparsers.add_parser("list", help="List testcases")
    list_parser.add_argument(
        '--gh-user', type=str, default='gr0vity-dev', help='GitHub user (default: gr0vity-dev)')
    list_parser.add_argument('--gh-repo', type=str, default='nanolab-configs',
                             help='GitHub repository (default: nanolab-configs)')
    list_parser.add_argument('--gh-path', type=str, default='default',
                             help='Path to testcases within the repository (default: default)')
    list_parser.add_argument('--local', action='store_true',
                             help="List testcases from local directory './testcases/'")

    return parser.parse_args()


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

        # copy config to disk
        config_path = resource_handler.copy_config_file(
            path_handler.config_copy_file_path)

        # resolve and downlaod resources defiend in the config
        resolved_config = resource_handler.download_and_replace_resources(
            config_path, path_handler.downloads_path)
        # replace docker_tags with commandline
        if self.args.image:
            resolved_config["docker_tags"] = self.args.image

        resolved_path = path_handler.get_resolved_config_path()
        snippet_path = path_handler.get_snippets_path()

        snippet_manager = SnippetManager(snippet_path)
        config_loader = ConfigLoader(snippet_manager)
        final_config = config_loader.load_config(resolved_config)
        self.conf_rw.write_json(resolved_path, final_config)
        ConfigValidator.validate_config(final_config)
        ConfigCommandExecutor.execute_commands(final_config)

    def list_testcases(self):
        if self.args.local:
            # Create a ConfigPathHandler instance
            # Placeholder since we don't need a specific testcase_alias for listing
            path_handler = ConfigPathHandler("placeholder")

            # Get the base path for test cases
            base_path = path_handler.get_resources_dir()

            # If --local flag is set, list test cases from the local directory
            for file in listdir(base_path):
                if file.endswith('_config.json') and file != 'resolved_config.json':
                    # Prepend the path and remove the '.json' extension before printing
                    print(f"{base_path}/{file}")
        else:
            # Otherwise, list test cases from the GitHub repository
            files = self.github_api.get_files()
            if files:
                for file in files:
                    if file["name"].endswith(".json"):
                        print(file["name"][:-5])

    def get_args(self):
        return self.args
