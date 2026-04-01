from tools.weather_tools import get_weather


DATE_LABEL_TO_INDEX = {
    "今天": 0,
    "明天": 1,
    "后天": 2,
}


def suggest_clothing(temp_max, temp_min):
    avg_temp = (temp_max + temp_min) / 2

    if avg_temp >= 28:
        return "建议穿短袖、轻薄衣物，注意防晒和补水"
    elif avg_temp >= 20:
        return "建议穿薄外套或长袖，体感通常比较舒服"
    elif avg_temp >= 12:
        return "建议穿外套，早晚可能偏凉"
    else:
        return "建议穿厚外套，天气偏冷，注意保暖"


def suggest_umbrella(rain_prob):
    if rain_prob >= 70:
        return "强烈建议带伞，最好减少长时间户外活动"
    elif rain_prob >= 40:
        return "建议随身带伞，以防突然下雨"
    else:
        return "一般不用带伞，但仍可留意天气变化"


def suggest_transport(rain_prob, wind_speed, weather_text):
    if "雷暴" in weather_text or rain_prob >= 80:
        return "更适合地铁、公交或打车，不建议长时间步行"
    if wind_speed is not None and wind_speed >= 35:
        return "风比较大，建议优先公共交通，减少骑行"
    if rain_prob >= 40:
        return "建议优先地铁或公交，步行距离不要太长"
    return "天气整体还可以，步行和公共交通都比较合适"


def suggest_activity(rain_prob, temp_max, weather_text):
    if "雷暴" in weather_text:
        return "更适合安排室内活动，如商场、博物馆、咖啡馆"
    if rain_prob >= 70:
        return "建议以室内活动为主"
    if temp_max >= 32:
        return "天气偏热，户外活动尽量避开中午，优先早晚出门"
    if temp_max <= 8:
        return "天气偏冷，户外停留时间不宜过长"
    return "比较适合正常出行，可安排适量户外活动"


def normalize_day_label(day_label):
    """
    把今天 / 明天 / 后天 规范化成索引。
    """
    if day_label is None or day_label == "":
        return "今天", 0

    day_label = day_label.strip()
    if day_label not in DATE_LABEL_TO_INDEX:
        raise ValueError("目前只支持：今天、明天、后天")

    return day_label, DATE_LABEL_TO_INDEX[day_label]


def plan_trip(city, day_label="今天"):
    """
    根据天气做一个简单出行规划。
    支持：
    - 今天
    - 明天
    - 后天
    """
    normalized_label, forecast_index = normalize_day_label(day_label)

    weather_data = get_weather(city)
    forecast = weather_data.get("forecast", [])

    if forecast_index >= len(forecast):
        raise ValueError(
            f"天气预报天数不足，暂时无法提供“{normalized_label}”的出行规划"
        )

    target_day = forecast[forecast_index]
    current = weather_data["current"]

    temp_max = target_day["temp_max"]
    temp_min = target_day["temp_min"]
    rain_prob = target_day["precipitation_probability_max"]
    weather_text = target_day["weather_text"]

    # 当前风速只能从 current 里拿，所以这里仍沿用当前风速做参考
    wind_speed = current.get("wind_speed")

    plan = {
        "city": weather_data["city"],
        "country": weather_data["country"],
        "country_code": weather_data.get("country_code", ""),
        "day_label": normalized_label,
        "date": target_day["date"],
        "weather_text": weather_text,
        "temp_max": temp_max,
        "temp_min": temp_min,
        "rain_prob": rain_prob,
        "clothing": suggest_clothing(temp_max, temp_min),
        "umbrella": suggest_umbrella(rain_prob),
        "transport": suggest_transport(rain_prob, wind_speed, weather_text),
        "activity": suggest_activity(rain_prob, temp_max, weather_text),
    }
    return plan


def format_trip_plan(plan):
    lines = [
        f"{plan['city']}, {plan['country']} ({plan.get('country_code', '')}) 在{plan['day_label']}（{plan['date']}）的出行建议：",
        f"天气：{plan['weather_text']}",
        f"温度：最高 {plan['temp_max']}°C，最低 {plan['temp_min']}°C",
        f"降水概率：{plan['rain_prob']}%",
        "",
        f"穿衣建议：{plan['clothing']}",
        f"带伞建议：{plan['umbrella']}",
        f"交通建议：{plan['transport']}",
        f"活动建议：{plan['activity']}",
    ]
    return "\n".join(lines)