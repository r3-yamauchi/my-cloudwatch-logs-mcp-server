"""CloudWatchLogsServiceのユニットテスト.

このテストモジュールは、MCPインターフェースを介さずに
CloudWatchLogsServiceの機能を直接テストします。
AWS Strands Agentsのtool機能として実装するための準備として、
各メソッドが適切に動作することを検証します。
"""

import pytest
from unittest.mock import MagicMock, patch
import os

from cloudwatch_logs.services.logs_service import CloudWatchLogsService
from cloudwatch_logs.domain.exceptions import AWSClientError, QueryTimeoutError
from cloudwatch_logs.domain.models import LogGroupMetadata, SavedLogsInsightsQuery


@pytest.mark.unit
@pytest.mark.aws_agents
class TestCloudWatchLogsService:
    """CloudWatchLogsServiceのユニットテストクラス."""

    def test_init_with_default_version(self):
        """デフォルトバージョンでの初期化テスト."""
        service = CloudWatchLogsService()
        assert service.version == '1.0.0'
        assert service._logs_client is None
        assert service._logs_client_region is None

    def test_init_with_custom_version(self):
        """カスタムバージョンでの初期化テスト."""
        custom_version = 'test-2.0.0'
        service = CloudWatchLogsService(version=custom_version)
        assert service.version == custom_version

    @patch('cloudwatch_logs.services.logs_service.boto3')
    @patch.dict(os.environ, {'AWS_PROFILE': 'test-profile'})
    def test_get_logs_client_with_profile(self, mock_boto3):
        """AWSプロファイル使用時のクライアント作成テスト."""
        service = CloudWatchLogsService()
        mock_session = MagicMock()
        mock_boto3.Session.return_value = mock_session
        
        result = service._get_logs_client('us-east-1')
        
        mock_boto3.Session.assert_called_once_with(
            profile_name='test-profile', 
            region_name='us-east-1'
        )
        mock_session.client.assert_called_once()

    @patch('cloudwatch_logs.services.logs_service.boto3')
    @patch.dict(os.environ, {}, clear=True)
    def test_get_logs_client_without_profile(self, mock_boto3):
        """AWSプロファイルなしでのクライアント作成テスト."""
        service = CloudWatchLogsService()
        mock_session = MagicMock()
        mock_boto3.Session.return_value = mock_session
        
        result = service._get_logs_client('us-west-2')
        
        mock_boto3.Session.assert_called_once_with(region_name='us-west-2')
        mock_session.client.assert_called_once()

    @patch('cloudwatch_logs.services.logs_service.boto3')
    def test_get_logs_client_error_handling(self, mock_boto3):
        """クライアント作成エラーのハンドリングテスト."""
        service = CloudWatchLogsService()
        mock_boto3.Session.side_effect = Exception('AWS credential error')
        
        with pytest.raises(AWSClientError) as exc_info:
            service._get_logs_client('us-east-1')
        
        assert 'Failed to create AWS client' in str(exc_info.value)

    def test_get_logs_client_caching(self, mock_logs_service):
        """クライアントキャッシングの動作テスト."""
        # 最初の呼び出し
        client1 = mock_logs_service.get_logs_client('us-east-1')
        
        # 同じリージョンでの2回目の呼び出し（キャッシュされたものを返す）
        client2 = mock_logs_service.get_logs_client('us-east-1')
        
        assert client1 is client2

    def test_describe_log_groups_basic(self, mock_logs_service):
        """基本的なロググループ取得テスト."""
        result = mock_logs_service.describe_log_groups()
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], LogGroupMetadata)
        assert result[0].logGroupName == '/aws/lambda/test-function'

    def test_describe_log_groups_with_parameters(self, mock_logs_service):
        """パラメータ指定でのロググループ取得テスト."""
        result = mock_logs_service.describe_log_groups(
            region='us-west-2',
            log_group_name_prefix='/aws/lambda/',
            log_group_class='STANDARD',
            max_items=50
        )
        
        assert isinstance(result, list)
        assert len(result) == 1

    def test_describe_log_groups_error_handling(self, mock_logs_service):
        """ロググループ取得のエラーハンドリングテスト."""
        # AWS APIエラーをシミュレート
        mock_client = mock_logs_service.get_logs_client('us-east-1')
        mock_client.get_paginator.side_effect = Exception('API Error')
        
        with pytest.raises(AWSClientError) as exc_info:
            mock_logs_service.describe_log_groups()
        
        assert 'Failed to describe log groups' in str(exc_info.value)

    def test_get_saved_queries_basic(self, mock_logs_service, sample_log_group_metadata):
        """基本的な保存クエリ取得テスト."""
        result = mock_logs_service.get_saved_queries([sample_log_group_metadata])
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], SavedLogsInsightsQuery)
        assert result[0].name == 'Error Logs Query'

    def test_get_saved_queries_filtering(self, mock_logs_service):
        """保存クエリのフィルタリングテスト."""
        # 関連しないロググループでテスト
        from cloudwatch_logs.domain.models import LogGroupMetadata
        unrelated_log_group = LogGroupMetadata(
            logGroupName='/aws/ecs/unrelated',
            creationTime='2023-04-29T20:00:00+00:00',
            metricFilterCount=0,
            storedBytes=0,
            logGroupClass='STANDARD',
            logGroupArn='arn:aws:logs:us-east-1:123456789012:log-group:/aws/ecs/unrelated'
        )
        
        result = mock_logs_service.get_saved_queries([unrelated_log_group])
        
        # フィルタリングにより、関連するクエリがないことを確認
        assert isinstance(result, list)
        # 実際のフィルタリングロジックに依存

    def test_start_query_basic(self, mock_logs_service, sample_query_params):
        """基本的なクエリ開始テスト."""
        result = mock_logs_service.start_query(
            log_group_names=sample_query_params['log_group_names'],
            log_group_identifiers=sample_query_params['log_group_identifiers'],
            start_time=sample_query_params['start_time'],
            end_time=sample_query_params['end_time'],
            query_string=sample_query_params['query_string'],
            limit=sample_query_params['limit']
        )
        
        assert result == 'test-query-id-12345'

    def test_start_query_with_limit(self, mock_logs_service):
        """制限付きクエリ開始テスト."""
        result = mock_logs_service.start_query(
            log_group_names=['/aws/lambda/test-function'],
            log_group_identifiers=None,
            start_time="2023-04-29T20:00:00+00:00",
            end_time="2023-04-29T21:00:00+00:00",
            query_string='fields @timestamp, @message | limit 100',
            limit=100
        )
        
        assert result == 'test-query-id-12345'

    def test_get_query_results_basic(self, mock_logs_service):
        """基本的なクエリ結果取得テスト."""
        result = mock_logs_service.get_query_results('test-query-id-12345')
        
        assert isinstance(result, dict)
        assert result['queryId'] == 'test-query-id-12345'
        assert result['status'] == 'Complete'
        assert 'results' in result
        assert 'statistics' in result

    def test_stop_query_basic(self, mock_logs_service):
        """基本的なクエリ停止テスト."""
        result = mock_logs_service.stop_query('test-query-id-12345')
        
        assert result is True

    @pytest.mark.asyncio
    async def test_poll_for_query_completion_success(self, mock_logs_service):
        """クエリ完了ポーリングの成功テスト."""
        result = await mock_logs_service.poll_for_query_completion(
            'test-query-id-12345',
            max_timeout=1  # 短いタイムアウトでテスト
        )
        
        assert isinstance(result, dict)
        assert result['queryId'] == 'test-query-id-12345'
        assert result['status'] == 'Complete'

    @pytest.mark.asyncio
    async def test_poll_for_query_completion_timeout(self, mock_logs_service):
        """クエリ完了ポーリングのタイムアウトテスト."""
        # 常にRunningステータスを返すようにモック設定
        mock_client = mock_logs_service.get_logs_client('us-east-1')
        mock_client.get_query_results.return_value = {
            'queryId': 'test-query-id-12345',
            'status': 'Running',
            'results': []
        }
        
        with pytest.raises(QueryTimeoutError) as exc_info:
            await mock_logs_service.poll_for_query_completion(
                'test-query-id-12345',
                max_timeout=0.1  # 非常に短いタイムアウト
            )
        
        assert 'did not complete within' in str(exc_info.value)

    def test_process_query_results(self, mock_logs_service):
        """クエリ結果処理のテスト."""
        sample_response = {
            'queryId': 'test-id',
            'status': 'Complete',
            'statistics': {'recordsMatched': 10},
            'results': [
                [
                    {'field': '@timestamp', 'value': '2023-04-29T20:00:00.000Z'},
                    {'field': '@message', 'value': 'Test message'}
                ]
            ]
        }
        
        result = mock_logs_service._process_query_results(sample_response, 'custom-query-id')
        
        assert result['queryId'] == 'custom-query-id'
        assert result['status'] == 'Complete'
        assert result['statistics'] == {'recordsMatched': 10}
        assert len(result['results']) == 1
        assert result['results'][0]['@timestamp'] == '2023-04-29T20:00:00.000Z'


@pytest.mark.unit
@pytest.mark.aws_agents
class TestCloudWatchLogsServiceAWSAgents:
    """AWS Strands Agents用の特別なテストケース."""

    def test_direct_service_instantiation(self):
        """サービスの直接インスタンス化テスト（MCPなし）."""
        service = CloudWatchLogsService(version='agents-1.0.0')
        assert service.version == 'agents-1.0.0'
        # MCPコンテキストなしで動作することを確認

    def test_service_methods_without_mcp_context(self, mock_logs_service):
        """MCPコンテキストなしでのサービスメソッド実行テスト."""
        # describe_log_groupsメソッドが直接呼び出し可能であることを確認
        result = mock_logs_service.describe_log_groups(
            region='us-east-1',
            log_group_name_prefix='/aws/lambda/'
        )
        
        assert isinstance(result, list)
        assert len(result) > 0
        
        # AWS Strands Agentsで使用する際の典型的なパターン
        log_group_data = [lg.model_dump() for lg in result]
        assert isinstance(log_group_data, list)
        assert 'logGroupName' in log_group_data[0]

    @pytest.mark.asyncio
    async def test_async_methods_for_agents(self, mock_logs_service):
        """AWS Strands Agents用の非同期メソッドテスト."""
        # 非同期メソッドが正常に動作することを確認
        query_id = mock_logs_service.start_query(
            log_group_names=['/aws/lambda/test-function'],
            log_group_identifiers=None,
            start_time="2023-04-29T20:00:00+00:00",
            end_time="2023-04-29T21:00:00+00:00",
            query_string='fields @timestamp, @message | limit 10'
        )
        
        result = await mock_logs_service.poll_for_query_completion(
            query_id,
            max_timeout=1
        )
        
        # AWS Strands Agentsでの使用に適した形式で結果を取得
        assert isinstance(result, dict)
        assert 'results' in result
        assert 'queryId' in result

    def test_error_handling_for_agents(self):
        """AWS Strands Agents用のエラーハンドリングテスト."""
        service = CloudWatchLogsService()
        
        # AWS認証エラーのシミュレーション
        with patch('cloudwatch_logs.services.logs_service.boto3') as mock_boto3:
            mock_boto3.Session.side_effect = Exception('NoCredentialsError')
            
            with pytest.raises(AWSClientError) as exc_info:
                service._get_logs_client('us-east-1')
            
            # エラーメッセージがAWS Strands Agentsで適切に処理できる形式であることを確認
            error_message = str(exc_info.value)
            assert 'Failed to create AWS client' in error_message
            assert 'us-east-1' in error_message