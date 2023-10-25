import os
import requests
from pathlib import Path
import json


class DataResolver():

    def resolve_config(self, path):

        if path.startswith('http') or path.startswith('https'):
            return requests.get(path).text
        else:
            with open(os.path.abspath(path), 'r') as f:
                return f.read()

    def resolve_config_elements(self, config_path):
        """
        Resolves all the elements from a config file, downloading any remote URLs to disk paths.
        """
        with open(config_path, 'r') as f:
            config = json.load(f)

        for key in config.get("global", {}).keys():
            if isinstance(config["global"][key],
                          str) and config["global"][key].startswith('http'):
                url = config["global"][key]
                filename = Path(url).name
                destination_path = os.path.join(os.path.dirname(config_path),
                                                filename)
                self.download_file(url, destination_path)
                config["global"][key] = destination_path

        return config

    def download_file(self, url: str, destination_path: str):
        """
        Downloads a file from the given URL to the local destination path.
        Skips the download if the file already exists.
        """
        destination_path = Path(destination_path)
        if destination_path.exists():
            return

        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            with open(destination_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
