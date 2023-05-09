import unittest
import time
import os
from unittest.mock import patch
import nanolab.main as run
from unit_tests.utils import match_expected_error, match_expected_output, contains_expected_substring, remove_nanolab_resources

from pathlib import Path
import pytest

os.environ["NL_PATH"] = "unit_tests"


@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown():
    # Setup code
    remove_nanolab_resources()
    print("Setup for all tests in the module")
    yield

    # Teardown code
    remove_nanolab_resources()
    print("Teardown for all tests in the module")


class TestRun(unittest.TestCase):

    @patch('sys.argv', [
        'nanolab', 'run', '--testcase',
        'unit_tests/test_configs/invalid_type.json'
    ])
    def test_invalid_type(self):
        expected_message = "Invalid command type 'invalid' at index 0 in 'commands'"
        match_expected_error(ValueError, expected_message)

    @patch('sys.argv', [
        'nanolab', 'run', '--testcase',
        'unit_tests/test_configs/invalid_snippet_key.json'
    ])
    def test_invalid_snippet_key(self):
        expected_message = "'non_existent_snippet'"
        match_expected_error(KeyError, expected_message)

    @patch('sys.argv', [
        'nanolab', 'run', '--testcase',
        'unit_tests/test_configs/invalid_method.json'
    ])
    def test_invalid_method(self):
        expected_message = "Python command: Method 'non_existent_method' not found in class 'NodeInteraction'."
        match_expected_error(ValueError, expected_message)

    @patch('sys.argv', [
        'nanolab', 'run', '--testcase',
        'unit_tests/test_configs/invalid_snippet_missing_mandatory_var.json'
    ])
    def test_invalid_snippet_missing_mandatory_var(self):
        expected_message = "'Missing value(s) for mandatory variable(s): unused_mandatory_var'"
        match_expected_error(KeyError, expected_message)

    @patch('sys.argv', [
        'nanolab', 'run', '--testcase',
        'unit_tests/test_configs/threaded_parallel.json'
    ])
    def test_threaded_parallel(self):
        start_time = time.time()
        run.main()
        duration = time.time() - start_time
        self.assertTrue(duration > 1, f"too short: {duration:.2f} s")
        self.assertTrue(duration < 1.35, f"too long: {duration:.2f} s")

    @patch('sys.argv', [
        'nanolab', 'run', '--testcase',
        'unit_tests/test_configs/threaded_with_group.json'
    ])
    def test_threaded_with_group(self):
        start_time = time.time()
        run.main()
        duration = time.time() - start_time
        self.assertTrue(duration > 2, f"too short: {duration:.2f} s")
        self.assertTrue(duration < 2.35, f"too long: {duration:.2f} s")

    @patch('sys.argv', [
        'nanolab', 'run', '--testcase',
        'unit_tests/test_configs/valid_snippets_and_bash.json'
    ])
    def test_valid_snippets_and_bash(self):
        expected_output = "Hello, World!\nfile test.txt"
        match_expected_output(expected_output)

    @patch('sys.argv', [
        'nanolab', 'run', '--testcase',
        'unit_tests/test_configs/snippet_without_vars.json'
    ])
    def test_snippet_without_vars(self):
        expected_output = "No vars needed!"
        match_expected_output(expected_output)

    @patch('sys.argv', [
        'nanolab', 'run', '--testcase',
        'unit_tests/test_configs/snippet_in_snippet.json'
    ])
    def test_snippet_in_snippet(self):
        expected_output = "file test.txt"
        match_expected_output(expected_output)

    @patch('sys.argv', [
        'nanolab', 'run', '--testcase',
        'unit_tests/test_configs/snippet_with_unused_vars.json'
    ])
    def test_snippet_with_unused_vars(self):
        expected_output = "file test.txt"
        match_expected_output(expected_output)

    @patch('sys.argv', [
        'nanolab', 'run', '--testcase',
        'unit_tests/test_configs/docker_tags.json'
    ])
    def test_docker_tags(self):
        expected_output = "tag1\nnanocurrency/nano:V24.0"
        match_expected_output(expected_output)

    @patch('sys.argv', [
        'nanolab', 'run', '--testcase',
        'unit_tests/test_configs/nanomock_create_down.json'
    ])
    def test_nanolocal_create(self):
        os.environ["NL_CONF_DIR"] = "unit_tests/nanomock"
        os.environ["NL_CONF_FILE"] = "nl_config.toml"
        expected_output = "SUCCESS: 2 containers have been removed"
        contains_expected_substring(expected_output)


if __name__ == '__main__':
    unittest.main()
