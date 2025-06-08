import streamlit as st
import pandas as pd
from datetime import datetime, time
from database import (
    get_user_logs,
    get_subject_priorities,
    update_subject_priority,
    get_subject_concentration_by_time
)

def render_subject_recommender():
    """과목 추천 시스템 UI"""
    st.markdown("## 📚 과목별 시간 추천")
    
    # 1. 과목 우선순위 설정
    st.markdown("### 1️⃣ 과목 우선순위 설정")
    
    # 과목별 통계 데이터 가져오기
    df = get_user_logs(st.session_state.user_id)
    if df.empty:
        st.warning("아직 공부 기록이 없습니다.")
        return
    
    # 과목별 평균 시간 계산
    subject_stats = df.groupby('subject').agg({
        'duration': ['mean', 'count']
    }).round(2)
    subject_stats.columns = ['평균 시간(분)', '기록 수']
    
    # 현재 우선순위 가져오기
    priorities = get_subject_priorities(st.session_state.user_id)
    
    # 과목들을 3개씩 그룹화
    subjects = list(subject_stats.index)
    subject_groups = [subjects[i:i+3] for i in range(0, len(subjects), 3)]
    
    # 우선순위 설정 UI
    for group in subject_groups:
        cols = st.columns(3)
        for i, subject in enumerate(group):
            with cols[i]:
                st.write(f"**{subject}**")
                avg_time = int(subject_stats.loc[subject, '평균 시간(분)'])
                st.write(f"평균: {avg_time}분")
                avg_time = max(10, avg_time)
                
                priority = st.number_input(
                    "우선순위",
                    min_value=1,
                    max_value=10,
                    value=priorities.get(subject, {}).get('priority', 1),
                    key=f"priority_{subject}"
                )
                
                target_minutes = st.number_input(
                    "목표 시간(분)",
                    min_value=10,  # 최소값 10분으로 낮춤
                    max_value=240,
                    step=10,  # 10분 단위로 변경
                    value=avg_time,  # 기본값을 평균 시간으로 설정
                    key=f"target_{subject}"
                )
                
                # 우선순위 업데이트
                update_subject_priority(
                    st.session_state.user_id,
                    subject,
                    priority,
                    target_minutes
                )
        
        st.markdown("---")
    
    # 2. 시간대별 추천
    st.markdown("### 2️⃣ 시간대별 추천")
    
    # 시간대별 집중도 분석
    time_analysis = get_subject_concentration_by_time(st.session_state.user_id)
    
    if not time_analysis:
        st.warning("시간대별 분석을 위한 충분한 데이터가 없습니다.")
        return
    
    # 시간대별 상위 3개 과목 추천
    st.markdown("#### 📅 시간대별 추천 과목 (상위 3개)")
    
    # 모든 시간대의 과목 집중도 데이터 수집
    hour_subject_data = {}
    for subject, hours in time_analysis.items():
        for hour, data in hours.items():
            if hour not in hour_subject_data:
                hour_subject_data[hour] = []
            hour_subject_data[hour].append({
                'subject': subject,
                'concentration': data['concentration'],
                'priority': priorities.get(subject, {}).get('priority', 1)
            })
    
    # 표 데이터 준비
    table_data = []
    for hour in sorted(hour_subject_data.keys()):
        # 집중도와 우선순위를 고려하여 정렬
        sorted_subjects = sorted(
            hour_subject_data[hour],
            key=lambda x: (x['concentration'], x['priority']),
            reverse=True
        )[:3]
        
        row = {
            '시간': f"{hour:02d}:00",
            '1순위': f"{sorted_subjects[0]['subject']} ({sorted_subjects[0]['concentration']:.1f}%)",
            '2순위': f"{sorted_subjects[1]['subject']} ({sorted_subjects[1]['concentration']:.1f}%)" if len(sorted_subjects) > 1 else "-",
            '3순위': f"{sorted_subjects[2]['subject']} ({sorted_subjects[2]['concentration']:.1f}%)" if len(sorted_subjects) > 2 else "-"
        }
        table_data.append(row)
    
    # 표로 출력
    st.table(pd.DataFrame(table_data))
    
    # 시간대별 집중도 표
    st.markdown("#### 📊 시간대별 집중도")
    
    # 모든 시간대 수집
    all_hours = sorted(set(
        hour for subject in time_analysis.values()
        for hour in subject.keys()
    ))
    
    # 표 데이터 준비
    concentration_data = []
    for subject in sorted(time_analysis.keys()):
        row = {'과목': subject}
        for hour in all_hours:
            if hour in time_analysis[subject]:
                row[f"{hour:02d}:00"] = f"{time_analysis[subject][hour]['concentration']:.1f}%"
            else:
                row[f"{hour:02d}:00"] = "-"
        concentration_data.append(row)
    
    # 표로 출력
    st.table(pd.DataFrame(concentration_data))

def generate_schedule(time_analysis, priorities):
    """시간표 생성"""
    schedule = {}
    used_hours = set()
    
    # 우선순위가 높은 순서대로 정렬
    sorted_subjects = sorted(
        priorities.items(),
        key=lambda x: x[1]['priority'],
        reverse=True
    )
    
    for subject, info in sorted_subjects:
        if subject not in time_analysis:
            continue
            
        # 해당 과목의 시간대별 집중도
        hours = time_analysis[subject]
        
        # 사용 가능한 시간대 중 가장 집중도가 높은 시간 선택
        available_hours = {
            hour: data['concentration']
            for hour, data in hours.items()
            if hour not in used_hours
        }
        
        if not available_hours:
            continue
            
        best_hour = max(available_hours.items(), key=lambda x: x[1])[0]
        schedule[best_hour] = subject
        used_hours.add(best_hour)
    
    return dict(sorted(schedule.items())) 