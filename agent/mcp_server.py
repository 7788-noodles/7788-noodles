import logging
import sys

from mcp.server.fastmcp import FastMCP

from tools.todo_tools import (
    add_todo,
    list_todos,
    mark_todo_done,
    delete_todo,
    format_todos,
    normalize_date_label,
)
from tools.command_parser import extract_date_and_time
from tools.weather_tools import get_weather, format_weather
from tools.trip_tools import plan_trip, format_trip_plan
from tools.file_tools import (
    create_file,
    read_file,
    overwrite_file,
    append_file,
    replace_in_file,
    list_files,
    format_file_list,
)

# 注意：
# MCP 官方文档强调，STDIO transport 下不要往 stdout 打印内容，
# 否则会破坏 JSON-RPC 消息。
# 所以这里把日志写到 stderr。
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

logger = logging.getLogger(__name__)

# 初始化 MCP Server
mcp = FastMCP("life-assistant")


# =========================
# 待办工具
# =========================

@mcp.tool()
def add_todo_tool(task_text: str, priority: str = "medium") -> str:
    """
    添加待办任务。
    这个工具支持从 task_text 中自动识别：
    - 今天 / 明天 / 后天
    - 简单时间，如 14:30、下午三点、早上9点

    Args:
        task_text: 原始任务文本，例如“明天下午三点开组会”
        priority: 优先级，可选 low / medium / high
    """
    parsed = extract_date_and_time(task_text)
    cleaned_task = parsed["cleaned_task"]

    if not cleaned_task:
        raise ValueError("没有识别到有效的任务内容")

    todo = add_todo(
        task=cleaned_task,
        date=parsed["date_value"],
        time_text=parsed["time_text"],
        priority=priority,
    )
    return format_todos([todo])


@mcp.tool()
def list_todos_tool(
    date_label: str = "",
    only_undone: bool = False,
) -> str:
    """
    查看待办任务。

    Args:
        date_label: 可选，支持“今天”“明天”“后天”，留空表示查看全部日期
        only_undone: 是否只看未完成任务
    """
    date_value = normalize_date_label(date_label) if date_label else None
    todos = list_todos(date=date_value, only_undone=only_undone)
    return format_todos(todos)


@mcp.tool()
def mark_todo_done_tool(todo_id: int) -> str:
    """
    把某个待办标记为已完成。

    Args:
        todo_id: 待办的 id
    """
    todo = mark_todo_done(todo_id)
    return format_todos([todo])


@mcp.tool()
def delete_todo_tool(todo_id: int) -> str:
    """
    删除某个待办。

    Args:
        todo_id: 待办的 id
    """
    result = delete_todo(todo_id)
    return f"删除成功，已删除任务 id = {result['deleted_id']}"


# =========================
# 天气工具
# =========================

@mcp.tool()
def get_weather_tool(city: str) -> str:
    """
    查询某个城市的天气。

    Args:
        city: 城市名，例如 东京 / Tokyo / 上海 / Beijing
    """
    weather_data = get_weather(city)
    return format_weather(weather_data)


@mcp.tool()
def plan_trip_tool(city: str, day_label: str = "今天") -> str:
    """
    根据天气规划今天 / 明天 / 后天的出行建议。

    Args:
        city: 城市名，例如 东京 / Tokyo / 上海
        day_label: 支持 今天 / 明天 / 后天
    """
    plan = plan_trip(city, day_label=day_label)
    return format_trip_plan(plan)


# =========================
# 文件工具
# =========================

@mcp.tool()
def create_file_tool(file_path: str, content: str = "") -> str:
    """
    在 workspace 目录中创建文件。

    Args:
        file_path: 相对路径，例如 notes/today.txt
        content: 初始文件内容
    """
    result = create_file(file_path, content)
    return f"{result['message']}: {result['file_path']}"


@mcp.tool()
def read_file_tool(file_path: str) -> str:
    """
    读取 workspace 目录中的文件内容。

    Args:
        file_path: 相对路径，例如 notes/today.txt
    """
    result = read_file(file_path)
    return f"文件: {result['file_path']}\n--------------------\n{result['content']}\n--------------------"


@mcp.tool()
def overwrite_file_tool(file_path: str, content: str) -> str:
    """
    覆盖写入 workspace 目录中的文件。
    文件不存在时会自动创建。

    Args:
        file_path: 相对路径，例如 notes/today.txt
        content: 新的完整内容
    """
    result = overwrite_file(file_path, content)
    return f"{result['message']}: {result['file_path']}"


@mcp.tool()
def append_file_tool(file_path: str, content: str) -> str:
    """
    在 workspace 目录中的文件末尾追加内容。
    文件不存在时会自动创建。

    Args:
        file_path: 相对路径，例如 notes/today.txt
        content: 要追加的内容
    """
    result = append_file(file_path, content)
    return f"{result['message']}: {result['file_path']}"


@mcp.tool()
def replace_in_file_tool(file_path: str, old_text: str, new_text: str) -> str:
    """
    替换文件中的文本。

    Args:
        file_path: 相对路径，例如 notes/today.txt
        old_text: 要替换的旧文本
        new_text: 替换后的新文本
    """
    result = replace_in_file(file_path, old_text, new_text)
    return f"{result['message']}: {result['file_path']}"


@mcp.tool()
def list_files_tool(sub_dir: str = "") -> str:
    """
    查看 workspace 根目录或某个子目录下的文件列表。

    Args:
        sub_dir: 子目录，留空表示 workspace 根目录
    """
    result = list_files(sub_dir)
    return format_file_list(result)


# =========================
# 多步骤工具
# =========================

@mcp.tool()
def weather_and_trip_tool(city: str, day_label: str = "今天") -> str:
    """
    一次完成两个步骤：
    1. 查询天气
    2. 规划出行

    Args:
        city: 城市名
        day_label: 今天 / 明天 / 后天
    """
    weather_result = get_weather_tool(city)
    trip_result = plan_trip_tool(city, day_label)

    return (
        f"我已经为你完成两个步骤：\n"
        f"\n"
        f"【步骤 1：查询天气】\n{weather_result}\n"
        f"\n"
        f"【步骤 2：规划出行】\n{trip_result}"
    )


@mcp.tool()
def save_undone_todos_to_file_tool(file_path: str) -> str:
    """
    一次完成两个步骤：
    1. 查看未完成待办
    2. 保存到文件

    Args:
        file_path: 保存到 workspace 中的相对路径
    """
    todo_result = list_todos_tool(only_undone=True)
    save_result = overwrite_file(file_path, todo_result)

    return (
        f"我已经为你完成两个步骤：\n"
        f"\n"
        f"【步骤 1：查看未完成待办】\n{todo_result}\n"
        f"\n"
        f"【步骤 2：保存到文件】\n{save_result['message']}: {save_result['file_path']}"
    )


@mcp.tool()
def save_weather_to_file_tool(city: str, file_path: str) -> str:
    """
    一次完成两个步骤：
    1. 查询天气
    2. 写入文件

    Args:
        city: 城市名
        file_path: 保存到 workspace 中的相对路径
    """
    weather_result = get_weather_tool(city)
    save_result = overwrite_file(file_path, weather_result)

    return (
        f"我已经为你完成两个步骤：\n"
        f"\n"
        f"【步骤 1：查询天气】\n{weather_result}\n"
        f"\n"
        f"【步骤 2：写入文件】\n{save_result['message']}: {save_result['file_path']}"
    )


@mcp.tool()
def append_trip_to_file_tool(city: str, file_path: str, day_label: str = "今天") -> str:
    """
    一次完成两个步骤：
    1. 规划出行
    2. 追加写入文件

    Args:
        city: 城市名
        file_path: 保存到 workspace 中的相对路径
        day_label: 今天 / 明天 / 后天
    """
    trip_result = plan_trip_tool(city, day_label)
    save_result = append_file(file_path, trip_result + "\n")

    return (
        f"我已经为你完成两个步骤：\n"
        f"\n"
        f"【步骤 1：规划出行】\n{trip_result}\n"
        f"\n"
        f"【步骤 2：追加写入文件】\n{save_result['message']}: {save_result['file_path']}"
    )


def main():
    logger.info("Starting MCP server: life-assistant")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()