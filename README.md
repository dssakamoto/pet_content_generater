# LLM分析エージェントチャットボット

ローカルLLM（Ollama）を使ったデータ分析・可視化ツール

## セットアップ
1. Ollamaインストール・起動: `ollama serve`
2. モデル取得: `ollama pull llama3.2`
3. 依存インストール: `pip install -r requirements.txt`
4. 起動: `streamlit run app/main.py`

## 使い方
1. サイドバーからCSV/JSON/Excelをアップロード
2. チャット欄に分析指示を入力（例: "売上の月別推移を折れ線グラフで表示して"）
3. LLMが自動でコードを生成・実行し、グラフを表示
