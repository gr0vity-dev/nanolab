from nanolab.xnomin.peers import get_connected_socket_endpoint, message_header, block_state, block_type_enum, message_type_enum, network_id, message_type, get_peers_from_service
from nanolab.xnomin.handshake import node_handshake_id
from nanomock.modules.nl_parse_config import ConfigReadWrite
from nanolab.src.utils import get_config_parser
from typing import Any, Dict, List
import asyncio
import random
import time
import itertools

from nanolab.loggers.logger_manager import LoggingManager


async def start_loggers(logger_params: Dict, sink_params: List[Dict]):
    logger_manager = LoggingManager(logger_params, sink_params)
    await logger_manager.start_logging()


async def xnolib_publish(params: dict):

    block_lists = get_blocks_from_disk(params)
    sp = SocketPublish(params)
    messages, _ = sp.flatten_messages(block_lists)
    sp_task = asyncio.create_task(sp.run(messages))
    await asyncio.gather(sp_task)


def read_blocks_from_disk(path, seeds=False, hashes=False, blocks=False):
    res = ConfigReadWrite().read_json(path)
    if seeds: return res["s"]
    if hashes: return res["h"]
    if blocks: return res["b"]
    return res


def set_default_params(params: dict, all_blocks: dict):
    params.setdefault("start_round", 0)
    params.setdefault("end_round", len(all_blocks["h"]))
    params.setdefault("subset", {})
    params["subset"].setdefault("start_index", 0)
    params["subset"].setdefault(
        "end_index", max(len(inner_list) for inner_list in all_blocks["h"]))

    return params


def get_block_subset(all_blocks: dict, start_round: int, end_round: int,
                     start_index: int, end_index: int):
    blocks = {}
    blocks['b'] = [
        x[start_index:end_index]
        for x in all_blocks['b'][start_round:end_round]
    ]
    blocks['h'] = [
        x[start_index:end_index]
        for x in all_blocks['h'][start_round:end_round]
    ]
    return blocks


def get_blocks_from_disk(params: dict):
    # mandatory params: blocks_path
    # optional params: start_round, end_round, subset
    blocks_path = params["blocks_path"]
    all_blocks = read_blocks_from_disk(blocks_path)

    params = set_default_params(params, all_blocks)
    subset_start_index = params["subset"]["start_index"]
    subset_end_index = params["subset"]["end_index"]

    blocks = get_block_subset(all_blocks, params["start_round"],
                              params["end_round"], subset_start_index,
                              subset_end_index)

    return blocks


class SocketPublish:

    def __init__(self, params: Dict[str, Any]):
        self.bps = params["bps"]
        self.peers = params.get("peers")
        self.split = params.get("split", False)
        # skips 1st socket (genesis)
        self.split_skip = params.get("split_skip", False)
        self.reverse = params.get("reverse", False)
        self.shuffle = params.get("shuffle", False)
        self.sockets, self.hdr = self.__set_sockets_handshake()

    def handshake_peer(self, peeraddr, peerport, ctx):
        try:
            print('Connecting to [%s]:%s' % (peeraddr, peerport))
            s = get_connected_socket_endpoint(peeraddr, peerport)
            signing_key, verifying_key = node_handshake_id.keypair()
            node_handshake_id.perform_handshake_exchange(
                ctx, s, signing_key, verifying_key)
            return s
        except Exception as e:
            print(str(e))
            pass

    class msg_publish:

        def __init__(self, hdr, block):
            assert (isinstance(hdr, message_header))
            self.hdr = hdr
            self.block = block

        def serialise(self):
            data = self.hdr.serialise_header()
            data += self.block.serialise(False)
            return data

        def __str__(self):
            return str(self.hdr) + "\n" + str(self.block)

    def get_xnolib_context(self, peers=None):
        ctx = get_config_parser().get_xnolib_localctx()
        ctx["net_id"] = network_id(ord('X'))

        if peers is not None:  # chose a single peer , if enabled in config file
            for peer in ctx["peers"].copy():
                if peer not in peers:
                    ctx["peers"].pop(peer, None)
        return ctx

    def __set_sockets_handshake(self):
        ctx = self.get_xnolib_context(peers=self.peers)
        msgtype = message_type_enum.publish
        hdr = message_header(ctx['net_id'], [18, 18, 18],
                             message_type(msgtype), 0)
        hdr.set_block_type(block_type_enum.state)
        all_peers = get_peers_from_service(ctx)
        sockets = []
        # Handshake with all peers
        for peer in all_peers:
            s = self.handshake_peer(str(peer.ip), peer.port, ctx)
            if s is not None:
                sockets.append({
                    "socket": s,
                    "peer": str(peer.ip) + ":" + str(peer.port)
                })
        return sockets, hdr

    def flatten_messages(self,
                         block_lists: List[List[Dict[str, Any]]]) -> List[Any]:
        messages = []
        for block_list in block_lists['b']:
            publish_msg = [
                self.msg_publish(self.hdr, block_state.parse_from_json(block))
                for block in block_list
            ]
            messages.extend(publish_msg)

        block_hashes = list(itertools.chain(*block_lists['h']))

        return messages, block_hashes

    async def publish_message(self, socket: Dict[str, Any],
                              messages: List[Any]) -> None:
        start_time = time.time()
        sent_messages = 0
        for idx, message in enumerate(messages):
            try:
                socket['socket'].sendall(message.serialise())
                sent_messages += 1
                if sent_messages % self.bps == 0:
                    end_time = time.time()
                    elapsed_time = end_time - start_time
                    remaining_time = max(1 - elapsed_time, 0)
                    await asyncio.sleep(remaining_time)
                    start_time = time.time()
            except Exception as e:
                print(
                    f"Error sending message {idx+1} to {socket['peer']}: {str(e)}"
                )

    def create_publish_tasks(self, sockets: List[Dict[str, Any]],
                             messages: List[Any]) -> List[asyncio.Task]:
        if self.split:
            tasks = self.create_split_tasks(sockets, messages)
        elif self.split_skip:
            tasks = self.create_split_tasks(sockets,
                                            messages,
                                            skip_first_socket=True)
        elif self.shuffle:
            tasks = self.create_shuffle_tasks(sockets, messages)
        elif self.reverse:
            tasks = self.create_reverse_tasks(sockets, messages)
        else:
            tasks = self.create_default_tasks(sockets, messages)
        return tasks

    def create_split_tasks(self, sockets, messages, skip_first_socket=False):
        num_sockets = len(sockets) - 1 if skip_first_socket else len(sockets)
        messages_per_socket, remainder = divmod(len(messages), num_sockets)
        tasks = []
        sockets_to_use = sockets[1:] if skip_first_socket else sockets
        for i, socket in enumerate(sockets_to_use,
                                   start=int(skip_first_socket)):
            start = i * messages_per_socket + min(i, remainder)
            end = start + messages_per_socket + (1 if i < remainder else 0)
            tasks.append(self.publish_message(socket, messages[start:end]))
        return tasks

    def create_shuffle_tasks(self, sockets, messages):
        tasks = [
            self.publish_message(socket, random.sample(messages,
                                                       len(messages)))
            for socket in sockets
        ]
        return tasks

    def create_reverse_tasks(self, sockets, messages):
        messages.reverse()
        tasks = self.create_default_tasks(sockets, messages)
        return tasks

    def create_default_tasks(self, sockets, messages):
        tasks = [self.publish_message(socket, messages) for socket in sockets]
        return tasks

    async def run(self, messages: List[Any]) -> int:
        tasks = self.create_publish_tasks(self.sockets, messages)
        await asyncio.gather(*tasks)
        # make sure the last few blocks are published.
        #ideally this would check if all messages are received
        await asyncio.sleep(15)

        message_count = len(messages)
        return message_count
