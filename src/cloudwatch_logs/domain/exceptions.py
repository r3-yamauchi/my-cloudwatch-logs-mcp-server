"""CloudWatch Logs MCP サーバーのカスタム例外定義モジュール.

このモジュールはCloudWatch Logs MCP サーバーで使用される
カスタム例外クラスを定義します。階層構造により、適切なエラーハンドリングを
実現し、問題の特定と対処を容易にします。
"""


class CloudWatchLogsError(Exception):
    """CloudWatch Logs MCP サーバーのベース例外クラス.
    
    すべてのカスタム例外はこのクラスを継承します。
    これにより、パッケージ固有の例外を統一的に処理できます。
    """
    pass


class InvalidParameterError(CloudWatchLogsError):
    """不正なパラメータが指定された場合に発生する例外.
    
    API呼び出し時にパラメータの検証に失敗した場合、
    または必須パラメータが不足している場合に発生します。
    
    例:
        - log_group_namesとlog_group_identifiersの両方が指定された場合
        - 必須パラメータが未指定の場合
    """
    pass


class AWSClientError(CloudWatchLogsError):
    """AWS クライアント操作が失敗した場合に発生する例外.
    
    AWS SDK (boto3) の操作でエラーが発生した場合に発生します。
    認証エラー、権限不足、サービス制限などが原因となります。
    
    例:
        - AWS認証情報の不備
        - IAM権限の不足
        - CloudWatch Logsサービスのエラー
    """
    pass


class QueryTimeoutError(CloudWatchLogsError):
    """クエリの実行がタイムアウトした場合に発生する例外.
    
    CloudWatch Logs Insightsクエリの実行時間が
    指定されたタイムアウト値を超えた場合に発生します。
    
    例:
        - 大量のログデータを処理するクエリ
        - 複雑なクエリによる処理時間の延長
    """
    pass


class QueryExecutionError(CloudWatchLogsError):
    """クエリの実行が失敗した場合に発生する例外.
    
    CloudWatch Logs Insightsクエリの実行中に
    エラーが発生した場合に発生します。
    
    例:
        - 不正なクエリ構文
        - 存在しないロググループの指定
        - クエリの実行時エラー
    """
    pass