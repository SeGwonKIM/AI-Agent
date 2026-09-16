"""scenes.csv 한 줄 = 그림 한 장. 묶어서 만들고 out/ 에 저장한다.

사람이 정해야 하는 넷은 이 파일 맨 위에 상수로 모아 뒀다.
바꾸고 싶으면 거기만 고치면 된다.

  1) 입력 형식   COLUMNS
  2) 모델과 값   MODEL_ID · STEPS · GUIDANCE · DTYPE
  3) 재현 기록   out/{id}.json 에 프롬프트·시드·모델을 함께 남긴다
  4) 실패 처리   한 줄이 실패해도 멈추지 않고, 끝에 실패 목록을 찍는다

쓰는 법:
    python generate.py                       # scenes.csv → out/
    python generate.py --scenes 다른.csv --out 다른폴더
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

# ── 1) 입력 형식 ─────────────────────────────────────────────
# id 는 파일 이름과 시드를 만드는 데 쓰고, 나머지 여섯 개가 프롬프트가 된다.
ID_COLUMN = "id"
PROMPT_COLUMNS = ["subject", "action", "camera", "lighting", "environment", "style"]
COLUMNS = [ID_COLUMN] + PROMPT_COLUMNS

# ── 2) 모델과 값 ─────────────────────────────────────────────
# sdxl-turbo 는 적은 스텝으로 한 장을 뽑도록 만들어진 모델이라
# 스텝을 늘리거나 가이던스를 올리면 오히려 나빠진다. 그래서 값을 박아 둔다.
MODEL_ID = "stabilityai/sdxl-turbo"
STEPS = 4
GUIDANCE = 0.0
DTYPE = "float16"


def build_prompt(row: dict[str, str]) -> str:
    """여섯 칸을 영어 문장 하나로 잇는다.

    "무엇이 + 무엇을 한다" 를 먼저 놓고, 찍는 법·빛·장소·그림체를 쉼표로 덧붙인다.
    빈 칸은 그냥 건너뛴다 — 쉼표만 둘씩 이어지면 모델이 헷갈린다.
    """
    subject = row.get("subject", "").strip()
    action = row.get("action", "").strip()

    head = " ".join(p for p in (subject, action) if p)
    tail = [row.get(c, "").strip() for c in ("camera", "lighting", "environment", "style")]

    parts = [p for p in [head] + tail if p]
    if not parts:
        raise ValueError("여섯 칸이 모두 비어 있어 프롬프트를 만들 수 없습니다")
    return ", ".join(parts) + "."


def seed_from_id(scene_id: str) -> int:
    """id 를 언제 돌려도 같은 숫자 하나로 바꾼다.

    파이썬 기본 hash() 를 쓰면 안 된다. 실행할 때마다 값이 달라져서
    (해시 랜덤화) 같은 id 인데 어제와 오늘 다른 그림이 나온다 — 재현이 깨진다.
    sha256 은 어느 컴퓨터에서 언제 돌려도 같은 값이라 여기에 쓴다.
    """
    digest = hashlib.sha256(scene_id.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big")      # 0 ~ 4,294,967,295


def load_scenes(path: Path) -> list[dict[str, str]]:
    """csv 를 읽고, 그림을 만들기 전에 어긋난 곳을 먼저 잡는다."""
    if not path.exists():
        sys.exit(f"입력 파일이 없습니다: {path.resolve()}")

    # utf-8-sig: 엑셀이 저장한 csv 는 맨 앞에 보이지 않는 표식(BOM)이 붙는다.
    # 그냥 utf-8 로 읽으면 첫 열 이름이 "\ufeffid" 가 되어 id 를 못 찾는다.
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        sys.exit(f"읽을 줄이 없습니다: {path}")

    missing = [c for c in COLUMNS if c not in rows[0]]
    if missing:
        sys.exit(f"열이 모자랍니다: {', '.join(missing)}\n필요한 열: {', '.join(COLUMNS)}")

    ids = [r[ID_COLUMN].strip() for r in rows]
    if not all(ids):
        sys.exit("id 가 빈 줄이 있습니다")
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        # 같은 id 가 둘이면 뒤엣것이 앞엣것을 덮어쓴다. 조용히 사라지느니 먼저 막는다.
        sys.exit(f"id 가 겹칩니다: {', '.join(sorted(dup))}")

    return rows


def load_pipeline():
    """모델을 GPU 에 한 번만 올린다.

    이 한 번이 몇십 초 걸린다. 줄마다 올렸다 내렸다 하면 그 시간이 줄 수만큼 곱해진다.
    """
    import torch
    from diffusers import AutoPipelineForText2Image

    if not torch.cuda.is_available():
        sys.exit(
            "GPU(CUDA)를 찾지 못했습니다.\n"
            f"{DTYPE} 은 GPU 에서 쓰는 형식이라 CPU 로는 돌릴 수 없습니다.\n"
            "구글 코랩처럼 GPU 가 딸린 곳에서 돌리세요."
        )

    pipe = AutoPipelineForText2Image.from_pretrained(
        MODEL_ID,
        torch_dtype=getattr(torch, DTYPE),
        variant="fp16",
    ).to("cuda")
    return torch, pipe


def main() -> None:
    ap = argparse.ArgumentParser(description="scenes.csv 로 그림을 묶어서 만든다")
    ap.add_argument("--scenes", type=Path, default=Path("scenes.csv"))
    ap.add_argument("--out", type=Path, default=Path("out"))
    args = ap.parse_args()

    rows = load_scenes(args.scenes)
    args.out.mkdir(parents=True, exist_ok=True)

    print(f"{len(rows)}줄 · 모델 {MODEL_ID} · 스텝 {STEPS} · 가이던스 {GUIDANCE} · {DTYPE}")
    print("모델을 올리는 중입니다 (처음이면 내려받느라 몇 분 걸립니다)...")
    torch, pipe = load_pipeline()

    failed: list[tuple[str, str]] = []

    for n, row in enumerate(rows, 1):
        scene_id = row[ID_COLUMN].strip()
        try:
            prompt = build_prompt(row)
            seed = seed_from_id(scene_id)

            # 시드를 넣은 난수기를 줄마다 새로 만든다.
            # 돌려쓰면 앞 줄이 난수기를 얼마나 썼는지에 따라 결과가 달라진다.
            generator = torch.Generator(device="cuda").manual_seed(seed)

            image = pipe(
                prompt=prompt,
                num_inference_steps=STEPS,
                guidance_scale=GUIDANCE,
                generator=generator,
            ).images[0]

            image.save(args.out / f"{scene_id}.png")

            # ── 3) 재현 기록 ──────────────────────────────────
            # 그림만 남기면 나중에 "이거 어떻게 나왔지?" 를 알 수 없다.
            # 같은 그림을 다시 만들려면 아래 넷이 전부 있어야 한다.
            record = {
                "id": scene_id,
                "prompt": prompt,
                "seed": seed,
                "model": MODEL_ID,
                "steps": STEPS,
                "guidance_scale": GUIDANCE,
                "dtype": DTYPE,
            }
            (args.out / f"{scene_id}.json").write_text(
                json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
            )

            print(f"[{n}/{len(rows)}] {scene_id}  seed={seed}")

        except Exception as e:                      # noqa: BLE001
            # ── 4) 실패 처리 ──────────────────────────────────
            # 한 줄이 넘어졌다고 멈추면, 이미 올려 둔 모델과 지금까지 만든 것이 아깝다.
            # 건너뛰고 끝까지 간 다음 한꺼번에 알린다.
            failed.append((scene_id, f"{type(e).__name__}: {e}"))
            print(f"[{n}/{len(rows)}] {scene_id}  실패 — 건너뜁니다")

    done = len(rows) - len(failed)
    print(f"\n끝났습니다. 성공 {done} · 실패 {len(failed)} → {args.out.resolve()}")

    if failed:
        print("\n실패한 줄:")
        for scene_id, reason in failed:
            print(f"  {scene_id}: {reason}")
        sys.exit(1)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")   # 윈도우 콘솔에서 한글이 깨지지 않게
    main()
