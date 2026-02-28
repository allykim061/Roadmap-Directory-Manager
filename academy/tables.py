# academy/tables.py
import pandas as pd

from .config import (
    COL_NAME, COL_SCHOOL, COL_GRADE, COL_DAYS, COL_PERIOD, COL_STATUS,
    GRADE_ORDER, WEEKDAY_ORDER
)
from .utils import split_days, extract_period_numbers, match_attendance, get_student_key, sanitize_letter
from .filters import filter_students_for_day_period


def generate_total_list_html(df: pd.DataFrame) -> str:
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


def generate_table1(df: pd.DataFrame, show_school: bool, show_count: bool, month_text: str) -> str:
    df_active = df[df[COL_STATUS] == "재원"].copy()
    html = f"<h2 style='text-align:center; font-size:16pt;'>학년별 명단 ({month_text})</h2>"
    html += "<table style='font-size: 4pt;'><thead><tr><th style='width:15%'>학년</th><th>학생 명단</th><th style='width:15%'>인원수</th></tr></thead><tbody>"

    total = 0
    for grade in GRADE_ORDER:
        group = df_active[df_active[COL_GRADE] == grade]
        if group.empty:
            continue

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

    df_active["days_count"] = df_active[COL_DAYS].apply(lambda x: len(split_days(x)))
    summary_texts = []

    def get_summary_str(count_target, label, is_show_school, is_show_count):
        df_target = df_active[df_active["days_count"] == count_target].sort_values(by=[COL_SCHOOL, COL_NAME])
        if df_target.empty:
            return ""

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
            for _, school_group in df_target.groupby(COL_SCHOOL, sort=False):
                groups.append(" ".join(school_group[COL_NAME].tolist()))

        return f"{label}: " + " ".join(groups)

    str_1day = get_summary_str(1, "주 1회", show_school, show_count)
    str_3day = get_summary_str(3, "주 3회", show_school, show_count)

    if str_1day:
        summary_texts.append(str_1day)
    if str_3day:
        summary_texts.append(str_3day)

    summary_final_str = "<br>".join(summary_texts)
    html += f"<tr><th>합계</th><td style='text-align:left !important; padding-left:10px !important;'>{summary_final_str}</td><td>{total}</td></tr></tbody></table>"
    return html


def generate_table2(df: pd.DataFrame, month_text: str) -> str:
    df_active = df[df[COL_STATUS] == "재원"].copy()
    html = f"<h2 class='no-print' style='text-align:center; font-size:16pt;'>{month_text} 반편성 내역</h2>"
    target_days = ["월", "화", "수", "목"]

    periods_set = set()
    for p_str in df_active[COL_PERIOD]:
        for n in extract_period_numbers(p_str):
            if n > 0:
                periods_set.add(n)
    periods = sorted(periods_set) if periods_set else [1, 2, 3]

    for p in periods:
        html += "<div class='a4-print-box'><table class='weekly-table'><thead><tr>"
        html += "<th style='width:10%;'>수업시간</th>"
        for d in target_days:
            html += f"<th style='width:20%;'>{d}</th>"
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

            count_html = f"<div class='weekly-name' style='text-align: left; font-weight: normal; margin-top: 2px;'>{len(students)}명</div>" if len(students) > 0 else ""
            html += f"<td style='vertical-align:top !important; text-align:left !important; padding:5px 4px;'>{''.join(student_list)}{count_html}</td>"

        html += f"<td></td></tr></tbody></table><div class='date-footer'>{month_text}</div></div>"
    return html


def generate_table3(df: pd.DataFrame, target_date, include_paused: bool, assignment_map: dict) -> str:
    weekday = WEEKDAY_ORDER[target_date.weekday()]
    day_mask = df[COL_DAYS].astype(str).apply(lambda x: weekday in split_days(x))
    df_day = df[day_mask].copy()

    if not include_paused:
        df_day = df_day[df_day[COL_STATUS] == "재원"]

    grade_sort_map = {g: i for i, g in enumerate(GRADE_ORDER)}

    # 각 교시별로 "행 모델"을 만든다: ("student"/"blank"/"summary", name_text, assign_letter)
    rows = {1: [], 2: [], 3: []}

    # 교시별 배정 알파벳 합계
    p_alpha_counts = {1: {}, 2: {}, 3: {}}
    p_counts = {1: 0, 2: 0, 3: 0}

    for p in [1, 2, 3]:
        df_p = filter_students_for_day_period(df_day, weekday, p)
        df_p["_grade_order"] = df_p[COL_GRADE].map(grade_sort_map).fillna(999)
        df_p = df_p.sort_values(["_grade_order", COL_SCHOOL, COL_NAME])

        last_level = None

        # 1) 학생 행
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

            # 학교급 바뀌면 빈 줄(간격)
            if last_level is not None and current_level != last_level:
                rows[p].append(("blank", "", ""))

            pause = " (휴)" if row[COL_STATUS] == "휴원" else ""
            s_str = str(row[COL_SCHOOL]).strip()
            school_grade = s_str + (grade[1:] if s_str and grade and s_str[-1] == grade[0] else grade)

            name_text = f"{row[COL_NAME]} ({school_grade}){pause}"

            skey = get_student_key(row)
            akey = (p, skey)
            letter = sanitize_letter(assignment_map.get(akey, ""))

            rows[p].append(("student", name_text, letter))
            p_counts[p] += 1

            if letter:
                p_alpha_counts[p][letter] = p_alpha_counts[p].get(letter, 0) + 1

            last_level = current_level

        # 2) 인원수 + 알파벳 합계를 "이름 칸"으로 내려붙이기
        # 2) 인원수 + 알파벳 합계를 "이름 칸"으로 내려붙이기
        if p_counts[p] > 0:
            # 인원수와 알파벳 합계를 하나의 리스트에 차곡차곡 모읍니다.
            summary_lines = [f"{p_counts[p]}명"]
            
            letters = sorted(p_alpha_counts[p].keys())
            for L in letters:
                summary_lines.append(f"{L} : {p_alpha_counts[p][L]}명")
                
            # 모은 글자들을 <br>(엔터)로 연결해서 하나의 덩어리로 만듭니다.
            combined_summary = "<br>".join(summary_lines)
            
            # 표에는 합쳐진 덩어리를 딱 "한 줄(한 칸)"로만 추가합니다.
            rows[p].append(("summary", combined_summary, ""))

    # 3교시 중 가장 긴 길이에 맞춰 행 수 통일
    max_rows = max(len(rows[1]), len(rows[2]), len(rows[3])) if not df_day.empty else 0
    for p in [1, 2, 3]:
        while len(rows[p]) < max_rows:
            rows[p].append(("blank", "", ""))

    html = (
        f"<h2 style='text-align:left; border-bottom:2px solid black; padding-bottom:5px;'>"
        f"{target_date.month}-{target_date.day} {weekday}</h2>"
    )

    html += "<table class='table3-custom daily-table'><thead><tr>"
    for p in [1, 2, 3]:
        html += (
            f"<th style='width:21%;'>{p}교시</th>"
            f"<th style='width:4%;'>출석</th>"
            f"<th style='width:4%;'>숙제</th>"
            f"<th style='width:4%;'>배정</th>"
        )
    html += "</tr></thead><tbody>"

    # 기본 테두리(가로선 제거 + 세로선만 유지)
    cell_base = (
        "border-top:0px !important; border-bottom:0px !important;"
        "border-left:1px solid #ccc !important; border-right:1px solid #ccc !important;"
    )

    for i in range(max_rows):
        html += "<tr style='border-top:0px !important; border-bottom:0px !important;'>"

        for p in [1, 2, 3]:
            rtype, name_text, letter = rows[p][i]

            if rtype == "blank":
                html += (
                    f"<td style='{cell_base}'></td>"
                    f"<td style='{cell_base}'></td>"
                    f"<td style='{cell_base}'></td>"
                    f"<td style='{cell_base}'></td>"
                )

            elif rtype == "student":
                html += (
                    f"<td class='name-cell' style='{cell_base}'>{name_text}</td>"
                    f"<td style='{cell_base}'><div class='check-box'></div></td>"
                    f"<td style='{cell_base}'><div class='check-box'></div></td>"
                    f"<td class='assign-cell' style='{cell_base}'>{letter}</td>"
                )

            else:  # "summary" -> 합쳐진 텍스트를 출력
                html += (
                    # ✅ 수정: line-height(줄간격)를 1.2로 설정, 글자 간격 줄이기
                    # 여러 줄이 들어가므로 vertical-align:top을 줘서 위로 딱 붙게 만듭니다.
                    f"<td class='name-cell' style='{cell_base} text-align:left !important; padding-left:4px !important; padding-top:4px !important; padding-bottom:4px !important; vertical-align:top !important; line-height:0.6 !important;'>"
                    f"{name_text}</td>"
                    f"<td style='{cell_base}'></td>"
                    f"<td style='{cell_base}'></td>"
                    f"<td style='{cell_base}'></td>"
                )

        html += "</tr>"

    # 표 맨 아래 굵은 마감선(원하면 유지)
    html += "<tr><td colspan='12' style='border-top:2px solid black !important;'></td></tr>"

    return html + "</tbody></table>"


def generate_table4(df: pd.DataFrame, show_grade: bool, month_text: str) -> str:
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