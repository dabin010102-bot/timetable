from __future__ import annotations

from datetime import datetime, timedelta
import html
import json
import re
import io
from pathlib import Path

import pandas as pd
import streamlit as st

# -------------------------------------------------
# 기본 설정
# -------------------------------------------------
st.set_page_config(page_title="INUTimetable", layout="wide")

st.markdown(
    """
    <style>
    :root {
      --text-main: #0b1220;
      --text-sub: #1f2937;
      --card-bg: #ffffff;
      --card-border: #cbd5e1;
      --accent-bg: #dbeafe;
      --accent-text: #0b1220;
    }
    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
      color: var(--text-main) !important;
      font-family: "Segoe UI", "Malgun Gothic", "Noto Sans KR", sans-serif !important;
      font-size: 16px !important;
      background: #ffffff !important;
    }
    [data-testid="stHeader"], [data-testid="stToolbar"] {
      background: transparent !important;
    }
    .stMarkdown, .stCaption, .stText, .stMetricLabel, .stMetricValue, .st-emotion-cache-10trblm {
      color: var(--text-main) !important;
    }
    h1, h2, h3, h4, h5, h6, p, span, label, small, div {
      color: var(--text-main) !important;
    }
    [data-testid="stSidebar"] * {
      color: var(--text-main) !important;
    }
    [data-testid="stSidebar"] {
      background: #f8fbff !important;
      border-right: 1px solid #d6e0ea !important;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label {
      background: #ffffff !important;
      border: 1px solid #cbd5e1 !important;
      border-radius: 10px !important;
      padding: 8px 10px !important;
      margin-bottom: 8px !important;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label:hover {
      background: #eaf2ff !important;
      border-color: #7c9ed6 !important;
    }
    [data-testid="stSidebar"] [role="radiogroup"] p,
    [data-testid="stSidebar"] label p,
    [data-testid="stSidebar"] .stRadio label span {
      color: #08111f !important;
      font-weight: 700 !important;
      opacity: 1 !important;
    }
    [data-testid="stSidebar"] .stCaption {
      color: #334155 !important;
    }
    [data-baseweb="input"] input,
    [data-baseweb="input"] textarea,
    .stTextInput input,
    .stTextArea textarea,
    .stSelectbox div,
    .stMultiSelect div,
    .stNumberInput input {
      color: #0b1220 !important;
      background: #ffffff !important;
      font-size: 15px !important;
    }
    div[data-baseweb="select"] * {
      color: #08111f !important;
      font-weight: 700 !important;
    }
    div[data-baseweb="popover"] * {
      color: #08111f !important;
      background: #ffffff !important;
    }
    div[role="listbox"] * {
      color: #08111f !important;
      font-weight: 700 !important;
    }
    .stButton button, .stDownloadButton button, .stFormSubmitButton button {
      color: #0b1220 !important;
      background: #e2ecff !important;
      border: 1px solid #94a3b8 !important;
      font-weight: 700 !important;
      font-size: 15px !important;
    }
    .stButton button:hover, .stDownloadButton button:hover, .stFormSubmitButton button:hover {
      background: #cfe0ff !important;
      border-color: #64748b !important;
    }
    [data-testid="stDataFrame"] * {
      color: #0b1220 !important;
      font-size: 14px !important;
    }
    .stInfo, .stSuccess, .stWarning, .stError {
      color: #0b1220 !important;
    }
    div[data-testid="stMetric"] {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 10px 12px;
    }
    .big-summary-row {
      display:grid;
      grid-template-columns: repeat(5, minmax(120px, 1fr));
      gap:10px;
      margin: 6px 0 12px 0;
    }
    .big-summary-card {
      border:1px solid #cbd5e1;
      border-radius:12px;
      background:#ffffff;
      padding:10px 12px;
      min-height:84px;
    }
    .big-summary-title {
      font-size:13px;
      font-weight:700;
      color:#334155 !important;
    }
    .big-summary-value {
      margin-top:6px;
      font-size:22px;
      font-weight:800;
      color:#0b1220 !important;
      line-height:1.2;
      word-break:keep-all;
    }
    .calendar-wrap table {width:100%; border-collapse:collapse; table-layout:fixed; font-size:13px;}
    .calendar-wrap th, .calendar-wrap td {border:1px solid #cfd8e3; padding:5px; vertical-align:top; height:58px;}
    .calendar-wrap th {background:#dbe7f9; text-align:center; font-size:14px; color:var(--text-main);}
    .calendar-wrap .time-col {background:#f3f7fc; width:90px; text-align:center; font-weight:700; color:var(--text-main);}
    .calendar-wrap .exam {background:#dbeafe !important; color:#0b1220 !important; border:2px solid #7aa7df !important;}
    .calendar-wrap .course {font-weight:900; margin-bottom:3px; font-size:13px; color:#0b1220 !important;}
    .calendar-wrap .empty {background:#ffffff;}
    .calendar-wrap .exam-block {
      display:block;
      min-height:46px;
      background:#bfdbfe;
      border:1px solid #60a5fa;
      border-radius:7px;
      padding:5px 6px;
      line-height:1.22;
      box-shadow: inset 0 0 0 1px rgba(255,255,255,.45);
    }
    .calendar-wrap .exam-link {
      text-decoration:none !important;
      color:#0b1220 !important;
      display:block;
    }
    .calendar-wrap .grade-pill {
      display:inline-block;
      margin-left:4px;
      padding:1px 5px;
      border-radius:999px;
      background:#1d4ed8;
      color:#ffffff !important;
      font-size:11px;
      font-weight:900;
    }
    .calendar-wrap .room-line {
      color:#1e3a8a !important;
      font-weight:800;
      font-size:12px;
    }
    .calendar-wrap .cont {
      min-height:46px;
      background:#bfdbfe;
      border-left:1px solid #60a5fa;
      border-right:1px solid #60a5fa;
      border-radius:5px;
    }
    .click-grid-head {
      display:grid;
      grid-template-columns: 84px repeat(5, minmax(110px, 1fr));
      border-top:1px solid #cfd8e3;
      border-left:1px solid #cfd8e3;
      background:#dbe7f9;
      font-weight:800;
      text-align:center;
    }
    .click-grid-row {
      display:grid;
      grid-template-columns: 84px repeat(5, minmax(110px, 1fr));
      border-left:1px solid #cfd8e3;
    }
    .click-grid-cell, .click-grid-time {
      min-height:62px;
      border-right:1px solid #cfd8e3;
      border-bottom:1px solid #cfd8e3;
      padding:4px;
      background:#ffffff;
      font-size:12px;
    }
    .click-grid-time {
      background:#f3f7fc;
      text-align:center;
      font-weight:800;
      padding-top:14px;
    }
    .click-grid-exam {
      background:#dbeafe;
      border:1px solid #bfdbfe;
      border-radius:6px;
      padding:5px;
      line-height:1.25;
      font-weight:700;
      color:#0b1220 !important;
      min-height:42px;
    }
    .click-grid-possible {
      background:#dcfce7;
      border:1px solid #86efac;
      border-radius:6px;
      padding:5px;
      line-height:1.25;
      font-weight:800;
      color:#14532d !important;
      text-align:center;
      min-height:42px;
    }
    .click-grid-selected-move {
      background:#dbeafe;
      border:2px solid #2563eb;
      border-radius:6px;
      padding:5px;
      line-height:1.25;
      font-weight:900;
      color:#1e3a8a !important;
      text-align:center;
      min-height:42px;
    }
    .click-grid-cont {
      background:#eff6ff;
      border-radius:4px;
      min-height:42px;
    }
    div[data-testid="stButton"] button[kind="secondary"] {
      white-space: pre-line !important;
      min-height:56px !important;
      width:100% !important;
      line-height:1.2 !important;
      padding:6px 6px !important;
      font-size:12px !important;
      background:#dbeafe !important;
      border:1px solid #60a5fa !important;
      color:#0b1220 !important;
      font-weight:800 !important;
      border-radius:8px !important;
    }
    div[data-testid="stButton"] button[kind="secondary"]:hover {
      background:#bfdbfe !important;
      border-color:#2563eb !important;
      color:#0b1220 !important;
    }
    .result-table-wrap {overflow-x:auto; margin-top:10px;}
    .result-table {width:100%; border-collapse:collapse; font-size:14px; background:#ffffff;}
    .result-table th, .result-table td {border:1px solid #d8e0ea; padding:8px 10px; text-align:left; color:#0b1220 !important;}
    .result-table th {background:#eaf2ff; font-weight:800;}
    .result-table td.change {background:#ffe3e3; color:#7f1d1d !important; font-weight:800;}
    </style>
    """,
    unsafe_allow_html=True,
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR_CANDIDATES = [
    BASE_DIR,
    BASE_DIR / "결과",
    Path(r"C:\xpressmp\결과"),
    Path(r"C:\xpressmp"),
]

RESULT_JSON_CANDIDATES = ["result_service_data.json", "결과_서비스데이터.json"]
IS_CANDIDATES = ["IS.xlsx", str(Path(r"C:\xpressmp\IS.xlsx"))]
OT_CANDIDATES = ["OT_all_sessions.xlsx", "OT_all_sessions (1).xlsx", str(Path(r"C:\xpressmp\OT_all_sessions.xlsx"))]
COURSEEN_CANDIDATES = [
    "coursetable_en.csv",
    "coursetable_en.xlsx.csv",
    "coursetable.csv",
    str(Path(r"C:\xpressmp\coursetable_en.csv")),
    str(Path(r"C:\xpressmp\coursetable_en.xlsx.csv")),
    str(Path(r"C:\xpressmp\coursetable.csv")),
]
ROOM_ORDER = [402, 479, 482, 483, 502, 583]
WEIGHT_ROOM_MOVE = 0.1048
WEIGHT_TIME_MOVE = 0.4331
WEIGHT_DAILY = 0.4620
D_MAX = 0
T_MAX = 4
REPORT_DIR_CANDIDATES = [
    BASE_DIR / "결과_리포트",
    BASE_DIR / "결과" / "결과_리포트",
    Path(r"C:\xpressmp\결과\결과_리포트"),
]

DAY_LABELS = {1: "월", 2: "화", 3: "수", 4: "목", 5: "금", 6: "토", 7: "일"}
DAY_ORDER = ["월", "화", "수", "목", "금"]
DAY_KO_TO_NUM = {v: k for k, v in DAY_LABELS.items()}
WEEK_START_DATE = {
    7: datetime(2026, 4, 13).date(),
    8: datetime(2026, 4, 20).date(),
    9: datetime(2026, 4, 27).date(),
}

# 화면 표시용 과목명 매핑(영문 -> 한글)
COURSE_NAME_KO = {
    "Calculus(1)": "대학수학(1)",
    "IntroIE&M": "산업경영공학개론",
    "GenAIApps": "생성형AI응용",
    "Database": "데이터베이스",
    "Det.ManageSci": "확정적 경영과학",
    "Ergonomics": "인간공학",
    "Prob&Stats(1)": "확률및통계(1)",
    "ProdDevProcess": "제품개발프로세스",
    "QualityEng": "품질공학",
    "ReinforcLearn": "강화학습",
    "SmartLogistics": "스마트물류",
    "DataMining": "데이터마이닝",
    "ErgoExpEval": "인간공학적실험평가론",
    "IntroFinEng": "금융공학개론",
    "Optim&Apps": "최적화모델링응용",
    "ProdControl": "생산통제",
    "Corp&Safety": "기업과안전",
    "SmartMfg&Auto": "스마트제조자동화",
}

# 학년 파일이 없거나 매칭이 실패해도 화면에서 학년이 비지 않도록 하는 기본값
COURSE_GRADE_FALLBACK = {
    "Calculus(1)": "1",
    "IntroIE&M": "1",
    "GenAIApps": "3",
    "Database": "3",
    "Det.ManageSci": "3",
    "Ergonomics": "3",
    "Prob&Stats(1)": "3",
    "ProdDevProcess": "3",
    "QualityEng": "4",
    "ReinforcLearn": "3",
    "SmartLogistics": "3",
    "DataMining": "3",
    "ErgoExpEval": "3",
    "IntroFinEng": "3",
    "Optim&Apps": "3",
    "ProdControl": "3",
    "Corp&Safety": "3",
    "SmartMfg&Auto": "3",
}


# -------------------------------------------------
# 유틸
# -------------------------------------------------
def normalize_name(text: str) -> str:
    x = str(text or "").strip().replace(" ", "")
    x = x.replace("IntrolE&M", "IntroIE&M").replace("IntroIEandM", "IntroIE&M")
    x = re.sub(r"[-_]\d+$", "", x)
    return x.lower()


def normalize_exact(text: str) -> str:
    x = str(text or "").strip().replace(" ", "")
    x = x.replace("IntrolE&M", "IntroIE&M").replace("IntroIEandM", "IntroIE&M")
    return x.lower()


def slot_to_time(slot: int) -> str:
    mins = 9 * 60 + slot * 30
    return f"{mins // 60:02d}:{mins % 60:02d}"


def minute_to_time(minute: int) -> str:
    return f"{minute // 60:02d}:{minute % 60:02d}"


def to_korean_course_name(course: str) -> str:
    raw = str(course)
    section = ""
    m = re.search(r"([-_]\d+)$", raw.strip())
    if m:
        section = m.group(1)
    base_key = re.sub(r"[-_]\d+$", "", raw.strip())
    for eng, kor in COURSE_NAME_KO.items():
        if normalize_name(eng) == normalize_name(base_key):
            return f"{kor}{section}"
    return raw


def fallback_grade_for_course(course: str) -> str:
    base_key = re.sub(r"[-_]\d+$", "", str(course or "").strip())
    for key, grade in COURSE_GRADE_FALLBACK.items():
        if normalize_name(key) == normalize_name(base_key):
            return str(grade)
    return "-"


def format_grade_label(value) -> str:
    text = str(value or "").strip()
    if not text or text == "-" or text.lower() == "nan":
        return "-"
    return text if "학년" in text else f"{text}학년"


def find_existing_path(candidates: list[str], prefer_latest: bool = False) -> Path | None:
    expanded: list[Path] = []
    for c in candidates:
        p = Path(c)
        if p.is_absolute():
            expanded.append(p)
        else:
            for d in DATA_DIR_CANDIDATES:
                expanded.append(d / c)

    existing = [p for p in expanded if p.exists()]
    if not existing:
        return None
    if prefer_latest:
        return max(existing, key=lambda p: p.stat().st_mtime)
    for p in existing:
        return p
    return None


def find_existing_dir(candidates: list[Path]) -> Path | None:
    for p in candidates:
        if p.exists() and p.is_dir():
            return p
    return None


@st.cache_data(show_spinner=False)
def load_result_payload() -> tuple[dict, Path]:
    p = find_existing_path(RESULT_JSON_CANDIDATES, prefer_latest=True)
    if p is None:
        raise FileNotFoundError("결과 JSON 파일을 찾지 못했습니다. 먼저 gurobl.py를 실행하세요.")
    return json.loads(p.read_text(encoding="utf-8")), p


@st.cache_data(show_spinner=False)
def load_is_df() -> tuple[pd.DataFrame, Path]:
    p = find_existing_path(IS_CANDIDATES)
    if p is None:
        raise FileNotFoundError("IS.xlsx를 찾지 못했습니다.")
    return pd.read_excel(p), p


@st.cache_data(show_spinner=False)
def load_ot_df() -> tuple[pd.DataFrame, Path | None]:
    p = find_existing_path(OT_CANDIDATES)
    if p is None:
        return pd.DataFrame(), None
    return pd.read_excel(p), p


@st.cache_data(show_spinner=False)
def load_courseen_df() -> tuple[pd.DataFrame, Path | None]:
    p = find_existing_path(COURSEEN_CANDIDATES)
    if p is None:
        return pd.DataFrame(), None
    if p.suffix.lower() in [".xlsx", ".xls"]:
        return pd.read_excel(p), p
    return pd.read_csv(p), p


def build_exam_df(payload: dict) -> pd.DataFrame:
    exams = payload["exams"]
    assignment = payload["assignment"]
    tmove = payload.get("time_move_map", {})
    rmove = payload.get("room_change_map", {})

    rows = []
    for i, ex in enumerate(exams):
        info = assignment[str(i)]
        week = int(info["week"])
        dow = int(info["dow"])
        start_slot = int(info["slot_val"])
        dur = int(ex["dur_slots"])
        dur_minutes = int(ex.get("dur_minutes", dur * 30))
        rooms = [int(r) for r in info["rooms"]]

        date0 = WEEK_START_DATE[week] + timedelta(days=dow - 1)
        start_dt = datetime(date0.year, date0.month, date0.day, 9, 0) + timedelta(minutes=30 * start_slot)
        end_dt = start_dt + timedelta(minutes=dur_minutes)

        rows.append(
            {
                "시험인덱스": i,
                "과목": ex["name"],
                "기준과목": ex.get("base_key", normalize_name(ex["name"])),
                "과목명": to_korean_course_name(ex["name"]),
                "정규과목": normalize_name(ex["name"]),
                "주차": week,
                "요일번호": dow,
                "요일": DAY_LABELS.get(dow, str(dow)),
                "날짜": f"{date0.month}/{date0.day}",
                "시작슬롯": start_slot,
                "종료슬롯": start_slot + dur,
                "표시종료슬롯": start_slot + (dur_minutes / 30.0),
                "시험시간(분)": dur_minutes,
                "시작": slot_to_time(start_slot),
                "종료": minute_to_time(9 * 60 + start_slot * 30 + dur_minutes),
                "강의실": " ".join(str(r) for r in rooms),
                "강의실목록": rooms,
                "x_iwdt": 1,
                "TimeMove_i": int(tmove.get(str(i), 0)),
                "RoomChange_i": int(rmove.get(str(i), 0)),
                "start_dt": start_dt,
                "end_dt": end_dt,
            }
        )

    return pd.DataFrame(rows).sort_values(["주차", "start_dt", "과목"]).reset_index(drop=True)


def detect_id_col(df_is: pd.DataFrame) -> str:
    for c in df_is.columns:
        name = str(c).lower()
        if "학번" in name or "student" in name or name in {"id", "sid"}:
            return c
    return df_is.columns[0]


def resolve_is_columns_for_course(is_cols: list[str], course_name: str) -> list[str]:
    nc = normalize_name(course_name)
    matched = []
    for c in is_cols:
        ncol = normalize_name(c)
        if ncol == nc or ncol.startswith(nc) or nc.startswith(ncol):
            matched.append(c)
    return matched


def find_student_row(df_is: pd.DataFrame, sid: str) -> int | None:
    id_col = detect_id_col(df_is)
    s = df_is[id_col].astype(str).str.strip()
    hit = s[s == sid]
    if len(hit) == 0:
        return None
    return int(hit.index[0])


def student_exam_df(exam_df: pd.DataFrame, df_is: pd.DataFrame, row_idx: int) -> pd.DataFrame:
    is_cols = [str(c) for c in df_is.columns]
    taken_idxs = []

    unique_courses = exam_df[["시험인덱스", "과목"]].drop_duplicates()
    for _, r in unique_courses.iterrows():
        idx = int(r["시험인덱스"])
        course = str(r["과목"])
        cols = resolve_is_columns_for_course(is_cols, course)
        taken = False
        for c in cols:
            try:
                v = float(df_is.at[row_idx, c])
                if v > 0:
                    taken = True
                    break
            except Exception:
                continue
        if taken:
            taken_idxs.append(idx)

    return exam_df[exam_df["시험인덱스"].isin(taken_idxs)].copy().sort_values(["주차", "start_dt", "과목"]).reset_index(drop=True)


def intervals_overlap(start_a: float, end_a: float, start_b: float, end_b: float) -> bool:
    return (start_a < end_b) and (start_b < end_a)


@st.cache_data(show_spinner=False)
def build_exam_student_sets(exam_df: pd.DataFrame, df_is: pd.DataFrame) -> dict[int, set[int]]:
    is_cols = [str(c) for c in df_is.columns]
    student_sets: dict[int, set[int]] = {}
    for _, row in exam_df[["시험인덱스", "과목"]].drop_duplicates().iterrows():
        idx = int(row["시험인덱스"])
        course = str(row["과목"])
        cols = resolve_is_columns_for_course(is_cols, course)
        st_set: set[int] = set()
        if cols:
            for s_idx in df_is.index:
                for c in cols:
                    try:
                        v = float(df_is.at[s_idx, c])
                        if v > 0:
                            st_set.add(int(s_idx))
                            break
                    except Exception:
                        continue
        student_sets[idx] = st_set
    return student_sets


def daily_penalty_from_count(n: int) -> int:
    if n <= 0:
        return 0
    return (n - 1) * (n - 1)


def score_move_impact(
    exam_df: pd.DataFrame,
    target_idx: int,
    new_week: int,
    new_day: int,
    new_start: int,
    new_room: int,
    student_sets: dict[int, set[int]],
    summary: dict,
) -> dict:
    base = exam_df.copy()
    trow = base[base["시험인덱스"] == target_idx]
    if trow.empty:
        return {"feasible": False, "reason": "대상 과목을 찾지 못했습니다."}
    trow = trow.iloc[0]

    dur_slots = float(trow["표시종료슬롯"]) - float(trow["시작슬롯"])
    new_end = float(new_start) + dur_slots

    # 1) 강의실 중복 체크
    room_conflicts = []
    others = base[base["시험인덱스"] != target_idx]
    for _, r in others.iterrows():
        if int(r["주차"]) != int(new_week) or int(r["요일번호"]) != int(new_day):
            continue
        rooms = set(int(x) for x in r["강의실목록"])
        if int(new_room) not in rooms:
            continue
        if intervals_overlap(float(new_start), float(new_end), float(r["시작슬롯"]), float(r["표시종료슬롯"])):
            room_conflicts.append(str(r["과목명"]))

    # 2) 학생 동시시험 체크
    target_students = student_sets.get(int(target_idx), set())
    student_conflict_count = 0
    for s_idx in target_students:
        has_overlap = False
        for _, r in others.iterrows():
            eidx = int(r["시험인덱스"])
            if s_idx not in student_sets.get(eidx, set()):
                continue
            if int(r["주차"]) != int(new_week) or int(r["요일번호"]) != int(new_day):
                continue
            if intervals_overlap(float(new_start), float(new_end), float(r["시작슬롯"]), float(r["표시종료슬롯"])):
                has_overlap = True
                break
        if has_overlap:
            student_conflict_count += 1

    feasible = (len(room_conflicts) == 0) and (student_conflict_count == 0)
    if not feasible:
        reason_parts = []
        if room_conflicts:
            reason_parts.append(f"강의실 중복: {len(room_conflicts)}건")
        if student_conflict_count > 0:
            reason_parts.append(f"학생 동시시험: {student_conflict_count}명")
        return {
            "feasible": False,
            "reason": " / ".join(reason_parts),
            "room_conflicts": room_conflicts[:10],
            "student_conflict_count": student_conflict_count,
        }

    # 시뮬레이션 반영
    sim = base.copy()
    mask = sim["시험인덱스"] == target_idx
    sim.loc[mask, "주차"] = int(new_week)
    sim.loc[mask, "요일번호"] = int(new_day)
    sim.loc[mask, "요일"] = DAY_LABELS.get(int(new_day), str(new_day))
    date0 = WEEK_START_DATE[int(new_week)] + timedelta(days=int(new_day) - 1)
    sim.loc[mask, "날짜"] = f"{date0.month}/{date0.day}"
    sim.loc[mask, "시작슬롯"] = int(new_start)
    # 표시종료슬롯은 75분 같은 시험시간 때문에 2.5처럼 소수 슬롯이 될 수 있다.
    # 종료슬롯은 표 렌더링용 정수 컬럼이므로 올림 처리해서 pandas int 컬럼 오류를 막는다.
    display_end_slot = float(new_start) + float(dur_slots)
    sim.loc[mask, "종료슬롯"] = int(display_end_slot + 0.999999)
    sim.loc[mask, "표시종료슬롯"] = display_end_slot
    sim.loc[mask, "시작"] = slot_to_time(int(new_start))
    end_mins = int(9 * 60 + int(new_start) * 30 + int(float(trow["시험시간(분)"])))
    sim.loc[mask, "종료"] = minute_to_time(end_mins)
    sim.loc[mask, "강의실목록"] = [[int(new_room)]]
    sim.loc[mask, "강의실"] = str(int(new_room))

    # 변경 건수/영향
    time_changed = int((int(trow["주차"]) != int(new_week)) or (int(trow["요일번호"]) != int(new_day)) or (int(trow["시작슬롯"]) != int(new_start)))
    room_changed = int(int(new_room) not in set(int(x) for x in trow["강의실목록"]))
    affected_students = len(target_students)

    # 하루 3/4개 증가 추정
    def day_count_map(df: pd.DataFrame) -> dict[tuple[int, int, int], int]:
        out: dict[tuple[int, int, int], int] = {}
        for s_idx in df_is.index:
            sid = int(s_idx)
            for _, er in df.iterrows():
                eidx = int(er["시험인덱스"])
                if sid not in student_sets.get(eidx, set()):
                    continue
                key = (sid, int(er["주차"]), int(er["요일번호"]))
                out[key] = out.get(key, 0) + 1
        return out

    before_day = day_count_map(base)
    after_day = day_count_map(sim)

    before_3 = sum(1 for v in before_day.values() if v >= 3)
    after_3 = sum(1 for v in after_day.values() if v >= 3)
    before_4 = sum(1 for v in before_day.values() if v >= 4)
    after_4 = sum(1 for v in after_day.values() if v >= 4)

    daily_before = sum(daily_penalty_from_count(v) for v in before_day.values())
    daily_after = sum(daily_penalty_from_count(v) for v in after_day.values())

    base_time_move = int(summary.get("time_move_sum", 0))
    base_room_move = int(summary.get("room_move_sum", 0))
    base_daily_penalty = int(summary.get("daily_penalty_sum", 0))
    base_obj = float(summary.get("objective", 0.0))

    new_time_move = base_time_move - int(trow.get("TimeMove_i", 0)) + time_changed
    new_room_move = base_room_move - int(trow.get("RoomChange_i", 0)) + room_changed
    new_daily_penalty = base_daily_penalty - daily_before + daily_after

    new_obj = (
        WEIGHT_ROOM_MOVE * new_room_move
        + WEIGHT_TIME_MOVE * new_time_move
        + WEIGHT_DAILY * new_daily_penalty
    )

    return {
        "feasible": True,
        "affected_students": affected_students,
        "daily3_increase": after_3 - before_3,
        "daily4_increase": after_4 - before_4,
        "room_change_delta": new_room_move - base_room_move,
        "time_move_delta": new_time_move - base_time_move,
        "objective_before": base_obj,
        "objective_after": new_obj,
        "objective_delta": new_obj - base_obj,
    }


def recommend_move_alternatives(
    exam_df: pd.DataFrame,
    target_idx: int,
    student_sets: dict[int, set[int]],
    summary: dict,
    topn: int = 3,
) -> list[dict]:
    target = exam_df[exam_df["시험인덱스"] == target_idx].iloc[0]
    cur_week = int(target["주차"])
    cur_day = int(target["요일번호"])
    cur_start = int(target["시작슬롯"])
    candidates = []
    for w in [7, 8, 9]:
        for d in [1, 2, 3, 4, 5]:
            for ds in [-2, -1, 0, 1, 2]:
                st = cur_start + ds
                if st < 0 or st > 18:
                    continue
                for room in ROOM_ORDER:
                    res = score_move_impact(exam_df, target_idx, w, d, st, int(room), student_sets, summary)
                    if not res.get("feasible", False):
                        continue
                    impact = (
                        abs(float(res["objective_delta"])) * 1000
                        + max(0, int(res["daily4_increase"])) * 100000
                        + max(0, int(res["daily3_increase"])) * 1000
                    )
                    if w == cur_week and d == cur_day and st == cur_start and room in set(int(x) for x in target["강의실목록"]):
                        continue
                    tag = "학생충돌0/영향작음"
                    if int(res["room_change_delta"]) <= 0 and int(res["time_move_delta"]) == 0:
                        tag = "강의실변경 최소"
                    elif int(res["daily3_increase"]) > 0:
                        tag = "일부 학생부담 증가"
                    candidates.append(
                        {
                            "week": w, "day": d, "start": st, "room": int(room),
                            "impact": impact, "tag": tag, **res
                        }
                    )
    candidates = sorted(candidates, key=lambda x: (x["impact"], x["objective_delta"]))
    return candidates[:topn]


def build_original_map(df_ot: pd.DataFrame) -> dict[str, dict]:
    if df_ot.empty:
        return {"base": {}, "exact": {}}

    cmap_base: dict[str, dict] = {}
    cmap_exact: dict[str, dict] = {}
    for _, row in df_ot.iterrows():
        c = str(row.get("course", "")).strip()
        if not c:
            continue
        key_base = normalize_name(c)
        key_exact = normalize_exact(c)
        day = int(float(row.get("day", 0))) if pd.notna(row.get("day", None)) else 0
        start = int(float(row.get("start", 0))) if pd.notna(row.get("start", None)) else 0
        week = int(float(row.get("week", 0))) if pd.notna(row.get("week", None)) else 0
        room = int(float(row.get("room", 0))) if pd.notna(row.get("room", None)) else 0

        cmap_base.setdefault(key_base, {"slots": set(), "rooms": set(), "weekslots": set(), "grade": "-"})
        cmap_exact.setdefault(key_exact, {"slots": set(), "rooms": set(), "weekslots": set(), "grade": "-"})
        if day > 0:
            cmap_base[key_base]["slots"].add((day, start))
            cmap_exact[key_exact]["slots"].add((day, start))
            if week > 0:
                cmap_base[key_base]["weekslots"].add((week, day, start))
                cmap_exact[key_exact]["weekslots"].add((week, day, start))
        if room > 0:
            cmap_base[key_base]["rooms"].add(room)
            cmap_exact[key_exact]["rooms"].add(room)

        # 학년 정보가 파일에 있으면 사용
        for gcol in ["grade", "학년", "year"]:
            if gcol in df_ot.columns and pd.notna(row.get(gcol, None)):
                gval = str(row.get(gcol)).strip()
                if gval:
                    cmap_base[key_base]["grade"] = gval
                    cmap_exact[key_exact]["grade"] = gval

    return {"base": cmap_base, "exact": cmap_exact}


def build_grade_map_from_courseen(df_courseen: pd.DataFrame) -> dict[str, str]:
    grade_map: dict[str, str] = {}
    if df_courseen.empty:
        return grade_map
    course_col = None
    grade_col = None
    for c in df_courseen.columns:
        cs = str(c).strip().lower()
        if course_col is None and cs in ["course_name", "course", "과목", "과목명"]:
            course_col = c
        if grade_col is None and cs in ["grade", "year", "학년"]:
            grade_col = c
    if course_col is None or grade_col is None:
        return grade_map

    for _, row in df_courseen.iterrows():
        cname = str(row.get(course_col, "")).strip()
        if not cname:
            continue
        g = str(row.get(grade_col, "")).strip()
        if not g or g.lower() == "nan":
            continue
        key = normalize_name(cname)
        if key and key not in grade_map:
            grade_map[key] = g
    return grade_map


def add_change_columns(df: pd.DataFrame, orig_maps: dict[str, dict], grade_map: dict[str, str] | None = None) -> pd.DataFrame:
    orig_base = orig_maps.get("base", {})
    grade_map = grade_map or {}
    out = df.copy()
    old_time = []
    old_room = []
    time_status = []
    room_status = []
    final_status = []
    grade_col = []

    for _, r in out.iterrows():
        key = str(r["정규과목"])
        meta = orig_base.get(key, {"slots": set(), "weekslots": set(), "rooms": set(), "grade": "-"})

        cur_week = int(r["주차"])
        cur_day = int(r["요일번호"])
        cur_start = int(r["시작슬롯"])
        cur_rooms = set(r["강의실목록"])

        slots = meta.get("slots", set())
        weekslots = meta.get("weekslots", set())
        rooms = meta.get("rooms", set())

        keep_time = (cur_week, cur_day, cur_start) in weekslots if weekslots else (cur_day, cur_start) in slots
        keep_room = len(cur_rooms & rooms) > 0 if rooms else False

        time_changed = not keep_time
        room_changed = not keep_room

        if not time_changed and not room_changed:
            fs = "유지"
        elif time_changed and room_changed:
            fs = "시간+강의실 변경"
        elif time_changed:
            fs = "시간 변경"
        else:
            fs = "강의실 변경"

        time_status.append("시간 변경" if time_changed else "유지")
        room_status.append("강의실 변경" if room_changed else "유지")
        final_status.append(fs)
        grade_col.append(grade_map.get(key, meta.get("grade", "-")))

        if slots:
            first_slot = sorted(slots)[0]
            old_time.append(f"{DAY_LABELS.get(first_slot[0], first_slot[0])} {slot_to_time(first_slot[1])}")
        else:
            old_time.append("-")

        old_room.append(" ".join(str(x) for x in sorted(rooms)) if rooms else "-")

    out["학년"] = grade_col
    out["기존시간"] = old_time
    out["기존강의실"] = old_room
    out["시간변경여부"] = time_status
    out["강의실변경여부"] = room_status
    out["변경상태"] = final_status
    if "과목명" not in out.columns:
        out["과목명"] = out["과목"].apply(to_korean_course_name)
    return out


def _extract_section_no(text: str) -> int | None:
    m = re.search(r"[-_](\d+)$", str(text).strip())
    if not m:
        return None
    return int(m.group(1))


def add_change_columns_student(
    df_student: pd.DataFrame,
    df_is: pd.DataFrame,
    row_idx: int,
    orig_maps: dict[str, dict],
    grade_map: dict[str, str] | None = None,
) -> pd.DataFrame:
    out = df_student.copy()
    orig_base = orig_maps.get("base", {})
    orig_exact = orig_maps.get("exact", {})
    grade_map = grade_map or {}
    is_cols = [str(c) for c in df_is.columns]

    old_time = []
    old_room = []
    section_used = []
    time_status = []
    room_status = []
    final_status = []
    grade_col = []

    for _, r in out.iterrows():
        course = str(r["과목"])
        base_key = str(r["정규과목"])
        cur_week = int(r["주차"])
        cur_day = int(r["요일번호"])
        cur_start = int(r["시작슬롯"])
        cur_rooms = set(r["강의실목록"])

        # 1) 학생이 실제 수강한 분반 컬럼 찾기(IS 기준)
        match_cols = resolve_is_columns_for_course(is_cols, course)
        taken_cols = []
        for c in match_cols:
            try:
                v = float(df_is.at[row_idx, c])
                if v > 0:
                    taken_cols.append(c)
            except Exception:
                continue

        # 2) 분반 우선 매핑(정확키) -> 실패 시 기본(통합키)
        meta = None
        picked_section = "-"
        for c in taken_cols:
            k = normalize_exact(c)
            if k in orig_exact:
                meta = orig_exact[k]
                picked_section = c
                break

        if meta is None and taken_cols:
            sec = _extract_section_no(taken_cols[0])
            if sec is not None:
                # 오탈자(예: IntroIE&M vs IntrolE&M) 보완: 분반 번호로 후보 탐색
                for k, v in orig_exact.items():
                    if k.endswith(f"-{sec}") or k.endswith(f"_{sec}"):
                        if normalize_name(k).startswith(base_key[:6]) or base_key.startswith(normalize_name(k)[:6]):
                            meta = v
                            picked_section = k
                            break

        if meta is None:
            meta = orig_base.get(base_key, {"slots": set(), "weekslots": set(), "rooms": set(), "grade": "-"})

        slots = meta.get("slots", set())
        weekslots = meta.get("weekslots", set())
        rooms = meta.get("rooms", set())

        keep_time = (cur_week, cur_day, cur_start) in weekslots if weekslots else (cur_day, cur_start) in slots
        keep_room = len(cur_rooms & rooms) > 0 if rooms else False

        time_changed = not keep_time
        room_changed = not keep_room

        if not time_changed and not room_changed:
            fs = "유지"
        elif time_changed and room_changed:
            fs = "시간+강의실 변경"
        elif time_changed:
            fs = "시간 변경"
        else:
            fs = "강의실 변경"

        # 원래시간은 첫 슬롯 1개가 아니라 분반의 전체 시간(요일/시작) 목록을 표시
        if slots:
            parts = []
            for d, st in sorted(slots, key=lambda x: (x[0], x[1])):
                parts.append(f"{DAY_LABELS.get(d, d)} {slot_to_time(st)}")
            old_time.append(", ".join(parts))
        else:
            old_time.append("-")
        old_room.append(" ".join(str(x) for x in sorted(rooms)) if rooms else "-")
        time_status.append("시간 변경" if time_changed else "유지")
        room_status.append("강의실 변경" if room_changed else "유지")
        final_status.append(fs)
        section_used.append(picked_section)
        grade_col.append(grade_map.get(base_key, meta.get("grade", "-")))

    out["분반기준"] = section_used
    out["학년"] = grade_col
    out["원래시간(내분반)"] = old_time
    out["원래강의실(내분반)"] = old_room
    # 기존 컬럼도 유지(다른 화면/다운로드 호환)
    out["기존시간"] = old_time
    out["기존강의실"] = old_room
    out["시간변경여부"] = time_status
    out["강의실변경여부"] = room_status
    out["변경상태"] = final_status
    if "과목명" not in out.columns:
        out["과목명"] = out["과목"].apply(to_korean_course_name)
    return out


def build_calendar_html(df_student: pd.DataFrame, target_week: int, clickable: bool = False) -> str:
    time_rows = [slot_to_time(s) for s in range(0, 22)]
    table = {t: {d: "" for d in DAY_ORDER} for t in time_rows}
    df_w = df_student[df_student["주차"] == target_week].copy()

    for _, r in df_w.iterrows():
        day = str(r.get("요일", ""))
        if day not in DAY_ORDER:
            continue
        s0 = int(r.get("시작슬롯", 0))
        s1 = int(float(r.get("표시종료슬롯", r.get("종료슬롯", s0))) + 0.999999)
        show_course = r.get("과목명", r.get("과목", ""))
        grade_txt = format_grade_label(r.get("학년", fallback_grade_for_course(r.get("과목", show_course))))
        start_txt = str(r.get("시작", ""))
        end_txt = str(r.get("종료", ""))
        room_txt = str(r.get("강의실", "-"))
        dur_txt = str(r.get("시험시간(분)", ""))
        text_main = (
            "<div class='exam-block'>"
            f"<div class='course'>{show_course}<span class='grade-pill'>{grade_txt}</span></div>"
            f"<div>{start_txt}~{end_txt} · {dur_txt}분</div>"
            f"<div class='room-line'>강의실 {room_txt}</div>"
            "</div>"
        )
        if clickable and "시험인덱스" in r:
            idx_val = int(r.get("시험인덱스", -1))
            text_main = (
                f"<a href='?pick={idx_val}&week={target_week}' class='exam-link'>"
                f"{text_main}</a>"
            )
        for s in range(s0, s1):
            tlabel = slot_to_time(s)
            if s == s0:
                table[tlabel][day] = text_main
            else:
                table[tlabel][day] = "<div class='cont'></div>"

    html_rows = []
    for t in time_rows:
        cells = [f"<td class='time-col'>{t}</td>"]
        for d in DAY_ORDER:
            val = table[t][d]
            cls = "exam" if val else "empty"
            cells.append(f"<td class='{cls}'>{val}</td>")
        html_rows.append("<tr>" + "".join(cells) + "</tr>")

    table_html = (
        "<div class='calendar-wrap'><table><thead><tr><th>시간</th>"
        + "".join(f"<th>{d}</th>" for d in DAY_ORDER)
        + "</tr></thead><tbody>"
        + "".join(html_rows)
        + "</tbody></table></div>"
    )
    return table_html


def build_feasible_area_html(
    exam_df: pd.DataFrame,
    target_idx: int,
    target_week: int,
    target_room: int,
    student_sets: dict[int, set[int]],
    summary: dict,
) -> tuple[str, list[dict]]:
    time_rows = [slot_to_time(s) for s in range(0, 22)]
    table = {t: {d: "" for d in DAY_ORDER} for t in time_rows}
    df_w = exam_df[exam_df["주차"] == target_week].copy()

    # 기존 배정(연파랑)
    for _, r in df_w.iterrows():
        day = str(r.get("요일", ""))
        if day not in DAY_ORDER:
            continue
        s0 = int(r.get("시작슬롯", 0))
        s1 = int(float(r.get("표시종료슬롯", r.get("종료슬롯", s0))) + 0.999999)
        show_course = r.get("과목명", r.get("과목", ""))
        grade_txt = str(r.get("학년", "-"))
        for s in range(s0, s1):
            tlabel = slot_to_time(s)
            if s == s0:
                table[tlabel][day] = f"<div class='course'>{show_course}</div><div>{grade_txt}학년</div>"
            else:
                table[tlabel][day] = "<div class='cont'></div>"

    # 가능 영역(초록) + 목적함수 변화 요약 텍스트
    feasible_rows: list[dict] = []
    cell_delta: dict[tuple[str, str], float] = {}
    day_labels = ["월", "화", "수", "목", "금"]
    duration_slots = int(
        float(exam_df.loc[exam_df["시험인덱스"] == target_idx, "표시종료슬롯"].iloc[0])
        - float(exam_df.loc[exam_df["시험인덱스"] == target_idx, "시작슬롯"].iloc[0])
    )
    for d in day_labels:
        dnum = DAY_KO_TO_NUM[d]
        for st_slot in range(0, 19):
            out = score_move_impact(
                exam_df=exam_df,
                target_idx=int(target_idx),
                new_week=int(target_week),
                new_day=int(dnum),
                new_start=int(st_slot),
                new_room=int(target_room),
                student_sets=student_sets,
                summary=summary,
            )
            if not out.get("feasible", False):
                continue
            feasible_rows.append(
                {
                    "요일": d,
                    "시작": slot_to_time(st_slot),
                    "종료": slot_to_time(st_slot + duration_slots),
                    "강의실": int(target_room),
                    "영향학생수": int(out["affected_students"]),
                    "하루3개증가": int(out["daily3_increase"]),
                    "하루4개증가": int(out["daily4_increase"]),
                    "목적함수변화": float(out["objective_delta"]),
                }
            )
            cell_delta[(d, slot_to_time(st_slot))] = float(out["objective_delta"])
            for s in range(st_slot, st_slot + duration_slots):
                tlabel = slot_to_time(s)
                if tlabel not in table:
                    continue
                if table[tlabel][d]:
                    continue
                if s == st_slot:
                    dlt = float(cell_delta.get((d, slot_to_time(st_slot)), 0.0))
                    table[tlabel][d] = (
                        "<div style='background:#dcfce7;color:#14532d;font-weight:800;border-radius:6px;padding:2px 4px;'>"
                        f"가능<br>Δ {dlt:+.2f}</div>"
                    )
                else:
                    table[tlabel][d] = (
                        "<div style='background:#dcfce7;color:#14532d;font-weight:700;border-radius:6px;padding:2px 4px;'>·</div>"
                    )

    html_rows = []
    for t in time_rows:
        cells = [f"<td class='time-col'>{t}</td>"]
        for d in DAY_ORDER:
            val = table[t][d]
            cls = "exam" if val else "empty"
            cells.append(f"<td class='{cls}'>{val}</td>")
        html_rows.append("<tr>" + "".join(cells) + "</tr>")

    table_html = (
        "<div class='calendar-wrap'><table><thead><tr><th>시간</th>"
        + "".join(f"<th>{d}</th>" for d in DAY_ORDER)
        + "</tr></thead><tbody>"
        + "".join(html_rows)
        + "</tbody></table></div>"
    )
    return table_html, feasible_rows


def get_feasible_rooms_for_week(
    exam_df: pd.DataFrame,
    target_idx: int,
    target_week: int,
    student_sets: dict[int, set[int]],
    summary: dict,
) -> list[int]:
    rooms = []
    for room in ROOM_ORDER:
        _html, rows = build_feasible_area_html(
            exam_df=exam_df,
            target_idx=target_idx,
            target_week=target_week,
            target_room=int(room),
            student_sets=student_sets,
            summary=summary,
        )
        if rows:
            rooms.append(int(room))
    return rooms


def load_report_images() -> tuple[list[Path], Path | None]:
    report_dir = find_existing_dir(REPORT_DIR_CANDIDATES)
    if report_dir is None:
        return [], None
    images = sorted(
        [p for p in report_dir.glob("*.png") if p.is_file()],
        key=lambda p: p.name,
    )
    return images, report_dir


def generate_fallback_report_images(exam_df: pd.DataFrame, summary: dict, out_dir: Path) -> None:
    """리포트 png가 없을 때 최소 시각화 파일을 자동 생성한다."""
    try:
        import matplotlib.pyplot as plt
    except Exception:
        return

    out_dir.mkdir(parents=True, exist_ok=True)

    # summary image
    summary_img = out_dir / "page_00_summary.png"
    fig = plt.figure(figsize=(10, 4))
    fig.patch.set_facecolor("white")
    lines = [
        "Optimization Summary",
        f"Objective: {float(summary.get('objective', 0)):.4f}",
        f"RoomMoveSum: {int(summary.get('room_move_sum', 0))}",
        f"TimeMoveSum: {int(summary.get('time_move_sum', 0))}",
        f"DailyPenaltySum: {int(summary.get('daily_penalty_sum', 0))}",
        f"OverlapViolation: {int(summary.get('overlap_violation', 0))}",
        f"SectionConsecutiveViolation: {int(summary.get('section_overlap_violation', 0))}",
    ]
    fig.text(0.05, 0.9, "\n".join(lines), fontsize=14, va="top")
    fig.savefig(summary_img, dpi=150, bbox_inches="tight")
    plt.close(fig)

    # room images
    for room in ROOM_ORDER:
        room_img = out_dir / f"page_room_{room}.png"
        room_df = exam_df[exam_df["강의실목록"].apply(lambda xs: int(room) in set(xs))].copy()
        room_df = room_df.sort_values(["주차", "요일번호", "시작슬롯"])
        fig = plt.figure(figsize=(12, 6))
        fig.patch.set_facecolor("white")
        title = f"ROOM {room} Exam Timetable (Week 7/8/9)"
        fig.text(0.03, 0.95, title, fontsize=16, weight="bold", va="top")
        if room_df.empty:
            fig.text(0.03, 0.80, "No assigned exams.", fontsize=13)
        else:
            y = 0.88
            for _, r in room_df.iterrows():
                line = (
                    f"{int(r['주차'])}주차 {r['요일']} {r['시작']}~{r['종료']}  |  "
                    f"{r['과목명']} ({int(r['시험시간(분)'])}분)"
                )
                fig.text(0.03, y, line, fontsize=11, va="top")
                y -= 0.03
                if y < 0.05:
                    break
        fig.savefig(room_img, dpi=150, bbox_inches="tight")
        plt.close(fig)


def build_optimization_summary_df(payload: dict) -> pd.DataFrame:
    summary = payload.get("summary", {})
    rows = [
        ["목적함수값", f"{float(summary.get('objective', 0)):.4f}"],
        ["가중치(강의실이동)", f"{WEIGHT_ROOM_MOVE:.4f}"],
        ["가중치(시간이동)", f"{WEIGHT_TIME_MOVE:.4f}"],
        ["가중치(하루시험수)", f"{WEIGHT_DAILY:.4f}"],
        ["요일 이동 한계 D_max", str(D_MAX)],
        ["시간 이동 한계 T_max", str(T_MAX)],
        ["강의실 변경 합", str(int(summary.get("room_move_sum", 0)))],
        ["시간 이동 합", str(int(summary.get("time_move_sum", 0)))],
        ["하루 시험수 벌점 합", str(int(summary.get("daily_penalty_sum", 0)))],
        ["학생 동시시험 위반", str(int(summary.get("overlap_violation", 0)))],
        ["같은과목 분반 연속배정 위반", str(int(summary.get("section_overlap_violation", 0)))],
        ["하루 4시험 위반", str(int(summary.get("daily4_count", 0)))],
        ["실행시간(초)", f"{float(summary.get('runtime_sec', 0)):.4f}"],
        ["Gurobi 시간(초)", f"{float(summary.get('gurobi_runtime_sec', 0)):.4f}"],
    ]
    return pd.DataFrame(rows, columns=["항목", "값"])


def build_verify_df(payload: dict) -> pd.DataFrame:
    rows = payload.get("verify_rows", [])
    if rows:
        normalized = []
        labels = {
            "(1)": "과목 1회 배정",
            "(2)": "필요 강의실 수",
            "(3)": "수용인원",
            "(4)": "강의실 중복",
            "(5)": "학생 동시시험",
            "(5-1)": "같은과목 분반연속배정",
            "(7)": "하루 4시험 금지",
            "(8)": "벌점정의",
            "(9)": "강의실변경정의",
            "(10)": "시간이동정의",
            "(11)": "최대이동 허용",
        }
        for idx, row in enumerate(rows):
            key = str(row[0]) if len(row) > 0 else f"({idx + 1})"
            count = str(row[1]) if len(row) > 1 else "0"
            prefix = key.split()[0] if " " in key else key
            label = labels.get(prefix, key)
            normalized.append([f"{prefix} {label}", count])
        return pd.DataFrame(normalized, columns=["제약식", "위반건수"])
    return pd.DataFrame(
        [
            ["(5) 학생 동시시험", str(int(payload.get("summary", {}).get("overlap_violation", 0)))],
            ["(5-1) 같은과목 분반연속배정", str(int(payload.get("summary", {}).get("section_overlap_violation", 0)))],
            ["(7) 하루 4시험 금지", str(int(payload.get("summary", {}).get("daily4_count", 0)))],
        ],
        columns=["제약식", "위반건수"],
    )


def build_decision_df(payload: dict, exam_df: pd.DataFrame) -> pd.DataFrame:
    fallback = exam_df.copy().sort_values(["주차", "요일번호", "시작슬롯", "과목명"])
    out = pd.DataFrame()
    out["과목명"] = fallback["과목명"]
    out["x_iwdt"] = fallback.apply(lambda r: f"({int(r['주차'])}, {str(r['요일'])}, {str(r['시작'])})", axis=1)
    out["z_iwdtr"] = fallback["강의실"]
    out["TimeMove_i"] = fallback["TimeMove_i"]
    out["RoomChange_i"] = fallback["RoomChange_i"]
    return out.reset_index(drop=True)


def fill_missing_grade(df: pd.DataFrame, grade_map: dict[str, str]) -> pd.DataFrame:
    out = df.copy()
    if "학년" not in out.columns:
        out["학년"] = "-"
    filled = []
    for _, row in out.iterrows():
        val = str(row.get("학년", "")).strip()
        if val and val != "-" and val.lower() != "nan":
            filled.append(val)
            continue
        key = str(row.get("정규과목", "")).strip()
        if not key:
            key = normalize_name(row.get("과목", ""))
        # 원본 학년 데이터가 없을 때 임의 숫자 부여를 하지 않고 '-'로 유지한다.
        filled.append(grade_map.get(key, "-"))
    out["학년"] = filled
    return out


def dataframe_to_html_table(df: pd.DataFrame, highlight_cols: list[str] | None = None) -> str:
    highlight_cols = highlight_cols or []
    parts = ["<div class='result-table-wrap'><table class='result-table'><thead><tr>"]
    for col in df.columns:
        parts.append(f"<th>{html.escape(str(col))}</th>")
    parts.append("</tr></thead><tbody>")

    for _, row in df.iterrows():
        parts.append("<tr>")
        for col in df.columns:
            val = "" if pd.isna(row[col]) else str(row[col])
            cls = ""
            if col in highlight_cols and ("변경" in val and val != "유지"):
                cls = " class='change'"
            parts.append(f"<td{cls}>{html.escape(val)}</td>")
        parts.append("</tr>")
    parts.append("</tbody></table></div>")
    return "".join(parts)


def render_calendar_grid(df_student: pd.DataFrame, target_week: int):
    st.markdown(f"#### {target_week}주차 캘린더형 시험시간표")
    table_html = build_calendar_html(df_student, target_week)
    st.markdown(table_html, unsafe_allow_html=True)


def render_clickable_calendar(
    calendar_df: pd.DataFrame,
    target_week: int,
    key_prefix: str,
    feasible_rows: list[dict] | None = None,
    selected_candidate: dict | None = None,
) -> None:
    feasible_map = {}
    for row in feasible_rows or []:
        feasible_map[(str(row["요일"]), str(row["시작"]))] = row
    selected_key = None
    if selected_candidate:
        selected_key = (str(selected_candidate.get("요일")), str(selected_candidate.get("시작")))

    df_w = calendar_df[calendar_df["주차"] == target_week].copy()
    starts = {}
    cont = set()
    for _, r in df_w.iterrows():
        day = str(r.get("요일", ""))
        if day not in DAY_ORDER:
            continue
        s0 = int(r.get("시작슬롯", 0))
        s1 = int(r.get("종료슬롯", s0))
        starts[(day, slot_to_time(s0))] = r
        for s in range(s0 + 1, s1):
            cont.add((day, slot_to_time(s)))

    st.markdown(
        "<div class='click-grid-head'><div class='click-grid-cell'>시간</div>"
        + "".join(f"<div class='click-grid-cell'>{d}</div>" for d in DAY_ORDER)
        + "</div>",
        unsafe_allow_html=True,
    )

    for slot in range(0, 22):
        time_label = slot_to_time(slot)
        cols = st.columns([0.8, 1, 1, 1, 1, 1])
        cols[0].markdown(f"<div class='click-grid-time'>{time_label}</div>", unsafe_allow_html=True)
        for idx, day in enumerate(DAY_ORDER, start=1):
            key = (day, time_label)
            if key in feasible_map:
                delta = float(feasible_map[key]["목적함수변화"])
                css_class = "click-grid-selected-move" if key == selected_key else "click-grid-possible"
                title = "선택안" if key == selected_key else "가능"
                cols[idx].markdown(
                    f"<div class='{css_class}'>"
                    f"{title}<br>Δ {delta:+.2f}<br>"
                    f"{int(feasible_map[key]['영향학생수'])}명 영향</div>",
                    unsafe_allow_html=True,
                )
            elif key in starts:
                r = starts[key]
                exam_idx = int(r["시험인덱스"])
                selected_mark = "선택됨\n" if int(st.session_state.get("sim_selected_idx") or -1) == exam_idx else ""
                label = f"{selected_mark}{r['과목명']}\n{r['강의실']}\n{r['시작']}~{r['종료']}"
                if cols[idx].button(label, key=f"{key_prefix}_pick_{target_week}_{exam_idx}_{day}_{slot}"):
                    st.session_state.sim_selected_idx = exam_idx
                    st.rerun()
            elif key in cont:
                cols[idx].markdown("<div class='click-grid-cont'></div>", unsafe_allow_html=True)
            else:
                cols[idx].markdown("<div class='click-grid-cell'></div>", unsafe_allow_html=True)


def render_room_calendar_fallback(exam_df_src: pd.DataFrame, room_no: int, key_prefix: str):
    room_df = exam_df_src[exam_df_src["강의실목록"].apply(lambda xs: room_no in set(xs))].copy()
    room_df = room_df.sort_values(["주차", "start_dt", "과목명"]).reset_index(drop=True)
    week_choice = st.radio(
        f"{room_no}호 주차 선택",
        ["7주차", "8주차", "9주차"],
        horizontal=True,
        key=f"{key_prefix}_week",
    )
    wk = int(str(week_choice).replace("주차", ""))
    st.markdown(f"##### 강의실 {room_no} | {wk}주차")
    st.markdown(build_calendar_html(room_df, wk), unsafe_allow_html=True)


def student_summary_cards(df_student: pd.DataFrame):
    def _card_html(a: str, b: str, c: str, d: str, e: str) -> str:
        cards = [
            ("내 시험 개수", a),
            ("첫 시험", b),
            ("마지막 시험", c),
            ("하루 최대 시험 수", d),
            ("연속 시험 여부", e),
        ]
        parts = ["<div class='big-summary-row'>"]
        for title, val in cards:
            parts.append(
                "<div class='big-summary-card'>"
                f"<div class='big-summary-title'>{html.escape(title)}</div>"
                f"<div class='big-summary-value'>{html.escape(val)}</div>"
                "</div>"
            )
        parts.append("</div>")
        return "".join(parts)

    if df_student.empty:
        st.markdown(_card_html("0", "-", "-", "0", "없음"), unsafe_allow_html=True)
        return

    count_exam = len(df_student)
    first_exam = df_student["start_dt"].min()
    last_exam = df_student["start_dt"].max()

    day_counts = df_student.groupby(["주차", "요일", "날짜"]).size()
    max_per_day = int(day_counts.max()) if len(day_counts) else 0

    dfx = df_student.sort_values("start_dt")[["start_dt", "end_dt"]].reset_index(drop=True)
    consecutive = False
    for i in range(len(dfx) - 1):
        if dfx.loc[i, "end_dt"] == dfx.loc[i + 1, "start_dt"]:
            consecutive = True
            break

    st.markdown(
        _card_html(
            str(count_exam),
            first_exam.strftime("%m/%d %H:%M"),
            last_exam.strftime("%m/%d %H:%M"),
            str(max_per_day),
            "있음" if consecutive else "없음",
        ),
        unsafe_allow_html=True,
    )


def make_student_calendar_png(df_student: pd.DataFrame, sid: str) -> bytes | None:
    try:
        import matplotlib.pyplot as plt
    except Exception:
        return None
    if df_student.empty:
        return None

    df = df_student.copy().sort_values(["주차", "요일번호", "시작슬롯"])
    rows = []
    for _, r in df.iterrows():
        rows.append(
            [
                f"{int(r['주차'])}주차",
                str(r["요일"]),
                str(r["시작"]),
                str(r["종료"]),
                str(r["과목명"]),
                str(r["강의실"]),
            ]
        )
    cols = ["주차", "요일", "시작", "종료", "과목", "강의실"]
    data = pd.DataFrame(rows, columns=cols)

    fig_h = max(4, min(18, 1.0 + 0.35 * len(data)))
    fig, ax = plt.subplots(figsize=(14, fig_h))
    ax.axis("off")
    ax.set_title(f"학번 {sid} 시험 캘린더 요약", fontsize=14, pad=10)
    tbl = ax.table(cellText=data.values, colLabels=data.columns, loc="center", cellLoc="center")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    tbl.scale(1, 1.2)

    import io as _io
    buf = _io.BytesIO()
    fig.savefig(buf, format="png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def make_student_calendar_ics(df_student: pd.DataFrame, sid: str) -> bytes:
    """학생 개인 시험 일정을 휴대폰/Google Calendar에 넣을 수 있는 ICS 파일로 만든다."""
    def esc(text) -> str:
        return str(text or "").replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")

    now = datetime.now().strftime("%Y%m%dT%H%M%S")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//INUTimetable//Exam Timetable//KO",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:INUTimetable {esc(sid)} 시험시간표",
    ]

    for _, r in df_student.sort_values(["start_dt", "과목명"]).iterrows():
        start = pd.to_datetime(r["start_dt"]).strftime("%Y%m%dT%H%M%S")
        end = pd.to_datetime(r["end_dt"]).strftime("%Y%m%dT%H%M%S")
        course = esc(r.get("과목명", r.get("과목", "")))
        room = esc(r.get("강의실", "-"))
        week = esc(r.get("주차", "-"))
        uid = f"inutimetable-{sid}-{int(r.get('시험인덱스', 0))}@inu"
        desc = esc(
            f"{week}주차 {r.get('요일', '')} {r.get('시작', '')}~{r.get('종료', '')} / "
            f"강의실 {room} / {r.get('시험시간(분)', '')}분"
        )
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{now}",
                f"DTSTART:{start}",
                f"DTEND:{end}",
                f"SUMMARY:{course} 시험",
                f"LOCATION:강의실 {room}",
                f"DESCRIPTION:{desc}",
                "END:VEVENT",
            ]
        )

    lines.append("END:VCALENDAR")
    return ("\r\n".join(lines) + "\r\n").encode("utf-8")


# -------------------------------------------------
# 데이터 로드
# -------------------------------------------------
try:
    payload, payload_path = load_result_payload()
except Exception as e:
    st.error(str(e))
    st.stop()

try:
    df_is, is_path = load_is_df()
except Exception as e:
    st.error(str(e))
    st.stop()

df_ot, ot_path = load_ot_df()
df_courseen, courseen_path = load_courseen_df()
exam_df = build_exam_df(payload)
orig_maps = build_original_map(df_ot)
grade_map = build_grade_map_from_courseen(df_courseen)
exam_df = add_change_columns(exam_df, orig_maps, grade_map)
exam_df = fill_missing_grade(exam_df, grade_map)
opt_summary_df = build_optimization_summary_df(payload)
verify_df = build_verify_df(payload)
decision_df = build_decision_df(payload, exam_df)
report_images, report_dir = load_report_images()
if report_dir is None:
    report_dir = BASE_DIR / "결과_리포트"
if not report_images:
    generate_fallback_report_images(exam_df, payload.get("summary", {}), report_dir)
    report_images, report_dir = load_report_images()

summary = payload.get("summary", {})

# -------------------------------------------------
# UI
# -------------------------------------------------
st.title("INUTimetable")
st.caption("빌드: 66aea8a-hotfix")
st.caption("최적화 결과 조회 서비스 | 충돌 최소화 · 학생 부담 완화")

with st.sidebar:
    st.header("메뉴")
    menu = st.radio("페이지 선택", ["최적화 결과", "학번별 조회", "전체 시간표", "변경사항 확인"], index=0)
    st.markdown("---")
    st.caption(f"결과 파일: {payload_path}")
    st.caption(f"IS 파일: {is_path}")
    if ot_path is not None:
        st.caption(f"OT 파일: {ot_path}")
    if courseen_path is not None:
        st.caption(f"CourseEn 파일: {courseen_path}")

# 전체 요약 카드
g1, g2, g3, g4, g5 = st.columns(5)
g1.metric("전체 시험 과목 수", int(exam_df["과목"].nunique()))
used_rooms = set(sum(exam_df["강의실목록"].tolist(), []))
g2.metric("사용/후보 강의실 수", f"{len(used_rooms)}/{len(ROOM_ORDER)}")
g3.metric("학생 충돌 여부", "없음" if int(summary.get("overlap_violation", 0)) == 0 else "있음")
g4.metric("분반 연속배정 위반", "없음" if int(summary.get("section_overlap_violation", 0)) == 0 else "있음")
g5.metric("최적화 penalty 점수", f"{float(summary.get('objective', 0)):.4f}")

if menu == "학번별 조회":
    st.subheader("학번별 시험시간표 조회")

    if "searched_sid" not in st.session_state:
        st.session_state.searched_sid = ""
    if "search_ok" not in st.session_state:
        st.session_state.search_ok = False

    with st.form("search_form"):
        sid_input = st.text_input("학번 입력", value=st.session_state.searched_sid)
        submitted = st.form_submit_button("검색")

    if submitted:
        sid = sid_input.strip()
        if not sid:
            st.session_state.search_ok = False
            st.warning("학번을 입력하세요.")
        else:
            row_idx_tmp = find_student_row(df_is, sid)
            if row_idx_tmp is None:
                st.session_state.search_ok = False
                st.warning("검색 결과가 없습니다. 학번을 다시 확인하세요.")
            else:
                st.session_state.searched_sid = sid
                st.session_state.search_ok = True
                if "selected_week" not in st.session_state:
                    st.session_state.selected_week = 7

    if st.session_state.search_ok and st.session_state.searched_sid:
        sid = st.session_state.searched_sid
        row_idx = find_student_row(df_is, sid)
        if row_idx is not None:
            df_student = student_exam_df(exam_df, df_is, row_idx)
            df_student = add_change_columns_student(df_student, df_is, row_idx, orig_maps, grade_map)
            df_student = fill_missing_grade(df_student, grade_map)

            student_summary_cards(df_student)

            week_label = st.radio(
                "주차 선택",
                ["7주차", "8주차", "9주차"],
                horizontal=True,
                key="week_selector_radio",
            )
            cur_week = int(str(week_label).replace("주차", ""))
            st.markdown(f"### 현재 페이지: {cur_week}주차")
            try:
                render_calendar_grid(df_student, cur_week)
            except Exception:
                st.warning("해당 주차 렌더링 중 문제가 있어 빈 시간표로 표시합니다.")
                render_calendar_grid(pd.DataFrame(columns=df_student.columns), cur_week)

            st.markdown("#### 시험 상세 표")
            show_cols = [
                "과목명", "학년", "주차", "요일", "날짜", "시작", "종료", "시험시간(분)", "강의실",
                "원래시간(내분반)", "원래강의실(내분반)", "시간변경여부", "강의실변경여부",
            ]
            for col in show_cols:
                if col not in df_student.columns:
                    df_student[col] = "-"
            view_df = df_student[show_cols].copy()
            st.markdown(
                dataframe_to_html_table(
                    view_df,
                    highlight_cols=["시간변경여부", "강의실변경여부"],
                ),
                unsafe_allow_html=True,
            )

            # 캘린더 다운로드(항상 노출)
            calendar_blocks = []
            for w in [7, 8, 9]:
                calendar_blocks.append(f"<h2>{w}주차</h2>")
                calendar_blocks.append(build_calendar_html(df_student, w))

            calendar_doc = (
                "<!doctype html><html lang='ko'><head><meta charset='utf-8'>"
                "<title>학생 시험 캘린더</title></head><body>"
                f"<h1>학번 {sid} 시험 캘린더</h1>"
                + "".join(calendar_blocks)
                + "</body></html>"
            )
            st.download_button(
                "캘린더 다운로드(HTML)",
                data=calendar_doc.encode("utf-8"),
                file_name=f"student_{sid}_calendar.html",
                mime="text/html",
            )
            png_bytes = make_student_calendar_png(df_student, sid)
            if png_bytes is not None:
                st.download_button(
                    "캘린더 이미지 저장(PNG)",
                    data=png_bytes,
                    file_name=f"student_{sid}_calendar.png",
                    mime="image/png",
                )
            st.download_button(
                "휴대폰/Google 캘린더에 저장(ICS)",
                data=make_student_calendar_ics(df_student, sid),
                file_name=f"student_{sid}_exam_calendar.ics",
                mime="text/calendar",
            )

            st.markdown("#### 시각화 파일")
            room_choice_student = st.selectbox(
                "강의실 선택(학번별 조회)",
                [str(r) for r in ROOM_ORDER],
                index=0,
                key="student_room_select",
            )
            selected_room_path_student = report_dir / f"page_room_{room_choice_student}.png" if report_dir is not None else None
            if selected_room_path_student is not None and selected_room_path_student.exists():
                st.image(str(selected_room_path_student), use_container_width=True)
            else:
                render_room_calendar_fallback(exam_df, int(room_choice_student), "student_room_fallback")

            # 해석 문구
            total_n = len(df_student)
            max_day = int(df_student.groupby(["주차", "요일", "날짜"]).size().max()) if total_n else 0
            changed_n = int(
                (
                    (df_student["시간변경여부"] == "시간 변경")
                    | (df_student["강의실변경여부"] == "강의실 변경")
                ).sum()
            ) if total_n else 0
            dfx = df_student.sort_values("start_dt")[["start_dt", "end_dt"]].reset_index(drop=True)
            has_consec = any(dfx.loc[i, "end_dt"] == dfx.loc[i + 1, "start_dt"] for i in range(max(0, len(dfx)-1)))

            st.info(
                f"해당 학생은 총 {total_n}개의 시험이 배정되었습니다. "
                f"하루 최대 시험 수는 {max_day}개입니다. "
                f"연속 시험은 {'있습니다' if has_consec else '없습니다'}. "
                f"내 분반 기준 원래 시간/강의실 대비 변경된 과목은 {changed_n}개입니다."
            )


elif menu == "전체 시간표":
    st.subheader("전체 시간표")

    if "manual_moves" not in st.session_state:
        st.session_state.manual_moves = {}
    if "manual_move_history" not in st.session_state:
        st.session_state.manual_move_history = []
    if "sim_selected_idx" not in st.session_state:
        st.session_state.sim_selected_idx = None

    def _apply_manual_moves(df_src: pd.DataFrame) -> pd.DataFrame:
        out = df_src.copy()
        for k, mv in st.session_state.manual_moves.items():
            idx = int(k)
            mask = out["시험인덱스"] == idx
            if not mask.any():
                continue
            dur_min = int(out.loc[mask, "시험시간(분)"].iloc[0])
            dur_slots = max(1, int((dur_min + 29) // 30))
            out.loc[mask, "주차"] = int(mv["week"])
            out.loc[mask, "요일번호"] = int(mv["day"])
            out.loc[mask, "요일"] = DAY_LABELS.get(int(mv["day"]), str(mv["day"]))
            out.loc[mask, "시작슬롯"] = int(mv["start_slot"])
            out.loc[mask, "종료슬롯"] = int(mv["start_slot"]) + dur_slots
            out.loc[mask, "표시종료슬롯"] = float(int(mv["start_slot"]) + dur_slots)
            out.loc[mask, "시작"] = slot_to_time(int(mv["start_slot"]))
            out.loc[mask, "종료"] = minute_to_time(540 + int(mv["start_slot"]) * 30 + dur_min)
            out.loc[mask, "강의실"] = str(int(mv["room"]))
            out.loc[mask, "강의실목록"] = [[int(mv["room"])] for _ in range(int(mask.sum()))]
        return out

    exam_df_view = _apply_manual_moves(exam_df)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        sim_week_view = st.selectbox("주차", ["7주차", "8주차", "9주차"], key="sim_week_view")
    with c2:
        viz_room = st.selectbox("강의실", [str(r) for r in ROOM_ORDER], key="overall_viz_room")
    with c3:
        viz_grade = st.selectbox("학년", ["전체", "1", "2", "3", "4"], key="overall_viz_grade")
    with c4:
        course_options = ["전체"] + sorted(exam_df_view["과목명"].astype(str).dropna().unique().tolist())
        viz_course = st.selectbox("과목", course_options, key="overall_viz_course")

    sim_week_num = int(str(sim_week_view).replace("주차", ""))
    current_filter_sig = f"{sim_week_num}|{viz_room}|{viz_grade}|{viz_course}"
    if st.session_state.get("sim_filter_sig") != current_filter_sig:
        st.session_state.sim_filter_sig = current_filter_sig
        st.session_state.sim_selected_idx = None
    calendar_src = exam_df_view.copy()
    calendar_src = calendar_src[calendar_src["강의실목록"].apply(lambda xs: int(viz_room) in set(xs))]
    if viz_grade != "전체":
        calendar_src = calendar_src[calendar_src["학년"].astype(str).str.replace("학년", "", regex=False).str.strip() == str(viz_grade)]
    if viz_course != "전체":
        calendar_src = calendar_src[calendar_src["과목명"].astype(str) == str(viz_course)]
    calendar_src = calendar_src.sort_values(["주차", "요일번호", "시작슬롯", "과목명"]).reset_index(drop=True)

    ctl1, ctl2 = st.columns([1, 1])
    with ctl1:
        if st.button("초기화(구로비 원본)", key="reset_to_gurobi_btn"):
            st.session_state.manual_moves = {}
            st.session_state.manual_move_history = []
            st.session_state.sim_selected_idx = None
            st.rerun()
    with ctl2:
        if st.button("이전(방금 작업 취소)", key="undo_last_move_btn"):
            if st.session_state.manual_move_history:
                item = st.session_state.manual_move_history.pop()
                idx_key = str(item["idx"])
                prev = item["prev"]
                if prev is None:
                    st.session_state.manual_moves.pop(idx_key, None)
                else:
                    st.session_state.manual_moves[idx_key] = prev
                st.rerun()
            else:
                st.info("되돌릴 작업이 없습니다.")

    left_col, right_col = st.columns([8, 4])
    with left_col:
        st.markdown("##### 현재 전체 시간표")
        # 블록 클릭으로 과목 선택
        render_clickable_calendar(calendar_src, sim_week_num, "overall_click")

    visible_week = calendar_src[calendar_src["주차"] == sim_week_num].copy().sort_values(["요일번호", "시작슬롯", "과목명"]).reset_index(drop=True)
    student_sets = build_exam_student_sets(exam_df_view, df_is)

    with right_col:
        st.markdown("#### 이동 설정")
        st.caption(f"저장된 변경: {len(st.session_state.manual_moves)}건")
        tab_t, tab_r = st.tabs(["시간이동", "강의실이동"])
        if visible_week.empty:
            with tab_t:
                st.info("이 조건에서 표시할 시험이 없습니다.")
            with tab_r:
                st.info("이 조건에서 표시할 시험이 없습니다.")
        else:
            idx_values = [int(x) for x in visible_week["시험인덱스"].tolist()]
            if st.session_state.sim_selected_idx not in idx_values:
                with tab_t:
                    st.info("왼쪽 캘린더에서 이동할 과목 블록을 먼저 클릭하세요.")
                    fallback_labels = visible_week.apply(
                        lambda r: f"[{int(r['시험인덱스'])}] {r['과목명']} | {r['요일']} {r['시작']}~{r['종료']}",
                        axis=1,
                    ).tolist()
                    fb_pick = st.selectbox("블록 클릭이 안되면 여기서 과목 선택", fallback_labels, key="fallback_pick_exam_t")
                    fb_idx = int(fb_pick.split("]")[0].replace("[", ""))
                    if st.button("이 과목 선택", key="fallback_select_btn_t"):
                        st.session_state.sim_selected_idx = fb_idx
                        st.rerun()
                with tab_r:
                    st.info("왼쪽 캘린더에서 이동할 과목 블록을 먼저 클릭하세요.")
                    fallback_labels = visible_week.apply(
                        lambda r: f"[{int(r['시험인덱스'])}] {r['과목명']} | {r['요일']} {r['시작']}~{r['종료']}",
                        axis=1,
                    ).tolist()
                    fb_pick = st.selectbox("블록 클릭이 안되면 여기서 과목 선택", fallback_labels, key="fallback_pick_exam_r")
                    fb_idx = int(fb_pick.split("]")[0].replace("[", ""))
                    if st.button("이 과목 선택", key="fallback_select_btn_r"):
                        st.session_state.sim_selected_idx = fb_idx
                        st.rerun()
            else:
                sel_idx = int(st.session_state.sim_selected_idx)
                sel_row = visible_week[visible_week["시험인덱스"] == sel_idx].iloc[0]
                st.markdown(
                    f"선택 과목: **{sel_row['과목명']}**  \n"
                    f"{sel_row['요일']} {sel_row['시작']}~{sel_row['종료']} / 강의실 {sel_row['강의실']}"
                )

                all_rows = []
                for room in ROOM_ORDER:
                    _h, rows = build_feasible_area_html(
                        exam_df=exam_df_view,
                        target_idx=sel_idx,
                        target_week=int(sim_week_num),
                        target_room=int(room),
                        student_sets=student_sets,
                        summary=summary,
                    )
                    all_rows.extend(rows)
                uniq = {}
                for r in all_rows:
                    key = (str(r["요일"]), str(r["시작"]), str(r["종료"]), int(r["강의실"]))
                    uniq[key] = r
                feasible_rows = list(uniq.values())
                st.caption(f"가능 후보 수: {len(feasible_rows)}")

                # 후보가 비어도 현재 배정안은 최소 1개 후보로 노출해 이동 UI가 비지 않게 한다.
                if not feasible_rows:
                    cur_day_no = int(sel_row["요일번호"])
                    cur_start_slot = int(sel_row["시작슬롯"])
                    cur_room = int(str(sel_row["강의실"]).split()[0])
                    cur_out = score_move_impact(
                        exam_df=exam_df_view,
                        target_idx=sel_idx,
                        new_week=int(sim_week_num),
                        new_day=int(cur_day_no),
                        new_start=int(cur_start_slot),
                        new_room=int(cur_room),
                        student_sets=student_sets,
                        summary=summary,
                    )
                    if cur_out.get("feasible", False):
                        dur_slots = int(float(sel_row.get("표시종료슬롯", sel_row["종료슬롯"])) - float(sel_row["시작슬롯"]))
                        feasible_rows.append(
                            {
                                "요일": str(sel_row["요일"]),
                                "시작": str(sel_row["시작"]),
                                "종료": slot_to_time(int(cur_start_slot + dur_slots)),
                                "강의실": int(cur_room),
                                "영향학생수": int(cur_out.get("affected_students", 0)),
                                "하루3개증가": int(cur_out.get("daily3_increase", 0)),
                                "하루4개증가": int(cur_out.get("daily4_increase", 0)),
                                "목적함수변화": float(cur_out.get("objective_delta", 0.0)),
                            }
                        )

                if not feasible_rows:
                    with tab_t:
                        st.warning("가능한 이동안이 없습니다.")
                    with tab_r:
                        st.warning("가능한 이동안이 없습니다.")
                else:
                    time_opts = sorted({f"{r['요일']} {r['시작']}~{r['종료']}" for r in feasible_rows})
                    room_opts = sorted({str(int(r["강의실"])) for r in feasible_rows}, key=lambda x: int(x))
                    cand = None
                    with tab_t:
                        tsel = st.selectbox("가능한 시간", time_opts, key="sim_time_filter")
                        time_filtered = [r for r in feasible_rows if f"{r['요일']} {r['시작']}~{r['종료']}" == tsel]
                        room_filtered_opts = sorted({str(int(r["강의실"])) for r in time_filtered}, key=lambda x: int(x))
                        rsel = st.selectbox("가능한 강의실", room_filtered_opts, key="sim_room_filter_by_time")
                        cands = [r for r in time_filtered if str(int(r["강의실"])) == rsel]
                        if cands:
                            cand = cands[0]
                    with tab_r:
                        rsel2 = st.selectbox("가능한 강의실", room_opts, key="sim_room_filter")
                        room_filtered = [r for r in feasible_rows if str(int(r["강의실"])) == rsel2]
                        time_filtered_opts = sorted({f"{r['요일']} {r['시작']}~{r['종료']}" for r in room_filtered})
                        tsel2 = st.selectbox("가능한 시간", time_filtered_opts, key="sim_time_filter_by_room")
                        cands2 = [r for r in room_filtered if f"{r['요일']} {r['시작']}~{r['종료']}" == tsel2]
                        if cands2:
                            cand = cands2[0]

                    if cand is None:
                        st.warning("선택한 조건의 이동안이 없습니다.")
                    else:
                        st.caption(f"선택 이동안: {cand['요일']} {cand['시작']}~{cand['종료']} / {cand['강의실']}호")
                        sim_day_no = DAY_KO_TO_NUM[str(cand["요일"])]
                        sim_start_slot = int((int(str(cand["시작"]).split(":")[0]) * 60 + int(str(cand["시작"]).split(":")[1]) - 540) / 30)
                        sim_room = int(cand["강의실"])

                        out = score_move_impact(
                            exam_df=exam_df_view,
                            target_idx=sel_idx,
                            new_week=int(sim_week_num),
                            new_day=int(sim_day_no),
                            new_start=int(sim_start_slot),
                            new_room=int(sim_room),
                            student_sets=student_sets,
                            summary=summary,
                        )
                        st.markdown("#### 영향 요약")
                        st.write(f"영향학생: {int(out.get('affected_students', 0))}명")
                        st.write(f"목적함수 변화: {float(out.get('objective_delta', 0.0)):+.4f}")
                        st.write(f"시간이동 변화: {int(out.get('time_move_delta', 0)):+d}")
                        st.write(f"강의실변경 변화: {int(out.get('room_change_delta', 0)):+d}")

                        if st.button("시간표 변경 저장", key="save_move_btn"):
                            prev_state = st.session_state.manual_moves.get(str(sel_idx))
                            st.session_state.manual_move_history.append({"idx": int(sel_idx), "prev": prev_state})
                            st.session_state.manual_moves[str(sel_idx)] = {
                                "week": int(sim_week_num),
                                "day": int(sim_day_no),
                                "start_slot": int(sim_start_slot),
                                "room": int(sim_room),
                            }
                            st.success("변경 저장 완료")
                            st.rerun()
        if st.session_state.manual_moves:
            rows = []
            for k, mv in st.session_state.manual_moves.items():
                rows.append(
                    {
                        "시험인덱스": int(k),
                        "주차": int(mv["week"]),
                        "요일": DAY_LABELS.get(int(mv["day"]), str(mv["day"])),
                        "시작": slot_to_time(int(mv["start_slot"])),
                        "강의실": int(mv["room"]),
                    }
                )
            st.dataframe(pd.DataFrame(rows).sort_values(["주차", "요일", "시작"]), use_container_width=True, hide_index=True)
elif menu == "변경사항 확인":
    st.subheader("기존 대비 변경사항 확인")

    df_ch = exam_df.copy().sort_values(["변경상태", "주차", "요일번호", "시작슬롯"]) 
    changed_only = st.checkbox("변경된 과목만 보기", value=False)
    if changed_only:
        df_ch = df_ch[df_ch["변경상태"] != "유지"]

    cols = [
        "과목명", "학년", "기존시간", "시작", "종료", "시험시간(분)", "요일", "주차", "기존강의실", "강의실",
        "시간변경여부", "강의실변경여부", "변경상태",
    ]

    view_ch = df_ch[cols].copy()
    st.markdown(
        dataframe_to_html_table(
            view_ch,
            highlight_cols=["시간변경여부", "강의실변경여부", "변경상태"],
        ),
        unsafe_allow_html=True,
    )

    st.download_button(
        "변경사항 CSV 다운로드",
        data=df_ch[cols].to_csv(index=False).encode("utf-8-sig"),
        file_name="change_report.csv",
        mime="text/csv",
    )

elif menu == "최적화 결과":
    st.subheader("구로비 최적화 결과")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("목적함수값", f"{float(summary.get('objective', 0)):.4f}")
    k2.metric("강의실 변경 합", int(summary.get("room_move_sum", 0)))
    k3.metric("시간 이동 합", int(summary.get("time_move_sum", 0)))
    k4.metric("하루 시험수 벌점 합", int(summary.get("daily_penalty_sum", 0)))
    st.info(
        f"현재 가중치: 강의실이동 {WEIGHT_ROOM_MOVE:.4f} / 시간이동 {WEIGHT_TIME_MOVE:.4f} / 하루시험수 {WEIGHT_DAILY:.4f} | "
        f"이동제약: D_max={D_MAX}, T_max={T_MAX}"
    )
    st.markdown("#### 목적함수 결과")
    st.dataframe(opt_summary_df, use_container_width=True, hide_index=True)

    st.markdown("#### 제약식 위반표")
    st.dataframe(verify_df, use_container_width=True, hide_index=True)

    st.markdown("#### 결정변수 결과")
    st.dataframe(decision_df, use_container_width=True, hide_index=True)
    st.download_button(
        "결정변수 결과 다운로드(CSV)",
        data=decision_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="optimized_decision_table.csv",
        mime="text/csv",
    )

    if report_dir is not None:
        pdf_path = report_dir / "결과_발표링크용.pdf"
        if pdf_path.exists():
            st.download_button(
                "발표용 PDF 다운로드",
                data=pdf_path.read_bytes(),
                file_name=pdf_path.name,
                mime="application/pdf",
            )





