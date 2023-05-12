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

    def end(self):
        pass