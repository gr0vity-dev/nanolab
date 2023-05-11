# handlers/logger_handler.py

from nanolab.decorators import ensure_duration
from nanomock.modules.nl_rpc import NanoRpc
from nanolab.loggers.factories.logger_factory import LoggerFactory
from nanolab.loggers.factories.sink_factory import StorageFactory
from nanolab.loggers.base_logger import AbstractLogger
from nanolab.loggers.sinks.base_sink import AbstractStorage
import asyncio


class LoggerHandler:

    def __init__(self, nodes_config):
        self.nodes_config = nodes_config

    async def create_logger_and_storage(self, node, logger_type, hashes,
                                        logger_timeout, logger_expected_count,
                                        storage_type):
        nanorpc = NanoRpc(node["rpc_url"])
        node_version = nanorpc.version()
        formatted_node_version = f'{node_version["node_vendor"]} {node_version["build_info"][0:7]}'
        start_block_count = nanorpc.block_count()

        cemented_start = int(start_block_count["cemented"])
        count_start = int(start_block_count["count"])

        logger = LoggerFactory.create_logger(logger_type, node["rpc_url"],
                                             len(hashes), logger_timeout,
                                             cemented_start, count_start)
        storage = StorageFactory.create_storage(storage_type, node["name"],
                                                formatted_node_version,
                                                count_start, cemented_start,
                                                len(hashes) + count_start)

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

    async def perform_logging_task(self, logger: AbstractLogger,
                                   storage: AbstractStorage):
        async for logs in logger.fetch_logs():
            storage.store_logs(logs)
