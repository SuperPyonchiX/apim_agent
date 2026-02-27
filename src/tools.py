import json
import math
from datetime import datetime, timezone

from agents import function_tool


@function_tool
def get_weather(city: str, unit: str = "celsius") -> str:
    """指定された都市の現在の天気情報を取得する。

    Args:
        city: 天気を調べる都市名。
        unit: 温度の単位。'celsius' または 'fahrenheit'。
    """
    # スタブ実装 — 実際のAPIに置き換えてください
    weather_data = {
        "tokyo": {"temp": 22, "condition": "晴れ時々曇り"},
        "大阪": {"temp": 24, "condition": "晴れ"},
        "london": {"temp": 15, "condition": "雨"},
        "new york": {"temp": 28, "condition": "晴れ"},
        "東京": {"temp": 22, "condition": "晴れ時々曇り"},
    }
    data = weather_data.get(city.lower(), {"temp": 20, "condition": "不明"})
    temp = data["temp"]
    if unit == "fahrenheit":
        temp = temp * 9 / 5 + 32
    return json.dumps(
        {"city": city, "temperature": temp, "unit": unit, "condition": data["condition"]},
        ensure_ascii=False,
    )


@function_tool
def calculate(expression: str) -> str:
    """数式を安全に評価する。

    Args:
        expression: '2 + 3 * 4' や 'sqrt(16)' のような数式。
    """
    allowed_names = {
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "pi": math.pi,
        "e": math.e,
        "abs": abs,
        "round": round,
        "pow": pow,
    }
    try:
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return json.dumps({"expression": expression, "result": result})
    except Exception as e:
        return json.dumps({"expression": expression, "error": str(e)})


@function_tool
def get_current_time(timezone_name: str = "UTC") -> str:
    """現在の日付と時刻を取得する。

    Args:
        timezone_name: タイムゾーン名（現在はUTCのみサポート）。
    """
    now = datetime.now(timezone.utc)
    return json.dumps(
        {
            "timezone": timezone_name,
            "datetime": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
        }
    )


@function_tool
def search_knowledge_base(query: str, max_results: int = 3) -> str:
    """内部ナレッジベースから情報を検索する。

    Args:
        query: 検索クエリ文字列。
        max_results: 返す結果の最大数（1〜10）。
    """
    # スタブ実装 — 実際のベクトル検索やDB検索に置き換えてください
    max_results = max(1, min(10, max_results))
    return json.dumps(
        {
            "query": query,
            "results": [
                {
                    "title": f"Result {i + 1} for '{query}'",
                    "snippet": f"Sample content about {query}...",
                }
                for i in range(max_results)
            ],
        },
        ensure_ascii=False,
    )
