"""
ベクトルストアモジュール
ChromaDB を使用したドキュメントの埋め込み保存・検索を行います。
"""

import os
import sys
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from src.ollama_client import OllamaClient

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False


class VectorStore:
    """ChromaDB を使ったベクトルストア管理クラス"""

    def __init__(self, notebook_id: str, ollama_client: Optional[OllamaClient] = None):
        """
        Args:
            notebook_id: ノートブックID（ChromaDB コレクション名に使用）
            ollama_client: OllamaClient インスタンス（省略時は新規作成）
        """
        if not CHROMA_AVAILABLE:
            raise ImportError(
                "chromadb がインストールされていません: pip install chromadb"
            )

        self.notebook_id = notebook_id
        self.ollama = ollama_client or OllamaClient()

        # ChromaDB クライアントの初期化（永続化）
        chroma_path = os.path.join(config.DATA_DIR, "chromadb")
        os.makedirs(chroma_path, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(anonymized_telemetry=False),
        )

        # ノートブックごとにコレクションを作成
        collection_name = f"notebook_{notebook_id}".replace("-", "_")
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_documents(
        self,
        chunks: list[str],
        source_name: str,
        source_id: str,
    ) -> int:
        """
        ドキュメントチャンクを埋め込みベクトルとして追加します。

        Args:
            chunks: テキストチャンクのリスト
            source_name: ソースファイル名
            source_id: ソースID（ユニーク識別子）

        Returns:
            追加したチャンク数
        """
        if not chunks:
            return 0

        # 既存のソースを削除（再インデックス対応）
        self._delete_source(source_id)

        embeddings = []
        ids = []
        metadatas = []

        for i, chunk in enumerate(chunks):
            embedding = self.ollama.get_embeddings(chunk)
            chunk_id = f"{source_id}_chunk_{i}"

            embeddings.append(embedding)
            ids.append(chunk_id)
            metadatas.append({
                "source_id": source_id,
                "source_name": source_name,
                "chunk_index": i,
            })

        self.collection.add(
            embeddings=embeddings,
            documents=chunks,
            ids=ids,
            metadatas=metadatas,
        )

        return len(chunks)

    def search(self, query: str, top_k: int = config.TOP_K_RESULTS) -> list[dict]:
        """
        クエリに関連するチャンクを検索します。

        Args:
            query: 検索クエリ
            top_k: 返す上位件数

        Returns:
            [{"text": ..., "source_name": ..., "score": ...}] のリスト
        """
        if self.collection.count() == 0:
            return []

        query_embedding = self.ollama.get_embeddings(query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        output = []
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for doc, meta, dist in zip(docs, metas, distances):
            output.append({
                "text": doc,
                "source_name": meta.get("source_name", "不明"),
                "source_id": meta.get("source_id", ""),
                # hnsw:space が 'cosine' の場合、ChromaDB は cosine distance を返す
                # cosine similarity = 1 - cosine distance
                "score": 1 - dist,
            })

        return output

    def delete_source(self, source_id: str) -> None:
        """指定ソースのチャンクを全削除します"""
        self._delete_source(source_id)

    def _delete_source(self, source_id: str) -> None:
        """指定ソースの既存チャンクを削除します（内部用）"""
        try:
            existing = self.collection.get(
                where={"source_id": source_id}
            )
            if existing["ids"]:
                self.collection.delete(ids=existing["ids"])
        except (KeyError, ValueError):
            # ソースが存在しない場合は無視する
            pass

    def get_document_count(self) -> int:
        """コレクション内のチャンク総数を返します"""
        return self.collection.count()

    def delete_collection(self) -> None:
        """このノートブックのコレクションを削除します"""
        collection_name = f"notebook_{self.notebook_id}".replace("-", "_")
        try:
            self.client.delete_collection(name=collection_name)
        except Exception:
            pass
