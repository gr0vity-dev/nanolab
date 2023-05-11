# handlers/logger_handler.py

from nanolab.decorators import ensure_duration
from nanomock.modules.nl_rpc import NanoRpc
from nanolab.loggers.factories.logger_factory import LoggerFactory
from nanolab.loggers.factories.sink_factory import SinkFactory
from nanolab.loggers.contracts import ILogger, ISink
import asyncio


class LoggerHandler:

    def __init__(self, nodes_config):
        self.nodes_config = nodes_config

    async def create_logger_and_storage(self, node, logger_type, hashes,
                                        logger_timeout, logger_expected_count,
                                        storage_type):
        config = {
            "rpc_url": node["rpc_url"],
            "node_name": node["name"],
            "expected_blocks_count": logger_expected_count,
            "timeout": logger_timeout
        }

        logger = LoggerFactory.create_logger(logger_type, config)
        storage = SinkFactory.create_storage(storage_type)

        return logger, storage

    @ensure_duration(duration=2)
    async def create_loggers(self,
                             hashes,
                             logger_type=None,
                             logger_timeout=None,
                             included_peers=None,
                             excluded_peers=None,
                             logger_expected_count=None,
                             storage_type=None):
        if not logger_type: return []
        tasks = []
        for node in self.nodes_config:
            if included_peers and node["name"] not in included_peers:
                continue
            if excluded_peers and node["name"] in excluded_peers:
                continue
            tasks.append(
                self.create_logger_and_storage(node, logger_type, hashes,
                                               logger_timeout,
                                               logger_expected_count,
                                               storage_type))

        loggers_and_storages = await asyncio.gather(*tasks)
        return loggers_and_storages

    def get_logger_tasks(self, loggers_and_storages):
        logger_tasks = [
            asyncio.create_task(self.perform_logging_task(logger, storage))
            for logger, storage in loggers_and_storages
        ]
        return logger_tasks

    async def perform_logging_task(self,
                                   logger: ILogger,
                                   storage: ISink,
                                   sleep_period: int = 1):
        async for logs in logger.fetch_logs():
            storage.store_logs(logs)
            await asyncio.sleep(sleep_period)