"""生成コードの安全な実行エンジン

静的チェックと制限されたexec環境でLLM生成コードを安全に実行します。
"""
from __future__ import annotations

import io
import re
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

# 静的安全チェック: 正規表現で禁止パターンを検出する
# トークン境界を考慮した厳密なパターンを使用
_FORBIDDEN_REGEXES: list[tuple[str, re.Pattern[str]]] = [
    # import文: 行頭や空白・セミコロン後のimport、fromXimportも検出
    ("import文", re.compile(r"(^|[\s;])import\s", re.MULTILINE)),
    ("from import文", re.compile(r"(^|[\s;])from\s+\S+\s+import\s", re.MULTILINE)),
    # ファイル操作 (open / pathlib)
    ("open()", re.compile(r"\bopen\s*\(")),
    # サブプロセス
    ("subprocess", re.compile(r"\bsubprocess\b")),
    # os/sys モジュールアクセス
    ("os.", re.compile(r"\bos\s*\.")),
    ("sys.", re.compile(r"\bsys\s*\.")),
    # 危険な組み込み関数
    ("eval()", re.compile(r"\beval\s*\(")),
    ("exec()", re.compile(r"\bexec\s*\(")),
    ("compile()", re.compile(r"\bcompile\s*\(")),
    ("globals()", re.compile(r"\bglobals\s*\(")),
    ("locals()", re.compile(r"\blocals\s*\(")),
    ("vars()", re.compile(r"\bvars\s*\(")),
    ("dir()", re.compile(r"\bdir\s*\(")),
    # breakpoint / input はbuiltinsにないが静的にも明示ブロック
    ("breakpoint()", re.compile(r"\bbreakpoint\s*\(")),
    ("input()", re.compile(r"\binput\s*\(")),
    # dunder属性アクセス（__class__, __mro__, __builtins__ 等）
    ("dunder属性", re.compile(r"__\w+")),
    # 文字列結合によるimport迂回対策
    ("__import__", re.compile(r"__import__")),
    # pandas/numpyを経由したファイルI/O: 読み取り
    ("pd.read_*(ファイル読み取り)", re.compile(
        r"\bpd\s*\.\s*read_(?:csv|excel|json|parquet|feather|hdf|orc|sas|spss|stata|table|fwf|clipboard)\s*\("
    )),
    ("pd.ExcelFile()", re.compile(r"\bpd\s*\.\s*ExcelFile\s*\(")),
    ("np.load()", re.compile(r"\bnp\s*\.\s*(?:load|loadtxt|fromfile|genfromtxt|memmap)\s*\(")),
    # pandas/numpy/plotlyを経由したファイルI/O: 書き込み
    ("df.to_csv/excel等(ファイル書き込み)", re.compile(
        r"\.\s*to_(?:csv|excel|json|parquet|feather|hdf|orc|stata|pickle|sql)\s*\("
    )),
    ("np.save/savetxt()", re.compile(r"\bnp\s*\.\s*(?:save|savez|savetxt|tofile)\s*\(")),
    ("fig.write_image/html()", re.compile(r"\bfig\s*\.\s*write_(?:image|html|json)\s*\(")),
    ("plt.imsave()", re.compile(r"\bplt\s*\.\s*(?:imsave|rcParams)\s*[\[\(]")),
]


class CodeSafetyError(Exception):
    """コードの安全チェックに失敗した場合の例外"""
    pass


def check_code_safety(code: str) -> None:
    """コードの静的安全チェックを実施する

    正規表現ベースの厳密なパターンマッチングで禁止構文を検出する。
    トークン境界を考慮するため、単純な部分文字列マッチより迂回が困難。

    Args:
        code: チェック対象のPythonコード文字列

    Raises:
        CodeSafetyError: 禁止パターンが検出された場合
    """
    for label, pattern in _FORBIDDEN_REGEXES:
        if pattern.search(code):
            raise CodeSafetyError(
                f"セキュリティポリシー違反: '{label}' の使用は禁止されています"
            )


def _build_safe_globals(df: pd.DataFrame) -> dict[str, Any]:
    """制限されたexec環境のグローバル変数を構築する

    allowed_builtinsには、モジュール探索や動的属性アクセスに悪用できる
    getattr / vars / dir / compile / globals / locals 等を含めない。
    """
    # 許可するbuiltins（危険な動的アクセス関数は除外）
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
        "format": format,
        "repr": repr,
        "None": None,
        "True": True,
        "False": False,
        # type/hasattr は静的チェックで __dunder__ アクセスを禁止しているため許可
        "type": type,
        "hasattr": hasattr,
        # getattr は意図的に除外: getattr(pd, 'io') 等でモジュール探索が可能なため
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

    # plt.savefigをモンキーパッチしてBytesIOにキャプチャ
    # MockPltオブジェクトではなく実際のpltモジュールを使い、savefigのみ差し替える。
    # これによりplt.figure()等のmatplotlib内部状態管理が正常に動作する。
    fig_buffer = io.BytesIO()
    _original_savefig = plt.savefig

    def patched_savefig(*args: Any, **kwargs: Any) -> None:
        """plt.savefigをBytesIOにリダイレクトするパッチ

        ユーザーコードが plt.savefig("output.png") を呼んだとき、
        実際のファイルではなく fig_buffer に PNG バイト列を書き込む。
        """
        plt.gcf().savefig(fig_buffer, format="png", bbox_inches="tight")

    plt.savefig = patched_savefig  # type: ignore[assignment]
    # safe_globalsのpltは実際のpltモジュールを参照させる（MockPltは不要）
    safe_globals["plt"] = plt

    # stdoutキャプチャ
    stdout_buffer = io.StringIO()

    try:
        with redirect_stdout(stdout_buffer):
            exec(code, safe_globals)  # noqa: S102
    finally:
        # 必ずplt.savefigを元に戻す
        plt.savefig = _original_savefig  # type: ignore[assignment]

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
