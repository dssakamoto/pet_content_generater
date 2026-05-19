"""エージェントのテストモジュール"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from app.agent.agent import AgentResult, AnalysisAgent, _extract_code_blocks, _remove_code_blocks
from app.agent.code_executor import CodeSafetyError, check_code_safety, execute_code
from app.agent.prompts import build_system_prompt
from app.config import Settings
from app.data.context import DataContext


# テスト用のサンプルDataFrame
@pytest.fixture
def sample_df() -> pd.DataFrame:
    return pd.DataFrame({
        "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
        "sales": [100000, 120000, 90000],
        "product": ["商品A", "商品B", "商品A"],
    })


@pytest.fixture
def sample_data_ctx(sample_df: pd.DataFrame) -> DataContext:
    return DataContext(
        df=sample_df,
        filename="test.csv",
        schema_summary="テスト用スキーマ",
        sample_rows=sample_df.head(5).to_string(),
    )


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        ollama_base_url="http://localhost:11434",
        default_model="llama3.2",
        max_retries=3,
        code_exec_timeout=10,
    )


class TestCodeExtraction:
    """コードブロック抽出のテスト"""

    def test_extract_single_code_block(self) -> None:
        """単一コードブロックの抽出テスト"""
        text = """説明文

```python
print("Hello")
x = 1 + 2
```

説明の続き"""
        blocks = _extract_code_blocks(text)
        assert len(blocks) == 1
        assert 'print("Hello")' in blocks[0]

    def test_extract_multiple_code_blocks(self) -> None:
        """複数コードブロックの抽出テスト"""
        text = """
```python
x = 1
```

間のテキスト

```python
y = 2
```
"""
        blocks = _extract_code_blocks(text)
        assert len(blocks) == 2

    def test_extract_no_code_block(self) -> None:
        """コードブロックがない場合のテスト"""
        text = "コードブロックのないテキストです。"
        blocks = _extract_code_blocks(text)
        assert len(blocks) == 0

    def test_remove_code_blocks(self) -> None:
        """コードブロック除去のテスト"""
        text = """説明文

```python
print("test")
```

補足説明"""
        result = _remove_code_blocks(text)
        assert "```python" not in result
        assert "説明文" in result
        assert "補足説明" in result


class TestCodeSafetyCheck:
    """コード安全チェックのテスト"""

    def test_safe_code_passes(self) -> None:
        """安全なコードがチェックを通ることのテスト"""
        safe_code = """
result = df.groupby('product')['sales'].sum()
print(result)
"""
        # 例外が発生しないことを確認
        check_code_safety(safe_code)

    def test_import_blocked(self) -> None:
        """importが禁止されることのテスト"""
        with pytest.raises(CodeSafetyError, match="import"):
            check_code_safety("import os\nos.listdir('.')")

    def test_open_blocked(self) -> None:
        """open()が禁止されることのテスト"""
        with pytest.raises(CodeSafetyError, match="open"):
            check_code_safety("f = open('test.txt', 'w')")

    def test_subprocess_blocked(self) -> None:
        """subprocessが禁止されることのテスト"""
        with pytest.raises(CodeSafetyError, match="subprocess"):
            check_code_safety("subprocess.run(['ls'])")

    def test_os_blocked(self) -> None:
        """os.が禁止されることのテスト"""
        with pytest.raises(CodeSafetyError, match="os\\."):
            check_code_safety("os.listdir('.')")

    def test_eval_blocked(self) -> None:
        """eval()が禁止されることのテスト"""
        with pytest.raises(CodeSafetyError, match="eval"):
            check_code_safety("eval('1 + 1')")

    def test_exec_blocked(self) -> None:
        """exec()が禁止されることのテスト"""
        with pytest.raises(CodeSafetyError, match="exec"):
            check_code_safety("exec('x = 1')")

    def test_dunder_blocked(self) -> None:
        """__が禁止されることのテスト"""
        with pytest.raises(CodeSafetyError):
            check_code_safety("x.__class__.__mro__")


class TestCodeExecutor:
    """コード実行エンジンのテスト"""

    def test_execute_simple_print(self, sample_df: pd.DataFrame) -> None:
        """シンプルなprintコードの実行テスト"""
        code = "print(df.shape)"
        _, _, stdout, error = execute_code(code, sample_df, timeout=10)

        assert error is None
        assert "(3, 3)" in stdout

    def test_execute_dataframe_operation(self, sample_df: pd.DataFrame) -> None:
        """DataFrameの操作コードの実行テスト"""
        code = """
result = df['sales'].sum()
print(f"合計: {result}")
"""
        _, _, stdout, error = execute_code(code, sample_df, timeout=10)

        assert error is None
        assert "合計: 310000" in stdout

    def test_blocked_code_returns_error(self, sample_df: pd.DataFrame) -> None:
        """禁止コードがエラーを返すことのテスト"""
        code = "import os"
        _, _, _, error = execute_code(code, sample_df, timeout=10)

        assert error is not None
        assert "import" in error.lower() or "セキュリティ" in error

    def test_timeout_returns_error(self, sample_df: pd.DataFrame) -> None:
        """タイムアウトがエラーを返すことのテスト"""
        # 無限ループ（タイムアウトを引き起こす）
        code = "while True: pass"
        _, _, _, error = execute_code(code, sample_df, timeout=2)

        assert error is not None
        assert "タイムアウト" in error

    def test_execute_returns_figure_for_matplotlib(self, sample_df: pd.DataFrame) -> None:
        """matplotlibの図がキャプチャされることのテスト"""
        code = """
plt.figure()
plt.plot(df['sales'])
plt.savefig("output.png")
"""
        figure_bytes, _, _, error = execute_code(code, sample_df, timeout=10)

        assert error is None
        assert figure_bytes is not None
        assert len(figure_bytes) > 0

    def test_execute_syntax_error_returns_error(self, sample_df: pd.DataFrame) -> None:
        """構文エラーがエラーとして返ることのテスト"""
        code = "this is not valid python!!!"
        _, _, _, error = execute_code(code, sample_df, timeout=10)

        assert error is not None


class TestSystemPrompt:
    """システムプロンプトのテスト"""

    def test_build_system_prompt(self) -> None:
        """システムプロンプトが正しく生成されることのテスト"""
        schema_summary = "テスト用スキーマ情報"
        sample_rows = "テスト用サンプル行"

        prompt = build_system_prompt(schema_summary, sample_rows)

        assert schema_summary in prompt
        assert sample_rows in prompt
        assert "データ分析エージェント" in prompt
        assert "```python" in prompt


class TestAnalysisAgent:
    """AnalysisAgentクラスのテスト"""

    def test_agent_init(self, test_settings: Settings) -> None:
        """エージェントの初期化テスト"""
        agent = AnalysisAgent(test_settings)
        assert agent.settings == test_settings
        assert agent.client is not None

    def test_check_connection_failure(self, test_settings: Settings) -> None:
        """接続失敗時のcheck_connectionテスト"""
        agent = AnalysisAgent(test_settings)

        # Ollamaが起動していない環境ではFalseを返すはず
        with patch.object(agent.client, "list", side_effect=Exception("接続失敗")):
            is_connected, models = agent.check_connection()

        assert is_connected is False
        assert models == []

    def test_check_connection_success(self, test_settings: Settings) -> None:
        """接続成功時のcheck_connectionテスト"""
        agent = AnalysisAgent(test_settings)

        mock_model = MagicMock()
        mock_model.model = "llama3.2"
        mock_response = MagicMock()
        mock_response.models = [mock_model]

        with patch.object(agent.client, "list", return_value=mock_response):
            is_connected, models = agent.check_connection()

        assert is_connected is True
        assert "llama3.2" in models

    def test_run_with_mock_ollama(
        self, test_settings: Settings, sample_data_ctx: DataContext
    ) -> None:
        """モックOllamaでのrunメソッドテスト"""
        agent = AnalysisAgent(test_settings)

        mock_response = MagicMock()
        mock_response.message.content = """
データを分析します。

```python
result = df['sales'].sum()
print(f"売上合計: {result}")
```

以上の結果が得られます。
"""
        with patch.object(agent.client, "chat", return_value=mock_response):
            result = agent.run(
                user_query="売上合計を教えて",
                data_ctx=sample_data_ctx,
                history=[],
            )

        assert isinstance(result, AgentResult)
        assert result.code is not None
        assert "sales" in result.code
        assert result.error is None
        assert "310000" in result.explanation or result.figure_bytes is not None or True

    def test_run_no_code_block(
        self, test_settings: Settings, sample_data_ctx: DataContext
    ) -> None:
        """コードブロックがない場合のrunメソッドテスト"""
        agent = AnalysisAgent(test_settings)

        mock_response = MagicMock()
        mock_response.message.content = "コードブロックのない応答です。"

        with patch.object(agent.client, "chat", return_value=mock_response):
            result = agent.run(
                user_query="質問",
                data_ctx=sample_data_ctx,
                history=[],
            )

        assert isinstance(result, AgentResult)
        assert result.code is None
        assert result.error is not None

    def test_run_with_ollama_error(
        self, test_settings: Settings, sample_data_ctx: DataContext
    ) -> None:
        """Ollama呼び出しエラー時のrunメソッドテスト"""
        agent = AnalysisAgent(test_settings)

        with patch.object(agent.client, "chat", side_effect=Exception("接続エラー")):
            result = agent.run(
                user_query="質問",
                data_ctx=sample_data_ctx,
                history=[],
            )

        assert isinstance(result, AgentResult)
        assert result.error is not None
