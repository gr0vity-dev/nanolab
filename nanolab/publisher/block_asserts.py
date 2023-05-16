from abc import ABC, abstractmethod
from nanolab.src.nano_rpc import NanoRpcV2
from nanolab.publisher.block_event import BlockConfirmationEvent
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

    def __init__(self, event_bus=None, node_name=None):
        self.event_bus = event_bus
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
        unconfirmed_blocks = await self._unconfirmed_blocks(
            block_hashes, batch_size=len(block_hashes))
        if unconfirmed_blocks:
            raise AssertionError(
                f"{len(list(unconfirmed_blocks))} blocks are not confirmed")

    async def _publish_block_confirmation_event(self, wait_s, block_hash,
                                                timeout):
        if not self.event_bus: return
        event = BlockConfirmationEvent(block_hash, timeout, wait_s)
        await self.event_bus.publish('block_confirmed', event)

    async def assert_blocks_confirmed_wait(self, block_hashes, wait_s,
                                           interval):
        batch_size = 1000
        unconfirmed_blocks = set(block_hashes)
        start_time = time.time()
        while time.time() - start_time < wait_s and unconfirmed_blocks:
            confirmed_blocks = await self._blocks_confirmed(
                list(unconfirmed_blocks)[:batch_size])
            for block_hash in confirmed_blocks:
                conf_duration = time.time() - start_time
                await self._publish_block_confirmation_event(
                    conf_duration, block_hash, True)
                unconfirmed_blocks.remove(block_hash)
            if unconfirmed_blocks:
                await asyncio.sleep(interval)

        if unconfirmed_blocks:
            # If there are any remaining unconfirmed blocks, raise an AssertionError and send the events.
            for block_hash in unconfirmed_blocks:
                await self._publish_block_confirmation_event(
                    wait_s, block_hash, False)
            raise AssertionError(
                f"{len(list(unconfirmed_blocks))} unconfirmed blocks! e.g. {list(unconfirmed_blocks)[0]}"
            )

    async def assert_single_block_confirmed(self, block_hash: str):
        await self.assert_blocks_confirmed([block_hash])

    async def assert_single_block_confirmed_wait(self, block_hash, wait_s,
                                                 interval):
        await self.assert_blocks_confirmed_wait([block_hash], wait_s, interval)