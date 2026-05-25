import os
import requests
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

class NeocitiesAPI:
    BASE_URL = "https://neocities.org/api"

    def __init__(self, user, password):
        self.auth = (user, password)

    def get_info(self, sitename=None):
        """获取站点信息"""
        params = {}
        if sitename:
            params['sitename'] = sitename
        
        response = requests.get(f"{self.BASE_URL}/info", auth=self.auth, params=params)
        return response.json()

    def list_files(self, path=None):
        """列出文件"""
        params = {}
        if path:
            params['path'] = path
            
        response = requests.get(f"{self.BASE_URL}/list", auth=self.auth, params=params)
        return response.json()

    def upload_files(self, files_dict):
        """
        上传文件
        files_dict: 格式为 {'remote_path': 'local_path'}
        """
        files = []
        for remote_path, local_path in files_dict.items():
            if os.path.isfile(local_path):
                files.append((remote_path, open(local_path, 'rb')))
            else:
                print(f"Warning: File not found: {local_path}")
        
        if not files:
            return {"result": "error", "message": "No files to upload"}

        # API 文档指出上传是 POST /api/upload
        # 这里的 files 列表需要转换成 requests 能够处理的多部分上传格式
        # 实际上 Neocities API 通常期望字段名作为文件名
        
        upload_data = {}
        for remote_name, file_obj in files:
            upload_data[remote_name] = file_obj

        response = requests.post(f"{self.BASE_URL}/upload", auth=self.auth, files=upload_data)
        
        # 关闭所有打开的文件
        for _, f in files:
            f.close()
            
        return response.json()

    def delete_files(self, filenames):
        """
        删除文件
        filenames: 文件名列表
        """
        data = {'filenames[]': filenames}
        response = requests.post(f"{self.BASE_URL}/delete", auth=self.auth, data=data)
        return response.json()

def main():
    user = os.getenv("NEOCITIES_USER")
    password = os.getenv("NEOCITIES_PASS")

    if not user or not password:
        print("Error: NEOCITIES_USER or NEOCITIES_PASS not found in .env file")
        return

    api = NeocitiesAPI(user, password)

    # 1. 获取站点信息
    print("--- 站点信息 ---")
    info = api.get_info()
    print(info)

    # 2. 列出文件
    print("\n--- 文件列表 ---")
    files = api.list_files()
    print(files)

    # 3. 演示上传（如果当前目录下有 README.md）
    if os.path.exists("README.md"):
        print("\n--- 上传 README.md ---")
        # 将本地 README.md 上传为 index_backup.md (仅作演示)
        res = api.upload_files({"index_backup.md": "README.md"})
        print(res)

if __name__ == "__main__":
    main()
