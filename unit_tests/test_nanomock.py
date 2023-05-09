import unittest
import json
import time
import os
from unittest.mock import patch
from .utils import contains_expected_substring


#@patch decorator is used to replace 'app.run.NodeInteraction' with the following TestClass
class TestClass:

    def long_running_method(self, duration=1):
        time.sleep(duration)


class TestRun(unittest.TestCase):

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
