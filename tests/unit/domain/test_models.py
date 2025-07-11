"""ドメインモデルのユニットテスト.

このテストモジュールは、Pydanticベースのドメインモデルの
データバリデーション、変換、シリアライゼーション機能をテストします。
AWS Strands Agentsでの使用を考慮し、JSON変換とデータ整合性を重点的に検証します。
"""

import json
import pytest
from cloudwatch_logs.domain.models import (
    LogAnomaly,
    LogAnomalyDetector,
    LogAnomalyResults,
    LogGroupMetadata,
    LogsAnalysisResult,
    LogsMetadata,
    LogsQueryCancelResult,
    SavedLogsInsightsQuery,
)
from pydantic import ValidationError


@pytest.mark.unit
@pytest.mark.aws_agents
class TestLogGroupMetadata:
    """LogGroupMetadataモデルのテストクラス."""

    def test_valid_log_group_creation(self):
        """有効なロググループメタデータの作成テスト."""
        data = {
            'logGroupName': '/aws/lambda/test-function',
            'creationTime': '2023-04-29T20:00:00+00:00',
            'retentionInDays': 14,
            'metricFilterCount': 2,
            'storedBytes': 1024000,
            'kmsKeyId': 'arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012',
            'dataProtectionStatus': 'ACTIVATED',
            'inheritedProperties': ['ACCOUNT_DATA_PROTECTION'],
            'logGroupClass': 'STANDARD',
            'logGroupArn': 'arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/test-function'
        }

        model = LogGroupMetadata(**data)

        assert model.logGroupName == '/aws/lambda/test-function'
        assert model.creationTime == '2023-04-29T20:00:00+00:00'
        assert model.retentionInDays == 14
        assert model.metricFilterCount == 2
        assert model.storedBytes == 1024000
        assert model.logGroupClass == 'STANDARD'

    def test_minimal_log_group_creation(self):
        """最小限のロググループメタデータ作成テスト."""
        data = {
            'logGroupName': '/aws/lambda/minimal',
            'creationTime': '2023-04-29T20:00:00+00:00',
            'metricFilterCount': 0,
            'storedBytes': 0,
            'logGroupArn': 'arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/minimal'
        }

        model = LogGroupMetadata(**data)

        assert model.logGroupName == '/aws/lambda/minimal'
        assert model.retentionInDays is None
        assert model.kmsKeyId is None
        assert model.logGroupClass == 'STANDARD'  # デフォルト値
        assert model.inheritedProperties == []  # デフォルト値

    def test_epoch_timestamp_conversion(self):
        """エポックタイムスタンプの変換テスト."""
        data = {
            'logGroupName': '/aws/lambda/epoch-test',
            'creationTime': 1682798400000,  # 2023-04-29T20:00:00Z
            'metricFilterCount': 0,
            'storedBytes': 0,
            'logGroupArn': 'arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/epoch-test'
        }

        model = LogGroupMetadata(**data)

        # エポックタイムスタンプがISO 8601形式に変換されることを確認
        assert '2023-04-29T20:00:00' in model.creationTime
        assert '+00:00' in model.creationTime

    def test_json_serialization(self):
        """JSON シリアライゼーションテスト."""
        data = {
            'logGroupName': '/aws/lambda/json-test',
            'creationTime': '2023-04-29T20:00:00+00:00',
            'metricFilterCount': 1,
            'storedBytes': 512000,
            'logGroupArn': 'arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/json-test'
        }

        model = LogGroupMetadata(**data)

        # model_dump()でJSONシリアライズ可能な辞書を取得
        model_dict = model.model_dump()
        json_str = json.dumps(model_dict)

        # JSON文字列から辞書に戻す
        parsed_dict = json.loads(json_str)

        assert parsed_dict['logGroupName'] == '/aws/lambda/json-test'
        assert parsed_dict['creationTime'] == '2023-04-29T20:00:00+00:00'

    def test_invalid_log_group_name(self):
        """無効なロググループ名のバリデーションテスト."""
        data = {
            'creationTime': '2023-04-29T20:00:00+00:00',
            'metricFilterCount': 0,
            'storedBytes': 0,
            'logGroupArn': 'arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/test'
        }

        with pytest.raises(ValidationError) as exc_info:
            LogGroupMetadata(**data)

        # logGroupNameが必須フィールドであることを確認
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('logGroupName',) for error in errors)


@pytest.mark.unit
@pytest.mark.aws_agents
class TestSavedLogsInsightsQuery:
    """SavedLogsInsightsQueryモデルのテストクラス."""

    def test_basic_saved_query_creation(self):
        """基本的な保存クエリの作成テスト."""
        data = {
            'name': 'Error Analysis Query',
            'queryString': 'fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc',
            'logGroupNames': ['/aws/lambda/test-function']
        }

        model = SavedLogsInsightsQuery(**data)

        assert model.name == 'Error Analysis Query'
        assert 'ERROR' in model.queryString
        assert '/aws/lambda/test-function' in model.logGroupNames

    def test_prefix_extraction_from_query(self):
        """クエリ文字列からのプレフィックス抽出テスト."""
        data = {
            'name': 'Prefix Test Query',
            'queryString': 'SOURCE logGroups(namePrefix:["/aws/lambda/", "/aws/ecs/"]) fields @timestamp, @message',
        }

        model = SavedLogsInsightsQuery(**data)

        assert '/aws/lambda/' in model.logGroupPrefixes
        assert '/aws/ecs/' in model.logGroupPrefixes

    def test_empty_sets_default(self):
        """空のセットのデフォルト値テスト."""
        data = {
            'name': 'Empty Test Query',
            'queryString': 'fields @timestamp, @message'
        }

        model = SavedLogsInsightsQuery(**data)

        assert isinstance(model.logGroupNames, set)
        assert isinstance(model.logGroupPrefixes, set)
        assert len(model.logGroupNames) == 0
        assert len(model.logGroupPrefixes) == 0

    def test_json_serialization_with_sets(self):
        """セットを含むJSONシリアライゼーションテスト."""
        data = {
            'name': 'Set Test Query',
            'queryString': 'fields @timestamp, @message',
            'logGroupNames': ['/aws/lambda/func1', '/aws/lambda/func2']
        }

        model = SavedLogsInsightsQuery(**data)
        model_dict = model.model_dump()

        # セットがリストに変換されることを確認
        assert isinstance(model_dict['logGroupNames'], list)
        assert '/aws/lambda/func1' in model_dict['logGroupNames']
        assert '/aws/lambda/func2' in model_dict['logGroupNames']


@pytest.mark.unit
@pytest.mark.aws_agents
class TestLogAnomaly:
    """LogAnomalyモデルのテストクラス."""

    def test_basic_anomaly_creation(self):
        """基本的な異常データの作成テスト."""
        data = {
            'anomalyDetectorArn': 'arn:aws:logs:us-east-1:123456789012:anomaly-detector/test',
            'logGroupArnList': ['arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/test'],
            'firstSeen': '2023-04-29T20:00:00+00:00',
            'lastSeen': '2023-04-29T20:30:00+00:00',
            'description': 'Unusual error pattern detected',
            'priority': 'HIGH',
            'patternRegex': 'ERROR.*timeout',
            'patternString': 'ERROR connection timeout',
            'logSamples': [
                {
                    'timestamp': 1682798400000,
                    'message': 'ERROR connection timeout'
                }
            ],
            'histogram': {
                '1682798400000': 5,
                '1682798430000': 3
            }
        }

        model = LogAnomaly(**data)

        assert model.description == 'Unusual error pattern detected'
        assert model.priority == 'HIGH'
        assert len(model.logSamples) == 1
        assert len(model.histogram) == 2

    def test_epoch_timestamp_conversion_in_anomaly(self):
        """異常データ内のエポックタイムスタンプ変換テスト."""
        data = {
            'anomalyDetectorArn': 'arn:aws:logs:us-east-1:123456789012:anomaly-detector/test',
            'logGroupArnList': ['arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/test'],
            'firstSeen': 1682798400000,  # エポックタイムスタンプ
            'lastSeen': 1682798460000,   # エポックタイムスタンプ
            'description': 'Test anomaly',
            'priority': 'MEDIUM',
            'patternRegex': 'ERROR.*',
            'patternString': 'ERROR pattern',
            'logSamples': [
                {
                    'timestamp': 1682798430000,  # これも変換される
                    'message': 'Sample message'
                }
            ],
            'histogram': {
                '1682798400000': 5,  # キーも変換される
                '1682798430000': 3
            }
        }

        model = LogAnomaly(**data)

        # firstSeen, lastSeenがISO形式に変換されることを確認
        assert '2023-04-29T20:00:00' in model.firstSeen
        assert '2023-04-29T20:01:00' in model.lastSeen

        # logSamplesのタイムスタンプも変換される
        assert len(model.logSamples) == 1  # 1つに制限
        sample = model.logSamples[0]
        assert '2023-04-29T20:00:30' in sample['timestamp']

        # histogramのキーも変換される
        histogram_keys = list(model.histogram.keys())
        assert any('2023-04-29T20:00:00' in key for key in histogram_keys)

    def test_log_samples_limitation(self):
        """ログサンプルの数制限テスト."""
        data = {
            'anomalyDetectorArn': 'arn:aws:logs:us-east-1:123456789012:anomaly-detector/test',
            'logGroupArnList': ['arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/test'],
            'firstSeen': '2023-04-29T20:00:00+00:00',
            'lastSeen': '2023-04-29T20:30:00+00:00',
            'description': 'Test anomaly',
            'priority': 'LOW',
            'patternRegex': 'INFO.*',
            'patternString': 'INFO pattern',
            'logSamples': [
                {'timestamp': 1682798400000, 'message': 'Sample 1'},
                {'timestamp': 1682798410000, 'message': 'Sample 2'},
                {'timestamp': 1682798420000, 'message': 'Sample 3'}
            ],
            'histogram': {}
        }

        model = LogAnomaly(**data)

        # logSamplesが1つに制限されることを確認
        assert len(model.logSamples) == 1
        assert model.logSamples[0]['message'] == 'Sample 1'


@pytest.mark.unit
@pytest.mark.aws_agents
class TestComplexModels:
    """複合モデルのテストクラス."""

    def test_logs_metadata_composition(self):
        """LogsMetadataの構成テスト."""
        log_group_data = {
            'logGroupName': '/aws/lambda/test',
            'creationTime': '2023-04-29T20:00:00+00:00',
            'metricFilterCount': 1,
            'storedBytes': 1024,
            'logGroupArn': 'arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/test'
        }

        query_data = {
            'name': 'Test Query',
            'queryString': 'fields @timestamp, @message'
        }

        log_group = LogGroupMetadata(**log_group_data)
        query = SavedLogsInsightsQuery(**query_data)

        metadata = LogsMetadata(
            log_group_metadata=[log_group],
            saved_queries=[query]
        )

        assert len(metadata.log_group_metadata) == 1
        assert len(metadata.saved_queries) == 1
        assert metadata.log_group_metadata[0].logGroupName == '/aws/lambda/test'

    def test_logs_analysis_result_composition(self):
        """LogsAnalysisResultの構成テスト."""
        anomaly_results = LogAnomalyResults(
            anomaly_detectors=[],
            anomalies=[]
        )

        analysis_result = LogsAnalysisResult(
            log_anomaly_results=anomaly_results,
            top_patterns={'queryId': 'pattern-123', 'results': []},
            top_patterns_containing_errors={'queryId': 'error-123', 'results': []}
        )

        assert hasattr(analysis_result, 'log_anomaly_results')
        assert hasattr(analysis_result, 'top_patterns')
        assert hasattr(analysis_result, 'top_patterns_containing_errors')
        assert analysis_result.top_patterns['queryId'] == 'pattern-123'

    def test_logs_query_cancel_result(self):
        """LogsQueryCancelResultのテスト."""
        cancel_result = LogsQueryCancelResult(success=True)
        assert cancel_result.success is True

        cancel_result_failed = LogsQueryCancelResult(success=False)
        assert cancel_result_failed.success is False

    def test_full_workflow_json_serialization(self):
        """フルワークフローのJSONシリアライゼーションテスト."""
        # 完全なワークフローで使用されるデータの作成
        log_group = LogGroupMetadata(
            logGroupName='/aws/lambda/workflow-test',
            creationTime='2023-04-29T20:00:00+00:00',
            metricFilterCount=2,
            storedBytes=2048000,
            logGroupArn='arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/workflow-test'
        )

        saved_query = SavedLogsInsightsQuery(
            name='Workflow Query',
            queryString='fields @timestamp, @message | filter @message like /workflow/'
        )

        anomaly_detector = LogAnomalyDetector(
            anomalyDetectorArn='arn:aws:logs:us-east-1:123456789012:anomaly-detector/workflow',
            detectorName='workflow-detector',
            anomalyDetectorStatus='ACTIVE'
        )

        anomaly = LogAnomaly(
            anomalyDetectorArn='arn:aws:logs:us-east-1:123456789012:anomaly-detector/workflow',
            logGroupArnList=['arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/workflow-test'],
            firstSeen='2023-04-29T20:15:00+00:00',
            lastSeen='2023-04-29T20:45:00+00:00',
            description='Workflow anomaly detected',
            priority='MEDIUM',
            patternRegex='workflow.*error',
            patternString='workflow error',
            logSamples=[],
            histogram={}
        )

        # 複合オブジェクトの作成
        metadata = LogsMetadata(
            log_group_metadata=[log_group],
            saved_queries=[saved_query]
        )

        anomaly_results = LogAnomalyResults(
            anomaly_detectors=[anomaly_detector],
            anomalies=[anomaly]
        )

        analysis_result = LogsAnalysisResult(
            log_anomaly_results=anomaly_results,
            top_patterns={'queryId': 'workflow-patterns', 'results': []},
            top_patterns_containing_errors={'queryId': 'workflow-errors', 'results': []}
        )

        # 各オブジェクトがJSONシリアライズ可能であることを確認
        metadata_json = json.dumps(metadata.model_dump(), default=str)
        analysis_json = json.dumps(analysis_result.model_dump(), default=str)

        assert isinstance(metadata_json, str)
        assert isinstance(analysis_json, str)
        assert 'workflow-test' in metadata_json
        assert 'workflow-patterns' in analysis_json


@pytest.mark.unit
@pytest.mark.aws_agents
class TestModelValidation:
    """モデルバリデーションのテストクラス."""

    def test_required_field_validation(self):
        """必須フィールドのバリデーションテスト."""
        # logGroupNameが必須
        with pytest.raises(ValidationError):
            LogGroupMetadata(
                creationTime='2023-04-29T20:00:00+00:00',
                metricFilterCount=0,
                storedBytes=0
                # logGroupArn も必須だが省略
            )

    def test_type_validation(self):
        """型バリデーションのテスト."""
        # storedBytesは整数でなければならない
        with pytest.raises(ValidationError):
            LogGroupMetadata(
                logGroupName='/aws/lambda/test',
                creationTime='2023-04-29T20:00:00+00:00',
                metricFilterCount=0,
                storedBytes='not-an-integer',  # 無効な型
                logGroupArn='arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/test'
            )

    def test_optional_field_defaults(self):
        """オプションフィールドのデフォルト値テスト."""
        log_group = LogGroupMetadata(
            logGroupName='/aws/lambda/defaults-test',
            creationTime='2023-04-29T20:00:00+00:00',
            metricFilterCount=0,
            storedBytes=0,
            logGroupArn='arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/defaults-test'
        )

        # デフォルト値の確認
        assert log_group.retentionInDays is None
        assert log_group.kmsKeyId is None
        assert log_group.dataProtectionStatus is None
        assert log_group.inheritedProperties == []
        assert log_group.logGroupClass == 'STANDARD'
