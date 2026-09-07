"""강의소스/{MMDD}/*.mhtml → 강의노트/{YYYY-MM-DD}/원본.md

mhtml 은 브라우저가 페이지를 통째로 저장한 것이라 메일과 같은 형식(MIME
multipart/related)이다. 안에 HTML 한 조각과 그림·CSS 조각들이 함께 들어 있다.
여기서는 화면 장식(사이드바·버튼·타이머)을 걷어내고 제목·문단·목록만 순서대로 뽑아
한 파일로 이어 붙인다.

쓰는 법:
    PYTHONIOENCODING=utf-8 python .claude/skills/lecture-extract/mhtml2md.py 2026-09-07
    PYTHONIOENCODING=utf-8 python .claude/skills/lecture-extract/mhtml2md.py 0907 --list

  기본      원본.md 를 만든다 (이미 있으면 --force 없이는 덮지 않는다)
  --list    파일별 step 번호만 출력한다 (강의 URL 의 steps/NNNNN 로 어느 강의인지 찾을 때)
  --force   원본.md 를 덮어쓴다
  --any-day  주말·공휴일 검사를 건너뛴다 (강의는 평일에만 열린다)
"""

from __future__ import annotations

import email
import re
import sys
from datetime import date, timedelta
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]     # …/AI-Agent
SRC_ROOT = ROOT / "강의소스"
NOTE_ROOT = ROOT / "강의노트"

# 본문이 아닌 껍데기 — 통째로 건너뛴다.
# aside 는 강의 목록 사이드바다 ("대기중", "00:00:12" 같은 진행 표시가 본문에 섞인다).
SKIP_TAGS = {
    "script", "style", "noscript", "nav", "header", "footer",
    "svg", "button", "select", "aside", "dialog", "form",
    "title",   # <title> 은 블록 태그가 아니라 첫 h1 과 한 줄로 붙어 버린다
}
HEADINGS = {"h1": "# ", "h2": "## ", "h3": "### ", "h4": "#### "}
BLOCK_TAGS = {"p", "li", "blockquote", "pre", "figcaption", "dd", "dt", "td", "th"}

# 매 페이지에 붙는 화면 문구 — 본문이 아니다
JUNK = re.compile(
    r"^(진행 중 학습으로 이동|오늘 하루 보지 않기|대기중|이전|다음|목차|"
    r"바이브 코딩으로 웹 만들기[_\s]*Agt\d*|\d{1,2}:\d{2}(:\d{2})?)$"
)


class Extractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.buf: list[str] = []
        self.skip = 0
        self.prefix = ""

    def handle_starttag(self, tag, attrs):
        if tag in SKIP_TAGS:
            self.skip += 1
            return
        if self.skip:
            return
        if tag in HEADINGS or tag in BLOCK_TAGS:
            self.flush()
            self.prefix = HEADINGS.get(tag, "- " if tag == "li" else "")
        elif tag == "br":
            self.buf.append("\n")

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS:
            self.skip = max(0, self.skip - 1)
            return
        if self.skip:
            return
        if tag in HEADINGS or tag in BLOCK_TAGS:
            self.flush()

    def handle_data(self, data):
        if not self.skip:
            self.buf.append(data)

    def flush(self):
        text = re.sub(r"[ \t]+", " ", "".join(self.buf)).strip()
        self.buf = []
        if text and not JUNK.match(text):
            line = self.prefix + text
            # 사이드바가 남긴 같은 줄 반복을 접는다
            if not self.out or self.out[-1] != line:
                self.out.append(line)
        self.prefix = ""


def load(path: Path) -> tuple[str, str]:
    """mhtml 에서 (본문 HTML, 그 페이지의 원래 주소) 를 꺼낸다.

    주소는 HTML 본문이 아니라 MIME 헤더(Content-Location / Snapshot-Content-Location)에
    들어 있다. 본문을 뒤져서는 step 번호를 찾을 수 없다.
    """
    msg = email.message_from_bytes(path.read_bytes())
    url = msg.get("Snapshot-Content-Location") or ""
    for part in msg.walk():
        if part.get_content_type() == "text/html":
            charset = part.get_content_charset() or "utf-8"
            html = part.get_payload(decode=True).decode(charset, "replace")
            return html, (part.get("Content-Location") or url)
    return "", url


def step_id(url: str) -> str:
    m = re.search(r"steps/(\d+)", url or "")
    return m.group(1) if m else "-"


def sort_key(path: Path):
    """파일명 앞 숫자로 강의 순서를 잡는다 (1., 2., … 없으면 이름순)."""
    m = re.match(r"(\d+)", path.stem)
    return (0, int(m.group(1))) if m else (1, path.stem)


def holidays() -> set[str]:
    """강의노트/holidays.txt 에 적어 둔 공휴일 (한 줄에 YYYY-MM-DD, # 뒤는 주석)."""
    path = NOTE_ROOT / "holidays.txt"
    if not path.exists():
        return set()
    out = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        day = line.split("#")[0].strip()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
            out.add(day)
    return out


def check_lecture_day(full: str) -> None:
    """강의는 평일에만 열린다 — 주말·공휴일이면 폴더 이름이 잘못된 것이다.

    2026-09-05(토)를 09-07(월) 강의로 잘못 적어 두는 실수가 실제로 있었다.
    폴더명을 +1 하다 주말을 건너뛰지 않으면 이렇게 어긋난다.
    """
    d = date.fromisoformat(full)
    reason = None
    if d.weekday() >= 5:                      # 5=토, 6=일
        reason = ["월", "화", "수", "목", "금", "토", "일"][d.weekday()] + "요일 (주말)"
    elif full in holidays():
        reason = "공휴일 (강의노트/holidays.txt 에 등재)"
    if not reason:
        return

    nxt = d
    while nxt.weekday() >= 5 or nxt.isoformat() in holidays():
        nxt += timedelta(days=1)
    sys.exit(
        f"{full} 은 {reason} 이라 강의가 없습니다.\n"
        f"강의는 평일에만 열립니다 — 폴더 이름이 잘못됐을 가능성이 큽니다.\n"
        f"다음 강의일은 {nxt.isoformat()} ({['월','화','수','목','금'][nxt.weekday()]}) 입니다.\n"
        f"폴더 이름을 먼저 고치세요:  mv 강의소스/{full[5:7]}{full[8:10]} "
        f"강의소스/{nxt.strftime('%m%d')}\n"
        f"(날짜가 정말 맞다면 --any-day 로 검사를 건너뜁니다.)"
    )


def resolve_dates(arg: str, skip_check: bool = False) -> tuple[Path, Path]:
    """'2026-09-07' 또는 '0907' 를 받아 (강의소스 폴더, 강의노트 폴더) 를 돌려준다.

    강의소스는 MMDD, 강의노트는 YYYY-MM-DD 를 쓴다 — 표기가 다르니 주의.
    """
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", arg):
        full, mmdd = arg, arg[5:7] + arg[8:10]
    elif re.fullmatch(r"\d{4}", arg):
        mmdd, full = arg, f"{date.today().year}-{arg[:2]}-{arg[2:]}"
    else:
        sys.exit(f"날짜 형식이 아닙니다: {arg}  (YYYY-MM-DD 또는 MMDD)")
    if not skip_check:
        check_lecture_day(full)
    return SRC_ROOT / mmdd, NOTE_ROOT / full


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    if not args:
        sys.exit(__doc__)

    src_dir, note_dir = resolve_dates(args[0], "--any-day" in flags)
    if not src_dir.is_dir():
        sys.exit(f"강의소스 폴더가 없습니다: {src_dir}")

    files = sorted(
        (p for p in src_dir.glob("*.mhtml") if p.is_file()),
        key=sort_key,
    )
    if not files:
        sys.exit(f"mhtml 이 없습니다: {src_dir}")

    if "--list" in flags:
        for p in files:
            print(f"{step_id(load(p)[1]):>6}  {p.name}")
        return

    out_path = note_dir / "원본.md"
    if out_path.exists() and "--force" not in flags:
        sys.exit(f"이미 있습니다: {out_path}\n덮어쓰려면 --force")

    chunks: list[str] = []
    for p in files:
        html, url = load(p)
        parser = Extractor()
        parser.feed(html)
        parser.flush()
        title = p.stem.replace(" _ 모두의연구소", "").strip()
        body = "\n\n".join(parser.out)
        sid = step_id(url)
        chunks.append(f"# {title}\n\n<!-- step {sid} -->\n\n{body}")
        print(f"  step {sid:>6}  {len(parser.out):>4}블록  {title}")

    note_dir.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n\n".join(chunks) + "\n", encoding="utf-8")
    print(f"\n{len(files)}개 강의 → {out_path}")


if __name__ == "__main__":
    main()
