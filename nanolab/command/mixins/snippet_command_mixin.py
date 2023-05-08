from nanolab.src.snippet_manager import SnippetManager
from .base_mixin import CommandMixinBase


class SnippetCommandMixin(CommandMixinBase):

    def validate(self):
        snippet = self.command_instance.snippet_manager.get_snippet_by_key(
            self.command_instance.command_config["key"])
        missing_vars = set(snippet.get("mandatory_vars", set())) - set(
            self.command_instance.command_config.get("variables", {}).keys())
        if missing_vars:
            raise KeyError(
                f"Missing value(s) for mandatory variable(s): {', '.join(missing_vars)}"
            )

    def execute(self):
        snippet = self.command_instance.snippet_manager.get_snippet_by_key(
            self.command_instance.command_config["key"])

        for snippet_command in snippet["commands"]:
            snippet_command["variables"] = self._get_completed_variables()
            self.command_instance.execute_another_command(snippet_command)
