import time
import app.node_interaction as nni
from app.node_tools import StatsLogger
import asyncio

statsLogger = None


class NodeCommands:
    pass


class TestClass:

    def long_running_method(self, duration=1):
        time.sleep(duration)


class NodeInteraction:

    def __init__(self):
        # Your existing code...
        self.logger = None

    def publish_blocks_test(self,
                            params,
                            logger_type="rpc",
                            logger_timeout=600,
                            logger_include_peers=None,
                            logger_exclude_peers=None):

        asyncio.run(
            nni.xnolib_publish(params, logger_type, logger_timeout,
                               logger_include_peers, logger_exclude_peers))
