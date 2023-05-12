from nanolab.loggers.builders import RPCLoggerBuilder
from typing import Dict, Any


class LoggerFactory:

    @staticmethod
    def create_logger(logger_type: str, config: Dict[str, Any]):
        if logger_type == "rpc":
            builder = RPCLoggerBuilder()
        elif logger_type == "websocket":
            pass
            #builder = WebsocketLoggerBuilder()
        else:
            raise ValueError(f"Unknown logger type: {logger_type}")

        for key, value in config.items():
            if hasattr(builder, f'set_{key}'):
                getattr(builder, f'set_{key}')(value)

        return builder.build()