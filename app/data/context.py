"""データコンテキスト定義モジュール"""
from dataclasses import dataclass

import pandas as pd


@dataclass
class DataContext:
    """アップロードされたデータのコンテキスト情報を保持するクラス"""

    df: pd.DataFrame
    filename: str
    schema_summary: str
    sample_rows: str
