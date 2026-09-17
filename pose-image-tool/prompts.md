# 프롬프트 모음

## 제일 중요한 규칙

**프롬프트에 자세를 쓰지 않습니다.**

자세는 뼈대가 정합니다. 프롬프트에 `stretching`, `sitting`, `arms raised` 같은 말을
또 넣으면 두 지시가 부딪혀 결과가 나빠집니다.

프롬프트에는 이것만 씁니다.

| 쓸 것 | 예 |
|---|---|
| 누구인가 | `a young man`, `a business woman`, `a friendly white humanoid robot` |
| 무엇을 입었나 | `in a grey hoodie and jeans`, `in a navy suit` |
| 어디인가 | `bright photo studio, plain white background` |
| 어떤 사진인가 | `photorealistic`, `flat vector illustration` |

## 실제로 써 본 것

`samples/output_01.png` 을 만든 값입니다.

```
프롬프트   a young man in a grey hoodie and jeans,
          bright photo studio, plain white background, photorealistic

빼기       low quality, blurry, deformed hands, extra limbs,
          extra fingers, watermark, text

POSE_STRENGTH  0.8
STEPS          25
SEED           42
참조 사진       sportimg.jpg (기지개 켜는 사람)
```

## 빼기(negative) 프롬프트

거의 항상 이대로 두면 됩니다. 손가락 문제를 줄여 줍니다.

```
low quality, blurry, deformed hands, extra limbs, extra fingers, watermark, text
```

## 인물만 바꿔 보기

**배경을 나타내는 뒷부분을 똑같이 두면** 여러 장이 한 세트로 보입니다.

```
a young man in a grey hoodie and jeans, photorealistic
a business woman in a navy suit, photorealistic
a child in a yellow raincoat, photorealistic
a friendly white humanoid robot, glossy plastic, photorealistic
an elderly man in a beige cardigan, photorealistic
a firefighter in full gear, photorealistic
```

뒤에 공통으로 붙일 말:

```
, bright photo studio, plain light grey background
```

## 그림체 바꿔 보기

인물을 고정하고 이 부분만 바꾸면 같은 사람의 다른 그림체가 나옵니다.

```
photorealistic
flat vector illustration
watercolor painting
3d render, soft studio lighting
pencil sketch on white paper
anime style, clean lineart
```

## 기록

쓴 프롬프트와 결과를 남겨 두면 다음에 처음부터 헤매지 않습니다.

| 날짜 | 참조 사진 | 프롬프트 요약 | STRENGTH | SEED | 결과 |
|---|---|---|---|---|---|
| 2026-09-16 | sportimg.jpg | grey hoodie 청년 | 0.8 | 42 | `samples/output_01.png` |
| | | | | | |
