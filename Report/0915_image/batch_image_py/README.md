# 배치 이미지 생성

`scenes.csv` 한 줄이 그림 한 장이 된다. 여섯 칸을 영어 문장으로 이어 프롬프트를 만들고,
`out/{id}.png` 와 `out/{id}.json` 을 남긴다.

## 돌리는 법

```bash
pip install -r requirements.txt
python generate.py
```

`out/` 이 없으면 알아서 만든다. 다른 파일을 쓰려면 `--scenes`, `--out` 을 준다.

**GPU(CUDA)가 필요하다.** `float16` 은 GPU 에서 쓰는 형식이라 CPU 로는 돌지 않는다.
없으면 구글 코랩처럼 GPU 가 딸린 곳에서 돌린다.

## 입력 — scenes.csv

| 열 | 뜻 | 예 |
|---|---|---|
| `id` | 파일 이름이자 시드의 재료. **겹치면 안 된다** | `fox-01` |
| `subject` | 무엇이 | `a red fox` |
| `action` | 무엇을 하는가 | `leaping over a fallen log` |
| `camera` | 어떻게 찍었는가 | `low-angle close-up shot` |
| `lighting` | 빛 | `golden hour backlight` |
| `environment` | 어디인가 | `misty pine forest` |
| `style` | 그림체 | `cinematic photorealistic` |

여섯 칸은 이렇게 한 문장이 된다:

```
a red fox leaping over a fallen log, low-angle close-up shot,
golden hour backlight, misty pine forest, cinematic photorealistic.
```

## 출력 — out/

`{id}.png` 와 `{id}.json` 이 짝으로 나온다. json 은 이렇게 생겼다.

```json
{
  "id": "fox-01",
  "prompt": "a red fox leaping over a fallen log, ...",
  "seed": 2115970659,
  "model": "stabilityai/sdxl-turbo",
  "steps": 4,
  "guidance_scale": 0.0,
  "dtype": "float16"
}
```

그림만 남기면 나중에 "이게 어떻게 나왔더라" 를 알 수 없다. 같은 그림을 다시 만들려면
프롬프트·시드·모델·값이 전부 있어야 해서 함께 적는다.

## 사람이 정한 것 / 맡긴 것

이 스크립트에서 **맡기면 안 되는 넷**은 코드 맨 위에 상수로 모여 있다.

| 정한 것 | 어디에 | 왜 |
|---|---|---|
| 입력 형식 | `COLUMNS` | 칸 이름이 바뀌면 프롬프트 뜻이 달라진다 |
| 모델과 값 | `MODEL_ID` `STEPS` `GUIDANCE` `DTYPE` | sdxl-turbo 는 적은 스텝용이라 값을 올리면 오히려 나빠진다 |
| 재현 기록 | `out/{id}.json` | 이게 없으면 좋은 결과를 두 번 만들 수 없다 |
| 실패 처리 | 줄마다 건너뛰고 끝에 목록 | 한 줄 때문에 올려 둔 모델과 지금까지 만든 것을 버리지 않는다 |

반복문을 어떻게 짜고 파일을 어떻게 쓸지는 정하지 않았다 — 그건 바뀌어도 결과가 같다.

## 시드 — 같은 id 면 언제나 같은 그림

`id` 를 sha256 으로 숫자 하나로 바꾼다.

```
"fox-01" → sha256 → 앞 4바이트 → 2115970659
```

파이썬 기본 `hash()` 를 쓰면 **실행할 때마다 값이 달라진다**(해시 랜덤화).
같은 `id` 인데 어제와 오늘 다른 그림이 나와서 재현이 깨진다. `sha256` 은 어느
컴퓨터에서 언제 돌려도 같은 값이라 그걸 쓴다.
