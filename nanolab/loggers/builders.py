from abc import ABC, abstractmethod
from nanolab.loggers.sources.rpc_logger import RPCLogger


class LoggerBuilder(ABC):

    def __init__(self):
        self.timeout = None

    def set_timeout(self, timeout):
        self.timeout = timeout
        return self

    @abstractmethod
    def build(self):
        pass


class RPCLoggerBuilder(LoggerBuilder):

    def __init__(self):
        super().__init__()
        self.rpc_url = None
        self.expected_blocks_count = None
        self.node_name = None

    def set_rpc_url(self, rpc_url):
        self.rpc_url = rpc_url
        return self

    def set_expected_blocks_count(self, expected_blocks_count):
        self.expected_blocks_count = expected_blocks_count
        return self

    def set_node_name(self, node_name):
        self.node_name = node_name
        return self

    def build(self):
        if self.rpc_url is None or self.expected_blocks_count is None or self.node_name is None:
            raise Exception("Missing required parameters")
        return RPCLogger(self.node_name, self.rpc_url,
                         self.expected_blocks_count, self.timeout)


# class WebSocketLoggerBuilder(LoggerBuilder):

#     def __init__(self):
#         super().__init__()
#         self.websocket_url = None
#         self.channel = None

#     def set_websocket_url(self, websocket_url):
#         self.websocket_url = websocket_url
#         return self

#     def set_channel(self, channel):
#         self.channel = channel
#         return self

#     def build(self):
#         if self.websocket_url is None or self.channel is None:
#             raise Exception("Missing required parameters")
#         # Assuming a hypothetical WebSocketLogger class
#         return WebSocketLogger(self.websocket_url, self.channel, self.timeout)
