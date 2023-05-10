#!/bin/env python3

import binascii

from nanolab.xnomin.peers import message_header, message_type, message_type_enum


class telemetry_req:

    def __init__(self, ctx: dict):
        self.header = message_header(
            ctx['net_id'], [18, 18, 18],
            message_type(message_type_enum.telemetry_req), 0)

    def serialise(self) -> bytes:
        return self.header.serialise_header()


class telemetry_ack:

    def __init__(self, hdr: message_header, signature: bytes, node_id: bytes,
                 block_count: int, cemented_count: int, unchecked_count: int,
                 account_count: int, bandwidth_cap: int, peer_count: int,
                 protocol_ver: int, uptime: int, genesis_hash: bytes,
                 major_ver: int, minor_ver: int, patch_ver: int,
                 pre_release_ver: int, maker_ver: int, timestamp: int,
                 active_difficulty: int):
        self.hdr = hdr
        self.sig_verified = False
        self.sig = signature
        self.node_id = node_id
        self.block_count = block_count
        self.cemented_count = cemented_count
        self.unchecked_count = unchecked_count
        self.account_count = account_count
        self.bandwidth_cap = bandwidth_cap
        self.peer_count = peer_count
        self.protocol_ver = protocol_ver
        self.uptime = uptime
        self.genesis_hash = genesis_hash
        self.major_ver = major_ver
        self.minor_ver = minor_ver
        self.patch_ver = patch_ver
        self.pre_release_ver = pre_release_ver
        self.maker_ver = maker_ver
        self.timestamp = timestamp
        self.active_difficulty = active_difficulty

    @classmethod
    def from_json(self, json_tel: dict):
        return telemetry_ack(
            message_header.from_json(json_tel['hdr']),
            binascii.unhexlify(json_tel['sig']),
            binascii.unhexlify(json_tel['node_id']), json_tel['block_count'],
            json_tel['cemented_count'], json_tel['unchecked_count'],
            json_tel['account_count'], json_tel['bandwidth_cap'],
            json_tel['peer_count'], json_tel['protocol_ver'],
            json_tel['uptime'], binascii.unhexlify(json_tel['genesis_hash']),
            json_tel['major_ver'], json_tel['minor_ver'],
            json_tel['patch_ver'], json_tel['pre_release_ver'],
            json_tel['maker_ver'], json_tel['timestamp'],
            json_tel['active_difficulty'])