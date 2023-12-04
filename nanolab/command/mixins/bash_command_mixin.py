import subprocess
from .base_mixin import CommandMixinBase


class BashCommandMixin(CommandMixinBase):

    def validate(self):
        pass
        # Validation logic for BashCommand

    def execute(self):
        command_config = self.command_instance.command_config
        variables = self._get_completed_variables()
        command = self.safe_format(command_config['command'], **variables)
        background = command_config.get('background', False)

        if background:
            self.execute_background(command, command_config.get('pid'))
        else:
            self.execute_foreground(command)

    def execute_foreground(self, command):
        process = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Stream the output
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())

        # Check for any errors
        error_output = process.stderr.read()
        if error_output:
            print(
                f"Error executing command: {command}\nError: {error_output.strip()}")

    def execute_background(self, command, pid_file=None):
        process = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if pid_file:
            self.write_pid_to_file(process.pid, pid_file)
        print(
            f"Command '{command}' is running in the background with PID {process.pid}")

    def write_pid_to_file(self, pid, filename):
        with open(filename, 'w') as file:
            file.write(str(pid))

    def handle_command_output(self, command, process):
        if process.returncode != 0:
            print(
                f"Error executing command: {command}\nError: {process.stderr.strip()}")
        else:
            response = process.stdout.strip() or process.stderr.strip() or command
            print(response)

    def safe_format(self, template, **kwargs):
        class SafeDict(dict):
            def __missing__(self, key):
                return ''
        return template.format_map(SafeDict(**kwargs))
