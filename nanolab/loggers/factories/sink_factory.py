#from nanolab.loggers.sinks.csv_sink import CSVSink
from nanolab.loggers.sinks.console_sink import ConsoleSink


class SinkFactory:

    @staticmethod
    def create_storage(storage_type):
        if storage_type == 'console':
            return ConsoleSink()
        elif storage_type == 'csv':
            pass
            #return CSVSink(*args, **kwargs)
        else:
            raise ValueError(f"Invalid storage_type: {storage_type}")