# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

このファイルは、Claude Code (claude.ai/code) がこのリポジトリで作業する際のガイダンスを提供します。

## 開発環境とコマンド

このプロジェクトはPython 3.10以上で動作し、`uv`パッケージマネージャーを使用しています。

### 初期セットアップ

```bash
# 開発環境の完全セットアップ
uv sync --group dev

# 開発者モードでのMCPサーバー起動確認
uv run cloudwatch-logs-mcp
```

### 必須コマンド

```bash
# 開発環境のセットアップ
uv sync --group dev

# MCPサーバーの実行
uv run cloudwatch-logs-mcp

# または
uv run python -m interfaces.mcp_server

# テストの実行
uv run pytest

# 特定のテストディレクトリの実行
uv run pytest tests/unit/
uv run pytest tests/integration/

# 特定のテストファイルの実行
uv run pytest tests/unit/services/test_logs_service.py

# 特定のテストクラス・メソッドの実行
uv run pytest tests/unit/services/test_logs_service.py::TestCloudWatchLogsService::test_init_with_default_version

# テストマーカーによる実行
uv run pytest -m unit                    # ユニットテストのみ
uv run pytest -m integration            # 統合テストのみ
uv run pytest -m aws_agents             # AWS Strands Agents用テストのみ
uv run pytest -m "unit and aws_agents"  # 複数マーカーの組み合わせ

# カバレッジ付きテストの実行
uv run pytest --cov=src/cloudwatch_logs

# カバレッジレポートをHTMLで出力
uv run pytest --cov=src/cloudwatch_logs --cov-report=html

# リンティングの実行
uv run ruff check

# フォーマッティングの実行
uv run ruff format

# 型チェックの実行
uv run pyright

# 全体的な品質チェック
uv run ruff check && uv run pyright
```

### 開発依存関係

- `ruff` - コードフォーマットとリンティング
- `pyright` - 型チェック
- `pytest` - テストフレームワーク
- `pytest-asyncio` - 非同期テストサポート
- `pytest-cov` - カバレッジ測定
- `pytest-mock` - モック機能拡張

## プロジェクトアーキテクチャ

### 高レベル構造

このプロジェクトは、CloudWatch Logs機能に特化したModel Context Protocol（MCP）サーバーです。クリーンアーキテクチャを採用し、以下の層に分離されています：

1. **ドメイン層** (`src/cloudwatch_logs/domain/`) - ビジネスロジックとデータモデル
2. **サービス層** (`src/cloudwatch_logs/services/`) - AWS API操作と分析処理
3. **ユーティリティ層** (`src/cloudwatch_logs/utils/`) - 共通ヘルパー関数
4. **インターフェース層** (`src/interfaces/`) - MCP固有の処理

### コアコンポーネント

#### ドメイン層 (Domain Layer)
- **models.py**: Pydanticベースのデータモデル定義
  - LogGroupMetadata: ロググループメタデータ
  - SavedLogsInsightsQuery: 保存されたクエリ
  - LogAnomaly: ログ異常データ
  - LogsAnalysisResult: 分析結果
- **exceptions.py**: カスタム例外階層
  - CloudWatchLogsError: ベース例外
  - InvalidParameterError: パラメータエラー
  - AWSClientError: AWS APIエラー
  - QueryTimeoutError: クエリタイムアウト
  - QueryExecutionError: クエリ実行エラー

#### サービス層 (Service Layer)
- **logs_service.py**: CloudWatch Logs API操作
  - ロググループの検索と取得
  - 保存されたクエリの管理
  - CloudWatch Logs Insightsクエリの実行
  - クエリ結果の取得とポーリング
  - クエリのキャンセル
- **analysis_service.py**: ログ分析と異常検知
  - ログ異常検知器との統合
  - パターン分析（上位5つのメッセージパターン）
  - エラーパターン分析（エラー関連用語の特定）
  - 並列処理による効率的な分析
- **documentation_service.py**: クエリ構文ドキュメント提供
  - CloudWatch Logs Insightsクエリ構文の包括的ドキュメント
  - コマンド・関数・例の検索機能
  - ベストプラクティス・トラブルシューティング情報
  - AWS Strands Agents SDK互換性

#### ユーティリティ層 (Utils Layer)
- **time_utils.py**: 時間変換ユーティリティ
  - epoch_ms_to_utc_iso: エポックミリ秒からISO 8601への変換
  - convert_time_to_timestamp: ISO 8601からUnixタイムスタンプへの変換
- **data_utils.py**: データ処理ユーティリティ
  - remove_null_values: null値の除去
  - filter_by_prefixes: プレフィックスによるフィルタリング
  - clean_up_pattern: パターン結果の最適化

#### ドキュメンテーション層 (Documentation Layer)
- **query_syntax.py**: クエリ構文データベース
  - 包括的なCloudWatch Logs Insightsクエリ構文情報
  - 複数のAWS公式ドキュメントURLからの統合データ
  - コマンド・関数・例・ベストプラクティス・トラブルシューティング
  - 検索・フィルタリング・カテゴリ別取得機能

#### インターフェース層 (Interface Layer)
- **mcp_server.py**: MCPサーバーの起動と初期化
  - FastMCPフレームワークの設定
  - ツールの登録と管理
  - エラーハンドリング
- **mcp_tools.py**: MCPツールの実装
  - describe_log_groups: ロググループ検索
  - analyze_log_group: ログ分析
  - execute_log_insights_query: クエリ実行
  - get_logs_insight_query_results: 結果取得
  - cancel_logs_insight_query: クエリキャンセル
  - get_query_syntax_documentation: クエリ構文ドキュメント取得

### 重要な設計原則

#### 1. クリーンアーキテクチャ
- **依存性逆転**: 上位層が下位層に依存し、下位層は抽象に依存
- **単一責任**: 各クラス・モジュールは単一の責任を持つ
- **インターフェース分離**: MCP固有の処理をインターフェース層に分離

#### 2. AWS認証情報の処理
- 環境変数`AWS_PROFILE`の自動検出
- リージョン別クライアントの動的生成とキャッシュ
- 認証エラーの一貫したハンドリング

#### 3. 非同期処理の最適化
- `asyncio.gather`による並列処理
- CloudWatch Logs Insightsのポーリング機能
- タイムアウトとエラーハンドリング

#### 4. データモデルの型安全性
- Pydantic v2による厳密な型定義
- 実行時バリデーションとコンパイル時チェック
- APIレスポンスの型安全な変換

#### 5. パフォーマンス最適化
- クライアントキャッシュによる無駄なAPI呼び出しの削減
- トークン使用量の最適化（`clean_up_pattern`）
- ページネーション対応

#### 6. デュアルインターフェース対応
- **MCP互換性**: FastMCPフレームワークでの完全なMCP実装
- **AWS Strands Agents SDK互換性**: MCP非依存での直接実行サポート
- **共通のコアロジック**: 両インターフェースで同じビジネスロジックを使用

### テスト戦略

#### テスト構造
```
tests/
├── conftest.py                    # 共通フィクスチャとテスト設定
├── unit/                          # ユニットテスト
│   ├── domain/                    # ドメイン層テスト
│   ├── services/                  # サービス層テスト
│   └── utils/                     # ユーティリティテスト
└── integration/                   # 統合テスト
    └── tools/                     # ツール統合テスト
```

#### テストマーカー
- `unit`: ユニットテスト（外部依存なし）
- `integration`: 統合テスト（モック化されたAWS API使用）
- `aws_agents`: AWS Strands Agents用のテスト
- `slow`: 実行時間が長いテスト

#### AWS Strands Agents対応テスト
- MCPインターフェースを介さない直接実行テスト
- JSONシリアライゼーションの検証
- エラーハンドリングパターンの確認
- 並行処理のテスト

#### モック戦略
- boto3のモック化による独立したテスト環境
- 現実的なAWS APIレスポンスのシミュレート
- エラー条件の再現可能なテスト

### 設定管理

#### コード品質設定 (pyproject.toml)
- **Ruff**: 99文字の行長制限、Google形式のdocstring
- **Pyright**: 厳密な型チェック
- **pytest**: 非同期テストの自動処理

#### pytest設定 (pytest.ini)
- テストマーカーの定義
- 非同期モードの自動設定
- 警告フィルタリング

### AWS認証情報の処理

このMCPサーバーは、AWS CloudWatch Logs APIへのアクセスに標準的なAWS認証情報チェーンを使用します。

#### 認証方法の優先順位

1. **環境変数 `AWS_PROFILE`** (推奨)
   - 指定されたプロファイルを使用してAWSクライアントを作成
   - `~/.aws/credentials` と `~/.aws/config` からプロファイル情報を読み込み

2. **環境変数での直接認証**
   - `AWS_ACCESS_KEY_ID` と `AWS_SECRET_ACCESS_KEY` を直接使用

3. **デフォルト認証情報**
   - boto3のデフォルト認証情報チェーンに従う（IAMロール、デフォルトプロファイルなど）

#### 実装の詳細

```python
# logs_service.py:86-94 での認証処理
if aws_profile := os.environ.get('AWS_PROFILE'):
    logger.info(f'Using AWS profile: {aws_profile} for region: {region}')
    return boto3.Session(profile_name=aws_profile, region_name=region).client('logs', config=config)
else:
    logger.info(f'Using default AWS credentials for region: {region}')
    return boto3.Session(region_name=region).client('logs', config=config)
```

#### AWS権限要件

このMCPサーバーの実行には以下のIAM権限が必要です：

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

### 開発時の注意点

#### 言語とローカライゼーション
- **コメントとドキュメント**: 日本語で記述
- **ユーザー向けメッセージ**: 英語を維持（MCP仕様準拠）
- **API仕様とdocstring**: 英語を維持（国際的な互換性のため）
- **エラーメッセージ**: 英語を維持（デバッグとログ解析のため）

#### パフォーマンス考慮事項
- AWSクライアントのキャッシュとリージョン別管理
- ページネーション対応による大量データの効率的な処理
- トークン使用量の最適化（特にパターン分析結果）
- 非同期処理による並列化

#### セキュリティ考慮事項
- AWS認証情報の適切な管理
- IAM権限の最小権限原則
- ログ出力時のセンシティブ情報の除外
- エラーメッセージでの機密情報の漏洩防止

#### 重要なファイルの場所
- **設定ファイル**: `pyproject.toml` (依存関係、ruff、pyright設定)
- **テスト設定**: `pytest.ini` (テストマーカー、実行オプション)
- **共通フィクスチャ**: `tests/conftest.py` (モック設定、サンプルデータ)
- **エントリーポイント**: `src/interfaces/mcp_server.py:main()`

### 拡張性

#### AWS Strands Agents SDKとの互換性
このプロジェクトは、MCP以外のインターフェースでも使用できるよう設計されています：

```python
# MCP非依存での直接使用例
from cloudwatch_logs.services.logs_service import CloudWatchLogsService
from cloudwatch_logs.services.analysis_service import CloudWatchAnalysisService
from cloudwatch_logs.services.documentation_service import DocumentationService

# サービスの直接インスタンス化
logs_service = CloudWatchLogsService(version='agents-1.0.0')
analysis_service = CloudWatchAnalysisService(logs_service)
documentation_service = DocumentationService(version='agents-1.0.0')

# 直接メソッド呼び出し
log_groups = logs_service.describe_log_groups(region='us-east-1')
query_docs = documentation_service.get_full_documentation()
```

#### 将来的な拡張
- CLI インターフェースの追加
- REST API インターフェースの追加
- GraphQL API インターフェースの追加
- 他のCloudWatchサービス（Metrics、Alarms）との統合

### トラブルシューティング

#### よくある問題
1. **AWS認証エラー**: 
   - AWS_PROFILEの設定確認
   - IAM権限の確認

2. **テスト実行エラー**:
   - 依存関係の更新: `uv sync --group dev`
   - パッケージの競合確認

3. **型チェックエラー**:
   - Pydanticモデルの定義確認
   - インポートパスの確認

#### ログ出力の活用
- loguru を使用した構造化ログ
- AWS API呼び出しの詳細ログ
- エラー発生時のスタックトレース

#### デバッグ方法
- LOG_LEVEL=DEBUG での詳細ログ出力
- pytest の -v オプションでの詳細テスト出力
- AWS APIコールのモック化による問題の切り分け
