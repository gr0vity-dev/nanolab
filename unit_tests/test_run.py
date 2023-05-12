import unittest
import os
import shutil
import nanolab.main as run
import pytest
import time

from io import StringIO
from unittest.mock import patch

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


tc = unittest.TestCase()


def match_expected_error(error_type, expected_message):
    with tc.assertRaises(error_type) as cm:
        run.main()

    tc.assertEqual(str(cm.exception), expected_message)


def match_expected_output(expected_output):
    captured_output = StringIO()
    # Replace sys.stdout with captured_output within the context
    with patch('sys.stdout', captured_output):
        run.main()

    # Get the captured output as a string
    # output = captured_output.getvalue().replace("\r", "").replace("\n", "")
    output = captured_output.getvalue().strip()

    tc.assertEqual(output, expected_output)


def contains_expected_substring(expected_substring):
    captured_output = StringIO()
    with patch('sys.stdout', captured_output):
        run.main()
    # Get the captured output as a string
    output = captured_output.getvalue().replace("\r", "").replace("\n", "")

    tc.assertIn(expected_substring, output)


def remove_nanolab_resources():
    if os.path.exists("./unit_tests/snippets"):
        shutil.rmtree("./unit_tests/snippets")
    if os.path.exists("./unit_tests/resources"):
        shutil.rmtree("./unit_tests/resources")


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
        expected_message = "\"Mandatory variable 'unused_mandatory_var' is missing in 'test_snippet_unused_mandatory_var'. Variables defined: ['file_name']\""
        match_expected_error(KeyError, expected_message)

    @patch('sys.argv', [
        'nanolab', 'run', '--testcase',
        'unit_tests/test_configs/threaded_parallel.json'
    ])
    def test_threaded_parallel(self):
        start_time = time.time()
        run.main()
        duration = time.time() - start_time
        self.assertTrue(duration > 0.48, f"too short: {duration:.2f} s")
        self.assertTrue(duration < 0.52, f"too long: {duration:.2f} s")

    @patch('sys.argv', [
        'nanolab', 'run', '--testcase',
        'unit_tests/test_configs/threaded_with_group.json'
    ])
    def test_threaded_with_group(self):
        start_time = time.time()
        run.main()
        duration = time.time() - start_time
        self.assertTrue(duration > 0.98, f"too short: {duration:.2f} s")
        self.assertTrue(duration < 1.02, f"too long: {duration:.2f} s")

    @patch('sys.argv', [
        'nanolab', 'run', '--testcase',
        'unit_tests/test_configs/threaded_delay_negative.json'
    ])
    def test_threaded_delay_negative(self):
        start_time = time.time()
        run.main()
        duration = time.time() - start_time
        self.assertTrue(duration > 0.48, f"too short: {duration:.2f} s")
        self.assertTrue(duration < 0.52, f"too long: {duration:.2f} s")

    @patch('sys.argv', [
        'nanolab', 'run', '--testcase',
        'unit_tests/test_configs/threaded_delay.json'
    ])
    def test_threaded_delay(self):
        start_time = time.time()
        run.main()
        duration = time.time() - start_time
        self.assertTrue(duration > 0.48, f"too short: {duration:.2f} s")
        self.assertTrue(duration < 0.52, f"too long: {duration:.2f} s")

    @patch('sys.argv', [
        'nanolab', 'run', '--testcase',
        'unit_tests/test_configs/snippet_python_valid.json'
    ])
    def test_python_snippet(self):
        expected_output = "Hello there from python snippet"
        match_expected_output(expected_output)

    @patch('sys.argv', [
        'nanolab', 'run', '--testcase',
        'unit_tests/test_configs/snippet_python_list.json'
    ])
    def test_python_snippet_list(self):
        expected_output = "['pr1', 'pr2'] 2"
        match_expected_output(expected_output)

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

    @patch('sys.argv', [
        'nanolab', 'run', '--testcase',
        'unit_tests/test_configs/globals_resolve_url.json'
    ])
    def test_resolve_url(self):
        expected_output = "mDMEXZTdLxYJKwYBBAHaRw8BAQdAPXgGtAVcgz+RNJRvSgk1YrV5bzEY"
        contains_expected_substring(expected_output)

    @patch('sys.argv', [
        'nanolab', 'run', '--testcase',
        'unit_tests/test_configs/globals_resolve_path.json'
    ])
    def test_resolve_path(self):
        expected_output = "globals_resolve_path"
        contains_expected_substring(expected_output)

    @patch('sys.argv', [
        'nanolab', 'run', '--testcase',
        'unit_tests/test_configs/snippet_circular_ref.json'
    ])
    def test_snippet_circular_reference(self):
        expected_message = "Circular snippet reference detected: circular_in_snippet"
        match_expected_error(ValueError, expected_message)

    @patch('sys.argv', [
        'nanolab', 'run', '--testcase',
        'unit_tests/test_configs/snippet_nested_circular_ref.json'
    ])
    def test_snippet_nested_circular_reference(self):
        expected_message = "Circular snippet reference detected: nested_circular_in_snippet_p1"
        match_expected_error(ValueError, expected_message)

    # @patch('sys.argv', [
    #     'nanolab', 'run', '--testcase',
    #     'unit_tests/test_configs/valid_threaded_snippet.json'
    # ])
    # def test_valid_threaded_snippet(self):
    #     expected_message = "test_snippet outside threaded"
    #     contains_expected_substring(expected_message)


if __name__ == '__main__':
    unittest.main()
