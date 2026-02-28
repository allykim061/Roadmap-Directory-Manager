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

    p_data = {1: [], 2: [], 3: []}
    p_assign = {1: [], 2: [], 3: []}
    p_counts = {1: 0, 2: 0, 3: 0}
    p_alpha_counts = {1: {}, 2: {}, 3: {}}

    for p in [1, 2, 3]:
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

    html += "<tr style='border-top: 0px !important; border-bottom: 2px solid black !important;'>"
    for p in [1, 2, 3]:
        count_text = f"{p_counts[p]}명" if p_counts[p] > 0 else ""
        html += f"<td class='name-cell' style='{bottom_border} font-weight: bold; text-align: right; padding-right: 10px; padding-top: 6px; padding-bottom: 6px;'>{count_text}</td><td style='{bottom_border}'></td><td style='{bottom_border}'></td><td style='{bottom_border}'></td>"
    html += "</tr>"

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

    html += "<tr><td colspan='12' style='border-top: 1px solid #ccc !important;'></td></tr>"
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