# Pet Content Generator

テーマを入力して、ペット（猫・犬）の癒し系画像やショート動画を自動生成するフルスタック Web アプリです。

## デモ

1. テーマを入力（例：「春のお花見」）
2. 動物（猫 / 犬 / おまかせ）と出力形式（画像 / 動画）を選択
3. 「生成」ボタンをクリック
4. ポラロイド風フレームで画像が表示され、ダウンロードできる

## 技術スタック

| レイヤー | 技術 |
|---|---|
| フロントエンド | React 18 / TypeScript / Vite / Tailwind CSS |
| バックエンド | FastAPI / Python 3.11 / Pillow / ffmpeg |
| インフラ | Docker Compose |

## セットアップ

### 前提条件

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) がインストール・起動されていること

### 環境変数

```bash
cp .env.example .env
```

`.env` を編集して、使用する API キーを入力します。

| 変数 | 値 | 用途 |
|---|---|---|
| `IMAGE_GENERATOR` | `mock`（デフォルト）/ `gemini` / `openai` / `stability` | 画像生成エンジンの切り替え |
| `GEMINI_API_KEY` | — | Google Gemini API キー |
| `OPENAI_API_KEY` | — | OpenAI API キー |
| `STABILITY_API_KEY` | — | Stability AI API キー |

未使用のキーは空欄のままで構いません。`IMAGE_GENERATOR=mock` の場合は API キー不要で動作します。

> **Gemini を使う場合の注意:** 通常の Gemini API キー（ai.google.dev）で利用できるのは `gemini-2.0-flash-exp-image-generation` モデルです。Imagen シリーズ（`imagen-4.0-*` など）は Vertex AI 専用のため、通常のキーでは使用できません。

### 起動

```bash
docker compose up --build
```

初回はイメージのビルドが走るため少し時間がかかります。

### アクセス

| サービス | URL |
|---|---|
| フロントエンド | http://localhost:5173 |
| バックエンド API | http://localhost:8000 |

### 停止

```bash
docker compose down
```

## API

```
POST /api/generate/image
  Body: { "theme": "テーマ文字列", "animal": "cat"|"dog"|"random", "count": 1-8 }
  Response: { "images": ["/outputs/{uuid}.png", ...] }

POST /api/generate/video
  Body: { "theme": "テーマ文字列", "animal": "cat"|"dog"|"random" }
  Response: { "video": "/outputs/{uuid}.mp4" }
```

## アーキテクチャ

```
Frontend (React+Vite :5173)
  └─ /api, /outputs → proxy → Backend (FastAPI :8000)
                                ├─ generators/   (Strategy pattern)
                                │   └─ mock.py   (Pillow, 1080x1080)
                                ├─ video/
                                │   └─ composer.py (ffmpeg, 1080x1920)
                                └─ publishers/   (将来の SNS 連携)
```

### バックエンド

- **`generators/`** — `ImageGenerator` ABC を実装して差し替え可能。起動時に `IMAGE_GENERATOR` 環境変数でファクトリが選択
  - `mock.py` — Pillow でグラデーション背景 + 動物シルエット + テーマ文字を描画（1080×1080）
  - `gemini.py` — `gemini-2.0-flash-exp-image-generation` モデルで生成。無料 API キーで利用可
  - `openai_gen.py` — DALL-E 3 で生成。count 枚を並列リクエスト
  - `stability.py` — Stability AI v2beta REST API で生成。httpx で非同期リクエスト
- **`video/`** — `VideoComposer` が ffmpeg でズーム＆フェード付きの縦動画（1080×1920）を合成
- **`publishers/`** — SNS 投稿用の `Publisher` ABC（未実装、将来の拡張ポイント）
- **`config.py`** — `pydantic-settings` による設定管理。API キーはすべて `str | None = None`（未設定でも起動可）

### フロントエンド

- **デザインシステム** — `index.css` に CSS カスタムプロパティ（`--accent: #C85A2C` など）と共通クラス（`.polaroid`, `.stamp-btn`）を定義。Google Fonts（Playfair Display + Outfit）使用
- `App.tsx` — 状態管理コンテナ。`handleGenerate` を `useCallback` でメモ化、`label` 等の派生値はレンダー中に計算
- `components/` — `ThemeInput`（下線のみの入力）、`OutputSelector` / `GenerateButton` / `Preview` は `memo()` でラップ済み（タイピング中の不要な再レンダーを防止）
- `api/client.ts` — バックエンド API の fetch ラッパー

## 開発

ソースコードはバインドマウントによりホットリロードされます。ファイルを保存すると自動反映されます。

| 対象 | マウント先 |
|---|---|
| `backend/app/` | コンテナ内 `/app/app` |
| `frontend/src/`, `frontend/index.html` | コンテナ内 `/app/src`, `/app/index.html` |

## 拡張ポイント

- **Gemini 動画生成** — `settings.gemini_api_key` を参照する実装を `video/` に追加
- **新しい画像生成エンジン** — `ImageGenerator` ABC を実装し `IMAGE_GENERATOR` 変数で切り替え
- **SNS 投稿機能** — `Publisher` ABC を実装しルーターにエンドポイントを追加
- **新しい動物タイプ** — `mock.py` にシルエット描画関数を追加し `generate.py` のバリデーションを更新
