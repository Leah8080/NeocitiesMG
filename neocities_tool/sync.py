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

def sync_files(api, local_dir):
    local_path = Path(local_dir)
    if not local_path.is_dir():
        rprint(f"[bold red]错误:[/bold red] 本地目录 {local_dir} 不存在或不是目录")
        return

    rprint(f"[bold blue]开始同步本地目录: {local_path.absolute()}[/bold blue]")

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
            # 简单的 size 对比
            if p.stat().st_size != remote_files_map[rel_path].get('size'):
                to_upload[rel_path] = str(p)

    # 需要删除的：远程有但本地没有的文件，且不被忽略
    to_delete = []
    for f_path in remote_files_map:
        if f_path not in local_files:
            # 如果远程文件在忽略列表中，我们不删除它
            if not (spec and spec.match_file(f_path)):
                to_delete.append(f_path)
    
    # 需要删除的目录
    to_delete_dirs = []
    for d_path in remote_dirs:
        if d_path not in local_dirs:
            if not (spec and spec.match_file(d_path)):
                to_delete_dirs.append(d_path)
    
    # 合并删除列表
    all_to_delete = to_delete + to_delete_dirs

    rprint(f"[cyan]待上传文件: {len(to_upload)}[/cyan]")
    rprint(f"[cyan]待删除文件/目录: {len(all_to_delete)}[/cyan]")

    if not to_upload and not all_to_delete:
        rprint("[bold green]已经是最新的了，无需同步。[/bold green]")
        return

    # 4. 执行上传
    if to_upload:
        with Progress() as progress:
            task = progress.add_task("[green]上传中...", total=len(to_upload))
            # 考虑到大型同步，这里可以分批上传，但文档未说明限制
            # 我们直接分批，每批 20 个文件，防止请求过大
            items = list(to_upload.items())
            batch_size = 20
            for i in range(0, len(items), batch_size):
                batch = dict(items[i:i+batch_size])
                res = api.upload_files(batch)
                if res.get('result') == 'success':
                    progress.update(task, advance=len(batch))
                else:
                    rprint(f"[bold red]分批上传失败 ({i}-{i+len(batch)}):[/bold red] {res.get('message')}")
            rprint("[bold green]上传流程结束[/bold green]")

    # 5. 执行删除
    if all_to_delete:
        with console.status("[bold red]正在删除远程多余文件..."):
            res = api.delete_files(all_to_delete)
            if res.get('result') == 'success':
                rprint("[bold green]删除成功[/bold green]")
            else:
                rprint(f"[bold red]删除失败:[/bold red] {res.get('message')}")

    rprint("[bold green]同步完成！[/bold green]")
