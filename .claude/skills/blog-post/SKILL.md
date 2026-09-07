---
name: blog-post
description: 학습 정리 글을 blog_ksk(Jekyll/GitHub Pages 블로그)에 올린다. "블로그에 올려줘", "블로그 글 써줘", "오늘 배운 거 포스팅", "강의노트 블로그에 올려줘", "글 날짜가 하루 밀렸어" 같은 요청에 사용한다.
---

# blog_ksk 에 글 올리기

`blog_ksk` 는 minimal-mistakes 테마의 Jekyll 블로그다. 2026-08-31 부터 강의 정리 글을
같은 방식으로 여덟 번 올렸다. 그 절차를 그대로 옮긴 것이다.

| | 값 |
|---|---|
| 경로 | `C:\AI-Agent\blog_ksk` (독립 저장소, `SeGwonKIM/blog_ksk`) |
| 공개 주소 | https://segwonkim.github.io/blog_ksk |
| 테마 | `mmistakes/minimal-mistakes@4.24.0` (remote_theme) |
| 타임존 | `Asia/Seoul` (`_config.yml`) |
| 글 폴더 | `_posts/` |
| 글 주소 형식 | `/{카테고리}/{YYYY}/{MM}/{DD}/{슬러그}.html` (Jekyll 기본값 — `permalink` 미설정) |

## 순서

### 1. 원본을 확인한다

강의 정리 글이면 `강의노트/{YYYY-MM-DD}/summary.md` 를 먼저 읽는다.
summary.md 가 없으면 `/summarize-lecture` 를 먼저 돌리라고 안내한다 — 블로그 글을 원본 없이 지어내지 않는다.

### 2. 파일을 만든다

파일명은 **반드시** `_posts/YYYY-MM-DD-영문-슬러그.md`:

```
_posts/2026-09-03-backend-glossary-network-security-deploy.md
_posts/2026-09-04-database-sql-security-backup.md
```

- 날짜는 **강의 날짜**를 쓴다 (정리한 날짜가 아니다).
- 슬러그는 소문자 영문 + 하이픈. 한글 파일명은 쓰지 않는다.

### 3. front matter 를 채운다

기존 글과 형태를 맞춘다:

```yaml
---
title: "서비스의 기억을 만드는 법 — 데이터베이스, SQL, 그리고 지키는 일"
excerpt: "🗓️ 2026-09-04 · 도서관 비유부터 SQL 한 줄 읽기, 표와 관계, 색인과 트랜잭션, SQL 주입과 3-2-1 백업까지 — 데이터베이스 하루치를 비전공자 눈높이로 정리했습니다."
categories:
  - 학습노트
tags:
  - 바이브코딩
  - 데이터베이스
  - SQL
---
```

규칙:

- `title` — 그날의 주제를 한 문장으로. `—`(em dash)로 앞뒤를 나누는 형태를 유지한다.
  `9월 4일 강의 정리` 같은 무성의한 제목은 쓰지 않는다.
- `excerpt` — **`🗓️ {날짜} · ` 로 시작**하고, 다룬 것들을 열거한 뒤
  `— ... 정리했습니다.` 로 끝낸다. 이 형식이 목록 화면에 그대로 노출된다.
- `categories` — 학습 정리는 항상 `학습노트`.
- `tags` — 첫 태그는 항상 `바이브코딩`, 그 뒤에 그날 주제 태그 3~6개.

### 4. 본문을 쓴다

- `## 1. 제목` 처럼 **번호 붙인 h2** 로 큰 흐름을 나눈다 (보통 8~12개).
- 그 아래 필요하면 번호 없는 `### 소제목`.
- **비전공자 눈높이**로 쓴다. 비유를 먼저 주고 용어를 나중에 붙이는 순서
  (예: DB 글의 "도서관 비유", SQL 주입의 "Little Bobby Tables").
- 원본 summary.md 에 없는 내용을 지어내지 않는다. 표현은 다듬어도 사실은 추가하지 않는다.

### 5. 커밋하고 올린다

```bash
git add _posts && git commit -m "데이터베이스 정리 글 추가 (2026-09-04)" && git push
```

커밋 제목은 한국어로 `<주제> 글 추가 (YYYY-MM-DD)` 형태. `_posts` 만 add 한다 —
`.omc/` 같은 다른 미추적 폴더를 끌어들이지 않는다.

**푸시가 거부되면 (며칠 만에 올릴 때 거의 매번 겪는다)**

```
! [rejected] main -> main (fetch first)
hint: Updates were rejected because the remote contains work that you do not have locally.
```

원격에 쌓인 것은 `scheduled-rebuild.yml` 이 **매일 자정(00:05 KST)에 올리는 빈 커밋**이다.
내용 변경이 없으니 충돌 위험 없이 그 위로 얹으면 된다. 먼저 무엇이 쌓였는지 확인하고,

```bash
git fetch origin && git log --oneline HEAD..origin/main
```

`chore: scheduled rebuild to publish dated posts` 뿐이면 리베이스로 이력을 한 줄로 유지한다.

```bash
git pull --rebase origin main && git push
```

`chore: scheduled rebuild` 가 아닌 커밋이 섞여 있으면 **리베이스하지 말고 먼저 사용자에게 알린다**
(다른 곳에서 글을 올렸을 수 있다).

### 6. 올라갔는지 확인한다

Pages 빌드 상태를 직접 본다. 보통 20~45초 걸린다.

```bash
gh api repos/SeGwonKIM/blog_ksk/pages/builds/latest --jq '.status, .commit'
```

`building` → `built` 이 되면 끝. 기다릴 때는 백그라운드로 돌린다.

```bash
until s=$(gh api repos/SeGwonKIM/blog_ksk/pages/builds/latest --jq .status); [ "$s" = built ] || [ "$s" = errored ]; do sleep 5; done; echo "$s"
```

**글 주소는 날짜가 들어간다.** `_config.yml` 에 `permalink` 설정이 없어서 Jekyll 기본값
(`/:categories/:year/:month/:day/:title.html`)이 적용된다.

```
https://segwonkim.github.io/blog_ksk/학습노트/2026/09/05/ai-agent-mcp-skills-harness.html
                                    └ 카테고리 ┘└ 강의 날짜 ┘└ 슬러그 ┘
```

`/학습노트/{슬러그}/` 형태가 아니다 — 주소를 사용자에게 알려줄 때 **추측하지 말고 사이트맵에서 확인한다.**

```bash
curl -s https://segwonkim.github.io/blog_ksk/sitemap.xml | grep -o "<loc>[^<]*</loc>" | tail -5
```

## 날짜가 밀렸을 때 (겪은 문제)

두 가지를 이미 처리해 뒀으니 다시 건드리지 않는다:

1. **타임존** — `_config.yml` 의 `timezone: "Asia/Seoul"`. 이걸 지우면 글 날짜와 URL 날짜가
   하루 밀린다 (커밋 `e45d0fb` 에서 고친 문제).
2. **미래 날짜 글** — Jekyll 은 날짜가 미래인 글을 빌드에서 빼 버린다. 그래서
   `.github/workflows/scheduled-rebuild.yml` 이 매일 00:05 KST(15:05 UTC)에 빈 커밋을 눌러
   Pages 를 다시 빌드한다. 오늘보다 뒤 날짜로 글을 올렸다면 **당장 안 보이는 게 정상**이고,
   자정 넘으면 자동으로 뜬다. (이 빈 커밋이 5번 단계의 푸시 거부를 일으키는 원인이기도 하다.)
   급하면 수동으로:

```bash
gh workflow run scheduled-rebuild.yml --repo SeGwonKIM/blog_ksk
```

## 지킬 것

- **자동으로 올리지 않는다.** 글 초안을 보여주고 사용자 확인을 받은 뒤 커밋·푸시한다.
- 공개 블로그다. 개인 정보, 이메일, 로컬 절대경로, `.env` 값, `todo.db` 내용을 본문에 넣지 않는다.
- `_site/` 는 빌드 결과물이니 커밋에 끌어들이지 않는다.
- `blog_ksk` 는 `C:\AI-Agent` 와 별개 저장소다. 반드시 `blog_ksk` 폴더 안에서 git 명령을 쓴다.
