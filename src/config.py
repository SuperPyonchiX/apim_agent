import os
import sys

from dotenv import load_dotenv

load_dotenv()


def _require_env(name: str, description: str) -> str:
    """必須の環境変数を取得し、未設定の場合は分かりやすいエラーを表示して終了する。"""
    value = os.environ.get(name)
    if not value:
        print(f"\nエラー: 環境変数 {name} が設定されていません。", file=sys.stderr)
        print(f"  説明: {description}", file=sys.stderr)
        print(f"\n  対処法:", file=sys.stderr)
        print(f"    1. プロジェクトルートに .env ファイルがあるか確認してください", file=sys.stderr)
        print(f"    2. .env.example を参考に .env ファイルを作成してください", file=sys.stderr)
        print(f"       cp .env.example .env", file=sys.stderr)
        print(f"    3. .env 内の {name} に値を設定してください\n", file=sys.stderr)
        sys.exit(1)
    return value


AZURE_APIM_ENDPOINT: str = _require_env(
    "AZURE_APIM_ENDPOINT",
    "Azure API Management のエンドポイント URL（例: https://xxx.azure-api.net/xxx）",
)
AZURE_APIM_SUBSCRIPTION_KEY: str = _require_env(
    "AZURE_APIM_SUBSCRIPTION_KEY",
    "Azure API Management のサブスクリプションキー",
)
AZURE_API_VERSION: str = os.environ.get("AZURE_API_VERSION", "2025-04-01-preview")
AZURE_DEPLOYMENT_NAME: str = os.environ.get("AZURE_DEPLOYMENT_NAME", "gpt-4o")
CLIENT_APPROACH: str = os.environ.get("CLIENT_APPROACH", "azure")
