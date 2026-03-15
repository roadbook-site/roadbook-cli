import requests
from .config import get_token, get_server_url

class APIClient:
    def __init__(self):
        self.base_url = get_server_url().rstrip("/")
        self.token = get_token()
        self.session = requests.Session()
        if self.token:
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})

    def login(self, username, password):
        url = f"{self.base_url}/api/v1/auth/login/access-token"
        response = self.session.post(url, data={"username": username, "password": password})
        response.raise_for_status()
        data = response.json()
        self.token = data["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        return self.token

    def list_roadbooks(self, query=None):
        url = f"{self.base_url}/api/v1/roadbooks/"
        params = {}
        if query:
            params["q"] = query
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_roadbook(self, roadbook_id):
        url = f"{self.base_url}/api/v1/roadbooks/{roadbook_id}"
        response = self.session.get(url)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    def create_roadbook(self, data):
        url = f"{self.base_url}/api/v1/roadbooks/"
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()

    def upload_content(self, roadbook_id, file_path):
        url = f"{self.base_url}/api/v1/roadbooks/{roadbook_id}/content"
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = self.session.post(url, files=files)
        response.raise_for_status()
        return response.json()

    def download_content(self, roadbook_id, destination_path):
        url = f"{self.base_url}/api/v1/roadbooks/{roadbook_id}/content"
        response = self.session.get(url, stream=True)
        response.raise_for_status()
        with open(destination_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
