# CloudWatch Logs MCP ツール - 日本語翻訳

このファイルは、`src/interfaces/mcp_tools.py` 内の英語で書かれた部分（docstring）の日本語翻訳を提供します。

## 目次

1. [describe_log_groups メソッド](#describe_log_groups-メソッド)
2. [analyze_log_group メソッド](#analyze_log_group-メソッド)
3. [execute_log_insights_query メソッド](#execute_log_insights_query-メソッド)
4. [get_logs_insight_query_results メソッド](#get_logs_insight_query_results-メソッド)
5. [cancel_logs_insight_query メソッド](#cancel_logs_insight_query-メソッド)
6. [補足情報](#補足情報)
   - [パラメータの説明](#パラメータの説明)

## describe_log_groups メソッド

### 概要
AWS CloudWatch ログ グループと、それらに関連付けられた保存されたクエリを一覧表示します。
名前プレフィックスでのオプションフィルタリングも可能です。

### 説明
このツールは、アカウント内のログ グループ、または監視アカウントとしてこのアカウントにリンクされたアカウント内のログ グループに関する情報を取得します。
プレフィックスが指定された場合、指定されたプレフィックスで始まる名前のログ グループのみが返されます。

また、返されたログ グループのいずれかに関連付けられたユーザー保存クエリも返されます。

### 使用方法
このツールは、ログを取得またはクエリするログ グループと、ユーザーが保存したクエリを発見するために使用します。

### 戻り値
ログ グループ メタデータ辞書のリストと、それらに関連付けられた保存されたクエリ

各ログ グループ メタデータには以下の詳細が含まれます：
- logGroupName: ログ グループの名前
- creationTime: ログ グループが作成されたタイムスタンプ
- retentionInDays: 設定されている場合の保持期間
- storedBytes: 保存されているバイト数
- kmsKeyId: 設定されている場合、データ暗号化に使用されるKMSキーID
- dataProtectionStatus: このログ グループに保護ポリシーがあるか、過去にあったかを表示（設定されている場合）
- logGroupClass: ログ グループ クラスの種類
- logGroupArn: ログ グループのAmazonリソース名（ARN）。このバージョンのARNには、ログ グループ名の後の末尾の:*は含まれません。

返されたログ グループに適用可能な保存されたクエリも含まれます。

## analyze_log_group メソッド

### 概要
指定された時間ウィンドウ内で CloudWatch ログ グループの異常、メッセージ パターン、エラー パターンを分析します。

### 説明
このツールは、指定されたログ グループの分析を以下の方法で実行します：
1. ログ グループに関連付けられたログ異常検出器を発見し、チェックします
2. 指定された時間範囲内にあるこれらの検出器からの異常を取得します
3. 最も一般的な5つのメッセージ パターンを特定します
4. エラー関連用語を含む上位5つのパターンを見つけます

### 使用方法
このツールは、ログ データの異常を検出し、一般的なパターンを理解するために使用します。
特に、問題を示す可能性があるエラー パターンに焦点を当てます。
これにより、潜在的な問題を特定し、アプリケーションの典型的な動作を理解することができます。

### 戻り値
以下を含む LogsAnalysisResult オブジェクト：
- log_anomaly_results: 異常検出器とその発見に関する情報
  - anomaly_detectors: ログ グループの異常検出器のリスト
  - anomalies: 指定された時間範囲内にある異常のリスト
- top_patterns: 最も一般的なメッセージ パターンのクエリ結果
- top_patterns_containing_errors: エラー関連用語を含むパターンのクエリ結果（error、exception、fail、timeout、fatal）

## execute_log_insights_query メソッド

### 概要
CloudWatch Logs Insights クエリを実行し、結果が利用可能になるまで待機します。

### 重要事項
この操作には以下のパラメータのいずれか一つを正確に含める必要があります：log_group_names、または log_group_identifiers。

### 重要な注意点
返されるログの量は、エージェントのコンテキスト ウィンドウを簡単に圧迫する可能性があります。
常にクエリに制限を含めるか（| limit 50）、limit パラメータを使用してください。

### 使用方法
1つ以上のログ グループでクエリ、フィルタリング、統計の収集、またはパターンの検索を行うために使用します。例えば、以下のクエリは1時間ごとの例外をリストします。

```
filter @message like /Exception/
| stats count(*) as exceptionCount by bin(1h)
| sort exceptionCount desc
```

### 戻り値
最終的なクエリ結果を含む辞書：
- status: クエリの現在のステータス（例：Scheduled、Running、Complete、Failed など）
- results: ステータスが Complete の場合の実際のクエリ結果のリスト
- statistics: クエリのパフォーマンス統計
- messages: クエリに関する情報メッセージ

## get_logs_insight_query_results メソッド

### 概要
以前に開始された CloudWatch Logs Insights クエリの結果を取得します。

### 使用方法
execute_log_insights_query ツールによってログ クエリが開始され、ポーリング タイムアウトが発生した場合、このツールを使用してクエリ結果を再度取得することができます。

### 戻り値
最終的なクエリ結果を含む辞書：
- status: クエリの現在のステータス（例：Scheduled、Running、Complete、Failed など）
- results: ステータスが Complete の場合の実際のクエリ結果のリスト
- statistics: クエリのパフォーマンス統計
- messages: クエリに関する情報メッセージ

## cancel_logs_insight_query メソッド

### 概要
進行中の CloudWatch Logs Insights クエリをキャンセルします。クエリが既に終了している場合は、指定されたクエリが実行されていないというエラーを返します。

### 使用方法
execute_log_insights_query ツールによってログ クエリが開始され、ポーリング タイムアウトが発生した場合、このツールを使用してクエリを途中でキャンセルし、追加コストの発生を回避することができます。

### 戻り値
"success" キーを持つ LogsQueryCancelResult。クエリが正常にキャンセルされた場合は True になります。

## 補足情報

### パラメータの説明
- **account_identifiers**: include_linked_accounts が True に設定されている場合、検索するアカウントのリストを指定するために使用します。重要：include_linked_accounts が True の場合のみ影響があります。
- **include_linked_accounts**: AWS アカウントが監視アカウントの場合、これを True に設定することで、account_identifiers にリストされているアカウントのログ グループを返すことができます。
- **log_group_class**: 指定された場合、指定されたクラスのログ グループのみにフィルタリングします。
- **log_group_name_prefix**: ログ グループを名前でフィルタリングする正確なプレフィックス。重要：このプレフィックスで始まる名前のログ グループのみが返されます。
- **max_items**: 返すログ グループの最大数。
- **region**: クエリするAWSリージョン。デフォルトは us-east-1。
- **start_time**: CloudWatch Logs Insights クエリ ウィンドウのISO 8601形式の開始時刻（例："2025-04-19T20:00:00+00:00"）。
- **end_time**: CloudWatch Logs Insights クエリ ウィンドウのISO 8601形式の終了時刻（例："2025-04-19T21:00:00+00:00"）。
- **query_string**: CloudWatch Log Insights クエリ言語でのクエリ文字列。詳細は https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax.html を参照。
- **limit**: 返すログ イベントの最大数。エージェントのトークンを過度に消費しないよう、このパラメータまたはクエリ内の `| limit <int>` オペレータのいずれかを使用することが重要です。
- **max_timeout**: 結果の取得を諦める前に完全な結果をポーリングする最大時間（秒）。
- **query_id**: 結果を取得するクエリの一意のID。重要：このIDは execute_log_insights_query ツールによって返されます。
