import os
from dotenv import load_dotenv
from rich.prompt import Prompt
from neocities_tool.api import NeocitiesAPI
from neocities_tool.ui import console, show_menu, display_info, display_files, rprint
from neocities_tool.sync import sync_files

# 加载 .env 文件中的环境变量
load_dotenv()

def main():
    user = os.getenv("NEOCITIES_USER")
    password = os.getenv("NEOCITIES_PASS")

    if not user or not password:
        rprint("[bold red]错误:[/bold red] 未在 .env 文件中找到 NEOCITIES_USER 或 NEOCITIES_PASS")
        return

    api = NeocitiesAPI(user, password)
    
    while True:
        show_menu()
        choice = Prompt.ask("请选择操作", choices=["1", "2", "3", "0"], default="0")

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
            local_dir = Prompt.ask("请输入本地同步目录路径", default=".")
            sync_files(api, local_dir)

        elif choice == "0":
            rprint("[yellow]程序已退出[/yellow]")
            break
        
        console.input("\n[dim]按回车键继续...[/dim]")
        console.clear()

if __name__ == "__main__":
    main()
