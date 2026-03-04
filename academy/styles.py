# academy/styles.py
import streamlit as st

def get_print_css(orientation: str = "세로") -> str:
    page_size = "A4 portrait" if orientation == "세로" else "A4 landscape"

    return f"""
    <style>
        @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css");

        /* =========================
           공통(화면/인쇄)
           ========================= */
        html, body {{
            font-family: 'Pretendard', sans-serif !important;
        }}
        body, .stApp {{ font-family: 'Pretendard', sans-serif !important; }}

        .report-view {{
            border: 1px solid #ccc;
            padding: 20px;
            background: white;
            margin-top: 20px;
            color: black;
        }}

        .a4-print-box {{ margin-bottom: 15px; page-break-after: always; }}
        .a4-print-box:last-child {{ page-break-after: auto; }}

        .date-footer {{ margin-top: 5px; text-align: right; font-size: 11pt; color: #666; }}
        .check-box {{ display: inline-block; width: 14px; height: 14px; border: 1px solid #000; vertical-align: middle; }}

        table {{
            width: 100%;
            border-collapse: collapse;
            table-layout: fixed;
            margin-bottom: 10px;
        }}

        th {{
            border: 1px solid #ccc !important;
            padding: 8px 4px !important;
            text-align: center !important;
            vertical-align: middle !important;
            white-space: nowrap !important;
            word-break: keep-all !important;
            font-size: 10pt !important;
            background-color: #f0f0f0 !important;
            color: black !important;
        }}

        td {{
            border: 1px solid #ccc;
            padding: 6px 4px;
            text-align: center;
            vertical-align: middle !important;
            word-wrap: break-word;
            font-size: 10pt;
            color: black;
        }}

        .daily-table td.name-cell {{
            text-align: left;
            padding-left: 4px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            font-size: 10pt;
            letter-spacing: -0.2px;
        }}

        .weekly-name {{
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            font-size: 9pt;
            letter-spacing: -0.6px;
            margin-bottom: 3px;
        }}

        /* =========================
           1번표(table1)
           ========================= */
        .table1-custom {{
            width: 100%;
            border-collapse: collapse;
            table-layout: fixed;
        }}
        .table1-custom th:first-child, .table1-custom td:first-child {{ width: 8% !important; }}
        .table1-custom th:last-child, .table1-custom td:last-child {{ width: 8% !important; }}
        .table1-custom th, .table1-custom td {{ font-size: 11pt !important; }}

        .table1-custom .t1-names {{
            text-align: left !important;
            vertical-align: top !important;
            padding: 8px 6px !important;
            font-size: 11.5pt !important;
            line-height: 1.8 !important;
            word-break: keep-all !important;
        }}

        /* =========================
           2번표(주간)
           ========================= */
        .weekly-table td {{
            vertical-align: top !important;
            padding-top: 2px !important;
        }}
        .weekly-table td.period-cell {{
            vertical-align: middle !important;
            text-align: center !important;
            font-weight: bold !important;
        }}

        /* =========================
           3번표(일일 출석부) - 화면에서도 가로선 제거 + 세로선만
           ========================= */
        .daily-grid-container {{
            display: flex;
            width: 100%;
            gap: 6px;                 /* 화면/인쇄 균형 */
            align-items: flex-start;
        }}

        .period-column {{
            flex: 1 1 0;
            min-width: 0;
        }}

        .period-column table {{
            width: 100%;
        }}

        .table3-custom {{
            border-collapse: collapse !important;
            width: 100%;
        }}

        /* (A) 테이블/행 단위 가로 border 제거 */
        .table3-custom,
        .table3-custom thead,
        .table3-custom tbody,
        .table3-custom tr {{
            border-top: 0 !important;
            border-bottom: 0 !important;
        }}

        /* (B) 셀: 가로선 완전 제거 + 세로선만 켜기(화면에선 회색) */
        .table3-custom th,
        .table3-custom td {{
            border: none !important;
            border-top: 0 !important;
            border-bottom: 0 !important;
            border-left: 1px solid #999 !important;
            border-right: 1px solid #999 !important;
        }}

        /* (C) 헤더: 위/아래 선 유지 + 헤더 글자 수평 강제 */
        .table3-custom thead th {{
            border-top: 1px solid #000 !important;
            border-bottom: 2px solid #000 !important;

            writing-mode: horizontal-tb !important;
            transform: none !important;
            white-space: nowrap !important;
            word-break: keep-all !important;

            padding: 4px 2px !important;
            overflow: hidden !important;
            text-overflow: clip !important;
        }}

        /* (D) 외곽(좌/우) */
        .table3-custom th:first-child,
        .table3-custom td:first-child {{
            border-left: 1px solid #000 !important;
        }}

        .table3-custom th:last-child,
        .table3-custom td:last-child {{
            border-right: 1px solid #000 !important;
        }}

        /* (E) 결석 표시 */
        .table3-custom .name-cell.absent {{
            text-decoration: line-through !important;
        }}

        /* (F) 학생 텍스트 */
        .table3-custom .student-inner {{
            font-size: 11pt !important;
            line-height: 1.2;
        }}

        .table3-custom .student-inner.new-grade-gap {{
            padding-top: 7px !important;
        }}

        /* (G) 요약/간격 */
        .table3-custom .summary-cell {{
            text-align: left !important;
            padding: 2px 4px !important;
            font-size: 10.5pt !important;
            line-height: 1.2 !important;
        }}

        .table3-custom td.t3-gap {{
            padding: 0 !important;
            height: 3px !important;
            line-height: 0 !important;
            font-size: 0 !important;
        }}

        /* (H) 하단 마감선: tables.py에서 <tr class='t3-bottom'> 쓰는 버전 기준 */
        .table3-custom tbody tr.t3-bottom td {{
            padding: 0 !important;
            height: 0 !important;
            line-height: 0 !important;
            font-size: 0 !important;

            border-top: 1.5px solid #000 !important;
            border-bottom: none !important;
            border-left: none !important;
            border-right: none !important;
        }}

        .assign-cell {{
            font-weight: normal;
        }}

        /* =========================
           4번표(table4)
           ========================= */
        .table4-custom th:first-child, .table4-custom td:first-child {{
            width: 14% !important;
        }}

        /* =========================
           화면 전용
           ========================= */
        @media screen {{
            .print-only {{ display: none !important; }}
        }}

        /* =========================
           인쇄 전용 (옵션1: report-view만 인쇄)
           ========================= */
        @media print {{
            /* 1) Streamlit UI/조작 요소 숨김 */
            div[role="tablist"], header, footer,
            [data-testid="stSidebar"], [data-testid="stHeader"],
            .stButton, .stDateInput, .stTextInput, .stCheckbox, [data-testid="stExpander"],
            .no-print, [data-testid="stDataFrame"] {{
                display: none !important;
            }}

            /* 2) 상단 여백(공백) 핵심 제거 */
            html, body, .stApp, .stAppViewContainer, section.main, .main, .block-container {{
                margin: 0 !important;
                padding: 0 !important;
            }}

            /* report-view 자체가 갖고 있던 화면용 여백 제거 (네 코드에 margin-top:20px, padding:20px 있음) */
            .report-view {{
                margin: 0 !important;
                padding: 0 !important;
                border: none !important;
                background: #fff !important;
            }}

            /* 3) 페이지 여백 (더 올리고 싶으면 top을 4mm까지도 가능) */
            @page {{ size: A4 portrait; margin: 6mm 5mm; }}

            /* 4) 제목 위쪽 공백 제거 */
            h2, h2.t3-title {{
                margin: 0 0 6px 0 !important;
                padding: 0 !important;
            }}

            /* 전역 인쇄 테이블(3번표 제외) */
            table {{
                font-size: 7.5pt !important;
                border: 1px solid #000 !important;
                margin-bottom: 5px !important;
                page-break-inside: auto;
            }}
            tr {{ page-break-inside: avoid; page-break-after: auto; }}

            table:not(.table3-custom) th,
            table:not(.table3-custom) td {{
                border: 1px solid #000 !important;
                color: #000 !important;
            }}

            /* ✅ 3번표 인쇄: 세로선을 검정으로 + 외곽 살짝 강조 */
            .table3-custom th,
            .table3-custom td {{
                border-left: 1px solid #000 !important;
                border-right: 1px solid #000 !important;
            }}

            .table3-custom thead th {{
                border-top: 1px solid #000 !important;
                border-bottom: 2px solid #000 !important;
                writing-mode: horizontal-tb !important;
                transform: none !important;
                white-space: nowrap !important;
            }}

            .table3-custom th:first-child,
            .table3-custom td:first-child {{
                border-left: 2px solid #000 !important;
            }}
            .table3-custom th:last-child,
            .table3-custom td:last-child {{
                border-right: 2px solid #000 !important;
            }}

            /* 하단 마감선(인쇄에서는 조금 더 또렷하게) */
            .table3-custom tbody tr.t3-bottom td {{
                border-top: 2px solid #000 !important;
            }}

            /* 인쇄 가독성 */
            th {{
                background-color: #f0f0f0 !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
                font-size: 8pt !important;
                padding: 4px 2px !important;
            }}
            td {{
                padding: 2px 1px !important;
                line-height: 1.0 !important;
            }}

            .daily-grid-container {{ gap: 4px !important; }}
            .check-box {{ width: 10px !important; height: 10px !important; }}

            .table3-custom .student-inner {{ font-size: 9.5pt !important; }}
            .table3-custom .summary-cell {{
                font-size: 8.5pt !important;
                line-height: 0.8 !important;
            }}

            /* 1번표 인쇄 고정 */
            .table1-custom th, .table1-custom td:not(.t1-names) {{ font-size: 11pt !important; }}
            .table1-custom .t1-names {{
                font-size: 11.5pt !important;
                padding: 8px 6px !important;
                line-height: 1.8 !important;
            }}

            /* 요약/간격/blank는 전역 td 규칙보다 우선하게 고정 */
            .table3-custom td.summary-cell{{
                padding: 2px 4px !important;
                line-height: 1.2 !important;
                vertical-align: top !important;
            }}
            .table3-custom td.t3-gap{{
                height: 3px !important;
                padding: 0 !important;
                line-height: 0 !important;
                font-size: 0 !important;
            }}

        }}
    </style>
    """

@st.cache_data
def get_print_css_cached(orientation: str) -> str:
    return get_print_css(orientation)