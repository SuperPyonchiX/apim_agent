from openai import AsyncAzureOpenAI, AsyncOpenAI

from src.config import (
    AZURE_APIM_ENDPOINT,
    AZURE_APIM_SUBSCRIPTION_KEY,
    AZURE_API_VERSION,
    CLIENT_APPROACH,
)


def create_azure_client() -> AsyncAzureOpenAI:
    """AsyncAzureOpenAI を使用してAPIM経由のクライアントを構築する（推奨）。

    SDK内部で以下のURLを構築:
      POST {azure_endpoint}/openai/responses?api-version=2025-04-01-preview

    認証ヘッダー:
      api-key: <subscription_key>                (api_key パラメータから)
      Ocp-Apim-Subscription-Key: <subscription_key>  (default_headers から)
    """
    return AsyncAzureOpenAI(
        azure_endpoint=AZURE_APIM_ENDPOINT,
        api_version=AZURE_API_VERSION,
        api_key=AZURE_APIM_SUBSCRIPTION_KEY,
        default_headers={
            "Ocp-Apim-Subscription-Key": AZURE_APIM_SUBSCRIPTION_KEY,
        },
    )


def create_openai_client() -> AsyncOpenAI:
    """標準の AsyncOpenAI を使用する代替アプローチ。

    手動で base_url, default_headers, default_query を設定する。
    注意: Authorization: Bearer ヘッダーが送信されるため、
    APIMの設定によっては認証エラーになる可能性あり。
    """
    return AsyncOpenAI(
        base_url=f"{AZURE_APIM_ENDPOINT.rstrip('/')}/openai",
        api_key=AZURE_APIM_SUBSCRIPTION_KEY,
        default_headers={
            "Ocp-Apim-Subscription-Key": AZURE_APIM_SUBSCRIPTION_KEY,
        },
        default_query={
            "api-version": AZURE_API_VERSION,
        },
    )


def create_client() -> AsyncOpenAI:
    """CLIENT_APPROACH 環境変数に基づいてクライアントを返す。"""
    if CLIENT_APPROACH == "azure":
        return create_azure_client()
    elif CLIENT_APPROACH == "openai":
        return create_openai_client()
    else:
        raise ValueError(
            f"Unknown CLIENT_APPROACH: {CLIENT_APPROACH!r}. Use 'azure' or 'openai'."
        )
