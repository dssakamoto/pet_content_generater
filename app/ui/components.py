"""UIコンポーネントモジュール

Streamlitのチャットメッセージやデータ情報を描画するコンポーネントを提供します。
"""
from __future__ import annotations

from typing import Any

import streamlit as st
from loguru import logger

from app.data.context import DataContext


def render_message(msg: dict[str, Any]) -> None:
    """チャットメッセージを描画する

    user: st.chat_message("user") で表示
    assistant: テキスト → 図 → コードexpander の順で表示

    Args:
        msg: メッセージ辞書 {role, content, figure_bytes, plotly_fig, code, error}
    """
    role = msg.get("role", "user")
    content = msg.get("content", "")

    if role == "user":
        with st.chat_message("user"):
            st.markdown(content)

    elif role == "assistant":
        with st.chat_message("assistant"):
            # 1. テキスト（説明文）を表示
            if content:
                st.markdown(content)

            # 2. エラーがあれば表示
            error = msg.get("error")
            if error:
                st.error(f"エラー: {error}")

            # 3. matplotlibの図を表示
            figure_bytes = msg.get("figure_bytes")
            if figure_bytes:
                try:
                    st.image(figure_bytes, use_container_width=True)
                except Exception as e:
                    logger.error(f"matplotlib図の表示に失敗: {e}")
                    st.warning("図の表示に失敗しました")

            # 4. plotlyの図を表示
            plotly_fig = msg.get("plotly_fig")
            if plotly_fig is not None:
                try:
                    st.plotly_chart(plotly_fig, use_container_width=True)
                except Exception as e:
                    logger.error(f"plotly図の表示に失敗: {e}")
                    st.warning("インタラクティブグラフの表示に失敗しました")

            # 5. 生成コードをexpanderで表示
            code = msg.get("code")
            if code:
                with st.expander("生成されたコードを表示", expanded=False):
                    st.code(code, language="python")

    else:
        # 未知のロールはそのまま表示
        with st.chat_message(role):
            st.markdown(content)


def render_data_info(ctx: DataContext) -> None:
    """サイドバーにデータ情報を表示する

    Args:
        ctx: DataContextインスタンス
    """
    st.sidebar.subheader("データ情報")

    # ファイル名
    st.sidebar.markdown(f"**ファイル名:** {ctx.filename}")

    # データ形状
    rows, cols = ctx.df.shape
    st.sidebar.markdown(f"**行数:** {rows:,} | **列数:** {cols}")

    # スキーマサマリー（expanderに格納）
    with st.sidebar.expander("スキーマ詳細", expanded=False):
        st.text(ctx.schema_summary)

    # サンプルデータプレビュー
    with st.sidebar.expander("サンプルデータ（先頭5行）", expanded=False):
        st.dataframe(ctx.df.head(5), use_container_width=True)


def render_connection_status(is_connected: bool, models: list[str]) -> None:
    """サイドバーにOllama接続状態を表示する

    Args:
        is_connected: 接続成功フラグ
        models: 利用可能なモデル名リスト
    """
    st.sidebar.subheader("Ollama接続状態")

    if is_connected:
        st.sidebar.success("接続中")
        if models:
            st.sidebar.markdown(f"利用可能なモデル数: **{len(models)}**")
        else:
            st.sidebar.warning("モデルが見つかりません。`ollama pull llama3.2` を実行してください。")
    else:
        st.sidebar.error("接続失敗")
        st.sidebar.markdown(
            "Ollamaが起動していることを確認してください。\n"
            "起動コマンド: `ollama serve`"
        )
