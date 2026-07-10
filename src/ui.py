from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import print as rprint

console = Console()

def show_menu(local_repo=None):
    if local_repo:
        repo_text = f"本地项目: {local_repo}"
        repo_style = "dim"
    else:
        repo_text = "本地项目: 未配置 (NEOCITIES_REPO)"
        repo_style = "dim red"

    text = Text(justify="center")
    text.append("NEOCITIES MANAGER\n", style="bold cyan")
    text.append(repo_text + "\n", style=repo_style)
    text.append("\n")
    text.append("[1] ", style="bold green"); text.append("站点信息  ")
    text.append("[2] ", style="bold green"); text.append("站点文件  ")
    text.append("[3] ", style="bold green"); text.append("同步本地  ")
    text.append("[0] ", style="bold green"); text.append("退出程序")

    console.print(Panel(text, border_style="green", padding=(1, 4), expand=False))

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
        table.add_column("路径")
        table.add_column("类型", justify="center")
        table.add_column("大小 (Bytes)", justify="right")
        table.add_column("最后更新")

        for f in files_data['files']:
            if f['is_directory']:
                f_type = "目录"
                path_style = "yellow"
            else:
                f_type = "文件"
                path_style = "cyan"
            f_size = str(f.get('size', '-'))
            table.add_row(Text(f['path'], style=path_style), f_type, f_size, f['updated_at'])
        console.print(table)
    else:
        rprint(f"[bold red]错误:[/bold red] {files_data.get('message')}")
