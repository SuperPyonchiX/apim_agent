import asyncio
import sys

from agents import Runner, RunConfig, set_default_openai_client, set_tracing_disabled

from src.agent import create_agent
from src.client import create_client

WELCOME_MESSAGE = """
================================================================
  Azure APIM アシスタント
================================================================

  ファイル操作・Excel操作を中心とした汎用AIアシスタントです。

  主な機能:
    - Excelファイルの読み込み・書き込み
    - ソースコード / テキストファイルの読み込み
    - ディレクトリ内容の一覧取得
    - 静的解析結果のトリアージ（誤検知/逸脱/修正の分類）

  入力例:
    「C:\\results.xlsx を読み込んで内容を教えて」
    「C:\\project\\src を基準にして analysis.xlsx の
     静的解析結果をトリアージして」

  終了するには quit と入力してください
================================================================
"""


def setup() -> None:
    """Agents SDKの初期設定: カスタムクライアント登録とトレーシング無効化。"""
    set_tracing_disabled(True)
    client = create_client()
    set_default_openai_client(client)


async def run_single(user_input: str) -> str:
    """1回のメッセージでエージェントを実行し、結果を返す。"""
    agent = create_agent()
    result = await Runner.run(
        agent,
        input=user_input,
        max_turns=200,
        run_config=RunConfig(
            tracing_disabled=True,
            workflow_name="azure-apim-agent",
        ),
    )
    return result.final_output


async def run_interactive() -> None:
    """対話モードでエージェントを実行する。"""
    agent = create_agent()
    print(WELCOME_MESSAGE)

    input_items: list = []

    while True:
        try:
            user_input = input("\nあなた: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nお疲れ様でした。")
            break

        if not user_input or user_input.lower() in ("quit", "exit", "q"):
            print("お疲れ様でした。")
            break

        try:
            if input_items:
                input_items.append({"role": "user", "content": user_input})
                run_input = input_items
            else:
                run_input = user_input

            result = await Runner.run(
                agent,
                input=run_input,
                max_turns=200,
                run_config=RunConfig(
                    tracing_disabled=True,
                    workflow_name="azure-apim-agent",
                ),
            )
            print(f"\nアシスタント: {result.final_output}")

            input_items = result.to_input_list()

        except Exception as e:
            print(f"\nエラーが発生しました: {type(e).__name__}: {e}")
            print("もう一度お試しください。問題が続く場合は入力内容を確認してください。")


def main() -> None:
    """エントリーポイント。"""
    setup()

    if len(sys.argv) > 1:
        user_input = " ".join(sys.argv[1:])
        result = asyncio.run(run_single(user_input))
        print(result)
    else:
        asyncio.run(run_interactive())


if __name__ == "__main__":
    main()
