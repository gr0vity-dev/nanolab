import threading
from nanolab import pycmd
from .base_mixin import CommandMixinBase
from collections import defaultdict
import heapq
import time


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
        schedule = []
        command_groups = defaultdict(list)
        config = self.command_instance.command_config["commands"]

        min_delay = min(cmd.get("delay", 0) for cmd in config)
        # Normalize all delays by adding the absolute value of the minimum delay
        config = [{
            **cmd, "delay": cmd.get("delay", 0) + abs(min_delay)
        } for cmd in config]

        def add_to_schedule(delay, target, args):
            # Get the current time and add the delay (could be negative)
            run_at = time.time() + delay
            # Add the task to the schedule
            heapq.heappush(schedule, (run_at, target, args))

        for command_config in config:
            group = command_config.get("group")
            if group:
                command_groups[group].append(command_config)
            else:
                delay = command_config.get("delay", 0)
                add_to_schedule(delay,
                                self.command_instance.execute_another_command,
                                (command_config, ))

        for group, command_configs in command_groups.items():
            delay = command_configs[0].get("delay", 0)
            add_to_schedule(delay, self._execute_command_sequence,
                            (command_configs, ))

        threads = []
        while schedule:
            run_at, target, args = heapq.heappop(schedule)
            delay = max(0, run_at - time.time())
            time.sleep(delay)  # wait until it's time to start this task
            thread = threading.Thread(target=target, args=args)
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()
