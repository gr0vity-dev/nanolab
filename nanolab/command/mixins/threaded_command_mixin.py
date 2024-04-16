import threading
from nanolab import pycmd
from .base_mixin import CommandMixinBase
from collections import defaultdict
import heapq
import time
import copy


class ThreadedCommandMixin(CommandMixinBase):

    def validate(self):
        for command_config in self.command_instance.command_config["commands"]:
            command = self.command_instance.create_command_instance(
                command_config)
            command.validate()

    def execute(self):
        normalized_commands = self._normalize_delays(
            self.command_instance.command_config["commands"])
        schedule = self._build_schedule(normalized_commands)
        self._execute_commands(schedule)

    def _execute_command_sequence(self, commands):
        for command_config in commands:
            self.command_instance.execute_another_command(command_config)

    def _normalize_delays(self, commands):
        min_delay = min(cmd.get("delay", 0) for cmd in commands)
        return [{**cmd, "delay": cmd.get("delay", 0) + abs(min_delay)} for cmd in commands]

    def _build_schedule(self, commands):
        schedule = []
        command_groups = defaultdict(list)

        def _add_to_schedule(delay, target, args):
            run_at = time.time() + delay
            time.sleep(0.01)
            heapq.heappush(schedule, (run_at, target, args))

        def _append_replicas(command_config):
            # Extract and remove the replication count from the command_config
            replica_count = int(command_config.pop('replicas', 1))
            for _ in range(replica_count):
                # Make a deep copy to ensure each command is a separate object
                replicated_command = copy.deepcopy(command_config)
                delay = replicated_command.get("delay", 0)
                _add_to_schedule(
                    delay, self.command_instance.execute_another_command, (replicated_command,))

        for command_config in commands:
            group = command_config.get("group")
            if group:
                # If the command is part of a group, append it to the respective group list
                command_groups[group].append(command_config)
            else:
                # Check if this command should be independently replicated
                if "replicas" in command_config:
                    _append_replicas(command_config)
                else:
                    delay = command_config.get("delay", 0)
                    _add_to_schedule(
                        delay, self.command_instance.execute_another_command, (command_config,))

        for group, command_configs in command_groups.items():
            delay = command_configs[0].get("delay", 0)
            _add_to_schedule(
                delay, self._execute_command_sequence, (command_configs,))

        return schedule

    def _execute_commands(self, schedule):
        threads = []
        while schedule:
            run_at, target, args = heapq.heappop(schedule)
            delay = max(0, run_at - time.time())
            time.sleep(delay)
            thread = threading.Thread(target=target, args=args)
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()
