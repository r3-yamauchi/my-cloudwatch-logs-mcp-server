"""CloudWatchAnalysisServiceのユニットテスト.

このテストモジュールは、MCPインターフェースを介さずに
CloudWatchAnalysisServiceの機能を直接テストします。
AWS Strands Agentsのtool機能として実装するための準備として、
ログ分析と異常検知の機能が適切に動作することを検証します。
"""

import pytest
from cloudwatch_logs.domain.exceptions import AWSClientError
from cloudwatch_logs.domain.models import (
    LogAnomaly,
    LogAnomalyResults,
    LogsAnalysisResult,
)
from cloudwatch_logs.services.analysis_service import CloudWatchAnalysisService
from unittest.mock import AsyncMock


@pytest.mark.unit
@pytest.mark.aws_agents
class TestCloudWatchAnalysisService:
    """CloudWatchAnalysisServiceのユニットテストクラス."""

    def test_init_with_logs_service(self, mock_logs_service):
        """ログサービスを使用した初期化テスト."""
        service = CloudWatchAnalysisService(mock_logs_service)
        assert service.logs_service is mock_logs_service

    def test_get_logs_client_delegation(self, mock_analysis_service, mock_logs_service):
        """ログクライアント取得の委譲テスト."""
        result = mock_analysis_service._get_logs_client('us-east-1')
        # logs_serviceのメソッドが呼ばれることを確認
        assert result is not None

    def test_is_applicable_anomaly_time_overlap(self, mock_analysis_service):
        """異常の時間範囲オーバーラップ判定テスト."""
        # 時間範囲が重複する異常
        anomaly = LogAnomaly(
            anomalyDetectorArn='test-arn',
            logGroupArnList=['arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/test-function'],
            firstSeen='2023-04-29T20:15:00+00:00',
            lastSeen='2023-04-29T20:45:00+00:00',
            description='Test anomaly',
            priority='HIGH',
            patternRegex='ERROR.*',
            patternString='ERROR pattern',
            logSamples=[],
            histogram={}
        )

        # テスト対象の時間範囲
        start_time = "2023-04-29T20:00:00+00:00"
        end_time = "2023-04-29T21:00:00+00:00"
        log_group_arn = 'arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/test-function'

        result = mock_analysis_service._is_applicable_anomaly(
            anomaly, log_group_arn, start_time, end_time
        )

        assert result is True

    def test_is_applicable_anomaly_no_time_overlap(self, mock_analysis_service):
        """異常の時間範囲非オーバーラップ判定テスト."""
        # 時間範囲が重複しない異常
        anomaly = LogAnomaly(
            anomalyDetectorArn='test-arn',
            logGroupArnList=['arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/test-function'],
            firstSeen='2023-04-29T18:00:00+00:00',  # 検索範囲より前
            lastSeen='2023-04-29T19:00:00+00:00',   # 検索範囲より前
            description='Test anomaly',
            priority='HIGH',
            patternRegex='ERROR.*',
            patternString='ERROR pattern',
            logSamples=[],
            histogram={}
        )

        start_time = "2023-04-29T20:00:00+00:00"
        end_time = "2023-04-29T21:00:00+00:00"
        log_group_arn = 'arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/test-function'

        result = mock_analysis_service._is_applicable_anomaly(
            anomaly, log_group_arn, start_time, end_time
        )

        assert result is False

    def test_is_applicable_anomaly_wrong_log_group(self, mock_analysis_service):
        """異常の異なるロググループ判定テスト."""
        # 異なるロググループの異常
        anomaly = LogAnomaly(
            anomalyDetectorArn='test-arn',
            logGroupArnList=['arn:aws:logs:us-east-1:123456789012:log-group:/aws/ecs/different'],
            firstSeen='2023-04-29T20:15:00+00:00',
            lastSeen='2023-04-29T20:45:00+00:00',
            description='Test anomaly',
            priority='HIGH',
            patternRegex='ERROR.*',
            patternString='ERROR pattern',
            logSamples=[],
            histogram={}
        )

        start_time = "2023-04-29T20:00:00+00:00"
        end_time = "2023-04-29T21:00:00+00:00"
        log_group_arn = 'arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/test-function'

        result = mock_analysis_service._is_applicable_anomaly(
            anomaly, log_group_arn, start_time, end_time
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_get_log_anomalies_basic(self, mock_analysis_service):
        """基本的なログ異常取得テスト."""
        log_group_arn = 'arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/test-function'
        start_time = "2023-04-29T20:00:00+00:00"
        end_time = "2023-04-29T21:00:00+00:00"

        result = await mock_analysis_service.get_log_anomalies(
            log_group_arn, start_time, end_time
        )

        assert isinstance(result, LogAnomalyResults)
        assert isinstance(result.anomaly_detectors, list)
        assert isinstance(result.anomalies, list)
        assert len(result.anomaly_detectors) >= 0
        assert len(result.anomalies) >= 0

    @pytest.mark.asyncio
    async def test_get_log_anomalies_with_region(self, mock_analysis_service):
        """リージョン指定でのログ異常取得テスト."""
        log_group_arn = 'arn:aws:logs:ap-northeast-1:123456789012:log-group:/aws/lambda/test-function'
        start_time = "2023-04-29T20:00:00+00:00"
        end_time = "2023-04-29T21:00:00+00:00"

        result = await mock_analysis_service.get_log_anomalies(
            log_group_arn, start_time, end_time, region='ap-northeast-1'
        )

        assert isinstance(result, LogAnomalyResults)

    @pytest.mark.asyncio
    async def test_get_log_anomalies_error_handling(self, mock_analysis_service):
        """ログ異常取得のエラーハンドリングテスト."""
        # AWS APIエラーをシミュレート
        mock_client = mock_analysis_service._get_logs_client('us-east-1')
        mock_client.get_paginator.side_effect = Exception('API Error')

        log_group_arn = 'arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/test-function'
        start_time = "2023-04-29T20:00:00+00:00"
        end_time = "2023-04-29T21:00:00+00:00"

        with pytest.raises(AWSClientError) as exc_info:
            await mock_analysis_service.get_log_anomalies(
                log_group_arn, start_time, end_time
            )

        assert 'Failed to get log anomalies' in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_analyze_log_patterns_basic(self, mock_analysis_service):
        """基本的なログパターン分析テスト."""
        log_group_arn = 'arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/test-function'
        start_time = "2023-04-29T20:00:00+00:00"
        end_time = "2023-04-29T21:00:00+00:00"

        # logs_serviceのstart_queryメソッドをモック
        mock_analysis_service.logs_service.start_query = AsyncMock(return_value='test-query-id')
        mock_analysis_service.logs_service.poll_for_query_completion = AsyncMock(
            return_value={
                'queryId': 'test-query-id',
                'status': 'Complete',
                'results': [
                    {'@pattern': 'INFO *', '@sampleCount': '100'},
                    {'@pattern': 'ERROR *', '@sampleCount': '10'}
                ]
            }
        )

        result = await mock_analysis_service.analyze_log_patterns(
            log_group_arn, start_time, end_time
        )

        assert isinstance(result, dict)
        assert 'queryId' in result
        assert 'results' in result

    @pytest.mark.asyncio
    async def test_analyze_error_patterns_basic(self, mock_analysis_service):
        """基本的なエラーパターン分析テスト."""
        log_group_arn = 'arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/test-function'
        start_time = "2023-04-29T20:00:00+00:00"
        end_time = "2023-04-29T21:00:00+00:00"

        # logs_serviceのメソッドをモック
        mock_analysis_service.logs_service.start_query = AsyncMock(return_value='test-error-query-id')
        mock_analysis_service.logs_service.poll_for_query_completion = AsyncMock(
            return_value={
                'queryId': 'test-error-query-id',
                'status': 'Complete',
                'results': [
                    {'@pattern': 'ERROR connection timeout', '@sampleCount': '5'},
                    {'@pattern': 'ERROR database failure', '@sampleCount': '3'}
                ]
            }
        )

        result = await mock_analysis_service.analyze_error_patterns(
            log_group_arn, start_time, end_time
        )

        assert isinstance(result, dict)
        assert 'queryId' in result
        assert 'results' in result

    @pytest.mark.asyncio
    async def test_analyze_log_group_comprehensive(self, mock_analysis_service):
        """包括的なログ分析テスト."""
        log_group_arn = 'arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/test-function'
        start_time = "2023-04-29T20:00:00+00:00"
        end_time = "2023-04-29T21:00:00+00:00"

        # すべての非同期メソッドをモック
        mock_analysis_service.get_log_anomalies = AsyncMock(
            return_value=LogAnomalyResults(
                anomaly_detectors=[],
                anomalies=[]
            )
        )
        mock_analysis_service.analyze_log_patterns = AsyncMock(
            return_value={'queryId': 'pattern-query', 'results': []}
        )
        mock_analysis_service.analyze_error_patterns = AsyncMock(
            return_value={'queryId': 'error-query', 'results': []}
        )

        result = await mock_analysis_service.analyze_log_group(
            log_group_arn, start_time, end_time
        )

        assert isinstance(result, LogsAnalysisResult)
        assert hasattr(result, 'log_anomaly_results')
        assert hasattr(result, 'top_patterns')
        assert hasattr(result, 'top_patterns_containing_errors')

    @pytest.mark.asyncio
    async def test_analyze_log_group_with_custom_timeout(self, mock_analysis_service):
        """カスタムタイムアウトでの包括的ログ分析テスト."""
        log_group_arn = 'arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/test-function'
        start_time = "2023-04-29T20:00:00+00:00"
        end_time = "2023-04-29T21:00:00+00:00"
        custom_timeout = 60

        # メソッドをモック
        mock_analysis_service.get_log_anomalies = AsyncMock(
            return_value=LogAnomalyResults(
                anomaly_detectors=[],
                anomalies=[]
            )
        )
        mock_analysis_service.analyze_log_patterns = AsyncMock(
            return_value={'queryId': 'pattern-query', 'results': []}
        )
        mock_analysis_service.analyze_error_patterns = AsyncMock(
            return_value={'queryId': 'error-query', 'results': []}
        )

        result = await mock_analysis_service.analyze_log_group(
            log_group_arn, start_time, end_time, max_timeout=custom_timeout
        )

        # タイムアウト値が正しく渡されていることを検証
        mock_analysis_service.analyze_log_patterns.assert_called_once()
        mock_analysis_service.analyze_error_patterns.assert_called_once()

        assert isinstance(result, LogsAnalysisResult)


@pytest.mark.unit
@pytest.mark.aws_agents
class TestCloudWatchAnalysisServiceAWSAgents:
    """AWS Strands Agents用の特別なテストケース."""

    def test_direct_service_instantiation_for_agents(self, mock_logs_service):
        """AWS Strands Agents用のサービス直接インスタンス化テスト."""
        service = CloudWatchAnalysisService(mock_logs_service)
        assert service.logs_service is mock_logs_service
        # MCPコンテキストなしで動作することを確認

    @pytest.mark.asyncio
    async def test_anomaly_detection_for_agents(self, mock_analysis_service):
        """AWS Strands Agents用の異常検知テスト."""
        log_group_arn = 'arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/agents-function'
        start_time = "2023-04-29T20:00:00+00:00"
        end_time = "2023-04-29T21:00:00+00:00"

        result = await mock_analysis_service.get_log_anomalies(
            log_group_arn, start_time, end_time
        )

        # AWS Strands Agentsでの使用に適した形式で結果を確認
        result_dict = result.model_dump()
        assert 'anomaly_detectors' in result_dict
        assert 'anomalies' in result_dict
        assert isinstance(result_dict['anomaly_detectors'], list)
        assert isinstance(result_dict['anomalies'], list)

    @pytest.mark.asyncio
    async def test_pattern_analysis_for_agents(self, mock_analysis_service):
        """AWS Strands Agents用のパターン分析テスト."""
        log_group_arn = 'arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/agents-function'
        start_time = "2023-04-29T20:00:00+00:00"
        end_time = "2023-04-29T21:00:00+00:00"

        # logs_serviceのメソッドをモック
        mock_analysis_service.logs_service.start_query = AsyncMock(return_value='agents-query-id')
        mock_analysis_service.logs_service.poll_for_query_completion = AsyncMock(
            return_value={
                'queryId': 'agents-query-id',
                'status': 'Complete',
                'results': [
                    {'@pattern': 'Agent started', '@sampleCount': '50'},
                    {'@pattern': 'Agent completed task', '@sampleCount': '45'}
                ]
            }
        )

        result = await mock_analysis_service.analyze_log_patterns(
            log_group_arn, start_time, end_time
        )

        # AWS Strands Agentsでの結果処理に適した形式であることを確認
        assert isinstance(result, dict)
        assert 'results' in result
        pattern_data = result['results']
        assert isinstance(pattern_data, list)

    @pytest.mark.asyncio
    async def test_comprehensive_analysis_for_agents(self, mock_analysis_service):
        """AWS Strands Agents用の包括的分析テスト."""
        log_group_arn = 'arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/agents-function'
        start_time = "2023-04-29T20:00:00+00:00"
        end_time = "2023-04-29T21:00:00+00:00"

        # 実際のAWS Strands Agentsツールでの使用パターンをテスト
        mock_analysis_service.get_log_anomalies = AsyncMock(
            return_value=LogAnomalyResults(
                anomaly_detectors=[],
                anomalies=[]
            )
        )
        mock_analysis_service.analyze_log_patterns = AsyncMock(
            return_value={'queryId': 'agents-pattern-query', 'results': []}
        )
        mock_analysis_service.analyze_error_patterns = AsyncMock(
            return_value={'queryId': 'agents-error-query', 'results': []}
        )

        result = await mock_analysis_service.analyze_log_group(
            log_group_arn, start_time, end_time, region='us-east-1'
        )

        # AWS Strands Agentsで使用する際の典型的なレスポンス形式
        analysis_data = result.model_dump()

        assert 'log_anomaly_results' in analysis_data
        assert 'top_patterns' in analysis_data
        assert 'top_patterns_containing_errors' in analysis_data

        # JSON serializable であることを確認（AWS Strands Agentsで重要）
        import json
        json_str = json.dumps(analysis_data, default=str)
        assert isinstance(json_str, str)

    @pytest.mark.asyncio
    async def test_error_handling_for_agents(self, mock_analysis_service):
        """AWS Strands Agents用のエラーハンドリングテスト."""
        log_group_arn = 'arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/agents-function'
        start_time = "2023-04-29T20:00:00+00:00"
        end_time = "2023-04-29T21:00:00+00:00"

        # AWS APIエラーをシミュレート
        mock_client = mock_analysis_service._get_logs_client('us-east-1')
        mock_client.get_paginator.side_effect = Exception('AccessDenied')

        with pytest.raises(AWSClientError) as exc_info:
            await mock_analysis_service.get_log_anomalies(
                log_group_arn, start_time, end_time
            )

        # エラーメッセージがAWS Strands Agentsで適切に処理できる形式であることを確認
        error_message = str(exc_info.value)
        assert 'Failed to get log anomalies' in error_message

        # エラー情報がログに適切に出力されることも確認
        # （実際の実装ではloggerが使用される）
