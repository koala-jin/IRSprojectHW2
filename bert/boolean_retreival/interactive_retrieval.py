import streamlit as st
import re
from datetime import datetime
from boolean_retrieval import PaperRetriever, suggest_category, CATEGORY_TAXONOMY

# 初始化检索器
retriever = PaperRetriever()

# 页面配置
st.set_page_config(page_title="论文检索系统", layout="wide")

# 会话状态初始化
if 'conditions' not in st.session_state:
    st.session_state.conditions = [{
        'logic_op': 'AND',
        'field': '主题分类',
        'value': ''
    }]

# 页面标题
st.title("📑 论文智能检索系统")

# 主检索面板
with st.container():
    st.header("🔍 构建检索条件")

    # 条件管理按钮
    cols = st.columns([3, 3, 10])
    with cols[0]:
        if st.button("➕ 添加条件", help="最多支持5个条件"):
            if len(st.session_state.conditions) < 5:
                st.session_state.conditions.append({
                    'logic_op': 'AND',
                    'field': '主题分类',
                    'value': ''
                })
    with cols[1]:
        if len(st.session_state.conditions) > 1 and st.button("➖ 删除条件"):
            st.session_state.conditions.pop()

    # 动态生成条件输入
    query_parts = []
    params = []
    for idx, cond in enumerate(st.session_state.conditions):
        cols = st.columns([2, 3, 12])

        # 逻辑运算符选择（首行不显示）
        with cols[0]:
            if idx > 0:
                logic_op = st.selectbox(
                    "逻辑关系",
                    ["AND", "OR", "NOT"],
                    index=0,
                    key=f"logic_{idx}",
                    label_visibility="collapsed"
                )
                cond['logic_op'] = logic_op
            else:
                st.write("")  # 占位对齐

        # 字段选择
        with cols[1]:
            field = st.selectbox(
                "字段选择",
                ["主题分类", "关键词", "作者", "发表年份"],
                key=f"field_{idx}",
                label_visibility="collapsed"
            )
            cond['field'] = field

        # 值输入
        with cols[2]:
            if field == "主题分类":
                value = st.text_input(
                    "分类名称",
                    key=f"value_{idx}",
                    placeholder="输入分类名称..."
                )
                # 自动提示
                if value:
                    suggestions = suggest_category(value)
                    if suggestions:
                        st.caption(f"可能匹配：{', '.join(suggestions)}")

            elif field == "发表年份":
                value = st.text_input(
                    "年份",
                    key=f"value_{idx}",
                    placeholder="格式：YYYY",
                    max_chars=4
                )

            else:  # 关键词/作者
                value = st.text_input(
                    "输入值",
                    key=f"value_{idx}",
                    placeholder=f"输入{field}..."
                )

            cond['value'] = value.strip()

# 执行检索
if st.button("🚀 开始检索", type="primary"):
    try:
        # 构建查询表达式
        query = []
        for idx, cond in enumerate(st.session_state.conditions):
            if not cond['value']:
                continue

            # 生成条件表达式
            expr = f"{cond['field']}:{cond['value']}"
            if idx > 0:
                expr = f"{cond['logic_op']} {expr}"

            query.append(expr)

        # 执行检索
        if query:
            results = retriever.advanced_search(" ".join(query))
            st.session_state.base_results = results
            st.session_state.filtered_results = results
            st.success(f"找到 {len(results)} 篇论文")
        else:
            st.warning("请输入有效的检索条件")
    except Exception as e:
        st.error(f"检索失败：{str(e)}")

# interactive_retrieval.py 修改以下部分
if 'base_results' in st.session_state:
    # 生成筛选选项时添加空值处理
    categories = list({
        p.get('category', '未知分类')
        for p in st.session_state.base_results
    })

    authors = sorted({
        a.strip()
        for p in st.session_state.base_results
        for a in re.split(r',|，', p.get('authors', ''))
        if a.strip()
    })

    # 日期处理增强
    min_date = min(
        datetime.strptime(str(p.get('published', '2000-01-01')), "%Y-%m-%d").date()
        for p in st.session_state.base_results
    )
    max_date = max(
        datetime.strptime(str(p.get('published', '2100-01-01')), "%Y-%m-%d").date()
        for p in st.session_state.base_results
    )

    with st.expander("🔎 在结果中筛选", expanded=True):
        cols = st.columns([3, 3, 2, 2])

        with cols[0]:
            sel_cats = st.multiselect(
                "主题分类（包含子类）",
                options=categories,
                format_func=lambda x: CATEGORY_TAXONOMY.get(x, {}).get('zh_name', x)
            )

        with cols[1]:
            sel_authors = st.multiselect(
                "作者（按字母排序）",
                options=authors,
                format_func=lambda x: x.title()
            )

        with cols[2]:
            start_date = st.date_input(
                "起始日期",
                value=min_date,
                min_value=min_date,
                max_value=max_date
            )

        with cols[3]:
            end_date = st.date_input(
                "结束日期",
                value=max_date,
                min_value=min_date,
                max_value=max_date
            )

        if st.button("应用筛选条件", key="apply_filter"):
            filtered = retriever.refine_search(
                base_results=st.session_state.base_results,
                categories=sel_cats,
                authors=sel_authors,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d")
            )
            st.session_state.filtered_results = filtered
            st.rerun()

    # 显示结果
    st.subheader(f"当前结果（{len(st.session_state.filtered_results)} 篇）")
    for idx, paper in enumerate(st.session_state.filtered_results, 1):
        with st.expander(f"{idx}. {paper['title']}"):
            st.markdown(f"""
            **分类**: `{paper['category']}`  
            **作者**: {', '.join(paper['authors'].split(',')[:3])}...  
            **发表时间**: {paper['published']}  
            **摘要**: {paper['abstract'][:200]}...
            """)
            if paper['pdf_url']:
                st.link_button("查看全文", paper['pdf_url'])

# 分类说明（需要补充CATEGORY_TAXONOMY的显示）