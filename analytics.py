# analytics.py

import streamlit as st
import pandas as pd
from database import get_user_logs, delete_study_log
from database import safe_parse_datetime

def render_recent_logs():
    """최근 공부 기록만 표시 (메인 페이지용)"""
    st.markdown("## 📊 공부 기록")
    df = get_user_logs(st.session_state.user_id)
    
    if df.empty:
        st.write("아직 기록이 없습니다.")
        return
    
    # 시간 형식 변환
    df["start_time"] = df["start_time"].apply(safe_parse_datetime)
    df["end_time"] = df["end_time"].apply(safe_parse_datetime)
    
    # 데이터 전처리
    df = preprocess_logs(df)
    
    # 최근 10개 기록만 표시
    recent_df = df.head(10)
    
    # 표시용 데이터프레임 준비
    display_df = recent_df[["start_time", "end_time", "subject", "duration", "felt_minutes", "concentrate_rate"]].copy()
    display_df["start_time"] = display_df["start_time"].dt.strftime('%m/%d %H:%M')
    
    # end_time과 duration을 안전하게 처리 (진행중인 세션 고려)
    display_df["end_time"] = display_df["end_time"].apply(
        lambda x: "진행중" if pd.isna(x) else x.strftime('%H:%M')
    )
    display_df["duration"] = display_df["duration"].apply(
        lambda x: "진행중" if pd.isna(x) else f"{int(round(x))}분"
    )
    
    # felt_minutes와 concentrate_rate도 안전하게 처리
    display_df["felt_minutes"] = display_df["felt_minutes"].apply(
        lambda x: "-" if pd.isna(x) else str(int(x))
    )
    display_df["concentrate_rate"] = display_df["concentrate_rate"].apply(
        lambda x: "-" if pd.isna(x) else f"{round(x, 1)}%"
    )
    
    # 컬럼명 한글로 변경 (안전한 방식)
    display_df = display_df.rename(columns={
        "start_time": "시작시간",
        "end_time": "종료시간", 
        "subject": "과목",
        "duration": "시간(분)",
        "felt_minutes": "체감시간(분)",
        "concentrate_rate": "집중도(%)"
    })
    
    # 사용법 안내
    st.info("💡 **삭제할 기록이 있다면 아래 표에서 해당 행을 클릭하세요**")
    
    # 행 선택 가능한 데이터프레임
    event = st.dataframe(
        display_df,
        on_select="rerun",
        selection_mode="single-row",
        use_container_width=True
    )
    
    # 행이 선택되었을 때 삭제 버튼 표시
    if len(event.selection['rows']) > 0:
        selected_row_idx = event.selection['rows'][0]
        selected_log_id = recent_df.iloc[selected_row_idx]['id']
        selected_subject = recent_df.iloc[selected_row_idx]['subject']
        
        # 디버깅 정보 표시
        # st.info(f"🔍 선택된 행: {selected_row_idx}, DB ID: {selected_log_id}, 과목: {selected_subject}")
        
        # 진행중인 세션인지 확인
        is_active = pd.isna(recent_df.iloc[selected_row_idx]['end_time'])
        
        if is_active:
            st.warning("🔄 진행중인 세션은 삭제할 수 없습니다.")
        else:
            st.warning(f"선택된 기록: **{selected_subject}** ")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🗑️ 선택된 기록 삭제", type="primary"):
                    # 삭제 시도 전에 정보 확인
                    st.info(f"삭제 시도: user_id={st.session_state.user_id}, log_id={selected_log_id}")
                    
                    if delete_study_log(st.session_state.user_id, selected_log_id):
                        st.success("✅ 기록이 삭제되었습니다.")
                        st.rerun()
                    else:
                        st.error("❌ 삭제에 실패했습니다.")
                        # 실패 원인 추가 정보
                        st.error(f"실패 상세: user_id={st.session_state.user_id}, log_id={selected_log_id} (타입: {type(selected_log_id)})")
            
            with col2:
                if st.button("❌ 취소"):
                    st.rerun()
    
    if len(df) > 10:
        st.info(f"💡 전체 {len(df)}개 기록 중 최근 10개만 표시됩니다. 상세 분석은 아래 탭에서 확인하세요!")

def render_analytics_tabs():
    """상세 분석 탭들 렌더링"""
    st.markdown("## 📈 상세 분석")
    df = get_user_logs(st.session_state.user_id)
    
    if df.empty:
        st.write("분석할 데이터가 없습니다.")
        return
    
    # 데이터 전처리
    df = preprocess_logs(df)
    
    # 탭 생성
    tab1, tab2, tab3, tab4 = st.tabs(["📋 전체 기록", "📚 과목별 분석", "📅 날짜별 트렌드", "🎯 집중도 분석"])
    
    with tab1:
        render_all_records(df)
    
    with tab2:
        render_subject_analysis(df)
    
    with tab3:
        render_daily_trend(df)
    
    with tab4:
        render_concentration_stats(df)

def render_subject_analysis(df):
    """과목별 상세 분석"""
    st.subheader("과목별 총 공부 시간")
    
    # 과목별 총 시간
    subj_summary = df.groupby("subject")["duration"].sum().to_frame()
    if not subj_summary.empty:
        st.bar_chart(subj_summary)
        
        # 과목별 상세 통계
        st.subheader("과목별 상세 통계")
        subj_stats = df.groupby("subject").agg({
            'duration': ['count', 'sum', 'mean'],
            'concentrate_rate': 'mean'
        }).round(2)
        subj_stats.columns = ['세션 수', '총 시간(분)', '평균 시간(분)', '평균 집중도(%)']
        st.dataframe(subj_stats, use_container_width=True)
    else:
        st.write("과목별 데이터가 없습니다.")

def preprocess_logs(df):
    """로그 데이터 전처리"""
    # 원본 DataFrame을 수정하지 않도록 복사본 생성
    df = df.copy()
    df["start_time"] = pd.to_datetime(df["start_time"])
    df["end_time"] = pd.to_datetime(df["end_time"])
    df["duration"] = (df["end_time"] - df["start_time"]).dt.total_seconds() / 60
    return df

def render_all_records(df):
    """전체 기록 표시"""
    st.subheader("전체 공부 기록")
    display_df = df[["start_time", "end_time", "subject", "duration", "felt_minutes", "concentrate_rate"]].copy()
    display_df = display_df.sort_values(by="start_time", ascending=False)
    st.dataframe(display_df, use_container_width=True)
    
    # 전체 통계 요약
    total_sessions = len(df)
    total_time = df['duration'].sum()
    avg_session = df['duration'].mean()
    avg_focus = df['concentrate_rate'].mean()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("총 세션 수", f"{total_sessions}회")
    with col2:
        st.metric("총 공부 시간", f"{total_time:.0f}분")
    with col3:
        st.metric("평균 세션 시간", f"{avg_session:.0f}분")
    with col4:
        st.metric("평균 집중도", f"{avg_focus:.1f}%")

def render_daily_trend(df):
    """날짜별 공부 시간 트렌드 차트"""
    st.subheader("날짜별 공부 시간 트렌드")
    df["date"] = df["start_time"].dt.date
    daily = df.groupby("date").agg({
        'duration': ['sum', 'count']
    }).rename(columns={'duration': '총 공부시간(분)', 'count': '세션 수'})
    
    if not daily.empty:
        st.line_chart(daily['총 공부시간(분)'])
        
        st.subheader("날짜별 상세 데이터")
        st.dataframe(daily, use_container_width=True)
    else:
        st.write("날짜별 데이터가 없습니다.")

def render_concentration_stats(df):
    """과목별 집중도 통계"""
    st.subheader("집중도 분석")
    
    if not df.empty:
        # 과목별 집중도 통계
        st.subheader("과목별 집중도 통계 (%)")
        focus_stats = df.groupby("subject")["concentrate_rate"] \
                        .agg(["count", "mean", "std", "min", "max"]) \
                        .rename(columns={
                            "count": "세션 수",
                            "mean": "평균 집중도(%)", 
                            "std": "집중도 편차", 
                            "min": "최저 집중도(%)", 
                            "max": "최고 집중도(%)"
                        }).round(2)
        st.dataframe(focus_stats, use_container_width=True)
        
        # 집중도 구간별 분석
        st.subheader("집중도 구간별 분석")
        df['focus_range'] = pd.cut(df['concentrate_rate'], 
                                  bins=[0, 50, 70, 85, 100], 
                                  labels=['낮음(0-50%)', '보통(50-70%)', '좋음(70-85%)', '매우좋음(85-100%)'])
        focus_range_stats = df['focus_range'].value_counts()
        st.bar_chart(focus_range_stats)
    else:
        st.write("집중도 데이터가 없습니다.") 