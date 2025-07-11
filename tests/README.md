# CloudWatch Logs MCP サーバー テストガイド

このディレクトリには、CloudWatch Logs MCP サーバーの包括的なテストスイートが含まれています。
特に **AWS Strands Agents** での使用を想定し、MCPインターフェースを介さない直接実行をテストしています。

## 🧪 テスト構造

```
tests/
├── conftest.py                    # 共通フィクスチャとテスト設定
├── unit/                          # ユニットテスト
│   ├── domain/                    # ドメイン層テスト
│   │   ├── test_models.py         # Pydanticモデルテスト
│   │   └── test_exceptions.py     # カスタム例外テスト
│   ├── services/                  # サービス層テスト
│   │   ├── test_logs_service.py   # CloudWatchLogsServiceテスト
│   │   └── test_analysis_service.py # CloudWatchAnalysisServiceテスト
│   └── utils/                     # ユーティリティテスト
│       ├── test_time_utils.py     # 時間変換関数テスト
│       └── test_data_utils.py     # データ処理関数テスト
└── integration/                   # 統合テスト
    └── tools/                     # ツール統合テスト
        └── test_aws_agents_tools.py # AWS Strands Agents用テスト
```

## 🚀 テスト実行方法

### 1. 基本実行

```bash
# 全テストの実行
uv run pytest

# 特定のディレクトリのテスト実行
uv run pytest tests/unit/
uv run pytest tests/integration/

# 特定のファイルのテスト実行
uv run pytest tests/unit/services/test_logs_service.py
```

### 2. マーカーベースの実行

```bash
# ユニットテストのみ実行
uv run pytest -m unit

# AWS Strands Agents用テストのみ実行
uv run pytest -m aws_agents

# 統合テストのみ実行
uv run pytest -m integration

# 複数マーカーの組み合わせ
uv run pytest -m "unit and aws_agents"
```

### 3. 詳細出力とカバレッジ

```bash
# 詳細出力付きで実行
uv run pytest -v

# カバレッジ測定付きで実行
uv run pytest --cov=src/cloudwatch_logs

# カバレッジレポートをHTMLで出力
uv run pytest --cov=src/cloudwatch_logs --cov-report=html
```

### 4. 特定のテストパターン

```bash
# 特定のテストクラスのみ実行
uv run pytest tests/unit/services/test_logs_service.py::TestCloudWatchLogsService

# 特定のテストメソッドのみ実行
uv run pytest tests/unit/services/test_logs_service.py::TestCloudWatchLogsService::test_init_with_default_version

# パターンマッチによるテスト実行
uv run pytest -k "test_aws_agents"
```

## 📋 テストマーカー

| マーカー | 説明 |
|---------|------|
| `unit` | ユニットテスト（外部依存なし） |
| `integration` | 統合テスト（モック化されたAWS API使用） |
| `aws_agents` | AWS Strands Agents用のテスト |
| `slow` | 実行時間が長いテスト |

## 🛠️ AWS Strands Agents用テストの特徴

### 1. MCPインターフェースなしでの直接実行
```python
# MCPコンテキストを使用しない直接実行
service = CloudWatchLogsService(version='agents-1.0.0')
result = service.describe_log_groups(region='us-east-1')
```

### 2. JSONシリアライゼーションテスト
```python
# AWS Strands Agentsでの使用に適したレスポンス形式
tool_response = {
    'status': 'success',
    'log_groups': [lg.model_dump() for lg in result]
}
json_str = json.dumps(tool_response, default=str)
```

### 3. エラーハンドリングパターン
```python
# AWS Strands Agentsでの適切なエラー処理
error_response = {
    'status': 'error',
    'error_type': type(e).__name__,
    'error_message': str(e),
    'is_retryable': isinstance(e, (QueryTimeoutError, AWSClientError))
}
```

## 🧩 テストフィクスチャ

### 主要フィクスチャ

- **`mock_boto3_session`**: AWS SDKのモック
- **`mock_logs_service`**: CloudWatchLogsServiceのモック
- **`mock_analysis_service`**: CloudWatchAnalysisServiceのモック
- **`sample_log_group_metadata`**: サンプルロググループデータ
- **`sample_anomaly`**: サンプル異常データ

### サンプルデータ

テストでは以下の現実的なサンプルデータを使用：

- **ロググループ**: `/aws/lambda/test-function`
- **タイムスタンプ**: `2023-04-29T20:00:00+00:00`
- **クエリ結果**: 実際のCloudWatch Logs Insightsレスポンス形式
- **異常データ**: CloudWatch異常検知器のレスポンス形式

## 📊 テスト範囲

### ユニットテスト
- ✅ データモデルのバリデーション
- ✅ 時間変換関数の正確性
- ✅ データ処理関数の効率性
- ✅ エラーハンドリングの適切性
- ✅ AWS API呼び出しのモック化

### 統合テスト
- ✅ サービス間の連携
- ✅ 非同期処理の正確性
- ✅ エンドツーエンドワークフロー
- ✅ 並行処理のテスト
- ✅ エラー伝播の検証

### AWS Strands Agents固有テスト
- ✅ 直接サービス呼び出し
- ✅ JSONシリアライゼーション
- ✅ エラーレスポンス形式
- ✅ 結果データ変換
- ✅ ツール実行パターン

## 🔧 開発者向けガイド

### 新しいテストの追加

1. **適切なディレクトリに配置**
   ```bash
   # ユニットテスト
   tests/unit/[layer]/test_[module].py
   
   # 統合テスト
   tests/integration/[component]/test_[feature].py
   ```

2. **適切なマーカーを使用**
   ```python
   @pytest.mark.unit
   @pytest.mark.aws_agents
   def test_new_feature():
       pass
   ```

3. **AWS Strands Agents用パターンを含める**
   ```python
   # 直接実行テスト
   def test_direct_service_call():
       service = CloudWatchLogsService()
       result = service.some_method()
       
       # JSON変換テスト
       json_result = json.dumps(result.model_dump(), default=str)
       assert isinstance(json_result, str)
   ```

### モックの活用

```python
# AWS APIのモック化
@patch('cloudwatch_logs.services.logs_service.boto3')
def test_with_mock(mock_boto3):
    mock_session = MagicMock()
    mock_boto3.Session.return_value = mock_session
    # テストロジック
```

### 非同期テストの作成

```python
@pytest.mark.asyncio
async def test_async_operation():
    result = await some_async_function()
    assert result is not None
```

## 🚨 テスト実行時の注意事項

1. **依存関係**: テスト実行前に `uv sync --group dev` を実行
2. **環境変数**: テスト用の環境変数は設定不要（モック使用）
3. **並行実行**: pytest-xdistを使用した並行実行可能

## 📈 継続的インテグレーション

```bash
# CI環境での実行例
uv run pytest -m "not slow" --cov=src/cloudwatch_logs --cov-report=xml
```

このテストスイートにより、AWS Strands Agentsでの安全で信頼性の高いツール実行が保証されます。
