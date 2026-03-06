# academy/styles.py
import streamlit as st

def get_print_css(orientation: str = "세로") -> str:
    page_size = "A4 portrait" if orientation == "세로" else "A4 landscape"

    # ✅ 안정형: @page는 @media print 밖에서 선언
    page_margin_top = "3mm"
    page_margin_lr  = "5mm"

    return f"""
    <style>
        /* =========================================================
           ✅ @page 안정형 선언 (최상단)
           ========================================================= */
        @page {{
            size: {page_size};
            margin: {page_margin_top} {page_margin_lr};
        }}

        /* =========================================================
           공통(화면/인쇄)
           ========================================================= */
        html, body, .stApp {{
            font-family:
              "Malgun Gothic",
              "맑은 고딕",
              "Apple SD Gothic Neo",
              "Noto Sans KR",
              sans-serif !important;
        }}

        .report-view {{
            border: 1px solid #ccc;
            padding: 20px;
            background: white;
            margin-top: 20px;
            color: black;
        }}

        .a4-print-box {{
            margin-bottom: 15px;
            page-break-after: always;
            break-after: page;
        }}
        .a4-print-box:last-child {{
            page-break-after: auto;
            break-after: auto;
        }}

        .date-footer {{ margin-top: 5px; text-align: right; font-size: 11pt; color: #666; }}

        /* 화면용 빈 네모 (결석/숙제 수기 체크용) */
        .check-box {{
            display: inline-block;
            width: 14px;
            height: 14px;
            border: 1px solid #000;
            vertical-align: middle;
        }}

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
            background-color: #F1F5F9 !important;
            color: black !important;
            font-weight: 600; /* 유지 */
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
            font-size: 8pt;          /* 2번표 글자크기 조정 유지 */
            letter-spacing: -0.6px;
            margin-bottom: 5px;      /* 2번표 줄 사이 간격 조정 유지 */
        }}

        /* =========================================================
           1번표(table1) / 4번표(table4)
           ========================================================= */
        .table1-custom {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
        .table1-custom th:first-child, .table1-custom td:first-child {{ width: 8% !important; }}
        .table1-custom th:last-child, .table1-custom td:last-child {{ width: 8% !important; }}
        .table1-custom th, .table1-custom td {{ font-size: 11pt !important; }}
        .table1-custom .t1-names {{
            text-align: left !important;
            vertical-align: top !important;
            padding: 8px 6px !important;
            font-size: 10.5pt !important;
            line-height: 1.8 !important;
            word-break: keep-all !important;
        }}

        /* ✅ (정리) t1-summary 블록은 제거: 현재 generate_table1 구조상 적용되지 않고,
              주1회/주3회 간격은 HTML inline style로 이미 “만족하는 상태”로 유지됨 */

        .table4-custom th:first-child, .table4-custom td:first-child {{ width: 14% !important; }}

        /* =========================================================
           2번표(주간)
           ========================================================= */
        .weekly-table td {{ vertical-align: top !important; padding-top: 2px !important; }}
        .weekly-table td.period-cell {{ vertical-align: middle !important; text-align: center !important; font-weight: bold !important; }}

        /* =========================================================
           3번표(일일 출석부)
           ========================================================= */
        .daily-grid-container {{ display: flex; width: 100%; gap: 6px; align-items: flex-start; }}
        .period-column {{ flex: 1 1 0; min-width: 0; }}
        .period-column table {{ width: 100%; }}
        .table3-custom {{ border-collapse: collapse !important; width: 100%; }}

        .table3-custom, .table3-custom thead, .table3-custom tbody, .table3-custom tr {{
            border-top: 0 !important;
            border-bottom: 0 !important;
        }}

        .table3-custom th, .table3-custom td {{
            border: none !important;
            border-top: 0 !important;
            border-bottom: 0 !important;
            border-left: 1px solid #999 !important;
            border-right: 1px solid #999 !important;
        }}

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

        .table3-custom th:first-child, .table3-custom td:first-child {{ border-left: 1px solid #000 !important; }}
        .table3-custom th:last-child, .table3-custom td:last-child {{ border-right: 1px solid #000 !important; }}
        .table3-custom .name-cell.absent {{ text-decoration: line-through !important; }}
        .table3-custom .student-inner {{ font-size: 10pt !important; line-height: 1.5; }}
        .table3-custom .student-inner.new-grade-gap {{ padding-top: 7px !important; }}
        .table3-custom .summary-cell {{ text-align: left !important; padding: 2px 4px !important; font-size: 10.5pt !important; line-height: 1.2 !important; }}
        .table3-custom td.t3-gap {{ padding: 0 !important; height: 3px !important; line-height: 0 !important; font-size: 0 !important; }}

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

        .assign-cell {{ font-weight: normal; }}

        /* =========================================================
           화면 전용
           ========================================================= */
        @media screen {{
            .print-only {{ display: none !important; }}
            .tab0-print-root {{ display: none !important; }}
        }}

        /* =========================================================
           인쇄 전용
           ========================================================= */
        @media print {{
            .tab0-print-root {{ display: block !important; }}
           /* 1) Streamlit UI 및 유령 공간(밀림 현상) 완벽 제거 */
            div[role="tablist"], header, footer,
            [data-testid="stSidebar"], [data-testid="stHeader"],
            .stButton, .stDateInput, .stTextInput, .stCheckbox, [data-testid="stExpander"],
            .no-print, [data-testid="stDataFrame"] {{
                display: none !important;
            }}

            /* ✅ 아래 2개 패치는 "0번표 인쇄"에서만 작동하게 스코프 */
            body:has(.tab0-print-root) .element-container:has([data-testid="stDataFrame"]) {{
                display: none !important;
                height: 0 !important;
                margin: 0 !important;
                padding: 0 !important;
            }}

            /* Streamlit 내부 레이아웃 gap 제거도 0번표 인쇄에서만 */
            body:has(.tab0-print-root) [data-testid="stVerticalBlock"],
            body:has(.tab0-print-root) [data-testid="stHorizontalBlock"],
            body:has(.tab0-print-root) [data-testid="column"] {{
                gap: 0 !important;
                padding: 0 !important;
                margin: 0 !important;
            }}

            /* 2) 페이지 여백 초기화 */
            html, body, .stApp, .stAppViewContainer,
            section.main, .main, .block-container {{
                margin: 0 !important;
                padding: 0 !important;
            }}

            /* 2) 페이지 여백 초기화 */
            html, body, .stApp, .stAppViewContainer,
            section.main, .main, .block-container {{
                margin: 0 !important;
                padding: 0 !important;
            }}

            .report-view {{
                margin: 0 !important;
                padding: 0 !important;
                border: none !important;
                background: #fff !important;
            }}

            h2, h2.t3-title {{
                margin: 0 0 6px 0 !important;
                padding: 0 !important;
            }}

            /* 3) 기본 테이블 인쇄 스타일 */
            table {{
                font-size: 7.5pt !important;
                border: 1px solid #000 !important;
                margin-bottom: 5px !important;
                page-break-inside: auto;
            }}

            tr {{
                page-break-inside: avoid;
                page-break-after: auto;
            }}

            /* ✅ 0번표(전체목록) 전용: 테두리 연한 회색으로 변경 (우선순위 강화) */
            .tab0-print-root table.total-list-table,
            .tab0-print-root table.total-list-table th,
            .tab0-print-root table.total-list-table td {{
                border: 1px solid #A2A2A2 !important; /* 💡 무조건 회색으로 덮어쓰기! */
            }}

            /* ✅ 0번표(전체목록)에서는 tr 쪼개기 제한을 풀어준다 (전역 tr avoid 무효화) */
            table.total-list-table tr {{
            page-break-inside: auto !important;
            break-inside: auto !important;
            }}

            table.total-list-table tbody {{
            break-inside: auto !important;
            }}

            table.total-list-table thead {{
            display: table-header-group !important;
            }}

            table:not(.table3-custom) th,
            table:not(.table3-custom) td {{
                border: 1px solid #000 !important;
                color: #000 !important;
            }}

            /* 0번표 헤더 반복 */
            table.total-list-table thead {{
                display: table-header-group !important;
            }}

            table.total-list-table tr {{
                break-inside: auto !important;
                page-break-inside: auto !important;
            }}

            table.total-list-table tbody {{
                break-inside: auto !important;
            }}

            /* 4) 3번표 스타일 */
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
                letter-spacing: -0.5px !important;
            }}

            .table3-custom th:first-child,
            .table3-custom td:first-child {{
                border-left: 2px solid #000 !important;
            }}

            .table3-custom th:last-child,
            .table3-custom td:last-child {{
                border-right: 2px solid #000 !important;
            }}

            .table3-custom tbody tr.t3-bottom td {{
                padding: 0 !important;
                height: 0 !important;
                line-height: 0 !important;
                font-size: 0 !important;
                border-top: 2px solid #000 !important;
                border-bottom: none !important;
                border-left: none !important;
                border-right: none !important;
                background: transparent !important;
            }}

            /* 인쇄 가독성 */
            th {{
                background-color: #F1F5F9 !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
                font-size: 8pt !important;
                padding: 4px 2px !important;
                letter-spacing: -0.5px !important;
            }}

            td {{
                padding: 2px 1px !important;
                line-height: 1.0 !important;
            }}

            .daily-grid-container {{
                gap: 4px !important;
            }}

            .check-box {{
                width: 14px !important;
                height: 14px !important;
                border: 2px solid black !important;
            }}

            /* 3번표 미세조정 */
            .table3-custom .student-inner {{
                font-size: 9.5pt !important;
            }}

            .table3-custom .summary-cell {{
                font-size: 8.5pt !important;
                line-height: 0.8 !important;
                padding: 2px 4px !important;
                vertical-align: top !important;
            }}

            .table3-custom td.t3-gap {{
                height: 3px !important;
                padding: 0 !important;
                line-height: 0 !important;
                font-size: 0 !important;
            }}

            /* 1번표 */
            .table1-custom th,
            .table1-custom td:not(.t1-names) {{
                font-size: 10pt !important;
            }}

            .table1-custom .t1-names {{
                font-size: 10.5pt !important;
                padding: 8px 6px !important;
                line-height: 1.65 !important;
            }}

            /* 2번표(주간표) 왼쪽 잘림 완벽 방어 */
            .weekly-table {{
                width: 100% !important;
                max-width: 100% !important;
                margin-left: 0 !important;
                box-sizing: border-box !important;
                table-layout: fixed !important;
            }}

            /* 0번표 제목 및 검색어 헤더 영역 (양쪽 끝 정렬) */
            .tab0-print-header {{
                display: flex !important;
                justify-content: space-between !important; /* 양쪽 끝으로 밀어내기 */
                align-items: flex-end !important; /* 바닥선 맞추기 */
                margin: 0 0 10px 0 !important;
                padding-top: 2mm !important; /* 잘림 방지 에어백 */
            }}

            .tab0-print-title {{
                text-align: left !important;
                font-size: 16pt !important;
                margin: 0 !important;
                padding: 0 !important;
            }}

            .tab0-print-count {{
                font-size: 11pt !important;
                color: #000 !important; /* 💡 회색(#666)에서 검정색(#000)으로 변경! */
                font-weight: 700 !important; /* 💡 진하게(bold) 추가! */
                margin-left: 6px !important;
            }}

            /* 💡 검색 결과 메시지 (오른쪽 위, 검정색 강제) */
            .tab0-print-search-msg {{
                font-size: 11pt !important;
                color: #000 !important; /* 인쇄 시 선명한 검정색! */
                font-weight: 500 !important;
                margin-bottom: 2px !important; /* 큰 제목과 줄맞춤용 미세 조정 */
            }}

            /* 페이지 에어백 */
            .a4-print-box {{
                padding-top: 2mm !important;
            }}

            .a4-print-box + .a4-print-box {{
                padding-top: 6mm !important;
            }}

            /* 위치 안정화 */
            body:has(.tab0-print-root) .tab0-print-root {{
                position: static !important;
                left: auto !important;
                top: auto !important;
                width: 100% !important;
            }}

        }}
    </style>
    """

@st.cache_data
def get_print_css_cached(orientation: str) -> str:
    return get_print_css(orientation)