import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE_DIR = os.path.join(BASE_DIR, "workspace")


def ensure_workspace():
    """确保 workspace 目录存在。"""
    os.makedirs(WORKSPACE_DIR, exist_ok=True)


def get_safe_path(relative_path):
    """
    把用户输入的相对路径转成安全的绝对路径。
    只允许操作 workspace 目录中的文件。
    """
    ensure_workspace()

    if not relative_path or not relative_path.strip():
        raise ValueError("文件路径不能为空")

    relative_path = relative_path.strip().replace("\\", "/")
    full_path = os.path.abspath(os.path.join(WORKSPACE_DIR, relative_path))
    workspace_abs = os.path.abspath(WORKSPACE_DIR)

    # 防止用户写 ../../ 逃出 workspace
    if not full_path.startswith(workspace_abs):
        raise ValueError("不允许访问 workspace 目录之外的文件")

    return full_path


def create_file(file_path, content=""):
    """
    创建一个新文件。
    如果父目录不存在，会自动创建。
    如果文件已存在，则报错。
    """
    safe_path = get_safe_path(file_path)

    if os.path.exists(safe_path):
        raise ValueError(f"文件已存在: {file_path}")

    parent_dir = os.path.dirname(safe_path)
    os.makedirs(parent_dir, exist_ok=True)

    with open(safe_path, "w", encoding="utf-8") as f:
        f.write(content)

    return {
        "message": "文件创建成功",
        "file_path": file_path,
        "absolute_path": safe_path,
    }


def read_file(file_path):
    """
    读取文件内容。
    """
    safe_path = get_safe_path(file_path)

    if not os.path.exists(safe_path):
        raise ValueError(f"文件不存在: {file_path}")

    if os.path.isdir(safe_path):
        raise ValueError(f"这是一个目录，不是文件: {file_path}")

    with open(safe_path, "r", encoding="utf-8") as f:
        content = f.read()

    return {
        "file_path": file_path,
        "content": content,
    }


def overwrite_file(file_path, content):
    """
    覆盖写入文件。
    如果文件不存在，会自动创建。
    """
    safe_path = get_safe_path(file_path)

    parent_dir = os.path.dirname(safe_path)
    os.makedirs(parent_dir, exist_ok=True)

    with open(safe_path, "w", encoding="utf-8") as f:
        f.write(content)

    return {
        "message": "文件已覆盖写入",
        "file_path": file_path,
        "absolute_path": safe_path,
    }


def append_file(file_path, content):
    """
    追加写入文件。
    如果文件不存在，会自动创建。
    """
    safe_path = get_safe_path(file_path)

    parent_dir = os.path.dirname(safe_path)
    os.makedirs(parent_dir, exist_ok=True)

    with open(safe_path, "a", encoding="utf-8") as f:
        f.write(content)

    return {
        "message": "内容已追加到文件末尾",
        "file_path": file_path,
        "absolute_path": safe_path,
    }


def replace_in_file(file_path, old_text, new_text):
    """
    替换文件中的指定文本。
    """
    if old_text == "":
        raise ValueError("old_text 不能为空")

    safe_path = get_safe_path(file_path)

    if not os.path.exists(safe_path):
        raise ValueError(f"文件不存在: {file_path}")

    if os.path.isdir(safe_path):
        raise ValueError(f"这是一个目录，不是文件: {file_path}")

    with open(safe_path, "r", encoding="utf-8") as f:
        content = f.read()

    if old_text not in content:
        raise ValueError("文件中没有找到要替换的内容")

    new_content = content.replace(old_text, new_text)

    with open(safe_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    return {
        "message": "文件内容替换成功",
        "file_path": file_path,
        "absolute_path": safe_path,
    }


def list_files(sub_dir=""):
    """
    列出 workspace 或其子目录中的文件和文件夹。
    """
    safe_path = get_safe_path(sub_dir) if sub_dir else WORKSPACE_DIR

    if not os.path.exists(safe_path):
        raise ValueError(f"目录不存在: {sub_dir}")

    if not os.path.isdir(safe_path):
        raise ValueError(f"不是目录: {sub_dir}")

    items = []
    for name in sorted(os.listdir(safe_path)):
        item_path = os.path.join(safe_path, name)
        items.append({
            "name": name,
            "type": "dir" if os.path.isdir(item_path) else "file"
        })

    return {
        "dir": sub_dir if sub_dir else ".",
        "items": items
    }


def format_file_list(result):
    """
    把 list_files 的结果格式化成字符串。
    """
    lines = [f"目录 {result['dir']} 的内容："]

    if not result["items"]:
        lines.append("（空目录）")
        return "\n".join(lines)

    for item in result["items"]:
        prefix = "[目录]" if item["type"] == "dir" else "[文件]"
        lines.append(f"{prefix} {item['name']}")

    return "\n".join(lines)