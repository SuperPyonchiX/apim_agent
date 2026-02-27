# Azure APIM OpenAI Agent

Azure API Management (APIM) を経由して Azure OpenAI Service に接続する AI エージェントアプリケーションです。
OpenAI Agents SDK の function calling 機能を活用し、複数のツールを備えた対話型アシスタントを提供します。

## 機能

- **対話モード**: ターミナル上でエージェントとチャット形式で会話
- **ワンショットモード**: コマンドライン引数で単一の質問を送信し、回答を取得
- **Function Calling ツール**:
  - 天気情報の取得（スタブ実装）
  - 数式計算
  - 現在時刻の取得
  - ナレッジベース検索（スタブ実装）

## 前提条件

- Python 3.13 以上
- Azure OpenAI Service のデプロイメント（GPT-5）
- Azure API Management のサブスクリプションキー

## セットアップ

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd azure_dev
```

### 2. 仮想環境の作成と依存パッケージのインストール

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. 環境変数の設定

```bash
cp .env.example .env
```

`.env` ファイルを開き、以下の値を設定してください：

| 変数名 | 必須 | 説明 | デフォルト値 |
|---|---|---|---|
| `AZURE_APIM_ENDPOINT` | Yes | Azure APIM のエンドポイント URL | - |
| `AZURE_APIM_SUBSCRIPTION_KEY` | Yes | APIM サブスクリプションキー | - |
| `AZURE_API_VERSION` | No | Azure OpenAI API バージョン | `2025-04-01-preview` |
| `AZURE_DEPLOYMENT_NAME` | No | Azure OpenAI デプロイ名 | `gpt-5` |
| `CLIENT_APPROACH` | No | クライアント方式（`azure` または `openai`） | `azure` |

## 使い方

### 対話モード

引数なしで実行すると、対話モードで起動します。`quit` と入力すると終了します。

```bash
python -m src.main
```

### ワンショットモード

コマンドライン引数にメッセージを渡すと、1回の応答で終了します。

```bash
python -m src.main "東京の天気を教えて"
python -m src.main "123 * 456 を計算して"
python -m src.main "今何時？"
```

## プロジェクト構成

```
azure_dev/
├── .env.example        # 環境変数テンプレート
├── .gitignore
├── requirements.txt    # Python 依存パッケージ
└── src/
    ├── __init__.py
    ├── config.py       # 環境変数の読み込み
    ├── client.py       # Azure OpenAI クライアント生成
    ├── tools.py        # エージェントツール定義
    ├── agent.py        # エージェント構築
    └── main.py         # エントリポイント
```

## アーキテクチャ

```
ユーザー入力
    │
    ▼
  main.py（エントリポイント）
    │
    ├── config.py（環境変数読み込み）
    ├── client.py（Azure OpenAI クライアント生成）
    │       │
    │       ▼
    │   Azure APIM ──► Azure OpenAI Service (GPT-5)
    │
    └── agent.py（エージェント構築）
            │
            └── tools.py（天気 / 計算 / 時刻 / 検索）
```

## クライアント方式

`CLIENT_APPROACH` 環境変数で接続方式を選択できます：

- **`azure`**（推奨）: `AsyncAzureOpenAI` クライアントを使用。`api-key` と `Ocp-Apim-Subscription-Key` ヘッダーの両方を設定します。
- **`openai`**: `AsyncOpenAI` クライアントを使用。APIM との認証で問題が発生する場合があります。

## ライセンス

※ ライセンス情報を追記してください。
