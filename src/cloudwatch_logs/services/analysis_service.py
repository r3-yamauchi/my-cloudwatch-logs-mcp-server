"""CloudWatch Logs分析サービス：異常検知とパターン分析を担当.

このモジュールは、CloudWatch Logsの高度な分析機能を提供します。
主な機能として異常検知、ログパターン分析、エラーパターン分析があり、
これらを組み合わせた包括的なログ分析を実行できます。
"""

import asyncio
import datetime
from loguru import logger
from typing import Dict, List

from cloudwatch_logs.domain.exceptions import AWSClientError
from cloudwatch_logs.domain.models import (
    LogAnomaly, 
    LogAnomalyDetector, 
    LogAnomalyResults, 
    LogsAnalysisResult
)
from cloudwatch_logs.services.logs_service import CloudWatchLogsService
from cloudwatch_logs.utils.data_utils import clean_up_pattern


class CloudWatchAnalysisService:
    """CloudWatch Logs分析・異常検知を担当するサービス."""

    def __init__(self, logs_service: CloudWatchLogsService):
        """CloudWatch分析サービスを初期化する.

        Args:
            logs_service: CloudWatch Logsサービス
        """
        self.logs_service = logs_service

    def _get_logs_client(self, region: str):
        """指定されたリージョンのCloudWatch Logsクライアントを取得する.

        Args:
            region: AWSリージョン

        Returns:
            CloudWatch Logsクライアント
        """
        return self.logs_service.get_logs_client(region)

    def _is_applicable_anomaly(
        self, 
        anomaly: LogAnomaly, 
        log_group_arn: str, 
        start_time: str, 
        end_time: str
    ) -> bool:
        """異常が指定された条件に適用可能かどうかを判定する.

        Args:
            anomaly: 異常データ
            log_group_arn: ロググループARN
            start_time: 開始時間（ISO 8601形式）
            end_time: 終了時間（ISO 8601形式）

        Returns:
            適用可能かどうか
        """
        # 時間範囲のオーバーラップを確認
        try:
            anomaly_first_seen = datetime.datetime.fromisoformat(anomaly.firstSeen)
            anomaly_last_seen = datetime.datetime.fromisoformat(anomaly.lastSeen)
            end_time_dt = datetime.datetime.fromisoformat(end_time)
            start_time_dt = datetime.datetime.fromisoformat(start_time)

            if anomaly_first_seen > end_time_dt or anomaly_last_seen < start_time_dt:
                return False
        except ValueError as e:
            logger.error(f'Error parsing timestamps for anomaly comparison: {e}')
            # 日時解析に失敗した場合は文字列比較でフォールバック処理
            if anomaly.firstSeen > end_time or anomaly.lastSeen < start_time:
                return False

        # このロググループに対する異常かどうかを確認
        return log_group_arn in anomaly.logGroupArnList

    async def get_log_anomalies(
        self,
        log_group_arn: str,
        start_time: str,
        end_time: str,
        region: str = 'us-east-1',
    ) -> LogAnomalyResults:
        """指定されたロググループの異常を取得する.

        Args:
            log_group_arn: ロググループARN
            start_time: 開始時間（ISO 8601形式）
            end_time: 終了時間（ISO 8601形式）
            region: AWSリージョン

        Returns:
            ログ異常結果

        Raises:
            AWSClientError: AWS API呼び出しに失敗した場合
        """
        try:
            logs_client = self._get_logs_client(region)
            
            # 1. このロググループの異常検知器を取得
            detectors: List[LogAnomalyDetector] = []
            paginator = logs_client.get_paginator('list_log_anomaly_detectors')
            for page in paginator.paginate(filterLogGroupArn=log_group_arn):
                detectors.extend([
                    LogAnomalyDetector.model_validate(d)
                    for d in page.get('anomalyDetectors', [])
                ])

            logger.info(f'Found {len(detectors)} anomaly detectors for log group')

            # 2. 各検知器の異常を取得
            anomalies: List[LogAnomaly] = []
            for detector in detectors:
                paginator = logs_client.get_paginator('list_anomalies')
                for page in paginator.paginate(
                    anomalyDetectorArn=detector.anomalyDetectorArn, 
                    suppressionState='UNSUPPRESSED'
                ):
                    anomalies.extend([
                        LogAnomaly.model_validate(anomaly) 
                        for anomaly in page.get('anomalies', [])
                    ])

            # 3. 適用可能な異常をフィルタリング
            applicable_anomalies = [
                anomaly for anomaly in anomalies 
                if self._is_applicable_anomaly(anomaly, log_group_arn, start_time, end_time)
            ]

            logger.info(
                f'Found {len(anomalies)} total anomalies, '
                f'{len(applicable_anomalies)} applicable to time range'
            )

            return LogAnomalyResults(
                anomaly_detectors=detectors, 
                anomalies=applicable_anomalies
            )

        except Exception as e:
            logger.error(f'Error in get_log_anomalies: {str(e)}')
            raise AWSClientError(f'Failed to get log anomalies: {str(e)}')

    async def analyze_log_patterns(
        self,
        log_group_arn: str,
        start_time: str,
        end_time: str,
        region: str = 'us-east-1',
        max_timeout: int = 30,
    ) -> Dict:
        """ログパターンを分析する.

        Args:
            log_group_arn: ロググループARN
            start_time: 開始時間（ISO 8601形式）
            end_time: 終了時間（ISO 8601形式）
            region: AWSリージョン
            max_timeout: 最大タイムアウト時間（秒）

        Returns:
            パターン分析結果

        Raises:
            AWSClientError: AWS API呼び出しに失敗した場合
        """
        try:
            query_id = self.logs_service.start_query(
                log_group_names=None,
                log_group_identifiers=[log_group_arn],
                start_time=start_time,
                end_time=end_time,
                query_string='pattern @message | sort @sampleCount desc | limit 5',
                limit=5,
                region=region,
            )

            result = await self.logs_service.poll_for_query_completion(
                query_id=query_id,
                max_timeout=max_timeout,
                region=region,
            )

            # パターン結果をクリーンアップ（トークン使用量最適化のため）
            clean_up_pattern(result.get('results', []))
            
            return result

        except Exception as e:
            logger.error(f'Error in analyze_log_patterns: {str(e)}')
            raise AWSClientError(f'Failed to analyze log patterns: {str(e)}')

    async def analyze_error_patterns(
        self,
        log_group_arn: str,
        start_time: str,
        end_time: str,
        region: str = 'us-east-1',
        max_timeout: int = 30,
    ) -> Dict:
        """エラーパターンを分析する.

        Args:
            log_group_arn: ロググループARN
            start_time: 開始時間（ISO 8601形式）
            end_time: 終了時間（ISO 8601形式）
            region: AWSリージョン
            max_timeout: 最大タイムアウト時間（秒）

        Returns:
            エラーパターン分析結果

        Raises:
            AWSClientError: AWS API呼び出しに失敗した場合
        """
        try:
            query_id = self.logs_service.start_query(
                log_group_names=None,
                log_group_identifiers=[log_group_arn],
                start_time=start_time,
                end_time=end_time,
                query_string='fields @timestamp, @message | filter @message like /(?i)(error|exception|fail|timeout|fatal)/ | pattern @message | limit 5',
                limit=5,
                region=region,
            )

            result = await self.logs_service.poll_for_query_completion(
                query_id=query_id,
                max_timeout=max_timeout,
                region=region,
            )

            # パターン結果をクリーンアップ（トークン使用量最適化のため）
            clean_up_pattern(result.get('results', []))
            
            return result

        except Exception as e:
            logger.error(f'Error in analyze_error_patterns: {str(e)}')
            raise AWSClientError(f'Failed to analyze error patterns: {str(e)}')

    async def analyze_log_group(
        self,
        log_group_arn: str,
        start_time: str,
        end_time: str,
        region: str = 'us-east-1',
        max_timeout: int = 30,
    ) -> LogsAnalysisResult:
        """ロググループの包括的な分析を実行する.

        Args:
            log_group_arn: ロググループARN
            start_time: 開始時間（ISO 8601形式）
            end_time: 終了時間（ISO 8601形式）
            region: AWSリージョン
            max_timeout: 最大タイムアウト時間（秒）

        Returns:
            ログ分析結果

        Raises:
            AWSClientError: AWS API呼び出しに失敗した場合
        """
        try:
            # 異常検知、パターン分析、エラーパターン分析を並列実行で効率化
            log_anomaly_results, pattern_result, error_pattern_result = await asyncio.gather(
                self.get_log_anomalies(log_group_arn, start_time, end_time, region),
                self.analyze_log_patterns(log_group_arn, start_time, end_time, region, max_timeout),
                self.analyze_error_patterns(log_group_arn, start_time, end_time, region, max_timeout),
            )

            return LogsAnalysisResult(
                log_anomaly_results=log_anomaly_results,
                top_patterns=pattern_result,
                top_patterns_containing_errors=error_pattern_result,
            )

        except Exception as e:
            logger.error(f'Error in analyze_log_group: {str(e)}')
            raise AWSClientError(f'Failed to analyze log group: {str(e)}')