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

    def publish_blocks(self,
                       publish_params,
                       logger_type=None,
                       logger_timeout=600,
                       logger_include_peers=None,
                       logger_exclude_peers=None,
                       logger_expected_count=None):
        '''
        mandatory publish_params: blocks_path, bps
        optional  publish_params: peers, split, split_skip, reverse, shuffle, 
                  start_round, end_round, subset.start_index, subset.end_index
         '''

        asyncio.run(
            nni.xnolib_publish(publish_params, logger_type, logger_timeout,
                               logger_include_peers, logger_exclude_peers,
                               logger_expected_count))
