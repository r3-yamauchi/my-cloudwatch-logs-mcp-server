"""CloudWatch Logs Insights クエリ構文ドキュメンテーションサービス.

このサービスは、CloudWatch Logs Insightsクエリ構文の包括的なドキュメントを提供します。
MCPサーバーとAWS Strands Agents SDK両方での使用に対応したサービス層として実装されています。
"""

from cloudwatch_logs.documentation.query_syntax import (
    CLOUDWATCH_LOGS_INSIGHTS_QUERY_SYNTAX,
    get_available_commands,
    get_available_function_categories,
    get_command_documentation,
    get_function_documentation,
    get_query_syntax_documentation,
    search_documentation,
)
from cloudwatch_logs.domain.models import QuerySyntaxDocumentation, QuerySyntaxElement
from loguru import logger
from typing import Any, Dict, List, Optional


class DocumentationService:
    """CloudWatch Logs Insightsクエリ構文ドキュメンテーションサービス.

    このサービスは、CloudWatch Logs Insightsクエリ構文の包括的なドキュメントを提供し、
    MCPサーバーとAWS Strands Agents SDK両方での使用に対応しています。
    """

    def __init__(self, version: str = '1.0.0'):
        """DocumentationServiceを初期化する.

        Args:
            version: サービスのバージョン情報
        """
        self.version = version
        logger.info(f'DocumentationService initialized with version: {version}')

    def get_full_documentation(self) -> QuerySyntaxDocumentation:
        """CloudWatch Logs Insightsクエリ構文の完全なドキュメントを取得する.

        Returns:
            QuerySyntaxDocumentation: 完全なクエリ構文ドキュメント
        """
        try:
            full_doc = get_query_syntax_documentation()

            # 全コマンドと関数を構文要素として変換
            elements = []

            # コマンド要素の追加
            for cmd_name, cmd_doc in full_doc.get('commands', {}).items():
                elements.append(QuerySyntaxElement(
                    name=cmd_name,
                    element_type='command',
                    description=cmd_doc.get('description', ''),
                    syntax=cmd_doc.get('syntax', ''),
                    examples=cmd_doc.get('examples', []),
                    limitations=cmd_doc.get('limitations', []),
                    related_elements=[]
                ))

            # 関数要素の追加
            for func_category, func_doc in full_doc.get('functions', {}).items():
                elements.append(QuerySyntaxElement(
                    name=func_category,
                    element_type='function_category',
                    description=func_doc.get('description', ''),
                    syntax='',
                    examples=func_doc.get('examples', []),
                    limitations=[],
                    related_elements=[]
                ))

            return QuerySyntaxDocumentation(
                query_type='overview',
                content=full_doc,
                matched_elements=elements,
                total_elements=len(elements),
                search_metadata={
                    'service_version': self.version,
                    'total_commands': len(full_doc.get('commands', {})),
                    'total_function_categories': len(full_doc.get('functions', {})),
                    'documentation_type': 'complete'
                }
            )

        except Exception as e:
            logger.error(f'Error getting full documentation: {str(e)}')
            raise

    def get_command_documentation(self, command: str) -> QuerySyntaxDocumentation:
        """特定のコマンドのドキュメントを取得する.

        Args:
            command: コマンド名（例: 'filter', 'stats', 'parse'）

        Returns:
            QuerySyntaxDocumentation: 指定されたコマンドのドキュメント

        Raises:
            KeyError: 指定されたコマンドが存在しない場合
        """
        try:
            cmd_doc = get_command_documentation(command)

            element = QuerySyntaxElement(
                name=command,
                element_type='command',
                description=cmd_doc.get('description', ''),
                syntax=cmd_doc.get('syntax', ''),
                examples=cmd_doc.get('examples', []),
                limitations=cmd_doc.get('limitations', []),
                related_elements=[]
            )

            return QuerySyntaxDocumentation(
                query_type='command',
                content={command: cmd_doc},
                matched_elements=[element],
                total_elements=1,
                search_metadata={
                    'service_version': self.version,
                    'command_name': command,
                    'documentation_type': 'command_specific'
                }
            )

        except KeyError:
            logger.error(f'Command not found: {command}')
            raise
        except Exception as e:
            logger.error(f'Error getting command documentation for {command}: {str(e)}')
            raise

    def get_function_documentation(self, function_category: str) -> QuerySyntaxDocumentation:
        """特定の関数カテゴリのドキュメントを取得する.

        Args:
            function_category: 関数カテゴリ（例: 'string', 'datetime', 'numeric'）

        Returns:
            QuerySyntaxDocumentation: 指定された関数カテゴリのドキュメント

        Raises:
            KeyError: 指定された関数カテゴリが存在しない場合
        """
        try:
            func_doc = get_function_documentation(function_category)

            element = QuerySyntaxElement(
                name=function_category,
                element_type='function_category',
                description=func_doc.get('description', ''),
                syntax='',
                examples=func_doc.get('examples', []),
                limitations=[],
                related_elements=[]
            )

            return QuerySyntaxDocumentation(
                query_type='function',
                content={function_category: func_doc},
                matched_elements=[element],
                total_elements=1,
                search_metadata={
                    'service_version': self.version,
                    'function_category': function_category,
                    'documentation_type': 'function_specific'
                }
            )

        except KeyError:
            logger.error(f'Function category not found: {function_category}')
            raise
        except Exception as e:
            logger.error(f'Error getting function documentation for {function_category}: {str(e)}')
            raise

    def search_documentation(self, search_term: str, limit: Optional[int] = None) -> QuerySyntaxDocumentation:
        """ドキュメント内でキーワード検索を実行する.

        Args:
            search_term: 検索キーワード
            limit: 検索結果の最大件数（Noneの場合は全件）

        Returns:
            QuerySyntaxDocumentation: 検索結果
        """
        try:
            search_results = search_documentation(search_term)

            # 検索結果を構文要素に変換
            elements = []
            for result in search_results:
                element = QuerySyntaxElement(
                    name=result['name'],
                    element_type=result['type'],
                    description=result['documentation'].get('description', ''),
                    syntax=result['documentation'].get('syntax', ''),
                    examples=result['documentation'].get('examples', []),
                    limitations=result['documentation'].get('limitations', []),
                    related_elements=[]
                )
                elements.append(element)

            # 結果を制限
            if limit is not None:
                elements = elements[:limit]

            return QuerySyntaxDocumentation(
                query_type='search',
                content={'search_results': search_results[:limit] if limit else search_results},
                matched_elements=elements,
                total_elements=len(elements),
                search_metadata={
                    'service_version': self.version,
                    'search_term': search_term,
                    'documentation_type': 'search_results',
                    'total_matches': len(search_results),
                    'returned_matches': len(elements)
                }
            )

        except Exception as e:
            logger.error(f'Error searching documentation for term "{search_term}": {str(e)}')
            raise

    def get_available_commands(self) -> List[str]:
        """利用可能なコマンドのリストを取得する.

        Returns:
            List[str]: コマンド名のリスト
        """
        try:
            return get_available_commands()
        except Exception as e:
            logger.error(f'Error getting available commands: {str(e)}')
            raise

    def get_available_function_categories(self) -> List[str]:
        """利用可能な関数カテゴリのリストを取得する.

        Returns:
            List[str]: 関数カテゴリ名のリスト
        """
        try:
            return get_available_function_categories()
        except Exception as e:
            logger.error(f'Error getting available function categories: {str(e)}')
            raise

    def get_examples_by_category(self, category: str) -> List[Dict[str, Any]]:
        """カテゴリ別のクエリ例を取得する.

        Args:
            category: 例のカテゴリ（'common_patterns', 'advanced_queries'）

        Returns:
            List[Dict[str, Any]]: 指定されたカテゴリの例のリスト
        """
        try:
            examples = CLOUDWATCH_LOGS_INSIGHTS_QUERY_SYNTAX.get('examples', {})
            return examples.get(category, [])
        except Exception as e:
            logger.error(f'Error getting examples for category {category}: {str(e)}')
            raise

    def get_best_practices(self) -> List[str]:
        """クエリ使用時のベストプラクティスを取得する.

        Returns:
            List[str]: ベストプラクティスのリスト
        """
        try:
            overview = CLOUDWATCH_LOGS_INSIGHTS_QUERY_SYNTAX.get('overview', {})
            return overview.get('best_practices', [])
        except Exception as e:
            logger.error(f'Error getting best practices: {str(e)}')
            raise

    def get_troubleshooting_guide(self) -> Dict[str, Any]:
        """トラブルシューティングガイドを取得する.

        Returns:
            Dict[str, Any]: トラブルシューティング情報
        """
        try:
            return CLOUDWATCH_LOGS_INSIGHTS_QUERY_SYNTAX.get('troubleshooting', {})
        except Exception as e:
            logger.error(f'Error getting troubleshooting guide: {str(e)}')
            raise

    def validate_query_syntax(self, query: str) -> Dict[str, Any]:
        """クエリ構文の基本的な検証を実行する（簡易版）.

        Args:
            query: 検証するクエリ文字列

        Returns:
            Dict[str, Any]: 検証結果
        """
        try:
            validation_result = {
                'is_valid': True,
                'warnings': [],
                'errors': [],
                'suggestions': []
            }

            # 基本的な構文チェック
            if not query.strip():
                validation_result['is_valid'] = False
                validation_result['errors'].append('Query cannot be empty')
                return validation_result

            # パイプ文字の使用チェック
            if '|' in query:
                commands = [cmd.strip() for cmd in query.split('|')]
                available_commands = self.get_available_commands()

                for cmd in commands:
                    if cmd:
                        cmd_name = cmd.split()[0].lower()
                        if cmd_name not in available_commands:
                            validation_result['warnings'].append(
                                f'Command "{cmd_name}" may not be recognized'
                            )

            # limitコマンドの推奨
            if 'limit' not in query.lower():
                validation_result['suggestions'].append(
                    'Consider adding a limit command to avoid consuming too many tokens'
                )

            return validation_result

        except Exception as e:
            logger.error(f'Error validating query syntax: {str(e)}')
            return {
                'is_valid': False,
                'errors': [f'Validation error: {str(e)}'],
                'warnings': [],
                'suggestions': []
            }

    def get_summary_stats(self) -> Dict[str, Any]:
        """ドキュメントの統計情報を取得する.

        Returns:
            Dict[str, Any]: ドキュメントの統計情報
        """
        try:
            doc = CLOUDWATCH_LOGS_INSIGHTS_QUERY_SYNTAX

            return {
                'total_commands': len(doc.get('commands', {})),
                'total_function_categories': len(doc.get('functions', {})),
                'total_examples': sum(
                    len(examples) for examples in doc.get('examples', {}).values()
                ),
                'service_version': self.version,
                'documentation_sections': list(doc.keys())
            }

        except Exception as e:
            logger.error(f'Error getting summary stats: {str(e)}')
            raise
