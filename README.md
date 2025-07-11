# CloudWatch Logs MCP サーバー

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/r3-yamauchi/my-cloudwatch-logs-mcp-server)

CloudWatch Logs機能に特化したModel Context Protocol (MCP) サーバーです。
クリーンアーキテクチャを採用し、保守性と拡張性を重視した設計になっています。

## 🚀 特徴

- **🏗️ クリーンアーキテクチャ**: ドメイン層、サービス層、インターフェース層の明確な分離
- **🔄 完全独立実装**: 外部依存を最小限に抑えた独立したコードベース
- **⚡ MCP互換**: FastMCPを使用した高性能なMCPサーバー実装
- **📈 拡張可能**: CLI、REST API、AWS Agents SDK toolなどの追加インターフェースに対応可能
- **🔒 型安全**: Pydantic v2を使用した厳密な型定義とバリデーション
- **🌐 マルチリージョン対応**: 任意のAWSリージョンでの動作をサポート
- **🔐 セキュア**: AWS プロファイルベースの認証をサポート

## 📋 実装されている機能

### 1. describe_log_groups
**CloudWatch ロググループの検索と一覧取得**

- 📁 ロググループのメタデータ取得
- 🔍 プレフィックスによる効率的なフィルタリング
- 💾 保存されたクエリの自動関連付け
- 🔗 複数アカウント対応（監視アカウント機能）

### 2. analyze_log_group
**包括的なログ分析と異常検知**

- 🔍 ログ異常検知器との統合
- 📊 上位5つのメッセージパターン分析
- ⚠️ エラーパターンの自動特定
- 📈 時系列データ分析

### 3. execute_log_insights_query
**CloudWatch Logs Insightsクエリの実行**

- 🚀 高性能なクエリ実行
- ⏱️ リアルタイムポーリングと結果取得
- ⏰ カスタマイズ可能なタイムアウト処理
- 🎯 最適化されたトークン使用量

### 4. get_logs_insight_query_results
**クエリ結果の取得**

- 🔄 既存クエリの結果取得
- ⏳ ポーリングタイムアウト後の結果取得
- 📊 構造化された結果データ

### 5. cancel_logs_insight_query
**クエリの管理とキャンセル**

- ⏹️ 実行中クエリの安全なキャンセル
- 💰 コスト節約のための早期終了
- 📝 詳細な実行ログ

## 🏗️ プロジェクト構造

```
cloudwatch-logs-mcp/
├── src/
│   ├── cloudwatch_logs/           # 🧠 コアビジネスロジック
│   │   ├── domain/               # 🏛️ ドメイン層
│   │   │   ├── models.py         # 📊 データモデル定義
│   │   │   └── exceptions.py     # ⚠️ カスタム例外
│   │   ├── services/             # 🔧 サービス層
│   │   │   ├── logs_service.py   # 🌐 AWS API操作
│   │   │   └── analysis_service.py # 🔍 分析・異常検知
│   │   └── utils/                # 🛠️ ユーティリティ
│   │       ├── time_utils.py     # ⏰ 時間変換
│   │       └── data_utils.py     # 📁 データ処理
│   └── interfaces/               # 🌐 インターフェース層
│       ├── mcp_server.py         # 🖥️ MCPサーバー
│       └── mcp_tools.py          # 🔧 MCPツール定義
├── pyproject.toml               # 📦 プロジェクト設定
└── README.md                    # 📖 ドキュメント
```

## 🛠️ 技術スタック

- **Python**: 3.10以上 - 最新の型ヒントと非同期処理をサポート
- **パッケージマネージャー**: uv - 高速で効率的な依存関係管理
- **AWS SDK**: boto3 - 公式のAWS SDK for Python
- **MCP フレームワーク**: FastMCP - 高性能なMCPサーバー実装
- **データモデル**: Pydantic v2 - 厳密な型バリデーションとシリアライゼーション
- **ログ**: loguru - 構造化ログと高度なログ機能
- **非同期処理**: asyncio - 効率的な非同期処理とコルーチン

## 🔧 セットアップ

### 1. 依存関係のインストール

```bash
# 開発環境のセットアップ
uv sync --group dev

# 本番環境のセットアップ
uv sync
```

### 2. AWS認証情報の設定

このMCPサーバーは、標準的なAWS認証情報チェーンを使用してAWS CloudWatch Logsにアクセスします。

#### 認証方法の優先順位

1. **AWS プロファイル認証 (推奨)**
   - `AWS_PROFILE` 環境変数で指定されたプロファイルを使用
   - `~/.aws/credentials` と `~/.aws/config` ファイルからプロファイル情報を読み込み

2. **環境変数による認証**
   - `AWS_ACCESS_KEY_ID` と `AWS_SECRET_ACCESS_KEY` を直接指定

3. **IAM ロール認証**
   - EC2インスタンスプロファイルやECSタスクロールなどのAWSサービス上での実行時

4. **その他の認証方法**
   - AWS SSOやAWS CLIの設定に基づく認証

#### プロファイルベース認証の設定例

```bash
# AWS プロファイルを指定
export AWS_PROFILE=your-profile

# 特定のリージョンを指定（オプション）
export AWS_DEFAULT_REGION=us-east-1

# 実行
uv run cloudwatch-logs-mcp
```

#### 環境変数ベース認証の設定例

```bash
# アクセスキーとシークレットアクセスキーを設定
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_DEFAULT_REGION=us-east-1

# 実行
uv run cloudwatch-logs-mcp
```

#### AWS クレデンシャルファイルの設定例

`~/.aws/credentials` ファイル:
```ini
[default]
aws_access_key_id = your-access-key
aws_secret_access_key = your-secret-key

[production]
aws_access_key_id = prod-access-key
aws_secret_access_key = prod-secret-key
```

`~/.aws/config` ファイル:
```ini
[default]
region = us-east-1
output = json

[profile production]
region = ap-northeast-1
output = json
```

#### 認証エラーのトラブルシューティング

認証に失敗した場合、以下を確認してください：

1. **AWS プロファイルの存在確認**
   ```bash
   aws configure list-profiles
   ```

2. **認証情報の確認**
   ```bash
   aws configure list
   ```

3. **権限の確認**
   ```bash
   aws sts get-caller-identity
   ```

4. **CloudWatch Logs へのアクセス確認**
   ```bash
   aws logs describe-log-groups --limit 1
   ```

### 3. MCPサーバーの実行

```bash
# 標準実行
uv run cloudwatch-logs-mcp

# 特定のリージョンで実行
AWS_DEFAULT_REGION=ap-northeast-1 uv run cloudwatch-logs-mcp

# デバッグモードで実行
LOG_LEVEL=DEBUG uv run cloudwatch-logs-mcp
```

## 🔨 開発コマンド

```bash
# コードフォーマット（自動修正）
uv run ruff format

# リンティング（コード品質チェック）
uv run ruff check

# リンティング（自動修正可能な問題を修正）
uv run ruff check --fix

# 型チェック（静的解析）
uv run pyright

# 全体的な品質チェック
uv run ruff check && uv run pyright
```

## 🔐 AWS権限要件

以下のIAM権限が必要です：

### 基本権限ポリシー

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:DescribeLogGroups",
        "logs:DescribeQueryDefinitions",
        "logs:ListLogAnomalyDetectors",
        "logs:ListAnomalies",
        "logs:StartQuery",
        "logs:GetQueryResults",
        "logs:StopQuery"
      ],
      "Resource": "*"
    }
  ]
}
```

### 権限の詳細説明

- **logs:DescribeLogGroups** - ロググループの一覧取得
- **logs:DescribeQueryDefinitions** - 保存されたクエリの取得
- **logs:ListLogAnomalyDetectors** - 異常検知器の一覧取得
- **logs:ListAnomalies** - 検出された異常の一覧取得
- **logs:StartQuery** - CloudWatch Logs Insightsクエリの開始
- **logs:GetQueryResults** - クエリ結果の取得
- **logs:StopQuery** - 実行中クエリの停止

### セキュリティのベストプラクティス

1. **最小権限の原則**: 必要最小限の権限のみを付与
2. **リソースベースの制限**: 可能な場合はワイルドカード「*」を避ける
3. **定期的な権限レビュー**: 不要な権限の削除を定期的に実施
4. **IAM条件の活用**: 時間やIPアドレスベースの制限を考慮

## 🎯 設計原則

### 1. 🏗️ 責任分離（Separation of Concerns）
- **ドメイン層**: ビジネスロジックとデータモデルの純粋な定義
- **サービス層**: AWS API操作と分析処理の具体的実装
- **インターフェース層**: MCP固有の処理と外部とのやり取り

### 2. 🔄 依存関係の制御（Dependency Inversion）
- コアロジックは外部フレームワークに依存しない設計
- インターフェース層でMCP固有の処理を完全に分離
- 将来的な拡張性を考慮した疎結合アーキテクチャ

### 3. ⚠️ エラーハンドリング（Error Handling）
- カスタム例外による統一されたエラー処理
- 適切なログ出力と分かりやすいエラーメッセージ
- MCPコンテキストでの適切なエラー通知

### 4. 🔒 型安全性（Type Safety）
- Pydantic v2による厳密な型定義
- 実行時バリデーションとコンパイル時チェック
- APIレスポンスの型安全な変換

### 5. 📊 パフォーマンス最適化
- 非同期処理による効率的なI/O操作
- クライアントキャッシュによる無駄なAPI呼び出しの削減
- トークン使用量の最適化

## 🧪 テスト

### テスト実行

```bash
# 全テストの実行
uv run pytest

# ユニットテストのみ実行
uv run pytest -m unit

# AWS Strands Agents用テストのみ実行
uv run pytest -m aws_agents

# カバレッジ付きテスト実行
uv run pytest --cov=src/cloudwatch_logs

# 詳細出力付きテスト実行
uv run pytest -v
```

### テスト種別

- **🔬 ユニットテスト**: 各層の独立したテスト
- **🔗 統合テスト**: サービス間連携のテスト
- **🤖 AWS Strands Agents用テスト**: MCP非依存の直接実行テスト
- **📊 JSONシリアライゼーションテスト**: データ変換の検証

詳細なテスト実行方法については、[tests/README.md](tests/README.md)を参照してください。

## 🚀 AWS Strands Agents SDK対応

このプロジェクトは、MCPサーバーとしてだけでなく、AWS Strands Agents SDKのツールとしても使用できるよう設計されています。

### 直接実行例

```python
from cloudwatch_logs.services.logs_service import CloudWatchLogsService
from cloudwatch_logs.services.analysis_service import CloudWatchAnalysisService

# サービスの直接インスタンス化
logs_service = CloudWatchLogsService(version='agents-1.0.0')
analysis_service = CloudWatchAnalysisService(logs_service)

# MCP非依存での実行
log_groups = logs_service.describe_log_groups(
    region='us-east-1',
    log_group_name_prefix='/aws/lambda/',
    max_items=10
)

# AWS Strands Agents用のレスポンス形式
tool_response = {
    'status': 'success',
    'log_groups_count': len(log_groups),
    'log_groups': [lg.model_dump() for lg in log_groups]
}
```

### クリーンアーキテクチャの利点

- **🔄 インターフェース独立性**: MCPに依存しないコアロジック
- **🧪 テスト容易性**: モック化とユニットテストが簡単
- **🔧 拡張性**: 新しいインターフェースの追加が容易
- **📊 再利用性**: 他のプロジェクトでのコンポーネント再利用

## 🚀 今後の拡張可能性

### インターフェース拡張
- **🖥️ CLI インターフェース**: 直接的なコマンドライン操作
- **🌐 REST API**: HTTP APIとしての提供
- **🤖 AWS Agents SDK tool**: Agent用ツールとしての利用（実装済み）
- **📱 GraphQL API**: 柔軟なクエリインターフェース

### 機能拡張
- **📊 他のCloudWatchサービス**: Metrics、Alarmsとの統合
- **🔍 リアルタイム監視**: ログストリームのリアルタイム監視
- **🤖 機械学習統合**: 異常検知の精度向上
- **📈 ダッシュボード**: 可視化とレポート機能

### 運用・監視機能
- **📊 メトリクス**: Prometheus/OpenTelemetryとの統合
- **🔍 トレーシング**: 分散トレーシング対応
- **🏥 ヘルスチェック**: アプリケーションの健全性監視
- **🔧 設定管理**: 動的設定変更対応

## 📄 ライセンス

このプロジェクトはApache License 2.0の下で提供されています。

## 📂 プロジェクト詳細

### ファイル構成の詳細

```
cloudwatch-logs-mcp/
├── src/
│   ├── cloudwatch_logs/
│   │   ├── domain/
│   │   │   ├── models.py          # Pydanticモデル定義
│   │   │   └── exceptions.py      # カスタム例外階層
│   │   ├── services/
│   │   │   ├── logs_service.py    # CloudWatch Logs API操作
│   │   │   └── analysis_service.py # 異常検知・パターン分析
│   │   └── utils/
│   │       ├── time_utils.py      # 時間変換ユーティリティ
│   │       └── data_utils.py      # データ処理ヘルパー
│   └── interfaces/
│       ├── mcp_server.py          # MCPサーバー起動
│       └── mcp_tools.py           # MCPツール実装
├── tests/                         # 包括的テストスイート
│   ├── conftest.py               # 共通フィクスチャ
│   ├── unit/                     # ユニットテスト
│   └── integration/              # 統合テスト
├── pyproject.toml                # プロジェクト設定
├── pytest.ini                   # pytest設定
├── README.md                     # プロジェクト概要
└── CLAUDE.md                     # 開発ガイド
```

### 設定ファイル

- **pyproject.toml**: uvパッケージマネージャー、ruff、pyrightの設定
- **pytest.ini**: テストマーカーと実行オプション
- **CLAUDE.md**: Claude Code用の開発ガイドライン
