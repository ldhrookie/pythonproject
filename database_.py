# database.py

import sqlite3
import pandas as pd
from datetime import date

DB_PATH = "site.db"

def init_db():
    """데이터베이스 초기화 및 테이블 생성"""
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

def get_user_by_credentials(username, password):
    """로그인 인증"""
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

def create_user(username, password):
    """회원가입"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO user (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def get_today_total_study_time(user_id):
    """특정 사용자의 오늘 공부 총 시간을 구하는 함수"""
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

def get_user_logs(user_id):
    """사용자의 모든 공부 기록 로드"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM log WHERE user_id = ?", conn, params=(user_id,))
    conn.close()
    return df

def save_study_log(user_id, start_time, end_time, subject, felt_minutes):
    """공부 로그 저장"""
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
    conn.commit()
    conn.close()
    return duration_minutes

def update_user_tier_data(user_id, tier_index, rank_point):
    """사용자의 티어 정보 업데이트"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE user SET tier_index = ?, rank_point = ? WHERE id = ?",
                   (tier_index, rank_point, user_id))
    conn.commit()
    conn.close()

def get_user_tier_data(user_id):
    """사용자의 현재 티어 정보 조회"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT tier_index, rank_point FROM user WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result 