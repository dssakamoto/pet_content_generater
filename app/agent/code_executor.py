"""生成コードの安全な実行エンジン

静的チェックと制限されたexec環境でLLM生成コードを安全に実行します。
"""
from __future__ import annotations

import io
import sys
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from contextlib import redirect_stdout
from typing import Any

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
from loguru import logger

matplotlib.use("Agg")  # GUIバックエンドを無効化

# 静的安全チェックで禁止するパターン
FORBIDDEN_PATTERNS: list[str] = [
    "import ",
    " import",
    "open(",
    "subprocess",
    "os.",
    "eval(",
    "exec(",
    "__",
]


class CodeSafetyError(Exception):
    """コードの安全チェックに失敗した場合の例外"""
    pass


def check_code_safety(code: str) -> None:
    """コードの静的安全チェックを実施する

    Args:
        code: チェック対象のPythonコード文字列

    Raises:
        CodeSafetyError: 禁止パターンが検出された場合
    """
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in code:
            raise CodeSafetyError(
                f"セキュリティポリシー違反: '{pattern}' の使用は禁止されています"
            )


def _build_safe_globals(df: pd.DataFrame) -> dict[str, Any]:
    """制限されたexec環境のグローバル変数を構築する"""
    # 許可するbuiltins
    allowed_builtins = {
        "print": print,
        "len": len,
        "range": range,
        "enumerate": enumerate,
        "zip": zip,
        "list": list,
        "dict": dict,
        "set": set,
        "tuple": tuple,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "sorted": sorted,
        "reversed": reversed,
        "map": map,
        "filter": filter,
        "isinstance": isinstance,
        "type": type,
        "hasattr": hasattr,
        "getattr": getattr,
        "format": format,
        "repr": repr,
        "None": None,
        "True": True,
        "False": False,
    }

    safe_globals: dict[str, Any] = {
        "__builtins__": allowed_builtins,
        "df": df.copy(),
        "pd": pd,
        "np": np,
        "plt": plt,
        "px": px,
    }

    return safe_globals


def _execute_code_internal(
    code: str,
    df: pd.DataFrame,
) -> tuple[bytes | None, object | None, str]:
    """コードを制限された環境で実行する（内部関数）

    Args:
        code: 実行するPythonコード
        df: 分析対象のDataFrame

    Returns:
        (figure_bytes, plotly_fig, stdout_str) のタプル
    """
    safe_globals = _build_safe_globals(df)

    # matplotlibの出力をBytesIOにリダイレクト
    figure_bytes: bytes | None = None
    plotly_fig: object | None = None

    # plt.savefigをオーバーライドしてBytesIOにキャプチャ
    fig_buffer = io.BytesIO()

    original_savefig = plt.savefig

    def patched_savefig(*args: Any, **kwargs: Any) -> None:
        """plt.savefigをBytesIOにリダイレクトするパッチ"""
        plt.savefig(fig_buffer, format="png", bbox_inches="tight")

    # plt.savefigをパッチ
    safe_globals["plt"] = type("MockPlt", (), {
        attr: getattr(plt, attr) for attr in dir(plt) if not attr.startswith("__")
    })()
    safe_globals["plt"].savefig = patched_savefig

    # stdoutキャプチャ
    stdout_buffer = io.StringIO()

    with redirect_stdout(stdout_buffer):
        exec(code, safe_globals)  # noqa: S102

    # matplotlib figureのキャプチャ
    fig_buffer.seek(0)
    content = fig_buffer.read()
    if content:
        figure_bytes = content
    else:
        # savefigが呼ばれなかった場合、現在のfigureを保存
        current_fig = plt.gcf()
        if current_fig.get_axes():
            buf = io.BytesIO()
            current_fig.savefig(buf, format="png", bbox_inches="tight")
            buf.seek(0)
            figure_bytes = buf.read() or None

    # plotly figureのキャプチャ
    if "fig" in safe_globals:
        candidate = safe_globals["fig"]
        # plotly figureかどうかチェック
        if hasattr(candidate, "to_html") and hasattr(candidate, "update_layout"):
            plotly_fig = candidate

    # matplotlibをリセット
    plt.close("all")

    stdout_str = stdout_buffer.getvalue()
    return figure_bytes, plotly_fig, stdout_str


def execute_code(
    code: str,
    df: pd.DataFrame,
    timeout: int = 30,
) -> tuple[bytes | None, object | None, str, str | None]:
    """生成コードを安全に実行する

    Args:
        code: 実行するPythonコード文字列
        df: 分析対象のDataFrame
        timeout: タイムアウト秒数

    Returns:
        (figure_bytes, plotly_fig, stdout, error) のタプル
        - figure_bytes: matplotlibの図のPNGバイト列（なければNone）
        - plotly_fig: plotlyのFigureオブジェクト（なければNone）
        - stdout: 標準出力の文字列
        - error: エラーメッセージ（なければNone）
    """
    # 静的安全チェック
    try:
        check_code_safety(code)
    except CodeSafetyError as e:
        logger.warning(f"コード安全チェック失敗: {e}")
        return None, None, "", str(e)

    # ThreadPoolExecutorでタイムアウト実装
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_execute_code_internal, code, df)
        try:
            figure_bytes, plotly_fig, stdout_str = future.result(timeout=timeout)
            logger.debug(f"コード実行成功 | stdout長: {len(stdout_str)}")
            return figure_bytes, plotly_fig, stdout_str, None
        except FuturesTimeoutError:
            error_msg = f"コードの実行がタイムアウトしました（{timeout}秒）"
            logger.error(error_msg)
            return None, None, "", error_msg
        except Exception as e:
            error_msg = f"コード実行エラー: {type(e).__name__}: {e}"
            logger.error(error_msg)
            return None, None, "", error_msg
