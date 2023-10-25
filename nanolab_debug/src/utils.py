from os import environ, path, walk
import shutil
from importlib import resources
from pathlib import Path
import logging
import requests
from nanomock.modules.nl_parse_config import ConfigParser
import filecmp

logger = logging.getLogger(__name__)


def _copy_changed_files(src_file: str, dst_file: str):
    """Copy files from source to destination if they have changed."""
    if not path.exists(dst_file) or not filecmp.cmp(
            src_file, dst_file, shallow=False):
        shutil.copy2(src_file, dst_file)


def _walk_and_copy(src_dir: str, dst_dir: str):
    """Walk through the source directory and copy changed files to destination."""
    for src_root, _, files in walk(src_dir):
        dst_root = src_root.replace(src_dir, dst_dir, 1)
        for file in files:
            src_file = path.join(src_root, file)
            dst_file = path.join(dst_root, file)
            _copy_changed_files(src_file, dst_file)


def extract_packaged_data_to_disk(snippets_path):
    with resources.path("nanolab", "__init__.py") as src_dir:
        src_dir = src_dir.parent / "snippets"
        dest_dir = snippets_path

        if src_dir.exists():
            dest_dir.mkdir(parents=True, exist_ok=True)
            _walk_and_copy(str(src_dir), str(dest_dir))
            logger.info(
                f"nanolab default snippets have been copied into {snippets_path}."
            )
        else:
            raise FileExistsError("nanolab.snippets not found.")


def set_nanomock_config_path(config_path: Path):
    environ["NL_CONF_DIR"] = config_path.parent
    environ["NL_CONF_FILE"] = config_path.name


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
            _download_remote_data(data, destination)
        else:
            _copy_local_data(data, destination)
        print(f"Done  Fetching '{filename}' to '{destination}'")
    else:
        print(f"Skip  Fetching '{filename}' to '{destination}'")

    return destination


def _download_remote_data(data: str, destination: Path) -> None:
    response = requests.get(data)
    if response.status_code == 200:
        with destination.open("wb") as f:
            f.write(response.content)

    else:
        raise requests.HTTPError(
            f"Failed to fetch '{destination.name}' from '{data}', status code: {response.status_code}"
        )


def _copy_local_data(data: str, destination: Path) -> None:
    with destination.open("w") as f:
        f.write(data)


def print_dot(func):

    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        print('.', end='', flush=True)
        return result

    return wrapper