import streamlit as st
import time
from deep_translator import GoogleTranslator
from bert_engine.embedder import BertEmbedder
from bert_engine.searcher import SemanticSearcher
from bert_engine.database import MySQLDocumentDB
import base64

# 设置页面配置
st.set_page_config(
    page_title="AI 向量检索系统",
    layout="centered",
)

# 加载背景图像
def set_background(image_path: str):
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    css = f"""
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{encoded}");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
        color: white;
    }}
    h1 {{
        text-align: center;
        font-size: 42px;
        font-weight: bold;
        color: white;
        text-shadow: 2px 2px 4px #000;
        font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
        background-color: rgba(0, 0, 0, 0);  /* 透明背景 */
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

set_background("Background.png")

# 美化后的标题（无背景块）
st.markdown(
    "<h1 style='text-align: center;'>🤖 AI 向量检索系统</h1>", 
    unsafe_allow_html=True
)
# 初始化 session_state
if "all_documents" not in st.session_state:
    st.session_state.all_documents = []
if "current_results" not in st.session_state:
    st.session_state.current_results = []
if "search_done" not in st.session_state:
    st.session_state.search_done = False
if "embedder" not in st.session_state:
    st.session_state.embedder = BertEmbedder()
if "elapsed_time" not in st.session_state:
    st.session_state.elapsed_time = 0.0

# 检索设置
query = st.text_input("请输入检索内容（中文将自动翻译为英文）")
field = st.selectbox("选择计算相似度标准", ["title", "abstract", "authors", "category", "title+abstract"], index=4)
sort_by = st.selectbox("排序方式", ["relevance", "date"])
page_size = st.selectbox("每页展示结果数量", [5, 10, 20, 50])
similarity_threshold = st.slider("相关性下限值（相似度）", 0.2, 0.4, 0.25, step=0.01)
current_page = st.number_input("页码", min_value=1, value=1, step=1)

col1, col2 = st.columns([1, 1])
search_triggered = col1.button("开始检索")
refine_triggered = col2.button("在结果中检索")

if (search_triggered or refine_triggered) and query.strip():
    #计时器
    start_time = time.time()
    #翻译：中文-->英文
    translated_query = GoogleTranslator(source='auto', target='en').translate(query)
    #进入数据库进行匹配
    if search_triggered:
        db = MySQLDocumentDB(password='123456')
        st.session_state.all_documents = db.fetch_all_documents()
        source_docs = st.session_state.all_documents
    else:
        source_docs = st.session_state.current_results

    documents = [{
        "id": doc["id"] if refine_triggered else doc["paper_id"],
        "title": doc["title"],
        "abstract": doc["abstract"],
        "authors": doc["authors"],
        "category": doc["category"],
        "published": doc["published"]
    } for doc in source_docs]

    searcher = SemanticSearcher(st.session_state.embedder, documents, field=field)
    all_results = searcher.search(translated_query, top_k=1000, sort_by=sort_by)
    filtered_results = [(pid, score) for pid, score in all_results if score >= similarity_threshold]

    result_ids_sorted = [pid for pid, _ in filtered_results]
    st.session_state.current_results = [next(doc for doc in documents if doc["id"] == pid) for pid in result_ids_sorted]
    st.session_state.filtered_result_scores = {pid: score for pid, score in filtered_results}
    st.session_state.search_done = True
    st.session_state.elapsed_time = time.time() - start_time

# 展示结果
if st.session_state.search_done and st.session_state.current_results:
    total_results = len(st.session_state.current_results)
    total_pages = (total_results + page_size - 1) // page_size
    if current_page > total_pages:
        st.warning(f"页码超过最大页数（共 {total_pages} 页），请重新选择。")
    else:
        st.markdown(f"⏱ 本次检索耗时: **{st.session_state.elapsed_time:.2f} 秒**")
        st.markdown(f"🔍 共找到 {total_results} 条相关结果，当前为第 {current_page} 页，每页显示 {page_size} 条：")

        start_idx = (current_page - 1) * page_size
        end_idx = start_idx + page_size
        page_results = st.session_state.current_results[start_idx:end_idx]

        db = MySQLDocumentDB(password='123456')
        for doc in page_results:
            score = st.session_state.filtered_result_scores.get(doc["id"], 0)
            st.markdown("---")
            st.markdown(f"📌 **{doc['title']}**")
            st.markdown(f"📅 发布时间: {doc['published']}")
            st.markdown(f"🧠 相似度: {score:.2f}")
            with st.expander("📖 查看摘要全文"):
                st.markdown(f"{doc['abstract']}")
            with st.expander("📘 GPT摘要查看"):
                try:
                    summary = db.fetch_summary_by_id(doc["id"])
                    st.markdown(summary if summary else "⚠️ 当前论文暂无摘要数据。")
                except Exception as e:
                    st.markdown(f"❌ 获取摘要失败: {e}")
