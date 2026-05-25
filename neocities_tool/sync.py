import os
from pathlib import Path
from .ui import console, rprint
from rich.progress import Progress

def sync_files(api, local_dir):
    local_path = Path(local_dir)
    if not local_path.is_dir():
        rprint(f"[bold red]错误:[/bold red] 本地目录 {local_dir} 不存在或不是目录")
        return

    rprint(f"[bold blue]开始同步本地目录: {local_path.absolute()}[/bold blue]")

    # 1. 获取本地文件列表 (相对路径)
    local_files = {}
    for p in local_path.rglob('*'):
        if p.is_file():
            # Neocities 使用正斜杠
            rel_path = p.relative_to(local_path).as_posix()
            local_files[rel_path] = p

    # 2. 获取远程文件列表
    with console.status("[bold green]正在获取远程文件列表..."):
        remote_data = api.list_files()
    
    if remote_data.get('result') != 'success':
        rprint(f"[bold red]错误: 无法获取远程文件列表:[/bold red] {remote_data.get('message')}")
        return

    remote_files = {f['path'] for f in remote_data['files'] if not f['is_directory']}
    remote_dirs = {f['path'] for f in remote_data['files'] if f['is_directory']}

    # 3. 计算差异
    # 需要上传的：本地有但远程没有，或者本地有的文件 (为了简单起见，这里可以加上文件大小校验，但 Neocities API 没提供 hash)
    # 暂时默认所有本地文件都尝试上传，或者你可以对比 size
    
    remote_files_map = {f['path']: f for f in remote_data['files'] if not f['is_directory']}
    
    to_upload = {}
    for rel_path, p in local_files.items():
        if rel_path not in remote_files_map:
            to_upload[rel_path] = str(p)
        else:
            # 简单的 size 对比
            if p.stat().st_size != remote_files_map[rel_path].get('size'):
                to_upload[rel_path] = str(p)

    # 需要删除的：远程有但本地没有的文件
    to_delete = [f for f in remote_files if f not in local_files]
    
    # 注意：Neocities 的删除 API 似乎只能删文件。
    # 如果要删目录，通常删除目录下所有文件即可。
    # 也可以尝试把目录路径加进去。
    
    # 检查是否有需要删除的目录（本地不存在的目录）
    local_dirs = {p.relative_to(local_path).as_posix() for p in local_path.rglob('*') if p.is_dir()}
    to_delete_dirs = [d for d in remote_dirs if d not in local_dirs]
    
    # 合并删除列表
    all_to_delete = to_delete + to_delete_dirs

    rprint(f"[cyan]待上传文件: {len(to_upload)}[/cyan]")
    rprint(f"[cyan]待删除文件/目录: {len(all_to_delete)}[/cyan]")

    if not to_upload and not all_to_delete:
        rprint("[bold green]已经是最新的了，无需同步。[/bold green]")
        return

    # 4. 执行上传
    if to_upload:
        # Neocities 限制单次上传文件数量或大小吗？文档没说，但最好分批或显示进度
        with Progress() as progress:
            task = progress.add_task("[green]上传中...", total=len(to_upload))
            # 我们可以一次性上传，或者分批。requests 里的 files 字典可以包含多个文件。
            # Neocities 建议一次不要传太多。
            # 这里简单处理，一次性传。
            res = api.upload_files(to_upload)
            if res.get('result') == 'success':
                progress.update(task, advance=len(to_upload))
                rprint("[bold green]上传成功[/bold green]")
            else:
                rprint(f"[bold red]上传失败:[/bold red] {res.get('message')}")

    # 5. 执行删除
    if all_to_delete:
        with console.status("[bold red]正在删除远程多余文件..."):
            res = api.delete_files(all_to_delete)
            if res.get('result') == 'success':
                rprint("[bold green]删除成功[/bold green]")
            else:
                rprint(f"[bold red]删除失败:[/bold red] {res.get('message')}")

    rprint("[bold green]同步完成！[/bold green]")
