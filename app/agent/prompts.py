"""システムプロンプト定義モジュール"""


SYSTEM_PROMPT_TEMPLATE = """あなたはデータ分析エージェントです。以下の制約を必ず守ってください。

【出力ルール】
1. ユーザーの質問に回答するPythonコードを必ず出力する
2. コードは ```python と ``` で囲む（マークダウン形式）
3. コードブロックの前後に日本語で分析の解説を書く

【コード制約】
- 利用可能な変数: df (pandas.DataFrame), plt (matplotlib.pyplot), px (plotly.express), pd (pandas), np (numpy)
- importは禁止（上記変数がすでに利用可能です）
- ファイルの読み書き・subprocess・os・eval・execは禁止
- 可視化はplt.savefig("output.png") または fig = px.*(...)の形式で終わること
- df操作後にprint文で結果を確認すること

【データ情報】
{schema_summary}

【サンプルデータ（先頭5行）】
{sample_rows}
"""


def build_system_prompt(schema_summary: str, sample_rows: str) -> str:
    """データ情報を埋め込んだシステムプロンプトを生成する

    Args:
        schema_summary: データのスキーマサマリー文字列
        sample_rows: データのサンプル行文字列

    Returns:
        完成したシステムプロンプト文字列
    """
    return SYSTEM_PROMPT_TEMPLATE.format(
        schema_summary=schema_summary,
        sample_rows=sample_rows,
    )
