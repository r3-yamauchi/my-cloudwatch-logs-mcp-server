"""クエリ構文ツールの統合テスト."""

import pytest
from cloudwatch_logs.domain.models import QuerySyntaxDocumentation
from cloudwatch_logs.services.documentation_service import DocumentationService
from interfaces.mcp_tools import CloudWatchLogsMCPTools
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.integration
class TestQuerySyntaxToolsIntegration:
    """クエリ構文ツールの統合テストクラス."""

    @pytest.fixture
    def mcp_tools(self):
        """MCPツールのフィクスチャ."""
        return CloudWatchLogsMCPTools(version='integration-test-1.0.0')

    @pytest.fixture
    def mock_context(self):
        """モックコンテキストのフィクスチャ."""
        ctx = MagicMock()
        ctx.error = AsyncMock()
        ctx.warning = AsyncMock()
        return ctx

    @pytest.mark.asyncio
    async def test_get_query_syntax_documentation_overview(self, mcp_tools, mock_context):
        """概要ドキュメント取得の統合テスト."""
        result = await mcp_tools.get_query_syntax_documentation(mock_context)

        assert isinstance(result, QuerySyntaxDocumentation)
        assert result.query_type == 'overview'
        assert 'commands' in result.content
        assert 'functions' in result.content
        assert len(result.matched_elements) > 0
        assert result.total_elements > 0
        assert result.search_metadata['service_version'] == 'integration-test-1.0.0'

    @pytest.mark.asyncio
    async def test_get_query_syntax_documentation_command(self, mcp_tools, mock_context):
        """コマンドドキュメント取得の統合テスト."""
        result = await mcp_tools.get_query_syntax_documentation(
            mock_context,
            query_type='command',
            command_name='filter'
        )

        assert isinstance(result, QuerySyntaxDocumentation)
        assert result.query_type == 'command'
        assert 'filter' in result.content
        assert len(result.matched_elements) == 1
        assert result.matched_elements[0].name == 'filter'

    @pytest.mark.asyncio
    async def test_get_query_syntax_documentation_function(self, mcp_tools, mock_context):
        """関数ドキュメント取得の統合テスト."""
        result = await mcp_tools.get_query_syntax_documentation(
            mock_context,
            query_type='function',
            function_category='string'
        )

        assert isinstance(result, QuerySyntaxDocumentation)
        assert result.query_type == 'function'
        assert 'string' in result.content
        assert len(result.matched_elements) == 1
        assert result.matched_elements[0].name == 'string'

    @pytest.mark.asyncio
    async def test_get_query_syntax_documentation_search(self, mcp_tools, mock_context):
        """検索ドキュメント取得の統合テスト."""
        result = await mcp_tools.get_query_syntax_documentation(
            mock_context,
            query_type='search',
            search_term='filter',
            search_limit=5
        )

        assert isinstance(result, QuerySyntaxDocumentation)
        assert result.query_type == 'search'
        assert 'search_results' in result.content
        assert len(result.matched_elements) <= 5
        assert result.search_metadata['search_term'] == 'filter'

    @pytest.mark.asyncio
    async def test_get_query_syntax_documentation_examples(self, mcp_tools, mock_context):
        """例ドキュメント取得の統合テスト."""
        result = await mcp_tools.get_query_syntax_documentation(
            mock_context,
            query_type='examples',
            example_category='common_patterns'
        )

        assert isinstance(result, QuerySyntaxDocumentation)
        assert result.query_type == 'examples'
        assert 'common_patterns' in result.content
        assert result.total_elements > 0

    @pytest.mark.asyncio
    async def test_get_query_syntax_documentation_best_practices(self, mcp_tools, mock_context):
        """ベストプラクティス取得の統合テスト."""
        result = await mcp_tools.get_query_syntax_documentation(
            mock_context,
            query_type='best_practices'
        )

        assert isinstance(result, QuerySyntaxDocumentation)
        assert result.query_type == 'best_practices'
        assert 'best_practices' in result.content
        assert result.total_elements > 0

    @pytest.mark.asyncio
    async def test_get_query_syntax_documentation_troubleshooting(self, mcp_tools, mock_context):
        """トラブルシューティング取得の統合テスト."""
        result = await mcp_tools.get_query_syntax_documentation(
            mock_context,
            query_type='troubleshooting'
        )

        assert isinstance(result, QuerySyntaxDocumentation)
        assert result.query_type == 'troubleshooting'
        assert 'troubleshooting' in result.content

    @pytest.mark.asyncio
    async def test_get_query_syntax_documentation_command_missing_name(self, mcp_tools, mock_context):
        """コマンド名が指定されていない場合のエラーテスト."""
        with pytest.raises(Exception):
            await mcp_tools.get_query_syntax_documentation(
                mock_context,
                query_type='command'
            )

        mock_context.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_query_syntax_documentation_function_missing_category(self, mcp_tools, mock_context):
        """関数カテゴリが指定されていない場合のエラーテスト."""
        with pytest.raises(Exception):
            await mcp_tools.get_query_syntax_documentation(
                mock_context,
                query_type='function'
            )

        mock_context.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_query_syntax_documentation_search_missing_term(self, mcp_tools, mock_context):
        """検索語が指定されていない場合のエラーテスト."""
        with pytest.raises(Exception):
            await mcp_tools.get_query_syntax_documentation(
                mock_context,
                query_type='search'
            )

        mock_context.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_query_syntax_documentation_invalid_query_type(self, mcp_tools, mock_context):
        """無効なクエリタイプのエラーテスト."""
        with pytest.raises(Exception):
            await mcp_tools.get_query_syntax_documentation(
                mock_context,
                query_type='invalid_type'
            )

        mock_context.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_query_syntax_documentation_invalid_command(self, mcp_tools, mock_context):
        """無効なコマンドのエラーテスト."""
        with pytest.raises(Exception):
            await mcp_tools.get_query_syntax_documentation(
                mock_context,
                query_type='command',
                command_name='invalid_command'
            )

        mock_context.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_query_syntax_documentation_invalid_function_category(self, mcp_tools, mock_context):
        """無効な関数カテゴリのエラーテスト."""
        with pytest.raises(Exception):
            await mcp_tools.get_query_syntax_documentation(
                mock_context,
                query_type='function',
                function_category='invalid_category'
            )

        mock_context.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_all_available_commands_are_documented(self, mcp_tools, mock_context):
        """全ての利用可能なコマンドがドキュメント化されているかテスト."""
        # 利用可能なコマンド一覧を取得
        commands = mcp_tools.documentation_service.get_available_commands()

        # 各コマンドのドキュメントが取得できることを確認
        for command in commands:
            result = await mcp_tools.get_query_syntax_documentation(
                mock_context,
                query_type='command',
                command_name=command
            )
            assert isinstance(result, QuerySyntaxDocumentation)
            assert result.query_type == 'command'

    @pytest.mark.asyncio
    async def test_all_available_function_categories_are_documented(self, mcp_tools, mock_context):
        """全ての利用可能な関数カテゴリがドキュメント化されているかテスト."""
        # 利用可能な関数カテゴリ一覧を取得
        categories = mcp_tools.documentation_service.get_available_function_categories()

        # 各関数カテゴリのドキュメントが取得できることを確認
        for category in categories:
            result = await mcp_tools.get_query_syntax_documentation(
                mock_context,
                query_type='function',
                function_category=category
            )
            assert isinstance(result, QuerySyntaxDocumentation)
            assert result.query_type == 'function'

    @pytest.mark.asyncio
    async def test_documentation_service_integration(self, mcp_tools):
        """DocumentationServiceとの統合テスト."""
        # DocumentationServiceが正しく初期化されていることを確認
        assert isinstance(mcp_tools.documentation_service, DocumentationService)
        assert mcp_tools.documentation_service.version == 'integration-test-1.0.0'

        # 基本的な操作が動作することを確認
        full_doc = mcp_tools.documentation_service.get_full_documentation()
        assert isinstance(full_doc, QuerySyntaxDocumentation)

        commands = mcp_tools.documentation_service.get_available_commands()
        assert isinstance(commands, list)
        assert len(commands) > 0

        categories = mcp_tools.documentation_service.get_available_function_categories()
        assert isinstance(categories, list)
        assert len(categories) > 0
