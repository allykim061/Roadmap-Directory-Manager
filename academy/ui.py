# academy/ui.py
import streamlit as st
import pandas as pd

from .config import (
    COL_NAME, COL_SCHOOL, COL_GRADE, COL_DAYS, COL_PERIOD, COL_STATUS,
    GRADE_ORDER, WEEKDAY_ORDER
)
from .data import load_data
from .styles import get_print_css_cached
from .tables import (
    generate_total_list_html,
    generate_table1, generate_table2, generate_table3, generate_table4
)
from .filters import filter_students_for_day_period
from .utils import get_student_key, sanitize_letter, now_kst, today_kst
from .utils import split_days

def run_app():
    df = load_data()

    # ✅ 배정 저장소(session_state)
    if "assignments" not in st.session_state:
        st.session_state["assignments"] = {}  # {date_iso: {(period, student_key): "A"}}

    # 사이드바
    with st.sidebar:
        print_orientation = st.radio("용지 방향", ["세로", "가로"])
        st.markdown(get_print_css_cached(print_orientation), unsafe_allow_html=True)

        if st.button("새로고침"):
            st.cache_data.clear()
            st.rerun()

    st.markdown(
        '<div class="no-print" style="background-color:#f1f3f5;padding:15px;border-radius:8px;'
        'border-left:5px solid #868396;margin-bottom:20px;">🖨️ 인쇄: 우측 상단 ⋮ ➜ Print 선택</div>',
        unsafe_allow_html=True,
    )

    tab_list = st.tabs(["전체 목록", "1. 학년별 명단", "2. 수업시간 명단", "3. 출석부", "4. 학교별 명단"])

    # 탭 0
    with tab_list[0]:
        st.markdown("<h2 style='font-size:16pt;'>등록 학생 목록</h2>", unsafe_allow_html=True)
        if not df.empty:
            st.dataframe(
                df[[COL_NAME, COL_SCHOOL, COL_GRADE, COL_DAYS, COL_PERIOD, COL_STATUS]],
                width="stretch",
                hide_index=True,
            )
            st.markdown(f"<div class='print-only'>{generate_total_list_html(df)}</div>", unsafe_allow_html=True)

    # 탭 1
    with tab_list[1]:
        if not df.empty:
            col1, col2 = st.columns([3, 1])
            with col1:
                m1 = st.text_input("제목(연/월)", value=now_kst().strftime("%Y.%m"), key="m1")
            with col2:
                show_school_t1 = st.checkbox("학교명 표시", value=True, key="chk_school_m1")
                show_count_t1 = st.checkbox("학교별 인원수 표시", value=True, key="chk_count_m1")

            st.markdown(
                f"<div class='report-view'>{generate_table1(df, show_school_t1, show_count_t1, m1)}</div>",
                unsafe_allow_html=True,
            )

    # 탭 2
    with tab_list[2]:
        if not df.empty:
            m2 = st.text_input("하단 표기", value=now_kst().strftime("%Y-%m"), key="m2")
            st.markdown(f"<div class='report-view'>{generate_table2(df, m2)}</div>", unsafe_allow_html=True)

    # 탭 3
    with tab_list[3]:
        if not df.empty:
            # ✅ 여기 중요: 배포(UTC)에서도 KST 기준 날짜로 기본값 고정
            d3 = st.date_input("날짜 선택", value=today_kst())

            weekday = WEEKDAY_ORDER[d3.weekday()]
            date_key = d3.isoformat()
            day_store = st.session_state["assignments"].setdefault(date_key, {})

            # 해당 요일 + 재원만
            day_mask = df[COL_DAYS].astype(str).apply(lambda x: weekday in split_days(x))
            df_day = df[day_mask].copy()
            df_day = df_day[df_day[COL_STATUS] == "재원"]

            grade_sort_map = {g: i for i, g in enumerate(GRADE_ORDER)}

            # 교시별 학생 목록 (안정 필터)
            per_period_students = {}
            for p in [1, 2, 3]:
                df_p = filter_students_for_day_period(df_day, weekday, p)
                df_p["_grade_order"] = df_p[COL_GRADE].map(grade_sort_map).fillna(999)
                df_p = df_p.sort_values(["_grade_order", COL_SCHOOL, COL_NAME])
                per_period_students[p] = df_p

            # 배정 입력 UI (인쇄 제외)
            st.markdown('<div class="no-print">', unsafe_allow_html=True)
            with st.expander("선생님 배정 입력 열기/닫기", expanded=False):
                st.caption("알파벳 1글자만 입력하세요. **배정 적용**을 눌러야 표/인쇄에 반영됩니다.")

                with st.form(key=f"assign_form_{date_key}", clear_on_submit=False):
                    c1, c2, c3 = st.columns(3)

                    def render_period_inputs(col, p):
                        with col:
                            st.markdown(f"**{p}교시**")
                            df_p = per_period_students.get(p, pd.DataFrame())
                            if df_p.empty:
                                st.caption("해당 교시 학생 없음")
                                return

                            for _, row in df_p.iterrows():
                                skey = get_student_key(row)
                                current = day_store.get((p, skey), "")
                                label = f"{row[COL_NAME]} ({row[COL_SCHOOL]} {row[COL_GRADE]})"

                                st.text_input(
                                    label,
                                    value=current,
                                    max_chars=1,
                                    key=f"assign_input_{date_key}_{p}_{skey}",
                                )

                    render_period_inputs(c1, 1)
                    render_period_inputs(c2, 2)
                    render_period_inputs(c3, 3)

                    apply_clicked = st.form_submit_button("배정 적용")

                    if apply_clicked:
                        for p in [1, 2, 3]:
                            df_p = per_period_students.get(p, pd.DataFrame())
                            if df_p.empty:
                                continue
                            for _, row in df_p.iterrows():
                                skey = get_student_key(row)
                                v = st.session_state.get(f"assign_input_{date_key}_{p}_{skey}", "")
                                day_store[(p, skey)] = sanitize_letter(v)

                        st.success("배정이 적용되었습니다. 아래 출석부/인쇄에 반영됩니다.")
            st.markdown("</div>", unsafe_allow_html=True)

            # 출석부 표
            st.markdown(f"<div class='report-view'>{generate_table3(df, d3, False, day_store)}</div>", unsafe_allow_html=True)

    # 탭 4
    with tab_list[4]:
        if not df.empty:
            m4 = st.text_input("제목(연/월)", value=now_kst().strftime("%Y.%m"), key="m4")
            st.markdown(f"<div class='report-view'>{generate_table4(df, True, m4)}</div>", unsafe_allow_html=True)