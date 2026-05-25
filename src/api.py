import os
import requests

class NeocitiesAPI:
    BASE_URL = os.getenv("NEOCITIES_BASE_URL", "https://neocities.org/api")

    def __init__(self, user, password):
        self.auth = (user, password)

    def get_info(self, sitename=None):
        params = {}
        if sitename:
            params['sitename'] = sitename
        response = requests.get(f"{self.BASE_URL}/info", auth=self.auth, params=params)
        return response.json()

    def list_files(self, path=None):
        params = {}
        if path:
            params['path'] = path
        response = requests.get(f"{self.BASE_URL}/list", auth=self.auth, params=params)
        return response.json()

    def upload_files(self, files_dict):
        """
        files_dict: {remote_path: local_path}
        """
        upload_data = {}
        opened_files = []
        try:
            for remote_path, local_path in files_dict.items():
                if os.path.isfile(local_path):
                    f = open(local_path, 'rb')
                    opened_files.append(f)
                    upload_data[remote_path] = f
            if not upload_data:
                return {"result": "error", "message": "No files to upload"}
            response = requests.post(f"{self.BASE_URL}/upload", auth=self.auth, files=upload_data)
            return response.json()
        finally:
            for f in opened_files:
                f.close()

    def delete_files(self, filenames):
        data = {'filenames[]': filenames}
        response = requests.post(f"{self.BASE_URL}/delete", auth=self.auth, data=data)
        return response.json()
