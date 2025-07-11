"""CloudWatch Logs用のMCPツールインターフェース.

このモジュールは、CloudWatch LogsサービスをMCPプロトコル経由で
呼び出し可能なツールとして公開するインターフェースを提供します。
各ツールは適切なパラメータ検証、エラーハンドリング、文書化を含んでいます。
"""

from mcp.server.fastmcp import Context
from pydantic import Field
from typing import Annotated, Dict, List, Literal, Optional

from cloudwatch_logs.domain.exceptions import InvalidParameterError
from cloudwatch_logs.domain.models import (
    LogsMetadata,
    LogsAnalysisResult,
    LogsQueryCancelResult,
)
from cloudwatch_logs.services.logs_service import CloudWatchLogsService
from cloudwatch_logs.services.analysis_service import CloudWatchAnalysisService


class CloudWatchLogsMCPTools:
    """MCPサーバー用のCloudWatch Logsツール."""

    def __init__(self, version: str = '1.0.0'):
        """CloudWatch Logs MCPツールを初期化する.

        Args:
            version: バージョン情報
        """
        self.logs_service = CloudWatchLogsService(version)
        self.analysis_service = CloudWatchAnalysisService(self.logs_service)

    def _validate_log_group_parameters(
        self, log_group_names: Optional[List[str]], log_group_identifiers: Optional[List[str]]
    ) -> None:
        """log_group_namesまたはlog_group_identifiersのいずれか一つが提供されることを検証する.

        Args:
            log_group_names: ロググループ名のリスト
            log_group_identifiers: ロググループ識別子のリスト

        Raises:
            InvalidParameterError: 両方または両方とも提供されていない場合
        """
        if bool(log_group_names) == bool(log_group_identifiers):
            raise InvalidParameterError(
                'Exactly one of log_group_names or log_group_identifiers must be provided'
            )

    def register(self, mcp):
        """すべてのCloudWatch LogsツールをMCPサーバーに登録する.

        Args:
            mcp: FastMCPサーバーインスタンス
        """
        # describe_log_groupsツールの登録
        mcp.tool(name='describe_log_groups')(self.describe_log_groups)

        # analyze_log_groupツールの登録
        mcp.tool(name='analyze_log_group')(self.analyze_log_group)

        # execute_log_insights_queryツールの登録
        mcp.tool(name='execute_log_insights_query')(self.execute_log_insights_query)

        # get_logs_insight_query_resultsツールの登録
        mcp.tool(name='get_logs_insight_query_results')(self.get_logs_insight_query_results)

        # cancel_logs_insight_queryツールの登録
        mcp.tool(name='cancel_logs_insight_query')(self.cancel_logs_insight_query)

    async def describe_log_groups(
        self,
        ctx: Context,
        account_identifiers: Annotated[
            List[str] | None,
            Field(
                description=(
                    'When include_linked_accounts is set to True, use this parameter to specify the list of accounts to search. IMPORTANT: Only has affect if include_linked_accounts is True'
                )
            ),
        ] = None,
        include_linked_accounts: Annotated[
            bool | None,
            Field(
                description=(
                    """If the AWS account is a monitoring account, set this to True to have the tool return log groups in the accounts listed in account_identifiers.
                If this parameter is set to true and account_identifiers contains a null value, the tool returns all log groups in the monitoring account and all log groups in all source accounts that are linked to the monitoring account."""
                )
            ),
        ] = False,
        log_group_class: Annotated[
            Literal['STANDARD', 'INFREQUENT_ACCESS'] | None,
            Field(
                description=('If specified, filters for only log groups of the specified class.')
            ),
        ] = None,
        log_group_name_prefix: Annotated[
            str | None,
            Field(
                description=(
                    'An exact prefix to filter log groups by name. IMPORTANT: Only log groups with names starting with this prefix will be returned.'
                )
            ),
        ] = None,
        max_items: Annotated[
            int | None, Field(description=('The maximum number of log groups to return.'))
        ] = None,
        region: Annotated[
            str,
            Field(description='AWS region to query. Defaults to us-east-1.'),
        ] = 'us-east-1',
    ) -> LogsMetadata:
        """Lists AWS CloudWatch log groups and saved queries associated with them, optionally filtering by a name prefix.

        This tool retrieves information about log groups in the account, or log groups in accounts linked to this account as a monitoring account.
        If a prefix is provided, only log groups with names starting with the specified prefix are returned.

        Additionally returns any user saved queries that are associated with any of the returned log groups.

        Usage: Use this tool to discover log groups that you'd retrieve or query logs from and queries that have been saved by the user.

        Returns:
        --------
        List of log group metadata dictionaries and saved queries associated with them
           Each log group metadata contains details such as:
                - logGroupName: The name of the log group.
                - creationTime: Timestamp when the log group was created
                - retentionInDays: Retention period, if set
                - storedBytes: The number of bytes stored.
                - kmsKeyId: KMS Key Id used for data encryption, if set
                - dataProtectionStatus: Displays whether this log group has a protection policy, or whether it had one in the past, if set
                - logGroupClass: Type of log group class
                - logGroupArn: The Amazon Resource Name (ARN) of the log group. This version of the ARN doesn't include a trailing :* after the log group name.
            Any saved queries that are applicable to the returned log groups are also included.
        """
        try:
            log_groups = self.logs_service.describe_log_groups(
                region=region,
                account_identifiers=account_identifiers,
                include_linked_accounts=include_linked_accounts,
                log_group_class=log_group_class,
                log_group_name_prefix=log_group_name_prefix,
                max_items=max_items,
            )
            
            saved_queries = self.logs_service.get_saved_queries(log_groups, region)
            
            return LogsMetadata(
                log_group_metadata=log_groups,
                saved_queries=saved_queries,
            )

        except Exception as e:
            await ctx.error(f'Error in describing log groups: {str(e)}')
            raise

    async def analyze_log_group(
        self,
        ctx: Context,
        log_group_arn: str = Field(
            ...,
            description='The log group arn to look for anomalies in, as returned by the describe_log_groups tools',
        ),
        start_time: str = Field(
            ...,
            description=(
                'ISO 8601 formatted start time for the CloudWatch Logs Insights query window (e.g., "2025-04-19T20:00:00+00:00").'
            ),
        ),
        end_time: str = Field(
            ...,
            description=(
                'ISO 8601 formatted end time for the CloudWatch Logs Insights query window (e.g., "2025-04-19T21:00:00+00:00").'
            ),
        ),
        region: Annotated[
            str,
            Field(description='AWS region to query. Defaults to us-east-1.'),
        ] = 'us-east-1',
    ) -> LogsAnalysisResult:
        """Analyzes a CloudWatch log group for anomalies, message patterns, and error patterns within a specified time window.

        This tool performs an analysis of the specified log group by:
        1. Discovering and checking log anomaly detectors associated with the log group
        2. Retrieving anomalies from those detectors that fall within the specified time range
        3. Identifying the top 5 most common message patterns
        4. Finding the top 5 patterns containing error-related terms

        Usage: Use this tool to detect anomalies and understand common patterns in your log data, particularly
        focusing on error patterns that might indicate issues. This can help identify potential problems and
        understand the typical behavior of your application.

        Returns:
        --------
        A LogsAnalysisResult object containing:
            - log_anomaly_results: Information about anomaly detectors and their findings
                * anomaly_detectors: List of anomaly detectors for the log group
                * anomalies: List of anomalies that fall within the specified time range
            - top_patterns: Results of the query for most common message patterns
            - top_patterns_containing_errors: Results of the query for patterns containing error-related terms
                (error, exception, fail, timeout, fatal)
        """
        try:
            return await self.analysis_service.analyze_log_group(
                log_group_arn=log_group_arn,
                start_time=start_time,
                end_time=end_time,
                region=region,
            )

        except Exception as e:
            await ctx.error(f'Error analyzing log group: {str(e)}')
            raise

    async def execute_log_insights_query(
        self,
        ctx: Context,
        log_group_names: Annotated[
            List[str] | None,
            Field(
                max_length=50,
                description='The list of up to 50 log group names to be queried. CRITICAL: Exactly one of [log_group_names, log_group_identifiers] should be non-null.',
            ),
        ] = None,
        log_group_identifiers: Annotated[
            List[str] | None,
            Field(
                max_length=50,
                description="The list of up to 50 logGroupIdentifiers to query. You can specify them by the log group name or ARN. If a log group that you're querying is in a source account and you're using a monitoring account, you must use the ARN. CRITICAL: Exactly one of [log_group_names, log_group_identifiers] should be non-null.",
            ),
        ] = None,
        start_time: str = Field(
            ...,
            description=(
                'ISO 8601 formatted start time for the CloudWatch Logs Insights query window (e.g., "2025-04-19T20:00:00+00:00").'
            ),
        ),
        end_time: str = Field(
            ...,
            description=(
                'ISO 8601 formatted end time for the CloudWatch Logs Insights query window (e.g., "2025-04-19T21:00:00+00:00").'
            ),
        ),
        query_string: str = Field(
            ...,
            description='The query string in the Cloudwatch Log Insights Query Language. See https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax.html.',
        ),
        limit: Annotated[
            int | None,
            Field(
                description='The maximum number of log events to return. It is critical to use either this parameter or a `| limit <int>` operator in the query to avoid consuming too many tokens of the agent.'
            ),
        ] = None,
        max_timeout: Annotated[
            int,
            Field(
                description='Maximum time in second to poll for complete results before giving up'
            ),
        ] = 30,
        region: Annotated[
            str,
            Field(description='AWS region to query. Defaults to us-east-1.'),
        ] = 'us-east-1',
    ) -> Dict:
        """Executes a CloudWatch Logs Insights query and waits for the results to be available.

        IMPORTANT: The operation must include exactly one of the following parameters: log_group_names, or log_group_identifiers.

        CRITICAL: The volume of returned logs can easily overwhelm the agent context window. Always include a limit in the query
        (| limit 50) or using the limit parameter.

        Usage: Use to query, filter, collect statistics, or find patterns in one or more log groups. For example, the following
        query lists exceptions per hour.

        ```
        filter @message like /Exception/
        | stats count(*) as exceptionCount by bin(1h)
        | sort exceptionCount desc
        ```

        Returns:
        --------
            A dictionary containing the final query results, including:
                - status: The current status of the query (e.g., Scheduled, Running, Complete, Failed, etc.)
                - results: A list of the actual query results if the status is Complete.
                - statistics: Query performance statistics
                - messages: Any informational messages about the query
        """
        try:
            # ロググループパラメータの排他的検証を実行
            self._validate_log_group_parameters(log_group_names, log_group_identifiers)

            # CloudWatch Logs Insightsクエリを開始
            query_id = self.logs_service.start_query(
                log_group_names=log_group_names,
                log_group_identifiers=log_group_identifiers,
                start_time=start_time,
                end_time=end_time,
                query_string=query_string,
                limit=limit,
                region=region,
            )

            # クエリ完了を待機（ポーリング処理）
            try:
                return await self.logs_service.poll_for_query_completion(
                    query_id=query_id,
                    max_timeout=max_timeout,
                    region=region,
                )
            except Exception as polling_error:
                # ポーリングタイムアウト時は部分的な結果とクエリIDを返却
                msg = f'Query {query_id} did not complete within {max_timeout} seconds. Use get_logs_insight_query_results with the returned queryId to try again to retrieve query results.'
                await ctx.warning(msg)
                return {
                    'queryId': query_id,
                    'status': 'Polling Timeout',
                    'message': msg,
                }

        except Exception as e:
            await ctx.error(f'Error executing CloudWatch Logs Insights query: {str(e)}')
            raise

    async def get_logs_insight_query_results(
        self,
        ctx: Context,
        query_id: str = Field(
            ...,
            description='The unique ID of the query to retrieve the results for. CRITICAL: This ID is returned by the execute_log_insights_query tool.',
        ),
        region: Annotated[
            str,
            Field(description='AWS region to query. Defaults to us-east-1.'),
        ] = 'us-east-1',
    ) -> Dict:
        """Retrieves the results of a previously started CloudWatch Logs Insights query.

        Usage: If a log query is started by execute_log_insights_query tool and has a polling time out, this tool can be used to try to retrieve
        the query results again.

        Returns:
        --------
            A dictionary containing the final query results, including:
                - status: The current status of the query (e.g., Scheduled, Running, Complete, Failed, etc.)
                - results: A list of the actual query results if the status is Complete.
                - statistics: Query performance statistics
                - messages: Any informational messages about the query
        """
        try:
            return self.logs_service.get_query_results(
                query_id=query_id,
                region=region,
            )

        except Exception as e:
            await ctx.error(f'Error retrieving CloudWatch Logs Insights query results: {str(e)}')
            raise

    async def cancel_logs_insight_query(
        self,
        ctx: Context,
        query_id: str = Field(
            ...,
            description='The unique ID of the ongoing query to cancel. CRITICAL: This ID is returned by the execute_log_insights_query tool.',
        ),
        region: Annotated[
            str,
            Field(description='AWS region to query. Defaults to us-east-1.'),
        ] = 'us-east-1',
    ) -> LogsQueryCancelResult:
        """Cancels an ongoing CloudWatch Logs Insights query. If the query has already ended, returns an error that the given query is not running.

        Usage: If a log query is started by execute_log_insights_query tool and has a polling time out, this tool can be used to cancel
        it prematurely to avoid incurring additional costs.

        Returns:
        --------
            A LogsQueryCancelResult with a "success" key, which is True if the query was successfully cancelled.
        """
        try:
            success = self.logs_service.stop_query(
                query_id=query_id,
                region=region,
            )
            
            return LogsQueryCancelResult(success=success)

        except Exception as e:
            await ctx.error(f'Error cancelling CloudWatch Logs Insights query: {str(e)}')
            raise