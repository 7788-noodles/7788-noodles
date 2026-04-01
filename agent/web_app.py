import asyncio
import json

from flask import Flask, jsonify, render_template, request
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from mcp_client import parse_natural_command, format_tool_result


SERVER_PYTHON = r"C:\Users\14624\Desktop\softw\agent\.venv\Scripts\python.exe"
SERVER_SCRIPT = r"C:\Users\14624\Desktop\softw\agent\mcp_server.py"

app = Flask(__name__)


async def call_mcp_tool_from_command(user_command: str):
    parsed = parse_natural_command(user_command)
    if parsed is None:
        return {
            "ok": False,
            "error": "没有识别这条命令。请换一种说法，或者输入更明确的命令。"
        }

    tool_name = parsed["tool_name"]
    arguments = parsed["arguments"]

    server_params = StdioServerParameters(
        command=SERVER_PYTHON,
        args=[SERVER_SCRIPT],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            tools_result = await session.list_tools()
            tool_names = {tool.name for tool in tools_result.tools}

            if tool_name not in tool_names:
                return {
                    "ok": False,
                    "error": f"工具不存在：{tool_name}"
                }

            result = await session.call_tool(tool_name, arguments=arguments)

            return {
                "ok": True,
                "tool_name": tool_name,
                "arguments": arguments,
                "result": format_tool_result(result),
            }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(silent=True) or {}
    user_command = (data.get("message") or "").strip()

    if not user_command:
        return jsonify({
            "ok": False,
            "error": "请输入命令。"
        }), 400

    try:
        result = asyncio.run(call_mcp_tool_from_command(user_command))
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": f"服务端出错：{e}"
        }), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)