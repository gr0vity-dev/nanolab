import socket
import time
from typing import Optional, Union, List
import ipaddress
import logging
import binascii
from hashlib import blake2b
import ed25519_blake2b
import json
import requests
from nanolab.xnomin.acctools import to_account_addr, account_key


def get_peers_from_service(ctx: dict, url=None):
    if url is None:
        url = ctx['peerserviceurl']
    if url == '':
        json_resp = ctx['peers']
    else:
        session = requests.Session()
        resp = session.get(url, timeout=15)
        json_resp = resp.json()
    return [Peer.from_json(r) for r in json_resp.values()]


def get_connected_socket_endpoint(addr: str,
                                  port: int,
                                  bind_endpoint: tuple = None
                                  ) -> socket.socket:
    s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
    s.settimeout(3)
    if bind_endpoint:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(bind_endpoint)
    s.connect((addr, port))
    return s


DEFAULT_LOGGER_NAME = ""  # an empty string will use the root logger


def get_logger(logger_name: str = DEFAULT_LOGGER_NAME) -> logging.Logger:
    logger = logging.getLogger(logger_name)
    if not logger.hasHandlers():
        logger.addHandler(logging.NullHandler())

    return logger


logger = get_logger()


def hexlify(data) -> str:
    if data is None: return 'None'
    return binascii.hexlify(data).decode("utf-8").upper()


class block_type_enum:
    invalid = 0
    not_a_block = 1
    send = 2
    receive = 3
    open = 4
    change = 5
    state = 6


class message_type_enum:
    invalid = 0x0
    not_a_block = 0x1
    keepalive = 0x2
    publish = 0x3
    confirm_req = 0x4
    confirm_ack = 0x5
    bulk_pull = 0x6
    bulk_push = 0x7
    frontier_req = 0x8
    # deleted 0x9
    node_id_handshake = 0x0a
    bulk_pull_account = 0x0b
    telemetry_req = 0x0c
    telemetry_ack = 0x0d


def message_type_enum_to_str(msg_type: int):
    return next(name for name, value in vars(message_type_enum).items()
                if value == msg_type)


def block_length_by_type(blktype: int) -> int:
    lengths = {2: 152, 3: 136, 4: 168, 5: 136, 6: 216}
    return lengths[blktype]


def node_id_handshake_size(is_query: bool, is_response: bool) -> int:
    size = 0
    if is_query:
        size += 32
    if is_response:
        size += 32 + 64
    return size


class network_id:

    def __init__(self, rawbyte: int):
        self.parse_header(int(rawbyte))

    def parse_header(self, rawbyte: bytes) -> None:
        if not (rawbyte in [ord('X'), ord('B'), ord('C'), ord('L')]):
            raise ValueError("ParseErrorBadNetworkId")
        self.id = rawbyte

    def __str__(self):
        return chr(self.id)

    def __eq__(self, other):
        if not isinstance(other, network_id):
            return False
        elif self.id != other.id:
            return False
        return True


class message_type:

    def __init__(self, num: int) -> None:
        if not (num in range(0, 14)):
            raise ValueError("ParseErrorBadMessageType")
        self.type = num

    def __str__(self):
        return '%s(%s)' % (str(self.type), message_type_enum_to_str(self.type))

    def __eq__(self, other):
        if not isinstance(other, message_type):
            return False
        return self.type == other.type


class message_header:

    def __init__(self, net_id: network_id, versions: List[int],
                 msg_type: message_type, ext: int):
        self.ext = ext
        self.net_id = net_id
        self.ver_max = versions[0]
        self.ver_using = versions[1]
        self.ver_min = versions[2]
        self.msg_type = msg_type
        assert isinstance(self.msg_type, message_type)

    def serialise_header(self) -> bytes:
        header = b""
        header += ord('R').to_bytes(1, "big")
        header += ord(str(self.net_id)).to_bytes(1, "big")
        header += self.ver_max.to_bytes(1, "big")
        header += self.ver_using.to_bytes(1, "big")
        header += self.ver_min.to_bytes(1, "big")
        header += self.msg_type.type.to_bytes(1, "big")
        header += self.ext.to_bytes(2, "little")
        return header

    def is_query(self) -> bool:
        return self.ext & 1

    def is_response(self) -> bool:
        return self.ext & 2

    def set_is_query(self, bool: bool) -> None:
        QUERY_MASK = 0x0001
        self.ext = self.ext & 0xfffe
        if bool:
            self.ext = self.ext | QUERY_MASK

    def set_is_response(self, bool: bool) -> None:
        RESPONSE_MASK = 0x0002
        self.ext = self.ext & 0xfffd
        if bool:
            self.ext = self.ext | RESPONSE_MASK

    def count_get(self) -> int:
        COUNT_MASK = 0xf000
        return (self.ext & COUNT_MASK) >> 12

    def block_type(self) -> int:
        BLOCK_TYPE_MASK = 0x0f00
        return (self.ext & BLOCK_TYPE_MASK) >> 8

    def set_block_type(self, block_type: int) -> None:
        assert (isinstance(block_type, int))
        block_type = block_type << 8
        self.ext = self.ext & 0xf0ff
        self.ext = self.ext | block_type

    def set_item_count(self, count: int) -> None:
        assert (isinstance(count, int))
        count = count << 12
        self.ext = self.ext & 0x0fff
        self.ext = self.ext | count

    @classmethod
    def parse_header(cls, data: bytes):
        assert (len(data) == 8)
        if data[0] != ord('R'):
            raise ValueError("ParseErrorBadMagicNumber")
        net_id = network_id(data[1])
        versions = [data[2], data[3], data[4]]
        msg_type = message_type(data[5])
        ext = int.from_bytes(data[6:], "little")
        return message_header(net_id, versions, msg_type, ext)

    def telemetry_ack_size(self) -> int:
        telemetry_size_mask = 0x3ff
        return self.ext & telemetry_size_mask

    @classmethod
    def from_json(self, json_hdr: dict):
        return message_header(
            network_id(json_hdr['net_id']),
            [json_hdr['ver_max'], json_hdr['ver_using'], json_hdr["ver_min"]],
            message_type(json_hdr['msg_type']), json_hdr['ext'])

    def payload_length_bytes(self) -> Optional[int]:
        if self.msg_type == message_type(message_type_enum.bulk_pull):
            return None

        if self.msg_type == message_type(message_type_enum.bulk_push):
            return 0

        elif self.msg_type == message_type(message_type_enum.telemetry_req):
            return 0

        elif self.msg_type == message_type(message_type_enum.frontier_req):
            return 32 + 4 + 4

        elif self.msg_type == message_type(
                message_type_enum.bulk_pull_account):
            return 32 + 16 + 1

        elif self.msg_type == message_type(message_type_enum.keepalive):
            return 8 * (16 + 2)

        elif self.msg_type == message_type(message_type_enum.publish):
            return block_length_by_type(self.block_type())

        # elif self.msg_type == message_type(message_type_enum.confirm_ack):
        #     return confirm_ack_size(self.block_type(), self.count_get())

        # elif self.msg_type == message_type(message_type_enum.confirm_req):
        #     return confirm_req_size(self.block_type(), self.count_get())

        elif self.msg_type == message_type(
                message_type_enum.node_id_handshake):
            return node_id_handshake_size(self.is_query(), self.is_response())

        elif self.msg_type == message_type(message_type_enum.telemetry_ack):
            return self.telemetry_ack_size()

        else:
            logger.debug(f"Unknown message type: {self.msg_type}")
            return None

    def __eq__(self, other):
        if str(self) == str(other):
            return True

    def __str__(self):
        str = "NetID: %s, " % self.net_id
        str += "VerMaxUsingMin: %s/%s/%s, " % (self.ver_max, self.ver_using,
                                               self.ver_min)
        str += "MsgType: %s, " % self.msg_type
        str += "Extensions: %s" % hexlify(self.ext.to_bytes(2, "big"))
        return str


class block_state:

    def __init__(self, account: bytes, prev: bytes, rep: bytes, bal: int,
                 link: bytes, sig: bytes, work: int):
        assert (isinstance(work, int))
        self.account = account
        self.previous = prev
        self.representative = rep
        self.balance = bal
        self.link = link
        self.signature = sig
        self.work = work
        self.ancillary = {
            "next": None,
            "peers": set(),
            "type": block_type_enum.not_a_block
        }

    def get_previous(self) -> bytes:
        return self.previous

    def get_next(self) -> bytes:
        return self.ancillary['next']

    def get_account(self) -> bytes:
        return self.account

    def get_balance(self) -> int:
        return self.balance

    def get_type_int(self) -> int:
        return block_type_enum.state

    def root(self) -> bytes:
        if int.from_bytes(self.previous, "big") == 0:
            return self.account
        else:
            return self.previous

    def set_type(self, block_type: int) -> None:
        assert block_type in range(block_type_enum.invalid,
                                   block_type_enum.state + 1)
        self.ancillary["type"] = block_type

    def hash_string(self):
        return hexlify(self.hash())

    def hash(self) -> bytes:
        STATE_BLOCK_HEADER_BYTES = (b'\x00' * 31) + b'\x06'
        data = b"".join([
            STATE_BLOCK_HEADER_BYTES, self.account, self.previous,
            self.representative,
            self.balance.to_bytes(16, "big"), self.link
        ])
        return blake2b(data, digest_size=32).digest()

    def serialise(self, include_block_type: bool) -> bytes:
        data = b''
        if include_block_type:
            data += (6).to_bytes(1, "big")
        data += self.account
        data += self.previous
        data += self.representative
        data += self.balance.to_bytes(16, "big")
        data += self.link
        data += self.signature

        # Block states proof of work is received and sent in big endian
        data += self.work.to_bytes(8, "big")
        return data

    def is_epoch_v2_block(self) -> bool:
        if self.link[0:14] == b'epoch v2 block':
            return True
        return False

    def is_epoch_v1_block(self) -> bool:
        if self.link[0:14] == b'epoch v1 block':
            return True
        return False

    def sign(self, signing_key: ed25519_blake2b.keys.SigningKey) -> None:
        self.signature = signing_key.sign(self.hash())

    def generate_work(self, min_difficulty: int) -> None:
        root_int = int.from_bytes(self.root(), byteorder='big')
        self.work = pow.find_pow_for_root_and_difficulty(
            root_int, min_difficulty)

    @classmethod
    def parse(cls, data: bytes):
        assert (len(data) == block_length_by_type(6))
        account = data[0:32]
        prev = data[32:64]
        rep = data[64:96]
        bal = int.from_bytes(data[96:112], "big")
        link = data[112:144]
        sig = data[144:208]
        # Block states proof of work is received and sent in big endian
        work = int.from_bytes(data[208:], "big")
        return block_state(account, prev, rep, bal, link, sig, work)

    @classmethod
    def parse_from_json(cls, json_obj: dict):
        assert (json_obj['type'] == 'state')
        account = account_key(json_obj['account'])
        prev = binascii.unhexlify(json_obj['previous'])
        rep = account_key(json_obj['representative'])
        bal = int(json_obj['balance'])
        if len(json_obj['link']) == 64:
            link = binascii.unhexlify(json_obj['link'])
        else:
            link = account_key(json_obj['link'])
        sig = binascii.unhexlify(json_obj['signature'])
        work = int.from_bytes(binascii.unhexlify(json_obj['work']), "big")
        return block_state(account, prev, rep, bal, link, sig, work)

    def to_json(self) -> str:
        jsonblk = {
            'type': 'state',
            'account': to_account_addr(self.account),
            'previous': hexlify(self.previous),
            'representative': to_account_addr(self.representative),
            'balance': str(self.balance),
            'link': hexlify(self.link),
            'link_as_account': to_account_addr(self.link),
            'signature': hexlify(self.signature),
            'work': hexlify(self.work.to_bytes(8, "big"))
        }
        return json.dumps(jsonblk, indent=4)

    def link_to_string(self) -> str:
        if self.link.startswith(b'epoch'):
            return self.link.decode('ascii').replace('\x00', '')
        else:
            return hexlify(self.link)

    # def __str__(self):
    #     hexacc = binascii.hexlify(self.account).decode("utf-8").upper()
    #     string = "------------- Block State -------------\n"
    #     string += "Hash : %s\n" % hexlify(self.hash())
    #     string += "Acc  : %s\n" % hexacc
    #     string += "       %s\n" % to_account_addr(self.account)
    #     string += "Prev : %s\n" % hexlify(self.previous)
    #     string += "Repr : %s\n" % hexlify(self.representative)
    #     string += "       %s\n" % to_account_addr(self.representative)
    #     string += "Bal  : %s\n" % (self.balance / (10**30))
    #     string += "Link : %s\n" % self.link_to_string()
    #     string += "Sign : %s\n" % hexlify(self.signature)
    #     string += "Work : %s\n" % hexlify(self.work.to_bytes(8, "big"))
    #     string += "Next : %s\n" % hexlify(self.ancillary["next"])
    #     string += "Peers: %s" % self.ancillary['peers']
    #     return string

    # def __hash__(self):
    #     return hash((self.account, self.previous, self.representative,
    #                  self.balance, self.link))

    # def __eq__(self, other):
    #     if not isinstance(other, block_state):
    #         return False
    #     elif self.account != other.account:
    #         assert (self.hash() != other.hash())
    #         return False
    #     elif self.previous != other.previous:
    #         assert (self.hash() != other.hash())
    #         return False
    #     elif self.representative != other.representative:
    #         assert (self.hash() != other.hash())
    #         return False
    #     elif self.balance != other.balance:
    #         assert (self.hash() != other.hash())
    #         return False
    #     elif self.link != other.link:
    #         assert (self.hash() != other.hash())
    #         return False
    #     elif self.signature != other.signature:
    #         assert (self.hash() != other.hash())
    #         return False
    #     elif self.work != other.work:
    #         assert (self.hash() != other.hash())
    #         return False
    #     elif self.ancillary != other.ancillary:
    #         assert (self.hash() != other.hash())
    #         return False

    #     return True


class ip_addr:

    def __init__(
        self,
        ipv6: Union[str, ipaddress.IPv6Address] = ipaddress.IPv6Address(0)):
        if isinstance(ipv6, str):
            self.ipv6 = ipaddress.IPv6Address(ipv6)
        else:
            self.ipv6 = ipv6
        assert isinstance(self.ipv6, ipaddress.IPv6Address)

    @classmethod
    def from_string(cls, ipstr: str):
        assert isinstance(ipstr, str)
        a = ipaddress.ip_address(ipstr)
        if a.version == 4:
            ipstr = '::ffff:' + str(a)
        ipv6 = ipaddress.IPv6Address(ipstr)
        return ip_addr(ipv6)

    def serialise(self) -> bytes:
        return self.ipv6.packed

    def is_ipv4(self) -> bool:
        return self.ipv6.ipv4_mapped is not None

    def __str__(self):
        if self.ipv6.ipv4_mapped:
            return '::ffff:' + str(self.ipv6.ipv4_mapped)
        return str(self.ipv6)

    def __eq__(self, other):
        if not isinstance(other, ip_addr):
            return False
        return self.ipv6 == other.ipv6

    def __hash__(self):
        return hash(self.ipv6)


class Peer:

    def __init__(self,
                 ip: ip_addr = ip_addr(),
                 port: int = 0,
                 score: int = -1,
                 is_voting: bool = False,
                 last_seen: int = int(time.time()),
                 incoming: bool = False):
        assert isinstance(ip, ip_addr)
        self.ip = ip
        self.port = port
        self.peer_id = None
        self.is_voting = is_voting
        self.telemetry = None
        self.aux = {}
        self.last_seen = last_seen
        self.incoming = incoming

        # sideband info, not used for equality and hashing
        self.score = score

    def serialise(self) -> bytes:
        data = b""
        data += self.ip.serialise()
        data += self.port.to_bytes(2, "little")
        return data

    def deduct_score(self, score: int) -> None:
        self.score = max(0, self.score - score)

    def merge(self, peer: "Peer") -> None:
        assert self == peer

        self.last_seen = peer.last_seen

        if peer.telemetry is not None:
            self.telemetry = peer.telemetry
        if peer.incoming is False:
            self.port = peer.port
            self.incoming = False
        if peer.is_voting is True:
            self.is_voting = True

        logger.log(VERBOSE, f"Merged peer {peer}")

    @classmethod
    def parse_peer(cls, data: bytes):
        assert (len(data) == 18)
        ip = parse_ipv6(data[0:16])
        port = int.from_bytes(data[16:], "little")
        return Peer(ip_addr(ip), port)

    @classmethod
    def from_json(self, json_peer):
        from nanolab.xnomin.telemetry_req import telemetry_ack
        # Add 'incoming' argument when peer service code gets updated
        peer = Peer(ip_addr(json_peer['ip']), json_peer['port'],
                    json_peer['score'], json_peer['is_voting'])  #,
        #json_peer['last_seen'])
        if 'telemetry' in json_peer and json_peer['telemetry'] is not None:
            peer.telemetry = telemetry_ack.from_json(json_peer['telemetry'])
        if 'peer_id' in json_peer and json_peer['peer_id']:
            peer.peer_id = binascii.unhexlify(json_peer['peer_id'])
        return peer

    def __str__(self):
        sw_ver = ''
        if self.telemetry:
            sw_ver = ' v' + self.telemetry.get_sw_version()
        return '%s:%s (score:%s, is_voting: %s%s)' % (str(
            self.ip), self.port, self.score, self.is_voting, sw_ver)

    def __eq__(self, other):
        return (self.peer_id is not None
                and self.peer_id == other.peer_id) or (self.ip == other.ip and
                                                       self.port == other.port)

    def __hash__(self):
        return hash((self.ip, self.port))