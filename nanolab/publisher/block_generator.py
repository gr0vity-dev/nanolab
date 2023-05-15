#from nanolab.src.nano_rpc_v2 import NanoRpcV2
from nanomock.modules.nl_rpc import NanoRpc, NanoLibTools
from nanolab.src.utils import get_config_parser
from abc import ABC, abstractmethod


class IBlockGenerator(ABC):

    @abstractmethod
    def __init__(self, node_name=None):
        pass

    @abstractmethod
    def get_random_account(self):
        pass

    @abstractmethod
    def blockgen_single_change(self,
                               source_seed=None,
                               source_index=None,
                               source_private_key=None,
                               rep=None):
        pass

    @abstractmethod
    def set_broadcast_blocks(self, broadcast):
        pass


class BlockGenerator(IBlockGenerator):

    def __init__(self, node_name=None):
        conf_p = get_config_parser()
        node_name = node_name if node_name else conf_p.get_nodes_name()[:-1]
        self.nano_rpc_default = NanoRpc(conf_p.get_node_rpc(node_name))
        self.broadcast = False
        self.single_account_open_counter = 0

    def get_random_account(self):
        random_seed = self.nano_rpc_default.generate_seed()
        random_account = NanoLibTools().nanolib_account_data(seed=random_seed)
        return random_account["account"]

    def blockgen_single_change(self,
                               source_seed=None,
                               source_index=None,
                               source_private_key=None,
                               rep=None):
        rep = rep if rep else self.get_random_account()
        if source_private_key:
            res = self.nano_rpc_default.create_change_block_pkey(
                source_private_key, rep, broadcast=self.broadcast)
            return res

        if source_seed and source_index >= 0:
            return self.nano_rpc_default.create_change_block(
                source_seed, source_index, rep, broadcast=self.broadcast)

        raise ValueError(
            "Either source_private_key or source_seed and source_index must not be None"
        )

    def set_broadcast_blocks(self, broadcast):
        self.broadcast = broadcast
