from agents import Agent

from src.config import AZURE_DEPLOYMENT_NAME
from src.tools import calculate, get_current_time, get_weather, search_knowledge_base


def create_agent() -> Agent:
    """ツール呼び出し機能付きのエージェントを作成する。"""
    return Agent(
        name="Azure APIM Assistant",
        instructions=(
            "あなたはツールを使えるアシスタントです。"
            "ユーザーの質問に対して、適切なツールを使って正確に回答してください。"
            "ツールの結果は自然な日本語で説明してください。"
            "ツールがエラーを返した場合は、問題を説明し代替案を提案してください。"
        ),
        model=AZURE_DEPLOYMENT_NAME,
        tools=[get_weather, calculate, get_current_time, search_knowledge_base],
    )
