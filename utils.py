# utils.py

import streamlit as st
import os
from tier_logic import Tier, update_tier_and_score
from database_ import get_today_total_study_time

TIER_IMAGE_DIR = "tier"

def get_tier_image_filename(tier_name):
    """
    tier_name(예: "루키", "브론즈1", "실버2", "골드3" 등)에 대응하는
    이미지 파일명을 정확히 리턴합니다.
    """
    tier_map = {
        "루키":      "rookie.png",
        "브론즈1":   "bronze1.png",
        "브론즈2":   "bronze2.png",
        "브론즈3":   "bronze3.png",
        "실버1":     "silver1.png",
        "실버2":     "silver2.png",
        "실버3":     "silver3.png",
        "골드1":     "gold1.png",
        "골드2":     "gold2.png",
        "골드3":     "gold3.png",
        "다이아1":   "diamond1.png",
        "다이아2":   "diamond2.png",
        "다이아3":   "diamond3.png",
        "크리스탈1": "crystal1.png",
        "크리스탈2": "crystal2.png",
        "크리스탈3": "crystal3.png",
        "레전드1":   "legend1.png",
        "레전드2":   "legend2.png",
        "레전드3":   "legend3.png",
        "얼티밋":    "ultimate.png"
    }
    return tier_map.get(tier_name, "rookie.png")

def render_user_info():
    """사용자 정보 및 티어 이미지 표시"""
    current_tier_name = Tier[st.session_state.tier_index]
    st.success(f"✅ {st.session_state.username}님 안녕하세요! (티어: {current_tier_name}, 점수: {st.session_state.rank_point}점)")
    
    # 티어 이미지
    img_name = get_tier_image_filename(current_tier_name)
    tier_img_file = os.path.join(TIER_IMAGE_DIR, img_name)
    
    if os.path.exists(tier_img_file):
        st.image(tier_img_file, width=80)
    else:
        st.warning("⚠️ 티어 이미지 파일을 찾을 수 없습니다.")

def update_daily_tier_progress():
    """일일 티어 진행도 업데이트"""
    if not st.session_state.today_flag:
        # 오늘 공부 시간(분) 계산
        today_minutes = get_today_total_study_time(st.session_state.user_id)
        # update_tier_and_score 호출
        rank, rank_point, tier_name, msg = update_tier_and_score(
            st.session_state.tier_index,
            st.session_state.rank_point,
            today_minutes
        )
        # 세션 상태에 반영
        st.session_state.tier_index = rank
        st.session_state.rank_point = rank_point
        st.session_state.today_flag = True
        if msg:
            st.info(msg) 