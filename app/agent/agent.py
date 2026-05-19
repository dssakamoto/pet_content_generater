"""メインエージェントモジュール

Ollamaを使用してデータ分析コードを生成・実行するエージェントクラスを提供します。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import ollama
from loguru import logger

from app.agent.code_executor import execute_code
from app.agent.prompts import build_system_prompt
from app.config import Settings
from app.data.context import DataContext


@dataclass
class AgentResult:
    """エージェントの実行結果を保持するデータクラス"""

    explanation: str
    code: str | None
    figure_bytes: bytes | None
    plotly_fig: object | None
    error: str | None
    raw_response: str


# コードブロック抽出用の正規表現パターン
CODE_BLOCK_PATTERN = re.compile(r"```python\s*(.*?)\s*```", re.DOTALL)


def _extract_code_blocks(text: str) -> list[str]:
    """マークダウンテキストからPythonコードブロックを抽出する

    Args:
        text: マークダウン形式のテキスト

    Returns:
        抽出されたコードブロックのリスト
    """
    return CODE_BLOCK_PATTERN.findall(text)


def _remove_code_blocks(text: str) -> str:
    """テキストからコードブロックを除去して説明文のみ返す"""
    return CODE_BLOCK_PATTERN.sub("", text).strip()


class AnalysisAgent:
    """ローカルLLMを使ったデータ分析エージェントクラス"""

    def __init__(self, settings: Settings) -> None:
        """エージェントを初期化する

        Args:
            settings: アプリケーション設定
        """
        self.settings = settings
        self.client = ollama.Client(host=settings.ollama_base_url)
        logger.info(f"AnalysisAgent初期化 | base_url={settings.ollama_base_url}")

    def check_connection(self) -> tuple[bool, list[str]]:
        """Ollamaへの接続確認と利用可能モデル一覧を返す

        Returns:
            (接続成功フラグ, モデル名リスト) のタプル
        """
        try:
            response = self.client.list()
            # ollamaライブラリのレスポンス形式に対応
            if hasattr(response, "models"):
                models = [m.model for m in response.models if hasattr(m, "model")]
            elif isinstance(response, dict) and "models" in response:
                models = [m.get("name", m.get("model", "")) for m in response["models"]]
            else:
                models = []
            logger.info(f"Ollama接続確認成功 | モデル数: {len(models)}")
            return True, models
        except Exception as e:
            logger.error(f"Ollama接続確認失敗: {e}")
            return False, []

    def run(
        self,
        user_query: str,
        data_ctx: DataContext,
        history: list[dict[str, str]],
        model: str | None = None,
    ) -> AgentResult:
        """エージェントのメイン実行メソッド

        1. システムプロンプト生成
        2. Ollama chat呼び出し
        3. レスポンスから```python...```ブロック抽出
        4. 安全チェック → 失敗時は再試行（max 3回）
        5. コード実行
        6. AgentResult返却

        Args:
            user_query: ユーザーの質問文字列
            data_ctx: データコンテキスト
            history: 会話履歴（{role, content}のリスト）
            model: 使用するモデル名（Noneの場合はデフォルト設定を使用）

        Returns:
            AgentResult インスタンス
        """
        model_name = model or self.settings.default_model

        # システムプロンプト生成
        system_prompt = build_system_prompt(
            schema_summary=data_ctx.schema_summary,
            sample_rows=data_ctx.sample_rows,
        )

        # 会話履歴を構築
        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt}
        ]
        # 過去の会話履歴を追加（最新20件に制限）
        for msg in history[-20:]:
            if msg.get("role") in ("user", "assistant"):
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"],
                })
        # 現在のユーザー質問を追加
        messages.append({"role": "user", "content": user_query})

        raw_response = ""
        last_error: str | None = None

        # リトライループ（最大3回）
        for attempt in range(1, self.settings.max_retries + 1):
            try:
                logger.info(f"Ollama呼び出し開始 | model={model_name}, attempt={attempt}")
                response = self.client.chat(
                    model=model_name,
                    messages=messages,
                )

                # レスポンスのテキストを取得
                if hasattr(response, "message") and hasattr(response.message, "content"):
                    raw_response = response.message.content
                elif isinstance(response, dict):
                    raw_response = response.get("message", {}).get("content", "")
                else:
                    raw_response = str(response)

                logger.debug(f"LLMレスポンス取得 | 文字数: {len(raw_response)}")

                # コードブロック抽出
                code_blocks = _extract_code_blocks(raw_response)

                if not code_blocks:
                    logger.warning(f"コードブロックが見つかりません (attempt {attempt})")
                    # コードが見つからない場合はそのまま返す
                    explanation = raw_response.strip()
                    return AgentResult(
                        explanation=explanation,
                        code=None,
                        figure_bytes=None,
                        plotly_fig=None,
                        error="コードブロックが見つかりませんでした",
                        raw_response=raw_response,
                    )

                # 最初のコードブロックを使用
                extracted_code = code_blocks[0]
                explanation = _remove_code_blocks(raw_response)

                # コード実行
                figure_bytes, plotly_fig, stdout, exec_error = execute_code(
                    code=extracted_code,
                    df=data_ctx.df,
                    timeout=self.settings.code_exec_timeout,
                )

                if exec_error:
                    last_error = exec_error
                    logger.warning(
                        f"コード実行失敗 (attempt {attempt}): {exec_error}"
                    )
                    # 次の試行に向けてエラー情報をメッセージに追加
                    if attempt < self.settings.max_retries:
                        messages.append({
                            "role": "assistant",
                            "content": raw_response,
                        })
                        messages.append({
                            "role": "user",
                            "content": (
                                f"前回のコードでエラーが発生しました: {exec_error}\n"
                                "コードを修正して再度出力してください。"
                            ),
                        })
                    continue

                logger.info(f"エージェント実行成功 (attempt {attempt})")
                return AgentResult(
                    explanation=explanation,
                    code=extracted_code,
                    figure_bytes=figure_bytes,
                    plotly_fig=plotly_fig,
                    error=None,
                    raw_response=raw_response,
                )

            except Exception as e:
                last_error = f"エージェント実行エラー: {type(e).__name__}: {e}"
                logger.error(f"エージェント実行例外 (attempt {attempt}): {e}")
                if attempt < self.settings.max_retries:
                    continue

        # すべてのリトライが失敗
        logger.error(f"最大リトライ回数到達 | last_error={last_error}")
        return AgentResult(
            explanation="申し訳ありません。コードの生成・実行に失敗しました。",
            code=None,
            figure_bytes=None,
            plotly_fig=None,
            error=last_error,
            raw_response=raw_response,
        )
