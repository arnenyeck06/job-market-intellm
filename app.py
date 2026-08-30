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

st.set_page_config(page_title="Job Market Intelligence", page_icon="💼", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #f8f7f4; color: #1a1a1a; }
    section[data-testid="stSidebar"] { background-color: #f1efe8; border-right: 1px solid #d3d1c7; }
    .stTabs [data-baseweb="tab-list"] { background-color: #f8f7f4; border-bottom: 1px solid #d3d1c7; }
    .stTabs [data-baseweb="tab"] { color: #888780; font-size: 13px; }
    .stTabs [aria-selected="true"] { color: #185fa5 !important; border-bottom: 2px solid #185fa5 !important; font-weight: 500 !important; }
    .stTabs [data-baseweb="tab-panel"] { background-color: #f8f7f4; }
    .stButton > button { background-color: #185fa5 !important; color: #fff !important; border: none !important; border-radius: 6px !important; font-weight: 500 !important; }
    .stButton > button:hover { background-color: #0c447c !important; }
    div[data-testid="stMetric"] { background: #ffffff; border: 0.5px solid #d3d1c7; border-radius: 8px; padding: 14px; }
    div[data-testid="stMetric"] label { color: #888780 !important; font-size: 11px !important; letter-spacing: 1px !important; text-transform: uppercase !important; }
    .stSelectbox > div > div { background: #ffffff !important; border: 0.5px solid #d3d1c7 !important; color: #1a1a1a !important; }
    .stTextInput > div > div > input { background: #ffffff !important; border: 0.5px solid #d3d1c7 !important; color: #1a1a1a !important; }
    .stTextInput > div > div > input:focus { border-color: #185fa5 !important; }
    .stRadio > div { gap: 8px; }
    .stDataFrame { background: #ffffff; border-radius: 8px; }
    .stSlider > div > div > div { background: #185fa5 !important; }
</style>
""", unsafe_allow_html=True)

st.title("💼 Job Market Intelligence Assistant")
st.caption("Insights from data engineering and AI job postings — powered by hybrid RAG and Claude")


def store_feedback(query: str, answer: str, feedback: int):
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
    st.markdown("### Filters")
    states = ["All"] + sorted(set(c.get("state", "") for c in chunks if c.get("state")))
    selected_state = st.selectbox("State", states)
    categories = ["All"] + sorted(set(c.get("category", "") for c in chunks if c.get("category")))
    selected_category = st.selectbox("Category", categories)
    search_mode = st.radio("Search mode", ["hybrid", "keyword", "vector"])
    num_results = st.slider("Results", 3, 10, 5)
    st.markdown("---")
    col1, col2 = st.columns(2)
    col1.metric("Jobs", len(chunks))
    col2.metric("States", len(set(c.get("state", "") for c in chunks if c.get("state"))))

# Tabs
tab1, tab2, tab3 = st.tabs(["💬 Ask assistant", "📊 Market overview", "📋 Job listings"])

with tab1:
    examples = [
        "What skills do data engineering roles require?",
        "Which companies pay the most for ML engineers?",
        "What is the average salary for LLM engineers?",
        "What are the top skills needed for remote DE roles?",
        "Compare data engineer vs ML engineer requirements",
    ]
    example = st.selectbox("Try an example question", [""] + examples)
    question = st.text_input(
        "Or ask your own question",
        value=example,
        placeholder="e.g. What Python skills are most in demand?"
    )

    if st.button("Ask") and question:
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
            st.caption(f"Query expanded for better retrieval")

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
                f'<div style="background:#e6f1fb;border-left:3px solid #185fa5;'
                f'padding:16px;border-radius:0 8px 8px 0;color:#1a1a1a;'
                f'line-height:1.8;font-size:14px">{result["answer"]}</div>',
                unsafe_allow_html=True
            )

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("**Sources**")
            for s in result["sources"]:
                salary = f" | ${s['salary_min']:,.0f}–${s['salary_max']:,.0f}" if s.get("salary_min") else ""
                st.markdown(
                    f'<div style="background:#fff;border:0.5px solid #d3d1c7;'
                    f'border-radius:6px;padding:8px 12px;margin-bottom:6px;font-size:13px">'
                    f'<strong>{s["title"]}</strong> · {s["company"]} — {s["location"]}{salary}</div>',
                    unsafe_allow_html=True
                )

            col1, col2 = st.columns(2)
            col1.metric("Input tokens", result["input_tokens"])
            col2.metric("Output tokens", result["output_tokens"])

            st.markdown("---")
            st.markdown("**Was this helpful?**")
            c1, c2, _ = st.columns([1, 1, 4])
            if c1.button("👍 Yes"):
                store_feedback(question, result["answer"], 1)
                st.success("Thanks for the feedback!")
            if c2.button("👎 No"):
                store_feedback(question, result["answer"], -1)
                st.info("Noted — thanks!")

with tab2:
    if chunks:
        df = pd.DataFrame(chunks)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Jobs indexed", len(chunks))
        col2.metric("Companies", df["company"].nunique())
        col3.metric("States", df["state"].nunique())
        avg_sal = df[df["salary_max"].notna()]["salary_max"].mean()
        col4.metric("Avg max salary", f"${avg_sal:,.0f}" if avg_sal else "N/A")

        st.markdown("<br>", unsafe_allow_html=True)

        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("#### Jobs by state")
            state_counts = df["state"].value_counts().head(8)
            st.bar_chart(state_counts)

        with col_right:
            st.markdown("#### Salary ranges")
            salary_df = df[df["salary_min"].notna()][
                ["title", "company", "salary_min", "salary_max"]
            ].drop_duplicates().sort_values("salary_max", ascending=False)
            if not salary_df.empty:
                st.dataframe(salary_df, use_container_width=True, hide_index=True)
    else:
        st.info("No data loaded. Run ingest.py first.")

with tab3:
    if chunks:
        df = pd.DataFrame(chunks)
        search_filter = st.text_input(
            "Filter listings",
            placeholder="e.g. Python, Spark, Remote"
        )
        if search_filter:
            df = df[df["text"].str.contains(search_filter, case=False, na=False)]

        display_df = df[["title", "company", "location", "state", "salary_min", "salary_max"]]\
            .drop_duplicates().reset_index(drop=True)
        st.dataframe(display_df, use_container_width=True, height=400, hide_index=True)
        st.caption(f"{len(display_df)} postings shown")
    else:
        st.info("No data loaded. Run ingest.py first.")

st.divider()
col1, col2, col3 = st.columns(3)
col1.caption("Data: Adzuna API")
col2.caption("Search: Hybrid RRF + re-ranking")
col3.caption("LLM: Claude Sonnet")