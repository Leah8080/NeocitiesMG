import os
import requests
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich.progress import Progress
from rich import print as rprint

# 加载 .env 文件中的环境变量
load_dotenv()

class NeocitiesAPI:
    BASE_URL = os.getenv("NEOCITIES_BASE_URL")

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

console = Console()

def show_menu():
    console.print(Panel.fit(
        "[bold cyan]Neocities API 交互工具[/bold cyan]\n"
        "[1] 查看站点信息\n"
        "[2] 列出文件列表\n"
        "[3] 上传文件\n"
        "[4] 删除文件\n"
        "[0] 退出程序",
        title="菜单", border_style="green"
    ))

def display_info(info):
    if info.get('result') == 'success':
        data = info['info']
        table = Table(title="站点基本信息", show_header=True, header_style="bold magenta")
        table.add_column("项目", style="dim")
        table.add_column("内容")
        table.add_row("站点名", data['sitename'])
        table.add_row("浏览量", str(data['views']))
        table.add_row("点击量", str(data['hits']))
        table.add_row("创建时间", data['created_at'])
        table.add_row("标签", ", ".join(data['tags']))
        console.print(table)
    else:
        rprint(f"[bold red]错误:[/bold red] {info.get('message')}")

def display_files(files_data):
    if files_data.get('result') == 'success':
        table = Table(title="文件列表", show_header=True, header_style="bold blue")
        table.add_column("路径", style="cyan")
        table.add_column("类型", justify="center")
        table.add_column("大小 (Bytes)", justify="right")
        table.add_column("最后更新")
        
        for f in files_data['files']:
            f_type = "目录" if f['is_directory'] else "文件"
            f_size = str(f.get('size', '-'))
            table.add_row(f['path'], f_type, f_size, f['updated_at'])
        console.print(table)
    else:
        rprint(f"[bold red]错误:[/bold red] {files_data.get('message')}")

def main():
    user = os.getenv("NEOCITIES_USER")
    password = os.getenv("NEOCITIES_PASS")

    if not user or not password:
        rprint("[bold red]错误:[/bold red] 未在 .env 文件中找到 NEOCITIES_USER 或 NEOCITIES_PASS")
        return

    api = NeocitiesAPI(user, password)
    
    while True:
        show_menu()
        choice = Prompt.ask("请选择操作", choices=["1", "2", "3", "4", "0"], default="0")

        if choice == "1":
            with console.status("[bold green]正在获取信息..."):
                info = api.get_info()
            display_info(info)
        
        elif choice == "2":
            path = Prompt.ask("请输入要查询的路径 (直接回车查询根目录)", default="")
            with console.status("[bold green]正在读取文件列表..."):
                files = api.list_files(path if path else None)
            display_files(files)

        elif choice == "3":
            local_path = Prompt.ask("请输入本地文件路径")
            if not os.path.exists(local_path):
                rprint("[bold red]错误:[/bold red] 本地文件不存在")
                continue
            remote_path = Prompt.ask("请输入远程存储路径", default=os.path.basename(local_path))
            
            with console.status(f"[bold green]正在上传 {local_path} ..."):
                res = api.upload_files({remote_path: local_path})
            
            if res.get('result') == 'success':
                rprint(f"[bold green]成功:[/bold green] {res.get('message')}")
            else:
                rprint(f"[bold red]失败:[/bold red] {res.get('message')}")

        elif choice == "4":
            filename = Prompt.ask("请输入要删除的文件名 (多个文件用逗号隔开)")
            filenames = [f.strip() for f in filename.split(",")]
            if Confirm.ask(f"确定要删除这些文件吗? {filenames}"):
                with console.status("[bold red]正在删除..."):
                    res = api.delete_files(filenames)
                if res.get('result') == 'success':
                    rprint(f"[bold green]成功:[/bold green] {res.get('message')}")
                else:
                    rprint(f"[bold red]失败:[/bold red] {res.get('message')}")

        elif choice == "0":
            rprint("[yellow]程序已退出[/yellow]")
            break
        
        console.input("\n[dim]按回车键继续...[/dim]")
        console.clear()

if __name__ == "__main__":
    from rich.prompt import Confirm
    main()
