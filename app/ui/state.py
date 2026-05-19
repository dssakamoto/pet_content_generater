"""セッション状態管理モジュール

Streamlitのsession_stateを初期化・管理するためのモジュールです。
"""
from __future__ import annotations

from typing import Any

import streamlit as st
from loguru import logger


def initialize_session_state() -> None:
    """session_stateの初期化を行う

    未初期化のキーに対してデフォルト値を設定します。
    """
    # チャットメッセージ履歴
    # 各要素: {role, content, figure_bytes, plotly_fig, code, error}
    if "messages" not in st.session_state:
        st.session_state.messages: list[dict[str, Any]] = []
        logger.debug("session_state.messages を初期化しました")

    # アップロードされたデータのコンテキスト
    if "data_context" not in st.session_state:
        st.session_state.data_context = None
        logger.debug("session_state.data_context を初期化しました")

    # 選択中のモデル名
    if "selected_model" not in st.session_state:
        st.session_state.selected_model: str = "llama3.2"
        logger.debug("session_state.selected_model を初期化しました")

    # アップロードファイルのハッシュ（変更検知用）
    if "file_hash" not in st.session_state:
        st.session_state.file_hash: str | None = None
        logger.debug("session_state.file_hash を初期化しました")


def clear_messages() -> None:
    """会話履歴をクリアする"""
    st.session_state.messages = []
    logger.info("会話履歴をクリアしました")


def add_user_message(content: str) -> None:
    """ユーザーメッセージを履歴に追加する

    Args:
        content: メッセージ内容
    """
    st.session_state.messages.append({
        "role": "user",
        "content": content,
        "figure_bytes": None,
        "plotly_fig": None,
        "code": None,
        "error": None,
    })


def add_assistant_message(
    content: str,
    figure_bytes: bytes | None = None,
    plotly_fig: object | None = None,
    code: str | None = None,
    error: str | None = None,
) -> None:
    """アシスタントメッセージを履歴に追加する

    Args:
        content: メッセージ内容（説明文）
        figure_bytes: matplotlibの図のPNGバイト列
        plotly_fig: plotlyのFigureオブジェクト
        code: 生成されたPythonコード
        error: エラーメッセージ
    """
    st.session_state.messages.append({
        "role": "assistant",
        "content": content,
        "figure_bytes": figure_bytes,
        "plotly_fig": plotly_fig,
        "code": code,
        "error": error,
    })


def get_chat_history() -> list[dict[str, str]]:
    """LLMに渡す形式の会話履歴を返す

    Returns:
        {role, content} のリスト
    """
    return [
        {"role": msg["role"], "content": msg["content"]}
        for msg in st.session_state.messages
    ]
