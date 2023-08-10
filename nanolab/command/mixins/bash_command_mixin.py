import subprocess
from .base_mixin import CommandMixinBase


class BashCommandMixin(CommandMixinBase):

    def validate(self):
        pass
        # Validation logic for BashCommand

    def execute(self):
        variables = self._get_completed_variables()
        command = self.command_instance.command_config['command'].format(
            **variables)
        process = subprocess.run(
            command, shell=True, text=True, capture_output=True)

        if process.returncode != 0:
            print(
                f"Error executing command: {command}\nError: {process.stderr.strip()}"
            )
        else:
            response = process.stdout.strip() or process.stderr.strip(
            ) or command
            print(response)
