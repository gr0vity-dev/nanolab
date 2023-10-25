import requests
import base64


class GitHubAPI:

    def __init__(self, github_user, github_repo, testcase_path):
        self.github_user = github_user
        self.github_repo = github_repo

        # Extract ref from testcase_path and update it
        self.testcase_path, self.gh_ref = self.extract_ref_from_path(
            testcase_path)

    def get_api_url(self, endpoint):
        url = f"https://api.github.com/repos/{self.github_user}/{self.github_repo}/contents/{endpoint}{self.gh_ref}"
        print(url)
        return url

    def extract_ref_from_path(self, testcase_path):
        if "?ref=" in testcase_path:
            parts = testcase_path.split("?ref=")

            # Return testcase_path (without ref) and the ref value
            return parts[0], "?ref=" + parts[1]
        else:
            # Return the original testcase_path and an empty string for gh_ref
            return testcase_path, ""

    def get_files(self):

        response = requests.get(self.get_api_url(self.testcase_path))
        if response.status_code == 200:
            return response.json()
        else:
            print(
                "Error retrieving the repository contents. Please check the provided URL.")
            return None

    def get_file_content(self, file_name):
        file_api_url = self.get_api_url(f"{self.testcase_path}/{file_name}")
        response = requests.get(file_api_url)

        if response.status_code == 200:
            file_content = response.json()["content"]
            return base64.b64decode(file_content).decode("utf-8")
        else:
            print(
                "Error retrieving the file. Please check the provided URL and file name.")
            return None
