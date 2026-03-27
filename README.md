# 📓 LocalNotebook（Windows 11対応）

完全ローカルで動作する **NotebookLM 風ドキュメント管理システム**。
Ollama + ChromaDB による RAG チャット・セマンティック検索・自動要約。
**インターネット不要・データ外部送信なし。**

---

## 機能一覧

| タブ | 機能 |
|------|------|
| 📄 ドキュメント | PDF / DOCX / TXT /　XLSX / Markdown のアップロード・管理・インデックス |
| 💬 チャット | ドキュメントを参照しながら Ollama で Q&A（RAGストリーミング） |
| 🔍 検索 | nomic-embed-text によるセマンティックベクトル検索 |
| 📝 要約 | 箇条書き / 詳細 / エグゼクティブ の3スタイルで自動要約 |
| 🗒️ メモ | ノートブックごとのメモ保存 |
| 📓 複数ノートブック | プロジェクト別に完全分離して管理 |

---

## セットアップ（初回のみ）

### 前提条件

- Python 3.10 以上 — https://www.python.org/
  インストール時に "Add Python to PATH" にチェックを入れること
- Ollama — https://ollama.com/download/windows

### 手順

**1. Ollama モデルを取得**（コマンドプロンプトで）

```
ollama pull gemma3:4b(ここでは例とします)
ollama pull nomic-embed-text
```

**2. setup.bat をダブルクリック**してパッケージをインストール

---

## 起動方法

**start.bat をダブルクリック** → ブラウザで index.html が自動で開きます。

---

## ファイル構成

```
local_notebook\
├── server.py          # FastAPI バックエンド（ポート 8765）
├── index.html         # シングルファイル UI
├── start.bat          # 起動スクリプト
├── setup.bat          # 初回セットアップ
└── notebook_data\     # 自動生成（データ保存先）
```

---

## 環境変数カスタマイズ

start.bat 冒頭に以下を追加できます：

```bat
set CHAT_MODEL=gemma3:4b
set EMBED_MODEL=nomic-embed-text
set DATA_DIR=C:\Users\yourname\Documents\notebook_data
```

---

## トラブルシューティング

**Ollamaが認識されない** → タスクトレイでOllamaが起動しているか確認

**python コマンドが見つからない** → `py server.py` で試す

**chromadb インストールエラー** → Visual C++ Build Tools が必要な場合がある
  https://visualstudio.microsoft.com/visual-cpp-build-tools/

**ポート8765が使用中** → server.py 末尾と index.html 内の `8765` を別の番号に変更

**補足**
メモからの追加ができません。
