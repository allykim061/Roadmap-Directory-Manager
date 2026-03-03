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
    
    html += "<table class='table1-custom'><thead><tr><th>학년</th><th>학생 명단</th><th>인원수</th></tr></thead><tbody>"

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

                # ✅ <div>를 벗겨내고 원래대로 텍스트만 묶습니다.
                if count == 1:
                    formatted_groups.append(f"{school_text}{names_str}{count_text}")
                else:
                    formatted_groups.append(f"{school_text}[{names_str}]{count_text}")

            # ✅ 띄어쓰기(" ")를 기준으로 가로로 쭉 이어 붙입니다.
            names_final_str = " ".join(formatted_groups)
        else:
            names_final_str = " ".join(group_sorted[COL_NAME].tolist())

        html += f"<tr><th>{grade}</th><td class='t1-names'>{names_final_str}</td><td>{len(group)}</td></tr>"
        total += len(group)

    # --- 주 N회 합계 요약 부분 ---
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

        return f"<div style='margin-bottom:8px;'><strong>{label}:</strong> " + " ".join(groups) + "</div>"

    str_1day = get_summary_str(1, "주 1회", show_school, show_count)
    str_3day = get_summary_str(3, "주 3회", show_school, show_count)

    if str_1day: summary_texts.append(str_1day)
    if str_3day: summary_texts.append(str_3day)

    summary_final_str = "".join(summary_texts)
    
    html += f"<tr><th>합계</th><td class='t1-names'>{summary_final_str}</td><td>{total}</td></tr></tbody></table>"
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

    # ✅ 학년 정렬용 딕셔너리
    grade_sort_map = {g: i for i, g in enumerate(GRADE_ORDER)}

    for p in periods:
        html += "<div class='a4-print-box'><table class='weekly-table'><thead><tr>"
        html += "<th style='width:10%;'>수업시간</th>"
        for d in target_days:
            html += f"<th style='width:20%;'>{d}</th>"
        html += "<th style='width:10%;'>비고</th></tr></thead><tbody>"
        
        # ✅ 수정 1: 인라인 스타일을 지우고 'period-cell' 클래스만 부여 (CSS가 중앙 정렬 담당)
        html += f"<tr><td class='period-cell'>{p}교시</td>"

        for d in target_days:
            condition = df_active.apply(
                lambda row: match_attendance(row[COL_DAYS], row[COL_PERIOD], d, p), 
                axis=1
            )
            students = df_active[condition].copy()

            student_list = []
            last_grade = None

            if not students.empty:
                # 학년(GRADE_ORDER) -> 학교 -> 이름 정렬
                students["_grade_order"] = students[COL_GRADE].map(grade_sort_map).fillna(999)
                students = students.sort_values(["_grade_order", COL_SCHOOL, COL_NAME])

                for _, r in students.iterrows():
                    grade = str(r[COL_GRADE]).strip()

                    # 학년 바뀌면 띄우기
                    if last_grade is not None and grade != last_grade:
                        student_list.append("<div class='weekly-name'>&nbsp;</div>")

                    s_str, g_str = str(r[COL_SCHOOL]).strip(), grade
                    school_grade = s_str + (g_str[1:] if s_str and g_str and s_str[-1] == g_str[0] else g_str)

                    student_list.append(
                        f"<div class='weekly-name' style='text-align:left;'>{r[COL_NAME]} ({school_grade})</div>"
                    )
                    last_grade = grade

            # 총 인원수
            count_html = (
                f"<div class='weekly-name' style='text-align:left; font-weight:bold; margin-top:4px;'>{len(students)}명</div>"
                if len(students) > 0 else ""
            )

            # ✅ 수정 2: 스타일 코드를 최소화 (vertical-align 등은 CSS에서 처리)
            html += (
                f"<td style='text-align:left !important;'>"
                f"{''.join(student_list)}{count_html}</td>"
            )

        html += f"<td></td></tr></tbody></table><div class='date-footer'>{month_text}</div></div>"
        
    return html


def generate_table3(df: pd.DataFrame, target_date, include_paused: bool, assignment_map: dict) -> str:
    weekday = WEEKDAY_ORDER[target_date.weekday()]
    day_mask = df[COL_DAYS].astype(str).apply(lambda x: weekday in split_days(x))
    df_day = df[day_mask].copy()

    if not include_paused:
        df_day = df_day[df_day[COL_STATUS] == "재원"]

    grade_sort_map = {g: i for i, g in enumerate(GRADE_ORDER)}

    rows = {1: [], 2: [], 3: []}

    p_alpha_counts = {1: {}, 2: {}, 3: {}}
    p_counts = {1: 0, 2: 0, 3: 0}
    p_absent_counts = {1: 0, 2: 0, 3: 0}

    for p in [1, 2, 3]:
        df_p = filter_students_for_day_period(df_day, weekday, p)
        df_p["_grade_order"] = df_p[COL_GRADE].map(grade_sort_map).fillna(999)
        df_p = df_p.sort_values(["_grade_order", COL_SCHOOL, COL_NAME])

        last_grade = None  # ✅ 학년 기준 추적 (초5 -> 초6 등)

        for _, row in df_p.iterrows():
            grade = str(row[COL_GRADE]).strip()

            # ✅ 학년이 바뀌는 '첫 학생 줄'에만 플래그를 세움 (gap row를 추가하지 않음)
            is_new_grade = (last_grade is not None and grade != last_grade)

            pause = " (휴)" if row[COL_STATUS] == "휴원" else ""
            s_str = str(row[COL_SCHOOL]).strip()
            school_grade = s_str + (grade[1:] if s_str and grade and s_str[-1] == grade[0] else grade)
            name_text = f"{row[COL_NAME]} ({school_grade}){pause}"

            skey = get_student_key(row)
            akey = (p, skey)

            data = assignment_map.get(akey, {"letter": "", "absent": False})
            if not isinstance(data, dict):
                data = {"letter": sanitize_letter(str(data)), "absent": False}

            letter = sanitize_letter(data.get("letter", ""))
            is_abs = bool(data.get("absent", False))

            # 집계: 결석은 제외
            if is_abs:
                p_absent_counts[p] += 1
            else:
                p_counts[p] += 1
                if letter:
                    p_alpha_counts[p][letter] = p_alpha_counts[p].get(letter, 0) + 1

            rows[p].append({
                "type": "student",
                "text": name_text,
                "letter": letter,
                "is_abs": is_abs,
                "is_new_grade": is_new_grade,  # ✅ 추가
            })

            last_grade = grade  # ✅ 업데이트

        total_in_period = p_counts[p] + p_absent_counts[p]
        if total_in_period > 0:
            # 명단과 합계 사이 빈 줄(기존 유지)
            rows[p].append({"type": "blank"})

            summary_lines = []
            if p_counts[p] > 0:
                summary_lines.append(f"{p_counts[p]}명")

            letters = sorted(p_alpha_counts[p].keys())
            for L in letters:
                summary_lines.append(f"{L} : {p_alpha_counts[p][L]}명")

            if p_absent_counts[p] > 0:
                summary_lines.append(
                    f"<span style='color:#d9534f; font-weight:600;'>결석 : {p_absent_counts[p]}명</span>"
                )

            if summary_lines:
                combined_summary = "<br>".join(summary_lines)
                rows[p].append({"type": "summary", "text": combined_summary})

    # 가장 긴 교시 길이에 맞춰 행 수 통일
    max_rows = max(len(rows[1]), len(rows[2]), len(rows[3])) if not df_day.empty else 0
    for p in [1, 2, 3]:
        while len(rows[p]) < max_rows:
            rows[p].append({"type": "blank"})

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

    cell_base = (
        "border-top:0px !important; border-bottom:0px !important;"
        "border-left:1px solid #ccc !important; border-right:1px solid #ccc !important;"
    )

    for i in range(max_rows):
        html += "<tr style='border-top:0px !important; border-bottom:0px !important;'>"

        for p in [1, 2, 3]:
            row_data = rows[p][i]
            rtype = row_data.get("type")

            if rtype == "blank":
                html += f"<td style='{cell_base}'></td>" * 4

            elif rtype == "student":
                name_text = row_data.get("text", "")
                letter = row_data.get("letter", "")
                is_abs = bool(row_data.get("is_abs", False))
                is_new_grade = bool(row_data.get("is_new_grade", False))

                abs_class = " absent" if is_abs else ""
                gap_class = " new-grade-gap" if is_new_grade else ""

                # ✅ 4칸 모두 같은 wrapper로 감싸서 "줄 전체"가 함께 내려가게 처리
                html += (
                    f"<td class='name-cell{abs_class}' style='{cell_base}'>"
                    f"<div class='student-inner{gap_class}'>{name_text}</div></td>"

                    f"<td style='{cell_base}'>"
                    f"<div class='student-inner{gap_class}'><div class='check-box'></div></div></td>"

                    f"<td style='{cell_base}'>"
                    f"<div class='student-inner{gap_class}'><div class='check-box'></div></div></td>"

                    f"<td class='assign-cell' style='{cell_base}'>"
                    f"<div class='student-inner{gap_class}'>{letter}</div></td>"
                )

            else:  # summary
                text = row_data.get("text", "")
                html += (
                    f"<td class='name-cell' style='{cell_base} text-align:left !important; padding-left:4px !important;"
                    f" padding-top:4px !important; padding-bottom:4px !important; line-height:1.2 !important;'>"
                    f"{text}</td>"
                    f"<td style='{cell_base}'></td>"
                    f"<td style='{cell_base}'></td>"
                    f"<td style='{cell_base}'></td>"
                )

        html += "</tr>"

    html += "<tr><td colspan='12' style='border-top:2px solid black !important;'></td></tr>"
    return html + "</tbody></table>"


def generate_table4(df: pd.DataFrame, show_grade: bool, month_text: str) -> str:
    df_active = df[df[COL_STATUS] == "재원"].copy()
    
    # ✅ 1) 학교급 정렬용 보조 함수: 초(1) -> 중(2) -> 고(3) -> 기타(4)
    def get_school_rank(school_name):
        name = str(school_name).strip()
        if not name: return 99
        if name.endswith("초"): return 1
        elif name.endswith("중"): return 2
        elif name.endswith("고"): return 3
        else: return 4

    # ✅ 2) 학교 이름 추출 후 [1순위: 학교급(초/중/고), 2순위: 가나다순] 정렬
    unique_schools = df_active[COL_SCHOOL].dropna().unique().tolist()
    unique_schools.sort(key=lambda x: (get_school_rank(x), str(x)))

    # 학년 정렬 기준표 (GRADE_ORDER: 초1 -> 초2 -> ... 고3)
    grade_sort_map = {str(g).strip(): i for i, g in enumerate(GRADE_ORDER)}

    html = f"<h2 style='text-align:center; font-size:16pt;'>학교별 명단 ({month_text})</h2>"
    
    # 1번 표의 비율(8%, 84%, 8%)과 큼직한 글자 스타일(table1-custom)유지, 첫번째 비율은 변경
    html += "<table class='table1-custom table4-custom'><thead><tr><th>학교</th><th>학생 명단</th><th>인원수</th></tr></thead><tbody>"
    
    total = 0
    for school in unique_schools:
        group = df_active[df_active[COL_SCHOOL] == school].copy()
        if group.empty:
            continue

        # 데이터에 묻어있는 공백 찌꺼기 청소
        group["_grade_clean"] = group[COL_GRADE].astype(str).str.strip()

        # [같은 학교 내 정렬] 1순위: 학년 순서, 2순위: 이름 가나다순
        group["_grade_order"] = group["_grade_clean"].map(grade_sort_map).fillna(999)
        group_sorted = group.sort_values(by=["_grade_order", COL_NAME])

        formatted_groups = []
        
        if show_grade:
            # 정렬된 순서를 그대로 유지하면서(sort=False) 학년별로 묶어줍니다.
            for grade, grade_group in group_sorted.groupby("_grade_clean", sort=False):
                names_list = grade_group[COL_NAME].tolist()
                names_str = " ".join(names_list)
                count = len(names_list)
                
                # 【학년】 뒤에 한 칸 띄우기 적용!
                grade_text = f"【{grade}】 "
                count_text = f" {count}명" if count >= 4 else ""
                
                if count == 1:
                    formatted_groups.append(f"{grade_text}{names_str}{count_text}")
                else:
                    formatted_groups.append(f"{grade_text}[{names_str}]{count_text}")
            
            names_final_str = " ".join(formatted_groups)
        else:
            names_final_str = " ".join(group_sorted[COL_NAME].tolist())

        # t1-names 클래스를 적용해 좌상단 정렬과 행간 띄우기 적용
        html += f"<tr><th>{school}</th><td class='t1-names'>{names_final_str}</td><td>{len(group)}</td></tr>"
        total += len(group)

    # 합계 칸
    html += f"<tr><th>합계</th><td class='t1-names'></td><td>{total}</td></tr></tbody></table>"
    
    return html