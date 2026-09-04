# 내 Todo 앱

5강(데이터베이스) 실습 — 할 일을 내 컴퓨터의 **SQLite 파일 하나(`todo.db`)** 에 저장한다.
껐다 켜도 남는다.

## 실행

```
python app.py
```

브라우저에서 http://localhost:8765 을 연다. 끄려면 `Ctrl+C`.

**설치할 것이 없다.** 웹서버도 sqlite3 도 파이썬에 들어 있다.
(강의에서 경고한 `better-sqlite3` 빌드 에러가 생길 일이 없다.)

## 되는 것 — CRUD

| | 하는 일 |
|---|---|
| **C** 추가 | 할 일 적기 (+ 마감일, 태그) |
| **R** 보기 | 전부 / 안 끝난 것 / 오늘까지 / 끝난 것, 그리고 검색 |
| **U** 고치기 | 체크박스로 완료 표시 |
| **D** 지우기 | × 버튼 |

## 데이터 모양

```
todos ──┐                          tags
 id     │   todo_tags (연결표)      id
 title  └──< todo_id   tag_id >──   name
 done       다대다(N:M) 를
 due_date   1:N 둘로 푼 것
 created_at
```

- 할 일 1건에 태그가 여럿, 태그 1개에 할 일도 여럿 → **다대다(N:M)** 라서 사이에 **연결표**를 둔다.
- 태그 이름은 `tags` 표에 **한 번만** 적고 나머지는 번호로 가리킨다 (정규화).
- 색인은 자주 하는 질문(`안 끝난 것을 마감일 순으로`)에만 하나 걸었다.

## 지킨 것

- **SQL 주입 방어** — 값을 문자열로 이어 붙이지 않고 자리표(`?`)로만 넘긴다.
- **`todo.db` 는 `.gitignore`** — 내 할 일 목록은 저장소에 올릴 것이 아니다.
- 서버는 `127.0.0.1` 에만 연다 — 같은 와이파이의 다른 기기도 못 들어온다.

## DB 안을 직접 들여다보려면

```
python -c "import sqlite3;c=sqlite3.connect('todo.db');print(c.execute('SELECT * FROM todos').fetchall())"
```

GUI 로 보고 싶으면 **DB Browser for SQLite** 나 VS Code 의 SQLite 확장을 쓰면 된다.
