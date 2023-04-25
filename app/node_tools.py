import json
import ssl
import threading
#import websocket
import asyncio
import time
from typing import List, Any
from nanolocal.common.nl_rpc import NanoRpc


class StatsLogger:

    def __init__(self,
                 logger_type: str,
                 node_name: str,
                 node_version: str,
                 hashes: List[Any],
                 start_block_count: dict,
                 timeout: int = 600,
                 ws_url: str = None,
                 rpc_url: str = None):
        self.logger_type = logger_type
        self.timeout = timeout
        self.node_name = node_name
        self.node_version = node_version
        self.ws_url = ws_url
        self.rpc_url = rpc_url
        self.hashes = hashes
        self.start_block_count = start_block_count
        self.expected_blocks_count = len(hashes)
        self.synced_block_count = self.expected_blocks_count + int(
            start_block_count["count"])
        self.nanorpc = NanoRpc(self.rpc_url)

    def is_fully_synced(self):
        block_count = self.nanorpc.block_count()
        cemented_diff = int(block_count["cemented"]) - int(
            self.start_block_count["cemented"])
        is_synced = cemented_diff == self.expected_blocks_count
        return is_synced, int(block_count["count"]), int(
            block_count["cemented"])

    async def log_rpc(self):
        if not self.rpc_url:
            raise ValueError("rpc_url must be defined")

        previous_count = 0
        previous_cemented = 0
        start_time = time.time()

        for _ in range(self.timeout):
            is_synced, check_count, cemented_count = self.is_fully_synced()

            elapsed_time = int(time.time() - start_time)
            bps = check_count - previous_count
            cps = cemented_count - previous_cemented

            print(
                f"{elapsed_time:>4} seconds {self.node_name:>12} - {self.node_version} - {cemented_count:>7}/{check_count:>7}/{self.synced_block_count:>7} - @{bps:>5} bps - @{cps:>5} cps"
            )

            if is_synced:
                break

            previous_count = check_count
            previous_cemented = cemented_count
            await asyncio.sleep(1)

    async def log_websocket(self, ws_url):
        if not self.ws_url: raise ValueError("ws_url must be defined")
        # Initialize the SimpleWs class with the required parameters
        simple_ws = SimpleWs(ws_url,
                             self.node_name,
                             self.node_version,
                             ws_topics=["confirmation"])

        # Implement your logic to monitor the WebSocket messages and calculate the stats
        # You may need to use additional synchronization mechanisms like asyncio.Lock or asyncio.Queue
        # to safely access the shared data between the StatsLogger and SimpleWs classes

        # When finished, close the WebSocket connection
        simple_ws.ws.close()

    async def start(self):
        if self.logger_type == "rpc":
            await self.log_rpc()
        elif self.logger_type == "websocket":
            await self.log_websocket()
        else:
            raise ValueError(
                "Invalid logger_type. Must be 'rpc' or 'websocket'.")

    async def end(self):
        if self.logging_task:
            try:
                await asyncio.wait_for(self.logging_task, timeout=self.timeout)
            except asyncio.TimeoutError:
                print("Logging task timed out.")
            self.logging_task = None

    async def start_logging(self):
        await self.start()

    async def end_logging(self):
        await self.end()


class SimpleWs:

    def __init__(self,
                 ws_url: str,
                 node_name: str,
                 node_version: str,
                 ws_topics=["confirmation"]):
        self.ws_url = ws_url
        self.node_name = node_name
        self.ws_topics = ws_topics

        self.ws = websocket.WebSocketApp(
            ws_url,
            on_message=lambda ws, msg: self.on_message(ws, msg),
            on_error=lambda ws, msg: self.on_error(ws, msg),
            on_close=lambda ws, msg, err: self.on_close(ws, msg, err),
            on_open=lambda ws: self.on_open(ws))

        if ws_url.startswith("wss"):
            self.wst = threading.Thread(
                target=self.ws.run_forever,
                kwargs={"sslopt": {
                    "cert_reqs": ssl.CERT_NONE
                }},
                daemon=True)
        else:
            self.wst = threading.Thread(target=self.ws.run_forever,
                                        daemon=True)

        self.wst.start()

    def on_message(self, ws, message):
        print(message)
        # You can implement your logic for handling WebSocket messages here.

    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws, msg, error):
        print("### websocket connection closed ###")

    def on_open(self, ws):
        if "confirmation" in self.ws_topics:
            ws.send(
                json.dumps({
                    "action": "subscribe",
                    "topic": "confirmation",
                    "options": {
                        "include_election_info": "false",
                        "include_block": "true"
                    }
                }))
        print("### websocket connection opened ###")
