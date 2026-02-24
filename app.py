import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date
import re

# --- [1. 설정 및 상수] ---
PAGE_TITLE = "학생 인원관리 시스템"
SCOPE = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

COL_ID, COL_NAME, COL_SCHOOL, COL_GRADE, COL_DAYS, COL_PERIOD, COL_STATUS = (
    "학생ID", "이름", "학교", "학년", "등원요일", "수업교시", "상태"
)

GRADE_ORDER = ["초1", "초2", "초3", "초4", "초5", "초6", "중1", "중2", "중3", "고1", "고2", "고3"]
WEEKDAY_ORDER = ["월", "화", "수", "목", "금", "토", "일"]

# --- [2. 인쇄 전용 CSS (극한 압축 + 전체목록 분리 모드)] ---
def get_print_css(orientation="세로"):
    page_size = "A4 portrait" if orientation == "세로" else "A4 landscape"

    return f"""
    <style>
        @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css");
        body, .stApp {{ font-family: 'Pretendard', sans-serif !important; }}
        .report-view {{ border: 1px solid #ccc; padding: 20px; background: white; margin-top: 20px; color: black; }}

        .a4-print-box {{ margin-bottom: 15px; page-break-after: always; }}
        .a4-print-box:last-child {{ page-break-after: auto; }}

        .date-footer {{ margin-top: 5px; text-align: right; font-size: 11pt; color: #666; }}
        .check-box {{ display: inline-block; width: 14px; height: 14px; border: 1px solid #000; vertical-align: middle; }}

        table {{ width: 100%; border-collapse: collapse; table-layout: fixed; margin-bottom: 10px; }}

        th {{
            border: 1px solid #ccc !important; padding: 8px 4px !important;
            text-align: center !important; vertical-align: middle !important;
            white-space: nowrap !important; word-break: keep-all !important;
            font-size: 10pt !important; background-color: #f0f0f0 !important; color: black !important;
        }}

        td {{
            border: 1px solid #ccc; padding: 6px 4px; text-align: center;
            vertical-align: middle !important; word-wrap: break-word;
            font-size: 10pt; color: black;
        }}

        .daily-table td.name-cell {{
            text-align: left; padding-left: 4px; white-space: nowrap;
            overflow: hidden; text-overflow: ellipsis; font-size: 10pt; letter-spacing: -0.2px;
        }}

        .weekly-name {{
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
            font-size: 9pt; letter-spacing: -0.6px; margin-bottom: 3px;
        }}

        /* ✅ 화면(Screen)에서만 적용: 인쇄용 전체 표를 숨김 */
        @media screen {{
            .print-only {{ display: none !important; }}
        }}

        /* 🖨️ 인쇄(Print) 시 적용 로직 */
        @media print {{
            div[role="tablist"], header, footer, [data-testid="stSidebar"], [data-testid="stHeader"],
            .stButton, .stDateInput, .stTextInput, .stCheckbox {{ display: none !important; }}
            .no-print {{ display: none !important; }}
            .block-container {{ padding: 0 !important; max-width: 100% !important; }}
            .report-view {{ border: none !important; padding: 0 !important; margin: 0 !important; }}
            
            /* ✅ 인쇄 시 스트림릿 스크롤 표를 숨기고, 인쇄용 전체 표를 보여줌 */
            [data-testid="stDataFrame"] {{ display: none !important; }}
            .print-only {{ display: block !important; }}
            
            /* 종이 여백 극한 최소화 (상하 8mm, 좌우 5mm) */
            @page {{ size: {page_size}; margin: 8mm 5mm; }}

            h2 {{ font-size: 12pt !important; margin-bottom: 5px !important; padding-bottom: 2px !important; }}

            table {{ font-size: 7.5pt !important; color: black; border: 1px solid black !important; margin-bottom: 5px !important; page-break-inside: auto; }}
            tr {{ page-break-inside: avoid; page-break-after: auto; }}
            th, td {{ border: 1px solid black !important; color: black !important; }}
            
            /* 제목칸(th) 높이 축소 및 8pt 유지 */
            th {{ background-color: #f0f0f0 !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; font-size: 8pt !important; padding: 4px 2px !important; }}
            .no-bg-th {{ background-color: white !important; }}

            /* 데이터칸(td) 위아래 여백 2px로 축소, 줄간격 1.0 */
            td {{ padding: 2px 1px !important; line-height: 1.0 !important; }}
            
            /* 학생 이름 글자 크기 최소화 (7.5pt ~ 7pt) 및 자간 축소 */
            .daily-table td.name-cell {{ font-size: 7.5pt !important; letter-spacing: -0.5px !important; }}
            .weekly-name {{ font-size: 7pt !important; margin-bottom: 1px !important; letter-spacing: -0.5px !important; }} 
            
            /* 체크박스 소형화 (10px) */
            .check-box {{ width: 10px !important; height: 10px !important; }}
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

# --- [4. 데이터 필터링 도우미 함수] ---
def split_days(days_str: str) -> list[str]:
    s = str(days_str).replace(" ", "")
    return [x for x in s.split(",") if x]

def periods_has_day_markers(periods_str: str) -> bool:
    s = str(periods_str)
    return any(d in s for d in WEEKDAY_ORDER)

def extract_period_numbers(periods_str: str) -> list[int]:
    s = str(periods_str).replace(" ", "")
    nums = re.findall(r"\d+", s) 
    out = []
    for n in nums:
        try:
            v = int(n)
            if v > 0: out.append(v)
        except: pass
    return out

def match_attendance(days_str, periods_str, target_day, target_period) -> bool:
    days = split_days(days_str)
    if target_day not in days: return False
    pstr = str(periods_str).replace(" ", "")
    if not pstr: return False

    if periods_has_day_markers(pstr):
        return f"{target_day}{target_period}" in pstr.split(",")
    else:
        return str(target_period) in [str(n) for n in extract_period_numbers(pstr)]

def format_student_name(name, school, grade, pause_mark=""):
    s_str, g_str = str(school).strip(), str(grade).strip()
    school_grade = s_str + (g_str[1:] if s_str and g_str and s_str[-1] == g_str[0] else g_str)
    return f"{name}({school_grade}){pause_mark}"

# --- [5. HTML 생성 함수] ---
def generate_total_list_html(df):
    """✅ 인쇄 전용 '전체 학생 목록' HTML (스크롤 없이 전부 펼쳐짐)"""
    html = "<table style='width:100%;'><thead><tr>"
    cols = [COL_NAME, COL_SCHOOL, COL_GRADE, COL_DAYS, COL_PERIOD, COL_STATUS]
    widths = {COL_NAME: "15%", COL_SCHOOL: "25%", COL_GRADE: "10%", COL_DAYS: "20%", COL_PERIOD: "20%", COL_STATUS: "10%"}
    
    for c in cols:
        w = widths.get(c, "15%")
        html += f"<th style='width:{w};'>{c}</th>"
    html += "</tr></thead><tbody>"
    
    for _, r in df.iterrows():
        html += "<tr>"
        for c in cols:
            html += f"<td>{r[c]}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    return html

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
    target_days = ["월", "화", "수", "목"]
    
    periods_set = set()
    for p_str in df_active[COL_PERIOD]:
        for n in extract_period_numbers(p_str):
            if n > 0: periods_set.add(n)
    periods = sorted(periods_set) if periods_set else [1, 2, 3]

    for p in periods:
        html += "<div class='a4-print-box'><table class='weekly-table'><thead><tr>"
        html += "<th style='width:10%;'>수업시간</th>"
        for d in target_days: html += f"<th style='width:20%;'>{d}</th>"
        html += "<th style='width:10%;'>비고</th></tr></thead><tbody>"
        html += f"<tr><td style='font-weight:bold;'>{p}교시</td>"
        
        for d in target_days:
            condition = df_active.apply(lambda row: match_attendance(row[COL_DAYS], row[COL_PERIOD], d, p), axis=1)
            students = df_active[condition].sort_values(COL_NAME)
            student_list = [f"<div class='weekly-name'>{format_student_name(r[COL_NAME], r[COL_SCHOOL], r[COL_GRADE])}</div>" for _, r in students.iterrows()]
            html += f"<td style='vertical-align:top !important; text-align:center; padding:5px 2px;'>{''.join(student_list)}</td>"
            
        html += f"<td></td></tr></tbody></table><div class='date-footer'>{month_text}</div></div>"
    return html

def generate_table3(df, target_date, include_paused):
    weekday = WEEKDAY_ORDER[target_date.weekday()]
    day_mask = df[COL_DAYS].apply(lambda x: weekday in split_days(x))
    df_day = df[day_mask].copy()

    if not include_paused: df_day = df_day[df_day[COL_STATUS] == "재원"]

    p_data = {1: [], 2: [], 3: []}
    for p in [1, 2, 3]:
        period_mask = df_day.apply(lambda row: match_attendance(row[COL_DAYS], row[COL_PERIOD], weekday, p), axis=1)
        df_p = df_day[period_mask].sort_values(COL_NAME)
        for _, row in df_p.iterrows():
            pause = " (휴)" if row[COL_STATUS] == "휴원" else ""
            p_data[p].append(format_student_name(row[COL_NAME], row[COL_SCHOOL], row[COL_GRADE], pause))

    max_rows = max(len(p_data[1]), len(p_data[2]), len(p_data[3])) if not df_day.empty else 0

    html = f"<h2 style='text-align:left; border-bottom:2px solid black; padding-bottom:5px;'>{target_date.month}-{target_date.day} {weekday}</h2>"
    html += "<table class='daily-table'><thead><tr>"
    
    for p in [1, 2, 3]:
        html += f"<th style='width:21%;'>{p}교시</th><th style='width:4%;'>출석</th><th style='width:4%;'>숙제</th><th style='width:4%;'>배정</th>"
    html += "</tr></thead><tbody>"

    for i in range(max_rows):
        html += "<tr>"
        for p in [1, 2, 3]:
            if i < len(p_data[p]):
                html += f"<td class='name-cell'>{p_data[p][i]}</td><td><div class='check-box'></div></td><td><div class='check-box'></div></td><td></td>"
            else:
                html += "<td></td><td></td><td></td><td></td>"
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

# --- [6. 메인 앱] ---
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
        if st.button("새로고침"):
            st.cache_data.clear()
            st.rerun()

    st.markdown('<div class="no-print" style="background-color:#f1f3f5;padding:15px;border-radius:8px;border-left:5px solid #868396;margin-bottom:20px;">🖨️ 인쇄: Ctrl + P</div>', unsafe_allow_html=True)

    tab_list = st.tabs(["전체 목록", "1. 학년별 명단", "2. 수업시간 명단", "3. 출석부", "4. 학교별 명단"])

    with tab_list[0]:
        st.markdown("<h2 style='font-size:16pt;'>등록 학생 목록</h2>", unsafe_allow_html=True)
        if not df.empty: 
            # 1. 화면 전용: 인터랙티브 스트림릿 표 (정렬/스크롤 가능)
            st.dataframe(df[[COL_NAME, COL_SCHOOL, COL_GRADE, COL_DAYS, COL_PERIOD, COL_STATUS]], use_container_width=True, hide_index=True)
            
            # 2. 인쇄 전용: 잘리지 않고 전체 인쇄되는 HTML 표 (화면에선 안 보임)
            total_list_html = generate_total_list_html(df)
            st.markdown(f"<div class='print-only'>{total_list_html}</div>", unsafe_allow_html=True)
            
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
