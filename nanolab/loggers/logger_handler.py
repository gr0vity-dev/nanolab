from nanolab.loggers.factories.logger_factory import LoggerFactory
from nanolab.loggers.factories.sink_factory import SinkFactory
from nanolab.loggers.contracts import ILogger, ISink
import asyncio


class LoggerHandler:

    def __init__(self, nodes_config, logger_params):
        self.nodes_config = nodes_config
        self.included_peers = logger_params.pop("included_peers", None)
        self.excluded_peers = logger_params.pop("excluded_peers", [])
        self.interval = logger_params.pop("interval", 1)
        self.logger_params = logger_params

    async def create_logger_and_storage(self, logger_type, sink_type,
                                        logger_config):
        logger = LoggerFactory.create_logger(logger_type, logger_config)
        storage = SinkFactory.create_storage(sink_type, logger_config)
        return logger, storage

    async def create_loggers(self, logger_type, sink_type, logger_params):
        tasks = []
        for node in self.nodes_config:
            if (self.included_peers and node["name"] not in self.included_peers
                ) or node["name"] in self.excluded_peers:
                continue
            current_params = dict(logger_params)
            current_params["node_name"] = node["name"]
            current_params["rpc_url"] = node["rpc_url"]
            tasks.append(
                self.create_logger_and_storage(logger_type, sink_type,
                                               current_params))

        return await asyncio.gather(*tasks)

    async def start_logging(self, logger_type, sink_type):

        loggers_and_storages = await self.create_loggers(
            logger_type, sink_type, self.logger_params)
        tasks = [
            self.perform_logging_task(logger, storage, self.interval)
            for logger, storage in loggers_and_storages
        ]
        await asyncio.gather(*tasks)

    async def perform_logging_task(self, logger: ILogger, storage: ISink,
                                   interval: int):
        async for logs in logger.fetch_logs():
            storage.store_logs(logs)
            await asyncio.sleep(interval)
