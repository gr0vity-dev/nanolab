from nanolab_debug.loggers.sinks.csv_sink import CSVSink
from nanolab_debug.loggers.sinks.sql_sink import SqlSink
from nanolab_debug.loggers.sinks.console_sink import ConsoleSink


class SinkFactory:

    @staticmethod
    def create_storage(sink_type, config_params_dict):
        if sink_type == 'console':
            return ConsoleSink(**config_params_dict)
        elif sink_type == 'sql':
            return SqlSink(**config_params_dict)
        elif sink_type == 'csv':
            return CSVSink(**config_params_dict)
        else:
            raise ValueError(f"Invalid storage_type: {sink_type}")
