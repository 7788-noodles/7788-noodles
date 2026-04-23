import re
import os
import io
import base64
import requests
import subprocess
import json
from flask import Flask, request, jsonify
from config import API_KEY, SECRET_KEY,BAILIAN_API_KEY
from imageio_ffmpeg import get_ffmpeg_exe
from openai import OpenAI

app = Flask(__name__)

bailian_client = OpenAI(
    # api_key="自己的真实 key。",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

def convert_mp3_bytes_to_wav_bytes(mp3_bytes):
    ffmpeg_path = get_ffmpeg_exe()
    cmd = [
        ffmpeg_path,
        "-i", "pipe:0",
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        "-f", "wav",
        "pipe:1"
    ]

    result = subprocess.run(
        cmd,
        input=mp3_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True
    )
    return result.stdout

def get_access_token():
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": API_KEY,
        "client_secret": SECRET_KEY
    }
    resp = requests.post(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return data.get("access_token", "")

def chinese_to_number(text_num):
    digit_map = {
        "零": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4,
        "五": 5, "六": 6, "七": 7, "八": 8, "九": 9
    }

    if text_num in digit_map:
        return digit_map[text_num]

    if text_num == "十":
        return 10

    if "十" in text_num:
        parts = text_num.split("十")
        left = parts[0]
        right = parts[1]

        tens = digit_map.get(left, 1) if left != "" else 1
        ones = digit_map.get(right, 0) if right != "" else 0
        return tens * 10 + ones

    return 0


def extract_amount(text):
    num_match = re.search(r'(\d+(\.\d+)?)', text)
    if num_match:
        return float(num_match.group(1))

    zh_match = re.search(r'([零一二两三四五六七八九十]+)(元|块|块钱)', text)
    if zh_match:
        return float(chinese_to_number(zh_match.group(1)))

    return 0

def classify_category_with_ai_placeholder(text):
    """
    现在这里已经不是纯占位了，而是真正调用百炼做分类。
    如果模型调用失败，就自动退回到规则分类。
    """

    text = text.strip()

    fallback_result = {
        "category": "其他",
        "remark": text
    }

    # 先准备一个简单的规则兜底
    if any(word in text for word in ["吃", "饭", "奶茶", "酸菜鱼", "火锅", "雪糕", "可乐", "早餐", "午饭", "晚饭"]):
        fallback_result = {"category": "餐饮", "remark": text}
    elif any(word in text for word in ["打车", "地铁", "公交", "高铁", "机票"]):
        fallback_result = {"category": "交通", "remark": text}
    elif any(word in text for word in ["买了", "下单", "衣服", "鞋", "裤子", "收纳盒", "文具", "日用品"]):
        fallback_result = {"category": "购物", "remark": text}

    try:
        prompt = f"""
你是一个记账分类助手。
请根据用户输入的消费描述，判断最合适的消费分类，并提取一个简短备注。

分类只能从以下选项中选一个：
餐饮、交通、购物、娱乐、学习、医疗、住房、其他

要求：
1. 只输出 JSON
2. 不要输出解释
3. JSON 格式必须是：
{{"category":"分类","remark":"简短备注"}}

用户输入：
{text}
        """.strip()

        response = bailian_client.chat.completions.create(
            model="qwen3.6-plus",
            messages=[
                {"role": "system", "content": "你是一个严格输出 JSON 的记账分类助手。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )

        content = response.choices[0].message.content.strip()
        print("百炼分类原始返回：", content)

        ai_result = json.loads(content)

        category = ai_result.get("category", "其他")
        remark = ai_result.get("remark", text)

        allowed_categories = ["餐饮", "交通", "购物", "娱乐", "学习", "医疗", "住房", "其他"]
        if category not in allowed_categories:
            category = "其他"

        return {
            "category": category,
            "remark": remark
        }

    except Exception as e:
        print("百炼分类失败，回退规则分类：", str(e))
        return fallback_result

def parse_text_to_bill(text):
    amount = extract_amount(text)

    # 这里以后可以直接替换成真正的大模型分类
    ai_result = classify_category_with_ai_placeholder(text)

    return {
        "type": "支出",
        "amount": amount,
        "category": ai_result["category"],
        "remark": ai_result["remark"]
    }

def analyze_bills_with_ai(bills):
    if not bills:
        return {
            "analysis": "当前还没有账单数据，因此暂时无法生成消费分析。",
            "suggestion": "可以先记录几笔日常消费，系统再为你生成更有针对性的消费建议。"
        }

    total_amount = sum(float(item.get("amount", 0) or 0) for item in bills)
    bill_count = len(bills)

    category_map = {}
    for item in bills:
        category = item.get("category", "其他") or "其他"
        amount = float(item.get("amount", 0) or 0)
        category_map[category] = category_map.get(category, 0) + amount

    category_stats = []
    for category, amount in category_map.items():
        percent = (amount / total_amount * 100) if total_amount > 0 else 0
        category_stats.append({
            "category": category,
            "amount": round(amount, 2),
            "percent": round(percent, 1)
        })

    category_stats.sort(key=lambda x: x["amount"], reverse=True)
    top_category = category_stats[0]["category"] if category_stats else "其他"

    recent_bills = bills[:3]

    summary_data = {
        "totalAmount": round(total_amount, 2),
        "billCount": bill_count,
        "topCategory": top_category,
        "categoryStats": category_stats,
        "recentBills": recent_bills
    }

    try:
        prompt = f"""
你是一个消费分析助手。
请根据用户的账单统计数据，生成简短、自然、友好的消费分析与建议。

要求：
1. 不要编造不存在的数据
2. 语言简洁自然
3. 输出必须是 JSON
4. JSON 格式必须为：
{{"analysis":"...","suggestion":"..."}}

用户账单统计数据：
{json.dumps(summary_data, ensure_ascii=False)}
        """.strip()

        response = bailian_client.chat.completions.create(
            model="qwen3.6-plus",
            messages=[
                {"role": "system", "content": "你是一个严格输出 JSON 的消费分析助手。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        content = response.choices[0].message.content.strip()
        print("百炼分析原始返回：", content)

        if content.startswith("```json"):
            content = content.replace("```json", "", 1).strip()

        if content.startswith("```"):
            content = content.replace("```", "", 1).strip()

        if content.endswith("```"):
            content = content[:-3].strip()

        ai_result = json.loads(content)

        analysis = ai_result.get("analysis", "")
        suggestion = ai_result.get("suggestion", "")

        return {
            "analysis": analysis,
            "suggestion": suggestion
        }

    except Exception as e:
        print("百炼分析失败，回退基础分析：", str(e))

        fallback_analysis = f"当前共记录 {bill_count} 笔账单，总支出为 {round(total_amount, 2)} 元，支出主要集中在 {top_category} 类别。"
        fallback_suggestion = f"建议重点关注 {top_category} 类支出，并逐步细化“其他”分类，提升后续统计分析的准确性。"

        return {
            "analysis": fallback_analysis,
            "suggestion": fallback_suggestion
        }

@app.route("/test_baidu_token", methods=["GET"])
def test_baidu_token():
    try:
        token = get_access_token()
        if not token:
            return jsonify({
                "success": False,
                "message": "没有获取到 access_token"
            })
        return jsonify({
            "success": True,
            "token_prefix": token[:20]
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        })

@app.route("/speech_to_text", methods=["POST"])
def speech_to_text():
    try:
        if "file" not in request.files:
            return jsonify({
                "success": False,
                "message": "没有上传文件"
            })

        audio_file = request.files["file"]
        file_bytes = audio_file.read()

        print("上传文件名：", audio_file.filename)
        print("原始音频字节大小：", len(file_bytes))

        if not file_bytes:
            return jsonify({
                "success": False,
                "message": "音频文件为空"
            })

        token = get_access_token()
        if not token:
            return jsonify({
                "success": False,
                "message": "获取百度 token 失败"
            })

        ext = os.path.splitext(audio_file.filename)[1].lower().replace(".", "")

        if ext == "mp3":
            final_bytes = convert_mp3_bytes_to_wav_bytes(file_bytes)
            audio_format = "wav"
            print("转换后 wav 字节大小：", len(final_bytes))
            with open("debug_output.wav", "wb") as f:
              f.write(final_bytes)
        else:
            final_bytes = file_bytes
            audio_format = ext if ext else "wav"

        speech = base64.b64encode(final_bytes).decode("utf-8")

        payload = {
            "format": audio_format,
            "rate": 16000,
            "channel": 1,
            "cuid": "miaomiao_wechat_app",
            "token": token,
            "dev_pid": 1537,
            "speech": speech,
            "len": len(final_bytes)
        }

        resp = requests.post(
            "http://vop.baidu.com/server_api",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=20
        )
        resp.raise_for_status()
        result = resp.json()

        if result.get("err_no") == 0:
            text = result.get("result", [""])[0].strip()
            print("百度识别完整返回：", result)
            print("识别出的 text：", repr(text))
            return jsonify({
                "success": True,
                "text": text
            })
        else:
            print("百度识别失败返回：", result)
            return jsonify({
                "success": False,
                "message": result.get("err_msg", "语音识别失败"),
                "baidu_result": result
            })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        })

@app.route("/parse_bill", methods=["POST"])
def parse_bill():
    data = request.get_json()
    text = data.get("text", "").strip()

    if not text:
        return jsonify({
            "success": False,
            "message": "text is empty"
        })

    result = parse_text_to_bill(text)

    return jsonify({
        "success": True,
        "data": result
    })

@app.route("/analyze_bills", methods=["POST"])
def analyze_bills():
    try:
        data = request.get_json()
        bills = data.get("bills", [])

        result = analyze_bills_with_ai(bills)

        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        })
        
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)