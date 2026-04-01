import json
import urllib.parse
import urllib.request


GEOCODING_API = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_API = "https://api.open-meteo.com/v1/forecast"

# 常见城市别名和国家偏好，避免“东京被匹配到中国”这类问题
CITY_ALIASES = {
    "东京": {"query": "Tokyo", "country_code": "JP"},
    "tokyo": {"query": "Tokyo", "country_code": "JP"},
    "大阪": {"query": "Osaka", "country_code": "JP"},
    "osaka": {"query": "Osaka", "country_code": "JP"},
    "京都": {"query": "Kyoto", "country_code": "JP"},
    "kyoto": {"query": "Kyoto", "country_code": "JP"},
    "上海": {"query": "Shanghai", "country_code": "CN"},
    "shanghai": {"query": "Shanghai", "country_code": "CN"},
    "北京": {"query": "Beijing", "country_code": "CN"},
    "beijing": {"query": "Beijing", "country_code": "CN"},
    "广州": {"query": "Guangzhou", "country_code": "CN"},
    "guangzhou": {"query": "Guangzhou", "country_code": "CN"},
}

# 关键修复：拦截明显不是地球城市的词
INVALID_NON_CITY_NAMES = {
    "火星", "mars",
    "月球", "moon",
    "木星", "jupiter",
    "土星", "saturn",
    "金星", "venus",
    "水星", "mercury",
    "天王星", "uranus",
    "海王星", "neptune",
    "冥王星", "pluto",
    "太阳", "sun",
}


def fetch_json(url):
    """请求一个 URL 并返回 JSON。"""
    with urllib.request.urlopen(url, timeout=15) as response:
        data = response.read().decode("utf-8")
        return json.loads(data)


def validate_city_input(city):
    """
    拦截明显不是地球城市的输入，避免把 Mars 这类词误匹配成地球上的同名地点。
    """
    if not city or not city.strip():
        raise ValueError("city 不能为空")

    city_clean = city.strip().lower()
    if city_clean in INVALID_NON_CITY_NAMES:
        raise ValueError(f"没有找到城市: {city.strip()}")

    return city.strip()


def normalize_city_input(city):
    """
    规范化用户输入，返回：
    - query: 真正用于 geocoding 搜索的关键词
    - preferred_country: 优先国家代码，可为 None
    """
    city = validate_city_input(city)
    city_lower = city.lower()

    if city_lower in CITY_ALIASES:
        item = CITY_ALIASES[city_lower]
        return item["query"], item["country_code"]

    return city, None


def choose_best_location(results, original_query, preferred_country=None):
    """
    从 geocoding 返回的多个候选结果里挑一个最合适的。
    规则：
    1. 如果有 preferred_country，优先该国家
    2. 优先名字完全匹配
    3. 再按人口从大到小排序
    """
    if not results:
        raise ValueError("没有找到匹配地点")

    query_lower = original_query.strip().lower()

    candidates = results

    if preferred_country is not None:
        filtered = [
            r for r in results
            if str(r.get("country_code", "")).upper() == preferred_country.upper()
        ]
        if filtered:
            candidates = filtered

    exact_matches = [
        r for r in candidates
        if r.get("name", "").strip().lower() == query_lower
    ]

    if exact_matches:
        exact_matches.sort(key=lambda r: r.get("population", 0), reverse=True)
        return exact_matches[0]

    candidates.sort(key=lambda r: r.get("population", 0), reverse=True)
    return candidates[0]


def get_location_by_city(city):
    """
    通过城市名查询经纬度。
    返回:
        {
            "name": "Tokyo",
            "country": "Japan",
            "country_code": "JP",
            "latitude": 35.6895,
            "longitude": 139.69171,
            "timezone": "Asia/Tokyo"
        }
    """
    query, preferred_country = normalize_city_input(city)

    params = {
        "name": query,
        "count": 5,
        "language": "zh",
        "format": "json"
    }

    if preferred_country is not None:
        params["countryCode"] = preferred_country

    url = f"{GEOCODING_API}?{urllib.parse.urlencode(params)}"
    data = fetch_json(url)

    results = data.get("results", [])
    if not results:
        raise ValueError(f"没有找到城市: {city}")

    item = choose_best_location(
        results=results,
        original_query=query,
        preferred_country=preferred_country,
    )

    return {
        "name": item.get("name", city),
        "country": item.get("country", ""),
        "country_code": item.get("country_code", ""),
        "latitude": item["latitude"],
        "longitude": item["longitude"],
        "timezone": item.get("timezone", "auto")
    }


def weather_code_to_text(code):
    """
    Open-Meteo 的 weather_code 转中文描述。
    """
    mapping = {
        0: "晴朗",
        1: "大致晴",
        2: "局部多云",
        3: "阴天",
        45: "有雾",
        48: "有雾并有霜",
        51: "小毛毛雨",
        53: "毛毛雨",
        55: "强毛毛雨",
        56: "冻毛毛雨",
        57: "强冻毛毛雨",
        61: "小雨",
        63: "中雨",
        65: "大雨",
        66: "冻雨",
        67: "强冻雨",
        71: "小雪",
        73: "中雪",
        75: "大雪",
        77: "雪粒",
        80: "小阵雨",
        81: "中阵雨",
        82: "强阵雨",
        85: "小阵雪",
        86: "强阵雪",
        95: "雷暴",
        96: "雷暴伴小冰雹",
        99: "雷暴伴大冰雹",
    }
    return mapping.get(code, f"未知天气代码({code})")


def get_weather(city):
    """
    按城市查询未来几天的天气。
    返回结构化 dict。
    """
    location = get_location_by_city(city)

    params = {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "timezone": "auto",
        "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        "forecast_days": 3
    }

    url = f"{FORECAST_API}?{urllib.parse.urlencode(params)}"
    data = fetch_json(url)

    current = data.get("current", {})
    daily = data.get("daily", {})

    forecast = []
    dates = daily.get("time", [])
    codes = daily.get("weather_code", [])
    max_temps = daily.get("temperature_2m_max", [])
    min_temps = daily.get("temperature_2m_min", [])
    rain_probs = daily.get("precipitation_probability_max", [])

    for i in range(len(dates)):
        forecast.append({
            "date": dates[i],
            "weather_code": codes[i],
            "weather_text": weather_code_to_text(codes[i]),
            "temp_max": max_temps[i],
            "temp_min": min_temps[i],
            "precipitation_probability_max": rain_probs[i]
        })

    return {
        "city": location["name"],
        "country": location["country"],
        "country_code": location["country_code"],
        "timezone": location["timezone"],
        "current": {
            "temperature": current.get("temperature_2m"),
            "apparent_temperature": current.get("apparent_temperature"),
            "weather_code": current.get("weather_code"),
            "weather_text": weather_code_to_text(current.get("weather_code")),
            "wind_speed": current.get("wind_speed_10m")
        },
        "forecast": forecast
    }


def format_weather(weather_data):
    """
    把天气结果格式化成更容易读的字符串。
    """
    lines = []
    lines.append(
        f"{weather_data['city']}, {weather_data['country']} ({weather_data.get('country_code', '')}) 的天气："
    )

    current = weather_data["current"]
    lines.append(
        f"当前：{current['weather_text']} | 气温: {current['temperature']}°C | "
        f"体感: {current['apparent_temperature']}°C | 风速: {current['wind_speed']} km/h"
    )

    lines.append("未来天气：")
    for day in weather_data["forecast"]:
        lines.append(
            f"{day['date']} | {day['weather_text']} | "
            f"最高 {day['temp_max']}°C / 最低 {day['temp_min']}°C | "
            f"降水概率 {day['precipitation_probability_max']}%"
        )

    return "\n".join(lines)