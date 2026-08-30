import os
import psycopg2
import psycopg2.extras


def get_conn():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5434"),
        dbname=os.getenv("POSTGRES_DB", "job_market"),
        user=os.getenv("POSTGRES_USER", "jobs"),
        password=os.getenv("POSTGRES_PASSWORD", "jobs123"),
    )


def vector_search(query_embedding, state=None, category=None, num_results=10):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    filters = []
    params = [str(query_embedding)]
    if state:
        filters.append("state ILIKE %s")
        params.append(f"%{state}%")
    if category:
        filters.append("category ILIKE %s")
        params.append(f"%{category}%")
    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    params.extend([str(query_embedding), num_results])
    cur.execute(f"""
        SELECT id, job_id, title, company, location, state,
               category, salary_min, salary_max, text,
               1 - (embedding <=> %s::vector) AS _score
        FROM chunks {where}
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """, params)
    results = [dict(r) for r in cur.fetchall()]
    cur.close()
    conn.close()
    return results
