"""CloudWatch Logs MCP サーバーのメインエントリーポイント.

このモジュールはCloudWatch Logs MCP サーバーの起動と初期化を担当します。
FastMCPフレームワークを使用してMCPサーバーを構築し、CloudWatch Logs関連の
ツールを登録して、クライアントからのリクエストを処理可能な状態にします。

アーキテクチャ上の位置づけ:
- インターフェース層の最上位モジュール
- MCPプロトコルの実装とサーバー起動を担当
- ビジネスロジックは分離されたサービス層に委譲

使用方法:
    コマンドライン実行:
        $ uv run cloudwatch-logs-mcp

    または直接実行:
        $ python -m interfaces.mcp_server
"""

from interfaces.mcp_tools import CloudWatchLogsMCPTools
from loguru import logger
from mcp.server.fastmcp import FastMCP


# MCPサーバーの初期化設定
# FastMCPフレームワークを使用してサーバーインスタンスを作成
mcp = FastMCP(
    'cloudwatch-logs-mcp',  # サーバー名（クライアント側で識別に使用）
    instructions=(
        'このMCPサーバーを使用して、CloudWatch Logsの読み取り専用コマンドを実行し、'
        'ログデータを分析します。ロググループの検索、CloudWatch Logs Insightsクエリの実行、'
        'ログパターンと異常の分析をサポートします。'
        'CloudWatch Logs Insightsを使用することで、ログデータを対話的に検索・分析できます。'
    ),
    dependencies=[
        'boto3',      # AWS SDK for Python
        'pydantic',   # データバリデーション
        'loguru',     # ログ出力
    ],
)

# CloudWatch Logsツールの初期化と登録
# サーバー起動時に必要なツールを事前に登録
try:
    # CloudWatch Logs MCPツールインスタンスの作成
    cloudwatch_logs_tools = CloudWatchLogsMCPTools(version='1.0.0')

    # MCPサーバーにツールを登録
    # これにより、クライアントから各ツールが呼び出し可能になる
    cloudwatch_logs_tools.register(mcp)

    logger.info('CloudWatch Logs tools registered successfully')
    logger.info('Available tools: describe_log_groups, analyze_log_group, '
                'execute_log_insights_query, get_logs_insight_query_results, '
                'cancel_logs_insight_query, get_query_syntax_documentation')

except Exception as e:
    # ツール登録に失敗した場合は、サーバーの起動を中止
    logger.error(f'Error initializing CloudWatch Logs tools: {str(e)}')
    logger.error('Server startup aborted due to tool registration failure')
    raise


def main():
    """MCPサーバーを実行する.

    このメイン関数は、MCPサーバーの起動処理を実行します。
    サーバーは起動後、MCPクライアントからの接続を待機し、
    リクエストに応じてCloudWatch Logs関連の処理を実行します。

    Note:
        この関数は無限ループとなり、サーバーの停止まで実行され続けます。
        CTRL+Cやシグナルによる停止が可能です。

    Raises:
        Exception: サーバーの起動に失敗した場合
    """
    logger.info('Starting CloudWatch Logs MCP server')
    logger.info('Server ready to accept MCP connections')

    try:
        # MCPサーバーの実行開始
        # この呼び出しは無限ループとなり、サーバーが停止するまで継続
        mcp.run()
    except KeyboardInterrupt:
        logger.info('Server shutdown requested by user')
    except Exception as e:
        logger.error(f'Server error: {str(e)}')
        raise
    finally:
        logger.info('CloudWatch Logs MCP server stopped')


if __name__ == '__main__':
    # このファイルが直接実行された場合のエントリーポイント
    main()
