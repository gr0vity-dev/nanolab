from .base_sink import AbstractStorage


class ConsoleSink(AbstractStorage):

    def __init__(self, node_name: str, node_version: str, count_start: int,
                 cemented_start: int, count_total: int):
        self.node_name = node_name
        self.node_version = node_version
        self.count_start = count_start
        self.cemented_start = cemented_start
        self.count_total = count_total

    def store_logs(self, logs: dict):
        elapsed_time = logs['elapsed_time']
        check_count = logs['check_count']
        cemented_count = logs['cemented_count']
        previous_count = logs['previous_count']
        previous_cemented = logs['previous_cemented']

        bps = 0 if previous_count == 0 else check_count - previous_count
        cps = 0 if previous_cemented == 0 else cemented_count - previous_cemented

        print(
            f"{elapsed_time:>4} seconds {self.node_name:>12} | {self.node_version} | \
{cemented_count:>7}/{check_count:>7}/{self.count_total:>7} @{bps:>5} bps \
(avg: {round((check_count - self.count_start)/max(1, elapsed_time),2)}) | \
@{cps:>5} cps (avg: {round((cemented_count - self.cemented_start)/max(1, elapsed_time),2)})"
        )