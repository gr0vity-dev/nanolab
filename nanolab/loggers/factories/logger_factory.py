from nanolab.loggers.builders import RPCLoggerBuilder
from typing import Dict, Any

# class LoggerFactory:

#     @staticmethod
#     def create_logger(logger_type, *args, **kwargs):
#         if logger_type == 'rpc':
#             return RPCLogger(*args, **kwargs)
#         elif logger_type == 'ws':
#             pass
#             #return WebSocketsLogger(*args, **kwargs)
#         else:
#             raise ValueError(f"Invalid logger_type: {logger_type}")


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