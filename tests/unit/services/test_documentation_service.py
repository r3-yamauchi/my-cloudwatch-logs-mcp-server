"""DocumentationServiceのユニットテスト."""

import pytest
from cloudwatch_logs.domain.models import QuerySyntaxDocumentation
from cloudwatch_logs.services.documentation_service import DocumentationService
from unittest.mock import patch


class TestDocumentationService:
    """DocumentationServiceのテストクラス."""

    @pytest.fixture
    def documentation_service(self):
        """DocumentationServiceのフィクスチャ."""
        return DocumentationService(version='test-1.0.0')

    def test_init(self, documentation_service):
        """DocumentationServiceの初期化をテストする."""
        assert documentation_service.version == 'test-1.0.0'

    def test_get_full_documentation(self, documentation_service):
        """完全なドキュメント取得のテスト."""
        result = documentation_service.get_full_documentation()

        assert isinstance(result, QuerySyntaxDocumentation)
        assert result.query_type == 'overview'
        assert 'commands' in result.content
        assert 'functions' in result.content
        assert len(result.matched_elements) > 0
        assert result.total_elements > 0
        assert result.search_metadata['service_version'] == 'test-1.0.0'

    def test_get_command_documentation_valid(self, documentation_service):
        """有効なコマンドのドキュメント取得テスト."""
        result = documentation_service.get_command_documentation('filter')

        assert isinstance(result, QuerySyntaxDocumentation)
        assert result.query_type == 'command'
        assert 'filter' in result.content
        assert len(result.matched_elements) == 1
        assert result.matched_elements[0].name == 'filter'
        assert result.matched_elements[0].element_type == 'command'

    def test_get_command_documentation_invalid(self, documentation_service):
        """無効なコマンドのドキュメント取得テスト."""
        with pytest.raises(KeyError):
            documentation_service.get_command_documentation('invalid_command')

    def test_get_function_documentation_valid(self, documentation_service):
        """有効な関数カテゴリのドキュメント取得テスト."""
        result = documentation_service.get_function_documentation('string')

        assert isinstance(result, QuerySyntaxDocumentation)
        assert result.query_type == 'function'
        assert 'string' in result.content
        assert len(result.matched_elements) == 1
        assert result.matched_elements[0].name == 'string'
        assert result.matched_elements[0].element_type == 'function_category'

    def test_get_function_documentation_invalid(self, documentation_service):
        """無効な関数カテゴリのドキュメント取得テスト."""
        with pytest.raises(KeyError):
            documentation_service.get_function_documentation('invalid_function')

    def test_search_documentation(self, documentation_service):
        """ドキュメント検索のテスト."""
        result = documentation_service.search_documentation('filter')

        assert isinstance(result, QuerySyntaxDocumentation)
        assert result.query_type == 'search'
        assert 'search_results' in result.content
        assert len(result.matched_elements) > 0
        assert result.search_metadata['search_term'] == 'filter'

    def test_search_documentation_with_limit(self, documentation_service):
        """制限付きドキュメント検索のテスト."""
        result = documentation_service.search_documentation('filter', limit=2)

        assert isinstance(result, QuerySyntaxDocumentation)
        assert len(result.matched_elements) <= 2
        assert result.search_metadata['returned_matches'] <= 2

    def test_get_available_commands(self, documentation_service):
        """利用可能なコマンド取得のテスト."""
        commands = documentation_service.get_available_commands()

        assert isinstance(commands, list)
        assert len(commands) > 0
        assert 'filter' in commands
        assert 'stats' in commands
        assert 'fields' in commands

    def test_get_available_function_categories(self, documentation_service):
        """利用可能な関数カテゴリ取得のテスト."""
        categories = documentation_service.get_available_function_categories()

        assert isinstance(categories, list)
        assert len(categories) > 0
        assert 'string' in categories
        assert 'datetime' in categories
        assert 'numeric' in categories

    def test_get_examples_by_category(self, documentation_service):
        """カテゴリ別の例取得のテスト."""
        examples = documentation_service.get_examples_by_category('common_patterns')

        assert isinstance(examples, list)
        assert len(examples) > 0

        # 無効なカテゴリの場合は空リストを返す
        empty_examples = documentation_service.get_examples_by_category('invalid_category')
        assert isinstance(empty_examples, list)
        assert len(empty_examples) == 0

    def test_get_best_practices(self, documentation_service):
        """ベストプラクティス取得のテスト."""
        best_practices = documentation_service.get_best_practices()

        assert isinstance(best_practices, list)
        assert len(best_practices) > 0

    def test_get_troubleshooting_guide(self, documentation_service):
        """トラブルシューティングガイド取得のテスト."""
        troubleshooting = documentation_service.get_troubleshooting_guide()

        assert isinstance(troubleshooting, dict)
        assert 'common_issues' in troubleshooting

    def test_validate_query_syntax_valid(self, documentation_service):
        """有効なクエリ構文の検証テスト."""
        result = documentation_service.validate_query_syntax('fields @timestamp, @message | limit 10')

        assert isinstance(result, dict)
        assert result['is_valid'] is True
        assert isinstance(result['warnings'], list)
        assert isinstance(result['errors'], list)
        assert isinstance(result['suggestions'], list)

    def test_validate_query_syntax_empty(self, documentation_service):
        """空のクエリ構文の検証テスト."""
        result = documentation_service.validate_query_syntax('')

        assert isinstance(result, dict)
        assert result['is_valid'] is False
        assert 'Query cannot be empty' in result['errors']

    def test_validate_query_syntax_with_limit_suggestion(self, documentation_service):
        """limitコマンドがない場合の提案テスト."""
        result = documentation_service.validate_query_syntax('fields @timestamp, @message')

        assert isinstance(result, dict)
        assert result['is_valid'] is True
        assert any('limit' in suggestion for suggestion in result['suggestions'])

    def test_get_summary_stats(self, documentation_service):
        """統計情報取得のテスト."""
        stats = documentation_service.get_summary_stats()

        assert isinstance(stats, dict)
        assert 'total_commands' in stats
        assert 'total_function_categories' in stats
        assert 'total_examples' in stats
        assert 'service_version' in stats
        assert 'documentation_sections' in stats
        assert stats['service_version'] == 'test-1.0.0'
        assert stats['total_commands'] > 0
        assert stats['total_function_categories'] > 0

    @patch('cloudwatch_logs.services.documentation_service.logger')
    def test_error_handling(self, mock_logger, documentation_service):
        """エラーハンドリングのテスト."""
        # get_command_documentationでのエラー
        with pytest.raises(KeyError):
            documentation_service.get_command_documentation('nonexistent')

        # get_function_documentationでのエラー
        with pytest.raises(KeyError):
            documentation_service.get_function_documentation('nonexistent')

        # ログが正しく出力されることを確認
        mock_logger.error.assert_called()

    def test_search_empty_term(self, documentation_service):
        """空の検索語でのテスト."""
        result = documentation_service.search_documentation('')

        assert isinstance(result, QuerySyntaxDocumentation)
        assert result.query_type == 'search'
        # 空の検索語では全ての要素がマッチするため、0以上の結果が返される
        assert len(result.matched_elements) >= 0
