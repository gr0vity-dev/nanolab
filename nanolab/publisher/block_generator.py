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
        self.nano_lib = NanoLibTools()

    def get_random_account(self):
        random_seed = self.nano_rpc_default.generate_seed()
        random_account = self.nano_lib.nanolib_account_data(seed=random_seed)
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

    def create_send_and_open_block(self, send_amount_raw, source_seed,
                                   source_index, destination_seed,
                                   destination_index, representative):
        #destination = self.nano_rpc_default.generate_account(destination_seed, destination_index)
        return self.blockgen_single_account_opener(
            representative=representative,
            source_seed=source_seed,
            source_index=source_index,
            destination_seed=destination_seed,
            destination_index=destination_index,
            send_amount=send_amount_raw)

    def blockgen_single_account_opener(
            self,
            representative=None,
            source_key=None,  #
            source_seed=None,
            source_index=None,
            destination_key=None,  #
            destination_seed=None,
            destination_index=None,
            send_amount=1,
            number_of_accounts=1000,
            accounts_keep_track=False,
            increment_index=False):
        if accounts_keep_track:
            if self.single_account_open_counter >= number_of_accounts:
                return []
            if increment_index:
                destination_index = self.single_account_open_counter
        self.single_account_open_counter = self.single_account_open_counter + 1

        destination = self.nano_lib.nanolib_account_data(
            private_key=destination_key,
            seed=destination_seed,
            index=destination_index)
        source = self.nano_lib.nanolib_account_data(private_key=source_key,
                                                    seed=source_seed,
                                                    index=source_index)

        send_block = self.nano_rpc_default.create_send_block_pkey(
            source["private"],
            destination["account"],
            send_amount,
            broadcast=self.broadcast)

        open_block = self.nano_rpc_default.create_open_block(
            destination["account"],
            destination["private"],
            send_amount,
            representative,
            send_block["hash"],
            broadcast=self.broadcast)
        open_block["account_data"]["source_seed"] = destination_seed
        open_block["account_data"]["source_index"] = destination_index

        res = [send_block, open_block]
        return res