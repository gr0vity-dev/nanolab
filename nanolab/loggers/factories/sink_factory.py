#from nanolab.loggers.sinks.csv_sink import CSVSink
from nanolab.loggers.sinks.console_sink import ConsoleSink


class StorageFactory:

    @staticmethod
    def create_storage(storage_type, *args, **kwargs):
        if storage_type == 'console':
            return ConsoleSink(*args, **kwargs)
        elif storage_type == 'csv':
            pass
            #return CSVStorage(*args, **kwargs)
        else:
            raise ValueError(f"Invalid storage_type: {storage_type}")