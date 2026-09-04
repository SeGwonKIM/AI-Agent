"""내 Todo 앱 — 데이터는 todo.db(SQLite 파일 하나)에 저장한다.

5강(데이터베이스) 실습. 설치할 것이 없다 — sqlite3 도 웹서버도 파이썬에 들어 있다.
better-sqlite3 처럼 빌드가 필요한 것을 쓰지 않으므로 윈도우에서 node-gyp 에러가 없다.

실행:  python app.py     →  http://localhost:8765

지키는 것
  · SQL 에 값을 이어 붙이지 않는다. 자리표(?)로만 넘긴다 (SQL 주입 방어)
  · todo.db 는 .gitignore 로 막는다 — 내 할 일 목록은 남의 저장소에 올릴 것이 아니다
"""

from __future__ import annotations

import json
import sqlite3
import sys
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "todo.db"
PORT = 8765

# ── 표 만들기 ────────────────────────────────────────────────
#  todos      : 할 일 (한 줄 = 한 건)
#  tags       : 태그 이름 (같은 이름이 두 번 생기지 않게 UNIQUE)
#  todo_tags  : 연결표 — 할 일과 태그는 다대다(N:M) 라서 사이에 표를 하나 둔다
SCHEMA = """
CREATE TABLE IF NOT EXISTS todos (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    title      TEXT    NOT NULL,
    done       INTEGER NOT NULL DEFAULT 0,
    due_date   TEXT,
    created_at TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS tags (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS todo_tags (
    todo_id INTEGER NOT NULL REFERENCES todos(id) ON DELETE CASCADE,
    tag_id  INTEGER NOT NULL REFERENCES tags(id)  ON DELETE CASCADE,
    PRIMARY KEY (todo_id, tag_id)
);

-- 자주 하는 질문에만 색인을 건다: "안 끝난 것을 마감일 순으로"
CREATE INDEX IF NOT EXISTS idx_todos_due ON todos(done, due_date);
"""


def connect() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")   # 연결표의 고리를 실제로 검사하게
    return con


def setup() -> None:
    first = not DB_PATH.exists()
    with connect() as con:
        con.executescript(SCHEMA)
    if first:
        print(f"  todo.db 를 새로 만들었습니다 ({DB_PATH})")


# ── 데이터 다루기 (CRUD) ─────────────────────────────────────
#  값은 전부 자리표(?)로 넘긴다. 문자열로 이어 붙이면 SQL 주입이 들어온다.

def _tags_of(con: sqlite3.Connection, todo_id: int) -> list[str]:
    rows = con.execute(
        "SELECT t.name FROM tags t "
        "JOIN todo_tags tt ON tt.tag_id = t.id "
        "WHERE tt.todo_id = ? ORDER BY t.name",
        (todo_id,),
    ).fetchall()
    return [r["name"] for r in rows]


def _set_tags(con: sqlite3.Connection, todo_id: int, names: list[str]) -> None:
    con.execute("DELETE FROM todo_tags WHERE todo_id = ?", (todo_id,))
    for raw in names:
        name = raw.strip().lstrip("#")
        if not name:
            continue
        con.execute("INSERT OR IGNORE INTO tags(name) VALUES (?)", (name,))
        tag_id = con.execute("SELECT id FROM tags WHERE name = ?", (name,)).fetchone()["id"]
        con.execute(
            "INSERT OR IGNORE INTO todo_tags(todo_id, tag_id) VALUES (?, ?)",
            (todo_id, tag_id),
        )


def list_todos(view: str = "all", q: str = "") -> list[dict]:
    """view: all(전부) · open(안 끝난 것) · today(오늘까지) · done(끝난 것)"""
    sql = "SELECT * FROM todos WHERE 1=1"
    args: list = []

    if view == "open":
        sql += " AND done = 0"
    elif view == "done":
        sql += " AND done = 1"
    elif view == "today":
        sql += " AND done = 0 AND due_date IS NOT NULL AND due_date <= ?"
        args.append(date.today().isoformat())

    if q:
        # LIKE 도 자리표로. 사용자가 친 글자를 명령에 이어 붙이지 않는다.
        sql += " AND title LIKE ?"
        args.append(f"%{q}%")

    # 마감일 있는 것 먼저, 그다음 최신순
    sql += " ORDER BY done, (due_date IS NULL), due_date, id DESC"

    with connect() as con:
        rows = con.execute(sql, args).fetchall()
        return [
            {
                "id": r["id"],
                "title": r["title"],
                "done": bool(r["done"]),
                "due_date": r["due_date"],
                "created_at": r["created_at"],
                "tags": _tags_of(con, r["id"]),
            }
            for r in rows
        ]


def create_todo(title: str, due_date: str | None, tags: list[str]) -> dict:
    title = (title or "").strip()
    if not title:
        raise ValueError("할 일 내용을 적어 주세요.")
    if len(title) > 200:
        raise ValueError("할 일은 200자까지 적을 수 있습니다.")
    due_date = _clean_date(due_date)

    with connect() as con:
        cur = con.execute(
            "INSERT INTO todos(title, done, due_date, created_at) VALUES (?, 0, ?, ?)",
            (title, due_date, datetime.now().isoformat(timespec="seconds")),
        )
        _set_tags(con, cur.lastrowid, tags or [])
    return {"id": cur.lastrowid}


def update_todo(todo_id: int, body: dict) -> None:
    with connect() as con:
        if "done" in body:
            con.execute("UPDATE todos SET done = ? WHERE id = ?",
                        (1 if body["done"] else 0, todo_id))
        if "title" in body:
            title = (body["title"] or "").strip()
            if title:
                con.execute("UPDATE todos SET title = ? WHERE id = ?", (title, todo_id))
        if "due_date" in body:
            con.execute("UPDATE todos SET due_date = ? WHERE id = ?",
                        (_clean_date(body["due_date"]), todo_id))
        if "tags" in body:
            _set_tags(con, todo_id, body["tags"] or [])


def delete_todo(todo_id: int) -> None:
    with connect() as con:
        con.execute("DELETE FROM todos WHERE id = ?", (todo_id,))


def stats() -> dict:
    with connect() as con:
        total = con.execute("SELECT COUNT(*) c FROM todos").fetchone()["c"]
        done = con.execute("SELECT COUNT(*) c FROM todos WHERE done = 1").fetchone()["c"]
        overdue = con.execute(
            "SELECT COUNT(*) c FROM todos WHERE done = 0 AND due_date IS NOT NULL AND due_date < ?",
            (date.today().isoformat(),),
        ).fetchone()["c"]
    return {"total": total, "done": done, "open": total - done, "overdue": overdue}


def _clean_date(value) -> str | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)).isoformat()
    except ValueError:
        raise ValueError("날짜는 2026-09-04 형태로 적어 주세요.")


# ── 웹서버 ───────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):
    server_version = "TodoApp/1.0"

    def log_message(self, fmt, *args):
        print(f"  {self.command} {self.path}")

    # --- 보내기 도우미 ---
    def _json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _file(self, name, ctype):
        path = ROOT / name
        if not path.is_file():
            return self._json({"error": "없는 파일"}, 404)
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    # --- 라우팅 ---
    def do_GET(self):
        url = urlparse(self.path)
        if url.path in ("/", "/index.html"):
            return self._file("index.html", "text/html; charset=utf-8")
        if url.path == "/api/todos":
            qs = parse_qs(url.query)
            return self._json({
                "todos": list_todos(qs.get("view", ["all"])[0], qs.get("q", [""])[0]),
                "stats": stats(),
            })
        return self._json({"error": "없는 주소"}, 404)

    def do_POST(self):
        if urlparse(self.path).path != "/api/todos":
            return self._json({"error": "없는 주소"}, 404)
        try:
            body = self._body()
            return self._json(create_todo(body.get("title"), body.get("due_date"), body.get("tags")), 201)
        except ValueError as e:
            return self._json({"error": str(e)}, 400)

    def do_PATCH(self):
        todo_id = self._id_from_path()
        if todo_id is None:
            return self._json({"error": "없는 주소"}, 404)
        try:
            update_todo(todo_id, self._body())
            return self._json({"ok": True})
        except ValueError as e:
            return self._json({"error": str(e)}, 400)

    def do_DELETE(self):
        todo_id = self._id_from_path()
        if todo_id is None:
            return self._json({"error": "없는 주소"}, 404)
        delete_todo(todo_id)
        return self._json({"ok": True})

    def _id_from_path(self) -> int | None:
        parts = urlparse(self.path).path.strip("/").split("/")
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "todos" and parts[2].isdigit():
            return int(parts[2])
        return None


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    print()
    print("  내 Todo 앱")
    print("  " + "-" * 34)
    setup()
    print(f"  브라우저에서 열기 : http://localhost:{PORT}")
    print("  끄려면 Ctrl+C")
    print()

    with ThreadingHTTPServer(("127.0.0.1", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  종료했습니다. 데이터는 todo.db 에 남아 있습니다.")


if __name__ == "__main__":
    main()
