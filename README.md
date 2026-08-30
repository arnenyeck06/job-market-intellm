# Job Market Intelligence Assistant

Job seekers spend hours manually scanning job boards — searching across dozens of postings to understand what skills are in demand, which companies are hiring, and what salaries to expect.

The Job Market Intelligence Assistant answers natural-language questions about the data engineering and AI job market, grounded in real job posting data with specific companies, salaries, and requirements cited in every answer.

This project was built as a capstone for [LLM Zoomcamp](https://github.com/DataTalksClub/llm-zoomcamp) — a free course about LLMs and RAG.

## Project overview

The assistant is a hybrid RAG application designed to help data professionals understand the job market.

The main use cases include:

1. **Skills research**: "What Python libraries do data engineering roles require?"
2. **Salary benchmarking**: "What is the average salary for LLM engineers in California?"
3. **Company research**: "Which companies are hiring the most data engineers right now?"
4. **Location analysis**: "What DE roles are available in Minnesota?"
5. **Role comparison**: "Compare data engineer vs ML engineer requirements"

## Dataset

Job postings are fetched from the [Adzuna API](https://developer.adzuna.com/) — free tier, 250 requests/month, structured JSON.

Keywords ingested by default:

- data engineer
- data scientist
- machine learning engineer
- AI engineer
- analytics engineer
- data architect
- MLOps engineer
- LLM engineer

You can find the synthetic test data in [`data/chunks.json`](data/chunks.json) (5 sample jobs for local testing without an Adzuna key).

## Technologies

- Python 3.12
- Docker and Docker Compose for containerization
- PostgreSQL + pgvector for vector storage
- minsearch for keyword search
- ONNX (Xenova/all-MiniLM-L6-v2, 384-dim) for embeddings
- Hybrid RRF (Reciprocal Rank Fusion) combining keyword + vector search
- FastAPI as the API interface
- Streamlit for the UI
- Kestra for daily ingestion orchestration
- Grafana for monitoring
- Anthropic Claude Sonnet as the LLM

## Preparation

1. Copy `.env.example` into `.env`:
```bash
   cp .env.example .env
```

2. Add your keys to `.env`:
ANTHROPIC_API_KEY=your-key-here
ADZUNA_APP_ID=your-app-id
ADZUNA_API_KEY=your-api-key
   - Anthropic key: [console.anthropic.com](https://console.anthropic.com/settings/keys)
   - Adzuna key: [developer.adzuna.com](https://developer.adzuna.com/) (free)

3. Install dependencies:
```bash
   pip install -r requirements.txt
```

4. Download the ONNX embedding model (~90MB, one time):
```bash
   python ingestion/download_model.py
```

## Running the application

### Start the stack

```bash
docker compose up -d
```

Starts:
- Postgres + pgvector on port **5434**
- Grafana on port **3002**

### Ingest job postings

```bash
export $(cat .env | xargs)
python ingest.py
```

Or with custom keywords:

```bash
python ingest.py --keywords "data engineer" "ML engineer" --pages 3
```

### Run the Streamlit UI

```bash
export TOKENIZERS_PARALLELISM=false
export $(cat .env | xargs)
streamlit run app.py
```

Open **http://localhost:8501**.

### Query via CLI

```bash
python query.py "what skills do data engineering roles require"
python query.py "highest paying ML jobs" --state "California"
python query.py "which companies are hiring DE roles" --search hybrid
```

### Set up Grafana monitoring

```bash
python monitoring/setup_grafana.py
```

Open **http://localhost:3002** (admin / admin).

## Using the application

| Tab | What you get |
|-----|-------------|
| 💬 Ask Assistant | Natural language Q&A grounded in job postings |
| 📊 Market Overview | Charts — jobs by state, salary ranges |
| 📋 Job Listings | Browse and filter indexed postings |

To ask a question: open the **💬 Ask Assistant** tab → pick an example or type your own → click **Ask**.

## Code

- [`ingestion/adzuna_client.py`](ingestion/adzuna_client.py) — fetch job postings from Adzuna API
- [`ingestion/parser.py`](ingestion/parser.py) — parse and chunk job descriptions
- [`ingestion/embedder.py`](ingestion/embedder.py) — ONNX embedding model
- [`search/minsearch.py`](search/minsearch.py) — TF-IDF keyword search
- [`search/vector_store.py`](search/vector_store.py) — pgvector cosine search
- [`search/hybrid.py`](search/hybrid.py) — RRF hybrid combiner
- [`agent/rag.py`](agent/rag.py) — RAG pipeline (retrieval + Claude generation)
- [`app.py`](app.py) — Streamlit UI
- [`ingest.py`](ingest.py) — CLI ingestion script
- [`query.py`](query.py) — CLI query script
- [`eval/`](eval/) — retrieval and LLM evaluation scripts
- [`kestra/`](kestra/) — Kestra daily ingestion DAG
- [`monitoring/`](monitoring/) — Grafana setup

## Experiments

Run retrieval and LLM evaluation after ingesting data:

```bash
# Generate ground truth Q&A pairs
python eval/generate_ground_truth.py

# Evaluate keyword vs vector vs hybrid
python eval/evaluate_retrieval.py

# Evaluate 2 prompt strategies with LLM-as-judge
python eval/evaluate_llm.py
```

### Retrieval evaluation results

| Method | Hit Rate | MRR |
|--------|----------|-----|
| Keyword (BM25) | TBD | TBD |
| Vector (cosine) | TBD | TBD |
| Hybrid RRF | TBD | TBD |

*Run `python eval/evaluate_retrieval.py` after ingesting data to populate this table.*

### LLM evaluation results

| Prompt | Relevance | Faithfulness | Combined |
|--------|-----------|--------------|----------|
| Prompt A (basic) | TBD | TBD | TBD |
| Prompt B (chain-of-thought) | TBD | TBD | TBD |

*Run `python eval/evaluate_llm.py` after ingesting data to populate this table.*

## Monitoring

Grafana is accessible at [localhost:3002](http://localhost:3002):
- Login: `admin`
- Password: `admin`

Dashboard panels:
1. Total jobs indexed
2. Total queries
3. Positive feedback %
4. Jobs by category (pie chart)
5. Queries over time (time series)
6. Most asked questions (table)

## Acknowledgements

Built as part of [LLM Zoomcamp](https://github.com/DataTalksClub/llm-zoomcamp) by DataTalksClub.

Data sourced from [Adzuna API](https://developer.adzuna.com/) — free tier available.
