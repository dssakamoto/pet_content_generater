"""Streamlitエントリポイント

LLM分析エージェントチャットボットのメインアプリケーションです。
"""
from __future__ import annotations

import hashlib
from typing import Any

import streamlit as st
from loguru import logger

from app.agent.agent import AnalysisAgent
from app.config import settings
from app.data.loader import load_file
from app.ui.components import render_connection_status, render_data_info, render_message
from app.ui.state import (
    add_assistant_message,
    add_user_message,
    clear_messages,
    get_chat_history,
    initialize_session_state,
)

# ページ設定（最初に呼び出す必要がある）
st.set_page_config(
    page_title="LLM分析エージェント",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _compute_file_hash(file_bytes: bytes) -> str:
    """ファイルのSHA256ハッシュを計算する"""
    return hashlib.sha256(file_bytes).hexdigest()


def _get_or_create_agent() -> AnalysisAgent:
    """エージェントインスタンスをキャッシュして返す"""
    if "agent" not in st.session_state:
        st.session_state.agent = AnalysisAgent(settings)
    return st.session_state.agent


def render_sidebar(agent: AnalysisAgent) -> None:
    """サイドバーを描画する

    Args:
        agent: AnalysisAgentインスタンス
    """
    st.sidebar.title("設定")

    # ---- Ollama接続確認 ----
    is_connected, available_models = agent.check_connection()
    render_connection_status(is_connected, available_models)

    st.sidebar.divider()

    # ---- モデル選択 ----
    st.sidebar.subheader("モデル選択")

    if available_models:
        # 利用可能なモデルをリスト表示
        model_options = available_models + ["手動入力..."]
        selected_option = st.sidebar.selectbox(
            "モデルを選択",
            options=model_options,
            index=0,
            key="model_selectbox",
        )

        if selected_option == "手動入力...":
            manual_model = st.sidebar.text_input(
                "モデル名を入力",
                value=st.session_state.selected_model,
                key="manual_model_input",
            )
            if manual_model:
                st.session_state.selected_model = manual_model
        else:
            st.session_state.selected_model = selected_option
    else:
        # 利用可能なモデルがない場合は手動入力のみ
        manual_model = st.sidebar.text_input(
            "モデル名を入力",
            value=st.session_state.selected_model,
            key="manual_model_input_fallback",
        )
        if manual_model:
            st.session_state.selected_model = manual_model

    st.sidebar.markdown(f"使用中: **{st.session_state.selected_model}**")

    st.sidebar.divider()

    # ---- ファイルアップロード ----
    st.sidebar.subheader("データアップロード")
    uploaded_file = st.sidebar.file_uploader(
        "CSV / JSON / Excel ファイルを選択",
        type=["csv", "json", "xlsx", "xls"],
        help="分析したいデータファイルをアップロードしてください",
    )

    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        file_hash = _compute_file_hash(file_bytes)

        # ファイルが変更された場合のみ再読み込み
        if st.session_state.file_hash != file_hash:
            with st.spinner(f"'{uploaded_file.name}' を読み込んでいます..."):
                try:
                    ctx = load_file(file_bytes, uploaded_file.name)
                    st.session_state.data_context = ctx
                    st.session_state.file_hash = file_hash
                    # データが変わったので会話履歴をリセット
                    clear_messages()
                    st.sidebar.success(f"'{uploaded_file.name}' を読み込みました")
                    logger.info(f"ファイル読み込み成功: {uploaded_file.name}")
                except Exception as e:
                    st.sidebar.error(f"ファイル読み込みエラー: {e}")
                    logger.error(f"ファイル読み込みエラー: {e}")

    # ---- データ情報表示 ----
    if st.session_state.data_context is not None:
        st.sidebar.divider()
        render_data_info(st.session_state.data_context)

    st.sidebar.divider()

    # ---- 会話履歴クリア ----
    if st.sidebar.button("会話履歴をクリア", use_container_width=True):
        clear_messages()
        st.rerun()


def render_main_area(agent: AnalysisAgent) -> None:
    """メインエリアを描画する

    Args:
        agent: AnalysisAgentインスタンス
    """
    # タイトル
    st.title("LLM分析エージェント")
    st.markdown("ローカルLLM（Ollama）を使ったデータ分析・可視化ツール")

    # データが未アップロードの場合はメッセージを表示
    if st.session_state.data_context is None:
        st.info(
            "サイドバーからCSV / JSON / Excelファイルをアップロードしてください。\n\n"
            "アップロード後、チャット欄に分析の指示を入力できます。\n\n"
            "例: 「売上の月別推移を折れ線グラフで表示して」"
        )

    st.divider()

    # ---- 会話履歴表示 ----
    for msg in st.session_state.messages:
        render_message(msg)

    # ---- チャット入力 ----
    user_input = st.chat_input(
        "データについて質問してください",
        disabled=(st.session_state.data_context is None),
    )

    if user_input:
        if st.session_state.data_context is None:
            st.warning("先にデータファイルをアップロードしてください。")
            return

        # ユーザーメッセージを表示・追加
        add_user_message(user_input)
        render_message({"role": "user", "content": user_input})

        # エージェント実行
        with st.spinner("分析中..."):
            try:
                history = get_chat_history()
                result = agent.run(
                    user_query=user_input,
                    data_ctx=st.session_state.data_context,
                    history=history[:-1],  # 直前のユーザーメッセージを除いた履歴
                    model=st.session_state.selected_model,
                )

                # アシスタントメッセージを追加
                add_assistant_message(
                    content=result.explanation,
                    figure_bytes=result.figure_bytes,
                    plotly_fig=result.plotly_fig,
                    code=result.code,
                    error=result.error,
                )

                # アシスタントメッセージを表示
                assistant_msg = st.session_state.messages[-1]
                render_message(assistant_msg)

                logger.info("エージェント実行完了")

            except Exception as e:
                error_msg = f"予期しないエラーが発生しました: {type(e).__name__}: {e}"
                logger.error(error_msg)
                add_assistant_message(
                    content="申し訳ありません。処理中にエラーが発生しました。",
                    error=error_msg,
                )
                st.error(error_msg)


def main() -> None:
    """メインアプリケーションのエントリポイント"""
    # session_state初期化
    initialize_session_state()

    # エージェント初期化（キャッシュ）
    agent = _get_or_create_agent()

    # サイドバー描画
    render_sidebar(agent)

    # メインエリア描画
    render_main_area(agent)


if __name__ == "__main__":
    main()
