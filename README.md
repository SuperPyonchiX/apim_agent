# Azure APIM OpenAI Agent

Azure API Management (APIM) を経由して Azure OpenAI Service に接続する AI エージェントアプリケーションです。
OpenAI Agents SDK の function calling 機能を活用し、ファイル操作・Excel操作を中心とした汎用AIアシスタントを提供します。

## 機能

- **対話モード**: ターミナル上でエージェントとチャット形式で会話（会話履歴を保持）
- **ワンショットモード**: コマンドライン引数で単一の質問を送信し、回答を取得
- **Function Calling ツール**:
  - Excelファイルの読み込み（ページネーション対応）
  - ソースコード / テキストファイルの読み込み（日本語エンコーディング自動判別）
  - Excelファイルへのセル書き込み（一括更新、列自動作成対応）
  - テキストファイルの新規作成・上書き保存（エンコーディング指定可）
  - ディレクトリ内容の一覧取得（globパターン対応、再帰検索対応）
- **ユーザー補助機能**:
  - 処理中スピナー表示（応答待ち時間の可視化）
  - `help` コマンドで使い方ガイドを随時表示
  - エラー時の具体的な対処法提示（認証エラー、タイムアウト等）
  - 環境変数未設定時の分かりやすいエラーメッセージ

### ユースケース例

- **静的解析トリアージ**: Excelの静的解析結果一覧を読み込み、ソースコードを確認して指摘を「誤検知・逸脱・修正」に分類
- **Excel分析**: Excelファイルの内容読み込みと集計・分析
- **ファイル操作**: ソースコードやテキストファイルの内容確認・調査
- **レポート作成**: 分析結果やまとめをテキストファイルとして保存
- **ファイル検索**: ディレクトリ内の再帰的なファイル検索

## 前提条件

- Python 3.13 以上
- Azure OpenAI Service のデプロイメント
- Azure API Management のサブスクリプションキー

## セットアップ

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd apim_agent
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
| `AZURE_DEPLOYMENT_NAME` | No | Azure OpenAI デプロイ名 | `gpt-4o` |
| `CLIENT_APPROACH` | No | クライアント方式（`azure` または `openai`） | `azure` |

## 使い方

### 対話モード

引数なしで実行すると、対話モードで起動します。`quit` と入力すると終了します。
対話中に `help` と入力すると使い方ガイドを表示できます。

```bash
python -m src.main
```

### ワンショットモード

コマンドライン引数にメッセージを渡すと、1回の応答で終了します。

```bash
python -m src.main "C:\results.xlsx を読み込んで内容を教えて"
```

### 静的解析トリアージの使用例

対話モードで以下のように指示します：

```
あなた: C:\analysis\findings.xlsx の静的解析結果を、C:\project\src を
        ベースディレクトリとしてトリアージしてください。
        各指摘のソースコードを確認し、「分類」列に結果を記入してください。
```

エージェントが自動的に以下を実行します：
1. Excelファイルの構造を把握
2. 各指摘についてソースコードを読み込み
3. 「誤検知」「逸脱」「修正」のいずれかに分類
4. 結果をExcelファイルに書き込み

## プロジェクト構成

```
apim_agent/
├── .env.example        # 環境変数テンプレート
├── .gitignore
├── requirements.txt    # Python 依存パッケージ
└── src/
    ├── __init__.py
    ├── config.py       # 環境変数の読み込み
    ├── client.py       # Azure OpenAI クライアント生成
    ├── tools.py        # エージェントツール定義（Excel/ファイル読み書き/ディレクトリ操作）
    ├── agent.py        # エージェント構築（システムプロンプト + ツール統合）
    └── main.py         # エントリポイント（CLI + 対話モード）
```

## アーキテクチャ

```
ユーザー入力
    │
    ▼
  main.py（エントリポイント / 会話履歴管理）
    │
    ├── config.py（環境変数読み込み）
    ├── client.py（Azure OpenAI クライアント生成）
    │       │
    │       ▼
    │   Azure APIM ──► Azure OpenAI Service
    │
    └── agent.py（エージェント構築）
            │
            └── tools.py（Excel読み書き / ファイル読み書き / ディレクトリ一覧）
```

## クライアント方式

`CLIENT_APPROACH` 環境変数で接続方式を選択できます：

- **`azure`**（推奨）: `AsyncAzureOpenAI` クライアントを使用。`api-key` と `Ocp-Apim-Subscription-Key` ヘッダーの両方を設定します。
- **`openai`**: `AsyncOpenAI` クライアントを使用。APIM との認証で問題が発生する場合があります。

## ライセンス

※ ライセンス情報を追記してください。
