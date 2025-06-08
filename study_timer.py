# study_timer.py

import streamlit as st
from datetime import datetime
import pandas as pd
import time
import os
from database import (
    start_study_session, 
    finish_study_session, 
    cancel_study_session,
    get_active_session,
    get_today_total_study_time,
    get_user_tier,
    update_user_tier,
)
from tier_logic import update_tier_and_score, Tier

def play_tier_up_sound():
    """티어 업 소리 재생"""
    try:
        import pygame
        pygame.mixer.init()
        pygame.mixer.music.load("tier_up.mp3")
        pygame.mixer.music.play()
        time.sleep(2)  # 소리가 끝날 때까지 대기
    except:
        st.error("티어 업 소리를 재생할 수 없습니다.")

def render_study_timer():
    """공부 타이머 UI 렌더링"""
    st.markdown("## ⏱ 공부 타이머")
    
    # 현재 시간
    current_time = datetime.now()
    
    # 진행 중인 세션이 있는지 확인
    if st.session_state.get('session_id') is None:
        active_session = get_active_session(st.session_state.user_id)
        if active_session:
            st.session_state.session_id = active_session['id']
            st.session_state.start_time = active_session['start_time']
            st.session_state.current_subject = active_session['subject']
    
    # 타이머가 실행 중인 경우
    if st.session_state.get('session_id') is not None:
        render_active_timer(current_time)
    else:
        render_timer_start()

def render_active_timer(current_time):
    """활성화된 타이머 UI"""
    start_time = st.session_state.start_time
    
    # 🔥 진행 중 표시를 더 눈에 띄게
    st.error("🔥 **공부 타이머 진행 중!** 🔥")
    
    st.info(f"""
    📅 **시작 시각**: {start_time.strftime('%H:%M:%S')}  
    📚 **과목**: {st.session_state.get('current_subject', '미설정')}
    """)
    
    st.markdown("---")
    
    # 타이머 종료 섹션
    st.subheader("📝 타이머 종료")
    
    elapsed_time = current_time - start_time
    elapsed_minutes = int(elapsed_time.total_seconds() / 60)
    
    # 상하 배치로 변경
    subject = st.text_input("과목 수정/입력", 
                           value=st.session_state.get('current_subject', ''),
                           key="subject_input")
    
    felt = st.number_input("체감 시간(분)", 
                          min_value=0, 
                          value=elapsed_minutes,
                          step=1, 
                          key="felt_input")
    
    # 버튼들도 상하 배치
    if st.button("✅ 타이머 완료", type="primary", use_container_width=True):
        complete_study_session(current_time, subject, felt)
    
    if st.button("❌ 타이머 취소", type="secondary", use_container_width=True):
        cancel_current_session()

def render_timer_start():
    """타이머 시작 UI"""
    col1, col2 = st.columns([2, 1])
    
    with col1:
        subject = st.text_input("과목 입력", value="국어", key="new_subject_input")
    
    with col2:
        st.write("")  # 여백
        if st.button("🟢 타이머 시작", type="primary", use_container_width=True):
            start_new_session(subject)

def start_new_session(subject):
    """새 공부 세션 시작"""
    start_time = datetime.now()
    session_id = start_study_session(st.session_state.user_id, start_time, subject)
    
    # 세션 상태 저장
    st.session_state.session_id = session_id
    st.session_state.start_time = start_time
    st.session_state.current_subject = subject
    
    st.success(f"🎯 공부 시작! (과목: {subject or '미설정'})")
    st.rerun()

def complete_study_session(end_time, subject, felt_minutes):
    """공부 세션 완료 처리"""
    session_id = st.session_state.session_id
    
    # 세션 완료
    duration_minutes = finish_study_session(session_id, st.session_state.user_id, end_time, subject, felt_minutes)
    
    # 오늘 총 공부 시간 계산
    today_minutes = get_today_total_study_time(st.session_state.user_id)
    
    # 티어 업데이트 계산
    new_rank, new_point, tier_name, msg = update_tier_and_score(
        st.session_state.tier_index,
        st.session_state.rank_point,
        today_minutes
    )
    
    # DB에 티어 정보 업데이트
    update_user_tier(st.session_state.user_id, new_rank, new_point)
    
    # 세션 상태 초기화
    clear_session_state()
    
    # 세션 상태 업데이트
    st.session_state.tier_index = new_rank
    st.session_state.rank_point = new_point
    
    # 메시지 표시
    success_msg = f"🎉 공부 완료! {duration_minutes}분 기록됨"
    if subject:
        success_msg += f" (과목: {subject})"
    
    st.success(success_msg)
    if msg:

        st.markdown(
            f"""
            <div style='position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); 
            background-color: rgb(25, 46, 67); padding: 20px; border-radius: 10px; 
            box-shadow: 0 0 10px rgba(0,0,0,0.1); z-index: 1000;'>
                <h4 style='margin: 0; color: rgb(199, 235, 255);'>🎉 {msg}</h4>
            </div>
            """,
            unsafe_allow_html=True
        )
        time.sleep(2) 
        # 티어가 올랐을 때만 풍선 효과와 소리 재생
        if "티어 상승" in msg:
            st.balloons()
            play_tier_up_sound()
    
    st.rerun()

def cancel_current_session():
    """현재 세션 취소"""
    session_id = st.session_state.session_id
    
    if cancel_study_session(session_id, st.session_state.user_id):
        clear_session_state()
        st.warning("⚠️ 타이머가 취소되었습니다.")
        st.rerun()
    else:
        st.error("❌ 세션 취소에 실패했습니다.")

def clear_session_state():
    """세션 상태 초기화"""
    keys_to_clear = ['session_id', 'start_time', 'current_subject']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key] 