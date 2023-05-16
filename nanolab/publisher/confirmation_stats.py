from nanolab.src.nano_rpc import NanoRpcV2
from nanolab.src.utils import get_config_parser
from time import strftime, gmtime, time
from math import ceil


class ConfirmationStatsManager:

    def __init__(self, block_timeout_s):
        self.calculator = ConfirmationCalculator(block_timeout_s)
        self.printer = ConfirmationStatsPrinter()
        self.formatter = ConfirmationTableFormatter()

    async def initialize(self, node_name):
        self.rpc_v2 = NanoRpcV2(get_config_parser().get_node_rpc(node_name))
        self.rpc_v2.create_session()
        start_block_count = await self.rpc_v2.block_count()
        self.calculator.set_start_block_count(start_block_count)

    def set_end_block_count(self, end_block_count: dict) -> None:
        self.calculator.set_end_block_count(end_block_count)

    async def print_stats(self) -> None:
        end_block_count = await self.rpc_v2.block_count()
        self.calculator.set_end_block_count(end_block_count)
        stats = self.calculator.compute_stats()
        self.printer.print_stats(stats, self.formatter)

    async def on_block_confirmed(self, event):
        # Do something with the event, for example, append it to a list
        self.calculator.add_event(event)


class ConfirmationCalculator:

    def __init__(self, block_timeout_s):
        self.block_timeout_s = block_timeout_s
        self.start_time = time()
        self.events = []  # Add this list to keep track of events

    def _percentile(self, data, percentile):
        n = len(data)
        p = n * percentile / 100
        if p.is_integer():
            return sorted(data)[int(p)]
        else:
            return sorted(data)[int(ceil(p)) - 1]

    def add_event(self, event):
        # You might want to change the structure of the data in the list
        self.events.append({
            "conf_duration": event.conf_duration,
            "timeout": not event.confirmed
        })

    def set_start_block_count(self, start_block_count):
        self.start_block_count = start_block_count

    def set_end_block_count(self, end_block_count):
        self.end_block_count = end_block_count

    def compute_stats(self):
        self.new_blocks = int(self.end_block_count.get("count", 0)) - int(
            self.start_block_count.get("count", 0))
        self.new_cemented = int(self.end_block_count.get("cemented", 0)) - int(
            self.start_block_count.get("cemented", 0))
        self.confirmations = [
            e["conf_duration"] for e in self.events if e["timeout"] == False
        ]
        self.timeouts = [e for e in self.events if e["timeout"]]
        self.conf_duration = time() - self.start_time

        gather_int = {
            "confs":
            len(self.confirmations),
            "timeouts":
            len(self.timeouts),
            "bps":
            self.new_blocks / self.conf_duration,
            "cps":
            self.new_cemented / self.conf_duration,
            "min_conf_s":
            min(self.confirmations) if len(self.confirmations) > 0 else -1,
            "max_conf_s":
            max(self.confirmations) if len(self.confirmations) > 0 else -1,
            "perc_50_s":
            self._percentile(self.confirmations, 50)
            if len(self.confirmations) > 0 else -1,
            "perc_75_s":
            self._percentile(self.confirmations, 75)
            if len(self.confirmations) > 0 else -1,
            "perc_90_s":
            self._percentile(self.confirmations, 90)
            if len(self.confirmations) > 0 else -1,
            "perc_99_s":
            self._percentile(self.confirmations, 99)
            if len(self.confirmations) > 0 else -1,
            "block_timeout_s":
            self.block_timeout_s,
            "total_s":
            self.conf_duration,
            "new_blocks":
            self.new_blocks,
            "new_cemented":
            self.new_cemented,
        }
        return gather_int


class ConfirmationTableFormatter:

    def format_table(self, table, print_header=True):
        col_width = [max(len(str(x)) for x in col) for col in zip(*table)]
        formatted_table = []
        for line in table:
            if not print_header:
                print_header = True
                continue
            formatted_table.append(" | ".join("{:{}}".format(x, col_width[i])
                                              for i, x in enumerate(line)) +
                                   " |")
        return formatted_table


class ConfirmationStatsPrinter:

    def print_stats(self, stats, formatter):
        table_pr1 = (stats.keys(),
                     [str(round(stats[x], 2)).ljust(8) for x in stats])
        formatted_table = formatter.format_table(table_pr1, print_header=True)
        print("\n")
        for line in formatted_table:
            print(f'{strftime("%H:%M:%S", gmtime())} {line}')
