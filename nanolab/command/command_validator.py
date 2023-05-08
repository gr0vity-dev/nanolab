from .command import Command


class CommandValidator:

    @staticmethod
    def validate_command(command_config: dict, snippets: dict = None):
        command = Command(command_config, snippets)
        command.validate()
