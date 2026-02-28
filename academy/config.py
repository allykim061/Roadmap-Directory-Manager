# academy/config.py

PAGE_TITLE = "학생 인원관리 시스템"

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

WORKSHEET_STUDENTS = "students"  # 시트 탭 이름(너 구글시트에서 쓰는 이름)

COL_ID = "학생ID"
COL_NAME = "이름"
COL_SCHOOL = "학교"
COL_GRADE = "학년"
COL_DAYS = "등원요일"
COL_PERIOD = "수업교시"
COL_STATUS = "상태"

REQUIRED_COLUMNS = {
    COL_ID, COL_NAME, COL_SCHOOL, COL_GRADE, COL_DAYS, COL_PERIOD, COL_STATUS
}

GRADE_ORDER = ["초1", "초2", "초3", "초4", "초5", "초6", "중1", "중2", "중3", "고1", "고2", "고3"]
WEEKDAY_ORDER = ["월", "화", "수", "목", "금", "토", "일"]