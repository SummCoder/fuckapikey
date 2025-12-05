import sqlite3
import click
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rapidfuzz import process, fuzz
from pathlib import Path

# --- 配置部分 ---
# 1. 获取当前用户的主目录 (C:\Users\xxx)
USER_HOME = Path.home()
# 2. 定义存放目录名为 .fuckapi
APP_DIR = USER_HOME / ".fuckapi"

# 3. 定义完整的数据库文件路径
DB_PATH = APP_DIR / "apikeys.db"

console = Console()

# --- 数据库操作 ---
def init_db():
    """初始化数据库表结构"""
    APP_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH)) 
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS keys (
            name TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            description TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_key_db(name, value, description):
    """写入数据库"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO keys (name, value, description) VALUES (?, ?, ?)", 
                       (name, value, description))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        console.print(f"[red]Error saving key: {e}[/red]")
        return False

def get_all_keys_db():
    """获取所有 Keys"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("SELECT name, value, description FROM keys")
    results = cursor.fetchall()
    conn.close()
    return results

def get_key_db(name):
    """获取单个 Key"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("SELECT name, value, description FROM keys WHERE name = ?", (name,))
    result = cursor.fetchone()
    conn.close()
    return result

# --- 辅助功能 ---
def find_similar_key(wrong_name, all_names):
    """使用模糊匹配查找最接近的 Key 名称 (类似 thefuck)"""
    if not all_names:
        return None
    
    # 提取最佳匹配，得分高于 60 才算相关
    match = process.extractOne(wrong_name, all_names, scorer=fuzz.WRatio)
    if match and match[1] > 60:
        return match[0]
    return None

def semantic_search(query, all_data):
    """简单的语义/关键词搜索，在描述和名称中查找"""
    results = []
    query = query.lower()
    for name, value, desc in all_data:
        search_content = (name + " " + (desc or "")).lower()
        if query in search_content:
            results.append((name, value, desc))
    return results

# --- CLI 命令定义 ---
@click.group()
def cli():
    """🔑 API Key 管理快捷工具"""
    init_db()

@cli.command()
@click.option('--name', '-n', help='API Key 的唯一名称')
@click.option('--value', '-v', help='API Key 的值')
@click.option('--desc', '-d', help='关于这个 Key 的描述')
def add(name, value, desc):
    """
    添加或更新 API Key。
    包含智能检测：会检查名称是否重复，或是否存在非常相似的名称以防止手误。
    """
    # 1. 获取名称 (如果未通过参数传入)
    if not name:
        name = Prompt.ask("[bold cyan]Key Name[/bold cyan]")
    
    # 获取现有数据进行比对
    all_data = get_all_keys_db()
    all_names = [row[0] for row in all_data]

    # --- 逻辑分支 A: 精确匹配 (已存在) ---
    if name in all_names:
        console.print(f"\n[yellow]⚠ 警告: Key '{name}' 已经存在！[/yellow]")
        existing_key = get_key_db(name)
        console.print(f"[dim]原描述: {existing_key[2]}[/dim]")
        
        if not Confirm.ask("是否覆盖更新旧值？"):
            console.print("[red]已取消操作。[/red]")
            return
        # 用户确认覆盖，继续向下执行

    # --- 逻辑分支 B: 模糊相似检测 (防止手误) ---
    else:
        # 查找最相似的 Key (相似度阈值设为 75)
        similar = process.extractOne(name, all_names, scorer=fuzz.WRatio) if all_names else None
        
        if similar and similar[1] > 75:
            existing_name = similar[0]
            score = similar[1]
            
            console.print(f"\n[bold orange1]检测到相似的 Key:[/bold orange1] [cyan]'{existing_name}'[/cyan] (相似度 {int(score)}%)")
            console.print(f"[dim]您输入的是: '{name}'[/dim]")
            
            # 给出选项
            options = [
                f"1. 更新原有的 '{existing_name}' (修正输入)",
                f"2. 坚持创建新 Key '{name}'",
                "3. 取消"
            ]
            console.print("\n".join(options))
            choice = Prompt.ask("请选择操作", choices=["1", "2", "3"], default="1")

            if choice == "1":
                name = existing_name  # 修正名称为已存在的那个
                console.print(f"[green]➜ 切换为更新: {name}[/green]")
            elif choice == "3":
                console.print("[red]已取消操作。[/red]")
                return
            # 选择 2 则不做改变，继续使用新名字创建

    # 2. 获取值和描述 (如果未通过参数传入)
    if not value:
        # password=False 让显示可见，如果希望像密码一样隐藏输入，改为 True
        value = Prompt.ask("[bold magenta]Key Value[/bold magenta]") 
    if not desc:
        desc = Prompt.ask("[bold green]Description[/bold green]", default="")

    # 3. 执行数据库写入
    if add_key_db(name, value, desc):
        action_text = "更新" if name in all_names else "新建"
        console.print(f"[bold green]✔ 成功{action_text} API Key: [white]{name}[/white][/bold green]")


@cli.command()
@click.option('--show-values', is_flag=True, help='显示真实的 Key 值（默认隐藏）')
def list(show_values):
    """列出所有存储的 API Key"""
    keys = get_all_keys_db()
    if not keys:
        console.print("[yellow]暂无存储的 API Key。请使用 'add' 命令添加。[/yellow]")
        return

    table = Table(title="存储的 API Keys", show_lines=True)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")
    table.add_column("Description", style="green")

    for name, value, desc in keys:
        # 简单的脱敏处理
        if show_values:
            display_value = value
        else:
            if len(value) > 8:
                display_value = value[:4] + "*" * 4 + value[-4:]
            else:
                display_value = "*" * 8
                
        table.add_row(name, display_value, desc)

    console.print(table)


@cli.command()
@click.argument('query')
def get(query):
    """
    获取一个 API Key。
    支持：精确查询、模糊纠错 (typo)、语义描述查询。
    """
    # 1. 尝试精确匹配
    result = get_key_db(query)
    if result:
        name, value, desc = result
        console.print(f"\n[bold cyan]Found:[/bold cyan] {name}")
        console.print(f"[bold magenta]Value:[/bold magenta] {value}")
        console.print(f"[dim]Description: {desc}[/dim]\n")
        return

    # 获取所有数据用于后续匹配
    all_data = get_all_keys_db()
    all_names = [row[0] for row in all_data]

    # 2. 尝试“语义”/关键词搜索 (搜索描述字段)
    semantic_matches = semantic_search(query, all_data)
    if semantic_matches:
        console.print(f"\n[yellow]未找到精确名称 '{query}'，但在描述或名称中找到了匹配项：[/yellow]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="green")
        
        for name, val, desc in semantic_matches:
            table.add_row(name, desc)
        console.print(table)
        
        # 如果只有一个匹配项，便捷地询问是否直接显示
        if len(semantic_matches) == 1:
            if Confirm.ask(f"是否显示 [cyan]{semantic_matches[0][0]}[/cyan] 的值?"):
                console.print(f"[bold magenta]Value:[/bold magenta] {semantic_matches[0][1]}")
        return

    # 3. 尝试模糊名称修正 (类似 thefuck)
    suggestion = find_similar_key(query, all_names)
    if suggestion:
        console.print(f"\n[red]未找到 Key: '{query}'[/red]")
        console.print(f"[bold green]➜ 您是不是要找: '{suggestion}' ?[/bold green]")
        
        if Confirm.ask("是否显示这个 Key 的信息?"):
            res = get_key_db(suggestion)
            console.print(f"[bold magenta]Value:[/bold magenta] {res[1]}")
            console.print(f"[dim]Description: {res[2]}[/dim]")
        return

    console.print(f"[red]✘ 未能找到与 '{query}' 相关的 Key 或建议。[/red]")

if __name__ == '__main__':
    cli()