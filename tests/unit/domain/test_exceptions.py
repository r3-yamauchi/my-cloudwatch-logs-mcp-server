"""ドメイン例外のユニットテスト.

このテストモジュールは、カスタム例外クラスの動作と
継承関係を検証します。AWS Strands Agentsでの使用を考慮し、
適切なエラーメッセージとエラーハンドリングパターンをテストします。
"""

import pytest

from cloudwatch_logs.domain.exceptions import (
    CloudWatchLogsError,
    InvalidParameterError,
    AWSClientError,
    QueryTimeoutError,
    QueryExecutionError
)


@pytest.mark.unit
@pytest.mark.aws_agents
class TestCloudWatchLogsError:
    """CloudWatchLogsErrorベース例外のテストクラス."""

    def test_base_exception_creation(self):
        """ベース例外の作成テスト."""
        error = CloudWatchLogsError("Base error message")
        assert str(error) == "Base error message"
        assert isinstance(error, Exception)

    def test_base_exception_inheritance(self):
        """ベース例外の継承テスト."""
        error = CloudWatchLogsError("Test error")
        assert isinstance(error, Exception)
        assert isinstance(error, CloudWatchLogsError)

    def test_empty_message(self):
        """空のメッセージでの例外作成テスト."""
        error = CloudWatchLogsError()
        assert str(error) == ""


@pytest.mark.unit
@pytest.mark.aws_agents
class TestInvalidParameterError:
    """InvalidParameterErrorのテストクラス."""

    def test_invalid_parameter_error_creation(self):
        """不正パラメータエラーの作成テスト."""
        error = InvalidParameterError("Invalid log group name")
        assert str(error) == "Invalid log group name"
        assert isinstance(error, CloudWatchLogsError)
        assert isinstance(error, InvalidParameterError)

    def test_parameter_validation_error_message(self):
        """パラメータバリデーションエラーメッセージテスト."""
        error = InvalidParameterError(
            "Exactly one of log_group_names or log_group_identifiers must be provided"
        )
        
        assert "log_group_names" in str(error)
        assert "log_group_identifiers" in str(error)
        assert "must be provided" in str(error)

    def test_inheritance_chain(self):
        """継承チェーンのテスト."""
        error = InvalidParameterError("Test")
        
        assert isinstance(error, Exception)
        assert isinstance(error, CloudWatchLogsError)
        assert isinstance(error, InvalidParameterError)

    def test_exception_catching_as_base(self):
        """ベースクラスでの例外キャッチテスト."""
        with pytest.raises(CloudWatchLogsError):
            raise InvalidParameterError("Test parameter error")


@pytest.mark.unit
@pytest.mark.aws_agents
class TestAWSClientError:
    """AWSClientErrorのテストクラス."""

    def test_aws_client_error_creation(self):
        """AWSクライアントエラーの作成テスト."""
        error = AWSClientError("Failed to create AWS client")
        assert str(error) == "Failed to create AWS client"
        assert isinstance(error, CloudWatchLogsError)

    def test_aws_credential_error_message(self):
        """AWS認証エラーメッセージテスト."""
        error = AWSClientError(
            "Failed to create AWS client for region us-east-1: NoCredentialsError"
        )
        
        assert "Failed to create AWS client" in str(error)
        assert "us-east-1" in str(error)
        assert "NoCredentialsError" in str(error)

    def test_aws_api_error_message(self):
        """AWS APIエラーメッセージテスト."""
        error = AWSClientError(
            "Failed to describe log groups: AccessDenied"
        )
        
        assert "Failed to describe log groups" in str(error)
        assert "AccessDenied" in str(error)

    def test_aws_agents_error_handling(self):
        """AWS Strands Agents用のエラーハンドリングテスト."""
        error_message = "Failed to execute CloudWatch operation: InternalServiceError"
        error = AWSClientError(error_message)
        
        # AWS Strands Agentsで適切に処理できる形式であることを確認
        assert isinstance(str(error), str)
        assert len(str(error)) > 0
        assert "CloudWatch" in str(error)


@pytest.mark.unit
@pytest.mark.aws_agents
class TestQueryTimeoutError:
    """QueryTimeoutErrorのテストクラス."""

    def test_query_timeout_error_creation(self):
        """クエリタイムアウトエラーの作成テスト."""
        error = QueryTimeoutError("Query did not complete within 30 seconds")
        assert "30 seconds" in str(error)
        assert isinstance(error, CloudWatchLogsError)

    def test_timeout_with_query_id(self):
        """クエリIDを含むタイムアウトエラーテスト."""
        error = QueryTimeoutError(
            "Query test-query-id-12345 did not complete within 60 seconds"
        )
        
        assert "test-query-id-12345" in str(error)
        assert "60 seconds" in str(error)

    def test_agents_timeout_handling(self):
        """AWS Strands Agentsでのタイムアウト処理テスト."""
        query_id = "agents-query-789"
        timeout_seconds = 120
        
        error = QueryTimeoutError(
            f"Query {query_id} did not complete within {timeout_seconds} seconds. "
            f"Use get_logs_insight_query_results to try again."
        )
        
        error_str = str(error)
        assert query_id in error_str
        assert str(timeout_seconds) in error_str
        assert "get_logs_insight_query_results" in error_str


@pytest.mark.unit
@pytest.mark.aws_agents
class TestQueryExecutionError:
    """QueryExecutionErrorのテストクラス."""

    def test_query_execution_error_creation(self):
        """クエリ実行エラーの作成テスト."""
        error = QueryExecutionError("Query execution failed")
        assert str(error) == "Query execution failed"
        assert isinstance(error, CloudWatchLogsError)

    def test_syntax_error_message(self):
        """クエリ構文エラーメッセージテスト."""
        error = QueryExecutionError(
            "Invalid query syntax: Unexpected token 'invalid' at line 1"
        )
        
        assert "Invalid query syntax" in str(error)
        assert "Unexpected token" in str(error)

    def test_resource_not_found_error(self):
        """リソース未発見エラーテスト."""
        error = QueryExecutionError(
            "Log group '/aws/lambda/nonexistent' does not exist"
        )
        
        assert "Log group" in str(error)
        assert "nonexistent" in str(error)
        assert "does not exist" in str(error)


@pytest.mark.unit
@pytest.mark.aws_agents
class TestExceptionHierarchy:
    """例外階層のテストクラス."""

    def test_all_custom_exceptions_inherit_base(self):
        """すべてのカスタム例外がベースクラスを継承することのテスト."""
        exceptions = [
            InvalidParameterError("test"),
            AWSClientError("test"),
            QueryTimeoutError("test"),
            QueryExecutionError("test")
        ]
        
        for exc in exceptions:
            assert isinstance(exc, CloudWatchLogsError)
            assert isinstance(exc, Exception)

    def test_exception_catching_patterns(self):
        """例外キャッチパターンのテスト."""
        # 具体的な例外をベースクラスでキャッチできることを確認
        with pytest.raises(CloudWatchLogsError):
            raise InvalidParameterError("Parameter error")
        
        with pytest.raises(CloudWatchLogsError):
            raise AWSClientError("AWS error")
        
        with pytest.raises(CloudWatchLogsError):
            raise QueryTimeoutError("Timeout error")
        
        with pytest.raises(CloudWatchLogsError):
            raise QueryExecutionError("Execution error")

    def test_exception_type_checking(self):
        """例外タイプチェックのテスト."""
        # AWS Strands Agentsでの使用パターン
        def handle_cloudwatch_error(error):
            if isinstance(error, InvalidParameterError):
                return "parameter_error"
            elif isinstance(error, AWSClientError):
                return "aws_error"
            elif isinstance(error, QueryTimeoutError):
                return "timeout_error"
            elif isinstance(error, QueryExecutionError):
                return "execution_error"
            elif isinstance(error, CloudWatchLogsError):
                return "general_error"
            else:
                return "unknown_error"
        
        assert handle_cloudwatch_error(InvalidParameterError("test")) == "parameter_error"
        assert handle_cloudwatch_error(AWSClientError("test")) == "aws_error"
        assert handle_cloudwatch_error(QueryTimeoutError("test")) == "timeout_error"
        assert handle_cloudwatch_error(QueryExecutionError("test")) == "execution_error"
        assert handle_cloudwatch_error(CloudWatchLogsError("test")) == "general_error"

    def test_error_message_preservation(self):
        """エラーメッセージの保持テスト."""
        original_message = "Original error message with details"
        
        exceptions = [
            CloudWatchLogsError(original_message),
            InvalidParameterError(original_message),
            AWSClientError(original_message),
            QueryTimeoutError(original_message),
            QueryExecutionError(original_message)
        ]
        
        for exc in exceptions:
            assert str(exc) == original_message


@pytest.mark.unit
@pytest.mark.aws_agents
class TestExceptionUsagePatterns:
    """AWS Strands Agents用の例外使用パターンテスト."""

    def test_parameter_validation_pattern(self):
        """パラメータバリデーションパターンのテスト."""
        def validate_log_group_parameters(log_group_names, log_group_identifiers):
            """実際のバリデーション関数のシミュレーション."""
            if bool(log_group_names) == bool(log_group_identifiers):
                raise InvalidParameterError(
                    'Exactly one of log_group_names or log_group_identifiers must be provided'
                )
        
        # 正常ケース
        validate_log_group_parameters(['group1'], None)
        validate_log_group_parameters(None, ['id1'])
        
        # エラーケース
        with pytest.raises(InvalidParameterError):
            validate_log_group_parameters(['group1'], ['id1'])  # 両方指定
        
        with pytest.raises(InvalidParameterError):
            validate_log_group_parameters(None, None)  # 両方未指定

    def test_aws_error_wrapping_pattern(self):
        """AWSエラーラッピングパターンのテスト."""
        def create_aws_client_simulation():
            """AWS クライアント作成のシミュレーション."""
            try:
                # 実際のAWSエラーをシミュレート
                raise Exception("NoCredentialsError: Unable to locate credentials")
            except Exception as e:
                raise AWSClientError(f"Failed to create AWS client: {str(e)}")
        
        with pytest.raises(AWSClientError) as exc_info:
            create_aws_client_simulation()
        
        error_message = str(exc_info.value)
        assert "Failed to create AWS client" in error_message
        assert "NoCredentialsError" in error_message

    def test_timeout_handling_pattern(self):
        """タイムアウトハンドリングパターンのテスト."""
        def simulate_query_polling(max_timeout):
            """クエリポーリングのシミュレーション."""
            query_id = "test-query-123"
            
            # タイムアウトをシミュレート
            if max_timeout < 10:
                raise QueryTimeoutError(
                    f"Query {query_id} did not complete within {max_timeout} seconds. "
                    f"Use get_logs_insight_query_results with the returned queryId to try again."
                )
            
            return {"queryId": query_id, "status": "Complete"}
        
        # 正常ケース
        result = simulate_query_polling(30)
        assert result["status"] == "Complete"
        
        # タイムアウトケース
        with pytest.raises(QueryTimeoutError) as exc_info:
            simulate_query_polling(5)
        
        error_message = str(exc_info.value)
        assert "test-query-123" in error_message
        assert "5 seconds" in error_message
        assert "get_logs_insight_query_results" in error_message

    def test_error_serialization_for_agents(self):
        """AWS Strands Agents用のエラーシリアライゼーションテスト."""
        def serialize_error_for_agents(error):
            """エラーをAWS Strands Agents用にシリアライズする関数."""
            return {
                "error_type": type(error).__name__,
                "error_message": str(error),
                "is_retryable": isinstance(error, (QueryTimeoutError, AWSClientError)),
                "is_user_error": isinstance(error, InvalidParameterError)
            }
        
        # 各種エラーのシリアライゼーション
        param_error = InvalidParameterError("Invalid parameter")
        serialized = serialize_error_for_agents(param_error)
        
        assert serialized["error_type"] == "InvalidParameterError"
        assert serialized["error_message"] == "Invalid parameter"
        assert serialized["is_retryable"] is False
        assert serialized["is_user_error"] is True
        
        # AWSエラーの場合
        aws_error = AWSClientError("AWS service error")
        serialized = serialize_error_for_agents(aws_error)
        
        assert serialized["error_type"] == "AWSClientError"
        assert serialized["is_retryable"] is True
        assert serialized["is_user_error"] is False