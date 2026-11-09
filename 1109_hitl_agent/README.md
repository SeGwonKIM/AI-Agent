# 🛡️ 글로벌 틱톡 숏폼 자동발행 HITL 게이트키퍼 에이전트

> **모두의연구소 AI 에이전트 2기**  
> **프로젝트: 9. 사람이 승인하는 에이전트 만들기 (Human-In-The-Loop)**  
> **제출자**: 김세권 (SeGwonKIM)  
> **저장소**: [https://github.com/SeGwonKIM/AI-Agent/tree/main/1109_hitl_agent](https://github.com/SeGwonKIM/AI-Agent/tree/main/1109_hitl_agent)

---

## 📌 1. 프로젝트 개요

본 프로젝트는 **다국어 글로벌 숏폼(TikTok) 자동 발행 파이프라인**의 최종 발행 단계 바로 직전에 **인간 승인(HITL: Human-In-The-Loop) 게이트**를 배치하여, 플랫폼 제재나 문화적 논란 등의 치명적인 위험을 방지하고 믿고 맡길 수 있는 자동화를 완성한 프로젝트입니다.

LangGraph v0.2+의 핵심 메커니즘인 `interrupt()`와 `InMemorySaver` 체크포인터, 그리고 `Command(resume=...)` 패턴을 완벽히 구현하여, 기준을 충족한 안전한 콘텐츠는 전자동으로 발행하고 의심/위험 건은 실행을 멈춘 뒤 담당자의 10초 승인 화면으로 연결합니다.

---

## 🚀 2. 빠른 실행 방법

### 방법 A: 원클릭 실행 (Windows 배치파일)
`run_demo.bat` 파일을 더블클릭하면 로컬 웹 서버가 즉시 실행되고 웹 브라우저가 자동으로 열립니다.

### 방법 B: 파이썬 표준 라이브러리 실행 (무설치/의존성 없음)
```bash
python standalone_demo.py
```
브라우저에서 [http://localhost:8501](http://localhost:8501) 로 접속합니다.

### 방법 C: Streamlit 대시보드 실행
```bash
pip install streamlit
streamlit run app.py
```

### 방법 D: 파이프라인 CLI 배치 테스트
```bash
python pipeline.py
```

---

## 📂 3. 디렉토리 구성

```text
1109_hitl_agent/
├── pipeline.py         # LangGraph v0.2 호환 HITL 파이프라인 엔진 (interrupt & resume & checkpointer)
├── app.py              # Streamlit 기반 인터랙티브 웹 대시보드
├── standalone_demo.py  # 순수 파이썬 표준 라이브러리(Zero-Dependency) 웹 서버
├── web_demo.html       # 10초 승인 카드가 구현된 프론트엔드 대시보드 UI
├── sample_data.json    # 한국/일본/대만/태국 8개 테스트 시나리오 데이터셋
├── run_demo.bat        # Windows 원클릭 실행 스크립트
├── README.md           # 프로젝트 안내 및 사용법
└── REPORT.md           # [루브릭 100% 충족] 정밀 프로젝트 보고서
```

---

## 📑 4. 상세 보고서 안내
승인 기준의 타당성, 파이프라인 구조도(Mermaid), 실행 통계 및 데모 화면 설계 비교 등 루브릭 평가 항목 전반은 **[`REPORT.md`](./REPORT.md)** 파일에 상세히 기술되어 있습니다.
