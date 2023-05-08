import threading
from nanolab.src.snippet_manager import SnippetManager
from nanolab import pycmd
from .base_mixin import CommandMixinBase
from collections import defaultdict


class ThreadedCommandMixin(CommandMixinBase):

    def _execute_command_sequence(self, commands):
        for command_config in commands:
            self.command_instance.execute_another_command(command_config)

    def validate(self):
        for python_command in self.command_instance.command_config["commands"]:
            if "method" not in python_command:
                raise ValueError(f"Python command: 'method' is required.")

            method_name = python_command["method"]

            if "class" in python_command:
                cls = getattr(pycmd, python_command["class"])
                if not cls:
                    raise ValueError(
                        f"Python command: Class '{python_command['class']}' not found."
                    )
                if not hasattr(cls, method_name):
                    raise ValueError(
                        f"Python command: Method '{method_name}' not found in class '{python_command['class']}'."
                    )
            else:
                if method_name not in globals():
                    raise ValueError(
                        f"Python command: Method '{method_name}' not found in the current module."
                    )

    def execute(self):
        threads = []
        command_groups = defaultdict(list)

        for command_config in self.command_instance.command_config["commands"]:
            group = command_config.get("group")
            if group:
                command_groups[group].append(command_config)
            else:
                thread = threading.Thread(
                    target=self.command_instance.execute_another_command,
                    args=(command_config, ))
                threads.append(thread)

        #execute these commands in sequence in one thread
        for group_commands in command_groups.values():
            thread = threading.Thread(target=self._execute_command_sequence,
                                      args=(group_commands, ))
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()
