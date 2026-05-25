from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

console = Console()

def show_menu():
    console.print(Panel.fit(
        "[bold cyan]Neocities API 交互工具[/bold cyan]\n"
        "[1] 查看站点信息\n"
        "[2] 列出文件列表\n"
        "[3] 同步文件 (上传本地 & 删除云端多余)\n"
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
