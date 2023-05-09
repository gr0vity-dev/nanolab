import json
import ssl
import threading
#import websocket
import asyncio
import time
from typing import List, Any
from nanomock.modules.nl_rpc import NanoRpc


class StatsLogger:

    def __init__(self,
                 logger_type: str,
                 node_name: str,
                 node_version: str,
                 hashes: List[Any],
                 start_block_count: dict,
                 timeout: int = 600,
                 expected_block_count=None,
                 ws_url: str = None,
                 rpc_url: str = None):

        self.logger_type = logger_type
        self.timeout = timeout
        self.node_name = node_name
        self.node_version = node_version
        self.ws_url = ws_url
        self.rpc_url = rpc_url
        self.hashes = hashes
        #self.start_block_count = start_block_count
        self.count_start = int(start_block_count["count"])
        self.cemented_start = int(start_block_count["cemented"])
        self.expected_blocks_count = expected_block_count or len(hashes)
        self.count_total = self.expected_blocks_count + self.count_start
        self.nanorpc = NanoRpc(self.rpc_url)
        self.logging_task = None

    def is_fully_synced(self):
        block_count = self.nanorpc.block_count()

        cemented = int(block_count["cemented"])
        count = int(block_count["count"])

        cemented_diff = cemented - self.cemented_start
        is_synced = cemented_diff == self.expected_blocks_count
        return is_synced, count, cemented

    def print_rpc_stats(self, elapsed_time, check_count, cemented_count,
                        previous_count, previous_cemented):
        bps = 0 if previous_count == 0 else check_count - previous_count
        cps = 0 if previous_cemented == 0 else cemented_count - previous_cemented
        print(
            f"{elapsed_time:>4} seconds {self.node_name:>12} | {self.node_version} | \
{cemented_count:>7}/{check_count:>7}/{self.count_total:>7} @{bps:>5} bps \
(avg: {round((check_count - self.count_start)/max(1, elapsed_time),2)}) | \
@{cps:>5} cps (avg: {round((cemented_count - self.cemented_start)/max(1, elapsed_time),2)})"
        )

    def print_ws_stats(self, elapsed_time, cemented_count, previous_cemented):
        cps = 0 if previous_cemented == 0 else cemented_count - previous_cemented
        print(
            f"""{elapsed_time:>4} seconds {self.node_name:>12} | {self.node_version} | @{cps:>5} cps (avg: {round((cemented_count)/max(1, elapsed_time),2)})"""
        )

    async def log_rpc(self):
        if not self.rpc_url:
            raise ValueError("rpc_url must be defined")

        previous_count = 0
        previous_cemented = 0
        start_time = time.time()

        while True:
            is_synced, check_count, cemented_count = self.is_fully_synced()
            elapsed_time = int(time.time() - start_time)
            self.print_rpc_stats(elapsed_time, check_count, cemented_count,
                                 previous_count, previous_cemented)

            if is_synced or elapsed_time > self.timeout:
                break

            previous_count = check_count
            previous_cemented = cemented_count
            await asyncio.sleep(1)

    async def log_websocket(self):
        if not self.ws_url:
            raise ValueError("ws_url must be defined")

        simple_ws = SimpleWs(self.ws_url,
                             self.node_name,
                             self.node_version,
                             ws_topics=["confirmation"])

        cemented_count = 0
        previous_cemented = 0
        start_time = time.time()

        while cemented_count < len(self.hashes):
            cemented_count = simple_ws.confirmed_hashes
            elapsed_time = int(time.time() - start_time)
            self.print_ws_stats(elapsed_time, cemented_count,
                                previous_cemented)

            if elapsed_time > self.timeout:
                break

            previous_cemented = cemented_count
            await asyncio.sleep(1)

        simple_ws.ws.close()

    async def start(self):
        if self.logger_type == "rpc":
            await self.log_rpc()
        elif self.logger_type == "ws":
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
        self.confirmed_hashes = 0
        self.lock = threading.Lock()

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

    def increment_confirmed_hash_count(self):
        with self.lock:
            self.confirmed_hashes += 1

    def on_message(self, ws, message):
        self.increment_confirmed_hash_count()
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
