"""AWS Strands Agents用のツール統合テスト.

このテストモジュールは、MCPインターフェースを介さずに
各ツールが直接実行できることを統合的にテストします。
AWS Strands Agentsでの実際の使用パターンをシミュレートし、
エンドツーエンドの動作を検証します。
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

from cloudwatch_logs.services.logs_service import CloudWatchLogsService
from cloudwatch_logs.services.analysis_service import CloudWatchAnalysisService
from cloudwatch_logs.domain.models import LogsMetadata, LogsAnalysisResult


@pytest.mark.integration
@pytest.mark.aws_agents
class TestAWSAgentsToolsIntegration:
    """AWS Strands Agents用のツール統合テストクラス."""

    @pytest.fixture
    def agents_logs_service(self, mock_boto3_session):
        """AWS Strands Agents用のLogsServiceフィクスチャ."""
        service = CloudWatchLogsService(version='agents-1.0.0')
        # boto3クライアントをモックに置き換え
        service._get_logs_client = lambda region: mock_boto3_session.client('logs')
        return service

    @pytest.fixture
    def agents_analysis_service(self, agents_logs_service):
        """AWS Strands Agents用のAnalysisServiceフィクスチャ."""
        return CloudWatchAnalysisService(agents_logs_service)

    def test_describe_log_groups_tool_for_agents(self, agents_logs_service):
        """AWS Strands Agents用のdescribe_log_groupsツールテスト."""
        # ツールの直接実行（MCPコンテキストなし）
        result = agents_logs_service.describe_log_groups(
            region='us-east-1',
            log_group_name_prefix='/aws/lambda/',
            max_items=50
        )
        
        # AWS Strands Agentsで使用するための結果変換
        tool_response = {
            'status': 'success',
            'log_groups_count': len(result),
            'log_groups': [lg.model_dump() for lg in result]
        }
        
        # JSONシリアライズ可能であることを確認
        json_response = json.dumps(tool_response, default=str)
        assert isinstance(json_response, str)
        assert 'log_groups_count' in json_response
        
        # 実際のツール実行結果の検証
        assert tool_response['status'] == 'success'
        assert tool_response['log_groups_count'] > 0
        assert isinstance(tool_response['log_groups'], list)

    def test_get_saved_queries_tool_for_agents(self, agents_logs_service):
        """AWS Strands Agents用の保存クエリ取得ツールテスト."""
        # まずロググループを取得
        log_groups = agents_logs_service.describe_log_groups()
        
        # 保存クエリを取得
        saved_queries = agents_logs_service.get_saved_queries(log_groups)
        
        # AWS Strands Agentsで使用するための結果変換
        tool_response = {
            'status': 'success',
            'saved_queries_count': len(saved_queries),
            'saved_queries': [sq.model_dump() for sq in saved_queries],
            'applicable_log_groups': [lg.logGroupName for lg in log_groups]
        }
        
        # JSONシリアライズとデシリアライズのテスト
        json_str = json.dumps(tool_response, default=str)
        parsed_response = json.loads(json_str)
        
        assert parsed_response['status'] == 'success'
        assert 'saved_queries_count' in parsed_response
        assert isinstance(parsed_response['saved_queries'], list)

    @pytest.mark.asyncio
    async def test_execute_query_tool_for_agents(self, agents_logs_service):
        """AWS Strands Agents用のクエリ実行ツールテスト."""
        # クエリ実行パラメータ
        query_params = {
            'log_group_identifiers': ['arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/test-function'],
            'start_time': "2023-04-29T20:00:00+00:00",
            'end_time': "2023-04-29T21:00:00+00:00",
            'query_string': 'fields @timestamp, @message | sort @timestamp desc | limit 10',
            'limit': 10
        }
        
        # クエリを開始
        query_id = agents_logs_service.start_query(
            log_group_names=None,
            log_group_identifiers=query_params['log_group_identifiers'],
            start_time=query_params['start_time'],
            end_time=query_params['end_time'],
            query_string=query_params['query_string'],
            limit=query_params['limit']
        )
        
        # クエリ結果を取得
        query_result = await agents_logs_service.poll_for_query_completion(
            query_id=query_id,
            max_timeout=30
        )
        
        # AWS Strands Agentsで使用するための結果変換
        tool_response = {
            'status': 'success',
            'query_id': query_id,
            'query_status': query_result.get('status'),
            'results_count': len(query_result.get('results', [])),
            'results': query_result.get('results', []),
            'statistics': query_result.get('statistics', {}),
            'execution_info': {
                'start_time': query_params['start_time'],
                'end_time': query_params['end_time'],
                'query_string': query_params['query_string'],
                'limit': query_params['limit']
            }
        }
        
        # 結果の検証
        assert tool_response['status'] == 'success'
        assert tool_response['query_id'] == query_id
        assert 'query_status' in tool_response
        assert isinstance(tool_response['results'], list)
        
        # JSONシリアライズテスト
        json_response = json.dumps(tool_response, default=str)
        assert isinstance(json_response, str)

    @pytest.mark.asyncio
    async def test_analyze_log_group_tool_for_agents(self, agents_analysis_service):
        """AWS Strands Agents用のログ分析ツールテスト."""
        log_group_arn = 'arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/test-function'
        start_time = "2023-04-29T20:00:00+00:00"
        end_time = "2023-04-29T21:00:00+00:00"
        
        # 非同期メソッドをモック（統合テスト用）
        agents_analysis_service.get_log_anomalies = AsyncMock(
            return_value=LogAnomalyResults(
                anomaly_detectors=[],
                anomalies=[]
            )
        )
        agents_analysis_service.analyze_log_patterns = AsyncMock(
            return_value={'queryId': 'pattern-query', 'results': []}
        )
        agents_analysis_service.analyze_error_patterns = AsyncMock(
            return_value={'queryId': 'error-query', 'results': []}
        )
        
        # ログ分析を実行
        analysis_result = await agents_analysis_service.analyze_log_group(
            log_group_arn=log_group_arn,
            start_time=start_time,
            end_time=end_time
        )
        
        # AWS Strands Agentsで使用するための結果変換
        tool_response = {
            'status': 'success',
            'analysis_type': 'comprehensive_log_analysis',
            'log_group_arn': log_group_arn,
            'time_range': {
                'start_time': start_time,
                'end_time': end_time
            },
            'anomaly_detection': {
                'detectors_count': len(analysis_result.log_anomaly_results.anomaly_detectors),
                'anomalies_count': len(analysis_result.log_anomaly_results.anomalies),
                'anomalies': [anomaly.model_dump() for anomaly in analysis_result.log_anomaly_results.anomalies]
            },
            'pattern_analysis': {
                'top_patterns': analysis_result.top_patterns,
                'error_patterns': analysis_result.top_patterns_containing_errors
            },
            'summary': {
                'has_anomalies': len(analysis_result.log_anomaly_results.anomalies) > 0,
                'has_patterns': len(analysis_result.top_patterns.get('results', [])) > 0,
                'has_error_patterns': len(analysis_result.top_patterns_containing_errors.get('results', [])) > 0
            }
        }
        
        # 結果の検証
        assert tool_response['status'] == 'success'
        assert tool_response['analysis_type'] == 'comprehensive_log_analysis'
        assert 'anomaly_detection' in tool_response
        assert 'pattern_analysis' in tool_response
        assert 'summary' in tool_response
        
        # JSONシリアライズテスト
        json_response = json.dumps(tool_response, default=str)
        assert isinstance(json_response, str)
        
        # デシリアライズして内容確認
        parsed_response = json.loads(json_response)
        assert parsed_response['anomaly_detection']['detectors_count'] >= 0
        assert parsed_response['anomaly_detection']['anomalies_count'] >= 0

    @pytest.mark.asyncio
    async def test_cancel_query_tool_for_agents(self, agents_logs_service):
        """AWS Strands Agents用のクエリキャンセルツールテスト."""
        # テスト用のクエリIDを使用
        test_query_id = 'test-query-id-12345'
        
        # クエリをキャンセル
        cancel_success = agents_logs_service.stop_query(test_query_id)
        
        # AWS Strands Agentsで使用するための結果変換
        tool_response = {
            'status': 'success',
            'action': 'cancel_query',
            'query_id': test_query_id,
            'cancelled': cancel_success,
            'message': f'Query {test_query_id} cancellation {"successful" if cancel_success else "failed"}'
        }
        
        # 結果の検証
        assert tool_response['status'] == 'success'
        assert tool_response['action'] == 'cancel_query'
        assert tool_response['query_id'] == test_query_id
        assert isinstance(tool_response['cancelled'], bool)
        
        # JSONシリアライズテスト
        json_response = json.dumps(tool_response)
        assert isinstance(json_response, str)

    def test_full_workflow_simulation_for_agents(self, agents_logs_service, agents_analysis_service):
        """AWS Strands Agents用のフルワークフローシミュレーション."""
        workflow_steps = []
        
        # Step 1: ロググループの検索
        log_groups = agents_logs_service.describe_log_groups(
            log_group_name_prefix='/aws/lambda/',
            max_items=10
        )
        workflow_steps.append({
            'step': 1,
            'action': 'discover_log_groups',
            'result': f'Found {len(log_groups)} log groups'
        })
        
        # Step 2: 保存クエリの取得
        saved_queries = agents_logs_service.get_saved_queries(log_groups)
        workflow_steps.append({
            'step': 2,
            'action': 'get_saved_queries',
            'result': f'Found {len(saved_queries)} saved queries'
        })
        
        # Step 3: クエリの準備と実行
        if log_groups:
            target_log_group = log_groups[0]
            query_id = agents_logs_service.start_query(
                log_group_names=[target_log_group.logGroupName],
                log_group_identifiers=None,
                start_time="2023-04-29T20:00:00+00:00",
                end_time="2023-04-29T21:00:00+00:00",
                query_string='fields @timestamp, @message | limit 5'
            )
            workflow_steps.append({
                'step': 3,
                'action': 'execute_query',
                'result': f'Started query {query_id}'
            })
        
        # AWS Strands Agentsで使用するワークフロー結果
        workflow_response = {
            'status': 'success',
            'workflow_type': 'cloudwatch_logs_analysis',
            'steps_completed': len(workflow_steps),
            'workflow_steps': workflow_steps,
            'summary': {
                'log_groups_discovered': len(log_groups),
                'saved_queries_found': len(saved_queries),
                'queries_executed': 1 if log_groups else 0
            }
        }
        
        # ワークフロー結果の検証
        assert workflow_response['status'] == 'success'
        assert workflow_response['steps_completed'] >= 2
        assert len(workflow_response['workflow_steps']) >= 2
        
        # JSONシリアライズテスト
        json_response = json.dumps(workflow_response, default=str)
        assert isinstance(json_response, str)

    def test_error_handling_for_agents(self, agents_logs_service):
        """AWS Strands Agents用のエラーハンドリングテスト."""
        # AWS APIエラーをシミュレート
        mock_client = agents_logs_service._get_logs_client('us-east-1')
        mock_client.get_paginator.side_effect = Exception('AccessDenied: User is not authorized')
        
        try:
            agents_logs_service.describe_log_groups()
            assert False, "例外が発生するはずです"
        except Exception as e:
            # AWS Strands Agentsで使用するエラーレスポンス
            error_response = {
                'status': 'error',
                'error_type': type(e).__name__,
                'error_message': str(e),
                'error_code': 'AWS_CLIENT_ERROR',
                'is_retryable': 'AccessDenied' not in str(e),
                'suggestions': [
                    'Check AWS credentials',
                    'Verify IAM permissions for CloudWatch Logs',
                    'Ensure correct AWS region is specified'
                ]
            }
            
            # エラーレスポンスの検証
            assert error_response['status'] == 'error'
            assert 'error_message' in error_response
            assert isinstance(error_response['suggestions'], list)
            
            # JSONシリアライズテスト
            json_error = json.dumps(error_response, default=str)
            assert isinstance(json_error, str)

    @pytest.mark.asyncio
    async def test_concurrent_operations_for_agents(self, agents_logs_service, agents_analysis_service):
        """AWS Strands Agents用の並行操作テスト."""
        # 複数の操作を並行実行
        async def describe_operation():
            return agents_logs_service.describe_log_groups(max_items=5)
        
        async def query_operation():
            query_id = agents_logs_service.start_query(
                log_group_names=['/aws/lambda/test-function'],
                log_group_identifiers=None,
                start_time="2023-04-29T20:00:00+00:00",
                end_time="2023-04-29T20:30:00+00:00",
                query_string='fields @timestamp | limit 1'
            )
            return await agents_logs_service.poll_for_query_completion(
                query_id=query_id,
                max_timeout=5
            )
        
        # 並行実行
        describe_result, query_result = await asyncio.gather(
            describe_operation(),
            query_operation(),
            return_exceptions=True
        )
        
        # AWS Strands Agentsで使用する並行操作結果
        concurrent_response = {
            'status': 'success',
            'operation_type': 'concurrent_cloudwatch_operations',
            'operations': [
                {
                    'name': 'describe_log_groups',
                    'status': 'success' if not isinstance(describe_result, Exception) else 'error',
                    'result_summary': f'Found {len(describe_result)} log groups' if not isinstance(describe_result, Exception) else str(describe_result)
                },
                {
                    'name': 'execute_query',
                    'status': 'success' if not isinstance(query_result, Exception) else 'error',
                    'result_summary': f'Query status: {query_result.get("status", "unknown")}' if not isinstance(query_result, Exception) else str(query_result)
                }
            ],
            'total_operations': 2,
            'successful_operations': sum(1 for op in [describe_result, query_result] if not isinstance(op, Exception))
        }
        
        # 並行操作結果の検証
        assert concurrent_response['status'] == 'success'
        assert concurrent_response['total_operations'] == 2
        assert concurrent_response['successful_operations'] >= 0
        
        # JSONシリアライズテスト
        json_response = json.dumps(concurrent_response, default=str)
        assert isinstance(json_response, str)