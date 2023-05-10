from abc import ABC, abstractmethod
from .mixins.bash_command_mixin import BashCommandMixin
from .mixins.python_command_mixin import PythonCommandMixin
from .mixins.threaded_command_mixin import ThreadedCommandMixin


class ICommand(ABC):

    @abstractmethod
    def validate(self):
        pass

    @abstractmethod
    def execute(self):
        pass


class Command(ICommand):

    def __init__(self, command_config: dict):
        self.command_config = command_config
        self.mixins = {
            'bash': BashCommandMixin,
            'python': PythonCommandMixin,
            'threaded': ThreadedCommandMixin
        }
        command_type = self.command_config['type']

        if command_type not in self.mixins:
            raise ValueError(f"Unsupported command type '{command_type}'")

        mixin = self.mixins[command_type](self)
        self.mixin = mixin

    def validate(self):
        self.mixin.validate()

    def execute(self):
        if self.command_config.get("skip"): return
        self.mixin.execute()

    def execute_another_command(self, command_config):
        another_command = Command(command_config)
        another_command.validate()
        another_command.execute()