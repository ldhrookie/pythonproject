import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date
import os

# tier_logic.py에서 가져오기
from tier_logic import update_tier_and_score, Tier

DB_PATH = "site.db"
TIER_IMAGE_DIR = "tier"

# main_streamlit.py 맨 위쪽에 추가할 함수
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
    # tier_map에 해당 키가 없으면 기본적으로 rookie.png 반환
    return tier_map.get(tier_name, "rookie.png")


# Initialize DB and tables (첫 실행 시 테이블이 없으면 생성)
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # user 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT UNIQUE NOT NULL,
            password    TEXT NOT NULL,
            tier_index  INTEGER DEFAULT 0,  -- Tier 리스트의 인덱스 (0부터 시작, 0=루키)
            rank_point  INTEGER DEFAULT 0   -- 현재 랭크 포인트 (티어 컷라인에 사용)
        )
    """)
    # log 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS log (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER,
            start_time    TEXT,
            end_time      TEXT,
            subject       TEXT,
            felt_minutes  INTEGER,
            concentrate_rate REAL,
            FOREIGN KEY(user_id) REFERENCES user(id)
        )
    """)
    conn.commit()
    conn.close()

# 로그인 함수
def login(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, tier_index, rank_point 
          FROM user 
         WHERE username = ? AND password = ?
    """, (username, password))
    row = cursor.fetchone()
    conn.close()
    return row  # None 또는 (id, username, tier_index, rank_point)

# 회원가입 함수
def signup(username, password):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO user (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

# 특정 사용자의 오늘 공부 총 시간을 구하는 함수
def get_today_total(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    today_str = date.today().isoformat()  # YYYY-MM-DD
    cursor.execute("""
        SELECT SUM( (julianday(end_time) - julianday(start_time)) * 24 * 60 )
          FROM log 
         WHERE user_id = ? 
           AND DATE(start_time) = ?
           AND end_time IS NOT NULL
    """, (user_id, today_str))
    result = cursor.fetchone()[0]
    conn.close()
    return int(result) if result else 0  # 오늘 공부 분 단위

# 오늘 모든 공부 기록 로드
def load_logs(user_id):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM log WHERE user_id = ?", conn, params=(user_id,))
    conn.close()
    return df

# 로그아웃 처리
def do_logout():
    for key in ["user_id", "username", "tier_index", "rank_point", "start_time", "today_flag"]:
        if key in st.session_state:
            st.session_state.pop(key)

# 로그 추가
def add_log(user_id, start_time, end_time, subject, felt_minutes):
    duration_minutes = int((end_time - start_time).total_seconds() / 60)
    rate = 0.0
    if duration_minutes > 0:
        rate = round(min(100, max(0, (felt_minutes / duration_minutes) * 100)), 2)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO log (user_id, start_time, end_time, subject, felt_minutes, concentrate_rate) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, start_time.isoformat(), end_time.isoformat(), subject, felt_minutes, rate)
    )
    # Update user score
    cursor.execute("UPDATE user SET rank_point = rank_point + ? WHERE id = ?", (duration_minutes, user_id))
    # Recalculate tier
    cursor.execute("SELECT rank_point FROM user WHERE id = ?", (user_id,))
    total_point = cursor.fetchone()[0]
    new_rank, new_point, _, _ = update_tier_and_score(
        st.session_state.tier_index,
        total_point - duration_minutes,  # 기존 점수
        get_today_total(user_id)         # 오늘 총 공부 분
    )
    # 실제 DB에는 update_tier_and_score가 최종적으로 계산한 값으로 반영
    cursor.execute("UPDATE user SET tier_index = ?, rank_point = ? WHERE id = ?",
                   (new_rank, new_point, user_id))
    conn.commit()
    conn.close()

# 앱 초기화
init_db()
st.set_page_config(page_title="공부 시스템", layout="centered")

# 세션 상태 초기화
if "user_id" not in st.session_state:
    st.session_state.user_id    = None
    st.session_state.username   = ""
    st.session_state.tier_index = 0
    st.session_state.rank_point = 0
    st.session_state.start_time = None
    st.session_state.today_flag  = False

st.title("📚 공부 타이머 & 로그 시스템")

# 1) 로그인 / 회원가입
if st.session_state.user_id is None:
    tab1, tab2 = st.tabs(["🔐 로그인", "🆕 회원가입"])
    with tab1:
        username_input = st.text_input("아이디")
        password_input = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            user = login(username_input, password_input)
            if user:
                st.session_state.user_id    = user[0]
                st.session_state.username   = user[1]
                st.session_state.tier_index = user[2]
                st.session_state.rank_point = user[3]
                st.session_state.today_flag  = False
                st.success(f"{user[1]}님, 환영합니다! (티어: {Tier[user[2]]}, 점수: {user[3]})")
                st.rerun()
            else:
                st.error("❌ 아이디 또는 비밀번호가 틀렸습니다.")
    with tab2:
        new_user = st.text_input("새 아이디")
        new_pass = st.text_input("새 비밀번호", type="password")
        if st.button("회원가입"):
            if signup(new_user, new_pass):
                st.success("🎉 회원가입 성공! 로그인해 주세요.")
            else:
                st.error("❌ 이미 존재하는 아이디입니다.")
    st.stop()

# 2) 로그인된 사용자 화면
if not st.session_state.today_flag:
    # 오늘 공부 시간(분) 계산
    today_minutes = get_today_total(st.session_state.user_id)
    # update_tier_and_score 호출
    rank, rank_point, tier_name, msg = update_tier_and_score(
        st.session_state.tier_index,
        st.session_state.rank_point,
        today_minutes
    )
    # 세션 상태에 반영
    st.session_state.tier_index = rank
    st.session_state.rank_point = rank_point
    st.session_state.today_flag  = True
    if msg:
        st.info(msg)

# 사용자 정보 + 티어 이미지
current_tier_name = Tier[st.session_state.tier_index]
st.success(f"✅ {st.session_state.username}님 로그인됨 (티어: {current_tier_name}, 점수: {st.session_state.rank_point}점)")

# 티어 이미지
# (기존)
# tier_img_file = os.path.join(TIER_IMAGE_DIR, f"{current_tier_name.lower()}.png")
# if os.path.exists(tier_img_file):
#     st.image(tier_img_file, width=80)

# (수정)
img_name = get_tier_image_filename(current_tier_name)
tier_img_file = os.path.join(TIER_IMAGE_DIR, img_name)

# 디버깅: 경로가 올바른지 확인하고 싶으면 다음 줄을 잠시 활성화해 보세요.
# st.write(f"▶️ trying to load: {tier_img_file}  → exists? {os.path.exists(tier_img_file)}")

if os.path.exists(tier_img_file):
    st.image(tier_img_file, width=80)
else:
    st.warning("⚠️ 티어 이미지 파일을 찾을 수 없습니다.")

st.markdown("---")

# 3) 공부 타이머
st.header("⏱ 공부 타이머")
col1, col2 = st.columns(2)
with col1:
    if st.session_state.start_time is None:
        if st.button("🟢 타이머 시작"):
            st.session_state.start_time = datetime.now()
    else:
        st.info(f"⏳ 시작 시각: {st.session_state.start_time.strftime('%H:%M:%S')}")

with col2:
    if st.session_state.start_time is not None:
        end_now = datetime.now()
        subject = st.text_input("과목 입력", key="subject_input")
        felt = st.number_input("체감 시간(분)", min_value=0, step=1, key="felt_input")
        if st.button("🔴 타이머 종료"):
            add_log(
                st.session_state.user_id,
                st.session_state.start_time,
                end_now,
                subject,
                felt
            )
            # DB에서 업데이트된 티어와 점수를 세션에 반영
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT tier_index, rank_point FROM user WHERE id = ?", (st.session_state.user_id,))
            new_rank, new_point = cursor.fetchone()
            conn.close()
            st.session_state.tier_index = new_rank
            st.session_state.rank_point = new_point
            st.session_state.start_time = None
            st.info("📌 기록이 저장되었습니다.")
            st.rerun()

st.markdown("---")

# 4) 공부 기록 분석
st.header("📊 공부 기록 분석")
df = load_logs(st.session_state.user_id)
if df.empty:
    st.write("아직 기록이 없습니다.")
else:
    df["start_time"] = pd.to_datetime(df["start_time"])
    df["end_time"]   = pd.to_datetime(df["end_time"])
    df["duration"]   = (df["end_time"] - df["start_time"]).dt.total_seconds() / 60

    st.subheader("전체 기록")
    st.dataframe(
        df[["start_time", "end_time", "subject", "duration", "felt_minutes", "concentrate_rate"]]
          .sort_values(by="start_time", ascending=False),
        use_container_width=True
    )

    # 과목별 총 공부 시간(분)
    st.subheader("과목별 총 공부 시간 (분)")
    subj_summary = df.groupby("subject")["duration"].sum().to_frame()
    st.bar_chart(subj_summary)

    # 날짜별 공부 시간 트렌드 (시간)
    st.subheader("날짜별 공부 시간 트렌드 (시간)")
    df["date"] = df["start_time"].dt.date
    daily = df.groupby("date")["duration"].sum().to_frame()
    st.line_chart(daily)

    # 과목별 집중도 통계 (%)
    st.subheader("과목별 집중도 통계 (%)")
    focus_stats = df.groupby("subject")["concentrate_rate"] \
                    .agg(["mean", "std"]) \
                    .rename(columns={"mean": "평균집중도", "std": "변동성"})
    st.dataframe(focus_stats, use_container_width=True)

st.markdown("---")

# 5) 로그아웃
if st.button("🚪 로그아웃"):
    do_logout()
    st.rerun()
