from nanolab.loggers.contracts import ISink, LogData
import datetime
import time


class ConsoleSink(ISink):
    """A storage that writes logs to the console."""
    percent_cemented = 0

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
        bps_avg = logs.bps_avg or 0
        cps_avg = logs.cps_avg or 0

        self.percent_cemented = percent_cemented

        print(
            f"{timestamp:<20} {elapsed_time:>4} sec | {node_name[:16]:<16} | {node_version:<10} | \
{cemented_count:>7}/{check_count:>7} @ CPS: {cps:>7} (avg {cps_avg:>7.2f}) ({percent_cemented:>6.2f}%) | \
BPS: {bps:>7} (avg {bps_avg:>7.2f}) ({percent_checked:>6.2f}%)")

    def end(self):
        print("PASS") if self.percent_cemented == 100 else print("FAIL")