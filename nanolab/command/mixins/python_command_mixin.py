from .base_mixin import CommandMixinBase
from nanolab import pycmd


class PythonCommandMixin(CommandMixinBase):

    def validate(self):

        if "method" not in self.command_instance.command_config:
            raise ValueError("Python command: 'method' is required.")

        method_name = self.command_instance.command_config["method"]

        if "class" in self.command_instance.command_config:
            cls = getattr(pycmd, self.command_instance.command_config["class"])
            if not cls:
                raise ValueError(
                    f"Python command: Class '{self.command_instance.command_config['class']}' not found."
                )
            if not hasattr(cls, method_name):
                raise ValueError(
                    f"Python command: Method '{method_name}' not found in class '{self.command_instance.command_config['class']}'."
                )
        else:
            if method_name not in globals():
                raise ValueError(
                    f"Python command: Method '{method_name}' not found in the current module."
                )

    def execute(self):
        class_name = self.command_instance.command_config.get(
            "class", "NodeInteraction")
        cls = getattr(pycmd, class_name)
        instance = cls(**self.command_instance.command_config.get(
            'constructor_params', {}))

        method = getattr(instance,
                         self.command_instance.command_config['method'])
        filtered_variables = self._get_filtered_variables(method)
        method(**filtered_variables)
