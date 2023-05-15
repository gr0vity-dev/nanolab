from abc import ABC, abstractmethod
from nanolab.src.nano_rpc import NanoRpcV2
from nanolab.publisher.block_asserts import BlockAsserts
from nanolab.publisher.block_generator import BlockGenerator
from nanolab.publisher.confirmation_stats import ConfirmationStatsManager
from nanolab.src.utils import get_config_parser, print_dot
import time
from nanolab.publisher.event_bus import EventBus
from nanolab.publisher.block_event import BlockEvent


class ITestCase(ABC):

    @abstractmethod
    def __init__(self, config: dict):
        pass

    @abstractmethod
    async def run(self):
        pass


class TestCaseFactory:

    @staticmethod
    def create(config: dict) -> ITestCase:
        # The config should include a 'type' field that identifies the test case type.
        if config['type'] == 'block_generation':
            return BlockGenerationTestCase(config)
        # Add more elif branches here for other test case types.
        else:
            raise ValueError(f"Invalid test case type: {config['type']}")


class BlockGenerationTestCase(ITestCase):

    def __init__(self, config: dict):
        self.event_bus = EventBus()
        conf_p = get_config_parser()

        self.source_seed = config["source_seed"]
        self.start_index = config["source_start_index"]
        self.block_count = config["block_count"]
        self.is_independent = config.get("is_independent", True)
        self.timeout_s = config.get("timeout_s", 10)
        self.node_name = config.get("node_name", conf_p.get_nodes_name()[:-1])
        self.ba_l = BlockAsserts(self.node_name)
        self.bg_l = BlockGenerator(self.node_name)
        self.stats_manager = ConfirmationStatsManager(self.timeout_s)
        self.event_bus.subscribe('block_confirmed',
                                 self.stats_manager.on_block_confirmed)

    @print_dot
    async def _generate_and_confirm_block(self, index):
        self.bg_l.set_broadcast_blocks(True)
        representative = self.bg_l.get_random_account()
        try:
            start_time = time.time()
            res = self.bg_l.blockgen_single_change(
                source_seed=self.source_seed,
                source_index=index,
                rep=representative)
            await self.ba_l.assert_single_block_confirmed_wait(
                res["hash"], self.timeout_s, 0.05)
            event = BlockEvent(time.time() - start_time, False)
            await self.event_bus.publish('block_confirmed', event)
        except AssertionError as ex:
            print("DEBUG", ex)
            event = BlockEvent(self.timeout_s, True)
            await self.event_bus.publish(
                'block_confirmed',
                event)  # publish event in case of an AssertionError
        return

    async def run(self):
        await self.stats_manager.initialize(self.node_name)
        for counter in range(self.start_index,
                             self.start_index + self.block_count):
            seed_index = counter if self.is_independent else self.start_index
            await self._generate_and_confirm_block(seed_index)

        await self.stats_manager.print_stats()  # no longer pass conf_lst

        return self.block_count
