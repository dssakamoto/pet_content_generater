"""データ読み込みモジュール

CSV/JSON/Excelファイルを読み込み、DataContextを生成します。
"""
from __future__ import annotations

import io
import json
from typing import BinaryIO

import numpy as np
import pandas as pd
from loguru import logger

from app.data.context import DataContext


def _build_schema_summary(df: pd.DataFrame, max_chars: int = 1500) -> str:
    """DataFrameのスキーマサマリーを生成する

    カラム名・型・null率・基本統計を含む文字列を返す。
    max_chars以内に収める。
    """
    lines: list[str] = []

    lines.append(f"行数: {len(df)}, 列数: {len(df.columns)}")
    lines.append("")
    lines.append("【カラム情報】")

    for col in df.columns:
        col_dtype = str(df[col].dtype)
        null_rate = df[col].isna().mean() * 100
        col_info = f"  {col} ({col_dtype}) | null率: {null_rate:.1f}%"

        # 数値型の場合は基本統計を追加
        if pd.api.types.is_numeric_dtype(df[col]):
            try:
                desc = df[col].describe()
                col_info += (
                    f" | min={desc['min']:.2f}, max={desc['max']:.2f},"
                    f" mean={desc['mean']:.2f}, std={desc['std']:.2f}"
                )
            except Exception:
                pass
        # 文字列型の場合はユニーク数を追加
        else:
            try:
                unique_count = df[col].nunique()
                col_info += f" | ユニーク数: {unique_count}"
                if unique_count <= 10:
                    unique_vals = df[col].dropna().unique().tolist()
                    col_info += f" | 値: {unique_vals}"
            except Exception:
                pass

        lines.append(col_info)

    summary = "\n".join(lines)

    # 文字数制限
    if len(summary) > max_chars:
        summary = summary[:max_chars] + "\n...(省略)"

    return summary


def _normalize_json(data: object) -> pd.DataFrame:
    """JSONデータをDataFrameに変換する（フラット・ネスト両対応）"""
    if isinstance(data, list):
        return pd.json_normalize(data)
    elif isinstance(data, dict):
        # dictの場合はリストに変換
        return pd.json_normalize([data])
    else:
        raise ValueError(f"サポートされていないJSONフォーマット: {type(data)}")


def load_csv(file_content: bytes, filename: str) -> DataContext:
    """CSVファイルを読み込みDataContextを返す

    utf-8 → shift_jis の順でエンコーディングを試行する。
    """
    df: pd.DataFrame | None = None
    encodings = ["utf-8", "utf-8-sig", "shift_jis", "cp932"]

    for encoding in encodings:
        try:
            df = pd.read_csv(io.BytesIO(file_content), encoding=encoding)
            logger.info(f"CSVファイル '{filename}' を {encoding} で読み込み成功")
            break
        except (UnicodeDecodeError, Exception) as e:
            logger.debug(f"エンコーディング {encoding} で失敗: {e}")
            continue

    if df is None:
        raise ValueError(f"CSVファイル '{filename}' の読み込みに失敗しました。サポートされているエンコーディングを確認してください。")

    schema_summary = _build_schema_summary(df)
    sample_rows = df.head(5).to_string()

    return DataContext(
        df=df,
        filename=filename,
        schema_summary=schema_summary,
        sample_rows=sample_rows,
    )


def load_json(file_content: bytes, filename: str) -> DataContext:
    """JSONファイルを読み込みDataContextを返す（フラット・ネスト両対応）"""
    try:
        data = json.loads(file_content.decode("utf-8"))
    except UnicodeDecodeError:
        try:
            data = json.loads(file_content.decode("shift_jis"))
        except Exception as e:
            raise ValueError(f"JSONファイル '{filename}' のデコードに失敗しました: {e}")
    except json.JSONDecodeError as e:
        raise ValueError(f"JSONファイル '{filename}' のパースに失敗しました: {e}")

    try:
        df = _normalize_json(data)
        logger.info(f"JSONファイル '{filename}' の読み込み成功")
    except Exception as e:
        raise ValueError(f"JSONファイル '{filename}' のDataFrame変換に失敗しました: {e}")

    schema_summary = _build_schema_summary(df)
    sample_rows = df.head(5).to_string()

    return DataContext(
        df=df,
        filename=filename,
        schema_summary=schema_summary,
        sample_rows=sample_rows,
    )


def load_excel(file_content: bytes, filename: str) -> DataContext:
    """Excelファイルを読み込みDataContextを返す（openpyxl使用）"""
    try:
        df = pd.read_excel(io.BytesIO(file_content), engine="openpyxl")
        logger.info(f"Excelファイル '{filename}' の読み込み成功")
    except Exception as e:
        raise ValueError(f"Excelファイル '{filename}' の読み込みに失敗しました: {e}")

    schema_summary = _build_schema_summary(df)
    sample_rows = df.head(5).to_string()

    return DataContext(
        df=df,
        filename=filename,
        schema_summary=schema_summary,
        sample_rows=sample_rows,
    )


def load_file(file_content: bytes, filename: str) -> DataContext:
    """ファイル拡張子に基づいて適切なローダーを呼び出す"""
    filename_lower = filename.lower()

    try:
        if filename_lower.endswith(".csv"):
            return load_csv(file_content, filename)
        elif filename_lower.endswith(".json"):
            return load_json(file_content, filename)
        elif filename_lower.endswith((".xlsx", ".xls")):
            return load_excel(file_content, filename)
        else:
            raise ValueError(
                f"サポートされていないファイル形式です: {filename}"
                " (CSV、JSON、Excelのみ対応)"
            )
    except Exception as e:
        logger.error(f"ファイル '{filename}' の読み込みエラー: {e}")
        raise
