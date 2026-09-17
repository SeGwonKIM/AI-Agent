# pose-image-tool

**사진 한 장의 자세를 그대로 빌려, 다른 사람으로 다시 그리는 도구.**

참조 사진에서 관절을 뽑아 뼈대로 만들고, 그 뼈대를 지킨 채 프롬프트대로
새 인물을 그립니다. 마네킹의 포즈는 그대로 두고 옷만 갈아입히는 것과 같습니다.

## 쓰는 법

`pose_tool.ipynb` 를 [Google Colab](https://colab.research.google.com) 에서 열고
**[런타임 → 런타임 유형 변경 → T4 GPU]** 로 바꾼 뒤 위에서부터 차례로 실행하면 됩니다.

## 들어 있는 것

```
pose-image-tool/
├── README.md          이 파일
├── pose_tool.ipynb    코랩 노트북 (실행 결과가 함께 저장돼 있음)
├── prompts.md         실제로 써 본 프롬프트와 쓰는 요령
└── samples/           결과 예시 (왼쪽부터 순서대로)
    ├── pose_01.jpg    참조로 쓴 사진
    ├── output_01.png  거기서 뽑아낸 뼈대
    └── output_02.png  그 뼈대로 만든 그림
```

## 어떻게 도는가

```
참조 사진  →  OpenPose 가 관절 18개를 뽑아 막대 그림으로  →  ControlNet 이
그 뼈대를 지키라고 붙잡는 동안  →  SDXL 이 프롬프트대로 그림
```

참조 사진의 **얼굴·옷·배경은 뼈대 단계에서 전부 버려집니다.** 남는 건 팔다리 위치뿐이라
사람을 바꿀 수 있습니다.

## 조절 손잡이

| 값 | 뜻 | 권장 |
|---|---|---|
| `POSE_STRENGTH` | 뼈대를 얼마나 세게 따를지 | **0.8** (1.0 은 뻣뻣, 0.5 아래는 자세가 흐트러짐) |
| `STEPS` | 그리는 횟수 | 25 |
| `SEED` | 같은 값이면 같은 그림 | 아무 숫자 |

## 쓰는 모델

| 역할 | 모델 |
|---|---|
| 자세 추출 | OpenPose (`controlnet_aux`) |
| 자세 고정 | [thibaud/controlnet-openpose-sdxl-1.0](https://huggingface.co/thibaud/controlnet-openpose-sdxl-1.0) |
| 그림 생성 | [stabilityai/stable-diffusion-xl-base-1.0](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0) |
| 색 복원 | [madebyollin/sdxl-vae-fp16-fix](https://huggingface.co/madebyollin/sdxl-vae-fp16-fix) |

**FLUX.2-klein 을 쓰지 않은 이유**: ControlNet 은 모델 구조마다 따로 만들어야 하는데,
klein(4B·9B)용은 아직 없습니다. FLUX.2 계열 ControlNet 은 FLUX.2-dev 전용이고,
그 모델은 무료 T4(15GB)에 들어가지 않습니다.

## 알아 둘 것

- **자세가 100% 똑같지는 않습니다.** 뼈대는 관절 위치만 담고 손가락 방향이나 몸의 두께는
  담지 못합니다. `samples/` 의 예시도 팔 모양이 조금 다릅니다.
- **참조 사진은 한 명만 나온 것**을 쓰세요. 여럿이면 뼈대가 섞입니다.
- **프롬프트에 자세를 쓰지 마세요.** 자세는 뼈대가 담당합니다. 자세히는 `prompts.md` 참고.
- **`mediapipe` 충돌**: 코랩에서 `controlnet_aux` 를 부를 때 `mediapipe` 때문에 오류가
  나는 일이 있습니다. 노트북에 우회 코드가 들어 있습니다.
- 무료 코랩은 GPU 세션을 하나만 허용합니다. 다른 노트북이 돌고 있으면
  **런타임 → 세션 관리**에서 먼저 끊으세요.
