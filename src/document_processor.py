"""
ドキュメント処理モジュール
PDF・DOCX・TXT・MD ファイルのテキスト抽出とチャンク分割を行います。
"""

import os
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def extract_text_from_file(file_path: str) -> str:
    """
    ファイルからテキストを抽出します。

    対応形式: .pdf, .txt, .docx, .md

    Args:
        file_path: 対象ファイルのパス

    Returns:
        抽出されたテキスト
    """
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        return _extract_pdf(file_path)
    elif ext in (".txt", ".md"):
        return _extract_text(file_path)
    elif ext == ".docx":
        return _extract_docx(file_path)
    else:
        raise ValueError(f"未対応のファイル形式です: {ext}")


def _extract_pdf(file_path: str) -> str:
    """PDF ファイルからテキストを抽出します"""
    try:
        import fitz  # PyMuPDF
    except ImportError as e:
        raise ImportError("PyMuPDF がインストールされていません: pip install pymupdf") from e

    text_parts = []
    with fitz.open(file_path) as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return "\n".join(text_parts)


def _extract_text(file_path: str) -> str:
    """TXT / MD ファイルからテキストを抽出します"""
    encodings = ["utf-8", "utf-8-sig", "cp932", "shift_jis"]
    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, LookupError):
            continue
    raise ValueError(f"ファイルのエンコーディングを判別できませんでした: {file_path}")


def _extract_docx(file_path: str) -> str:
    """DOCX ファイルからテキストを抽出します"""
    try:
        import docx
    except ImportError as e:
        raise ImportError(
            "python-docx がインストールされていません: pip install python-docx"
        ) from e

    doc = docx.Document(file_path)
    return "\n".join(para.text for para in doc.paragraphs if para.text.strip())


def split_text(
    text: str,
    chunk_size: int = config.CHUNK_SIZE,
    chunk_overlap: int = config.CHUNK_OVERLAP,
) -> list[str]:
    """
    テキストをチャンクに分割します。

    Args:
        text: 分割するテキスト
        chunk_size: チャンクサイズ（文字数）
        chunk_overlap: オーバーラップ（文字数）。chunk_size 未満である必要があります。

    Returns:
        テキストチャンクのリスト

    Raises:
        ValueError: chunk_overlap >= chunk_size の場合
    """
    if chunk_overlap >= chunk_size:
        raise ValueError(
            f"chunk_overlap ({chunk_overlap}) は chunk_size ({chunk_size}) 未満である必要があります"
        )

    if not text.strip():
        return []

    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - chunk_overlap

    return chunks


def process_file(file_path: str) -> tuple[str, list[str]]:
    """
    ファイルを処理してテキストとチャンクを返します。

    Args:
        file_path: 対象ファイルのパス

    Returns:
        (full_text, chunks) のタプル
    """
    full_text = extract_text_from_file(file_path)
    chunks = split_text(full_text)
    return full_text, chunks
