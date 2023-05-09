# nanolab/command/github.py

import requests
import base64


class GitHubAPI:

    def __init__(self, github_user, github_repo, testcase_path):
        self.github_user = github_user
        self.github_repo = github_repo
        self.testcase_path = testcase_path
        self.api_url = self.construct_github_api_url()

    def construct_github_api_url(self):
        if self.testcase_path == "default":
            self.testcase_path = "default"
        return f"https://api.github.com/repos/{self.github_user}/{self.github_repo}/contents/{self.testcase_path}"

    def get_files(self):
        print(self.api_url)
        response = requests.get(self.api_url)
        if response.status_code == 200:
            return response.json()
        else:
            print(
                "Error retrieving the repository contents. Please check the provided URL."
            )
            return None

    def get_file_content(self, file_name):
        file_api_url = f"{self.api_url}/{file_name}"
        response = requests.get(file_api_url)

        if response.status_code == 200:
            file_content = response.json()["content"]
            return base64.b64decode(file_content).decode("utf-8")
        else:
            print(
                "Error retrieving the file. Please check the provided URL and file name."
            )
            return None
