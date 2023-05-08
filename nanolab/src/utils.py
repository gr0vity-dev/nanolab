from os import environ
import shutil
from importlib import resources
from pathlib import Path
import logging
from nanomock.modules.nl_parse_config import ConfigParser

logger = logging.getLogger(__name__)


def extract_packaged_data_to_disk():
    destination_path = Path.cwd()

    with resources.path("nanolab", "__init__.py") as src_dir:
        src_dir = src_dir.parent / "snippets"
        dest_dir = destination_path / "nanolab" / "snippets"

        if src_dir.exists():
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src_dir, dest_dir, dirs_exist_ok=True)
            logger.info(
                "nanolab default snippets have been copied to your current working directory."
            )
        else:
            raise FileExistsError("nanolab.snippets not found.")


def get_config_parser() -> ConfigParser:
    default_path = "."
    default_file = "nl_config.toml"
    config_parser = ConfigParser(environ.get("NL_CONF_DIR", default_path),
                                 environ.get("NL_CONF_FILE", default_file))

    return config_parser