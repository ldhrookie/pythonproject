import streamlit as st
import pandas as pd
from datetime import datetime, time
from database import get_user_logs



def render_time_analysis():
    st.markdown("# ⏰ 시간대별 분석")
    st.markdown("---")
    
    # 1. 시간대 설정
    st.markdown("### 1️⃣ 시간대 설정")
    
    # 기존 시간대 목록 표시
    if "time_slots" not in st.session_state:
        st.session_state.time_slots = [
            {"start": time(19, 0), "end": time(20, 50), "name": "저녁 공부"}
        ]
    
    # 새로운 시간대 추가
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        new_start = st.time_input("시작 시간", time(19, 0))
    with col2:
        new_end = st.time_input("종료 시간", time(20, 50))
    with col3:
        new_name = st.text_input("시간대 이름", "새 시간대")
    
    if st.button("➕ 시간대 추가"):
        st.session_state.time_slots.append({
            "start": new_start,
            "end": new_end,
            "name": new_name
        })
        st.rerun()
    
    # 시간대 목록 표시 및 삭제 기능
    for i, slot in enumerate(st.session_state.time_slots):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"⏰ {slot['name']}: {slot['start'].strftime('%H:%M')} ~ {slot['end'].strftime('%H:%M')}")
        with col2:
            if st.button("🗑️ 삭제", key=f"delete_{i}"):
                st.session_state.time_slots.pop(i)
                st.rerun()
    
    st.markdown("---")
    
    # 2. 시간대별 분석
    st.markdown("### 2️⃣ 시간대별 분석")
    
    # 데이터 가져오기
    df = get_user_logs(st.session_state.user_id)
    if df.empty:
        st.warning("아직 공부 기록이 없습니다.")
        return
    
    # 시간 데이터 전처리
    df['start_time'] = pd.to_datetime(df['start_time'])
    df['start_hour'] = df['start_time'].dt.time
    
    # 각 시간대별 분석
    for slot in st.session_state.time_slots:
        st.subheader(f"📊 {slot['name']} 분석")
        
        # 해당 시간대의 데이터 필터링
        mask = (df['start_hour'] >= slot['start']) & (df['start_hour'] <= slot['end'])
        time_slot_df = df[mask].copy()
        
        if time_slot_df.empty:
            st.write("이 시간대의 기록이 없습니다.")
            continue
        
        # 과목별 집중도 평균 계산
        subject_stats = time_slot_df.groupby('subject').agg({
            'concentrate_rate': ['mean', 'count']
        }).round(2)
        
        subject_stats.columns = ['평균 집중도', '기록 수']
        subject_stats = subject_stats.sort_values('평균 집중도', ascending=False)
        
        # 결과 표시
        st.write("과목별 평균 집중도:")
        st.dataframe(subject_stats)
        
        # 시각화 (Streamlit 기본 차트 사용)
        st.bar_chart(subject_stats['평균 집중도'])

st.set_page_config(page_title="시간대별 분석", page_icon="⏰")

render_time_analysis()
st.markdown("---")
if st.button("🏠 메인 페이지", use_container_width=True):
    st.switch_page("main.py")
if st.button("📊 상세 분석", use_container_width=True):
    st.switch_page("pages/analytics.py")
if st.button("📚 과목별 시간 추천", use_container_width=True):
    st.switch_page("pages/subject_recommender.py")