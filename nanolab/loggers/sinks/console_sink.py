from nanolab.loggers.contracts import ISink, LogData
import datetime
import time


class ConsoleSink(ISink):
    """A storage that writes logs to the console."""

    def store_logs(self, logs: LogData):
        """Store logs by printing them to the console."""
        node_name = logs.node_name
        node_version = logs.node_version
        timestamp = logs.timestamp
        elapsed_time = logs.elapsed_time
        check_count = logs.check_count
        cemented_count = logs.cemented_count
        bps = logs.bps
        cps = logs.cps
        percent_cemented = logs.percent_cemented
        percent_checked = logs.percent_checked

        print(
            f"{timestamp:<20} {elapsed_time:>4} sec | {node_name[:16]:<16} | {node_version:<10} | \
C: {cemented_count:>7}/{check_count:>7} @ {cps:>4} cps ({percent_cemented:>6.2f}%) | \
B: {bps:>4} bps ({percent_checked:>6.2f}%)")


# class ConsoleSink(ISink):

#     def __init__(self, node_name: str, node_version: str, count_start: int,
#                  cemented_start: int, count_total: int):
#         self.node_name = node_name
#         self.node_version = node_version
#         self.count_start = count_start
#         self.cemented_start = cemented_start
#         self.count_total = count_total

#     def store_logs(self, logs: dict):
#         elapsed_time = logs['elapsed_time']
#         check_count = logs['check_count']
#         cemented_count = logs['cemented_count']
#         previous_count = logs['previous_count']
#         previous_cemented = logs['previous_cemented']

#         bps = 0 if previous_count == 0 else check_count - previous_count
#         cps = 0 if previous_cemented == 0 else cemented_count - previous_cemented

#         print(
#             f"{elapsed_time:>4} seconds {self.node_name:>12} | {self.node_version} | \
# {cemented_count:>7}/{check_count:>7}/{self.count_total:>7} @{bps:>5} bps \
# (avg: {round((check_count - self.count_start)/max(1, elapsed_time),2)}) | \
# @{cps:>5} cps (avg: {round((cemented_count - self.cemented_start)/max(1, elapsed_time),2)})"
#         )