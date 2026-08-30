"""
Streamlit UI for Job Market Intelligence Assistant.
"""

import streamlit as st
import json
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
os.environ["TOKENIZERS_PARALLELISM"] = "false"

st.set_page_config(
    page_title="Job Market Intelligence",
    page_icon="💼",
    layout="wide"
)

st.markdown("""
<style>
    .stApp { background-color: #0f0f0f; color: #ffffff; }
    section[data-testid="stSidebar"] { background-color: #1a1a1a; }
    .stTabs [data-baseweb="tab"] { color: #888; font-size: 12px; letter-spacing: 1px; }
    .stTabs [aria-selected="true"] { color: #00d4ff !important; border-bottom: 2px solid #00d4ff !important; }
    .stButton > button { background-color: #00d4ff !important; color: #000 !important; font-weight: 700 !important; }
    div[data-testid="stMetric"] { background-color: #1a1a1a; border-radius: 8px; padding: 12px; border: 1px solid #2a2a2a; }
</style>
""", unsafe_allow_html=True)

st.title("💼 Job Market Intelligence Assistant")
st.caption("Real-time insights from data engineering and AI job postings")


def store_feedback(query: str, answer: str, feedback: int):
    """Store user feedback to Postgres."""
    try:
        from ingestion.db_loader import get_conn
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO query_feedback (query, answer, feedback) VALUES (%s, %s, %s)",
            (query, answer[:500], feedback)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        st.error(f"Feedback error: {e}")


@st.cache_data
def load_chunks():
    try:
        with open("data/chunks.json") as f:
            return json.load(f)
    except Exception:
        return []


chunks = load_chunks()

from search.minsearch import Index
from ingestion.embedder import Embedder


@st.cache_resource
def build_search():
    idx = Index(text_fields=["text"], keyword_fields=["state", "category", "title"])
    idx.fit(chunks)
    emb = Embedder()
    return idx, emb


index, embedder = build_search()

# Sidebar
with st.sidebar:
    st.markdown("## 🔍 Filters")
    states = ["All"] + sorted(set(c.get("state", "") for c in chunks if c.get("state")))
    selected_state = st.selectbox("State", states)
    categories = ["All"] + sorted(set(c.get("category", "") for c in chunks if c.get("category")))
    selected_category = st.selectbox("Category", categories)
    search_mode = st.radio("Search mode", ["hybrid", "keyword", "vector"])
    num_results = st.slider("Results", 3, 10, 5)
    st.markdown("---")
    st.markdown(f"**{len(chunks)}** job chunks indexed")

# Tabs
tab1, tab2, tab3 = st.tabs(["💬 ASK ASSISTANT", "📊 MARKET OVERVIEW", "📋 JOB LISTINGS"])

with tab1:
    examples = [
        "What skills do data engineering roles require?",
        "Which companies pay the most for ML engineers?",
        "What is the average salary for LLM engineers?",
        "What are the top skills needed for remote DE roles?",
        "Compare data engineer vs ML engineer requirements",
    ]
    example = st.selectbox("Try an example", [""] + examples)
    question = st.text_input("Or ask your own question", value=example,
                             placeholder="e.g. What Python skills are most in demand?")

    if st.button("Ask", type="primary") and question:
        from search.hybrid import hybrid_search
        from search.vector_store import vector_search
        from search.reranker import rerank
        from agent.rag import answer_query
        from agent.query_rewriter import rewrite_query

        state = None if selected_state == "All" else selected_state
        category = None if selected_category == "All" else selected_category

        # Step 1: Query rewriting
        rewritten = rewrite_query(question)
        if rewritten != question:
            st.caption(f"🔄 Query expanded: *{rewritten[:80]}...*")

        with st.spinner("Searching job market data..."):
            if search_mode == "hybrid":
                retrieved = hybrid_search(rewritten, index, embedder, state=state,
                                         category=category, num_results=num_results * 2)
            elif search_mode == "vector":
                q_vec = embedder.encode(rewritten)
                retrieved = vector_search(q_vec, state=state, category=category,
                                         num_results=num_results * 2)
            else:
                filter_dict = {}
                if state:
                    filter_dict["state"] = state
                retrieved = index.search(rewritten, filter_dict=filter_dict,
                                        num_results=num_results * 2)

            # Step 2: Re-rank
            retrieved = rerank(rewritten, retrieved, embedder, top_n=num_results)

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            st.warning("Set ANTHROPIC_API_KEY in .env to enable AI answers.")
            st.markdown("**Retrieved job postings:**")
            for r in retrieved:
                salary = f" | ${r['salary_min']:,.0f}–${r['salary_max']:,.0f}" if r.get("salary_min") else ""
                st.markdown(f"- **{r['title']}** at {r['company']} — {r['location']}{salary}")
        else:
            with st.spinner("Generating answer..."):
cat > app.py << 'EOF'
"""
Streamlit UI for Job Market Intelligence Assistant.
"""

import streamlit as st
import json
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
os.environ["TOKENIZERS_PARALLELISM"] = "false"

st.set_page_config(
    page_title="Job Market Intelligence",
    page_icon="💼",
    layout="wide"
)

st.markdown("""
<style>
    .stApp { background-color: #0f0f0f; color: #ffffff; }
    section[data-testid="stSidebar"] { background-color: #1a1a1a; }
    .stTabs [data-baseweb="tab"] { color: #888; font-size: 12px; letter-spacing: 1px; }
    .stTabs [aria-selected="true"] { color: #00d4ff !important; border-bottom: 2px solid #00d4ff !important; }
    .stButton > button { background-color: #00d4ff !important; color: #000 !important; font-weight: 700 !important; }
    div[data-testid="stMetric"] { background-color: #1a1a1a; border-radius: 8px; padding: 12px; border: 1px solid #2a2a2a; }
</style>
""", unsafe_allow_html=True)

st.title("💼 Job Market Intelligence Assistant")
st.caption("Real-time insights from data engineering and AI job postings")


def store_feedback(query: str, answer: str, feedback: int):
    """Store user feedback to Postgres."""
    try:
        from ingestion.db_loader import get_conn
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO query_feedback (query, answer, feedback) VALUES (%s, %s, %s)",
            (query, answer[:500], feedback)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        st.error(f"Feedback error: {e}")


@st.cache_data
def load_chunks():
    try:
        with open("data/chunks.json") as f:
            return json.load(f)
    except Exception:
        return []


chunks = load_chunks()

from search.minsearch import Index
from ingestion.embedder import Embedder


@st.cache_resource
def build_search():
    idx = Index(text_fields=["text"], keyword_fields=["state", "category", "title"])
    idx.fit(chunks)
    emb = Embedder()
    return idx, emb


index, embedder = build_search()

# Sidebar
with st.sidebar:
    st.markdown("## 🔍 Filters")
    states = ["All"] + sorted(set(c.get("state", "") for c in chunks if c.get("state")))
    selected_state = st.selectbox("State", states)
    categories = ["All"] + sorted(set(c.get("category", "") for c in chunks if c.get("category")))
    selected_category = st.selectbox("Category", categories)
    search_mode = st.radio("Search mode", ["hybrid", "keyword", "vector"])
    num_results = st.slider("Results", 3, 10, 5)
    st.markdown("---")
    st.markdown(f"**{len(chunks)}** job chunks indexed")

# Tabs
tab1, tab2, tab3 = st.tabs(["💬 ASK ASSISTANT", "📊 MARKET OVERVIEW", "📋 JOB LISTINGS"])

with tab1:
    examples = [
        "What skills do data engineering roles require?",
        "Which companies pay the most for ML engineers?",
        "What is the average salary for LLM engineers?",
        "What are the top skills needed for remote DE roles?",
        "Compare data engineer vs ML engineer requirements",
    ]
    example = st.selectbox("Try an example", [""] + examples)
    question = st.text_input("Or ask your own question", value=example,
                             placeholder="e.g. What Python skills are most in demand?")

    if st.button("Ask", type="primary") and question:
        from search.hybrid import hybrid_search
        from search.vector_store import vector_search
        from search.reranker import rerank
        from agent.rag import answer_query
        from agent.query_rewriter import rewrite_query

        state = None if selected_state == "All" else selected_state
        category = None if selected_category == "All" else selected_category

        # Step 1: Query rewriting
        rewritten = rewrite_query(question)
        if rewritten != question:
            st.caption(f"🔄 Query expanded: *{rewritten[:80]}...*")

        with st.spinner("Searching job market data..."):
            if search_mode == "hybrid":
                retrieved = hybrid_search(rewritten, index, embedder, state=state,
                                         category=category, num_results=num_results * 2)
            elif search_mode == "vector":
                q_vec = embedder.encode(rewritten)
                retrieved = vector_search(q_vec, state=state, category=category,
                                         num_results=num_results * 2)
            else:
                filter_dict = {}
                if state:
                    filter_dict["state"] = state
                retrieved = index.search(rewritten, filter_dict=filter_dict,
                                        num_results=num_results * 2)

            # Step 2: Re-rank
            retrieved = rerank(rewritten, retrieved, embedder, top_n=num_results)

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            st.warning("Set ANTHROPIC_API_KEY in .env to enable AI answers.")
            st.markdown("**Retrieved job postings:**")
            for r in retrieved:
                salary = f" | ${r['salary_min']:,.0f}–${r['salary_max']:,.0f}" if r.get("salary_min") else ""
                st.markdown(f"- **{r['title']}** at {r['company']} — {r['location']}{salary}")
        else:
            with st.spinner("Generating answer..."):
                result = answer_query(question, retrieved)

            st.markdown("### Answer")
            st.markdown(
                f'<div style="background:#0a1a0a;border-left:3px solid #00d4ff;'
                f'padding:16px;border-radius:0 8px 8px 0;color:#eee;line-height:1.8">'
                f'{result["answer"]}</div>',
                unsafe_allow_html=True
            )

            st.markdown("**Sources**")
            for s in result["sources"]:
                salary = f" | ${s['salary_min']:,.0f}–${s['salary_max']:,.0f}" if s.get("salary_min") else ""
                st.markdown(f"- **{s['title']}** at {s['company']} — {s['location']}{salary}")

            col1, col2 = st.columns(2)
            col1.metric("Input tokens", result["input_tokens"])
            col2.metric("Output tokens", result["output_tokens"])

            # Feedback — stores to Postgres
            st.markdown("---")
            st.markdown("**Was this helpful?**")
            c1, c2 = st.columns(2)
            if c1.button("👍 Yes"):
                store_feedback(question, result["answer"], 1)
                st.success("Thanks!")
            if c2.button("👎 No"):
                store_feedback(question, result["answer"], -1)
                st.info("Thanks for the feedback!")

with tab2:
    if chunks:
        df = pd.DataFrame(chunks)
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Jobs Indexed", len(chunks))
        col2.metric("Companies", df["company"].nunique())
        col3.metric("States", df["state"].nunique())

        st.markdown("#### Jobs by State")
        state_counts = df["state"].value_counts().head(10)
        st.bar_chart(state_counts)

        st.markdown("#### Salary Ranges")
        salary_df = df[df["salary_min"].notna()][
            ["title", "company", "location", "salary_min", "salary_max"]
        ]
        if not salary_df.empty:
            st.dataframe(
                salary_df.sort_values("salary_max", ascending=False),
                use_container_width=True
            )
    else:
        st.info("No data loaded. Run ingest.py first.")

with tab3:
    if chunks:
        df = pd.DataFrame(chunks)
        search_filter = st.text_input("Filter listings", placeholder="e.g. Python, Spark, Remote")
        if search_filter:
            df = df[df["text"].str.contains(search_filter, case=False, na=False)]
        st.dataframe(
            df[["title", "company", "location", "state", "salary_min", "salary_max"]].drop_duplicates(),
            use_container_width=True,
            height=400
        )
    else:
        st.info("No data loaded. Run ingest.py first.")

st.divider()
col1, col2, col3 = st.columns(3)
col1.caption("📡 Data: Adzuna API")
col2.caption("🔍 Search: Hybrid RRF + Re-ranking")
col3.caption("🤖 LLM: Claude Sonnet")
