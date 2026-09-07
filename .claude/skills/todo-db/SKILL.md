---
name: todo-db
description: 내 컴퓨터의 Todo 앱 데이터베이스(todo_app/todo.db)를 조회하거나 다룬다. "할 일 목록 보여줘", "todo.db 어디 있어", "안 끝난 할 일", "태그별로 보여줘", "todo 앱 띄워줘" 같은 요청에 사용한다.
---

# Todo 앱 DB 다루기

5강(데이터베이스) 실습으로 만든 로컬 Todo 앱의 SQLite 파일을 읽고 정리해서 보여준다.

## 파일 위치

| | 경로 |
|---|---|
| DB | `todo_app/todo.db` (= `C:\AI-Agent\todo_app\todo.db`) |
| 백엔드 | `todo_app/app.py` (파이썬 내장 웹서버 + `sqlite3`) |
| 프론트 | `todo_app/index.html` |
| 설명 | `todo_app/README.md` |

`todo.db` 는 `todo_app/.gitignore` 에 들어 있어 **깃에 올라가지 않는다** — 이 컴퓨터에만 있는
로컬 파일이다. 그러므로 다른 곳에서 클론한 저장소에는 이 파일이 없다.

## 데이터 모양

```sql
todos      (id, title, done, due_date, created_at)
tags       (id, name)
todo_tags  (todo_id, tag_id)   -- 다대다 연결표
```

- `done` 은 0/1 정수. `due_date`, `created_at` 은 TEXT (ISO 8601, 예: `2026-09-04T18:14:52`).
- 할 일 ↔ 태그는 **N:M** 이라 `todo_tags` 를 거쳐야 한다.

## 조회하는 방법 (중요: 인코딩)

Bash 툴에서 파이썬으로 조회할 때 **반드시 `PYTHONIOENCODING=utf-8` 을 붙인다.**
붙이지 않으면 윈도우 콘솔 코드페이지 때문에 한글이 `5�� �����ϱ�` 처럼 깨져 나온다.

전체 할 일 + 태그를 한 번에 뽑는 기본 쿼리:

```bash
PYTHONIOENCODING=utf-8 python -c "
import sqlite3
c = sqlite3.connect('todo_app/todo.db')
for r in c.execute('''
  SELECT t.id, t.title, t.done, t.due_date, t.created_at,
         (SELECT group_concat(g.name, ', ')
            FROM todo_tags j JOIN tags g ON g.id = j.tag_id
           WHERE j.todo_id = t.id)
    FROM todos t ORDER BY t.id'''):
    print(r)
"
```

응용:
- 안 끝난 것만 → `WHERE t.done = 0`
- 오늘까지 마감 → `WHERE t.done = 0 AND t.due_date <= date('now')`
- 특정 태그 → `WHERE g.name = ?` 로 조인 (값은 **자리표 `?`** 로만 넘긴다, 문자열 이어붙이기 금지)

## 결과를 보여줄 때

- 마크다운 표로 정리한다: `# / 할 일 / 상태 / 마감일 / 태그 / 등록일`.
- 상태는 `⬜ 미완료` / `✅ 완료`, 마감일이 `NULL` 이면 `없음`.
- 마지막에 총 건수를 한 줄로 적는다.

## 지킬 것

- **기본은 읽기 전용.** `INSERT`/`UPDATE`/`DELETE` 는 사용자가 명확히 요청했을 때만 하고,
  실행 전에 무엇을 바꾸는지 먼저 말한다.
- `todo.db` 를 커밋하거나 저장소 밖으로 복사하지 않는다 (개인 할 일 목록).
- 앱이 켜져 있을 때 쓰기를 하면 잠금이 걸릴 수 있다 — 쓰기 전에 앱을 끄는 편이 낫다.

## 앱 띄우기

```bash
python todo_app/app.py
```

http://localhost:8765 (127.0.0.1 에만 열림). 끄려면 `Ctrl+C`.
설치할 것은 없다 — 웹서버와 `sqlite3` 모두 파이썬 내장.
