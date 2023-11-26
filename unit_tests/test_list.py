import pytest
import nanolab.main as run
from io import StringIO
from unittest.mock import patch
import os
from nanolab.src.config_handler import ConfigPathHandler
import json


def run_with_args(args):
    with patch('sys.argv', args):
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            run.main()
    return captured_output.getvalue().strip()


@pytest.mark.parametrize(
    "args, expected_substring", [
        (['nanolab', 'list'],
         "https://api.github.com/repos/gr0vity-dev/nanolab-configs/contents/default"),
        (['nanolab', 'list', '--gh-user', 'nanocurrency', '--gh-repo', 'nano-node',
         '--gh-path', 'ci'], "https://api.github.com/repos/nanocurrency/nano-node/contents/ci"),
        (['nanolab', 'list', '--gh-path', '4prs?ref=wip/4pr_shared_testcases'],
         "https://api.github.com/repos/gr0vity-dev/nanolab-configs/contents/4prs?ref=wip/4pr_shared_testcases")
    ]
)
def test_nanoclub_args(args, expected_substring):
    output = run_with_args(args)
    assert expected_substring in output


def _test_nanolab_list_local_returns_all_testcases():
    original_cwd = os.getcwd()  # Save the current working directory
    os.chdir('unit_tests')  # Change the working directory to 'unit_tests'

    # Create a ConfigPathHandler instance to get the base path
    path_handler = ConfigPathHandler("placeholder")
    base_path = path_handler.get_resources_dir()

    # Create 5 JSON files in the testcases/ directory
    for i in range(1, 6):
        with open(f"{base_path}/testcase{i}_config.json", "w") as file:
            json.dump({"test": "data"}, file)

    try:
        # Execute with --local flag
        output = run_with_args(['nanolab', 'list', '--local'])

        # Explicitly check that each of the created files is present in the output
        for i in range(1, 6):
            assert f"{base_path}/testcase{i}" in output

    finally:
        # Remove the created JSON files to clean up
        for i in range(1, 6):
            os.remove(f"{base_path}/testcase{i}_config.json")

        os.chdir(original_cwd)  # Restore the original working directory
