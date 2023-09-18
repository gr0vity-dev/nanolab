from nanolab.loggers.contracts import ILogger, LogData
from nanomock.modules.nl_rpc import NanoRpc
import time
from datetime import datetime
import asyncio
from typing import AsyncIterator


class RPCLogger(ILogger):
    """A logger that fetches logs from an RPC endpoint."""

    FETCH_INTERVAL_DELAY = 0.1  # seconds

    def __init__(self,
                 node_name: str,
                 rpc_url: str,
                 expected_blocks_count: int,
                 timeout: int,
                 count_start=None,
                 cemented_start=None):
        self.node_name = node_name
        self.rpc_url = rpc_url
        self.expected_blocks_count = expected_blocks_count
        self.timeout = int(timeout)
        self.nanorpc = NanoRpc(self.rpc_url)
        if count_start is None or cemented_start is None:
            self.count_start, self.cemented_start = self._get_block_count()
        else:
            self.count_start = count_start
            self.cemented_start = cemented_start
        node_version = self.nanorpc.version()
        self.node_version = f'{node_version["node_vendor"]} {node_version["build_info"][0:7]}' if node_version else "???"
        self.end_block_count = self.count_start + self.expected_blocks_count
        self.previous_count = 0
        self.previous_cemented = 0
        self.previous_elapsed_time = 0

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
        timeout_start = time.time()
        while True:
            count, cemented = self._get_block_count()
            is_synced = self.is_fully_synced(cemented)
            percent_cemented = ((cemented - self.cemented_start) /
                                self.expected_blocks_count) * 100
            percent_checked = (
                (count - self.count_start) / self.expected_blocks_count) * 100

            # Loggers are cerated before the publishing starts.
            # Elapsed is started when the first blcok is received by the node
            if percent_checked == 0:
                start_time = time.time()
            elapsed_time = int(time.time() - start_time)

            cps = (cemented - self.previous_cemented) / max(
                1, (elapsed_time -
                    self.previous_elapsed_time)) if percent_checked > 0 else 0
            bps = (count - self.previous_count) / max(
                1, (elapsed_time -
                    self.previous_elapsed_time)) if percent_checked > 0 else 0

            bps_avg = (
                count - self.count_start
            ) / elapsed_time if elapsed_time > 0 and percent_checked < 100 else None
            cps_avg = (cemented - self.cemented_start
                       ) / elapsed_time if elapsed_time > 0 else None

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
                bps_avg=bps_avg,
                cps_avg=cps_avg)
            if is_synced or time.time() - timeout_start > self.timeout:
                break

            self.previous_count = count
            self.previous_cemented = cemented
            self.previous_elapsed_time = elapsed_time
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
