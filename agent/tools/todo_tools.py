import json
import os
from datetime import datetime, timedelta


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
TODO_FILE = os.path.join(DATA_DIR, "todos.json")


def ensure_todo_file():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(TODO_FILE):
        with open(TODO_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)


def load_todos():
    ensure_todo_file()
    with open(TODO_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_todos(todos):
    with open(TODO_FILE, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)


def normalize_date_label(date_label):
    """
    把 今天 / 明天 / 后天 转成 YYYY-MM-DD
    未提供时返回空字符串
    """
    if not date_label:
        return ""

    today = datetime.now().date()

    if date_label == "今天":
        target_date = today
    elif date_label == "明天":
        target_date = today + timedelta(days=1)
    elif date_label == "后天":
        target_date = today + timedelta(days=2)
    else:
        raise ValueError("目前只支持：今天、明天、后天")

    return target_date.strftime("%Y-%m-%d")


def add_todo(task, date="", priority="medium", time_text=""):
    if not task or not task.strip():
        raise ValueError("task 不能为空")

    if priority not in ["low", "medium", "high"]:
        raise ValueError("priority 必须是 low、medium 或 high")

    todos = load_todos()
    max_id = max((todo["id"] for todo in todos), default=0)

    new_todo = {
        "id": max_id + 1,
        "task": task.strip(),
        "date": date.strip(),
        "time": time_text.strip(),
        "priority": priority,
        "done": False,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    todos.append(new_todo)
    save_todos(todos)
    return new_todo


def list_todos(date=None, only_undone=False):
    todos = load_todos()
    result = []

    for todo in todos:
        if date is not None and todo.get("date", "") != date:
            continue
        if only_undone and todo["done"]:
            continue
        result.append(todo)

    return result


def mark_todo_done(todo_id):
    todos = load_todos()

    for todo in todos:
        if todo["id"] == todo_id:
            todo["done"] = True
            save_todos(todos)
            return todo

    raise ValueError(f"没有找到 id={todo_id} 的任务")


def delete_todo(todo_id):
    """
    删除某个待办，并把剩余任务的 id 重新排成连续编号。
    """
    todos = load_todos()

    found = False
    new_todos = []
    for todo in todos:
        if todo["id"] == todo_id:
            found = True
            continue
        new_todos.append(todo)

    if not found:
        raise ValueError(f"没有找到 id={todo_id} 的任务")

    # 关键修复：删除后重新编号，保证 id 连续
    for index, todo in enumerate(new_todos, start=1):
        todo["id"] = index

    save_todos(new_todos)
    return {"deleted_id": todo_id}


def format_todos(todos):
    if not todos:
        return "当前没有待办任务。"

    lines = ["待办列表："]
    for todo in todos:
        status = "已完成" if todo["done"] else "未完成"
        date_text = todo.get("date", "") if todo.get("date", "") else "未设置"
        time_text = todo.get("time", "") if todo.get("time", "") else "未设置"
        lines.append(
            f"[{todo['id']}] {todo['task']} | 日期: {date_text} | 时间: {time_text} | 优先级: {todo['priority']} | 状态: {status}"
        )

    return "\n".join(lines)