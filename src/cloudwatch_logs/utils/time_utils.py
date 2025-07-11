"""CloudWatch Logs MCP サーバーの時間処理ユーティリティモジュール.

このモジュールはCloudWatch Logs APIとの時間データやり取りで使用される
時間変換関数を提供します。AWS APIは通常Unix タイムスタンプを使用しますが、
ユーザーインターフェースではISO 8601形式が一般的なため、
両形式間の変換を効率的に行います。
"""

import datetime


def epoch_ms_to_utc_iso(ms: int) -> str:
    """エポックからのミリ秒をISO 8601形式のタイムスタンプ文字列に変換する.

    CloudWatch Logs APIは時間をUnixエポックからのミリ秒で返すことが多いため、
    人間が読みやすいISO 8601形式に変換します。

    Args:
        ms: エポックからのミリ秒（1970-01-01 00:00:00 UTCからの経過時間）

    Returns:
        ISO 8601形式のタイムスタンプ文字列（例: "2023-04-19T20:00:00+00:00"）

    Note:
        fromisoformat()との互換性のため、'Z'接尾辞を'+00:00'に変換しています。
        これはPythonの datetime.fromisoformat() が 'Z' 接尾辞を完全には
        サポートしていないためです。

    Examples:
        >>> epoch_ms_to_utc_iso(1682798400000)  # 2023-04-29 20:00:00 UTC
        '2023-04-29T20:00:00+00:00'
    """
    # エポックミリ秒をdatetimeオブジェクトに変換（UTC タイムゾーン付き）
    iso_string = datetime.datetime.fromtimestamp(ms / 1000.0, tz=datetime.timezone.utc).isoformat()
    
    # タイムゾーンが+00:00として表現されることを確認
    # isoformat()メソッドがZを返す場合は Zを+00:00に変換
    if iso_string.endswith('Z'):
        iso_string = iso_string[:-1] + '+00:00'
    return iso_string


def convert_time_to_timestamp(time_str: str) -> int:
    """ISO 8601時間文字列をUnixタイムスタンプに変換する.

    ユーザーから提供されるISO 8601形式の時間文字列を、
    CloudWatch Logs APIが期待するUnixタイムスタンプ（秒）に変換します。

    Args:
        time_str: ISO 8601形式の時間文字列
                 例: "2023-04-19T20:00:00+00:00", "2023-04-19T20:00:00Z"

    Returns:
        整数のUnixタイムスタンプ（秒）
        例: 1682798400

    Raises:
        ValueError: 不正な時間文字列形式が指定された場合

    Examples:
        >>> convert_time_to_timestamp("2023-04-29T20:00:00+00:00")
        1682798400
        >>> convert_time_to_timestamp("2023-04-29T20:00:00Z")
        1682798400
    """
    return int(datetime.datetime.fromisoformat(time_str).timestamp())