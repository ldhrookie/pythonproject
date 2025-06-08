# database.py

import sqlite3
import pandas as pd
from datetime import date, datetime

DB_PATH = "site.db"

def init_db():
    """데이터베이스 초기화"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 사용자 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        tier_index INTEGER DEFAULT 0,
        rank_point INTEGER DEFAULT 0
    )
    ''')
    
    # 공부 기록 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS study_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        start_time TIMESTAMP NOT NULL,
        end_time TIMESTAMP,
        subject TEXT NOT NULL,
        duration INTEGER,
        felt_minutes INTEGER,
        concentrate_rate REAL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # 과목 우선순위 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS subject_priorities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        subject TEXT NOT NULL,
        priority INTEGER DEFAULT 1,
        target_minutes INTEGER,
        UNIQUE(user_id, subject),
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    conn.commit()
    conn.close()

def create_user_log_table(user_id):
    """사용자별 개별 로그 테이블 생성"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    table_name = f"log_user_{user_id}"
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time    TEXT,
            end_time      TEXT,
            subject       TEXT,
            felt_minutes  INTEGER,
            concentrate_rate REAL
        )
    """)
    # 성능을 위한 인덱스 생성
    cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_start_time ON {table_name}(start_time)")
    cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_subject ON {table_name}(subject)")
    conn.commit()
    conn.close()
    return table_name

def get_user_by_credentials(username, password):
    """로그인 인증"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, tier_index, rank_point 
          FROM users 
         WHERE username = ? AND password = ?
    """, (username, password))
    row = cursor.fetchone()
    conn.close()
    return row

def create_user(username, password):
    """회원가입 + 개별 로그 테이블 생성"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # 사용자 전용 로그 테이블 생성
        create_user_log_table(user_id)
        return True
    except sqlite3.IntegrityError:
        return False

def get_today_total_study_time(user_id):
    """사용자의 오늘 공부 총 시간 조회 (개별 테이블에서)"""
    table_name = f"log_user_{user_id}"
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 테이블 존재 확인
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    if not cursor.fetchone():
        conn.close()
        return 0
    
    today_str = date.today().isoformat()
    cursor.execute(f"""
        SELECT SUM( (julianday(end_time) - julianday(start_time)) * 24 * 60 )
          FROM {table_name}
         WHERE DATE(start_time) = ?
           AND end_time IS NOT NULL
    """, (today_str,))
    result = cursor.fetchone()[0]
    conn.close()
    return int(result) if result else 0

def get_user_logs(user_id):
    """사용자의 공부 기록 조회"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            start_time,
            end_time,
            subject,
            duration,
            felt_minutes,
            concentrate_rate
        FROM study_logs
        WHERE user_id = ?
        ORDER BY start_time DESC
    """, (user_id,))
    
    logs = cursor.fetchall()
    conn.close()
    
    if not logs:
        return pd.DataFrame()
    
    df = pd.DataFrame(logs, columns=[
        'start_time',
        'end_time',
        'subject',
        'duration',
        'felt_minutes',
        'concentrate_rate'
    ])
    
    # 시간 형식 변환
    df['start_time'] = pd.to_datetime(df['start_time'])
    df['end_time'] = pd.to_datetime(df['end_time'])
    
    return df

def start_study_session(user_id, start_time, subject=""):
    """공부 세션 시작 - 사용자별 테이블에 기록 (end_time은 NULL)"""
    # 테이블이 없으면 생성
    create_user_log_table(user_id)
    
    table_name = f"log_user_{user_id}"
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"""
        INSERT INTO {table_name} (start_time, end_time, subject, felt_minutes, concentrate_rate) 
        VALUES (?, NULL, ?, NULL, NULL)
    """, (start_time.isoformat(), subject))
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id

def get_active_session(user_id):
    """진행 중인 세션 조회 (사용자별 테이블에서 end_time이 NULL인 마지막 레코드)"""
    table_name = f"log_user_{user_id}"
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 테이블 존재 확인
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    if not cursor.fetchone():
        conn.close()
        return None
    
    cursor.execute(f"""
        SELECT id, start_time, subject 
        FROM {table_name}
        WHERE end_time IS NULL
        ORDER BY start_time DESC 
        LIMIT 1
    """)
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'id': row[0],
            'start_time': datetime.fromisoformat(row[1]),
            'subject': row[2] or ""
        }
    return None

def finish_study_session(session_id, user_id, end_time, subject, felt_minutes):
    """진행 중인 세션 완료"""
    table_name = f"log_user_{user_id}"
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 세션 정보 조회
    cursor.execute(f"SELECT start_time FROM {table_name} WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return 0
    
    start_time = datetime.fromisoformat(row[0])
    duration_minutes = int((end_time - start_time).total_seconds() / 60)
    rate = 0.0
    if duration_minutes > 0:
        rate = round(min(100, max(0, (felt_minutes / duration_minutes) * 100)), 2)
    
    # 세션 완료 처리
    cursor.execute(f"""
        UPDATE {table_name}
        SET end_time = ?, subject = ?, felt_minutes = ?, concentrate_rate = ?
        WHERE id = ?
    """, (end_time.isoformat(), subject, felt_minutes, rate, session_id))
    
    conn.commit()
    conn.close()
    return duration_minutes

def cancel_study_session(session_id, user_id):
    """진행 중인 세션 취소 (삭제)"""
    table_name = f"log_user_{user_id}"
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table_name} WHERE id = ? AND end_time IS NULL", (session_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def delete_study_log(user_id, log_id):
    """특정 공부 기록 삭제"""
    # numpy 타입을 Python int로 변환
    log_id = int(log_id)
    user_id = int(user_id)
    
    table_name = f"log_user_{user_id}"
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 테이블 존재 확인
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    if not cursor.fetchone():
        conn.close()
        return False
    
    # 기록 삭제
    cursor.execute(f"DELETE FROM {table_name} WHERE id = ?", (log_id,))
    deleted = cursor.rowcount > 0
    
    conn.commit()
    conn.close()
    return deleted

def get_user_tier(user_id):
    """사용자의 현재 티어 정보 조회"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT tier_index, rank_point FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return {
            'tier_index': result[0],
            'rank_point': result[1]
        }
    return None

def update_user_tier(user_id, tier_index, rank_point):
    """사용자의 티어 정보 업데이트"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET tier_index = ?, rank_point = ? WHERE id = ?",
                   (tier_index, rank_point, user_id))
    conn.commit()
    conn.close()

def get_database_stats():
    """데이터베이스 통계 조회 (관리용)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 전체 사용자 수
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    
    # 사용자별 로그 테이블 목록
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'log_user_%'")
    log_tables = [row[0] for row in cursor.fetchall()]
    
    stats = {
        'total_users': user_count,
        'log_tables': len(log_tables),
        'table_names': log_tables
    }
    
    conn.close()
    return stats

def cleanup_user_data(user_id):
    """사용자 데이터 완전 삭제 (GDPR 대응)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 사용자 로그 테이블 삭제
    table_name = f"log_user_{user_id}"
    cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
    
    # 사용자 계정 삭제
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    
    conn.commit()
    conn.close()

def get_subject_priorities(user_id):
    """과목 우선순위 조회"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 과목별 평균 공부 시간 계산
    cursor.execute('''
    SELECT subject, AVG(duration) as avg_duration
    FROM study_logs
    WHERE user_id = ? AND duration IS NOT NULL
    GROUP BY subject
    ''', (user_id,))
    
    avg_durations = {row[0]: int(row[1]) for row in cursor.fetchall()}
    
    # 우선순위 조회
    cursor.execute('''
    SELECT subject, priority, target_minutes
    FROM subject_priorities
    WHERE user_id = ?
    ''', (user_id,))
    
    priorities = cursor.fetchall()
    conn.close()
    
    # 결과 정리
    result = {}
    for subject, priority, target_minutes in priorities:
        result[subject] = {
            'priority': priority,
            'target_minutes': target_minutes or avg_durations.get(subject, 60)  # 기본값 60분
        }
    
    return result

def update_subject_priority(user_id, subject, priority, target_minutes):
    """과목 우선순위 업데이트"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO subject_priorities (user_id, subject, priority, target_minutes)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(user_id, subject) DO UPDATE SET
        priority = excluded.priority,
        target_minutes = excluded.target_minutes
    ''', (user_id, subject, priority, target_minutes))
    
    conn.commit()
    conn.close()

def get_subject_concentration_by_time(user_id):
    """시간대별 과목 집중도 분석"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT 
        subject,
        strftime('%H', start_time) as hour,
        AVG(concentrate_rate) as avg_concentration,
        COUNT(*) as session_count
    FROM study_logs
    WHERE user_id = ? AND concentrate_rate IS NOT NULL
    GROUP BY subject, hour
    HAVING session_count >= 3  -- 최소 3회 이상의 기록이 있는 경우만
    ORDER BY subject, hour
    ''', (user_id,))
    
    results = cursor.fetchall()
    conn.close()
    
    # 결과 정리
    time_analysis = {}
    for subject, hour, concentration, count in results:
        if subject not in time_analysis:
            time_analysis[subject] = {}
        time_analysis[subject][int(hour)] = {
            'concentration': concentration,
            'count': count
        }
    
    return time_analysis 