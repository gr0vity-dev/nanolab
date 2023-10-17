import subprocess
from .base_mixin import CommandMixinBase


class BashCommandMixin(CommandMixinBase):

    def validate(self):
        pass
        # Validation logic for BashCommand

    def execute(self):
        variables = self._get_completed_variables()
        command = self.safe_format(
            self.command_instance.command_config['command'], **variables)
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

    def safe_format(self, template, **kwargs):
        class SafeDict(dict):
            def __missing__(self, key):
                return ''
        return template.format_map(SafeDict(**kwargs))
