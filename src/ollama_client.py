"""
Ollama API クライアント
チャット補完と埋め込みベクトル生成を提供します。
"""

import json
import requests
from typing import Generator, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class OllamaClient:
    """Ollama API との通信を担当するクライアントクラス"""

    def __init__(
        self,
        base_url: str = config.OLLAMA_BASE_URL,
        chat_model: str = config.CHAT_MODEL,
        embed_model: str = config.EMBED_MODEL,
    ):
        self.base_url = base_url.rstrip("/")
        self.chat_model = chat_model
        self.embed_model = embed_model

    def is_available(self) -> bool:
        """Ollama サーバーが起動しているか確認します"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def list_models(self) -> list[str]:
        """利用可能なモデルの一覧を返します"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Ollama への接続に失敗しました: {e}") from e

    def get_embeddings(self, text: str) -> list[float]:
        """テキストの埋め込みベクトルを生成します"""
        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.embed_model, "prompt": text},
                timeout=60,
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"埋め込みベクトルの生成に失敗しました: {e}") from e

    def chat(
        self,
        messages: list[dict],
        stream: bool = True,
    ) -> Generator[str, None, None] | str:
        """
        チャット補完を行います。

        Args:
            messages: [{"role": "user"/"assistant"/"system", "content": "..."}]
            stream: ストリーミング出力するか

        Returns:
            stream=True の場合はジェネレーター、False の場合は文字列
        """
        payload = {
            "model": self.chat_model,
            "messages": messages,
            "stream": stream,
        }

        try:
            if stream:
                return self._chat_stream(payload)
            else:
                response = requests.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=300,
                )
                response.raise_for_status()
                return response.json()["message"]["content"]
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"チャットに失敗しました: {e}") from e

    def _chat_stream(self, payload: dict) -> Generator[str, None, None]:
        """ストリーミングチャットのジェネレーター"""
        with requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
            stream=True,
            timeout=300,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    if not chunk.get("done", False):
                        yield chunk["message"]["content"]
