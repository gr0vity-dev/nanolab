from abc import ABC, abstractmethod
from nanolab.src.nano_rpc import NanoRpcV2
from nanolab.src.utils import get_config_parser
import asyncio
import time


class IBlockAsserts(ABC):

    @abstractmethod
    async def assert_blocks_published(self, blocks):
        pass

    @abstractmethod
    async def assert_all_blocks_cemented(self):
        pass

    @abstractmethod
    async def assert_blocks_confirmed(self, block_hashes):
        pass

    @abstractmethod
    async def assert_blocks_confirmed_wait(self, block_hashes, wait_s,
                                           interval):
        pass

    @abstractmethod
    async def assert_single_block_confirmed(self, block_hash: str):
        pass

    @abstractmethod
    async def assert_single_block_confirmed_wait(self, block_hash, wait_s,
                                                 interval):
        pass


# This class contains the actual implementation of our block assertions.


class BlockAsserts(IBlockAsserts):

    def __init__(self, node_name=None):
        conf_p = get_config_parser()
        node_name = node_name if node_name else conf_p.get_nodes_name()[:-1]
        self.nano_rpc_default = NanoRpcV2(conf_p.get_node_rpc(node_name))
        self.nano_rpc_all = [NanoRpcV2(url) for url in conf_p.get_nodes_rpc()]

    async def _fetch_block_info(self, block_hash):
        return await self.nano_rpc_default.block_info(block_hash,
                                                      json_block="true")

    async def _fetch_all_block_info(self, block_hashes, filter_func=None):
        tasks = [
            self._fetch_block_info(block_hash) for block_hash in block_hashes
        ]
        responses = await asyncio.gather(*tasks)

        # The mapping relies on the fact the asyncio.gather function preserves the order of results,
        # meaning that results are returned in the order of the input awaitable objects.
        responses = [{
            **response, 'hash': hash
        } for response, hash in zip(responses, block_hashes)]
        if filter_func:
            responses = list(filter(filter_func, responses))
        return responses

    async def assert_blocks_published(self, blocks):
        block_infos = await self._fetch_all_block_info(blocks)

        assert all(info['exists']
                   for info in block_infos), f"Some blocks were not published"

    def assert_all_blocks_cemented(self):
        for rpc in self.nano_rpc_all:
            block_count = rpc.block_count()
            assert block_count["count"] == block_count[
                "cemented"], "Not all blocks are cemented"

    async def _blocks_confirmed(self, block_hashes):
        confirmed_blocks = set()
        for block_hash in block_hashes:
            block_info = await self._fetch_block_info(block_hash)
            if block_info.get('confirmed') == "true":
                confirmed_blocks.add(block_hash)
        return confirmed_blocks

    async def _unconfirmed_blocks(self, block_hashes, batch_size=None):
        batch = list(block_hashes)[:batch_size] if batch_size else block_hashes
        confirmed_blocks = await self._blocks_confirmed(batch)
        unconfirmed_blocks = set(block_hashes) - confirmed_blocks
        return unconfirmed_blocks

    async def assert_blocks_confirmed(self, block_hashes):
        unconfirmed_blocks = self._unconfirmed_blocks(
            block_hashes, batch_size=len(block_hashes))
        if unconfirmed_blocks:
            raise AssertionError(
                f"{len(unconfirmed_blocks)} blocks are not confirmed")

    async def assert_blocks_confirmed_wait(self, block_hashes, wait_s,
                                           interval):
        start_time = time.time()
        batch_size = 1000
        while time.time() - start_time < wait_s:
            unconfirmed_blocks = await self._unconfirmed_blocks(
                block_hashes, batch_size=batch_size)
            if not unconfirmed_blocks:
                return
            await asyncio.sleep(interval)
        raise AssertionError("Not all blocks confirmed within the wait time")

    async def assert_single_block_confirmed(self, block_hash: str):
        await self.assert_blocks_confirmed([block_hash])

    async def assert_single_block_confirmed_wait(self, block_hash, wait_s,
                                                 interval):
        await self.assert_blocks_confirmed_wait([block_hash], wait_s, interval)