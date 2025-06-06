# auth.py

import streamlit as st
from database_ import get_user_by_credentials, create_user
from tier_logic import Tier

def render_login_signup():
    """로그인/회원가입 UI 렌더링"""
    tab1, tab2 = st.tabs(["🔐 로그인", "🆕 회원가입"])
    
    with tab1:
        username_input = st.text_input("아이디")
        password_input = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            user = get_user_by_credentials(username_input, password_input)
            if user:
                st.session_state.user_id = user[0]
                st.session_state.username = user[1]
                st.session_state.tier_index = user[2]
                st.session_state.rank_point = user[3]
                st.session_state.today_flag = False
                st.success(f"{user[1]}님, 환영합니다! (티어: {Tier[user[2]]}, 점수: {user[3]})")
                st.rerun()
            else:
                st.error("❌ 아이디 또는 비밀번호가 틀렸습니다.")
    
    with tab2:
        new_user = st.text_input("새 아이디")
        new_pass = st.text_input("새 비밀번호", type="password")
        if st.button("회원가입"):
            if create_user(new_user, new_pass):
                st.success("🎉 회원가입 성공! 로그인해 주세요.")
            else:
                st.error("❌ 이미 존재하는 아이디입니다.")

def logout():
    """로그아웃 처리"""
    for key in ["user_id", "username", "tier_index", "rank_point", "start_time", "today_flag"]:
        if key in st.session_state:
            st.session_state.pop(key)

def is_logged_in():
    """로그인 여부 확인"""
    return st.session_state.get("user_id") is not None

def init_session_state():
    """세션 상태 초기화"""
    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        st.session_state.user_id = None
        st.session_state.username = ""
        st.session_state.tier_index = 0
        st.session_state.rank_point = 0
        st.session_state.start_time = None
        st.session_state.today_flag = False
        st.session_state.session_id = None
        st.session_state.current_subject = "" 