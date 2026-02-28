# academy/filters.py
import re
import pandas as pd

from .config import COL_DAYS, COL_PERIOD, WEEKDAY_ORDER


def norm_series(sr: pd.Series) -> pd.Series:
    """Series 전용 정규화: NaN -> '', NBSP/전각공백/모든 공백 제거"""
    return (
        sr.fillna("")
          .astype(str)
          .str.replace("\u00A0", "", regex=False)  # NBSP
          .str.replace("\u3000", "", regex=False)  # 전각공백
          .str.replace(r"\s+", "", regex=True)     # 모든 공백류
    )


def filter_students_for_day_period(df: pd.DataFrame, weekday: str, period: int) -> pd.DataFrame:
    """
    df에서 weekday에 등원하고, period에 해당하는 학생만 필터링해 반환.
    - COL_DAYS: "월,수" 형태
    - COL_PERIOD:
        * 요일마커 있음: "월1,수2" → 해당 weekday+period 토큰 포함
        * 숫자만 있음: "1,2,3" / "1 2 3" / "1/2/3" 등 → period 숫자 포함
    """
    if df is None or df.empty:
        return df.copy() if df is not None else pd.DataFrame()

    days = norm_series(df[COL_DAYS])
    pstr = norm_series(df[COL_PERIOD])

    # 요일 포함 여부: (^|,)월(,|$)
    day_pat = rf"(^|,){re.escape(weekday)}(,|$)"
    mask_day = days.str.contains(day_pat, regex=True, na=False)

    # 요일 마커 포함 여부
    marker_pat = "(" + "|".join(map(re.escape, WEEKDAY_ORDER)) + ")"
    has_marker = pstr.str.contains(marker_pat, regex=True, na=False)

    # 마커가 있는 경우: (^|,)월1(,|$)
    token_pat = rf"(^|,){re.escape(weekday)}{int(period)}(,|$)"
    mask_marker = pstr.str.contains(token_pat, regex=True, na=False)

    # 숫자만 있는 경우: 1이 10/11에 매칭되면 안 됨
    num_pat = rf"(?<!\d){int(period)}(?!\d)"
    mask_numeric = pstr.str.contains(num_pat, regex=True, na=False)

    mask = mask_day & ((has_marker & mask_marker) | ((~has_marker) & mask_numeric))
    return df.loc[mask].copy()