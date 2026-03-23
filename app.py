"""
LocalNoteBook - メインアプリケーション
NotebookLM ライクなローカル文書管理システム
Ollama + ChromaDB + Streamlit で構成
"""

import os
import sys
import streamlit as st
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from src.notebook_manager import NotebookManager
from src.ollama_client import OllamaClient
from src.document_processor import process_file
from src.vector_store import VectorStore

# ──────────────────────────── ページ設定 ────────────────────────────

st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon=config.APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────── セッション初期化 ────────────────────────────

def init_session_state() -> None:
    """セッション状態の初期化"""
    if "selected_notebook_id" not in st.session_state:
        st.session_state.selected_notebook_id = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = {}
    if "manager" not in st.session_state:
        st.session_state.manager = NotebookManager()
    if "ollama" not in st.session_state:
        st.session_state.ollama = OllamaClient()


init_session_state()
manager: NotebookManager = st.session_state.manager
ollama: OllamaClient = st.session_state.ollama

# ──────────────────────────── ヘルパー関数 ────────────────────────────

def get_vector_store(notebook_id: str) -> VectorStore:
    """ノートブック用のベクトルストアを取得します（キャッシュ）"""
    key = f"vs_{notebook_id}"
    if key not in st.session_state:
        st.session_state[key] = VectorStore(notebook_id, ollama)
    return st.session_state[key]


def get_chat_history(notebook_id: str) -> list[dict]:
    """ノートブックのチャット履歴を取得します"""
    if notebook_id not in st.session_state.chat_history:
        st.session_state.chat_history[notebook_id] = []
    return st.session_state.chat_history[notebook_id]


def add_chat_message(notebook_id: str, role: str, content: str) -> None:
    """チャット履歴にメッセージを追加します"""
    history = get_chat_history(notebook_id)
    history.append({"role": role, "content": content})


def format_file_size(size_bytes: int) -> str:
    """ファイルサイズを人間が読みやすい形式に変換します"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / 1024 ** 2:.1f} MB"


# ──────────────────────────── サイドバー ────────────────────────────

def render_sidebar() -> None:
    """サイドバーのレンダリング"""
    with st.sidebar:
        st.title(config.APP_TITLE)
        st.caption("ローカルAI文書管理システム")

        # Ollama 接続状態
        with st.expander("⚙️ 接続状態", expanded=False):
            if ollama.is_available():
                st.success("✅ Ollama 接続中")
                try:
                    models = ollama.list_models()
                    if models:
                        st.caption(f"利用可能なモデル: {len(models)} 件")
                except Exception:
                    pass
            else:
                st.error("❌ Ollama に接続できません")
                st.info("Ollama を起動してください:\n```\nollama serve\n```")

            st.caption(f"チャットモデル: `{config.CHAT_MODEL}`")
            st.caption(f"埋め込みモデル: `{config.EMBED_MODEL}`")

        st.divider()

        # 新規ノートブック作成
        with st.expander("➕ 新規ノートブック", expanded=False):
            with st.form("create_notebook_form", clear_on_submit=True):
                new_name = st.text_input("ノートブック名", placeholder="例: 研究メモ")
                new_desc = st.text_area(
                    "説明（省略可）", placeholder="このノートブックの概要", height=80
                )
                submitted = st.form_submit_button("作成", use_container_width=True)
                if submitted:
                    if new_name.strip():
                        nb = manager.create_notebook(new_name.strip(), new_desc.strip())
                        st.session_state.selected_notebook_id = nb["id"]
                        st.success(f"「{nb['name']}」を作成しました")
                        st.rerun()
                    else:
                        st.error("ノートブック名を入力してください")

        st.divider()

        # ノートブック一覧
        st.subheader("📚 ノートブック一覧")
        notebooks = manager.list_notebooks()

        if not notebooks:
            st.info("ノートブックがありません\n上の「新規ノートブック」から作成してください")
        else:
            for nb in notebooks:
                sources = manager.list_sources(nb["id"])
                source_count = len(sources)
                label = f"📓 {nb['name']}"
                if source_count > 0:
                    label += f"  ({source_count}件)"

                is_selected = st.session_state.selected_notebook_id == nb["id"]
                btn_type = "primary" if is_selected else "secondary"

                if st.button(
                    label,
                    key=f"nb_btn_{nb['id']}",
                    use_container_width=True,
                    type=btn_type,
                ):
                    st.session_state.selected_notebook_id = nb["id"]
                    st.rerun()


# ──────────────────────────── チャットタブ ────────────────────────────

def render_chat_tab(notebook_id: str) -> None:
    """チャットタブのレンダリング"""
    sources = manager.list_sources(notebook_id)
    indexed_sources = [s for s in sources if s.get("indexed")]

    if not indexed_sources:
        st.info(
            "💡 チャットを開始するには、まず「ソース」タブからドキュメントを追加してインデックス化してください。"
        )
        return

    history = get_chat_history(notebook_id)

    # チャット履歴の表示
    chat_container = st.container()
    with chat_container:
        if not history:
            st.info("メッセージを入力してチャットを開始してください。")
        else:
            for msg in history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

    # 入力エリア
    st.divider()

    col1, col2 = st.columns([5, 1])
    with col1:
        user_input = st.chat_input(
            "ドキュメントについて質問してください...",
            key=f"chat_input_{notebook_id}",
        )
    with col2:
        if st.button("🗑️ 履歴クリア", key=f"clear_chat_{notebook_id}"):
            st.session_state.chat_history[notebook_id] = []
            st.rerun()

    if user_input:
        _handle_chat(notebook_id, user_input)


def _handle_chat(notebook_id: str, user_input: str) -> None:
    """チャットメッセージを処理してレスポンスを表示します"""
    if not ollama.is_available():
        st.error("Ollama に接続できません。Ollama を起動してください。")
        return

    # ユーザーメッセージを追加・表示
    add_chat_message(notebook_id, "user", user_input)
    with st.chat_message("user"):
        st.markdown(user_input)

    # ベクトル検索でコンテキストを取得
    vs = get_vector_store(notebook_id)
    search_results = vs.search(user_input, top_k=config.TOP_K_RESULTS)

    if search_results:
        context_parts = []
        for r in search_results:
            context_parts.append(f"【{r['source_name']}】\n{r['text']}")
        context = "\n\n---\n\n".join(context_parts)
    else:
        context = "（関連するドキュメントが見つかりませんでした）"

    # システムプロンプト
    system_prompt = (
        "あなたは優秀なドキュメントアシスタントです。"
        "以下のドキュメントの内容を参考にして、ユーザーの質問に日本語で丁寧に回答してください。"
        "ドキュメントに記載されていない情報については、その旨を明確に伝えてください。\n\n"
        f"【参考ドキュメント】\n{context}"
    )

    # チャット履歴からメッセージを構築
    history = get_chat_history(notebook_id)
    messages = [{"role": "system", "content": system_prompt}]

    # 直近の会話履歴（最新10ターン = 20メッセージ）を含める
    recent_history = history[:-1]  # 最後のユーザーメッセージは除く
    if len(recent_history) > 20:
        recent_history = recent_history[-20:]
    messages.extend(recent_history)
    messages.append({"role": "user", "content": user_input})

    # ストリーミングレスポンス表示
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        try:
            for chunk in ollama.chat(messages, stream=True):
                full_response += chunk
                response_placeholder.markdown(full_response + "▌")
            response_placeholder.markdown(full_response)
        except Exception as e:
            st.error(f"レスポンス生成中にエラーが発生しました: {e}")
            return

    add_chat_message(notebook_id, "assistant", full_response)
    st.rerun()


# ──────────────────────────── ソースタブ ────────────────────────────

def render_sources_tab(notebook_id: str) -> None:
    """ソースタブのレンダリング"""
    sources = manager.list_sources(notebook_id)

    # ファイルアップロード
    st.subheader("📤 ソースを追加")
    ext_list = ", ".join(config.SUPPORTED_EXTENSIONS)
    uploaded_files = st.file_uploader(
        f"ファイルをアップロードしてください（対応形式: {ext_list}）",
        type=[ext.lstrip(".") for ext in config.SUPPORTED_EXTENSIONS],
        accept_multiple_files=True,
        key=f"uploader_{notebook_id}",
    )

    if uploaded_files:
        if st.button(
            f"📥 {len(uploaded_files)} 件のファイルをインデックス化",
            type="primary",
            key=f"index_btn_{notebook_id}",
        ):
            _index_uploaded_files(notebook_id, uploaded_files)

    st.divider()

    # ソース一覧
    st.subheader(f"📋 ソース一覧 ({len(sources)} 件)")

    if not sources:
        st.info("まだソースが追加されていません。上からファイルをアップロードしてください。")
        return

    for src in sources:
        with st.container():
            col1, col2, col3, col4 = st.columns([4, 2, 2, 1])
            with col1:
                icon = "✅" if src.get("indexed") else "⏳"
                st.write(f"{icon} **{src['filename']}**")
            with col2:
                st.caption(format_file_size(src.get("size", 0)))
            with col3:
                if src.get("indexed"):
                    st.caption(f"チャンク数: {src.get('chunk_count', 0)}")
                else:
                    st.caption("未インデックス")
            with col4:
                if st.button(
                    "🗑️",
                    key=f"del_src_{src['id']}",
                    help="このソースを削除",
                ):
                    _delete_source(notebook_id, src["id"])


def _index_uploaded_files(notebook_id: str, uploaded_files) -> None:
    """アップロードされたファイルをインデックス化します"""
    if not ollama.is_available():
        st.error("Ollama に接続できません。Ollama を起動してください。")
        return

    vs = get_vector_store(notebook_id)
    total = len(uploaded_files)
    progress_bar = st.progress(0, text="インデックス化を開始しています...")

    success_count = 0
    error_messages = []

    for i, uploaded_file in enumerate(uploaded_files):
        progress_text = f"処理中: {uploaded_file.name} ({i + 1}/{total})"
        progress_bar.progress((i + 1) / total, text=progress_text)

        try:
            file_bytes = uploaded_file.read()

            # 一時ファイルに保存して処理
            import tempfile
            suffix = Path(uploaded_file.name).suffix
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name

            try:
                _, chunks = process_file(tmp_path)
            finally:
                os.remove(tmp_path)

            if not chunks:
                error_messages.append(f"{uploaded_file.name}: テキストを抽出できませんでした")
                continue

            # ソースをデータベースに追加
            source = manager.add_source(
                notebook_id,
                uploaded_file.name,
                file_bytes,
                chunk_count=0,
            )

            # ベクトルストアにインデックス化
            chunk_count = vs.add_documents(chunks, uploaded_file.name, source["id"])

            # インデックス状態を更新
            manager.update_source_index(notebook_id, source["id"], chunk_count)

            success_count += 1

        except Exception as e:
            error_messages.append(f"{uploaded_file.name}: {e}")

    progress_bar.progress(1.0, text="完了!")

    if success_count > 0:
        st.success(f"✅ {success_count} 件のファイルをインデックス化しました")
    for msg in error_messages:
        st.error(f"❌ {msg}")

    st.rerun()


def _delete_source(notebook_id: str, source_id: str) -> None:
    """ソースを削除します（ベクトルストアからも削除）"""
    try:
        vs = get_vector_store(notebook_id)
        vs.delete_source(source_id)
    except Exception:
        pass

    manager.delete_source(notebook_id, source_id)
    st.success("ソースを削除しました")
    st.rerun()


# ──────────────────────────── 要約タブ ────────────────────────────

def render_summary_tab(notebook_id: str) -> None:
    """要約タブのレンダリング"""
    sources = manager.list_sources(notebook_id)
    indexed_sources = [s for s in sources if s.get("indexed")]

    if not indexed_sources:
        st.info(
            "💡 要約を生成するには、まず「ソース」タブからドキュメントを追加してインデックス化してください。"
        )
        return

    st.subheader("📝 ドキュメント要約")

    # ソース選択
    source_options = {s["filename"]: s for s in indexed_sources}
    source_options["すべてのソース（統合要約）"] = None

    selected_label = st.selectbox(
        "要約するソースを選択",
        options=list(source_options.keys()),
        key=f"summary_select_{notebook_id}",
    )

    col1, col2 = st.columns(2)
    with col1:
        summary_type = st.radio(
            "要約タイプ",
            ["概要", "詳細", "箇条書き", "キーワード抽出"],
            horizontal=True,
            key=f"summary_type_{notebook_id}",
        )
    with col2:
        if st.button("🔄 要約を生成", type="primary", key=f"gen_summary_{notebook_id}"):
            _generate_summary(notebook_id, source_options[selected_label], summary_type)


def _generate_summary(
    notebook_id: str,
    source: dict | None,
    summary_type: str,
) -> None:
    """要約を生成して表示します"""
    if not ollama.is_available():
        st.error("Ollama に接続できません。Ollama を起動してください。")
        return

    vs = get_vector_store(notebook_id)

    # コンテキストの取得
    if source is None:
        # すべてのソースからランダムサンプル
        all_sources = manager.list_sources(notebook_id)
        query = "このドキュメントの主要な内容と概要"
        results = vs.search(query, top_k=10)
    else:
        # 特定ソースのテキストを検索
        query = f"{source['filename']} の内容と概要"
        all_results = vs.search(query, top_k=20)
        results = [r for r in all_results if r.get("source_id") == source["id"]]
        if not results:
            results = all_results[:5]

    if not results:
        st.warning("ドキュメントからテキストを取得できませんでした。")
        return

    context = "\n\n".join(r["text"] for r in results)
    source_name = source["filename"] if source else "全ドキュメント"

    # 要約タイプに応じたプロンプト
    type_prompts = {
        "概要": "以下のドキュメントの内容を、3〜5文程度で簡潔に要約してください。",
        "詳細": "以下のドキュメントの内容を、重要な詳細を含めて詳しく要約してください。",
        "箇条書き": "以下のドキュメントの重要なポイントを箇条書き（・）で10項目以内にまとめてください。",
        "キーワード抽出": "以下のドキュメントから重要なキーワードや概念を10個程度抽出し、それぞれ簡単な説明を加えてください。",
    }

    prompt = (
        f"{type_prompts.get(summary_type, type_prompts['概要'])}\n\n"
        f"【ドキュメント: {source_name}】\n{context}"
    )

    messages = [
        {
            "role": "system",
            "content": "あなたは優秀なドキュメントアナリストです。与えられたドキュメントを正確に分析し、日本語で要約を作成してください。",
        },
        {"role": "user", "content": prompt},
    ]

    st.subheader(f"📄 {source_name} — {summary_type}")

    with st.spinner("要約を生成しています..."):
        try:
            response_placeholder = st.empty()
            full_response = ""
            for chunk in ollama.chat(messages, stream=True):
                full_response += chunk
                response_placeholder.markdown(full_response + "▌")
            response_placeholder.markdown(full_response)
        except Exception as e:
            st.error(f"要約生成中にエラーが発生しました: {e}")


# ──────────────────────────── ノートブック設定 ────────────────────────────

def render_settings_tab(notebook_id: str) -> None:
    """設定タブのレンダリング"""
    nb = manager.get_notebook(notebook_id)
    if not nb:
        return

    st.subheader("⚙️ ノートブック設定")

    with st.form("edit_notebook_form"):
        name = st.text_input("ノートブック名", value=nb["name"])
        desc = st.text_area("説明", value=nb.get("description", ""), height=100)
        save_btn = st.form_submit_button("💾 保存", type="primary")

        if save_btn:
            if name.strip():
                manager.update_notebook(notebook_id, name.strip(), desc.strip())
                st.success("設定を保存しました")
                st.rerun()
            else:
                st.error("ノートブック名を入力してください")

    st.divider()
    st.subheader("⚠️ 危険な操作")

    col1, col2 = st.columns(2)
    with col1:
        if st.button(
            "🗑️ このノートブックを削除",
            type="secondary",
            key=f"delete_nb_{notebook_id}",
        ):
            st.session_state[f"confirm_delete_{notebook_id}"] = True

    if st.session_state.get(f"confirm_delete_{notebook_id}"):
        st.warning(f"「{nb['name']}」を削除しますか？この操作は元に戻せません。")
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("✅ はい、削除します", type="primary"):
                # ベクトルストアも削除
                try:
                    vs = get_vector_store(notebook_id)
                    vs.delete_collection()
                except Exception:
                    pass
                manager.delete_notebook(notebook_id)
                st.session_state.selected_notebook_id = None
                st.session_state.pop(f"confirm_delete_{notebook_id}", None)
                st.rerun()
        with col_no:
            if st.button("❌ キャンセル"):
                st.session_state.pop(f"confirm_delete_{notebook_id}", None)
                st.rerun()


# ──────────────────────────── メインコンテンツ ────────────────────────────

def render_main_content() -> None:
    """メインコンテンツのレンダリング"""
    notebook_id = st.session_state.selected_notebook_id

    if notebook_id is None:
        # ウェルカム画面
        st.title("📓 LocalNoteBook へようこそ")
        st.markdown(
            """
            **LocalNoteBook** は、Ollama を使用した完全ローカル動作の文書管理・AI チャットシステムです。

            ### 🚀 はじめ方
            1. 左のサイドバーから「**➕ 新規ノートブック**」を作成してください
            2. ノートブックを選択し、「**ソース**」タブからドキュメントをアップロードします
            3. インデックス化が完了したら、「**チャット**」タブで質問できます

            ### 📋 対応ファイル形式
            - **PDF** (.pdf) — 論文、マニュアル、レポートなど
            - **テキスト** (.txt) — プレーンテキスト
            - **Word** (.docx) — Microsoft Word ドキュメント
            - **Markdown** (.md) — メモ、README など

            ### ⚙️ 必要な環境
            - [Ollama](https://ollama.ai/) が起動していること
            - チャットモデル: `""" + config.CHAT_MODEL + """`
            - 埋め込みモデル: `""" + config.EMBED_MODEL + """`

            ```bash
            # 必要なモデルのダウンロード
            ollama pull """ + config.CHAT_MODEL + """
            ollama pull """ + config.EMBED_MODEL + """
            ```

            ### 🔒 プライバシー
            すべての処理はローカル環境で行われます。データが外部に送信されることはありません。
            """
        )
        return

    nb = manager.get_notebook(notebook_id)
    if not nb:
        st.error("ノートブックが見つかりません")
        st.session_state.selected_notebook_id = None
        return

    # ノートブックヘッダー
    st.title(f"📓 {nb['name']}")
    if nb.get("description"):
        st.caption(nb["description"])

    # タブ
    tab_chat, tab_sources, tab_summary, tab_settings = st.tabs(
        ["💬 チャット", "📄 ソース", "📝 要約", "⚙️ 設定"]
    )

    with tab_chat:
        render_chat_tab(notebook_id)

    with tab_sources:
        render_sources_tab(notebook_id)

    with tab_summary:
        render_summary_tab(notebook_id)

    with tab_settings:
        render_settings_tab(notebook_id)


# ──────────────────────────── エントリーポイント ────────────────────────────

render_sidebar()
render_main_content()
