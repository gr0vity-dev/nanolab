from os import environ, path, walk
import time
import shutil
from importlib import resources
from pathlib import Path
import logging
import requests
from nanomock.modules.nl_parse_config import ConfigParser
import filecmp

logger = logging.getLogger(__name__)


def copy_if_changed(src_dir, dst_dir):
    for src_root, dirs, files in walk(src_dir):
        dst_root = src_root.replace(src_dir, dst_dir, 1)
        for file in files:
            src_file = path.join(src_root, file)
            dst_file = path.join(dst_root, file)
            if not path.exists(dst_file) or not filecmp.cmp(
                    src_file, dst_file, shallow=False):
                shutil.copy2(src_file, dst_file)


def extract_packaged_data_to_disk(snippets_path):
    with resources.path("nanolab", "__init__.py") as src_dir:
        src_dir = src_dir.parent / "snippets"
        dest_dir = snippets_path

        if src_dir.exists():
            dest_dir.mkdir(parents=True, exist_ok=True)
            copy_if_changed(str(src_dir), str(dest_dir))
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


def download_data(data: str, filename: str, resource_path: Path) -> Path:
    destination = resource_path / filename.strip()

    if not destination.exists():
        print(f"Start Fetching '{filename}' to '{destination}'")
        if data.startswith("http://") or data.startswith("https://"):
            response = requests.get(data)
            with destination.open("wb") as f:
                f.write(response.content)
        else:
            with destination.open("w") as f:
                f.write(data)
        print(f"Done  Fetching '{filename}' to '{destination}'")
        wait_for_file(destination, timeout=10)
    else:
        print(f"Skip  Fetching '{filename}' to '{destination}'")

    return destination


def wait_for_file(file_path: str, timeout: int = 10):
    """Wait for a file to be written completely."""

    # Convert the timeout to seconds.
    timeout = time.time() + timeout

    # Wait for the file to exist.
    while not path.exists(file_path):
        time.sleep(0.1)
        if time.time() > timeout:
            raise TimeoutError(
                f"Timeout waiting for file {file_path} to exist.")

    # Wait for the file size to stop changing.
    old_file_size = -1
    while old_file_size != path.getsize(file_path):
        old_file_size = path.getsize(file_path)
        time.sleep(0.1)
        if time.time() > timeout:
            raise TimeoutError(
                f"Timeout waiting for file {file_path} to be written completely."
            )

    # Now the file should be written completely.
