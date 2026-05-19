"""データローダーのテストモジュール"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from app.data.context import DataContext
from app.data.loader import load_csv, load_excel, load_file, load_json

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestLoadCsv:
    """CSVローダーのテスト"""

    def test_load_sample_csv(self) -> None:
        """サンプルCSVファイルの読み込みテスト"""
        csv_path = FIXTURES_DIR / "sample.csv"
        file_bytes = csv_path.read_bytes()

        ctx = load_csv(file_bytes, "sample.csv")

        assert isinstance(ctx, DataContext)
        assert ctx.filename == "sample.csv"
        assert isinstance(ctx.df, pd.DataFrame)
        assert len(ctx.df) >= 10
        assert "date" in ctx.df.columns
        assert "product" in ctx.df.columns
        assert "sales" in ctx.df.columns
        assert "quantity" in ctx.df.columns
        assert "region" in ctx.df.columns

    def test_csv_schema_summary(self) -> None:
        """CSVのスキーマサマリーが生成されることのテスト"""
        csv_path = FIXTURES_DIR / "sample.csv"
        file_bytes = csv_path.read_bytes()

        ctx = load_csv(file_bytes, "sample.csv")

        assert ctx.schema_summary != ""
        assert len(ctx.schema_summary) <= 1500
        assert "sales" in ctx.schema_summary

    def test_csv_sample_rows(self) -> None:
        """CSVのサンプル行が生成されることのテスト"""
        csv_path = FIXTURES_DIR / "sample.csv"
        file_bytes = csv_path.read_bytes()

        ctx = load_csv(file_bytes, "sample.csv")

        assert ctx.sample_rows != ""
        # head(5)の文字列なので「商品A」が含まれるはず
        assert "商品A" in ctx.sample_rows

    def test_load_file_with_csv(self) -> None:
        """load_file()がCSVを正しく処理するテスト"""
        csv_path = FIXTURES_DIR / "sample.csv"
        file_bytes = csv_path.read_bytes()

        ctx = load_file(file_bytes, "sample.csv")

        assert isinstance(ctx, DataContext)
        assert ctx.filename == "sample.csv"

    def test_load_file_unsupported_format(self) -> None:
        """サポートされていないファイル形式のテスト"""
        with pytest.raises(ValueError, match="サポートされていないファイル形式"):
            load_file(b"some content", "test.txt")


class TestLoadJson:
    """JSONローダーのテスト"""

    def test_load_sample_json(self) -> None:
        """サンプルJSONファイルの読み込みテスト"""
        json_path = FIXTURES_DIR / "sample.json"
        file_bytes = json_path.read_bytes()

        ctx = load_json(file_bytes, "sample.json")

        assert isinstance(ctx, DataContext)
        assert ctx.filename == "sample.json"
        assert isinstance(ctx.df, pd.DataFrame)
        assert len(ctx.df) >= 3
        assert "month" in ctx.df.columns
        assert "category" in ctx.df.columns
        assert "revenue" in ctx.df.columns
        assert "cost" in ctx.df.columns

    def test_json_schema_summary(self) -> None:
        """JSONのスキーマサマリーが生成されることのテスト"""
        json_path = FIXTURES_DIR / "sample.json"
        file_bytes = json_path.read_bytes()

        ctx = load_json(file_bytes, "sample.json")

        assert ctx.schema_summary != ""
        assert "revenue" in ctx.schema_summary

    def test_load_nested_json(self) -> None:
        """ネストしたJSONの読み込みテスト"""
        nested_data = [
            {"id": 1, "info": {"name": "テスト", "value": 100}},
            {"id": 2, "info": {"name": "サンプル", "value": 200}},
        ]
        json_bytes = json.dumps(nested_data, ensure_ascii=False).encode("utf-8")

        ctx = load_json(json_bytes, "nested.json")

        assert isinstance(ctx.df, pd.DataFrame)
        # json_normalizeによりネストが展開されているはず
        assert "id" in ctx.df.columns

    def test_load_file_with_json(self) -> None:
        """load_file()がJSONを正しく処理するテスト"""
        json_path = FIXTURES_DIR / "sample.json"
        file_bytes = json_path.read_bytes()

        ctx = load_file(file_bytes, "sample.json")

        assert isinstance(ctx, DataContext)
        assert ctx.filename == "sample.json"

    def test_invalid_json(self) -> None:
        """不正なJSONのエラー処理テスト"""
        with pytest.raises(ValueError, match="パースに失敗"):
            load_json(b"not valid json {{{", "invalid.json")


class TestSchemaBuilder:
    """スキーマサマリー生成のテスト"""

    def test_schema_summary_length_limit(self) -> None:
        """スキーマサマリーが1500文字以内に収まることのテスト"""
        # 多くのカラムを持つDataFrameを生成
        import numpy as np

        large_df = pd.DataFrame({
            f"column_{i}": range(100)
            for i in range(50)
        })
        large_df_bytes = large_df.to_csv(index=False).encode("utf-8")
        ctx = load_csv(large_df_bytes, "large.csv")

        assert len(ctx.schema_summary) <= 1500

    def test_schema_includes_null_rate(self) -> None:
        """スキーマサマリーにnull率が含まれることのテスト"""
        import io
        import numpy as np

        df_with_nulls = pd.DataFrame({
            "a": [1, None, 3, None, 5],
            "b": ["x", "y", None, "w", "v"],
        })
        csv_bytes = df_with_nulls.to_csv(index=False).encode("utf-8")
        ctx = load_csv(csv_bytes, "nulls.csv")

        assert "null率" in ctx.schema_summary
