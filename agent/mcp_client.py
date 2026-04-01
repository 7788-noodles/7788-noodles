import asyncio
import json
import re

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


SERVER_PYTHON = r"C:\Users\14624\Desktop\softw\agent\.venv\Scripts\python.exe"
SERVER_SCRIPT = r"C:\Users\14624\Desktop\softw\agent\mcp_server.py"


def format_tool_result(result):
    """
    把 tool 返回结果尽量转成人能看的文本。
    """
    if hasattr(result, "content"):
        parts = []
        for item in result.content:
            if hasattr(item, "text"):
                parts.append(item.text)
            else:
                parts.append(str(item))
        return "\n".join(parts)

    return json.dumps(result, ensure_ascii=False, indent=2, default=str)


def print_help():
    print("\n=== 使用说明 ===")
    print("你可以直接输入自然语言命令，例如：")
    print("1. 查询东京天气")
    print("2. 规划东京明天出行")
    print("3. 添加待办：明天下午三点开组会")
    print("4. 查看待办")
    print("5. 查看未完成待办")
    print("6. 标记待办完成 1")
    print("7. 删除待办 2")
    print("8. 创建文件 notes/today.txt 内容：今天要写作业")
    print("9. 读取文件 notes/today.txt")
    print("10. 覆盖写入 notes/today.txt 内容：新的内容")
    print("11. 追加写入 notes/today.txt 内容：补充内容")
    print('12. 替换文件 notes/today.txt 里的 "旧内容" 为 "新内容"')
    print("13. 查看文件列表")
    print("14. 查看目录 notes")
    print("15. 帮我查询东京天气并规划明天出行")
    print("16. 帮我查看未完成待办并保存到文件 reports/todos.txt")
    print("17. 帮我查询上海天气并写入文件 reports/weather.txt")
    print("18. 帮我规划北京明天出行并追加写入文件 reports/trip.txt")
    print("\n输入 help 查看帮助，输入 q 退出。")


def extract_after_prefix(text, prefixes):
    for prefix in prefixes:
        if text.startswith(prefix):
            return text[len(prefix):].strip()
    return None


def parse_natural_command(command):
    """
    把自然语言命令解析成：
    {
        "tool_name": "...",
        "arguments": {...}
    }
    如果无法解析，返回 None
    """
    text = command.strip()

    if not text:
        return None

    # =========================
    # 多步骤命令
    # =========================

    match_weather_trip = re.match(r"^帮我查询(.+?)天气并规划(今天|明天|后天)?出行$", text)
    if match_weather_trip:
        city = match_weather_trip.group(1).strip()
        day_label = match_weather_trip.group(2) if match_weather_trip.group(2) else "今天"
        return {
            "tool_name": "weather_and_trip_tool",
            "arguments": {
                "city": city,
                "day_label": day_label,
            }
        }

    match_todo_save = re.match(r"^帮我查看未完成待办并保存到文件\s+(.+)$", text)
    if match_todo_save:
        file_path = match_todo_save.group(1).strip()
        return {
            "tool_name": "save_undone_todos_to_file_tool",
            "arguments": {
                "file_path": file_path,
            }
        }

    match_weather_save = re.match(r"^帮我查询(.+?)天气并写入文件\s+(.+)$", text)
    if match_weather_save:
        city = match_weather_save.group(1).strip()
        file_path = match_weather_save.group(2).strip()
        return {
            "tool_name": "save_weather_to_file_tool",
            "arguments": {
                "city": city,
                "file_path": file_path,
            }
        }

    match_trip_append = re.match(r"^帮我规划(.+?)(今天|明天|后天)?出行并追加写入文件\s+(.+)$", text)
    if match_trip_append:
        city = match_trip_append.group(1).strip()
        day_label = match_trip_append.group(2) if match_trip_append.group(2) else "今天"
        file_path = match_trip_append.group(3).strip()
        return {
            "tool_name": "append_trip_to_file_tool",
            "arguments": {
                "city": city,
                "file_path": file_path,
                "day_label": day_label,
            }
        }

    # =========================
    # 单步命令：待办
    # =========================

    add_prefixes = [
        "帮我添加一个待办：",
        "帮我添加待办：",
        "添加一个待办：",
        "添加待办：",
    ]
    task_text = extract_after_prefix(text, add_prefixes)
    if task_text is not None:
        return {
            "tool_name": "add_todo_tool",
            "arguments": {
                "task_text": task_text,
                "priority": "medium",
            }
        }

    if text in ["查看待办", "查看我的待办", "列出待办", "显示待办"]:
        return {
            "tool_name": "list_todos_tool",
            "arguments": {}
        }

    if text in ["查看未完成待办", "查看未完成的待办", "列出未完成待办"]:
        return {
            "tool_name": "list_todos_tool",
            "arguments": {
                "only_undone": True
            }
        }

    match_done = re.match(r"^标记待办完成\s+(\d+)$", text)
    if match_done:
        todo_id = int(match_done.group(1))
        return {
            "tool_name": "mark_todo_done_tool",
            "arguments": {
                "todo_id": todo_id
            }
        }

    match_delete = re.match(r"^删除待办\s+(\d+)$", text)
    if match_delete:
        todo_id = int(match_delete.group(1))
        return {
            "tool_name": "delete_todo_tool",
            "arguments": {
                "todo_id": todo_id
            }
        }

    # =========================
    # 单步命令：天气和出行
    # =========================

    weather_prefixes = ["查询", "查看"]
    for prefix in weather_prefixes:
        if text.startswith(prefix) and text.endswith("天气"):
            city = text[len(prefix):-2].strip()
            if city:
                return {
                    "tool_name": "get_weather_tool",
                    "arguments": {
                        "city": city
                    }
                }

    trip_patterns = [
        r"^规划(.+?)(今天|明天|后天)出行$",
        r"^帮我规划(.+?)(今天|明天|后天)出行$",
        r"^规划(.+?)出行$",
        r"^帮我规划(.+?)出行$",
    ]
    for pattern in trip_patterns:
        match = re.match(pattern, text)
        if match:
            if len(match.groups()) == 2:
                city = match.group(1).strip()
                day_label = match.group(2).strip()
            else:
                city = match.group(1).strip()
                day_label = "今天"

            return {
                "tool_name": "plan_trip_tool",
                "arguments": {
                    "city": city,
                    "day_label": day_label,
                }
            }

    # =========================
    # 单步命令：文件
    # =========================

    match_create = re.match(r"^创建文件\s+(.+?)\s+内容：(.*)$", text)
    if match_create:
        file_path = match_create.group(1).strip()
        content = match_create.group(2)
        return {
            "tool_name": "create_file_tool",
            "arguments": {
                "file_path": file_path,
                "content": content,
            }
        }

    match_read = re.match(r"^读取文件\s+(.+)$", text)
    if match_read:
        file_path = match_read.group(1).strip()
        return {
            "tool_name": "read_file_tool",
            "arguments": {
                "file_path": file_path,
            }
        }

    match_overwrite = re.match(r"^覆盖写入\s+(.+?)\s+内容：(.*)$", text)
    if match_overwrite:
        file_path = match_overwrite.group(1).strip()
        content = match_overwrite.group(2)
        return {
            "tool_name": "overwrite_file_tool",
            "arguments": {
                "file_path": file_path,
                "content": content,
            }
        }

    match_append = re.match(r"^追加写入\s+(.+?)\s+内容：(.*)$", text)
    if match_append:
        file_path = match_append.group(1).strip()
        content = match_append.group(2)
        return {
            "tool_name": "append_file_tool",
            "arguments": {
                "file_path": file_path,
                "content": content,
            }
        }

    match_replace = re.match(r'^替换文件\s+(.+?)\s+里的\s+"(.*?)"\s+为\s+"(.*?)"$', text)
    if match_replace:
        file_path = match_replace.group(1).strip()
        old_text = match_replace.group(2)
        new_text = match_replace.group(3)
        return {
            "tool_name": "replace_in_file_tool",
            "arguments": {
                "file_path": file_path,
                "old_text": old_text,
                "new_text": new_text,
            }
        }

    if text in ["查看文件列表", "列出文件", "查看工作区文件"]:
        return {
            "tool_name": "list_files_tool",
            "arguments": {}
        }

    match_list_dir = re.match(r"^查看目录\s+(.+)$", text)
    if match_list_dir:
        sub_dir = match_list_dir.group(1).strip()
        return {
            "tool_name": "list_files_tool",
            "arguments": {
                "sub_dir": sub_dir
            }
        }

    return None


async def natural_language_client():
    server_params = StdioServerParameters(
        command=SERVER_PYTHON,
        args=[SERVER_SCRIPT],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            print("=== MCP 自然语言客户端连接成功 ===")
            print_help()

            tools_result = await session.list_tools()
            tools = tools_result.tools
            tool_names = {tool.name for tool in tools}

            while True:
                user_input = input("\n请输入自然语言命令：").strip()

                if user_input.lower() in ["q", "quit", "exit", "退出"]:
                    print("程序已退出。")
                    break

                if user_input.lower() in ["help", "帮助"]:
                    print_help()
                    continue

                parsed = parse_natural_command(user_input)
                if parsed is None:
                    print("没有识别这条命令。输入 help 查看支持的命令。")
                    continue

                tool_name = parsed["tool_name"]
                arguments = parsed["arguments"]

                if tool_name not in tool_names:
                    print(f"工具不存在：{tool_name}")
                    continue

                print(f"\n=== 解析结果 ===")
                print(f"tool: {tool_name}")
                print("arguments:")
                print(json.dumps(arguments, ensure_ascii=False, indent=2))

                try:
                    result = await session.call_tool(
                        tool_name,
                        arguments=arguments,
                    )
                    print("\n=== 工具调用结果 ===")
                    print(format_tool_result(result))
                except Exception as e:
                    print(f"\n工具调用失败：{e}")


if __name__ == "__main__":
    asyncio.run(natural_language_client())