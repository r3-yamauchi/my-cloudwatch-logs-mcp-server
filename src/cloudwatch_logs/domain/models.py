"""CloudWatch Logs MCP サーバーのデータモデル定義.

このモジュールは、CloudWatch Logsサービスとの通信で使用される
すべてのデータ構造をPydanticモデルとして定義しています。
"""

import json
import re
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Any, Dict, List, Optional, Set

from cloudwatch_logs.utils.time_utils import epoch_ms_to_utc_iso


class LogGroupMetadata(BaseModel):
    """CloudWatch ロググループのメタデータ."""

    logGroupName: str = Field(..., description='ロググループの名前')
    creationTime: str = Field(..., description='ロググループが作成されたISO 8601タイムスタンプ')
    retentionInDays: Optional[int] = Field(default=None, description='保持期間（設定されている場合）')
    metricFilterCount: int = Field(..., description='メトリックフィルタの数')
    storedBytes: int = Field(..., description='保存されているバイト数')
    kmsKeyId: Optional[str] = Field(
        default=None, description='データ暗号化に使用されるKMSキーID（設定されている場合）'
    )
    dataProtectionStatus: Optional[str] = Field(
        default=None,
        description='このロググループに保護ポリシーがあるか、過去にあったかを表示',
    )
    inheritedProperties: List[str] = Field(
        default_factory=list, description='ロググループの継承プロパティのリスト'
    )
    logGroupClass: str = Field(
        default='STANDARD', description='ロググループクラスのタイプ (STANDARD または INFREQUENT_ACCESS)'
    )
    logGroupArn: str = Field(
        ...,
        description='ロググループのAmazon Resource Name (ARN). この版のARNはロググループ名の後にトレーリング:*を含まない',
    )

    @field_validator('creationTime', mode='before')
    @classmethod
    def convert_to_iso8601(cls, v):
        """値がUnixエポックの整数の場合、ISO タイムスタンプ文字列に変換."""
        if isinstance(v, int):
            return epoch_ms_to_utc_iso(v)
        return v


class SavedLogsInsightsQuery(BaseModel):
    """保存されたCloudWatch Logs Insightsクエリ."""

    logGroupNames: Set[str] = Field(
        default_factory=set, description='クエリに関連付けられたロググループ（オプション）'
    )
    name: str = Field(..., description='保存されたクエリの名前')
    queryString: str = Field(..., description='CloudWatch Log Insights クエリ言語のクエリ文字列')
    logGroupPrefixes: Set[str] = Field(
        default_factory=set,
        description='クエリに関連付けられたロググループのプレフィックス（オプション）',
    )

    @model_validator(mode='before')
    @classmethod
    def extract_prefixes(cls, values):
        """クエリ文字列のSOURCEコマンドを解析してロググループプレフィックスを抽出（存在する場合）."""
        query_string = values.get('queryString', '')
        if query_string:
            # SOURCE ... パターンにマッチし、括弧内の内容を抽出
            source_match = re.search(r'SOURCE\s+logGroups\((.*?)\)', query_string)
            if source_match:
                content = source_match.group(1)
                # namePrefixとその値を抽出
                prefix_match = re.search(r'namePrefix:\s*\[(.*?)\]', content)
                if prefix_match:
                    # プレフィックスを分割し、空白と引用符を除去
                    values['logGroupPrefixes'] = {
                        p.strip().strip('\'"') for p in prefix_match.group(1).split(',')
                    }
        return values


class LogsMetadata(BaseModel):
    """CloudWatch ログに関する情報."""

    log_group_metadata: List[LogGroupMetadata] = Field(
        ..., description='ロググループに関するメタデータのリスト'
    )
    saved_queries: List[SavedLogsInsightsQuery] = Field(
        ..., description='ログに関連付けられた保存されたクエリ'
    )


class LogAnomalyDetector(BaseModel):
    """CloudWatch Logs異常検知器."""

    anomalyDetectorArn: str = Field(..., description='異常検知器のARN')
    detectorName: str = Field(..., description='異常検知器の名前')
    anomalyDetectorStatus: str = Field(..., description='異常検知器の現在のステータス')


class LogAnomaly(BaseModel):
    """検知されたログ異常."""

    anomalyDetectorArn: str = Field(..., description='この異常を発見した検知器のARN')
    logGroupArnList: List[str] = Field(
        ..., description='この異常にマッチするロググループARNのリスト'
    )
    firstSeen: str = Field(..., description='このパターンが最初に見られたISO 8601タイムスタンプ')
    lastSeen: str = Field(..., description='このパターンが最後に見られたISO 8601タイムスタンプ')
    description: str = Field(..., description='異常の説明')
    priority: str = Field(..., description='異常の優先度')
    patternRegex: str = Field(..., description='この異常にマッチした正規表現パターン')
    patternString: str = Field(..., description='この異常にマッチした文字列パターン')
    logSamples: List[Dict[str, str]] = Field(
        ..., description='この異常にマッチしたサンプルログメッセージ'
    )
    histogram: Dict[str, int] = Field(
        ..., description='この異常のログメッセージ数のヒストグラム'
    )

    @field_validator('firstSeen', 'lastSeen', mode='before')
    @classmethod
    def convert_to_iso8601(cls, v):
        """値がUnixエポックの整数の場合、ISO タイムスタンプ文字列に変換."""
        if isinstance(v, int):
            return epoch_ms_to_utc_iso(v)
        return v

    @field_validator('histogram', mode='before')
    @classmethod
    def convert_histogram_to_iso8601(cls, v):
        """値がUnixエポックの整数の場合、ISO タイムスタンプ文字列に変換."""
        return {epoch_ms_to_utc_iso(int(timestamp)): count for timestamp, count in v.items()}

    @field_validator('logSamples', mode='before')
    @classmethod
    def convert_log_samples_to_iso8601(cls, v):
        """値がUnixエポックの整数の場合、ISO タイムスタンプ文字列に変換、1つに制限.

        logSamplesはコンテキストウィンドウトークンを節約するため1つに制限される
        """

        def replace_timestamp_with_iso8601(sample: Dict):
            sample['timestamp'] = epoch_ms_to_utc_iso(sample['timestamp'])
            return sample

        return [replace_timestamp_with_iso8601(sample) for sample in v[:1]]


class LogAnomalyResults(BaseModel):
    """ログ異常クエリの結果."""

    anomaly_detectors: List[LogAnomalyDetector] = Field(
        ..., description='このロググループを監視している異常検知器のリスト'
    )
    anomalies: List[LogAnomaly] = Field(
        ..., description='指定された時間範囲で発見された異常のリスト'
    )


class LogsAnalysisResult(BaseModel):
    """ロググループ分析の結果."""

    log_anomaly_results: LogAnomalyResults = Field(
        ..., description='ロググループ内の適用可能なログ異常を探した結果'
    )
    top_patterns: Dict[str, Any] = Field(
        ..., description='ロググループで発見された上位メッセージパターン'
    )
    top_patterns_containing_errors: Dict[str, Any] = Field(
        ..., description='エラーを含むメッセージで発見された上位エラーパターン'
    )


class LogsQueryCancelResult(BaseModel):
    """Logs Insightクエリキャンセルの結果."""

    success: bool = Field(
        ...,
        description='logs insightクエリが正常にキャンセルされた場合はTrue、そうでなければFalse',
    )