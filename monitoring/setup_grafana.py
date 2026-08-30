"""
setup_grafana.py
Configure Grafana datasource and dashboard.
Run once after docker compose up.

Usage:
  python monitoring/setup_grafana.py
"""

import requests

GRAFANA_URL = "http://localhost:3002"
GRAFANA_AUTH = ("admin", "admin")


def setup_datasource():
    ds = {
        "name": "Job Market Postgres",
        "type": "postgres",
        "url": "postgres:5432",
        "database": "job_market",
        "user": "jobs",
        "secureJsonData": {"password": "jobs123"},
        "jsonData": {"sslmode": "disable"}
    }
    r = requests.post(f"{GRAFANA_URL}/api/datasources", auth=GRAFANA_AUTH, json=ds)
    print(f"Datasource: {r.status_code}")
    return r.json().get("datasource", {}).get("uid", "")


def setup_dashboard():
    dashboard = {
        "dashboard": {
            "title": "Job Market Intelligence Monitor",
            "panels": [
                {"title": "Total Jobs Indexed", "type": "stat", "gridPos": {"x": 0, "y": 0, "w": 6, "h": 4},
                 "targets": [{"rawSql": "SELECT COUNT(*) FROM jobs", "format": "table"}]},
                {"title": "Total Queries", "type": "stat", "gridPos": {"x": 6, "y": 0, "w": 6, "h": 4},
                 "targets": [{"rawSql": "SELECT COUNT(*) FROM query_feedback", "format": "table"}]},
                {"title": "Positive Feedback %", "type": "gauge", "gridPos": {"x": 12, "y": 0, "w": 6, "h": 4},
                 "targets": [{"rawSql": "SELECT ROUND(100.0*SUM(CASE WHEN feedback=1 THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0),1) FROM query_feedback", "format": "table"}]},
                {"title": "Jobs by Category", "type": "piechart", "gridPos": {"x": 0, "y": 4, "w": 8, "h": 6},
                 "targets": [{"rawSql": "SELECT category, COUNT(*) FROM jobs GROUP BY category ORDER BY COUNT(*) DESC", "format": "table"}]},
                {"title": "Queries Over Time", "type": "timeseries", "gridPos": {"x": 8, "y": 4, "w": 16, "h": 6},
                 "targets": [{"rawSql": "SELECT created_at as time, COUNT(*) FROM query_feedback GROUP BY 1 ORDER BY 1", "format": "time_series"}]},
                {"title": "Most Asked Questions", "type": "table", "gridPos": {"x": 0, "y": 10, "w": 24, "h": 6},
                 "targets": [{"rawSql": "SELECT query, COUNT(*) as count FROM query_feedback GROUP BY query ORDER BY count DESC LIMIT 10", "format": "table"}]},
            ]
        },
        "overwrite": True
    }
    r = requests.post(f"{GRAFANA_URL}/api/dashboards/db", auth=GRAFANA_AUTH, json=dashboard)
    print(f"Dashboard: {r.status_code}")


if __name__ == "__main__":
    setup_datasource()
    setup_dashboard()
    print(f"Done. Open: {GRAFANA_URL}")
