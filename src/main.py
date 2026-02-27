import asyncio
import sys

from agents import Runner, RunConfig, set_default_openai_client, set_tracing_disabled

from src.agent import create_agent
from src.client import create_client


def setup() -> None:
    """Agents SDKの初期設定: カスタムクライアント登録とトレーシング無効化。"""
    # トレーシングを無効化（デフォルトではOpenAIサーバーに送信されるため）
    set_tracing_disabled(True)

    # APIM向けカスタムクライアントを登録
    client = create_client()
    set_default_openai_client(client)


async def run_single(user_input: str) -> str:
    """1回のメッセージでエージェントを実行し、結果を返す。"""
    agent = create_agent()
    result = await Runner.run(
        agent,
        input=user_input,
        run_config=RunConfig(
            tracing_disabled=True,
            workflow_name="azure-apim-agent",
        ),
    )
    return result.final_output


async def run_interactive() -> None:
    """対話モードでエージェントを実行する。"""
    agent = create_agent()
    print("Agent ready. メッセージを入力してください（'quit' で終了）。")
    print("-" * 50)

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not user_input or user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye.")
            break

        try:
            result = await Runner.run(
                agent,
                input=user_input,
                run_config=RunConfig(
                    tracing_disabled=True,
                    workflow_name="azure-apim-agent",
                ),
            )
            print(f"\nAssistant: {result.final_output}")
        except Exception as e:
            print(f"\nError: {type(e).__name__}: {e}")


def main() -> None:
    """エントリーポイント。"""
    setup()

    if len(sys.argv) > 1:
        # ワンショットモード: CLIの引数をメッセージとして実行
        user_input = " ".join(sys.argv[1:])
        result = asyncio.run(run_single(user_input))
        print(result)
    else:
        # 対話モード
        asyncio.run(run_interactive())


if __name__ == "__main__":
    main()
