"""データユーティリティ関数のユニットテスト.

このテストモジュールは、データ処理に関するユーティリティ関数をテストします。
AWS Strands Agentsでの使用を考慮し、効率的なデータ処理と
適切なデータクリーンアップ機能を検証します。
"""

import pytest
import json
from cloudwatch_logs.utils.data_utils import (
    remove_null_values,
    filter_by_prefixes,
    clean_up_pattern
)


@pytest.mark.unit
@pytest.mark.aws_agents
class TestRemoveNullValues:
    """remove_null_values関数のテストクラス."""

    def test_basic_null_removal(self):
        """基本的なnull値除去テスト."""
        input_dict = {
            'name': 'test',
            'value': None,
            'count': 5,
            'description': None,
            'active': True
        }
        
        result = remove_null_values(input_dict)
        
        expected = {
            'name': 'test',
            'count': 5,
            'active': True
        }
        assert result == expected

    def test_empty_dict(self):
        """空の辞書のテスト."""
        result = remove_null_values({})
        assert result == {}

    def test_no_null_values(self):
        """null値がない辞書のテスト."""
        input_dict = {
            'name': 'test',
            'count': 5,
            'active': True,
            'tags': ['tag1', 'tag2']
        }
        
        result = remove_null_values(input_dict)
        assert result == input_dict

    def test_all_null_values(self):
        """すべてnull値の辞書のテスト."""
        input_dict = {
            'name': None,
            'count': None,
            'active': None
        }
        
        result = remove_null_values(input_dict)
        assert result == {}

    def test_false_and_zero_values_preserved(self):
        """False値と0値が保持されることのテスト."""
        input_dict = {
            'name': 'test',
            'count': 0,
            'active': False,
            'description': None,
            'empty_string': '',
            'empty_list': []
        }
        
        result = remove_null_values(input_dict)
        
        expected = {
            'name': 'test',
            'count': 0,
            'active': False,
            'empty_string': '',
            'empty_list': []
        }
        assert result == expected

    def test_aws_api_parameter_cleaning(self):
        """AWS APIパラメータクリーニングのシミュレーション."""
        # 典型的なAWS APIパラメータ
        api_params = {
            'logGroupNamePrefix': '/aws/lambda/',
            'logGroupClass': 'STANDARD',
            'accountIdentifiers': None,  # オプションパラメータ
            'includeLinkedAccounts': False,
            'maxItems': None,  # 未指定
            'nextToken': None  # ページング用（未使用）
        }
        
        cleaned_params = remove_null_values(api_params)
        
        expected = {
            'logGroupNamePrefix': '/aws/lambda/',
            'logGroupClass': 'STANDARD',
            'includeLinkedAccounts': False
        }
        assert cleaned_params == expected

    def test_nested_structures_not_affected(self):
        """ネストした構造は影響を受けないことのテスト."""
        input_dict = {
            'name': 'test',
            'nested': {
                'inner_name': 'inner',
                'inner_value': None  # ネスト内のNoneは除去されない
            },
            'list_with_none': [1, None, 3],  # リスト内のNoneは除去されない
            'top_level_none': None  # これは除去される
        }
        
        result = remove_null_values(input_dict)
        
        expected = {
            'name': 'test',
            'nested': {
                'inner_name': 'inner',
                'inner_value': None
            },
            'list_with_none': [1, None, 3]
        }
        assert result == expected

    def test_original_dict_not_modified(self):
        """元の辞書が変更されないことのテスト."""
        original = {
            'name': 'test',
            'value': None,
            'count': 5
        }
        original_copy = original.copy()
        
        result = remove_null_values(original)
        
        # 元の辞書は変更されていない
        assert original == original_copy
        # 結果は異なる辞書
        assert result is not original


@pytest.mark.unit
@pytest.mark.aws_agents
class TestFilterByPrefixes:
    """filter_by_prefixes関数のテストクラス."""

    def test_basic_prefix_filtering(self):
        """基本的なプレフィックスフィルタリングテスト."""
        strings = {
            '/aws/lambda/function1',
            '/aws/lambda/function2',
            '/aws/ecs/service1',
            '/custom/app/log1'
        }
        prefixes = {'/aws/lambda/'}
        
        result = filter_by_prefixes(strings, prefixes)
        
        expected = {
            '/aws/lambda/function1',
            '/aws/lambda/function2'
        }
        assert result == expected

    def test_multiple_prefixes(self):
        """複数プレフィックスでのフィルタリングテスト."""
        strings = {
            '/aws/lambda/function1',
            '/aws/ecs/service1',
            '/aws/rds/database1',
            '/custom/app/log1'
        }
        prefixes = {'/aws/lambda/', '/aws/ecs/'}
        
        result = filter_by_prefixes(strings, prefixes)
        
        expected = {
            '/aws/lambda/function1',
            '/aws/ecs/service1'
        }
        assert result == expected

    def test_no_matches(self):
        """マッチしないケースのテスト."""
        strings = {
            '/aws/lambda/function1',
            '/aws/ecs/service1'
        }
        prefixes = {'/custom/', '/other/'}
        
        result = filter_by_prefixes(strings, prefixes)
        assert result == set()

    def test_empty_strings_set(self):
        """空の文字列セットのテスト."""
        strings = set()
        prefixes = {'/aws/lambda/'}
        
        result = filter_by_prefixes(strings, prefixes)
        assert result == set()

    def test_empty_prefixes_set(self):
        """空のプレフィックスセットのテスト."""
        strings = {
            '/aws/lambda/function1',
            '/aws/ecs/service1'
        }
        prefixes = set()
        
        result = filter_by_prefixes(strings, prefixes)
        assert result == set()

    def test_exact_match_prefix(self):
        """完全一致プレフィックスのテスト."""
        strings = {
            '/aws/lambda/function1',
            '/aws/lambda/',  # プレフィックスと完全一致
            '/aws/lambda/function2'
        }
        prefixes = {'/aws/lambda/'}
        
        result = filter_by_prefixes(strings, prefixes)
        
        # プレフィックスで始まるものすべてがマッチ
        expected = strings  # すべてマッチ
        assert result == expected

    def test_case_sensitive_filtering(self):
        """大文字小文字を区別するフィルタリングテスト."""
        strings = {
            '/AWS/Lambda/Function1',  # 大文字
            '/aws/lambda/function1',  # 小文字
            '/Aws/Lambda/Function1'   # 混在
        }
        prefixes = {'/aws/lambda/'}  # 小文字のプレフィックス
        
        result = filter_by_prefixes(strings, prefixes)
        
        expected = {'/aws/lambda/function1'}  # 小文字のみマッチ
        assert result == expected

    def test_aws_log_groups_filtering(self):
        """AWS ロググループフィルタリングのシミュレーション."""
        # 典型的なAWSロググループ名
        log_groups = {
            '/aws/lambda/user-service',
            '/aws/lambda/order-service',
            '/aws/lambda/payment-service',
            '/aws/ecs/web-frontend',
            '/aws/ecs/api-backend',
            '/aws/rds/aurora-cluster',
            '/custom/application/logs',
            '/nginx/access',
            '/application/debug'
        }
        
        # Lambda関数のみを取得
        lambda_prefix = {'/aws/lambda/'}
        lambda_groups = filter_by_prefixes(log_groups, lambda_prefix)
        
        expected_lambda = {
            '/aws/lambda/user-service',
            '/aws/lambda/order-service',
            '/aws/lambda/payment-service'
        }
        assert lambda_groups == expected_lambda
        
        # AWSサービス全般を取得
        aws_prefixes = {'/aws/'}
        aws_groups = filter_by_prefixes(log_groups, aws_prefixes)
        
        expected_aws = {
            '/aws/lambda/user-service',
            '/aws/lambda/order-service',
            '/aws/lambda/payment-service',
            '/aws/ecs/web-frontend',
            '/aws/ecs/api-backend',
            '/aws/rds/aurora-cluster'
        }
        assert aws_groups == expected_aws

    def test_overlapping_prefixes(self):
        """重複するプレフィックスのテスト."""
        strings = {
            '/aws/lambda/function1',
            '/aws/lambda/test/function1',
            '/aws/other/service1'
        }
        prefixes = {
            '/aws/',  # より一般的なプレフィックス
            '/aws/lambda/'  # より具体的なプレフィックス
        }
        
        result = filter_by_prefixes(strings, prefixes)
        
        # すべて/aws/で始まるのでマッチ
        assert result == strings

    def test_set_immutability(self):
        """元のセットが変更されないことのテスト."""
        original_strings = {
            '/aws/lambda/function1',
            '/aws/ecs/service1',
            '/custom/app/log1'
        }
        original_prefixes = {'/aws/lambda/'}
        
        strings_copy = original_strings.copy()
        prefixes_copy = original_prefixes.copy()
        
        result = filter_by_prefixes(original_strings, original_prefixes)
        
        # 元のセットは変更されていない
        assert original_strings == strings_copy
        assert original_prefixes == prefixes_copy


@pytest.mark.unit
@pytest.mark.aws_agents
class TestCleanUpPattern:
    """clean_up_pattern関数のテストクラス."""

    def test_basic_pattern_cleanup(self):
        """基本的なパターンクリーンアップテスト."""
        pattern_result = [
            {
                '@pattern': 'ERROR connection timeout',
                '@sampleCount': '10',
                '@tokens': ['error', 'connection', 'timeout'],
                '@visualization': 'bar_chart',
                '@logSamples': '[]'
            }
        ]
        
        clean_up_pattern(pattern_result)
        
        expected = [
            {
                '@pattern': 'ERROR connection timeout',
                '@sampleCount': '10',
                '@logSamples': []
            }
        ]
        assert pattern_result == expected

    def test_log_samples_limitation(self):
        """ログサンプル制限のテスト."""
        pattern_result = [
            {
                '@pattern': 'INFO application started',
                '@sampleCount': '5',
                '@logSamples': json.dumps([
                    {'timestamp': '2023-04-29T20:00:00Z', 'message': 'Sample 1'},
                    {'timestamp': '2023-04-29T20:01:00Z', 'message': 'Sample 2'},
                    {'timestamp': '2023-04-29T20:02:00Z', 'message': 'Sample 3'}
                ])
            }
        ]
        
        clean_up_pattern(pattern_result)
        
        # @logSamplesが1つに制限されることを確認
        assert len(pattern_result[0]['@logSamples']) == 1
        assert pattern_result[0]['@logSamples'][0]['message'] == 'Sample 1'

    def test_empty_log_samples(self):
        """空のログサンプルのテスト."""
        pattern_result = [
            {
                '@pattern': 'WARN deprecated method',
                '@sampleCount': '2',
                '@logSamples': '[]'
            }
        ]
        
        clean_up_pattern(pattern_result)
        
        # 空のリストは空のままであることを確認
        assert pattern_result[0]['@logSamples'] == []

    def test_missing_fields_handling(self):
        """欠落フィールドの処理テスト."""
        pattern_result = [
            {
                '@pattern': 'DEBUG trace info',
                '@sampleCount': '1'
                # @tokens, @visualization, @logSamples が存在しない
            }
        ]
        
        # エラーなく処理されることを確認
        clean_up_pattern(pattern_result)
        
        expected = [
            {
                '@pattern': 'DEBUG trace info',
                '@sampleCount': '1'
            }
        ]
        assert pattern_result == expected

    def test_multiple_entries_cleanup(self):
        """複数エントリのクリーンアップテスト."""
        pattern_result = [
            {
                '@pattern': 'ERROR database connection',
                '@sampleCount': '15',
                '@tokens': ['error', 'database'],
                '@visualization': 'pie_chart',
                '@logSamples': json.dumps([
                    {'timestamp': '2023-04-29T20:00:00Z', 'message': 'DB Error 1'},
                    {'timestamp': '2023-04-29T20:01:00Z', 'message': 'DB Error 2'}
                ])
            },
            {
                '@pattern': 'INFO successful request',
                '@sampleCount': '100',
                '@tokens': ['info', 'successful'],
                '@visualization': 'line_chart',
                '@logSamples': json.dumps([
                    {'timestamp': '2023-04-29T20:00:00Z', 'message': 'Success 1'}
                ])
            }
        ]
        
        clean_up_pattern(pattern_result)
        
        # すべてのエントリがクリーンアップされることを確認
        for entry in pattern_result:
            assert '@tokens' not in entry
            assert '@visualization' not in entry
            assert isinstance(entry['@logSamples'], list)
            assert len(entry['@logSamples']) <= 1

    def test_in_place_modification(self):
        """in-place変更のテスト."""
        original_pattern = [
            {
                '@pattern': 'TEST pattern',
                '@sampleCount': '5',
                '@tokens': ['test'],
                '@logSamples': '[]'
            }
        ]
        
        # 元のリストのIDを保存
        original_id = id(original_pattern)
        original_entry_id = id(original_pattern[0])
        
        clean_up_pattern(original_pattern)
        
        # 同じオブジェクトが変更されていることを確認
        assert id(original_pattern) == original_id
        assert id(original_pattern[0]) == original_entry_id

    def test_aws_agents_token_optimization(self):
        """AWS Strands Agents用トークン最適化のテスト."""
        # CloudWatch Logs Insightsから返される典型的なパターン結果
        pattern_result = [
            {
                '@pattern': 'ERROR Failed to process request',
                '@sampleCount': '25',
                '@tokens': [
                    'error', 'failed', 'process', 'request', 'timeout', 
                    'connection', 'database', 'retry', 'attempt'
                ],  # 多くのトークン（使用量を消費）
                '@visualization': {
                    'type': 'bar_chart',
                    'data': [1, 2, 3, 4, 5],
                    'metadata': {'color': 'red', 'title': 'Error Pattern'}
                },  # 複雑な可視化データ（使用量を消費）
                '@logSamples': json.dumps([
                    {
                        'timestamp': '2023-04-29T20:00:00Z',
                        'message': 'ERROR Failed to process request: timeout after 30s',
                        'requestId': 'req-123',
                        'userId': 'user-456',
                        'metadata': {'retry_count': 3, 'endpoint': '/api/process'}
                    },
                    {
                        'timestamp': '2023-04-29T20:01:00Z',
                        'message': 'ERROR Failed to process request: database connection lost',
                        'requestId': 'req-124',
                        'userId': 'user-789',
                        'metadata': {'retry_count': 1, 'endpoint': '/api/process'}
                    },
                    {
                        'timestamp': '2023-04-29T20:02:00Z',
                        'message': 'ERROR Failed to process request: invalid input data',
                        'requestId': 'req-125',
                        'userId': 'user-101',
                        'metadata': {'retry_count': 0, 'endpoint': '/api/process'}
                    }
                ])  # 複数のログサンプル（使用量を消費）
            },
            {
                '@pattern': 'INFO Request completed successfully',
                '@sampleCount': '1000',
                '@tokens': ['info', 'request', 'completed', 'successfully'],
                '@visualization': {
                    'type': 'line_chart',
                    'data': [10, 20, 30, 40, 50]
                },
                '@logSamples': json.dumps([
                    {
                        'timestamp': '2023-04-29T20:00:00Z',
                        'message': 'INFO Request completed successfully in 150ms'
                    }
                ])
            }
        ]
        
        clean_up_pattern(pattern_result)
        
        # トークン使用量が削減されていることを確認
        for entry in pattern_result:
            # 不要なフィールドが削除されている
            assert '@tokens' not in entry
            assert '@visualization' not in entry
            
            # 重要な情報は保持されている
            assert '@pattern' in entry
            assert '@sampleCount' in entry
            assert '@logSamples' in entry
            
            # ログサンプルが1つに制限されている
            assert len(entry['@logSamples']) <= 1
            
            # ログサンプルがリスト形式に変換されている
            assert isinstance(entry['@logSamples'], list)

    def test_invalid_json_in_log_samples(self):
        """ログサンプル内の無効なJSONの処理テスト."""
        pattern_result = [
            {
                '@pattern': 'ERROR parsing failed',
                '@sampleCount': '3',
                '@logSamples': 'invalid json string'  # 無効なJSON
            }
        ]
        
        # JSONパースエラーが発生することを確認
        with pytest.raises(json.JSONDecodeError):
            clean_up_pattern(pattern_result)

    def test_empty_pattern_result(self):
        """空のパターン結果のテスト."""
        pattern_result = []
        
        # エラーなく処理されることを確認
        clean_up_pattern(pattern_result)
        assert pattern_result == []