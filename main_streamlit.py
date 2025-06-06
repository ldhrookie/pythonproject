import streamlit as st
from database import init_db
from auth import render_login_signup, logout, is_logged_in, init_session_state
from utils import render_user_info, update_daily_tier_progress
from study_timer import render_study_timer
from analytics import render_recent_logs, render_analytics_tabs
from time_analysis import render_time_analysis

# 앱 초기화
init_db()
st.set_page_config(page_title="공부 시스템", layout="centered")

# 세션 상태 초기화 (한 번만 실행)
init_session_state()

st.title("📚 공부 타이머")

# 1) 로그인되지 않은 경우 - 로그인/회원가입 화면
if not is_logged_in():
    render_login_signup()
    st.stop()

# 2) 로그인된 사용자 화면
# 일일 티어 진행도 업데이트 (하루에 한 번만)
if not st.session_state.today_flag:
    update_daily_tier_progress()

# 사용자 정보 + 티어 이미지 표시
render_user_info()

st.markdown("---")

# 3) 공부 타이머
render_study_timer()

st.markdown("---")

# 4) 최근 공부 기록 (간단히)
render_recent_logs()

st.markdown("---")

# 상세 분석 탭들
render_analytics_tabs()

st.markdown("---")

# 시간대별 분석
render_time_analysis()

st.markdown("---")

# 로그아웃
if st.button("🚪 로그아웃"):
    logout()
    st.rerun()
