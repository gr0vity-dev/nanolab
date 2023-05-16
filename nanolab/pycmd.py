import time
import nanolab.node_interaction as nni
import asyncio
from nanolab.publisher.test_case import TestCaseFactory


class TestClass:

    def long_running_method(self, duration=1):
        time.sleep(duration)

    def test_list(self, test_list):
        if isinstance(test_list, list):
            print(test_list, len(test_list))

    def print_to_console(self, value):
        print(value)

    def return_value(self, value):
        return value


class NodeInteraction:

    def __init__(self):
        # Your existing code...
        self.logger = None

    def start_logger(self, logger_params, sink_params):
        asyncio.run(nni.start_loggers(logger_params, sink_params))

    def publish_create(self, params):
        # Create the test case using the factory
        test_case = TestCaseFactory.create(params)
        asyncio.run(test_case.run())

    def publish_blocks(self, publish_params):
        '''
        mandatory publish_params: blocks_path, bps
         optional publish_params: peers, split, split_skip, reverse, shuffle, 
                  start_round, end_round, subset.start_index, subset.end_index
         '''

        asyncio.run(nni.xnolib_publish(publish_params))
