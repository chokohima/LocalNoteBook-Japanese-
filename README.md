# LocalNoteBook 📓

Windows環境下でOllamaとPythonを使った完全ローカルAI文書管理システム

[NotebookLM](https://notebooklm.google.com/) にインスパイアされた、**完全ローカル動作**の文書管理・AIチャットアプリです。  
Ollama + ChromaDB + Streamlit を使用しており、データが一切外部に送信されません。

---

## 🚀 特徴

- 📁 **複数ノートブック管理** — プロジェクトや用途ごとにノートブックを作成
- 📤 **ドキュメントアップロード** — PDF / TXT / DOCX / MD に対応
- 🔍 **自動インデックス化** — アップロード時にベクトル埋め込みを生成・保存
- 💬 **RAGチャット** — ドキュメントの内容に基づいて日本語でAI回答
- 📝 **ドキュメント要約** — 概要・詳細・箇条書き・キーワード抽出に対応
- 🔒 **完全ローカル** — インターネット接続不要、データ漏洩リスクなし

---

## 📋 必要な環境

| ソフトウェア | バージョン | 用途 |
|---|---|---|
| Python | 3.10以上 | アプリケーション実行 |
| [Ollama](https://ollama.ai/) | 最新版 | ローカルLLM実行（GPU推奨） |
| GPU | VRAM 8GB以上推奨 | LLMの高速推論 |

---

## ⚙️ セットアップ

### 1. Ollama のインストールと起動

```bash
# Windows の場合: https://ollama.ai/ からインストーラーをダウンロード
# macOS の場合:
brew install ollama

# Ollama サーバーを起動
ollama serve
```

### 2. 必要なモデルをダウンロード

```bash
# チャット用モデル（llama3 推奨）
ollama pull llama3

# 埋め込み用モデル
ollama pull nomic-embed-text
```

> 他のモデルを使用する場合は `config.py` の `CHAT_MODEL` / `EMBED_MODEL` を変更してください。

### 3. リポジトリのクローンと依存ライブラリのインストール

```bash
git clone https://github.com/chokohima/LocalNoteBook-Japanese-.git
cd LocalNoteBook-Japanese-

# 仮想環境の作成（推奨）
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# 依存ライブラリのインストール
pip install -r requirements.txt
```

### 4. アプリの起動

```bash
streamlit run app.py
```

ブラウザが自動的に開き、`http://localhost:8501` でアプリにアクセスできます。

---

## 🖥️ 使い方

1. **ノートブックを作成** — 左のサイドバーから「➕ 新規ノートブック」をクリック
2. **ソースを追加** — 「📄 ソース」タブからファイルをアップロードし、インデックス化
3. **チャット** — 「💬 チャット」タブで質問する
4. **要約** — 「📝 要約」タブで概要・詳細・箇条書きを生成

---

## 📂 プロジェクト構成

```
LocalNoteBook-Japanese-/
├── app.py                     # メインアプリ（Streamlit）
├── config.py                  # 設定ファイル
├── requirements.txt           # 依存ライブラリ
├── src/
│   ├── __init__.py
│   ├── ollama_client.py       # Ollama API ラッパー
│   ├── document_processor.py  # ドキュメント解析・チャンク分割
│   ├── vector_store.py        # ChromaDB ベクトルストア
│   └── notebook_manager.py   # ノートブック/ソース管理
└── data/                      # データ保存ディレクトリ（自動生成）
    ├── notebooks.json         # ノートブック一覧
    ├── notebooks/             # ノートブックデータ
    └── chromadb/              # ベクトルデータベース
```

---

## ⚙️ 設定のカスタマイズ

`config.py` を編集して設定を変更できます：

```python
OLLAMA_BASE_URL = "http://localhost:11434"  # Ollama サーバーURL
CHAT_MODEL = "llama3"                        # チャットモデル
EMBED_MODEL = "nomic-embed-text"             # 埋め込みモデル
CHUNK_SIZE = 500                             # テキストチャンクサイズ
CHUNK_OVERLAP = 50                           # チャンクオーバーラップ
TOP_K_RESULTS = 5                            # RAG検索の上位件数
```

---

## 📜 ライセンス

MIT License — 詳細は [LICENSE](LICENSE) を参照してください。
