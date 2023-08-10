from os import environ
import inspect
import logging


class CommandMixinBase:

    def __init__(self, command_instance):
        self.command_instance = command_instance
        self.logger = logging.getLogger(__name__)

    def _get_completed_variables(self):
        variables = self.command_instance.command_config.get('variables', {})

        # add global variables
        variables["docker_tag"] = environ["docker_tag"]
        return variables

    def _get_filtered_variables(self, method):
        variables = self._get_completed_variables()
        method_parameters = self._get_method_parameters(method)
        return {
            key: value
            for key, value in variables.items() if key in method_parameters
        }

    def _get_method_parameters(self, method):
        signature = inspect.signature(method)
        return [param.name for param in signature.parameters.values()]
