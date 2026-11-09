"""
app.py - Streamlit Human Review & Approval Dashboard
LangGraph HITL 파이프라인 승인 대기열 관리 및 실시간 승인/반려/수정 웹 데모

실행 방법: streamlit run app.py
"""

import os
import json
import streamlit as st
from pipeline import TikTokPublishingGraph, InMemoryCheckpointer

st.set_page_config(
    page_title="TikTok 숏폼 자동발행 HITL 승인 관제센터",
    page_icon="🛡️",
    layout="wide"
)

# 세션 상태 초기화
if "graph" not in st.session_state:
    st.session_state.checkpointer = InMemoryCheckpointer()
    st.session_state.graph = TikTokPublishingGraph(checkpointer=st.session_state.checkpointer)
    st.session_state.executed = False
    st.session_state.results = []

graph = st.session_state.graph
checkpointer = st.session_state.checkpointer

st.title("🛡️ 글로벌 틱톡 자동발행 에이전트 HITL 관제센터")
st.caption("AI 에이전트 2기 프로젝트 | 9. 사람이 승인하는 에이전트 만들기 (LangGraph interrupt & resume)")

# 사이드바: 파이프라인 구동 및 설정
with st.sidebar:
    st.header("⚙️ 파이프라인 관제")
    if st.button("🚀 배치 콘텐츠 파이프라인 일괄 실행", use_container_width=True, type="primary"):
        sample_path = os.path.join(os.path.dirname(__file__), "sample_data.json")
        with open(sample_path, "r", encoding="utf-8") as f:
            cases = json.load(f)
        
        st.session_state.results = []
        for c in cases:
            res = graph.run(c)
            st.session_state.results.append(res)
        st.session_state.executed = True
        st.success(f"총 {len(cases)}건의 숏폼 파이프라인 처리가 완료되었습니다!")
        st.rerun()

    st.markdown("---")
    st.markdown("""
    **📋 3대 승인 기준 (Gate Rules)**
    1. **현지 문화·민감어 (위험도 >= 0.6)**  
       - 종교, 정치, 현지 금기어 감지 시 중단
    2. **기술 규격 및 메타데이터 무결성**  
       - 15초~60초 규격, 해시태그 3개 이상, 캡션 10자 이상
    3. **신규 계정/파일럿 초기 보호**  
       - 누적 발행 5회 미만 계정 전수 검수
    """)

# 메인 콘텐츠
if not st.session_state.executed:
    st.info("👈 좌측 사이드바의 **[배치 콘텐츠 파이프라인 일괄 실행]** 버튼을 눌러 작업을 시작해 주세요.")
else:
    pending_threads = checkpointer.list_pending_threads()
    
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    col_stat1.metric("총 처리 건수", len(st.session_state.results))
    col_stat2.metric("전자동 통과 건수", len([r for r in st.session_state.results if r["status"] == "COMPLETED"]))
    col_stat3.metric("인간 승인 대기 (HITL 멈춤)", len(pending_threads))

    st.markdown("---")
    tab1, tab2 = st.tabs(["⚠️ 승인 대기 목록 (HITL 중단 건)", "✅ 처리 완료 및 로그 내역"])

    with tab1:
        if not pending_threads:
            st.success("🎉 모든 승인 대기 건이 처리되었거나 대기 중인 항목이 없습니다.")
        else:
            st.subheader(f"인간 검수 대기 중인 작업: {len(pending_threads)}건")
            for thread_id in pending_threads:
                payload = checkpointer.get_interrupt(thread_id)
                state = checkpointer.load(thread_id)
                if not payload or not state:
                    continue

                with st.expander(f"🔴 [{state.country}] {state.task_id} - {state.channel_name} | {state.raw_title}", expanded=True):
                    c1, c2 = st.columns([1.2, 1])
                    
                    with c1:
                        st.markdown("### 📝 콘텐츠 정보 및 멈춤 원인")
                        st.markdown(f"**대상 채널**: `{state.channel_name}` ({state.country})")
                        st.markdown(f"**미디어 파일**: `{state.media_file}` ({state.duration_seconds}초)")
                        st.markdown(f"**현재 캡션**: {state.caption}")
                        st.markdown(f"**해시태그**: `{' '.join(state.hashtags)}`")
                        
                        st.markdown("#### 🚨 멈춘 이유 (기준 위반 사항)")
                        for r in payload["reasons_to_stop"]:
                            st.error(r)
                            
                        st.markdown("#### ⚡ 통과시키면 일어나는 일")
                        st.warning(payload["consequences_if_approved"])

                    with c2:
                        st.markdown("### ✍️ 담당자 승인 의사결정")
                        new_caption = st.text_area("캡션 수정 (필요 시)", value=state.caption, key=f"cap_{thread_id}")
                        new_tags = st.text_input("해시태그 수정 (쉼표로 구분)", value=", ".join(state.hashtags), key=f"tag_{thread_id}")
                        comment = st.text_input("승인/반려 코멘트", key=f"comm_{thread_id}", placeholder="예: 해시태그 추가 후 정상 발행 승인")

                        btn_col1, btn_col2, btn_col3 = st.columns(3)
                        with btn_col1:
                            if st.button("✅ 승인", key=f"app_{thread_id}", type="primary", use_container_width=True):
                                graph.resume(thread_id, action="approve", comment=comment)
                                st.success(f"{thread_id} 건이 승인되어 발행되었습니다!")
                                st.rerun()

                        with btn_col2:
                            if st.button("🛠️ 수정 후 승인", key=f"edit_{thread_id}", use_container_width=True):
                                parsed_tags = [t.strip() for t in new_tags.split(",") if t.strip()]
                                graph.resume(thread_id, action="edit_and_approve", comment=comment,
                                             edited_caption=new_caption, edited_hashtags=parsed_tags)
                                st.success(f"{thread_id} 건이 수정 후 승인되어 발행되었습니다!")
                                st.rerun()

                        with btn_col3:
                            if st.button("❌ 반려", key=f"rej_{thread_id}", use_container_width=True):
                                graph.resume(thread_id, action="reject", comment=comment)
                                st.warning(f"{thread_id} 건이 반려되어 발행이 취소되었습니다.")
                                st.rerun()

    with tab2:
        st.subheader("📜 전체 파이프라인 실행 상태")
        for res in st.session_state.results:
            tid = res["task_id"]
            current_state = checkpointer.load(tid)
            if not current_state:
                continue
            
            status_badge = "✅ 전자동 완료" if current_state.approval_status == "auto_approved" else \
                           "🟢 인간 승인 완료" if current_state.approval_status == "approved" else \
                           "🛠️ 수정 승인 완료" if current_state.approval_status == "edited_and_approved" else \
                           "❌ 반려됨" if current_state.approval_status == "rejected" else "⏳ 승인 대기 중"

            st.write(f"**{tid}** | {current_state.channel_name} | {status_badge} | 상태: `{current_state.approval_status}`")
            with st.expander(f"상세 로그 보기 ({tid})"):
                for l in current_state.execution_logs:
                    st.text(l)
