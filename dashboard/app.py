import os
import sqlite3
import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

DB_PATH = os.getenv("DB_PATH", "data.db")
BASE_DIR = os.path.dirname(__file__)
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True) if "/" in DB_PATH else None

app = FastAPI()
templates = Jinja2Templates(directory=TEMPLATES_DIR)

def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        repo TEXT,
        number INTEGER,
        type TEXT,            -- "Issue" or "Pull Request"
        title TEXT,
        summary TEXT,
        label TEXT,
        score REAL,
        created_at TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

@app.post("/ingest")
async def ingest(item: dict):
    # Required fields (same for issues and PRs)
    required = ["repo", "number", "type", "summary", "label", "score", "title"]
    if any(k not in item for k in required):
        raise HTTPException(status_code=400, detail="bad payload")

    # Normalize type
    # In your dashboard app.py
    issue_type = "Pull Request" if item["type"].lower().startswith("pull") else "issue"

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO events(repo,number,type,title,summary,label,score,created_at) VALUES(?,?,?,?,?,?,?,?)",
        (
            item["repo"],
            int(item["number"]),
            issue_type,
            item["title"],
            item["summary"],
            item["label"],
            float(item["score"]),
            datetime.datetime.utcnow().isoformat() + "Z",
        ),
    )
    conn.commit()
    conn.close()
    return {"ok": True}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT repo, number, type, title, label, score, summary, created_at FROM events ORDER BY id DESC LIMIT 200"
    )
    rows = cur.fetchall()
    conn.close()
    return templates.TemplateResponse("index.html", {"request": request, "rows": rows})
