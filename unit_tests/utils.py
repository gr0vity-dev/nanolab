import nanolab.main as run
import os
from io import StringIO
from unittest.mock import patch
import unittest
import nanolab.main as run

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