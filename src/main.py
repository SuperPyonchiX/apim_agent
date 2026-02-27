import asyncio
import sys
import threading

from agents import Runner, RunConfig, set_default_openai_client, set_tracing_disabled

from src.agent import create_agent
from src.client import create_client

WELCOME_MESSAGE = """
================================================================
  APIM アシスタントへようこそ!
================================================================

  ファイル操作・Excel操作を中心とした汎用AIアシスタントです。
  何でもお気軽にご質問ください。

  できること:
    * Excelファイルの読み込み・書き込み・分析
    * ソースコードやテキストファイルの閲覧
    * ファイル・ディレクトリ内のテキスト検索（grep的機能）
    * フォルダ内のファイル一覧・検索
    * テキストファイルの作成・保存・追記
    * ファイルのコピー・移動・比較
    * コマンド実行（ビルド、lint、静的解析ツール）
    * ExcelシートのCSVエクスポート
    * Web検索（最新情報の検索・取得）
    * Webページの取得・Markdown変換
    * 静的解析結果のトリアージ（誤検知/逸脱/修正の分類）

  入力例:
    「C:\\results.xlsx を読み込んで内容を教えて」
    「C:\\project\\src にある .py ファイルを一覧表示して」
    「C:\\project\\src で 'TODO' を含む行を検索して」
    「分析結果をまとめたレポートを作成して」
    「AIエージェントの最新トレンドを調べて」
    「https://example.com のページ内容を取得して」

  コマンド:
    help  ... この案内を再表示
    quit  ... 終了（exit, q でも可）

================================================================
"""

HELP_MESSAGE = """
================================================================
  ヘルプ - 使い方ガイド
================================================================

  ■ Excelの操作
    「C:\\data.xlsx を読み込んで内容を見せて」
    「C:\\data.xlsx のA列を集計して」
    「C:\\output.xlsx の "結果" 列に値を書き込んで」
    「C:\\data.xlsx のシート一覧を見せて」
    「C:\\data.xlsx をCSVにエクスポートして」
    「C:\\data.xlsx に "集計" シートを追加して」

  ■ ファイルの閲覧
    「C:\\project\\main.py を読んで」
    「C:\\project\\main.py の100行目から150行目を見せて」
    「C:\\project\\main.py のファイル情報を教えて」

  ■ テキスト検索
    「C:\\project\\src で 'TODO' を含む行を検索して」
    「C:\\project\\src の .py ファイルから 'def main' を再帰検索して」

  ■ ファイルの作成・保存
    「分析結果をまとめて C:\\report.txt に保存して」
    「以下の内容でファイルを作成して」
    「C:\\log.txt にログを追記して」

  ■ ファイルのコピー・移動・比較
    「C:\\data.xlsx を C:\\backup\\data.xlsx にコピーして」
    「C:\\old.py と C:\\new.py の差分を見せて」

  ■ フォルダの一覧
    「C:\\project\\src の中身を見せて」
    「C:\\project\\src にある .py ファイルを探して」
    「C:\\project 以下の全 .c ファイルを再帰的に探して」

  ■ コマンド実行
    「python --version を実行して」
    「C:\\project で gcc -Wall main.c を実行して」

  ■ Web検索・ページ取得
    「Pythonの最新バージョンを調べて」
    「Azure OpenAI Serviceの料金を検索して」
    「https://example.com の内容を取得して要約して」
    「さっき検索したURLの詳細を見せて」

  ■ 静的解析トリアージ
    「C:\\analysis\\findings.xlsx の静的解析結果を
     C:\\project\\src をベースにトリアージして」

  コマンド:
    help  ... この案内を表示
    quit  ... 終了（exit, q でも可）

================================================================
"""

# ツール名 → 日本語表示名のマッピング
TOOL_DISPLAY_NAMES: dict[str, str] = {
    "read_excel": "Excelファイルを読み込み中",
    "read_source_code": "ソースコードを読み込み中",
    "write_excel_cells": "Excelファイルに書き込み中",
    "write_file": "ファイルを保存中",
    "list_directory": "フォルダを探索中",
    "search_in_file": "テキストを検索中",
    "get_file_info": "ファイル情報を取得中",
    "read_excel_sheet_names": "シート一覧を取得中",
    "copy_file": "ファイルをコピー/移動中",
    "run_command": "コマンドを実行中",
    "diff_files": "ファイルを比較中",
    "append_to_file": "ファイルに追記中",
    "create_excel_sheet": "シートを作成中",
    "export_excel_to_csv": "CSVにエクスポート中",
    "web_search": "Webを検索中",
    "web_fetch": "Webページを取得中",
}


def setup() -> None:
    """Agents SDKの初期設定: カスタムクライアント登録とトレーシング無効化。"""
    set_tracing_disabled(True)
    client = create_client()
    set_default_openai_client(client)


class LiveStatus:
    """処理の進捗をリアルタイムでスピナー付きで表示する。

    update() でメッセージを変更でき、Claude Code のように
    「今何をしているか」をユーザーにリアルタイムで伝える。
    """

    def __init__(self, message: str = "考え中..."):
        self._message = message
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._max_line_len = 0

    def start(self) -> None:
        self._stop_event.clear()
        self._max_line_len = 0
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()

    def update(self, message: str) -> None:
        """スピナーのメッセージを更新する。"""
        with self._lock:
            self._message = message

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join()
        # スピナー行をクリア
        clear_len = max(self._max_line_len + 4, 80)
        print(f"\r{' ' * clear_len}\r", end="", flush=True)

    def _spin(self) -> None:
        chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        idx = 0
        while not self._stop_event.is_set():
            with self._lock:
                msg = self._message
            line = f"\r{chars[idx]} {msg}"
            self._max_line_len = max(self._max_line_len, len(line))
            # 前回より短い場合に残る文字を消すためパディング
            padded = line.ljust(self._max_line_len)
            print(padded, end="", flush=True)
            idx = (idx + 1) % len(chars)
            self._stop_event.wait(0.1)


async def process_stream(result, status: LiveStatus) -> None:
    """ストリーミングイベントを処理し、LiveStatus をリアルタイム更新する。"""
    try:
        from openai.types.responses import (
            ResponseOutputItemAddedEvent,
            ResponseTextDeltaEvent,
            ResponseReasoningTextDeltaEvent,
            ResponseFunctionCallArgumentsDoneEvent,
        )
    except ImportError:
        pass

    tool_call_count = 0

    async for event in result.stream_events():
        if event.type == "raw_response_event":
            raw = event.data

            # テキスト生成中
            if isinstance(raw, ResponseTextDeltaEvent):
                status.update("回答を生成中...")

            # 推論・思考中
            elif isinstance(raw, ResponseReasoningTextDeltaEvent):
                status.update("考え中...")

            # ツール呼び出しの開始検出
            elif isinstance(raw, ResponseOutputItemAddedEvent):
                item = raw.item
                # function_call の場合、name からツール名を取得
                if getattr(item, "type", None) == "function_call":
                    tool_name = getattr(item, "name", "")
                    display = TOOL_DISPLAY_NAMES.get(tool_name, f"ツール実行中: {tool_name}")
                    tool_call_count += 1
                    status.update(display)
                # web_search_call の場合（ホステッドツール）
                elif getattr(item, "type", None) == "web_search_call":
                    tool_call_count += 1
                    status.update(TOOL_DISPLAY_NAMES.get("web_search", "Webを検索中"))

            # ツール引数の構築完了 → 実行中表示
            elif isinstance(raw, ResponseFunctionCallArgumentsDoneEvent):
                status.update("ツールを実行中...")

        elif event.type == "run_item_stream_event":
            # ツール出力が返ってきた → 次の処理へ
            if event.name == "tool_output":
                status.update("結果を分析中...")
            elif event.name == "tool_called":
                # RunItemStreamEvent の tool_called でもツール名を取得
                raw_item = getattr(event.item, "raw_item", None)
                if raw_item:
                    tool_name = getattr(raw_item, "name", "")
                    display = TOOL_DISPLAY_NAMES.get(tool_name, f"ツール実行中: {tool_name}")
                    status.update(display)


async def run_single(user_input: str) -> str:
    """1回のメッセージでエージェントを実行し、結果を返す。"""
    agent = create_agent()
    status = LiveStatus()
    status.start()
    try:
        result = Runner.run_streamed(
            agent,
            input=user_input,
            max_turns=200,
            run_config=RunConfig(
                tracing_disabled=True,
                workflow_name="azure-apim-agent",
            ),
        )
        await process_stream(result, status)
        status.stop()
        return result.final_output
    except Exception:
        status.stop()
        raise


async def run_interactive() -> None:
    """対話モードでエージェントを実行する。"""
    agent = create_agent()
    print(WELCOME_MESSAGE)

    input_items: list = []

    while True:
        try:
            user_input = input("\nあなた: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nお疲れ様でした。またいつでもどうぞ!")
            break

        if not user_input:
            continue

        lower_input = user_input.lower()
        if lower_input in ("quit", "exit", "q"):
            print("お疲れ様でした。またいつでもどうぞ!")
            break

        if lower_input in ("help", "?", "ヘルプ"):
            print(HELP_MESSAGE)
            continue

        status = LiveStatus()
        try:
            if input_items:
                input_items.append({"role": "user", "content": user_input})
                run_input = input_items
            else:
                run_input = user_input

            status.start()
            result = Runner.run_streamed(
                agent,
                input=run_input,
                max_turns=200,
                run_config=RunConfig(
                    tracing_disabled=True,
                    workflow_name="azure-apim-agent",
                ),
            )
            await process_stream(result, status)
            status.stop()
            print(f"\nアシスタント: {result.final_output}")

            input_items = result.to_input_list()

        except KeyboardInterrupt:
            status.stop()
            print("\n\n処理を中断しました。新しいメッセージを入力できます。")
        except Exception as e:
            status.stop()
            error_name = type(e).__name__
            print(f"\nエラーが発生しました: {error_name}: {e}")

            if "auth" in str(e).lower() or "401" in str(e) or "403" in str(e):
                print("→ 認証エラーの可能性があります。.env の AZURE_APIM_SUBSCRIPTION_KEY を確認してください。")
            elif "timeout" in str(e).lower() or "timed out" in str(e).lower():
                print("→ 接続がタイムアウトしました。ネットワーク接続を確認してください。")
            elif "connection" in str(e).lower():
                print("→ サーバーに接続できません。AZURE_APIM_ENDPOINT の設定とネットワーク接続を確認してください。")
            elif "rate" in str(e).lower() or "429" in str(e):
                print("→ APIのレート制限に達しました。しばらく待ってから再試行してください。")
            else:
                print("→ もう一度お試しください。問題が続く場合は .env の設定を確認してください。")


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
