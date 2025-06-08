import streamlit as st
from analytics import render_analytics_tabs

def render_analytics():
    st.markdown("# 📊 상세 분석")
    st.markdown("---")
    render_analytics_tabs()


st.set_page_config(page_title="상세 분석", page_icon="📊")
render_analytics()
st.markdown("---")
if st.button("🏠 메인 페이지", use_container_width=True):
    st.switch_page("main.py")
if st.button("⏰ 시간대별 분석", use_container_width=True):
    st.switch_page("pages/time_analysis.py")
if st.button("📚 과목별 시간 추천", use_container_width=True):
    st.switch_page("pages/subject_recommender.py")
