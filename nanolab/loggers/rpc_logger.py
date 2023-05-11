from .contracts import ILogger, LogData
from nanomock.modules.nl_rpc import NanoRpc
import time
from datetime import datetime
import asyncio
from typing import AsyncIterator


class RPCLogger(ILogger):
    """A logger that fetches logs from an RPC endpoint."""

    FETCH_INTERVAL_DELAY = 0.1  # seconds

    def __init__(self, node_name: str, rpc_url: str,
                 expected_blocks_count: int, timeout: int):
        self.node_name = node_name
        self.rpc_url = rpc_url
        self.expected_blocks_count = expected_blocks_count
        self.timeout = timeout
        self.nanorpc = NanoRpc(self.rpc_url)
        self.count_start, self.cemented_start = self._get_block_count()
        node_version = self.nanorpc.version()
        self.node_version = f'{node_version["node_vendor"]} {node_version["build_info"][0:7]}'
        self.end_block_count = self.count_start + self.expected_blocks_count
        self.previous_count = 0
        self.previous_cemented = 0

    def _get_block_count(self):
        block_count = self.nanorpc.block_count()
        return int(block_count["count"]), int(block_count["cemented"])

    def is_fully_synced(self, cemented):
        cemented_diff = cemented - self.cemented_start
        is_synced = cemented_diff == self.expected_blocks_count
        return is_synced

    async def fetch_logs(self) -> AsyncIterator[LogData]:
        """Yield logs at intervals."""
        start_time = time.time()

        while True:
            count, cemented = self._get_block_count()
            is_synced = self.is_fully_synced(cemented)
            elapsed_time = int(time.time() - start_time)
            percent_cemented = (cemented / self.end_block_count) * 100
            percent_checked = (count / self.end_block_count) * 100

            cps = cemented - self.previous_cemented if self.previous_cemented is not None else 0
            bps = count - self.previous_count if self.previous_count is not None else 0

            yield LogData(
                node_name=self.node_name,
                node_version=self.node_version,
                elapsed_time=elapsed_time,
                check_count=count,
                cemented_count=cemented,
                cps=cps,
                bps=bps,
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                percent_cemented=percent_cemented,
                percent_checked=percent_checked,
            )
            if is_synced or elapsed_time > self.timeout:
                break

            self.previous_count = count
            self.previous_cemented = cemented
            await asyncio.sleep(self.FETCH_INTERVAL_DELAY)


# class RPCLogger(ILogger):

#     def __init__(
#         self,
#         rpc_url: str,
#         expected_blocks_count: int,
#         timeout: int,
#     ):
#         self.nanorpc = NanoRpc(rpc_url)
#         self.expected_blocks_count = expected_blocks_count
#         self.timeout = timeout
#         self.count_start, self.cemented_start = self._get_block_count()

#     def _get_block_count(self):
#         block_count = self.nanorpc.block_count()
#         return int(block_count["count"]), int(block_count["cemented"])

#     def is_fully_synced(self):
#         count, cemented = self.nanorpc.block_count()
#         cemented_diff = cemented - self.cemented_start
#         is_synced = cemented_diff == self.expected_blocks_count
#         return is_synced, count, cemented

#     async def fetch_logs(self):
#         previous_count = 0
#         previous_cemented = 0
#         start_time = time.time()

#         while True:
#             is_synced, check_count, cemented_count = self.is_fully_synced()
#             elapsed_time = int(time.time() - start_time)

#             logs = {
#                 'elapsed_time': elapsed_time,
#                 'check_count': check_count,
#                 'cemented_count': cemented_count,
#                 'previous_count': previous_count,
#                 'previous_cemented': previous_cemented,
#             }

#             yield logs

#             if is_synced or elapsed_time > self.timeout:
#                 break

#             previous_count = check_count
#             previous_cemented = cemented_count
#             await asyncio.sleep(1)