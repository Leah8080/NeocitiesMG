import os
from pathlib import Path
from .ui import console, rprint
from rich.progress import Progress
import pathspec

def load_ignore_spec(local_path):
    ignore_file = local_path / ".gitignore"
    if ignore_file.exists():
        try:
            with open(ignore_file, 'r', encoding='utf-8') as f:
                return pathspec.PathSpec.from_lines('gitwildmatch', f)
        except Exception as e:
            rprint(f"[yellow]警告: 无法读取 .gitignore: {e}[/yellow]")
    return None

def generate_link_md(local_path, local_files):
    """
    根据 CNAME 和本地文件列表生成 link.md
    """
    cname_file = local_path / "CNAME"
    if not cname_file.exists():
        rprint("[yellow]警告: 未找到 CNAME 文件，跳过生成 link.md[/yellow]")
        return

    try:
        base_url = cname_file.read_text(encoding='utf-8').strip()
        if not base_url.startswith("http"):
            base_url = f"https://{base_url}"
        if not base_url.endswith("/"):
            base_url += "/"
    except Exception as e:
        rprint(f"[yellow]警告: 读取 CNAME 失败: {e}[/yellow]")
        return

    # 排序逻辑：根目录文件优先，然后按目录深度和字母排序
    def sort_key(rel_path):
        parts = rel_path.split('/')
        # 深度越浅越靠前，同深度按字母排序
        return (len(parts) - 1, rel_path)

    sorted_paths = sorted(local_files.keys(), key=sort_key)

    content = [f"# Site Links ({base_url})\n"]
    
    current_depth = -1
    for rel_path in sorted_paths:
        parts = rel_path.split('/')
        depth = len(parts) - 1
        
        if depth != current_depth:
            if depth == 0:
                content.append("## Root Files")
            else:
                # 显示所属目录名
                content.append(f"## {os.path.dirname(rel_path)}")
            current_depth = depth
        
        full_url = f"{base_url}{rel_path}"
        content.append(f"```text\n{full_url}\n```")

    try:
        link_md_path = local_path / "link.md"
        link_md_path.write_text("\n".join(content), encoding='utf-8')
        rprint(f"[bold green]成功生成链接文档: {link_md_path}[/bold green]")
    except Exception as e:
        rprint(f"[bold red]错误: 写入 link.md 失败:[/bold red] {e}")

from rich.tree import Tree
from rich.prompt import Confirm

def show_sync_preview(local_path, local_files):
    """
    显示待同步文件的树形预览
    """
    tree = Tree(f"[bold magenta]待同步目录结构: {local_path.name}[/bold magenta]")
    
    # 建立目录索引
    paths = sorted(local_files.keys())
    nodes = {"": tree}
    
    for path_str in paths:
        parts = path_str.split('/')
        for i in range(len(parts)):
            parent_path = "/".join(parts[:i])
            current_path = "/".join(parts[:i+1])
            if current_path not in nodes:
                is_file = (i == len(parts) - 1)
                style = "green" if is_file else "blue"
                nodes[current_path] = nodes[parent_path].add(f"[{style}]{parts[i]}[/{style}]")
    
    console.print(tree)

def sync_files(api, local_dir):
    local_path = Path(local_dir)
    if not local_path.is_dir():
        rprint(f"[bold red]错误:[/bold red] 本地目录 {local_dir} 不存在或不是目录")
        return

    rprint(f"[bold blue]正在分析本地目录: {local_path.absolute()}[/bold blue]")

    spec = load_ignore_spec(local_path)
    if spec:
        rprint("[dim]已加载 .gitignore 过滤规则[/dim]")

    # 1. 获取本地文件和目录列表 (相对路径)
    local_files = {}
    local_dirs = set()
    
    for p in local_path.rglob('*'):
        rel_path = p.relative_to(local_path).as_posix()
        
        # 检查是否被忽略
        if spec and spec.match_file(rel_path):
            continue
            
        if p.is_file():
            local_files[rel_path] = p
        elif p.is_dir():
            local_dirs.add(rel_path)

    # 显示预览并确认
    show_sync_preview(local_path, local_files)
    if not Confirm.ask("\n[bold yellow]确认根据以上结构同步到 Neocities 云端吗？[/bold yellow]", default=True):
        rprint("[yellow]同步操作已取消[/yellow]")
        return

    # 2. 获取远程文件列表
    with console.status("[bold green]正在获取远程文件列表..."):
        remote_data = api.list_files()
    
    if remote_data.get('result') != 'success':
        rprint(f"[bold red]错误: 无法获取远程文件列表:[/bold red] {remote_data.get('message')}")
        return

    remote_files_map = {f['path']: f for f in remote_data['files'] if not f['is_directory']}
    remote_dirs = {f['path'] for f in remote_data['files'] if f['is_directory']}

    # 3. 计算差异
    to_upload = {}
    for rel_path, p in local_files.items():
        if rel_path not in remote_files_map:
            to_upload[rel_path] = str(p)
        else:
            if p.stat().st_size != remote_files_map[rel_path].get('size'):
                to_upload[rel_path] = str(p)

    to_delete = []
    for f_path in remote_files_map:
        if f_path not in local_files:
            if not (spec and spec.match_file(f_path)):
                to_delete.append(f_path)
    
    to_delete_dirs = []
    for d_path in remote_dirs:
        if d_path not in local_dirs:
            if not (spec and spec.match_file(d_path)):
                to_delete_dirs.append(d_path)
    
    all_to_delete = to_delete + to_delete_dirs

    rprint(f"[cyan]待上传文件: {len(to_upload)}[/cyan]")
    rprint(f"[cyan]待删除文件/目录: {len(all_to_delete)}[/cyan]")

    # 4. 执行上传
    if to_upload:
        with Progress() as progress:
            task = progress.add_task("[green]上传中...", total=len(to_upload))
            items = list(to_upload.items())
            batch_size = 20
            for i in range(0, len(items), batch_size):
                batch = dict(items[i:i+batch_size])
                res = api.upload_files(batch)
                if res.get('result') == 'success':
                    progress.update(task, advance=len(batch))
                else:
                    rprint(f"[bold red]分批上传失败:[/bold red] {res.get('message')}")

    # 5. 执行删除
    if all_to_delete:
        with console.status("[bold red]正在删除远程多余文件..."):
            res = api.delete_files(all_to_delete)
            if res.get('result') == 'success':
                rprint("[bold green]删除成功[/bold green]")
            else:
                rprint(f"[bold red]删除失败:[/bold red] {res.get('message')}")

    rprint("[bold green]同步完成！[/bold green]")
    
    # 6. 生成链接文档
    generate_link_md(local_path, local_files)
