import aiohttp
import asyncio

COMMANDS = {
    "account_balance": {
        "required": ["account"],
        "optional": []
    },
    "account_info": {
        "required": ["account"],
        "optional":
        ["representative", "weight", "receivable", "include_confirmed"]
    },
    "account_get": {
        "required": ["key"],
        "optional": []
    },
    "account_history": {
        "required": ["account", "count"],
        "optional": ["raw", "head", "offset", "reverse", "account_filter"]
    },
    "account_key": {
        "required": ["account"],
        "optional": []
    },
    "account_representative": {
        "required": ["account"],
        "optional": []
    },
    "account_weight": {
        "required": ["account"],
        "optional": []
    },
    "accounts_balances": {
        "required": ["accounts"],
        "optional": []
    },
    "accounts_frontiers": {
        "required": ["accounts"],
        "optional": []
    },
    "accounts_receivable": {
        "required": ["accounts", "count"],
        "optional": [
            "threshold", "source", "include_active", "sorting",
            "include_only_confirmed"
        ]
    },
    "accounts_representatives": {
        "required": ["accounts"],
        "optional": []
    },
    "available_supply": {
        "required": [],
        "optional": []
    },
    "block_account": {
        "required": ["hash"],
        "optional": []
    },
    "block_confirm": {
        "required": ["hash"],
        "optional": []
    },
    "block_count": {
        "required": [],
        "optional": ["include_cemented"]
    },
    "block_create": {
        "required":
        ["type", "balance", "key", "representative", "link", "previous"],
        "optional": ["work", "version", "difficulty", "json_block"]
    },
    "block_hash": {
        "required": ["block"],
        "optional": ["json_block"]
    },
    "block_info": {
        "required": ["hash"],
        "optional": ["json_block"]
    },
    "blocks": {
        "required": ["hashes"],
        "optional": ["json_block"]
    },
    "blocks_info": {
        "required": ["hashes"],
        "optional": [
            "json_block", "receivable", "source", "pending", "receive_hash",
            "include_not_found"
        ]
    },
    "bootstrap": {
        "required": ["address", "port"],
        "optional": ["bypass_frontier_confirmation", "id"]
    },
    "bootstrap_any": {
        "required": [],
        "optional": ["force", "id", "account"]
    },
    "bootstrap_lazy": {
        "required": ["hash"],
        "optional": ["force", "id"]
    },
    "bootstrap_status": {
        "required": [],
        "optional": []
    },
    "chain": {
        "required": ["block", "count"],
        "optional": ["offset", "reverse"]
    },
    "confirmation_active": {
        "required": [],
        "optional": ["announcements"]
    },
    "confirmation_height_currently_processing": {
        "required": [],
        "optional": []
    },
    "confirmation_history": {
        "required": [],
        "optional": ["hash"]
    },
    "confirmation_info": {
        "required": ["json_block", "root"],
        "optional": ["contents", "json_block", "representatives"]
    },
    "confirmation_quorum": {
        "required": [],
        "optional": ["peer_details"]
    },
    "database_txn_tracker": {
        "required": ["min_read_time", "min_write_time"],
        "optional": []
    },
    "delegators": {
        "required": ["account"],
        "optional": ["threshold", "count", "start"]
    },
    "delegators_count": {
        "required": ["account"],
        "optional": []
    },
    "deterministic_key": {
        "required": ["seed", "index"],
        "optional": []
    },
    "epoch_upgrade": {
        "required": ["epoch", "key"],
        "optional": ["count", "threads"]
    },
    "frontier_count": {
        "required": [],
        "optional": []
    },
    "frontiers": {
        "required": ["account", "count"],
        "optional": []
    },
    "keepalive": {
        "required": ["address", "port"],
        "optional": []
    },
    "key_create": {
        "required": [],
        "optional": []
    },
    "key_expand": {
        "required": ["key"],
        "optional": []
    },
    "ledger": {
        "required": ["account", "count"],
        "optional": [
            "representative", "weight", "receivable", "modified_since",
            "sorting", "threshold"
        ]
    },
    "node_id": {
        "required": [],
        "optional": []
    },
    "node_id_delete": {
        "required": [],
        "optional": []
    },
    "peers": {
        "required": [],
        "optional": ["peer_details"]
    },
    "populate_backlog": {
        "required": [],
        "optional": []
    },
    "process": {
        "required": ["json_block", "subtype", "block"],
        "optional": ["force", "subtype", "json_block", "watch_work", "async"]
    },
    "receivable": {
        "required": ["account", "count"],
        "optional": [
            "count", "threshold", "source", "include_active", "min_version",
            "sorting", "include_only_confirmed"
        ]
    },
    "receivable_exists": {
        "required": ["hash"],
        "optional": ["include_active", "include_only_confirmed"]
    },
    "representatives": {
        "required": [],
        "optional": ["count", "sorting"]
    },
    "representatives_online": {
        "required": [],
        "optional": ["weight", "accounts"]
    },
    "republish": {
        "required": ["hash"],
        "optional": ["sources", "destinations"]
    },
    "sign": {
        "required": ["json_block", "key", "block"],
        "requiredAlternative": ["hash"],
        "optional": []
    },
    "stats": {
        "required": ["type"],
        "optional": []
    },
    "stats_clear": {
        "required": [],
        "optional": []
    },
    "stop": {
        "required": [],
        "optional": []
    },
    "successors": {
        "required": ["block", "count"],
        "optional": ["offset", "reverse"]
    },
    "telemetry": {
        "required": [],
        "optional": []
    },
    "validate_account_number": {
        "required": ["account"],
        "optional": []
    },
    "version": {
        "required": [],
        "optional": []
    },
    "unchecked": {
        "required": ["json_block", "count"],
        "optional": []
    },
    "unchecked_clear": {
        "required": [],
        "optional": []
    },
    "unchecked_get": {
        "required": ["json_block", "hash"],
        "optional": []
    },
    "unchecked_keys": {
        "required": ["json_block", "key", "count"],
        "optional": []
    },
    "unopened": {
        "required": ["account", "count"],
        "optional": ["threshold"]
    },
    "uptime": {
        "required": [],
        "optional": []
    },
    "work_cancel": {
        "required": ["hash"],
        "optional": []
    },
    "work_generate": {
        "required": ["hash"],
        "optional": [
            "use_peers", "difficulty", "multiplier", "account", "version",
            "block", "json_block"
        ]
    },
    "work_peer_add": {
        "required": ["address", "port"],
        "optional": []
    },
    "work_peers": {
        "required": [],
        "optional": []
    },
    "work_peers_clear": {
        "required": [],
        "optional": []
    },
    "work_validate": {
        "required": ["work", "hash"],
        "optional": ["difficulty", "multiplier", "version"]
    },
    "account_create": {
        "required": ["wallet"],
        "optional": ["index", "work"]
    },
    "account_list": {
        "required": ["wallet"],
        "optional": []
    },
    "account_move": {
        "required": ["wallet", "source", "accounts"],
        "optional": []
    },
    "account_remove": {
        "required": ["wallet", "account"],
        "optional": []
    },
    "account_representative_set": {
        "required": ["wallet", "account", "representative"],
        "optional": ["work"]
    },
    "accounts_create": {
        "required": ["wallet", "count"],
        "optional": ["work"]
    },
    "password_change": {
        "required": ["wallet", "password"],
        "optional": []
    },
    "password_enter": {
        "required": ["wallet", "password"],
        "optional": []
    },
    "password_valid": {
        "required": ["wallet"],
        "optional": []
    },
    "receive": {
        "required": ["wallet", "account", "block"],
        "optional": []
    },
    "receive_minimum": {
        "required": [],
        "optional": []
    },
    "receive_minimum_set": {
        "required": ["amount"],
        "optional": []
    },
    "search_receivable": {
        "required": ["wallet"],
        "optional": []
    },
    "search_receivable_all": {
        "required": [],
        "optional": []
    },
    "send": {
        "required":
        ["action", "wallet", "source", "destination", "amount", "id"],
        "optional": ["work"]
    },
    "wallet_add": {
        "required": ["wallet", "key"],
        "optional": ["work"]
    },
    "wallet_add_watch": {
        "required": ["wallet", "accounts"],
        "optional": []
    },
    "wallet_balances": {
        "required": ["wallet"],
        "optional": ["threshold"]
    },
    "wallet_change_seed": {
        "required": ["wallet", "seed"],
        "optional": ["count"]
    },
    "wallet_contains": {
        "required": ["wallet", "account"],
        "optional": []
    },
    "wallet_create": {
        "required": [],
        "optional": []
    },
    "wallet_destroy": {
        "required": ["wallet"],
        "optional": []
    },
    "wallet_export": {
        "required": ["wallet"],
        "optional": []
    },
    "wallet_frontiers": {
        "required": ["wallet"],
        "optional": []
    },
    "wallet_history": {
        "required": ["wallet"],
        "optional": ["modified_since"]
    },
    "wallet_info": {
        "required": ["wallet"],
        "optional": []
    },
    "wallet_ledger": {
        "required": ["wallet"],
        "optional": ["representative", "weight", "pending"]
    },
    "wallet_lock": {
        "required": ["wallet"],
        "optional": []
    },
    "wallet_pending": {
        "required": ["wallet"],
        "optional": ["count", "threshold", "source"]
    },
    "wallet_representative": {
        "required": ["wallet"],
        "optional": []
    },
    "wallet_representative_set": {
        "required": ["wallet", "representative"],
        "optional": ["work"]
    },
    "wallet_republish": {
        "required": ["wallet"],
        "optional": ["count"]
    },
    "wallet_work_get": {
        "required": ["wallet"],
        "optional": []
    },
    "work_get": {
        "required": ["wallet"],
        "optional": []
    },
    "work_set": {
        "required": ["wallet", "account", "work"],
        "optional": []
    },
    "nano_to_raw": {
        "required": ["amount"],
        "optional": []
    },
    "raw_to_nano": {
        "required": ["amount"],
        "optional": []
    },
    "active_difficulty": {
        "required": [],
        "optional": ["include_trend"]
    }
}


def generate_method(command, required, optional):

    async def method(self, *args, **kwargs):
        payload = {"action": command}
        for arg, value in zip(required, args):
            payload[arg] = value
        for arg in optional:
            if arg in kwargs:
                payload[arg] = kwargs[arg]
        return await self.process_payloads([payload])

    # Set the name and the docstring of the new function
    method.__name__ = command
    method.__doc__ = f"Execute the {command} command."

    return method


class NanoRpcV2:

    def __init__(self, url, username=None, password=None):
        self.url = url
        self.username = username
        self.password = password
        self.auth = aiohttp.BasicAuth(
            username, password) if username and password else None
        self.session: aiohttp.ClientSession = None

    def create_session(self):
        self.session = aiohttp.ClientSession()

    async def close_session(self):
        await self.session.close()

    async def process_payloads(self, payloads):
        async with aiohttp.ClientSession(auth=self.auth) as session:
            async with session.post(self.url, json=payloads[0]) as response:
                return await response.json()


# Generate the methods
for command, params in COMMANDS.items():
    method = generate_method(command, params["required"], params["optional"])
    setattr(NanoRpcV2, method.__name__, method)