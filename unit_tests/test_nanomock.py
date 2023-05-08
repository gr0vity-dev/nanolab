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

    dummy_args = Namespace(config=None, snippets=None)

    def load_config_to_env(self, config_path):
        os.environ["CONFIG_FILE"] = str(config_path)

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

    # def test_nanolocal_down(self):
    #     os.environ["NL_CONF_DIR"] = "unit_tests/nanomock"
    #     os.environ["NL_CONF_FILE"] = "nl_config.toml"
    #     self.load_config_to_env('unit_tests/test_configs/nanomock_down.json')
    #     expected_output = "SUCCESS: 0 containers have been removed"
    #     self.contains_expected_substring(expected_output)

    def test_nanolocal_create(self):
        os.environ["NL_CONF_DIR"] = "unit_tests/nanomock"
        os.environ["NL_CONF_FILE"] = "nl_config.toml"
        self.load_config_to_env(
            'unit_tests/test_configs/nanomock_create_down.json')
        expected_output = "SUCCESS: 2 containers have been removed"
        self.contains_expected_substring(expected_output)


if __name__ == '__main__':
    unittest.main()
