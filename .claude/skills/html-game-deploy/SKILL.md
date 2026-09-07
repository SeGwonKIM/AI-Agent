---
name: html-game-deploy
description: 단일 파일 HTML 게임/웹앱을 새로 만들어 GitHub Pages로 배포한다. "게임 만들어줘", "새 게임 프로젝트", "PRD 써줘", "GitHub Pages로 올려줘", "index.html 하나로 만들어줘" 같은 요청에 사용한다.
---

# 단일 파일 HTML 게임 만들어 배포하기

`ksk_game`, `ksk_game1`, `bom_game` 을 만들 때 세 번 반복한 절차를 그대로 옮긴 것이다.
새 게임/웹앱을 만들 때는 처음부터 이 순서를 따른다.

## 이미 이렇게 만든 것들

| 저장소 | 내용 | 파일 |
|---|---|---|
| `ksk_game` | 2D 레트로 레이싱 (커브 적용) | `PRD.md`, `README.md`, `index.html` (20KB) |
| `ksk_game1` | 오리지널 캐릭터 2D 횡스크롤 플랫폼 | `README.md`, `index.html` (21KB) |
| `bom_game` | 지뢰찾기 (수류탄 에디션) | `PRD.md`, `README.md`, `index.html` (17KB) |

전부 `github.com/SeGwonKIM/<저장소명>` 이고, 저장소에 파일이 **3개뿐**이다. 이 단순함이 핵심이다.

## 순서

### 1. PRD.md 를 먼저 쓴다 (코드보다 먼저)

`bom_game/PRD.md` 의 섹션 구성을 그대로 쓴다:

```
# PRD: <게임 이름>

- 작성일: YYYY-MM-DD
- 배포 형태: 단일 `index.html` (HTML/CSS/JS, 외부 라이브러리 없음) — 브라우저에서 즉시 실행, GitHub Pages로 온라인 배포

## 1. 개요
## 2. 목표
## 3. 대상 사용자 / 플랫폼
## 4. 핵심 사용자 플로우
## 5. 화면별 요구사항 (5.1 시작 화면 / 5.2 게임 화면 HUD / 5.3 ... / 5.4 결과 화면)
## 6. 게임 로직 요약
## 7. 기술 요구사항
## 8. 현재 구현 상태 (v1, `index.html` 기준)
## 9. 향후 개선 제안 (Out of scope for v1)
```

PRD를 먼저 커밋하고 (`docs: <게임> PRD 작성`) 그다음 구현을 커밋한다 — `bom_game` 이 그렇게 갔다.

### 2. index.html 하나에 전부 넣는다

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>게임 이름</title>
<style> /* 전부 인라인 */ </style>
</head>
<body>
...
<script> /* 전부 인라인 */ </script>
</body>
</html>
```

지킬 것:

- **외부 라이브러리 금지.** CDN도 `<link>`도 쓰지 않는다. 빌드 도구도 없다.
- `lang="ko"`, `charset="UTF-8"`, viewport 메타 세 줄은 항상 넣는다.
- 파일을 열기만 하면 실행돼야 한다 — 서버 없이 `index.html` 더블클릭으로 동작.
- 분량은 17~21KB 선. 이보다 크게 부풀지 않게 기능을 자른다.
- 리셋 CSS(`* { box-sizing: border-box; margin: 0; padding: 0; }`)와 어두운 배경 + `Segoe UI` 계열 폰트가 기존 3개의 공통 톤이다.

### 3. README.md 는 짧게

`bom_game/README.md` 형태를 따른다:

```
# <저장소명> — <게임 이름>

한두 문장 설명. 빌드 도구 없이 `index.html` 하나로 동작하며, 정적 호스팅에 바로 배포할 수 있습니다.

## 플레이 방법

`index.html`을 브라우저로 열면 바로 실행됩니다.

- 조작법 불릿
- HUD 설명
- PRD: [PRD.md](PRD.md)
```

### 4. 저장소 만들고 올린다

```bash
cd /c/AI-Agent/<프로젝트명> && git init -b main && git add -A && git commit -m "feat: <게임> 초기 구현"
```

```bash
gh repo create SeGwonKIM/<프로젝트명> --public --source=. --remote=origin --push
```

`gh` 2.98.0 이 이미 깔려 있다. 원격 주소는 SSH(`git@github.com:...`)든 HTTPS든 둘 다 쓰고 있어 상관없다.

### 5. GitHub Pages 를 켠다

```bash
gh api -X POST repos/SeGwonKIM/<프로젝트명>/pages -f "source[branch]=main" -f "source[path]=/"
```

배포 주소는 `https://segwonkim.github.io/<프로젝트명>/` 이다. 켠 뒤 1~2분 지나서 열린다.
확인:

```bash
gh api repos/SeGwonKIM/<프로젝트명>/pages --jq '.status, .html_url'
```

### 6. 마지막에 사용자에게 배포 주소를 알려준다

## 커밋 메시지 규칙 (기존 이력과 맞춘다)

- 한국어로 쓴다.
- `feat: 수류탄이 터졌을 때 직전 상태로 되돌리는 버튼 추가`
- `docs: 지뢰찾기(수류탄 에디션) PRD 작성`
- 무엇을 왜 바꿨는지가 제목에 들어간다. `update`, `fix bug` 같은 빈 제목은 쓰지 않는다.

## 주의

- **`C:\AI-Agent` 자체는 별개 저장소**(`SeGwonKIM/AI-Agent`)다. 게임은 각자 독립 저장소이므로
  `C:\AI-Agent` 루트에서 `git add` 하지 말고 반드시 프로젝트 폴더 안에서 작업한다.
- 새 프로젝트를 만들면 `C:\AI-Agent` 쪽에는 untracked 폴더로 보인다 — 정상이다. 루트에 커밋하지 않는다.
- 게임을 다 만들면 블로그에 쓸지 물어본다 (`blog-post` 스킬).
