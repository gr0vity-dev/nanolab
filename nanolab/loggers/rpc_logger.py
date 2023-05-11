from .base_logger import AbstractLogger
from nanomock.modules.nl_rpc import NanoRpc
import time
import asyncio


class RPCLogger(AbstractLogger):

    def __init__(self, rpc_url: str, expected_blocks_count: int, timeout: int,
                 cemented_start: int, count_start: int):
        self.rpc_url = rpc_url
        self.expected_blocks_count = expected_blocks_count
        self.timeout = timeout
        self.nanorpc = NanoRpc(self.rpc_url)
        self.cemented_start = cemented_start
        self.count_start = count_start

    def is_fully_synced(self):
        block_count = self.nanorpc.block_count()

        cemented = int(block_count["cemented"])
        count = int(block_count["count"])

        cemented_diff = cemented - self.cemented_start
        is_synced = cemented_diff == self.expected_blocks_count
        return is_synced, count, cemented

    async def fetch_logs(self):
        previous_count = 0
        previous_cemented = 0
        start_time = time.time()

        while True:
            is_synced, check_count, cemented_count = self.is_fully_synced()
            elapsed_time = int(time.time() - start_time)

            logs = {
                'elapsed_time': elapsed_time,
                'check_count': check_count,
                'cemented_count': cemented_count,
                'previous_count': previous_count,
                'previous_cemented': previous_cemented,
            }

            yield logs

            if is_synced or elapsed_time > self.timeout:
                break

            previous_count = check_count
            previous_cemented = cemented_count
            await asyncio.sleep(1)