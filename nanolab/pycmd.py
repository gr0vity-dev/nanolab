import time
import nanolab.node_interaction as nni
import asyncio


class TestClass:

    def long_running_method(self, duration=1):
        time.sleep(duration)


class NodeInteraction:

    def __init__(self):
        # Your existing code...
        self.logger = None

    def start_logger(self, logger_type, sink_type, logger_params):
        asyncio.run(nni.start_loggers(logger_type, sink_type, logger_params))

    def publish_blocks(self, publish_params):
        '''
        mandatory publish_params: blocks_path, bps
         optional publish_params: peers, split, split_skip, reverse, shuffle, 
                  start_round, end_round, subset.start_index, subset.end_index
         '''

        asyncio.run(nni.xnolib_publish(publish_params))
