from nanolab.loggers.factories.logger_factory import LoggerFactory
from nanolab.loggers.factories.sink_factory import SinkFactory
from nanolab.loggers.contracts import ILogger, ISink
from nanolab.src.utils import get_config_parser
import asyncio
from typing import List, Dict


class LoggingManager:

    def __init__(self, logger_params, sink_params: List[Dict]):
        self.nodes_config = get_config_parser().get_nodes_config()
        self.included_peers = logger_params.pop("included_peers", None)
        self.excluded_peers = logger_params.pop("excluded_peers", [])
        self.interval = logger_params.pop("interval", 1)
        self.logger_type = logger_params.pop("type", "rpc")

        self.logger_params = logger_params
        self.sink_params_list = sink_params

    async def create_logger_and_storages(self, current_logger_params):
        logger = LoggerFactory.create_logger(self.logger_type,
                                             current_logger_params)

        storages = []
        for sink_params in self.sink_params_list:
            sink_type = sink_params.pop("type", "console")
            storage = SinkFactory.create_storage(sink_type, sink_params)
            storages.append(storage)

        return logger, storages

    async def create_loggers(self):
        for node in self.nodes_config:
            if (self.included_peers and node["name"] not in self.included_peers
                ) or node["name"] in self.excluded_peers:
                continue
            current_params = dict(self.logger_params)
            current_params["node_name"] = node["name"]
            current_params["rpc_url"] = node["rpc_url"]
            yield await self.create_logger_and_storages(current_params)

    async def start_logging(self):
        tasks = []
        async for logger, storages in self.create_loggers():
            tasks.append(
                self.perform_logging_task(logger, storages, self.interval))
        await asyncio.gather(*tasks)

    async def perform_logging_task(self, logger: ILogger,
                                   storages: List[ISink], interval: int):
        async for logs in logger.fetch_logs():
            for storage in storages:
                storage.store_logs(logs)
            await asyncio.sleep(interval)
        for storage in storages:
            storage.end()
