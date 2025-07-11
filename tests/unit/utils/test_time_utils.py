"""時間ユーティリティ関数のユニットテスト.

このテストモジュールは、時間変換に関するユーティリティ関数をテストします。
AWS Strands Agentsでの使用を考慮し、様々な時間形式での正確な変換と
エラーハンドリングを検証します。
"""

import pytest
from cloudwatch_logs.utils.time_utils import convert_time_to_timestamp, epoch_ms_to_utc_iso


@pytest.mark.unit
@pytest.mark.aws_agents
class TestEpochMsToUtcIso:
    """epoch_ms_to_utc_iso関数のテストクラス."""

    def test_basic_conversion(self):
        """基本的なエポック時間からISO 8601への変換テスト."""
        # 2023-04-29T20:00:00.000Z
        epoch_ms = 1682798400000
        result = epoch_ms_to_utc_iso(epoch_ms)

        assert result == "2023-04-29T20:00:00+00:00"

    def test_zero_epoch(self):
        """エポック時間0（1970-01-01）の変換テスト."""
        epoch_ms = 0
        result = epoch_ms_to_utc_iso(epoch_ms)

        assert result == "1970-01-01T00:00:00+00:00"

    def test_millisecond_precision(self):
        """ミリ秒精度での変換テスト."""
        # 2023-04-29T20:00:00.123Z
        epoch_ms = 1682798400123
        result = epoch_ms_to_utc_iso(epoch_ms)

        # ミリ秒部分が含まれていることを確認
        assert result.startswith("2023-04-29T20:00:00")
        assert "+00:00" in result

    def test_future_date(self):
        """未来の日付の変換テスト."""
        # 2025-12-31T23:59:59.999Z
        epoch_ms = 1767225599999
        result = epoch_ms_to_utc_iso(epoch_ms)

        assert result.startswith("2025-12-31T23:59:59")
        assert "+00:00" in result

    def test_negative_epoch(self):
        """負のエポック時間（1970年以前）の変換テスト."""
        # 1969-12-31T23:00:00.000Z
        epoch_ms = -3600000  # 1時間前
        result = epoch_ms_to_utc_iso(epoch_ms)

        assert result.startswith("1969-12-31T23:00:00")
        assert "+00:00" in result

    def test_timezone_format(self):
        """タイムゾーン形式の確認テスト."""
        epoch_ms = 1682798400000
        result = epoch_ms_to_utc_iso(epoch_ms)

        # +00:00形式であることを確認（Zではない）
        assert result.endswith("+00:00")
        assert not result.endswith("Z")

    def test_aws_agents_usage_pattern(self):
        """AWS Strands Agents用の使用パターンテスト."""
        # CloudWatch APIから返される典型的なタイムスタンプ
        cloudwatch_timestamps = [
            1682798400000,  # ログ作成時間
            1682798460000,  # ログ更新時間
            1682798520000,  # 異常検知時間
        ]

        results = [epoch_ms_to_utc_iso(ts) for ts in cloudwatch_timestamps]

        # すべてが正しいISO 8601形式であることを確認
        for result in results:
            assert isinstance(result, str)
            assert "T" in result  # 日時セパレータ
            assert "+00:00" in result  # UTC タイムゾーン
            assert len(result) >= 19  # 最小限の長さ

    def test_large_epoch_values(self):
        """大きなエポック値の処理テスト."""
        # 非常に大きな値（遠い未来）
        large_epoch = 2147483647000  # 2038年問題の境界値 * 1000
        result = epoch_ms_to_utc_iso(large_epoch)

        assert isinstance(result, str)
        assert "+00:00" in result

    def test_type_consistency(self):
        """型の一貫性テスト."""
        epoch_ms = 1682798400000
        result = epoch_ms_to_utc_iso(epoch_ms)

        # 文字列であることを確認
        assert isinstance(result, str)

        # 空文字列でないことを確認
        assert len(result) > 0


@pytest.mark.unit
@pytest.mark.aws_agents
class TestConvertTimeToTimestamp:
    """convert_time_to_timestamp関数のテストクラス."""

    def test_basic_iso_conversion(self):
        """基本的なISO 8601からエポック時間への変換テスト."""
        iso_time = "2023-04-29T20:00:00+00:00"
        result = convert_time_to_timestamp(iso_time)

        assert result == 1682798400

    def test_z_suffix_conversion(self):
        """Z接尾辞付きISO 8601の変換テスト."""
        iso_time = "2023-04-29T20:00:00Z"
        result = convert_time_to_timestamp(iso_time)

        assert result == 1682798400

    def test_different_timezone_conversion(self):
        """異なるタイムゾーンでの変換テスト."""
        # JST (UTC+9)
        iso_time_jst = "2023-04-30T05:00:00+09:00"
        result = convert_time_to_timestamp(iso_time_jst)

        # UTC 2023-04-29T20:00:00と同じタイムスタンプになるはず
        assert result == 1682798400

    def test_microsecond_handling(self):
        """マイクロ秒を含むISO 8601の処理テスト."""
        iso_time = "2023-04-29T20:00:00.123456+00:00"
        result = convert_time_to_timestamp(iso_time)

        # 秒レベルでの比較（マイクロ秒は切り捨て）
        assert result == 1682798400

    def test_zero_timestamp(self):
        """エポック開始時刻の変換テスト."""
        iso_time = "1970-01-01T00:00:00+00:00"
        result = convert_time_to_timestamp(iso_time)

        assert result == 0

    def test_negative_timestamp(self):
        """1970年以前の時刻の変換テスト."""
        iso_time = "1969-12-31T23:00:00+00:00"
        result = convert_time_to_timestamp(iso_time)

        assert result == -3600  # -1時間

    def test_aws_agents_usage_pattern(self):
        """AWS Strands Agents用の使用パターンテスト."""
        # ユーザーから提供される典型的な時間範囲
        start_time = "2023-04-29T20:00:00+00:00"
        end_time = "2023-04-29T21:00:00+00:00"

        start_timestamp = convert_time_to_timestamp(start_time)
        end_timestamp = convert_time_to_timestamp(end_time)

        # 正しい時間間隔（1時間 = 3600秒）
        assert end_timestamp - start_timestamp == 3600

        # 両方とも正の整数
        assert isinstance(start_timestamp, int)
        assert isinstance(end_timestamp, int)
        assert start_timestamp > 0
        assert end_timestamp > 0

    def test_invalid_iso_format(self):
        """無効なISO 8601形式のエラーハンドリングテスト."""
        invalid_formats = [
            "2023/04/29T20:00:00",  # 日付区切りが/
            "April 29, 2023 8:00 PM",  # 自然言語形式
            "invalid-time-string",  # 完全に無効
            "2023-13-29T20:00:00",  # 無効な月
            "2023-04-32T20:00:00",  # 無効な日
        ]

        for invalid_time in invalid_formats:
            with pytest.raises(ValueError):
                convert_time_to_timestamp(invalid_time)

    def test_empty_string_error(self):
        """空文字列のエラーハンドリングテスト."""
        with pytest.raises(ValueError):
            convert_time_to_timestamp("")

    def test_none_value_error(self):
        """None値のエラーハンドリングテスト."""
        with pytest.raises(TypeError):
            convert_time_to_timestamp(None)


@pytest.mark.unit
@pytest.mark.aws_agents
class TestTimeUtilsIntegration:
    """時間ユーティリティ関数の統合テスト."""

    def test_round_trip_conversion(self):
        """往復変換の一貫性テスト."""
        # 元のエポック時間
        original_epoch_ms = 1682798400000

        # エポック → ISO → エポック
        iso_time = epoch_ms_to_utc_iso(original_epoch_ms)
        converted_epoch = convert_time_to_timestamp(iso_time)

        # 秒レベルでの一致を確認（ミリ秒は切り捨てられる）
        assert converted_epoch == original_epoch_ms // 1000

    def test_multiple_conversions_consistency(self):
        """複数回変換の一貫性テスト."""
        iso_time = "2023-04-29T20:00:00+00:00"

        # 同じ入力で複数回変換
        results = [convert_time_to_timestamp(iso_time) for _ in range(5)]

        # すべて同じ結果になることを確認
        assert all(result == results[0] for result in results)

    def test_timezone_normalization(self):
        """タイムゾーン正規化テスト."""
        # 同じ時刻を異なるタイムゾーンで表現
        utc_time = "2023-04-29T20:00:00+00:00"
        jst_time = "2023-04-30T05:00:00+09:00"  # UTC+9
        est_time = "2023-04-29T16:00:00-04:00"  # UTC-4

        utc_timestamp = convert_time_to_timestamp(utc_time)
        jst_timestamp = convert_time_to_timestamp(jst_time)
        est_timestamp = convert_time_to_timestamp(est_time)

        # すべて同じタイムスタンプになることを確認
        assert utc_timestamp == jst_timestamp == est_timestamp

    def test_aws_cloudwatch_api_simulation(self):
        """AWS CloudWatch API使用パターンのシミュレーション."""
        # ユーザーからの入力（ISO 8601形式）
        user_start_time = "2023-04-29T20:00:00+00:00"
        user_end_time = "2023-04-29T21:00:00+00:00"

        # AWS API用にタイムスタンプに変換
        api_start_time = convert_time_to_timestamp(user_start_time)
        api_end_time = convert_time_to_timestamp(user_end_time)

        # CloudWatch APIからの応答をシミュレート（エポックミリ秒）
        api_response_times = [
            api_start_time * 1000 + 15000,  # 15秒後
            api_start_time * 1000 + 30000,  # 30秒後
            api_start_time * 1000 + 45000,  # 45秒後
        ]

        # APIレスポンスをISO形式に変換
        response_iso_times = [
            epoch_ms_to_utc_iso(ts) for ts in api_response_times
        ]

        # すべて指定された時間範囲内であることを確認
        for iso_time in response_iso_times:
            timestamp = convert_time_to_timestamp(iso_time)
            assert api_start_time <= timestamp <= api_end_time

    def test_precision_handling(self):
        """精度処理のテスト."""
        # ミリ秒精度のエポック時間
        epoch_ms_with_precision = 1682798400123

        # ISO変換
        iso_time = epoch_ms_to_utc_iso(epoch_ms_with_precision)

        # 秒レベルでのタイムスタンプに戻す
        timestamp_seconds = convert_time_to_timestamp(iso_time)

        # 秒レベルでは元の値と一致することを確認
        expected_seconds = epoch_ms_with_precision // 1000
        assert timestamp_seconds == expected_seconds

    def test_edge_cases(self):
        """エッジケースのテスト."""
        edge_cases = [
            (0, "1970-01-01T00:00:00+00:00"),  # エポック開始
            (86400000, "1970-01-02T00:00:00+00:00"),  # 1日後
        ]

        for epoch_ms, expected_iso_start in edge_cases:
            # エポック → ISO 変換
            iso_result = epoch_ms_to_utc_iso(epoch_ms)
            assert iso_result.startswith(expected_iso_start.split('+')[0])

            # ISO → エポック 変換
            timestamp_result = convert_time_to_timestamp(iso_result)
            assert timestamp_result == epoch_ms // 1000
