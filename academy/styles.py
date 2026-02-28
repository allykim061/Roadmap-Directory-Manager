# academy/styles.py
import streamlit as st

def get_print_css(orientation: str = "세로") -> str:
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

        /* ===== 3번 표(table3) 전용 ===== */
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

        @media screen {{
            .print-only {{ display: none !important; }}
        }}

        @media print {{
            *, *::before, *::after {{ box-sizing: border-box !important; }}

            .weekly-table th,
            .weekly-table td {{
                overflow: hidden !important;
            }}

            div[role="tablist"], header, footer, [data-testid="stSidebar"], [data-testid="stHeader"],
            .stButton, .stDateInput, .stTextInput, .stCheckbox {{ display: none !important; }}
            .no-print {{ display: none !important; }}
            .block-container {{ padding: 0 !important; max-width: 100% !important; }}
            .report-view {{ border: none !important; padding: 0 !important; margin: 0 !important; }}

            [data-testid="stDataFrame"] {{ display: none !important; }}
            .print-only {{ display: block !important; }}

            @page {{ size: {page_size}; margin: 8mm 5mm; }}

            h2 {{ font-size: 12pt !important; margin-bottom: 5px !important; padding-bottom: 2px !important; }}

            table {{ font-size: 7.5pt !important; color: black; border: 1px solid black !important; margin-bottom: 5px !important; page-break-inside: auto; }}
            tr {{ page-break-inside: avoid; page-break-after: auto; }}
            th, td {{ border: 1px solid black !important; color: black !important; }}

            th {{ background-color: #f0f0f0 !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; font-size: 8pt !important; padding: 4px 2px !important; }}
            .no-bg-th {{ background-color: white !important; }}

            td {{ padding: 2px 1px !important; line-height: 1.0 !important; }}

            .daily-table td.name-cell {{ font-size: 7.5pt !important; letter-spacing: -0.5px !important; }}
            .weekly-name {{ font-size: 7pt !important; margin-bottom: 1px !important; letter-spacing: -0.5px !important; }}

            .check-box {{ width: 10px !important; height: 10px !important; }}

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