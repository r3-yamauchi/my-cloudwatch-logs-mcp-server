"""CloudWatch Logs MCP サーバーのデータ処理ユーティリティモジュール.

このモジュールはCloudWatch Logs APIのレスポンスデータを処理し、
クリーンアップや効率化を行うための関数を提供します。
特に、APIパラメータの最適化やクエリ結果の最適化に使用されます。
"""

import json
from typing import Dict, List, Set


def remove_null_values(d: Dict) -> Dict:
    """辞書からnull値（None値）を持つキーと値のペアを除去した新しい辞書を返す.

    AWS APIの多くはオプションパラメータを受け付けますが、
    None値を含むパラメータを送信するとエラーになることがあります。
    この関数は、そのような不要なパラメータを事前に除去します。

    Args:
        d: 処理する辞書（通常はAPI呼び出しパラメータ）

    Returns:
        null値が除去された新しい辞書

    Examples:
        >>> remove_null_values({"name": "test", "value": None, "count": 5})
        {"name": "test", "count": 5}
    """
    return {k: v for k, v in d.items() if v is not None}


def filter_by_prefixes(strings: Set[str], prefixes: Set[str]) -> Set[str]:
    """指定されたプレフィックスのいずれかで始まる文字列のみでフィルタリングして返す.

    保存されたCloudWatch Logs Insightsクエリは、特定のロググループまたは
    ロググループのプレフィックスに関連付けられています。この関数は、
    現在表示対象のロググループに関連するクエリのみを効率的に抽出します。

    Args:
        strings: フィルタリングする文字列のセット（通常はロググループ名）
        prefixes: フィルタリングに使用するプレフィックスのセット

    Returns:
        フィルタリングされた文字列のセット

    Examples:
        >>> strings = {"/aws/lambda/function1", "/aws/lambda/function2", "/aws/ecs/task1"}
        >>> prefixes = {"/aws/lambda/"}
        >>> filter_by_prefixes(strings, prefixes)
        {"/aws/lambda/function1", "/aws/lambda/function2"}
    """
    return {s for s in strings if any(s.startswith(p) for p in prefixes)}


def clean_up_pattern(pattern_result: List[Dict[str, str]]) -> None:
    """パターンクエリの結果から余分なフィールドを削除し、ログサンプルを最適化する.

    CloudWatch Logs Insightsのパターンクエリは、デバッグ情報や可視化情報を
    含む大量のデータを返すことがあります。MCPサーバーのコンテキストでは、
    これらの情報は不要であり、トークン使用量を削減するために除去します。

    Args:
        pattern_result: パターンクエリの結果リスト（in-place変更されます）

    Note:
        この関数は元のリストを変更します（in-place操作）。
        元データを保持する必要がある場合は、事前にコピーを作成してください。

    Examples:
        >>> pattern_result = [
        ...     {"@pattern": "ERROR", "@tokens": ["error", "failed"], "@logSamples": "[]"},
        ...     {"@pattern": "INFO", "@tokens": ["info"], "@logSamples": "[]"}
        ... ]
        >>> clean_up_pattern(pattern_result)
        >>> # @tokensフィールドが削除され、@logSamplesが最適化される
    """
    for entry in pattern_result:
        # デバッグ情報を削除（トークン使用量削減）
        entry.pop('@tokens', None)
        entry.pop('@visualization', None)
        
        # ログサンプルを1つに制限（コンテキストウィンドウサイズの制限対応）
        if '@logSamples' in entry:
            # JSON文字列をパースして最初の1つのみを保持
            log_samples = json.loads(entry.get('@logSamples', '[]'))
            entry['@logSamples'] = log_samples[:1]