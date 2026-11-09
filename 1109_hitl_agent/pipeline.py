"""
pipeline.py - Global TikTok Short-Form HITL (Human-in-the-loop) Publishing Pipeline
LangGraph v0.2+ Architecture Compatible with interrupt() & InMemorySaver Checkpointer.

과제: 9. 사람이 승인하는 에이전트 만들기 [프로젝트]
작성일: 2026-11-09
"""

import os
import json
import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime


# ==============================================================================
# 1. State Definition (에이전트 파이프라인 상태)
# ==============================================================================
@dataclass
class ContentState:
    task_id: str
    channel_id: str
    channel_name: str
    country: str
    cumulative_uploads: int
    raw_title: str
    media_file: str
    duration_seconds: int
    caption: str
    hashtags: List[str]
    text_content: str
    is_pilot: bool
    
    # 평가 지표 및 HITL 제어 변수
    risk_score: float = 0.0
    risk_reasons: List[str] = field(default_factory=list)
    criteria_failures: List[str] = field(default_factory=list)
    requires_approval: bool = False
    
    # 인간 승인 결과
    approval_status: str = "pending"  # auto_approved, pending_human, approved, rejected, edited_and_approved
    human_action: Optional[str] = None  # approve, reject, edit_and_approve
    human_comment: Optional[str] = None
    edited_caption: Optional[str] = None
    edited_hashtags: Optional[List[str]] = None
    
    # 최종 게시 정보
    is_published: bool = False
    published_at: Optional[str] = None
    execution_logs: List[str] = field(default_factory=list)


# ==============================================================================
# 2. Checkpointer & Interrupt System (체크포인터 및 일시정지 메커니즘)
# ==============================================================================
class InterruptException(Exception):
    """LangGraph interrupt()와 동일한 인터럽트 예외"""
    def __init__(self, value: Dict[str, Any]):
        self.value = value
        super().__init__(str(value))


class InMemoryCheckpointer:
    """중단된 상태를 안전하게 저장하고 재개하는 인메모리 체크포인터"""
    def __init__(self):
        self._storage: Dict[str, Dict[str, Any]] = {}
        self._interrupt_payloads: Dict[str, Dict[str, Any]] = {}

    def save(self, thread_id: str, state: ContentState, interrupt_payload: Optional[Dict[str, Any]] = None):
        self._storage[thread_id] = asdict(state)
        if interrupt_payload:
            self._interrupt_payloads[thread_id] = interrupt_payload

    def load(self, thread_id: str) -> Optional[ContentState]:
        data = self._storage.get(thread_id)
        if not data:
            return None
        return ContentState(**data)

    def get_interrupt(self, thread_id: str) -> Optional[Dict[str, Any]]:
        return self._interrupt_payloads.get(thread_id)

    def clear_interrupt(self, thread_id: str):
        self._interrupt_payloads.pop(thread_id, None)

    def list_pending_threads(self) -> List[str]:
        return list(self._interrupt_payloads.keys())


# ==============================================================================
# 3. 3대 승인 기준 평가 엔진 (계산 가능한 기준 설계)
# ==============================================================================
# 민감어 / 문화적 결례 사전
SENSITIVE_KEYWORDS = {
    "TH": ["사원", "불교", "왕실", "승려", "monk", "temple", "royal"],
    "JP": ["야쿠자", "원전", "지진", "혐한", "방사능"],
    "TW": ["양안", "독립", "하나의 중국", "정치", "대륙"],
    "KR": ["정치", "혐오", "비하", "극단"]
}

def evaluate_criteria(state: ContentState) -> ContentState:
    """
    루브릭 요건: 계산 가능한 승인 기준 3종 정밀 검증
    1) 기준 1 (문화적 리스크): risk_score >= 0.60 또는 현지 민감어 감지
    2) 기준 2 (기술 규격): duration < 15s or > 60s, hashtags < 3개, caption < 10자
    3) 기준 3 (계정 안정성): cumulative_uploads < 5회 또는 pilot 에피소드
    """
    failures = []
    reasons = []
    calculated_risk = 0.1  # 기본 안전 점수

    # [기준 1] 문화적/현지화 리스크 평가
    target_country = state.country.upper()
    keywords = SENSITIVE_KEYWORDS.get(target_country, [])
    full_text = f"{state.caption} {state.text_content} {' '.join(state.hashtags)}"
    
    found_sensitive = [k for k in keywords if k in full_text]
    if found_sensitive:
        calculated_risk = 0.85
        msg = f"[기준 1 위반] {target_country} 현지 문화/종교 민감어 감지: {', '.join(found_sensitive)} (위험점수: {calculated_risk})"
        failures.append(msg)
        reasons.append(f"현지 민감 키워드 '{', '.join(found_sensitive)}' 포함으로 인한 계정 섀도우밴 위험")

    state.risk_score = calculated_risk
    state.risk_reasons = reasons

    # [기준 2] 틱톡 플랫폼 기술 규격 및 메타데이터 무결성 평가
    if state.duration_seconds < 15:
        failures.append(f"[기준 2 위반] 영상 길이 미달: {state.duration_seconds}초 (최소 15초 이상 필수)")
    elif state.duration_seconds > 60:
        failures.append(f"[기준 2 위반] 숏폼 권장 길이 초과: {state.duration_seconds}초 (최대 60초 이내)")

    if len(state.hashtags) < 3:
        failures.append(f"[기준 2 위반] 필수 해시태그 부족: 현재 {len(state.hashtags)}개 (최소 3개 이상 필요)")

    if len(state.caption.strip()) < 10:
        failures.append(f"[기준 2 위반] 설명글 길이 부족: 현재 {len(state.caption.strip())}자 (최소 10자 이상 권장)")

    # [기준 3] 신규 계정 런칭 및 파일럿 영상 초기 보호 기준
    if state.cumulative_uploads < 5:
        failures.append(f"[기준 3 위반] 신규 런칭 계정 초기 보호: 누적 업로드 {state.cumulative_uploads}회 (< 5회) - 인간 감독 필수")
    elif state.is_pilot:
        failures.append("[기준 3 위반] 신규 파일럿 시리즈 1호 영상 - 브랜딩 톤앤매너 인간 검수 필수")

    # 종합 판정
    if failures:
        state.requires_approval = True
        state.criteria_failures = failures
        state.approval_status = "pending_human"
        state.execution_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 승인 기준 {len(failures)}건 미달 감지 -> HITL 멈춤 트리거")
    else:
        state.requires_approval = False
        state.criteria_failures = []
        state.approval_status = "auto_approved"
        state.execution_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 모든 승인 기준 정상 통과 -> 전자동 발행 승인 완료")

    return state


# ==============================================================================
# 4. Pipeline Execution Graph (노드 및 인터럽트 파이프라인)
# ==============================================================================
class TikTokPublishingGraph:
    def __init__(self, checkpointer: Optional[InMemoryCheckpointer] = None):
        self.checkpointer = checkpointer or InMemoryCheckpointer()

    def run(self, initial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        초기 입력을 받아 파이프라인을 실행합니다.
        승인이 필요한 경우 interrupt()로 실행을 멈추고 체크포인터에 상태를 보존합니다.
        """
        state = ContentState(**initial_data)
        thread_id = state.task_id
        state.execution_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 파이프라인 시작: {state.task_id} ({state.channel_name})")

        # 1단계: 승인 기준 평가
        state = evaluate_criteria(state)

        # 2단계: HITL 게이트 (기준 미달 시 멈춤)
        if state.requires_approval:
            # 10초 만에 판단할 수 있는 구조화된 승인 페이로드 구성
            consequence_text = f"즉시 {state.country} 현지 틱톡 공식 채널({state.channel_name})로 영상이 영구 게시되며 전 세계 구독자에게 푸시 알림이 발송됩니다."
            interrupt_payload = {
                "task_id": state.task_id,
                "channel_name": state.channel_name,
                "country": state.country,
                "media_file": state.media_file,
                "duration_seconds": state.duration_seconds,
                "caption": state.caption,
                "hashtags": state.hashtags,
                "risk_score": state.risk_score,
                "reasons_to_stop": state.criteria_failures,
                "consequences_if_approved": consequence_text,
                "allowed_actions": ["approve", "edit_and_approve", "reject"]
            }

            # 체크포인터에 보존 후 interrupt 발생
            self.checkpointer.save(thread_id, state, interrupt_payload)
            state.execution_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] interrupt() 발생: 담당자 승인 대기열로 이동 (체크포인트 저장)")
            return {
                "status": "INTERRUPTED",
                "task_id": thread_id,
                "interrupt_payload": interrupt_payload,
                "state": asdict(state)
            }

        # 기준 통과 건은 곧바로 발행 집행 노드로 이동
        state = self._publish_node(state)
        self.checkpointer.save(thread_id, state)
        return {
            "status": "COMPLETED",
            "task_id": thread_id,
            "state": asdict(state)
        }

    def resume(self, thread_id: str, action: str, comment: str = "",
               edited_caption: Optional[str] = None, edited_hashtags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        체크포인터에서 멈춘 상태를 복원하고, 인간의 판단을 주입하여 중단 지점부터 재개합니다.
        """
        state = self.checkpointer.load(thread_id)
        if not state:
            raise ValueError(f"Thread ID {thread_id} not found in checkpointer.")

        state.execution_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Command(resume) 수신: 액션={action}, 코멘트='{comment}'")
        state.human_action = action
        state.human_comment = comment

        if action == "approve":
            state.approval_status = "approved"
            state = self._publish_node(state)
        elif action == "edit_and_approve":
            state.approval_status = "edited_and_approved"
            if edited_caption:
                state.caption = edited_caption
            if edited_hashtags:
                state.hashtags = edited_hashtags
            state.execution_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 캡션/해시태그 인간 수정 반영 완료")
            state = self._publish_node(state)
        elif action == "reject":
            state.approval_status = "rejected"
            state.is_published = False
            state.execution_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 담당자에 의해 최종 반려됨 (게시 취소)")
        else:
            raise ValueError(f"Unknown human action: {action}")

        # 인터럽트 큐에서 해제 및 최종 저장
        self.checkpointer.clear_interrupt(thread_id)
        self.checkpointer.save(thread_id, state)

        return {
            "status": "COMPLETED",
            "task_id": thread_id,
            "state": asdict(state)
        }

    def _publish_node(self, state: ContentState) -> ContentState:
        """최종 발행 집행 노드"""
        state.is_published = True
        state.published_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        state.execution_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 틱톡 공식 API 퍼블리시 성공! (게시 완료: {state.published_at})")
        return state


# ==============================================================================
# 5. CLI Test & Batch Verification
# ==============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("TikTok HITL Publishing Pipeline 테스트 구동")
    print("=" * 70)

    sample_path = os.path.join(os.path.dirname(__file__), "sample_data.json")
    with open(sample_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    graph = TikTokPublishingGraph()
    interrupted_tasks = []
    auto_passed_tasks = []

    for item in cases:
        res = graph.run(item)
        if res["status"] == "INTERRUPTED":
            interrupted_tasks.append(res)
            print(f"⚠️ [인터럽트 멈춤] {res['task_id']} ({item['channel_name']}) - 사유 {len(res['interrupt_payload']['reasons_to_stop'])}건")
        else:
            auto_passed_tasks.append(res)
            print(f"✅ [전자동 통과] {res['task_id']} ({item['channel_name']}) - 즉시 발행 완료")

    print("-" * 70)
    print(f"총 {len(cases)}건 중: 전자동 통과 {len(auto_passed_tasks)}건 / HITL 승인 대기 {len(interrupted_tasks)}건")
    print("=" * 70)
