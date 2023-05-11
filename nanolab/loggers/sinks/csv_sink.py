from nanolab.loggers.contracts import ISink, LogData
import csv


class CSVSink(ISink):
    """A storage that writes logs to a CSV file."""

    def __init__(self, csv_file: str):
        self.csv_file = csv_file
        self.writer = csv.writer(open(self.csv_file, 'w', newline=''))
        self.writer.writerow([
            "timestamp", "elapsed_time", "check_count", "cemented_count",
            "bps", "cps", "percent_cemented", "percent_checked"
        ])

    def store_logs(self, logs: LogData):
        """Store logs by writing them to the CSV file."""
        data = [
            logs.timestamp, logs.elapsed_time, logs.check_count,
            logs.cemented_count, logs.bps, logs.cps, logs.percent_cemented,
            logs.percent_checked
        ]

        try:
            self.writer.writerow(data)
        except Exception as e:
            print(f"Failed to write to CSV file: {e}")