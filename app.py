import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date
import re

def norm(s: str) -> str:
    s = str(s)
    s = s.replace("\u00A0", "")  # NBSP
    s = s.replace("\u3000", "")  # 전각공백
    s = re.sub(r"\s+", "", s)    # 탭/줄바꿈 포함 전부
    return s

# --- [1. 설정 및 상수] ---
PAGE_TITLE = "학생 인원관리 시스템"
SCOPE = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

COL_ID, COL_NAME, COL_SCHOOL, COL_GRADE, COL_DAYS, COL_PERIOD, COL_STATUS = (
    "학생ID", "이름", "학교", "학년", "등원요일", "수업교시", "상태"
)

GRADE_ORDER = ["초1", "초2", "초3", "초4", "초5", "초6", "중1", "중2", "중3", "고1", "고2", "고3"]
WEEKDAY_ORDER = ["월", "화", "수", "목", "금", "토", "일"]

# --- [2. 인쇄 전용 CSS (전체목록 분리 모드)] ---
# --- [2. 인쇄 전용 CSS (전체목록 분리 모드)] ---
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

        /* ===== ✅ 3번 표(table3) 전용 CSS: 여기 추가 ===== */
        .table3-custom {{ border-collapse: collapse !important; width: 100%; }}

        .table3-custom th {{
            border-top: 1px solid black !important;
            border-bottom: 2px solid black !important;
            border-left: 1px solid #ccc !important;
            border-right: 1px solid #ccc !important;
        }}

        .table3-custom tbody tr {{ border-top: 0px !important; border-bottom: 0px !important; }}

        .table3-custom tbody td {{
            border-top: 0px !important;
            border-bottom: 0px !important;
            border-left: 1px solid #ccc !important;
            border-right: 1px solid #ccc !important;
        }}

        /* 마지막 줄만 아래 굵은선 */
        .table3-custom tbody tr:last-child td {{
            border-bottom: 2px solid black !important;
        }}

        .assign-cell {{ font-weight: bold; }}

        @media print {{
            .table3-custom tbody td {{
                border-left: 1px solid black !important;
                border-right: 1px solid black !important;
            }}
            .table3-custom tbody tr:last-child td {{
                border-bottom: 2px solid black !important;
            }}
        }}
        /* ===== ✅ table3 전용 CSS 끝 ===== */

        /* ✅ 화면(Screen)에서만 적용: 인쇄용 전체 표를 숨김 */
        @media screen {{
            .print-only {{ display: none !important; }}
        }}

        /* 🖨️ 인쇄(Print) 시 적용 로직 */
        @media print {{

            /* ✅ [에러 수정] f-string 내부 CSS 중괄호/블록 닫힘 오류 수정 */
            *, *::before, *::after {{ box-sizing: border-box !important; }}

            /* 2번 표 전용 가로 넘침 방지 */
            .weekly-table th,
            .weekly-table td {{
                overflow: hidden !important;
            }}

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

            /* 인쇄 시 배정 입력창 숨기기 */
            div[role="tablist"], header, footer, [data-testid="stSidebar"], [data-testid="stHeader"],
            .stButton, .stDateInput, .stTextInput, .stCheckbox, [data-testid="stExpander"] {{ 
                display: none !important; 
                }}
        }}
    </style>
    """

@st.cache_data
def get_print_css_cached(orientation: str) -> str:
    return get_print_css(orientation)

# --- [3. 데이터 로드 로직] ---
@st.cache_data(ttl=300, show_spinner="loading...")
def load_data():
    try:
        creds_info = st.secrets["SERVICE_ACCOUNT_INFO"]
        creds = Credentials.from_service_account_info(creds_info, scopes=SCOPE)
        client = gspread.authorize(creds)
        sh = client.open(st.secrets["SPREADSHEET_NAME"])
        df = pd.DataFrame(sh.worksheet("students").get_all_records())

        if not df.empty:
            
            # 1. 모든 컬럼명의 앞뒤, 중간 공백 제거
            df.columns = [norm(c) for c in df.columns]
            # 2. 필수 컬럼이 있는지 검증
            required = {COL_ID, COL_NAME, COL_SCHOOL, COL_GRADE, COL_DAYS, COL_PERIOD, COL_STATUS}
            missing = [c for c in required if c not in df.columns]
            if missing:
                st.error(f"구글 시트 헤더가 일치하지 않습니다. 누락된 항목: {missing}")
                st.info(f"현재 인식된 항목: {list(df.columns)}")
                st.stop()

            df[COL_PERIOD] = df[COL_PERIOD].astype(str).apply(norm)
            df[COL_STATUS] = df[COL_STATUS].astype(str).apply(norm)
            df[COL_DAYS]   = df[COL_DAYS].astype(str).apply(norm)
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
        except:
            pass
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

def filter_students_for_day_period(df: pd.DataFrame, weekday: str, period: int) -> pd.DataFrame:
    """
    df에서 weekday에 등원하고, period에 해당하는 학생만 필터링해 반환.
    row-wise apply(axis=1) 없이 column(Series) 기반으로만 처리해서 안정적.
    """
    if df is None or df.empty:
        return df.copy() if df is not None else pd.DataFrame()

    # 요일 포함 여부 (문자열 전처리 포함)
    days = df[COL_DAYS].astype(str).apply(norm)
    mask_day = days.apply(lambda s: weekday in [x for x in s.split(",") if x])

    # 교시 문자열 전처리
    pstr = df[COL_PERIOD].astype(str).apply(norm)

    # "월1,수2" 처럼 요일 마커가 있는지
    has_marker = pstr.apply(lambda s: any(d in s for d in WEEKDAY_ORDER))

    # case1: 요일마커가 있는 경우: "월1" 같은 토큰이 있는지
    mask_marker = has_marker & pstr.apply(lambda s: f"{weekday}{period}" in [x for x in s.split(",") if x])

    # case2: 숫자만 있는 경우: "1,2,3" 안에 period 숫자가 있는지
    mask_numeric = (~has_marker) & pstr.apply(lambda s: str(period) in re.findall(r"\d+", s))

    return df[mask_day & (mask_marker | mask_numeric)].copy()

def format_student_name(name, school, grade, pause_mark=""):
    s_str, g_str = str(school).strip(), str(grade).strip()
    school_grade = s_str + (g_str[1:] if s_str and g_str and s_str[-1] == g_str[0] else g_str)
    return f"{name}({school_grade}){pause_mark}"

def get_student_key(row) -> str:
    """배정 저장용 고유키: 학생ID가 있으면 그걸 우선 사용, 없으면 (이름|학교|학년)"""
    sid = str(row.get(COL_ID, "")).strip() if isinstance(row, dict) else str(row[COL_ID]).strip() if COL_ID in row else ""
    if sid and sid.lower() != "nan":
        return f"id:{sid}"
    name = str(row[COL_NAME]).strip()
    school = str(row[COL_SCHOOL]).strip()
    grade = str(row[COL_GRADE]).strip()
    return f"ng:{name}|{school}|{grade}"

def sanitize_letter(v: str) -> str:
    s = str(v).strip().upper()
    if not s:
        return ""
    ch = s[0]
    return ch if ("A" <= ch <= "Z") else ""

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

def generate_table1(df, show_school, show_count, month_text):
    df_active = df[df[COL_STATUS] == "재원"].copy()
    html = f"<h2 style='text-align:center; font-size:16pt;'>학년별 명단 ({month_text})</h2>"
    html += "<table style='font-size: 4pt;'><thead><tr><th style='width:15%'>학년</th><th>학생 명단</th><th style='width:15%'>인원수</th></tr></thead><tbody>"

    total = 0
    for grade in GRADE_ORDER:
        group = df_active[df_active[COL_GRADE] == grade]
        if group.empty: continue

        group_sorted = group.sort_values(by=[COL_SCHOOL, COL_NAME])

        if show_school or show_count:
            formatted_groups = []
            for school, school_group in group_sorted.groupby(COL_SCHOOL, sort=False):
                names_list = school_group[COL_NAME].tolist()
                names_str = " ".join(names_list)
                count = len(names_list)

                school_text = f"【{school}】" if show_school else ""
                count_text = f" {count}명" if (show_count and count >= 4) else ""

                if count == 1:
                    formatted_groups.append(f"{school_text}{names_str}{count_text}")
                else:
                    formatted_groups.append(f"{school_text}[{names_str}]{count_text}")

            names_final_str = " ".join(formatted_groups)
        else:
            names_final_str = " ".join(group_sorted[COL_NAME].tolist())

        html += f"<tr><th>{grade}<td style='text-align:left !important; padding-top: 25px; padding-bottom: 25px; padding-left:2px !important; font-size: 10pt; line-height: 2;'>{names_final_str}</td><td>{len(group)}</td></tr>"
        total += len(group)

    df_active['days_count'] = df_active[COL_DAYS].apply(lambda x: len(split_days(x)))

    summary_texts = []

    def get_summary_str(count_target, label, is_show_school, is_show_count):
        df_target = df_active[df_active['days_count'] == count_target].sort_values(by=[COL_SCHOOL, COL_NAME])
        if df_target.empty: return ""

        groups = []
        if is_show_school or is_show_count:
            for school, school_group in df_target.groupby(COL_SCHOOL, sort=False):
                names_list = school_group[COL_NAME].tolist()
                names_str = " ".join(names_list)
                count = len(names_list)

                school_text = f"【{school}】" if is_show_school else ""
                count_text = f" {count}명" if (is_show_count and count >= 4) else ""

                if count == 1:
                    groups.append(f"{school_text}{names_str}{count_text}")
                else:
                    groups.append(f"{school_text}[{names_str}]{count_text}")
        else:
            for school, school_group in df_target.groupby(COL_SCHOOL, sort=False):
                groups.append(" ".join(school_group[COL_NAME].tolist()))

        return f"{label}: " + " ".join(groups)

    str_1day = get_summary_str(1, "주 1회", show_school, show_count)
    str_3day = get_summary_str(3, "주 3회", show_school, show_count)

    if str_1day: summary_texts.append(str_1day)
    if str_3day: summary_texts.append(str_3day)

    summary_final_str = "<br>".join(summary_texts)

    html += f"<tr><th>합계</th><td style='text-align:left !important; padding-left:10px !important;'>{summary_final_str}</td><td>{total}</td></tr></tbody></table>"

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
        html += f"<tr><td style='font-weight:bold; text-align:center;'>{p}교시</td>"

        for d in target_days:
            condition = df_active.apply(lambda row: match_attendance(row[COL_DAYS], row[COL_PERIOD], d, p), axis=1)
            students = df_active[condition].sort_values(COL_NAME)

            student_list = []
            for _, r in students.iterrows():
                s_str, g_str = str(r[COL_SCHOOL]).strip(), str(r[COL_GRADE]).strip()
                school_grade = s_str + (g_str[1:] if s_str and g_str and s_str[-1] == g_str[0] else g_str)
                student_list.append(f"<div class='weekly-name' style='text-align: left;'>{r[COL_NAME]} ({school_grade})</div>")

            if len(students) > 0:
                count_html = f"<div class='weekly-name' style='text-align: left; font-weight: normal; margin-top: 2px;'>{len(students)}명</div>"
            else:
                count_html = ""

            html += f"<td style='vertical-align:top !important; text-align:left !important; padding:5px 4px;'>{''.join(student_list)}{count_html}</td>"

        html += f"<td></td></tr></tbody></table><div class='date-footer'>{month_text}</div></div>"
    return html

def generate_table3(df, target_date, include_paused, assignment_map):
    weekday = WEEKDAY_ORDER[target_date.weekday()]
    day_mask = df[COL_DAYS].apply(lambda x: weekday in split_days(x))
    df_day = df[day_mask].copy()

    if not include_paused:
        df_day = df_day[df_day[COL_STATUS] == "재원"]

    grade_sort_map = {g: i for i, g in enumerate(GRADE_ORDER)}

    p_data = {1: [], 2: [], 3: []}
    p_assign = {1: [], 2: [], 3: []}
    p_counts = {1: 0, 2: 0, 3: 0}

    # 교시별 배정 알파벳 합계
    p_alpha_counts = {1: {}, 2: {}, 3: {}}

    for p in [1, 2, 3]:
        # ✅ apply(axis=1) 제거: 컬럼 기반 필터 사용
        df_p = filter_students_for_day_period(df_day, weekday, p)

        df_p["_grade_order"] = df_p[COL_GRADE].map(grade_sort_map).fillna(999)
        df_p = df_p.sort_values(["_grade_order", COL_SCHOOL, COL_NAME])

        last_level = None
        for _, row in df_p.iterrows():
            grade = str(row[COL_GRADE]).strip()

            if grade.startswith("초"):
                current_level = "초"
            elif grade.startswith("중"):
                current_level = "중"
            elif grade.startswith("고"):
                current_level = "고"
            else:
                current_level = "기타"

            if last_level is not None and current_level != last_level:
                p_data[p].append("")
                p_assign[p].append("")

            pause = " (휴)" if row[COL_STATUS] == "휴원" else ""
            s_str = str(row[COL_SCHOOL]).strip()
            school_grade = s_str + (grade[1:] if s_str and grade and s_str[-1] == grade[0] else grade)

            p_data[p].append(f"{row[COL_NAME]} ({school_grade}){pause}")
            p_counts[p] += 1

            skey = get_student_key(row)
            akey = (p, skey)
            letter = sanitize_letter(assignment_map.get(akey, ""))
            p_assign[p].append(letter)

            if letter:
                p_alpha_counts[p][letter] = p_alpha_counts[p].get(letter, 0) + 1

            last_level = current_level

    max_rows = max(len(p_data[1]), len(p_data[2]), len(p_data[3])) if not df_day.empty else 0

    html = f"<h2 style='text-align:left; border-bottom:2px solid black; padding-bottom:5px;'>{target_date.month}-{target_date.day} {weekday}</h2>"

    html += "<table class='table3-custom daily-table'><thead><tr>"
    for p in [1, 2, 3]:
        html += f"<th style='width:21%;'>{p}교시</th><th style='width:4%;'>출석</th><th style='width:4%;'>숙제</th><th style='width:4%;'>배정</th>"
    html += "</tr></thead><tbody>"

    no_h_border = "border-top: 0px !important; border-bottom: 0px !important; border-left: 1px solid #ccc; border-right: 1px solid #ccc;"
    bottom_border = "border-top: 0px !important; border-bottom: 2px solid black !important; border-left: 1px solid #ccc; border-right: 1px solid #ccc;"

    for i in range(max_rows):
        html += "<tr style='border-top: 0px !important; border-bottom: 0px !important;'>"
        for p in [1, 2, 3]:
            if i < len(p_data[p]):
                val = p_data[p][i]
                letter = p_assign[p][i] if i < len(p_assign[p]) else ""
                if val == "":
                    html += f"<td style='{no_h_border}'></td><td style='{no_h_border}'></td><td style='{no_h_border}'></td><td style='{no_h_border}'></td>"
                else:
                    html += (
                        f"<td class='name-cell' style='{no_h_border}'>{val}</td>"
                        f"<td style='{no_h_border}'><div class='check-box'></div></td>"
                        f"<td style='{no_h_border}'><div class='check-box'></div></td>"
                        f"<td class='assign-cell' style='{no_h_border}'>{letter}</td>"
                    )
            else:
                html += f"<td style='{no_h_border}'></td><td style='{no_h_border}'></td><td style='{no_h_border}'></td><td style='{no_h_border}'></td>"
        html += "</tr>"

    # 인원수 표기 행
    html += "<tr style='border-top: 0px !important; border-bottom: 2px solid black !important;'>"
    for p in [1, 2, 3]:
        count_text = f"{p_counts[p]}명" if p_counts[p] > 0 else ""
        html += f"<td class='name-cell' style='{bottom_border} font-weight: bold; text-align: right; padding-right: 10px; padding-top: 6px; padding-bottom: 6px;'>{count_text}</td><td style='{bottom_border}'></td><td style='{bottom_border}'></td><td style='{bottom_border}'></td>"
    html += "</tr>"

    # 배정 합계 영역: 12칸 구조 유지 + 위/아래 가로선
    all_letters = sorted(set(p_alpha_counts[1].keys()) | set(p_alpha_counts[2].keys()) | set(p_alpha_counts[3].keys()))

    if not all_letters:
        html += "<tr>"
        for _ in range(12):
            html += "<td style='border-top: 1px solid #ccc !important; border-bottom: 1px solid #ccc !important;'></td>"
        html += "</tr>"
    else:
        for idx, L in enumerate(all_letters):
            top_line = "border-top: 1px solid #ccc !important;" if idx == 0 else ""
            bottom_line = "border-bottom: 1px solid #ccc !important;" if idx == len(all_letters) - 1 else ""
            cell_style = f"{top_line}{bottom_line} border-left: 1px solid #ccc !important; border-right: 1px solid #ccc !important; text-align:left !important; padding:6px 6px; font-size:10pt;"

            html += "<tr>"

            cnt1 = p_alpha_counts[1].get(L, 0)
            txt1 = f"<b>{L}</b> : {cnt1}명" if cnt1 > 0 else ""
            html += f"<td style='{cell_style}'></td><td style='{cell_style}'></td><td style='{cell_style}'></td><td style='{cell_style}'>{txt1}</td>"

            cnt2 = p_alpha_counts[2].get(L, 0)
            txt2 = f"<b>{L}</b> : {cnt2}명" if cnt2 > 0 else ""
            html += f"<td style='{cell_style}'></td><td style='{cell_style}'></td><td style='{cell_style}'></td><td style='{cell_style}'>{txt2}</td>"

            cnt3 = p_alpha_counts[3].get(L, 0)
            txt3 = f"<b>{L}</b> : {cnt3}명" if cnt3 > 0 else ""
            html += f"<td style='{cell_style}'></td><td style='{cell_style}'></td><td style='{cell_style}'></td><td style='{cell_style}'>{txt3}</td>"

            html += "</tr>"

    # 가장 아래칸 밑줄(마감 가로선) 한 줄 추가
    html += "<tr><td colspan='12' style='border-top: 1px solid #ccc !important;'></td></tr>"

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

    

    # ✅ 배정 저장소(session_state)
    if "assignments" not in st.session_state:
        st.session_state["assignments"] = {}  # {date_iso: {(period, student_key): "A"}}

    with st.sidebar:
        print_orientation = st.radio("용지 방향", ["세로", "가로"])
        st.markdown(get_print_css_cached(print_orientation), unsafe_allow_html=True)
        if st.button("새로고침"):
            st.cache_data.clear()
            st.rerun()

    df = load_data()


    st.markdown('<div class="no-print" style="background-color:#f1f3f5;padding:15px;border-radius:8px;border-left:5px solid #868396;margin-bottom:20px;">🖨️ 인쇄: 우측 상단 ⋮ ➜ Print 선택</div>', unsafe_allow_html=True)

    tab_list = st.tabs(["전체 목록", "1. 학년별 명단", "2. 수업시간 명단", "3. 출석부", "4. 학교별 명단"])

    with tab_list[0]:
        st.markdown("<h2 style='font-size:16pt;'>등록 학생 목록</h2>", unsafe_allow_html=True)
        if not df.empty:
            st.dataframe(
                df[[COL_NAME, COL_SCHOOL, COL_GRADE, COL_DAYS, COL_PERIOD, COL_STATUS]],
                width="stretch",
                hide_index=True
            )
            total_list_html = generate_total_list_html(df)
            st.markdown(f"<div class='print-only'>{total_list_html}</div>", unsafe_allow_html=True)

    with tab_list[1]:
        if not df.empty:
            col1, col2 = st.columns([3, 1])
            with col1:
                m1 = st.text_input("제목(연/월)", value=datetime.now().strftime("%Y.%m"), key="m1")
            with col2:
                show_school_t1 = st.checkbox("학교명 표시", value=True, key="chk_school_m1")
                show_count_t1 = st.checkbox("학교별 인원수 표시", value=True, key="chk_count_m1")

            st.markdown(f"<div class='report-view'>{generate_table1(df, show_school_t1, show_count_t1, m1)}</div>", unsafe_allow_html=True)

    with tab_list[2]:
        if not df.empty:
            m2 = st.text_input("하단 표기", value=datetime.now().strftime("%Y-%m"), key="m2")
            st.markdown(f"<div class='report-view'>{generate_table2(df, m2)}</div>", unsafe_allow_html=True)

    with tab_list[3]:
        if not df.empty:
            d3 = st.date_input("날짜 선택", value=date.today())

            # (1) 배정 입력 UI: 출석부(3번 표) 전용
            weekday = WEEKDAY_ORDER[d3.weekday()]
            date_key = d3.isoformat()
            day_store = st.session_state["assignments"].setdefault(date_key, {})

            # 해당 요일 + 재원만
            day_mask = df[COL_DAYS].apply(lambda x: weekday in split_days(x))
            df_day = df[day_mask].copy()
            df_day = df_day[df_day[COL_STATUS] == "재원"]

            grade_sort_map = {g: i for i, g in enumerate(GRADE_ORDER)}

            # 교시별 학생 목록
            # 교시별 학생 목록 (✅ apply(axis=1) 제거: 더 안정적인 컬럼 기반 필터)
            per_period_students = {}
            grade_sort_map = {g: i for i, g in enumerate(GRADE_ORDER)}

            for p in [1, 2, 3]:
                df_p = filter_students_for_day_period(df_day, weekday, p)

                # 학년 정렬용 컬럼 추가
                df_p["_grade_order"] = df_p[COL_GRADE].map(grade_sort_map).fillna(999)
                df_p = df_p.sort_values(["_grade_order", COL_SCHOOL, COL_NAME])

                per_period_students[p] = df_p

            # ✅ 인쇄 시 생략
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
                                    key=f"assign_input_{date_key}_{p}_{skey}"
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
            st.markdown('</div>', unsafe_allow_html=True)

            # (2) 출석부(인쇄용) 표 생성
            st.markdown(f"<div class='report-view'>{generate_table3(df, d3, False, day_store)}</div>", unsafe_allow_html=True)

    with tab_list[4]:
        if not df.empty:
            m4 = st.text_input("제목(연/월)", value=datetime.now().strftime("%Y.%m"), key="m4")
            st.markdown(f"<div class='report-view'>{generate_table4(df, True, m4)}</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
