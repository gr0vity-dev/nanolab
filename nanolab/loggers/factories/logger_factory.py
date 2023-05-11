from nanolab.loggers.rpc_logger import RPCLogger


class LoggerFactory:

    @staticmethod
    def create_logger(logger_type, *args, **kwargs):
        if logger_type == 'rpc':
            return RPCLogger(*args, **kwargs)
        elif logger_type == 'ws':
            pass
            #return WebSocketsLogger(*args, **kwargs)
        else:
            raise ValueError(f"Invalid logger_type: {logger_type}")