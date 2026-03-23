"""
ノートブック管理モジュール
ノートブックとソースのCRUD操作を提供します。
"""

import json
import os
import shutil
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class NotebookManager:
    """ノートブックの作成・取得・更新・削除を管理するクラス"""

    def __init__(self, data_dir: str = config.DATA_DIR):
        self.data_dir = data_dir
        self.notebooks_file = os.path.join(data_dir, "notebooks.json")
        os.makedirs(data_dir, exist_ok=True)
        self._ensure_notebooks_file()

    # ──────────────────────────── ノートブック CRUD ────────────────────────────

    def _ensure_notebooks_file(self) -> None:
        """notebooks.json が存在しない場合は作成します"""
        if not os.path.exists(self.notebooks_file):
            self._save_notebooks([])

    def _load_notebooks(self) -> list[dict]:
        """notebooks.json を読み込みます"""
        with open(self.notebooks_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_notebooks(self, notebooks: list[dict]) -> None:
        """notebooks.json に保存します"""
        with open(self.notebooks_file, "w", encoding="utf-8") as f:
            json.dump(notebooks, f, ensure_ascii=False, indent=2)

    def list_notebooks(self) -> list[dict]:
        """全ノートブックを返します"""
        return self._load_notebooks()

    def get_notebook(self, notebook_id: str) -> Optional[dict]:
        """指定IDのノートブックを返します（存在しない場合は None）"""
        notebooks = self._load_notebooks()
        for nb in notebooks:
            if nb["id"] == notebook_id:
                return nb
        return None

    def create_notebook(self, name: str, description: str = "") -> dict:
        """
        新しいノートブックを作成します。

        Args:
            name: ノートブック名
            description: 説明（省略可）

        Returns:
            作成したノートブックの辞書
        """
        notebooks = self._load_notebooks()

        notebook = {
            "id": str(uuid.uuid4()),
            "name": name,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        # ノートブック用ディレクトリを作成
        nb_dir = self._notebook_dir(notebook["id"])
        os.makedirs(os.path.join(nb_dir, "files"), exist_ok=True)
        self._save_sources(notebook["id"], [])

        notebooks.append(notebook)
        self._save_notebooks(notebooks)
        return notebook

    def update_notebook(
        self,
        notebook_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[dict]:
        """ノートブック情報を更新します"""
        notebooks = self._load_notebooks()
        for nb in notebooks:
            if nb["id"] == notebook_id:
                if name is not None:
                    nb["name"] = name
                if description is not None:
                    nb["description"] = description
                nb["updated_at"] = datetime.now().isoformat()
                self._save_notebooks(notebooks)
                return nb
        return None

    def delete_notebook(self, notebook_id: str) -> bool:
        """
        ノートブックを削除します（ファイルとベクトルストアも削除）。

        Returns:
            削除成功なら True
        """
        notebooks = self._load_notebooks()
        new_notebooks = [nb for nb in notebooks if nb["id"] != notebook_id]
        if len(new_notebooks) == len(notebooks):
            return False

        # ファイルディレクトリを削除
        nb_dir = self._notebook_dir(notebook_id)
        if os.path.exists(nb_dir):
            shutil.rmtree(nb_dir)

        self._save_notebooks(new_notebooks)
        return True

    # ──────────────────────────── ソース CRUD ────────────────────────────

    def _notebook_dir(self, notebook_id: str) -> str:
        return os.path.join(self.data_dir, "notebooks", notebook_id)

    def _sources_file(self, notebook_id: str) -> str:
        return os.path.join(self._notebook_dir(notebook_id), "sources.json")

    def _save_sources(self, notebook_id: str, sources: list[dict]) -> None:
        with open(self._sources_file(notebook_id), "w", encoding="utf-8") as f:
            json.dump(sources, f, ensure_ascii=False, indent=2)

    def list_sources(self, notebook_id: str) -> list[dict]:
        """ノートブックのソース一覧を返します"""
        sources_file = self._sources_file(notebook_id)
        if not os.path.exists(sources_file):
            return []
        with open(sources_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def add_source(
        self,
        notebook_id: str,
        filename: str,
        file_bytes: bytes,
        chunk_count: int = 0,
    ) -> dict:
        """
        ソースファイルをノートブックに追加します。

        Args:
            notebook_id: ノートブックID
            filename: ファイル名
            file_bytes: ファイルのバイト列
            chunk_count: インデックス済みチャンク数

        Returns:
            追加したソースの辞書
        """
        sources = self.list_sources(notebook_id)

        source_id = str(uuid.uuid4())
        files_dir = os.path.join(self._notebook_dir(notebook_id), "files")
        os.makedirs(files_dir, exist_ok=True)

        # ファイルを保存（source_id をプレフィックスとして衝突回避）
        saved_filename = f"{source_id}_{filename}"
        file_path = os.path.join(files_dir, saved_filename)
        with open(file_path, "wb") as f:
            f.write(file_bytes)

        source = {
            "id": source_id,
            "filename": filename,
            "saved_filename": saved_filename,
            "file_path": file_path,
            "size": len(file_bytes),
            "chunk_count": chunk_count,
            "indexed": chunk_count > 0,
            "created_at": datetime.now().isoformat(),
        }

        sources.append(source)
        self._save_sources(notebook_id, sources)

        # ノートブックの更新日時を更新
        notebooks = self._load_notebooks()
        for nb in notebooks:
            if nb["id"] == notebook_id:
                nb["updated_at"] = datetime.now().isoformat()
                break
        self._save_notebooks(notebooks)

        return source

    def update_source_index(
        self, notebook_id: str, source_id: str, chunk_count: int
    ) -> None:
        """ソースのインデックス状態を更新します"""
        sources = self.list_sources(notebook_id)
        for src in sources:
            if src["id"] == source_id:
                src["chunk_count"] = chunk_count
                src["indexed"] = chunk_count > 0
                break
        self._save_sources(notebook_id, sources)

    def delete_source(self, notebook_id: str, source_id: str) -> bool:
        """ソースを削除します（ファイルも削除）"""
        sources = self.list_sources(notebook_id)
        target = next((s for s in sources if s["id"] == source_id), None)
        if not target:
            return False

        # ファイルを削除
        if os.path.exists(target.get("file_path", "")):
            os.remove(target["file_path"])

        new_sources = [s for s in sources if s["id"] != source_id]
        self._save_sources(notebook_id, new_sources)
        return True

    def get_source_file_path(self, notebook_id: str, source_id: str) -> Optional[str]:
        """ソースのファイルパスを返します"""
        sources = self.list_sources(notebook_id)
        for src in sources:
            if src["id"] == source_id:
                file_path = src.get("file_path")
                if file_path is None:
                    import warnings
                    warnings.warn(
                        f"ソース {source_id} に file_path が見つかりません",
                        stacklevel=2,
                    )
                return file_path
        return None
