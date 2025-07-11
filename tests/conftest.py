"""テスト設定とフィクスチャの定義.

このモジュールはpytestのテスト設定と共通のフィクスチャを定義します。
AWS Strands Agents用のツール機能として使用するためのテスト環境を構築し、
MCPインターフェースを介さない直接的なテストを可能にします。
"""

import asyncio
import pytest
from typing import Any, Dict
from unittest.mock import MagicMock


# テスト用のサンプルデータ
SAMPLE_LOG_GROUP = {
    'logGroupName': '/aws/lambda/test-function',
    'creationTime': 1682798400000,  # 2023-04-29T20:00:00Z
    'retentionInDays': 14,
    'metricFilterCount': 2,
    'storedBytes': 1024000,
    'kmsKeyId': 'arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012',
    'dataProtectionStatus': 'ACTIVATED',
    'inheritedProperties': ['ACCOUNT_DATA_PROTECTION'],
    'logGroupClass': 'STANDARD',
    'logGroupArn': 'arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/test-function'
}

SAMPLE_SAVED_QUERY = {
    'name': 'Error Logs Query',
    'queryString': 'fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc | limit 100',
    'logGroupNames': ['/aws/lambda/test-function']
}

SAMPLE_ANOMALY_DETECTOR = {
    'anomalyDetectorArn': 'arn:aws:logs:us-east-1:123456789012:anomaly-detector/test-detector',
    'detectorName': 'test-detector',
    'anomalyDetectorStatus': 'ACTIVE'
}

SAMPLE_ANOMALY = {
    'anomalyDetectorArn': 'arn:aws:logs:us-east-1:123456789012:anomaly-detector/test-detector',
    'logGroupArnList': ['arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/test-function'],
    'firstSeen': 1682798400000,
    'lastSeen': 1682798460000,
    'description': 'Unusual error pattern detected',
    'priority': 'HIGH',
    'patternRegex': 'ERROR.*connection.*timeout',
    'patternString': 'ERROR connection timeout',
    'logSamples': [
        {
            'timestamp': 1682798430000,
            'message': 'ERROR connection timeout occurred'
        }
    ],
    'histogram': {
        '1682798400000': 5,
        '1682798430000': 3,
        '1682798460000': 2
    }
}

SAMPLE_QUERY_RESULT = {
    'queryId': 'test-query-id-12345',
    'status': 'Complete',
    'statistics': {
        'recordsMatched': 100,
        'recordsScanned': 1000,
        'bytesScanned': 1024000
    },
    'results': [
        [
            {'field': '@timestamp', 'value': '2023-04-29T20:00:00.000Z'},
            {'field': '@message', 'value': 'INFO Application started successfully'},
            {'field': '@ptr', 'value': 'CiQKGQoMNjQzNDU2Nzg5MDEyEgkiBwgBEB...'}
        ],
        [
            {'field': '@timestamp', 'value': '2023-04-29T20:01:00.000Z'},
            {'field': '@message', 'value': 'ERROR Failed to connect to database'},
            {'field': '@ptr', 'value': 'CiQKGQoMNjQzNDU2Nzg5MDEyEgkiBwgBEB...'}
        ]
    ]
}


@pytest.fixture
def mock_boto3_session():
    """boto3セッションのモックを作成する."""
    session_mock = MagicMock()
    client_mock = MagicMock()

    # CloudWatch Logs APIのレスポンスをモック
    client_mock.describe_log_groups.return_value = {
        'logGroups': [SAMPLE_LOG_GROUP],
        'nextToken': None
    }

    client_mock.describe_query_definitions.return_value = {
        'queryDefinitions': [SAMPLE_SAVED_QUERY],
        'nextToken': None
    }

    client_mock.list_log_anomaly_detectors.return_value = {
        'anomalyDetectors': [SAMPLE_ANOMALY_DETECTOR],
        'nextToken': None
    }

    client_mock.list_anomalies.return_value = {
        'anomalies': [SAMPLE_ANOMALY],
        'nextToken': None
    }

    client_mock.start_query.return_value = {
        'queryId': 'test-query-id-12345'
    }

    client_mock.get_query_results.return_value = SAMPLE_QUERY_RESULT

    client_mock.stop_query.return_value = {
        'success': True
    }

    # ページネーターのモック
    paginator_mock = MagicMock()
    paginator_mock.paginate.return_value = [
        {'logGroups': [SAMPLE_LOG_GROUP]},
    ]
    client_mock.get_paginator.return_value = paginator_mock

    session_mock.client.return_value = client_mock
    return session_mock


@pytest.fixture
def mock_logs_service(mock_boto3_session):
    """CloudWatchLogsServiceのモックを作成する."""
    from cloudwatch_logs.services.logs_service import CloudWatchLogsService

    service = CloudWatchLogsService(version='test-1.0.0')
    # boto3クライアントをモックに置き換え
    service._get_logs_client = lambda region: mock_boto3_session.client('logs')
    return service


@pytest.fixture
def mock_analysis_service(mock_logs_service):
    """CloudWatchAnalysisServiceのモックを作成する."""
    from cloudwatch_logs.services.analysis_service import CloudWatchAnalysisService

    return CloudWatchAnalysisService(mock_logs_service)


@pytest.fixture
def sample_log_group_metadata():
    """サンプルのロググループメタデータを提供する."""
    from cloudwatch_logs.domain.models import LogGroupMetadata
    return LogGroupMetadata.model_validate(SAMPLE_LOG_GROUP)


@pytest.fixture
def sample_saved_query():
    """サンプルの保存クエリを提供する."""
    from cloudwatch_logs.domain.models import SavedLogsInsightsQuery
    return SavedLogsInsightsQuery.model_validate(SAMPLE_SAVED_QUERY)


@pytest.fixture
def sample_anomaly_detector():
    """サンプルの異常検知器を提供する."""
    from cloudwatch_logs.domain.models import LogAnomalyDetector
    return LogAnomalyDetector.model_validate(SAMPLE_ANOMALY_DETECTOR)


@pytest.fixture
def sample_anomaly():
    """サンプルの異常データを提供する."""
    from cloudwatch_logs.domain.models import LogAnomaly
    return LogAnomaly.model_validate(SAMPLE_ANOMALY)


@pytest.fixture
def iso_time_start():
    """テスト用の開始時間（ISO 8601形式）を提供する."""
    return "2023-04-29T20:00:00+00:00"


@pytest.fixture
def iso_time_end():
    """テスト用の終了時間（ISO 8601形式）を提供する."""
    return "2023-04-29T21:00:00+00:00"


@pytest.fixture
def sample_query_params():
    """サンプルクエリパラメータを提供する."""
    return {
        'log_group_names': None,
        'log_group_identifiers': ['arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/test-function'],
        'start_time': "2023-04-29T20:00:00+00:00",
        'end_time': "2023-04-29T21:00:00+00:00",
        'query_string': 'fields @timestamp, @message | sort @timestamp desc | limit 10',
        'limit': 10,
        'region': 'us-east-1'
    }


@pytest.fixture(scope="session")
def event_loop():
    """セッション全体で使用するイベントループを作成する."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# テストマーカーの定義
def pytest_configure(config):
    """pytestの設定を行う."""
    config.addinivalue_line(
        "markers", "unit: ユニットテスト（外部依存なし）"
    )
    config.addinivalue_line(
        "markers", "integration: 統合テスト（モック化されたAWS APIを使用）"
    )
    config.addinivalue_line(
        "markers", "slow: 実行時間が長いテスト"
    )
    config.addinivalue_line(
        "markers", "aws_agents: AWS Strands Agents用のテスト"
    )


# カスタムアサーション関数
def assert_log_group_metadata(metadata, expected_name: str = None):
    """ロググループメタデータの基本的な検証を行う."""
    assert hasattr(metadata, 'logGroupName')
    assert hasattr(metadata, 'logGroupArn')
    assert hasattr(metadata, 'creationTime')

    if expected_name:
        assert metadata.logGroupName == expected_name


def assert_query_result(result: Dict[str, Any]):
    """クエリ結果の基本的な検証を行う."""
    assert 'queryId' in result
    assert 'status' in result
    assert 'results' in result

    if result['status'] == 'Complete':
        assert isinstance(result['results'], list)


def assert_anomaly_result(result):
    """異常検知結果の基本的な検証を行う."""
    assert hasattr(result, 'anomaly_detectors')
    assert hasattr(result, 'anomalies')
    assert isinstance(result.anomaly_detectors, list)
    assert isinstance(result.anomalies, list)
