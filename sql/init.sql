CREATE EXTENSION IF NOT EXISTS vector;

-- Raw job postings
CREATE TABLE IF NOT EXISTS jobs (
    id              TEXT PRIMARY KEY,
    title           TEXT,
    company         TEXT,
    location        TEXT,
    state           TEXT,
    country         TEXT DEFAULT 'us',
    salary_min      FLOAT,
    salary_max      FLOAT,
    contract_type   TEXT,
    category        TEXT,
    description     TEXT,
    url             TEXT,
    created         TIMESTAMP,
    ingested_at     TIMESTAMP DEFAULT NOW()
);

-- Chunked job descriptions for RAG
CREATE TABLE IF NOT EXISTS chunks (
    id          TEXT PRIMARY KEY,
    job_id      TEXT REFERENCES jobs(id),
    title       TEXT,
    company     TEXT,
    location    TEXT,
    state       TEXT,
    category    TEXT,
    salary_min  FLOAT,
    salary_max  FLOAT,
    text        TEXT NOT NULL,
    embedding   vector(384)
);

CREATE INDEX IF NOT EXISTS chunks_embedding_idx
    ON chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS chunks_category_idx ON chunks (category);
CREATE INDEX IF NOT EXISTS chunks_state_idx ON chunks (state);
CREATE INDEX IF NOT EXISTS chunks_title_idx ON chunks (title);

-- Skills extraction table
CREATE TABLE IF NOT EXISTS skills (
    id          SERIAL PRIMARY KEY,
    job_id      TEXT REFERENCES jobs(id),
    skill       TEXT,
    category    TEXT
);

CREATE INDEX IF NOT EXISTS skills_skill_idx ON skills (skill);

-- User feedback
CREATE TABLE IF NOT EXISTS query_feedback (
    id          SERIAL PRIMARY KEY,
    query       TEXT,
    answer      TEXT,
    feedback    INTEGER,
    created_at  TIMESTAMP DEFAULT NOW()
);
