import unittest
import json
import time
import os
import io
from pathlib import Path
from unittest.mock import patch
import nanolab.main as run
import pytest
from argparse import Namespace


#@patch decorator is used to replace 'app.run.NodeInteraction' with the following TestClass
class TestClass:

    def long_running_method(self, duration=1):
        time.sleep(duration)


class TestRun(unittest.TestCase):

    #allow pytest to work with interference from argparse config
    dummy_args = Namespace(config=None, snippets=None)

    @staticmethod
    def load_json(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)

    def load_config_to_env(self, config_path):
        os.environ["CONFIG_FILE"] = str(config_path)
        #os.environ["SNIPPET_FILE"] = "unit_tests/test_snippets.json"

    def match_expected_error(self, error_type, expected_message):
        with self.assertRaises(error_type) as cm:
            run.main(self.dummy_args)

        self.assertEqual(str(cm.exception), expected_message)

    def match_expected_output(self, expected_output):
        captured_output = io.StringIO()
        # Replace sys.stdout with captured_output within the context
        with patch('sys.stdout', captured_output):
            run.main(self.dummy_args)

        # Get the captured output as a string
        output = captured_output.getvalue().replace("\r", "").replace("\n", "")

        self.assertEqual(output, expected_output)

    def contains_expected_substring(self, expected_substring):
        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            run.main(self.dummy_args)
        # Get the captured output as a string
        output = captured_output.getvalue().replace("\r", "").replace("\n", "")

        self.assertIn(expected_substring, output)

    def test_invalid_type(self):
        self.load_config_to_env('unit_tests/test_configs/invalid_type.json')
        expected_message = "Invalid command type 'invalid' at index 0 in 'commands'"
        self.match_expected_error(ValueError, expected_message)

    def test_invalid_snippet_key(self):
        self.load_config_to_env(
            'unit_tests/test_configs/invalid_snippet_key.json')
        expected_message = "'non_existent_snippet'"
        self.match_expected_error(KeyError, expected_message)

    def test_invalid_method(self):
        self.load_config_to_env('unit_tests/test_configs/invalid_method.json')
        expected_message = "Python command: Method 'non_existent_method' not found in class 'NodeInteraction'."
        self.match_expected_error(ValueError, expected_message)

    def test_invalid_snippet_missing_mandatory_var(self):
        self.load_config_to_env(
            'unit_tests/test_configs/invalid_snippet_missing_mandatory_var.json'
        )
        expected_message = "'Missing value(s) for mandatory variable(s): unused_mandatory_var'"
        self.match_expected_error(KeyError, expected_message)

    def test_threaded_parallel(self):
        start_time = time.time()
        self.load_config_to_env(
            'unit_tests/test_configs/threaded_parallel.json')
        run.main(self.dummy_args)
        duration = time.time() - start_time
        self.assertTrue(duration > 0.48) and self.assertTrue(duration < 0.52)

    def test_threaded_with_group(self):
        start_time = time.time()
        self.load_config_to_env(
            'unit_tests/test_configs/threaded_with_group.json')
        run.main(self.dummy_args)
        duration = time.time() - start_time
        self.assertTrue(duration > 0.18, f"too short: {duration:.2f} s")
        self.assertTrue(duration < 0.22, f"too long: {duration:.2f} s")

    def test_valid_snippets_and_bash(self):
        self.load_config_to_env(
            'unit_tests/test_configs/valid_snippets_and_bash.json')
        expected_output = "Hello, World!file test.txt"
        self.match_expected_output(expected_output)

    def test_snippet_without_vars(self):
        self.load_config_to_env(
            'unit_tests/test_configs/snippet_without_vars.json')
        expected_output = "No vars needed!"
        self.match_expected_output(expected_output)

    def test_snippet_in_snippet(self):
        self.load_config_to_env(
            'unit_tests/test_configs/snippet_in_snippet.json')
        expected_output = "file test.txt"
        self.match_expected_output(expected_output)

    def test_snippet_with_unused_vars(self):
        self.load_config_to_env(
            'unit_tests/test_configs/snippet_with_unused_vars.json')
        expected_output = "file test.txt"
        self.match_expected_output(expected_output)

    def test_docker_tags(self):
        self.load_config_to_env('unit_tests/test_configs/docker_tags.json')
        expected_output = "tag1nanocurrency/nano:V24.0"
        self.match_expected_output(expected_output)


if __name__ == '__main__':
    unittest.main()
