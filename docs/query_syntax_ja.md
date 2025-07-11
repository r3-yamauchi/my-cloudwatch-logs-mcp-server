# CloudWatch Logs Insights クエリ構文 完全ガイド

## 概要

CloudWatch Logs Insightsは、ログデータの検索・分析・パターン発見を可能にする強力なクエリ言語をサポートしています。この言語は、一般的な関数、算術・比較演算、正規表現など、様々な機能と操作を提供します。

### 重要な注意事項

大規模なクエリの実行による過度な課金を避けるため、以下のベストプラクティスを守ってください：

- **各クエリに必要なロググループのみを選択する**
- **クエリの時間範囲を可能な限り狭く指定する**
- **コンソールでクエリを実行する際は、ページを閉じる前にすべてのクエリをキャンセルする**（そうしないとクエリは完了まで実行され続けます）
- **ダッシュボードにCloudWatch Logs Insightsウィジェットを追加する場合は、高頻度での更新を避ける**（更新のたびに新しいクエリが開始されます）

### 基本的な構文ルール

- **複数のコマンドを使用する場合は、パイプ文字（|）で区切る**
- **コメントを追加する場合は、ハッシュ文字（#）を使用する**
- **CloudWatch Logsは自動的に@文字で始まるフィールドを発見する**
- **すべてのコマンドはスタンダード・ログクラスをサポート。インフリークエントアクセス・ログクラスには一部制限があります**

## コマンド一覧

### display

**説明**: クエリ結果に特定のフィールドを表示します

**構文**: `display field1, field2, ...`

**動作**: 指定したフィールドのみを表示します。複数のdisplayコマンドを使用した場合、最後のdisplayコマンドのみが有効になります。

**例**:
```
fields @message
| parse @message "[*] *" as loggingType, loggingMessage
| filter loggingType = "ERROR"
| display loggingMessage
```

**ヒント**:
- クエリ内でdisplayは1回だけ使用することを推奨
- 複数回使用した場合、最後のdisplayコマンドのみが有効

### fields

**説明**: 特定のフィールドをクエリ結果に表示し、関数と操作をサポートします

**構文**: `fields field1, field2, expression as alias`

**動作**: displayコマンドがない場合、複数のfieldsコマンドで指定されたすべてのフィールドが表示されます

**例**:
```
# 特定のフィールドを表示
fields @timestamp, @message
| sort @timestamp desc
| limit 20
```

```
# 抽出フィールドを作成
fields ispresent(@message) as hasMessage, @timestamp
```

**ヒント**:
- 関数を使用する場合はdisplayではなくfieldsを使用
- 'as'キーワードで新しいフィールドを作成可能

### filter

**説明**: 1つ以上の条件に一致するログイベントをフィルタリングします

**構文**: `filter condition`

**サポートされる演算子**:
- **比較演算子**: `=`, `!=`, `<`, `<=`, `>`, `>=`
- **ブール演算子**: `and`, `or`, `not`
- **パターンマッチング**: `like`, `not like`, `=~`, `in`, `not in`

**例**:

```
# 単一条件フィルタ
fields @timestamp, @message
| filter range > 3000
| sort @timestamp desc
| limit 20
```

```
# 複数条件
filter range > 3000 and accountId = 123456789012
```

```
# パターンマッチング
filter @message like "Exception"
```

```
# 正規表現
filter @message =~ /Exception/
```

```
# 大文字小文字を区別しないマッチング
filter @message like /(?i)Exception/
```

```
# セットメンバーシップ
filter logGroup in ["example_group"]
```

**フィールドインデックス**:
- フィールドインデックスが作成されている場合、特定のフィルタパターンでクエリパフォーマンスが向上します
- サポートされるパターン: `filter fieldName = value`, `filter fieldName IN [values]`
- サポートされないパターン: `filter fieldName like pattern`

### stats

**説明**: 集計統計を計算し、視覚化を作成します

**構文**: `stats function(field) by grouping_field`

**集計関数**:
- `avg`: 数値の平均値
- `count`: イベントまたは非null値の数
- `count_distinct`: 一意の値の数
- `max`: 最大値
- `min`: 最小値
- `pct`: パーセンタイル計算
- `stddev`: 標準偏差
- `sum`: 合計値

**非集計関数**:
- `earliest`: 最も古いタイムスタンプからの値
- `latest`: 最新のタイムスタンプからの値
- `sortsFirst`: ソート順で最初の値
- `sortsLast`: ソート順で最後の値

**例**:

```
# 時系列の視覚化
stats count(*) by queryType, bin(1h)
```

```
# 平均値の計算
stats avg(myfield1) by bin(5m)
```

```
# 複数の集計
stats avg(bytes), max(bytes) by dstAddr
```

```
# グループ化された統計
stats count(*) by queryType
```

**複数のstatsコマンド**:
- 1つのクエリで最大2つのstatsコマンドを使用可能
- 2番目のstatsコマンドは最初のstatsコマンドの結果のみを参照可能
- sort/limitは2番目のstatsコマンドの後に配置する必要があります

### parse

**説明**: ログフィールドからデータを抽出し、グロブパターンまたは正規表現を使用します

**構文**: `parse field "pattern" as field1, field2`

**モード**:
- **グロブモード**: ワイルドカード（*）を使用したパターンマッチング
- **正規表現モード**: 複雑なパターンに対応した正規表現

**例**:

```
# グロブパターンによる抽出
parse @message "user=*, method:*, latency := *" as @user, @method, @latency
```

```
# 正規表現による抽出
parse @message /user=(?<user2>.*?), method:(?<method2>.*?), latency := (?<latency2>.*?)/
```

```
# 名前付きキャプチャグループ
parse @message /(?<NetworkInterface>eni-.*?) / | display NetworkInterface
```

```
# 複雑な解析とフィルタリング
FIELDS @message
| PARSE @message "* [*] *" as loggingTime, loggingType, loggingMessage
| FILTER loggingType IN ["ERROR", "INFO"]
| DISPLAY loggingMessage, loggingType = "ERROR" as isError
```

**制限事項**:
- JSONイベントは取り込み時に平坦化されます
- ネストされたJSONの解析にはグロブではなく正規表現が必要
- JSONイベントあたり最大200フィールド

### sort

**説明**: 指定したフィールドでログイベントを昇順（asc）または降順（desc）で表示します

**構文**: `sort field [asc|desc]`

**ソートアルゴリズム**: 自然ソートの更新版

**ソートルール**:
- 非数値の値は数値の値より前に配置
- 数値部分は長さ、次に数値で順序付け
- 非数値部分はUnicode値で順序付け

**例**:

```
# タイムスタンプの降順ソート
sort @timestamp desc
```

```
# トップNクエリ
stats sum(packets) as packetsTransferred by srcAddr, dstAddr
| sort packetsTransferred desc
| limit 15
```

### pattern

**説明**: ログデータを自動的にパターンにクラスタリングします

**構文**: `pattern field`

**入力タイプ**: 
- @messageフィールド
- parseコマンドで抽出されたフィールド
- 文字列操作されたフィールド

**出力フィールド**:
- `@pattern`: 動的トークンを含む共有テキスト構造
- `@ratio`: パターンに一致するログイベントの比率
- `@sampleCount`: パターンに一致するイベントの数
- `@severityLabel`: ログの重要度レベル（Error、Warning、Info、Debug）

**例**:

```
# 基本的なパターン分析
pattern @message
```

```
# フィルタリングとパターン
filter @message like /ERROR/
| pattern @message
```

```
# 解析とパターン
filter @message like /ERROR/
| parse @message 'Failed to do: *' as cause
| pattern cause
| sort @sampleCount asc
```

### limit

**説明**: 返すログイベントの最大数を指定します

**構文**: `limit number`

**デフォルト**: 省略した場合は10,000ログイベント

**例**:
```
# 最新の25件のイベント
fields @timestamp, @message
| sort @timestamp desc
| limit 25
```

### dedup

**説明**: 指定したフィールドの値に基づいて重複する結果を削除します

**構文**: `dedup field1, field2, ...`

**動作**:
- ソート順で最初の結果を保持
- Null値は重複とみなされません
- 予測可能な結果のためにsortと組み合わせて使用することを推奨

**例**:
```
# サーバー別の重複除去
fields @timestamp, server, severity, message
| sort @timestamp desc
| dedup server
```

**制限事項**:
- dedupの後にはlimitコマンドのみ使用可能
- null値を除外するにはisPresent()関数でフィルタリング

### その他のコマンド

**diff**: 現在の時間期間と同じ長さの前の時間期間を比較してトレンドを特定

**unmask**: データ保護ポリシーによってマスクされたコンテンツを表示

**unnest**: リストを複数のレコードに平坦化

**filterIndex**: パフォーマンス向上のためフィールドインデックスを使用するよう強制

**SOURCE**: プレフィックス、アカウント、クラスによってロググループを指定（CLI/APIのみ）

## 関数一覧

### 算術演算子

数値計算のための算術演算子:

| 演算子 | 説明 |
|--------|------|
| `+` | 加算 |
| `-` | 減算 |
| `*` | 乗算 |
| `/` | 除算 |
| `^` | 冪乗（2^3 = 8） |
| `%` | 剰余・モジュロ（10%3 = 1） |

**例**:
- `field1 + field2`: 2つの数値フィールドを加算
- `bytes / 1024`: バイトをキロバイトに変換

### ブール演算子

論理演算のためのブール演算子:

| 演算子 | 説明 |
|--------|------|
| `and` | 論理AND |
| `or` | 論理OR |
| `not` | 論理NOT |

**使用法**: TRUEまたはFALSEを返す関数でのみ使用

### 比較演算子

すべてのデータ型に対応する比較演算子:

| 演算子 | 説明 |
|--------|------|
| `=` | 等しい |
| `!=` | 等しくない |
| `<` | より小さい |
| `>` | より大きい |
| `<=` | 以下 |
| `>=` | 以上 |

**戻り値**: ブール値

### 数値関数

数学的操作のための数値関数:

| 関数 | 説明 |
|------|------|
| `abs(a)` | 絶対値 |
| `ceil(a)` | 天井関数（切り上げ） |
| `floor(a)` | 床関数（切り下げ） |
| `greatest(a, b, ...)` | 最大値 |
| `least(a, b, ...)` | 最小値 |
| `log(a)` | 自然対数 |
| `sqrt(a)` | 平方根 |

**例**:
- `abs(-5)` → `5`
- `ceil(3.14)` → `4`

### 日時関数

時間的操作のための日時関数:

**時間単位**:
- `ms`: ミリ秒（上限: 1000）
- `s`: 秒（上限: 60）
- `m`: 分（上限: 60）
- `h`: 時間（上限: 24）
- `d`: 日
- `w`: 週
- `mo`: 月
- `q`: 四半期
- `y`: 年

**主要関数**:

| 関数 | 説明 |
|------|------|
| `bin(period)` | @timestampを時間期間に丸める |
| `datefloor(timestamp, period)` | タイムスタンプを期間に切り捨て |
| `dateceil(timestamp, period)` | タイムスタンプを期間に切り上げ |
| `fromMillis(number)` | ミリ秒をタイムスタンプに変換 |
| `toMillis(timestamp)` | タイムスタンプをミリ秒に変換 |
| `now()` | 現在のエポック秒を返す |

**例**:
- `bin(5m)`: 5分間のタイムバケットを作成
- `toMillis(@timestamp)`: タイムスタンプをエポックからのミリ秒に変換
- `filter toMillis(@timestamp) >= (now() * 1000 - 7200000)`: 過去2時間のイベントをフィルタ

### 文字列関数

文字列操作のための関数:

| 関数 | 説明 |
|------|------|
| `isempty(str)` | フィールドが存在しないか空の場合に1を返す |
| `isblank(str)` | フィールドが存在しない、空、または空白文字のみの場合に1を返す |
| `concat(str1, str2, ...)` | 文字列を連結 |
| `ltrim(str, [chars])` | 左側の文字を除去 |
| `rtrim(str, [chars])` | 右側の文字を除去 |
| `trim(str, [chars])` | 両端の文字を除去 |
| `strlen(str)` | Unicode文字数での文字列長を返す |
| `toupper(str)` | 大文字に変換 |
| `tolower(str)` | 小文字に変換 |
| `substr(str, start, [length])` | 部分文字列を返す |
| `replace(str, search, replace)` | すべてのインスタンスを置換 |
| `strcontains(str, search)` | 部分文字列が含まれている場合に1を返す |

**例**:
- `toupper(@message)`: メッセージを大文字に変換
- `substr(@message, 0, 10)`: 最初の10文字を取得
- `replace(@message, "ERROR", "WARN")`: すべてのERRORをWARNに置換

### JSON関数

JSONの解析と操作のための関数:

| 関数 | 説明 |
|------|------|
| `jsonParse(str)` | JSON文字列をマップ/リストに解析 |
| `jsonStringify(obj)` | マップ/リストをJSON文字列に変換 |

**例**:
- `jsonParse(@message) as json_msg`: JSONメッセージをオブジェクトに解析
- `fields jsonParse(@message) as json_message | stats count() by json_message.status_code`: JSONフィールド値でグループ化

**構造へのアクセス**:
- **マップ**: ドット記法を使用（`obj.field`または`obj.\`special.field\``）
- **リスト**: ブラケット記法を使用（`list[index]`）

### IPアドレス関数

IPアドレスの検証とサブネットチェックのための関数:

| 関数 | 説明 |
|------|------|
| `isValidIp(str)` | IPv4またはIPv6アドレスを検証 |
| `isValidIpV4(str)` | IPv4アドレスを検証 |
| `isValidIpV6(str)` | IPv6アドレスを検証 |
| `isIpInSubnet(ip, subnet)` | IPがCIDRサブネット内にあるかチェック |
| `isIpv4InSubnet(ip, subnet)` | IPv4がサブネット内にあるかチェック |
| `isIpv6InSubnet(ip, subnet)` | IPv6がサブネット内にあるかチェック |

**例**:
- `isValidIp(clientIp)`: クライアントIPアドレスを検証
- `isIpInSubnet(clientIp, "192.168.1.0/24")`: IPがプライベートサブネット内にあるかチェック

### 汎用関数

一般的なユーティリティ関数:

| 関数 | 説明 |
|------|------|
| `ispresent(field)` | フィールドが存在する場合にtrueを返す |
| `coalesce(field1, field2, ...)` | 最初の非null値を返す |

**例**:
- `ispresent(@requestId)`: リクエストIDフィールドが存在するかチェック
- `coalesce(@clientIp, @sourceIp, "unknown")`: 利用可能な最初のIPフィールドまたはデフォルトを返す

## 実用的な例

### 一般的なパターン

```
# 1時間あたりの例外数を検索
filter @message like /Exception/
| stats count(*) as exceptionCount by bin(1h)
| sort exceptionCount desc
```

```
# 上位エラーパターン
filter @message like /ERROR/
| pattern @message
| sort @sampleCount desc
| limit 10
```

```
# 遅いリクエストの分析
filter @duration > 1000
| stats avg(@duration), max(@duration), count() by bin(5m)
| sort @timestamp desc
```

```
# 時間別のユーザーアクティビティ
parse @message "user=* action=*" as user, action
| stats count() by user, bin(1h)
| sort @timestamp desc
```

```
# ネットワークトラフィック分析
stats sum(bytes) as totalBytes by srcAddr, dstAddr
| sort totalBytes desc
| limit 20
```

### 高度なクエリ

```
# 多段階集計
FIELDS strlen(@message) AS message_length
| STATS sum(message_length)/1024/1024 as logs_mb BY bin(5m)
| STATS max(logs_mb) AS peak_mb, avg(logs_mb) AS avg_mb
```

```
# JSONによる複雑なフィルタリング
fields jsonParse(@message) as json_msg
| filter json_msg.status_code >= 400
| stats count() by json_msg.endpoint, bin(10m)
```

```
# IPサブネット分析
filter isIpInSubnet(@clientIp, "10.0.0.0/8")
| stats count() as internal_requests by bin(1h)
| sort @timestamp desc
```

## ベストプラクティス

### パフォーマンスと費用の最適化

1. **必要なロググループのみを選択**
2. **可能な限り狭い時間範囲を使用**
3. **クエリの早い段階でフィルタリング**
4. **利用可能な場合はフィールドインデックスを使用**
5. **limitコマンドを使用して結果を制限**

### クエリの効率化

1. **フィールドの選択を最適化**
2. **早期フィルタリングの実装**
3. **複数のstatsコマンドの適切な使用**
4. **適切なソートと制限**

### セキュリティ

1. **機密情報の適切な処理**
2. **アクセス権限の管理**
3. **ログ出力時の情報漏洩の防止**

## トラブルシューティング

### よくある問題と解決策

**クエリタイムアウト**:
- 時間範囲を縮小
- より具体的なフィルタを追加
- limitコマンドを使用
- フィールド選択を最適化

**高コスト**:
- より狭い時間範囲を使用
- クエリの早い段階でフィルタリング
- より少ないロググループを選択
- 利用可能な場合はフィールドインデックスを使用

**空の結果**:
- フィールド名を確認（大文字小文字を区別）
- フィルタ条件を確認
- 時間範囲を確認
- ispresent()を使用してフィールドの存在を確認

### デバッグのヒント

1. **段階的にクエリを構築**
2. **小さな時間範囲でテスト**
3. **フィールドの存在を確認**
4. **適切なデータ型を使用**
5. **正規表現の構文を確認**

## 追加リソース

### 関連ドキュメント

- CloudWatch Logs サービス全般
- フィールドインデックスの作成と使用
- データ保護ポリシーの設定
- 視覚化とダッシュボードの作成

### 学習リソース

- CloudWatch Logs Insights チュートリアル
- サンプルクエリ集
- パフォーマンス最適化ガイド
- セキュリティベストプラクティス

このガイドを参照することで、CloudWatch Logs Insightsの全機能を活用し、効率的で正確なログ分析を実行できます。