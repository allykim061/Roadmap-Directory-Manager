import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date

# --- [1. 설정 및 상수] ---
PAGE_TITLE = "학생 인원관리 시스템"
SCOPE = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

COL_ID, COL_NAME, COL_SCHOOL, COL_GRADE, COL_DAYS, COL_PERIOD, COL_STATUS = (
    "학생ID", "이름", "학교", "학년", "등원요일", "수업교시", "상태"
)

GRADE_ORDER = ["초1", "초2", "초3", "초4", "초5", "초6", "중1", "중2", "중3", "고1", "고2", "고3"]
WEEKDAY_ORDER = ["월", "화", "수", "목", "금", "토", "일"]

# --- [2. 인쇄 전용 CSS] ---
def get_print_css(orientation="세로"):
    page_size = "A4 portrait" if orientation == "세로" else "A4 landscape"

    return f"""
    <style>
        @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css");
        body, .stApp {{ font-family: 'Pretendard', sans-serif !important; }}
        .report-view {{ border: 1px solid #ccc; padding: 20px; background: white; margin-top: 20px; color: black; }}

        .a4-print-box {{ margin-bottom: 30px; page-break-after: always; }}
        .a4-print-box:last-child {{ page-break-after: auto; }}
        
        .date-footer {{ margin-top: 10px; text-align: right; font-size: 11pt; color: #666; }}
        .check-box {{ display: inline-block; width: 14px; height: 14px; border: 1px solid #000; vertical-align: middle; }}

        /* ✅ 수정 1: 모든 표 기본 틀 (비율 초과 방지) */
        table {{ width: 100%; border-collapse: collapse; table-layout: fixed; margin-bottom: 15px; }}
        
        /* ✅ 수정 2: 가장 위 행(제목) 강제 고정 */
        th {{ 
            border: 1px solid #ccc !important; 
            padding: 8px 4px !important; 
            text-align: center !important; 
            vertical-align: middle !important; /* 강제 상하 가운데 정렬 */
            white-space: nowrap !important; /* 강제 한 줄 유지 */
            word-break: keep-all !important; 
            font-size: 10pt !important; /* 글씨 크기 10pt 고정 */
            background-color: #f0f0f0 !important; /* 화면/인쇄 모두 회색 배경 */
            color: black !important;
        }}
        
        td {{ 
            border: 1px solid #ccc; 
            padding: 6px 4px; 
            text-align: center; 
            vertical-align: middle !important; /* 데이터도 강제 가운데 정렬 */
            word-wrap: break-word; 
            font-size: 10pt; 
            color: black;
        }}

        .daily-table td.name-cell {{
            text-align: left; padding-left: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
            font-size: 10pt; letter-spacing: -0.2px;
        }}

        .weekly-name {{
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
            font-size: 9pt; letter-spacing: -0.6px; margin-bottom: 4px;
        }}

        @media print {{
            div[role="tablist"], header, footer, [data-testid="stSidebar"], [data-testid="stHeader"], .stButton, .stDateInput, .stTextInput, .stCheckbox {{
                display: none !important;
            }}
            .no-print {{ display: none !important; }}
            .block-container {{ padding: 0 !important; max-width: 100% !important; }}
            .report-view {{ border: none !important; padding: 0 !important; margin: 0 !important; }}

            .date-footer {{ margin-top: auto !important; padding-top: 20px !important; color: black; }}

            table {{ font-size: 10pt !important; color: black; border: 1px solid black !important; }}
            th, td {{ border: 1px solid black !important; color: black !important; }}
            
            th {{ background-color: #f0f0f0 !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
            .no-bg-th {{ background-color: white !important; }} 
            
            @page {{ size: {page_size}; margin: 15mm 10mm; }}
        }}
    </style>
    """

# --- [3. 데이터 로드 로직] ---
@st.cache_data(ttl=60)
def load_data():
    try:
        creds_info = st.secrets["SERVICE_ACCOUNT_INFO"]
        creds = Credentials.from_service_account_info(creds_info, scopes=SCOPE)
        client = gspread.authorize(creds)
        sh = client.open(st.secrets["SPREADSHEET_NAME"])
        df = pd.DataFrame(sh.worksheet("students").get_all_records())

        if not df.empty:
            df.columns = df.columns.str.replace(" ", "")
            df[COL_PERIOD] = df[COL_PERIOD].astype(str).str.replace(" ", "")
            df[COL_STATUS] = df[COL_STATUS].astype(str).str.replace(" ", "")
            df[COL_DAYS] = df[COL_DAYS].astype(str).str.replace(" ", "")
        return df
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return pd.DataFrame()

def is_on_day(day_string, target_day):
    return target_day in day_string.split(',')

def is_in_period(period_string, target_period):
    return str(target_period) in period_string.split(',')

def format_student_name(name, school, grade, pause_mark=""):
    s_str, g_str = str(school).strip(), str(grade).strip()
    school_grade = s_str + (g_str[1:] if s_str and g_str and s_str[-1] == g_str[0] else g_str)
    return f"{name}({school_grade}){pause_mark}"

# --- [4. HTML 생성 함수] ---
def generate_table1(df, show_school, month_text):
    df_active = df[df[COL_STATUS] == "재원"].copy()
    html = f"<h2 style='text-align:center; font-size:16pt;'>학년별 명단 ({month_text})</h2>"
    html += "<table><thead><tr><th style='width:15%'>학년</th><th>학생 명단</th><th style='width:10%'>인원수</th></tr></thead><tbody>"
    total = 0
    for grade in GRADE_ORDER:
        group = df_active[df_active[COL_GRADE] == grade]
        if group.empty: continue
        names = [f"{r[COL_NAME]}({r[COL_SCHOOL]})" if show_school else r[COL_NAME] for _, r in group.iterrows()]
        html += f"<tr><th>{grade}</th><td style='text-align:left !important; padding-left:10px !important;'>{', '.join(names)}</td><td>{len(group)}</td></tr>"
        total += len(group)
    html += f"<tr><th>합계</th><td></td><td>{total}</td></tr></tbody></table>"
    return html

def generate_table2(df, month_text):
    df_active = df[df[COL_STATUS] == "재원"].copy()
    html = f"<h2 class='no-print' style='text-align:center; font-size:16pt;'>{month_text} 반편성 내역</h2>"
    target_days = ["월", "화", "수", "목", "금"]
    
    periods_set = set()
    for p_str in df_active[COL_PERIOD]:
        for p in str(p_str).split(','):
            if p.isdigit() and int(p) > 0:
                periods_set.add(int(p))
    periods = sorted(list(periods_set)) if periods_set else [1, 2, 3]

    for p in periods:
        html += "<div class='a4-print-box'><table class='weekly-table'><thead><tr>"
        html += "<th style='width:10%;'>수업시간</th>"
        for d in target_days: html += f"<th style='width:15%;'>{d}</th>"
        html += "<th style='width:15%;'>비고</th></tr></thead><tbody>"
        html += f"<tr><td style='font-weight:bold; font-size:10pt;'>{p}교시</td>"
        
        for d in target_days:
            day_mask = df_active[COL_DAYS].apply(lambda x: is_on_day(x, d))
            period_mask = df_active[COL_PERIOD].apply(lambda x: is_in_period(x, p))
            
            students = df_active[period_mask & day_mask].sort_values(COL_NAME)
            student_list = [f"<div class='weekly-name'>{format_student_name(r[COL_NAME], r[COL_SCHOOL], r[COL_GRADE])}</div>" for _, r in students.iterrows()]
            html += f"<td style='vertical-align:top !important; text-align:center; padding:10px 5px;'>{''.join(student_list)}</td>"
            
        html += f"<td></td></tr></tbody></table><div class='date-footer'>{month_text}</div></div>"
    return html

def generate_table3(df, target_date, include_paused):
    weekday = WEEKDAY_ORDER[target_date.weekday()]
    day_mask = df[COL_DAYS].apply(lambda x: is_on_day(x, weekday))
    df_day = df[day_mask].copy()
    if not include_paused: df_day = df_day[df_day[COL_STATUS] == "재원"]
    
    p_data = {1: [], 2: [], 3: []}
    for p in [1, 2, 3]:
        period_mask = df_day[COL_PERIOD].apply(lambda x: is_in_period(x, p))
        df_p = df_day[period_mask].sort_values(COL_NAME)
        
        for _, row in df_p.iterrows():
            pause = " (휴)" if row[COL_STATUS] == "휴원" else ""
            p_data[p].append(format_student_name(row[COL_NAME], row[COL_SCHOOL], row[COL_GRADE], pause))
            
    max_rows = max(len(p_data[1]), len(p_data[2]), len(p_data[3]))
    html = f"<h2 style='text-align:left; border-bottom:2px solid black; padding-bottom:5px; font-size:16pt;'>{target_date.month}-{target_date.day} {weekday}</h2>"
    html += "<table class='daily-table'><thead><tr>"
    
    # ✅ 수정 3: 가로 폭 비율을 합계 99%로 맞춰 찌그러짐 방지 (18+5+5+5=33% x 3개)
    for p in [1, 2, 3]:
        html += f"<th style='width:18%;'>{p}교시</th><th style='width:5%;'>출석</th><th style='width:5%;'>숙제</th><th style='width:5%;'>배정</th>"
    html += "</tr></thead><tbody>"
    
    for i in range(max_rows):
        html += "<tr>"
        for p in [1, 2, 3]:
            if i < len(p_data[p]): html += f"<td class='name-cell'>{p_data[p][i]}</td><td><div class='check-box'></div></td><td><div class='check-box'></div></td><td></td>"
            else: html += "<td></td><td></td><td></td><td></td>"
        html += "</tr>"
    return html + "</tbody></table>"

def generate_table4(df, show_grade, month_text):
    df_active = df[df[COL_STATUS] == "재원"].copy()
    unique_schools = sorted(df_active[COL_SCHOOL].unique())
    html = f"<h2 style='text-align:center; font-size:16pt;'>학교별 명단 ({month_text})</h2>"
    html += "<table><thead><tr><th style='width:20%'>학교</th><th>학생 명단</th><th style='width:10%'>인원수</th></tr></thead><tbody>"
    total = 0
    for school in unique_schools:
        group = df_active[df_active[COL_SCHOOL] == school]
        names = [f"{r[COL_NAME]}({r[COL_GRADE]})" if show_grade else r[COL_NAME] for _, r in group.iterrows()]
        html += f"<tr><th>{school}</th><td style='text-align:left !important; padding-left:10px !important;'>{', '.join(names)}</td><td>{len(group)}</td></tr>"
        total += len(group)
    html += f"<tr><th>합계</th><td></td><td>{total}</td></tr></tbody></table>"
    return html

# --- [5. 메인 앱] ---
def main():
    st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon="icon.png", 
        layout="wide"
    )

    df = load_data()
    with st.sidebar:
        print_orientation = st.radio("용지 방향", ["세로", "가로"])
        st.markdown(get_print_css(print_orientation), unsafe_allow_html=True)
        if st.button("새로고침"): st.cache_data.clear(); st.rerun()

    st.markdown('<div class="no-print" style="background-color:#f1f3f5;padding:15px;border-radius:8px;border-left:5px solid #868396;margin-bottom:20px;">🖨️ 인쇄: Ctrl + P</div>', unsafe_allow_html=True)
    tab_list = st.tabs(["전체 목록", "1. 학년별 명단", "2. 수업시간 명단", "3. 출석부", "4. 학교별 명단"])

    with tab_list[0]:
        st.markdown("<h2 style='font-size:16pt;'>등록 학생 목록</h2>", unsafe_allow_html=True)
        if not df.empty: st.dataframe(df[[COL_NAME, COL_SCHOOL, COL_GRADE, COL_DAYS, COL_PERIOD, COL_STATUS]], use_container_width=True, hide_index=True)
    with tab_list[1]:
        if not df.empty:
            m1 = st.text_input("제목(연/월)", value=datetime.now().strftime("%Y.%m"), key="m1")
            st.markdown(f"<div class='report-view'>{generate_table1(df, True, m1)}</div>", unsafe_allow_html=True)
    with tab_list[2]:
        if not df.empty:
            m2 = st.text_input("하단 표기", value=datetime.now().strftime("%Y-%m"), key="m2")
            st.markdown(f"<div class='report-view'>{generate_table2(df, m2)}</div>", unsafe_allow_html=True)
    with tab_list[3]:
        if not df.empty:
            d3 = st.date_input("날짜 선택", value=date.today())
            st.markdown(f"<div class='report-view'>{generate_table3(df, d3, False)}</div>", unsafe_allow_html=True)
    with tab_list[4]:
        if not df.empty:
            m4 = st.text_input("제목(연/월)", value=datetime.now().strftime("%Y.%m"), key="m4")
            st.markdown(f"<div class='report-view'>{generate_table4(df, True, m4)}</div>", unsafe_allow_html=True)

if __name__ == "__main__": main()

