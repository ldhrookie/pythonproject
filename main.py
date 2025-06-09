import streamlit as st

# 페이지 설정 (반드시 첫 번째 Streamlit 명령어여야 함)
st.set_page_config(page_title="공부 시스템", layout="centered")

from database import init_db
from auth import render_login_signup, logout, is_logged_in, init_session_state
from utils import render_user_info, update_daily_tier_progress
from study_timer import render_study_timer
from analytics import render_recent_logs#, render_analytics_tabs
# from pages.time_analysis import render_time_analysis
# from pages.subject_recommender import render_subject_recommender

# 앱 초기화
init_db()

# 세션 상태 초기화 (한 번만 실행)
init_session_state()

st.markdown("## 📚 공부 타이머")

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
# render_analytics_tabs()

# 페이지 이동 버튼들
# st.markdown("---")
if st.button("📊 상세 분석", use_container_width=True):
    st.switch_page("pages/analytics.py")
if st.button("⏰ 시간대별 분석", use_container_width=True):
    st.switch_page("pages/time_analysis.py")
if st.button("📚 과목별 시간 추천", use_container_width=True):
    st.switch_page("pages/subject_recommender.py")

# 로그아웃
if st.button("🚪 로그아웃"):
    logout()
    st.rerun()
