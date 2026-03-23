"""
LocalNoteBook 設定ファイル
"""

# Ollama API設定
OLLAMA_BASE_URL = "http://localhost:11434"

# 使用するモデル（Ollamaでpull済みのモデル名に合わせてください）
CHAT_MODEL = "llama3"
EMBED_MODEL = "nomic-embed-text"

# テキスト分割設定
CHUNK_SIZE = 500        # チャンクサイズ（文字数）
CHUNK_OVERLAP = 50      # チャンクオーバーラップ（文字数）

# RAG設定
TOP_K_RESULTS = 5       # 検索で返す上位件数

# データ保存先
DATA_DIR = "./data"

# サポートするファイル形式
SUPPORTED_EXTENSIONS = [".pdf", ".txt", ".docx", ".md"]

# Streamlit設定
APP_TITLE = "LocalNoteBook 📓"
APP_ICON = "📓"
