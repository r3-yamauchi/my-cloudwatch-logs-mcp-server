"""CloudWatch Logs APIとの連携を担当するサービス層モジュール.

このモジュールはCloudWatch Logs APIへの直接的な操作を抽象化し、
ビジネスロジックを提供します。AWS SDK (boto3) を使用してCloudWatch Logsの
各種操作を実行し、エラーハンドリングやデータ変換を行います。

主な機能:
- ロググループの検索と取得
- 保存されたクエリの管理
- CloudWatch Logs Insightsクエリの実行と管理
- 結果の取得とポーリング
- クエリのキャンセル
"""

import asyncio
import boto3
import os
from botocore.config import Config
from cloudwatch_logs.domain.exceptions import AWSClientError, QueryTimeoutError
from cloudwatch_logs.domain.models import LogGroupMetadata, SavedLogsInsightsQuery
from cloudwatch_logs.utils.data_utils import filter_by_prefixes, remove_null_values
from cloudwatch_logs.utils.time_utils import convert_time_to_timestamp
from loguru import logger
from timeit import default_timer as timer
from typing import Dict, List, Optional


class CloudWatchLogsService:
    """CloudWatch Logs APIとの連携を担当するサービスクラス.

    このクラスはAWS CloudWatch Logs APIとの直接的な通信を管理し、
    ロググループの検索、クエリの実行、結果の取得などの操作を提供します。

    設計原則:
    - 単一責任の原則: CloudWatch Logs APIとの連携に特化
    - 依存関係の注入: 設定可能なバージョン情報
    - エラーハンドリング: 適切な例外変換とログ出力
    - 効率性: クライアントのキャッシュとリージョン別管理

    Attributes:
        version: ユーザーエージェントに含めるバージョン情報
        _logs_client: キャッシュされたCloudWatch Logsクライアント
        _logs_client_region: 現在のクライアントのリージョン
    """

    def __init__(self, version: str = '1.0.0'):
        """CloudWatch Logsサービスを初期化する.

        Args:
            version: ユーザーエージェントに含めるバージョン情報
                    AWS APIコールの識別とデバッグに使用されます

        Note:
            初期化時点ではAWSクライアントは作成されません。
            初回使用時に遅延初期化されます。
        """
        self.version = version
        # AWSクライアントの遅延初期化とキャッシュ管理
        self._logs_client = None  # キャッシュされたCloudWatch Logsクライアント
        self._logs_client_region = None  # 現在のクライアントのリージョン

    def _get_logs_client(self, region: str):
        """指定されたリージョンのCloudWatch Logsクライアントを作成する.

        AWS認証情報を使用してCloudWatch Logsクライアントを作成します。
        環境変数AWS_PROFILEが設定されている場合は、指定されたプロファイルを使用します。

        Args:
            region: AWSリージョン（例: 'us-east-1', 'ap-northeast-1'）

        Returns:
            CloudWatch Logsクライアント (boto3.client)

        Raises:
            AWSClientError: クライアント作成に失敗した場合
                - 認証情報の不備
                - 不正なリージョン名
                - ネットワークエラー
        """
        # ユーザーエージェントにバージョン情報を追加（API使用状況の追跡のため）
        config = Config(user_agent_extra=f'cloudwatch-logs-mcp-server/{self.version}')

        try:
            # AWS_PROFILE環境変数が設定されている場合は、指定されたプロファイルを使用
            if aws_profile := os.environ.get('AWS_PROFILE'):
                logger.info(f'Using AWS profile: {aws_profile} for region: {region}')
                return boto3.Session(profile_name=aws_profile, region_name=region).client(
                    'logs', config=config
                )
            else:
                # デフォルトの認証情報を使用
                logger.info(f'Using default AWS credentials for region: {region}')
                return boto3.Session(region_name=region).client('logs', config=config)
        except Exception as e:
            logger.error(f'Error creating cloudwatch logs client for region {region}: {str(e)}')
            raise AWSClientError(f'Failed to create AWS client for region {region}: {str(e)}')

    def get_logs_client(self, region: str = 'us-east-1'):
        """指定されたリージョンのlogsクライアントを取得する（キャッシュ付き）.

        Args:
            region: AWSリージョン

        Returns:
            CloudWatch Logsクライアント
        """
        if self._logs_client is None or self._logs_client_region != region:
            self._logs_client = self._get_logs_client(region)
            self._logs_client_region = region
        return self._logs_client

    def describe_log_groups(
        self,
        region: str = 'us-east-1',
        account_identifiers: Optional[List[str]] = None,
        include_linked_accounts: bool = False,
        log_group_class: Optional[str] = None,
        log_group_name_prefix: Optional[str] = None,
        max_items: Optional[int] = None,
    ) -> List[LogGroupMetadata]:
        """CloudWatch ロググループの情報を取得する.

        Args:
            region: AWSリージョン
            account_identifiers: アカウント識別子のリスト
            include_linked_accounts: リンクされたアカウントを含めるか
            log_group_class: ロググループクラス
            log_group_name_prefix: ロググループ名のプレフィックス
            max_items: 取得する最大項目数

        Returns:
            ロググループメタデータのリスト

        Raises:
            AWSClientError: AWS API呼び出しに失敗した場合
        """
        try:
            logs_client = self.get_logs_client(region)
            paginator = logs_client.get_paginator('describe_log_groups')
            kwargs = {
                'accountIdentifiers': account_identifiers,
                'includeLinkedAccounts': include_linked_accounts,
                'logGroupNamePrefix': log_group_name_prefix,
                'logGroupClass': log_group_class,
            }

            if max_items:
                kwargs['PaginationConfig'] = {'MaxItems': max_items}

            log_groups = []
            for page in paginator.paginate(**remove_null_values(kwargs)):
                log_groups.extend(page.get('logGroups', []))

            logger.info(f'Retrieved {len(log_groups)} log groups')
            return [LogGroupMetadata.model_validate(lg) for lg in log_groups]

        except Exception as e:
            logger.error(f'Error in describe_log_groups: {str(e)}')
            raise AWSClientError(f'Failed to describe log groups: {str(e)}')

    def get_saved_queries(
        self,
        log_groups: List[LogGroupMetadata],
        region: str = 'us-east-1',
    ) -> List[SavedLogsInsightsQuery]:
        """指定されたロググループに関連する保存されたクエリを取得する.

        Args:
            log_groups: ロググループメタデータのリスト
            region: AWSリージョン

        Returns:
            保存されたクエリのリスト

        Raises:
            AWSClientError: AWS API呼び出しに失敗した場合
        """
        try:
            logs_client = self.get_logs_client(region)
            saved_queries = []
            next_token = None
            first_iteration = True

            # このAPIはページネーターを提供していないため、手動でページングを処理
            while first_iteration or next_token:
                first_iteration = False
                # TODO: 他のクエリ言語タイプのサポート（現在はCWLIのみ）
                kwargs = {'nextToken': next_token, 'queryLanguage': 'CWLI'}
                response = logs_client.describe_query_definitions(**remove_null_values(kwargs))
                saved_queries.extend(response.get('queryDefinitions', []))
                next_token = response.get('nextToken')

            logger.info(f'Retrieved {len(saved_queries)} saved queries')
            modeled_queries = [
                SavedLogsInsightsQuery.model_validate(saved_query) for saved_query in saved_queries
            ]

            log_group_targets = {lg.logGroupName for lg in log_groups}
            # 調査対象のロググループに適用可能な保存クエリのみに絞り込み
            filtered_queries = [
                query
                for query in modeled_queries
                if (query.logGroupNames & log_group_targets)
                or filter_by_prefixes(log_group_targets, query.logGroupPrefixes)
            ]

            logger.info(f'Filtered to {len(filtered_queries)} applicable saved queries')
            return filtered_queries

        except Exception as e:
            logger.error(f'Error in get_saved_queries: {str(e)}')
            raise AWSClientError(f'Failed to get saved queries: {str(e)}')

    def start_query(
        self,
        log_group_names: Optional[List[str]],
        log_group_identifiers: Optional[List[str]],
        start_time: str,
        end_time: str,
        query_string: str,
        limit: Optional[int] = None,
        region: str = 'us-east-1',
    ) -> str:
        """CloudWatch Logs Insightsクエリを開始する.

        Args:
            log_group_names: ロググループ名のリスト
            log_group_identifiers: ロググループ識別子のリスト
            start_time: 開始時間（ISO 8601形式）
            end_time: 終了時間（ISO 8601形式）
            query_string: クエリ文字列
            limit: 結果の最大数
            region: AWSリージョン

        Returns:
            クエリID

        Raises:
            AWSClientError: AWS API呼び出しに失敗した場合
        """
        try:
            logs_client = self.get_logs_client(region)
            kwargs = {
                'startTime': convert_time_to_timestamp(start_time),
                'endTime': convert_time_to_timestamp(end_time),
                'queryString': query_string,
                'logGroupIdentifiers': log_group_identifiers,
                'logGroupNames': log_group_names,
                'limit': limit,
            }

            response = logs_client.start_query(**remove_null_values(kwargs))
            query_id = response['queryId']
            logger.info(f'Started query with ID: {query_id}')
            return query_id

        except Exception as e:
            logger.error(f'Error in start_query: {str(e)}')
            raise AWSClientError(f'Failed to start query: {str(e)}')

    def get_query_results(
        self,
        query_id: str,
        region: str = 'us-east-1',
    ) -> Dict:
        """クエリ結果を取得する.

        Args:
            query_id: クエリID
            region: AWSリージョン

        Returns:
            クエリ結果の辞書

        Raises:
            AWSClientError: AWS API呼び出しに失敗した場合
        """
        try:
            logs_client = self.get_logs_client(region)
            response = logs_client.get_query_results(queryId=query_id)
            logger.info(f'Retrieved results for query ID {query_id}')
            return self._process_query_results(response, query_id)

        except Exception as e:
            logger.error(f'Error in get_query_results: {str(e)}')
            raise AWSClientError(f'Failed to get query results: {str(e)}')

    def stop_query(
        self,
        query_id: str,
        region: str = 'us-east-1',
    ) -> bool:
        """クエリを停止する.

        Args:
            query_id: クエリID
            region: AWSリージョン

        Returns:
            停止が成功したかどうか

        Raises:
            AWSClientError: AWS API呼び出しに失敗した場合
        """
        try:
            logs_client = self.get_logs_client(region)
            response = logs_client.stop_query(queryId=query_id)
            success = response.get('success', False)
            logger.info(f'Stop query {query_id}: {success}')
            return success

        except Exception as e:
            logger.error(f'Error in stop_query: {str(e)}')
            raise AWSClientError(f'Failed to stop query: {str(e)}')

    async def poll_for_query_completion(
        self,
        query_id: str,
        max_timeout: int = 30,
        region: str = 'us-east-1',
    ) -> Dict:
        """クエリの完了を指定されたタイムアウト内でポーリングする.

        Args:
            query_id: ポーリングするクエリID
            max_timeout: 最大待機時間（秒）
            region: AWSリージョン

        Returns:
            クエリ結果の辞書またはタイムアウトメッセージ

        Raises:
            QueryTimeoutError: タイムアウトした場合
            AWSClientError: AWS API呼び出しに失敗した場合
        """
        poll_start = timer()
        logs_client = self.get_logs_client(region)

        while poll_start + max_timeout > timer():
            try:
                response = logs_client.get_query_results(queryId=query_id)
                status = response['status']

                if status in {'Complete', 'Failed', 'Cancelled'}:
                    logger.info(f'Query {query_id} finished with status {status}')
                    return self._process_query_results(response, query_id)

                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f'Error polling query {query_id}: {str(e)}')
                raise AWSClientError(f'Failed to poll query results: {str(e)}')

        msg = f'Query {query_id} did not complete within {max_timeout} seconds'
        logger.warning(msg)
        raise QueryTimeoutError(msg)

    def _process_query_results(self, response: Dict, query_id: str = '') -> Dict:
        """クエリ結果のレスポンスを標準化された形式に処理する.

        Args:
            response: get_query_results APIからの生レスポンス
            query_id: レスポンスに含めるクエリID

        Returns:
            処理されたクエリ結果の辞書
        """
        return {
            'queryId': query_id or response.get('queryId', ''),
            'status': response['status'],
            'statistics': response.get('statistics', {}),
            'results': [
                {field['field']: field['value'] for field in line}
                for line in response.get('results', [])
            ],
        }
