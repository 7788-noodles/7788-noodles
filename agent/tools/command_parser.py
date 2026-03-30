import re

from tools.todo_tools import (
    add_todo,
    list_todos,
    mark_todo_done,
    delete_todo,
    format_todos,
    normalize_date_label,
)
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


def extract_after_prefix(text, prefixes):
    for prefix in prefixes:
        if text.startswith(prefix):
            return text[len(prefix):].strip()
    return None


def chinese_digit_to_int(ch):
    mapping = {
        "零": 0, "〇": 0,
        "一": 1, "二": 2, "两": 2, "三": 3, "四": 4,
        "五": 5, "六": 6, "七": 7, "八": 8, "九": 9,
    }
    return mapping.get(ch)


def parse_chinese_hour(text):
    """
    支持：
    一点 / 两点 / 三点 / 九点 / 十点 / 十一点 / 十二点
    """
    text = text.strip()

    if text == "十":
        return 10
    if text == "十一":
        return 11
    if text == "十二":
        return 12

    if len(text) == 1:
        value = chinese_digit_to_int(text)
        if value is not None:
            return value

    return None


def normalize_time(hour, minute=0, period=None):
    """
    把小时分钟格式化成 HH:MM
    period 可选：上午 / 早上 / 中午 / 下午 / 晚上
    """
    if hour is None:
        return ""

    hour = int(hour)
    minute = int(minute)

    if period in ["下午", "晚上"]:
        if 1 <= hour <= 11:
            hour += 12
    elif period == "中午":
        if 1 <= hour <= 10:
            hour += 12

    if hour == 24:
        hour = 0

    return f"{hour:02d}:{minute:02d}"


def extract_date_and_time(task_text):
    """
    从任务文本里提取：
    - date_label: 今天 / 明天 / 后天
    - date_value: YYYY-MM-DD
    - time_text: HH:MM
    - cleaned_task: 去掉日期时间后的任务内容
    """
    text = task_text.strip()

    date_label = ""
    date_value = ""
    time_text = ""

    # 1. 提取日期
    date_match = re.search(r"(今天|明天|后天)", text)
    if date_match:
        date_label = date_match.group(1)
        date_value = normalize_date_label(date_label)
        text = re.sub(r"(今天|明天|后天)", "", text, count=1).strip()

    # 2. 提取 24 小时制时间，例如 14:30 或 9:05
    match_hm = re.search(r"\b(\d{1,2}):(\d{2})\b", text)
    if match_hm:
        hour = int(match_hm.group(1))
        minute = int(match_hm.group(2))
        time_text = f"{hour:02d}:{minute:02d}"
        text = text.replace(match_hm.group(0), "", 1).strip()
    else:
        # 3. 提取 “下午3点 / 晚上8点 / 上午9点 / 中午12点”
        match_period_num = re.search(r"(早上|上午|中午|下午|晚上)\s*(\d{1,2})点(?:([0-5]?\d)分)?", text)
        if match_period_num:
            period = match_period_num.group(1)
            hour = int(match_period_num.group(2))
            minute = int(match_period_num.group(3)) if match_period_num.group(3) else 0
            time_text = normalize_time(hour, minute, period)
            text = text.replace(match_period_num.group(0), "", 1).strip()
        else:
            # 4. 提取 “下午三点 / 晚上八点 / 上午九点”
            match_period_cn = re.search(r"(早上|上午|中午|下午|晚上)\s*(十|十一|十二|[一二两三四五六七八九])点", text)
            if match_period_cn:
                period = match_period_cn.group(1)
                hour_cn = match_period_cn.group(2)
                hour = parse_chinese_hour(hour_cn)
                if hour is not None:
                    time_text = normalize_time(hour, 0, period)
                    text = text.replace(match_period_cn.group(0), "", 1).strip()
            else:
                # 5. 提取 “9点”
                match_num_only = re.search(r"\b(\d{1,2})点(?:([0-5]?\d)分)?", text)
                if match_num_only:
                    hour = int(match_num_only.group(1))
                    minute = int(match_num_only.group(2)) if match_num_only.group(2) else 0
                    time_text = normalize_time(hour, minute, None)
                    text = text.replace(match_num_only.group(0), "", 1).strip()
                else:
                    # 6. 提取 “三点”
                    match_cn_only = re.search(r"(十|十一|十二|[一二两三四五六七八九])点", text)
                    if match_cn_only:
                        hour_cn = match_cn_only.group(1)
                        hour = parse_chinese_hour(hour_cn)
                        if hour is not None:
                            time_text = normalize_time(hour, 0, None)
                            text = text.replace(match_cn_only.group(0), "", 1).strip()

    # 去掉可能残留的多余空格
    text = re.sub(r"\s+", " ", text).strip()

    return {
        "date_label": date_label,
        "date_value": date_value,
        "time_text": time_text,
        "cleaned_task": text,
    }


def handle_todo_command(command):
    """
    处理待办相关命令。
    支持示例：
    - 帮我添加一个待办：明天下午三点开组会
    - 添加待办：今天晚上健身
    - 添加待办：后天早上9点去医院
    - 添加待办：买牛奶
    - 查看待办
    - 查看未完成待办
    - 标记待办完成 1
    - 删除待办 2
    """
    text = command.strip()

    add_prefixes = [
        "帮我添加一个待办：",
        "帮我添加待办：",
        "添加一个待办：",
        "添加待办：",
    ]
    task = extract_after_prefix(text, add_prefixes)
    if task is not None:
        parsed = extract_date_and_time(task)
        cleaned_task = parsed["cleaned_task"]

        if not cleaned_task:
            raise ValueError("没有识别到有效的任务内容")

        todo = add_todo(
            task=cleaned_task,
            date=parsed["date_value"],
            time_text=parsed["time_text"],
            priority="medium",
        )
        return "已为你添加待办：\n" + format_todos([todo])

    if text in ["查看待办", "查看我的待办", "列出待办", "显示待办"]:
        todos = list_todos()
        return format_todos(todos)

    if text in ["查看未完成待办", "查看未完成的待办", "列出未完成待办"]:
        todos = list_todos(only_undone=True)
        return format_todos(todos)

    match_done = re.match(r"^标记待办完成\s+(\d+)$", text)
    if match_done:
        todo_id = int(match_done.group(1))
        todo = mark_todo_done(todo_id)
        return "已标记完成：\n" + format_todos([todo])

    match_delete = re.match(r"^删除待办\s+(\d+)$", text)
    if match_delete:
        todo_id = int(match_delete.group(1))
        result = delete_todo(todo_id)
        return f"删除成功，已删除任务 id = {result['deleted_id']}"

    return None


def handle_weather_command(command):
    text = command.strip()

    weather_prefixes = [
        "查询",
        "查看",
    ]

    for prefix in weather_prefixes:
        if text.startswith(prefix) and text.endswith("天气"):
            city = text[len(prefix):-2].strip()
            if city:
                weather_data = get_weather(city)
                return format_weather(weather_data)

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

            if city:
                plan = plan_trip(city, day_label=day_label)
                return format_trip_plan(plan)

    return None


def handle_file_command(command):
    text = command.strip()

    match_create = re.match(r"^创建文件\s+(.+?)\s+内容：(.*)$", text)
    if match_create:
        file_path = match_create.group(1).strip()
        content = match_create.group(2)
        result = create_file(file_path, content)
        return f"{result['message']}: {result['file_path']}"

    match_read = re.match(r"^读取文件\s+(.+)$", text)
    if match_read:
        file_path = match_read.group(1).strip()
        result = read_file(file_path)
        return f"文件: {result['file_path']}\n--------------------\n{result['content']}\n--------------------"

    match_overwrite = re.match(r"^覆盖写入\s+(.+?)\s+内容：(.*)$", text)
    if match_overwrite:
        file_path = match_overwrite.group(1).strip()
        content = match_overwrite.group(2)
        result = overwrite_file(file_path, content)
        return f"{result['message']}: {result['file_path']}"

    match_append = re.match(r"^追加写入\s+(.+?)\s+内容：(.*)$", text)
    if match_append:
        file_path = match_append.group(1).strip()
        content = match_append.group(2)
        result = append_file(file_path, content)
        return f"{result['message']}: {result['file_path']}"

    match_replace = re.match(r'^替换文件\s+(.+?)\s+里的\s+"(.*?)"\s+为\s+"(.*?)"$', text)
    if match_replace:
        file_path = match_replace.group(1).strip()
        old_text = match_replace.group(2)
        new_text = match_replace.group(3)
        result = replace_in_file(file_path, old_text, new_text)
        return f"{result['message']}: {result['file_path']}"

    if text in ["查看文件列表", "列出文件", "查看工作区文件"]:
        result = list_files("")
        return format_file_list(result)

    match_list_dir = re.match(r"^查看目录\s+(.+)$", text)
    if match_list_dir:
        sub_dir = match_list_dir.group(1).strip()
        result = list_files(sub_dir)
        return format_file_list(result)

    return None


def handle_help_command(command):
    text = command.strip()
    if text not in ["帮助", "help", "Help", "HELP"]:
        return None

    return (
        "你可以这样输入命令：\n"
        "\n"
        "【待办】\n"
        "添加待办：帮我添加一个待办：明天下午三点开组会\n"
        "添加待办：添加待办：今天晚上健身\n"
        "添加待办：添加待办：后天早上9点去医院\n"
        "添加待办：添加待办：明天 14:30 和导师开会\n"
        "查看待办：查看待办\n"
        "查看未完成待办：查看未完成待办\n"
        "标记完成：标记待办完成 1\n"
        "删除待办：删除待办 2\n"
        "\n"
        "【天气】\n"
        "查询天气：查询东京天气\n"
        "规划今天出行：规划上海今天出行\n"
        "规划明天出行：规划东京明天出行\n"
        "规划后天出行：帮我规划北京后天出行\n"
        "\n"
        "【文件】\n"
        "创建文件：创建文件 notes/today.txt 内容：今天要写作业\n"
        "读取文件：读取文件 notes/today.txt\n"
        "覆盖写入：覆盖写入 notes/today.txt 内容：新的内容\n"
        "追加写入：追加写入 notes/today.txt 内容：补充内容\n"
        "替换内容：替换文件 notes/today.txt 里的 \"旧内容\" 为 \"新内容\"\n"
        "查看文件列表：查看文件列表\n"
        "查看目录：查看目录 notes\n"
        "\n"
        "【多步骤任务】\n"
        "查询天气并规划出行：帮我查询东京天气并规划出行\n"
        "查询天气并规划明天出行：帮我查询东京天气并规划明天出行\n"
        "查看待办并保存到文件：帮我查看未完成待办并保存到文件 reports/todos.txt\n"
        "查询天气并写入文件：帮我查询上海天气并写入文件 reports/weather.txt\n"
        "规划出行并追加写入文件：帮我规划北京明天出行并追加写入文件 reports/trip.txt\n"
        "\n"
        "输入 exit 或 退出 可以结束程序。"
    )


def run_single_command(command):
    handlers = [
        handle_help_command,
        handle_todo_command,
        handle_weather_command,
        handle_file_command,
    ]

    for handler in handlers:
        result = handler(command)
        if result is not None:
            return result

    return None


def handle_multi_step_command(command):
    text = command.strip()

    match_weather_trip = re.match(r"^帮我查询(.+?)天气并规划(今天|明天|后天)?出行$", text)
    if match_weather_trip:
        city = match_weather_trip.group(1).strip()
        day_label = match_weather_trip.group(2) if match_weather_trip.group(2) else "今天"

        weather_result = run_single_command(f"查询{city}天气")
        trip_result = run_single_command(f"规划{city}{day_label}出行")

        return (
            f"我已经为你完成两个步骤：\n"
            f"\n"
            f"【步骤 1：查询天气】\n{weather_result}\n"
            f"\n"
            f"【步骤 2：规划出行】\n{trip_result}"
        )

    match_todo_save = re.match(r"^帮我查看未完成待办并保存到文件\s+(.+)$", text)
    if match_todo_save:
        file_path = match_todo_save.group(1).strip()
        todo_result = run_single_command("查看未完成待办")
        overwrite_result = overwrite_file(file_path, todo_result)

        return (
            f"我已经为你完成两个步骤：\n"
            f"\n"
            f"【步骤 1：查看未完成待办】\n{todo_result}\n"
            f"\n"
            f"【步骤 2：保存到文件】\n{overwrite_result['message']}: {overwrite_result['file_path']}"
        )

    match_weather_save = re.match(r"^帮我查询(.+?)天气并写入文件\s+(.+)$", text)
    if match_weather_save:
        city = match_weather_save.group(1).strip()
        file_path = match_weather_save.group(2).strip()

        weather_result = run_single_command(f"查询{city}天气")
        overwrite_result = overwrite_file(file_path, weather_result)

        return (
            f"我已经为你完成两个步骤：\n"
            f"\n"
            f"【步骤 1：查询天气】\n{weather_result}\n"
            f"\n"
            f"【步骤 2：写入文件】\n{overwrite_result['message']}: {overwrite_result['file_path']}"
        )

    match_trip_append = re.match(r"^帮我规划(.+?)(今天|明天|后天)?出行并追加写入文件\s+(.+)$", text)
    if match_trip_append:
        city = match_trip_append.group(1).strip()
        day_label = match_trip_append.group(2) if match_trip_append.group(2) else "今天"
        file_path = match_trip_append.group(3).strip()

        trip_result = run_single_command(f"规划{city}{day_label}出行")
        append_result = append_file(file_path, trip_result + "\n")

        return (
            f"我已经为你完成两个步骤：\n"
            f"\n"
            f"【步骤 1：规划出行】\n{trip_result}\n"
            f"\n"
            f"【步骤 2：追加写入文件】\n{append_result['message']}: {append_result['file_path']}"
        )

    return None


def process_command(command):
    multi_result = handle_multi_step_command(command)
    if multi_result is not None:
        return multi_result

    single_result = run_single_command(command)
    if single_result is not None:
        return single_result

    return (
        "我暂时没有理解这条命令。\n"
        "你可以输入 帮助 查看支持的命令格式。"
    )