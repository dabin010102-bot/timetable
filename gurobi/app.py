from __future__ import annotations

from datetime import datetime, timedelta
import json
import re
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
    .calendar-wrap table {width:100%; border-collapse:collapse; table-layout:fixed; font-size:13px;}
    .calendar-wrap th, .calendar-wrap td {border:1px solid #cfd8e3; padding:6px; vertical-align:top; height:52px;}
    .calendar-wrap th {background:#dbe7f9; text-align:center; font-size:14px; color:var(--text-main);}
    .calendar-wrap .time-col {background:#f3f7fc; width:90px; text-align:center; font-weight:700; color:var(--text-main);}
    .calendar-wrap .exam {background:var(--accent-bg); color:var(--accent-text);}
    .calendar-wrap .course {font-weight:800; margin-bottom:2px; font-size:13px; color:var(--accent-text);}
    .calendar-wrap .empty {background:#ffffff;}
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
COURSEEN_CANDIDATES = ["coursetable_en.csv", str(Path(r"C:\xpressmp\coursetable_en.csv"))]
ROOM_ORDER = [402, 479, 482, 483, 502, 583]
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


def find_existing_path(candidates: list[str]) -> Path | None:
    expanded: list[Path] = []
    for c in candidates:
        p = Path(c)
        if p.is_absolute():
            expanded.append(p)
        else:
            for d in DATA_DIR_CANDIDATES:
                expanded.append(d / c)

    for p in expanded:
        if p.exists():
            return p
    return None


def find_existing_dir(candidates: list[Path]) -> Path | None:
    for p in candidates:
        if p.exists() and p.is_dir():
            return p
    return None


@st.cache_data(show_spinner=False)
def load_result_payload() -> tuple[dict, Path]:
    p = find_existing_path(RESULT_JSON_CANDIDATES)
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
    if "course_name" not in df_courseen.columns or "grade" not in df_courseen.columns:
        return grade_map

    for _, row in df_courseen.iterrows():
        cname = str(row.get("course_name", "")).strip()
        if not cname:
            continue
        g = str(row.get("grade", "")).strip()
        if not g:
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


def add_change_columns_student(df_student: pd.DataFrame, df_is: pd.DataFrame, row_idx: int, orig_maps: dict[str, dict]) -> pd.DataFrame:
    out = df_student.copy()
    orig_base = orig_maps.get("base", {})
    orig_exact = orig_maps.get("exact", {})
    is_cols = [str(c) for c in df_is.columns]

    old_time = []
    old_room = []
    section_used = []
    time_status = []
    room_status = []
    final_status = []

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

    out["분반기준"] = section_used
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


def build_calendar_html(df_student: pd.DataFrame, target_week: int) -> str:
    time_rows = [slot_to_time(s) for s in range(0, 22)]
    table = {t: {d: "" for d in DAY_ORDER} for t in time_rows}
    df_w = df_student[df_student["주차"] == target_week].copy()

    for _, r in df_w.iterrows():
        day = str(r.get("요일", ""))
        if day not in DAY_ORDER:
            continue
        s0 = int(r.get("시작슬롯", 0))
        s1 = int(r.get("종료슬롯", s0))
        show_course = r.get("과목명", r.get("과목", ""))
        start_txt = str(r.get("시작", ""))
        end_txt = str(r.get("종료", ""))
        room_txt = str(r.get("강의실", "-"))
        dur_txt = str(r.get("시험시간(분)", ""))
        text_main = f"<div class='course'>{show_course}</div><div>{start_txt}~{end_txt}</div><div>{dur_txt}분 · 강의실 {room_txt}</div>"
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


def load_report_images() -> tuple[list[Path], Path | None]:
    report_dir = find_existing_dir(REPORT_DIR_CANDIDATES)
    if report_dir is None:
        return [], None
    images = sorted(
        [p for p in report_dir.glob("*.png") if p.is_file()],
        key=lambda p: p.name,
    )
    return images, report_dir


def build_optimization_summary_df(payload: dict) -> pd.DataFrame:
    summary = payload.get("summary", {})
    rows = [
        ["목적함수값", f"{float(summary.get('objective', 0)):.4f}"],
        ["강의실 변경 합", str(int(summary.get("room_move_sum", 0)))],
        ["시간 이동 합", str(int(summary.get("time_move_sum", 0)))],
        ["하루 시험수 벌점 합", str(int(summary.get("daily_penalty_sum", 0)))],
        ["학생 동시시험 위반", str(int(summary.get("overlap_violation", 0)))],
        ["같은과목 분반 동시시험 위반", str(int(summary.get("section_overlap_violation", 0)))],
        ["하루 4시험 위반", str(int(summary.get("daily4_count", 0)))],
        ["실행시간(초)", f"{float(summary.get('runtime_sec', 0)):.4f}"],
        ["Gurobi 시간(초)", f"{float(summary.get('gurobi_runtime_sec', 0)):.4f}"],
    ]
    return pd.DataFrame(rows, columns=["항목", "값"])


def build_verify_df(payload: dict) -> pd.DataFrame:
    rows = payload.get("verify_rows", [])
    if rows:
        return pd.DataFrame(rows, columns=["제약식", "위반건수"])
    return pd.DataFrame(
        [
            ["(5) 학생 동시시험", str(int(payload.get("summary", {}).get("overlap_violation", 0)))],
            ["(5-1) 같은과목 분반동시시험", str(int(payload.get("summary", {}).get("section_overlap_violation", 0)))],
            ["(7) 하루 4시험 금지", str(int(payload.get("summary", {}).get("daily4_count", 0)))],
        ],
        columns=["제약식", "위반건수"],
    )


def build_decision_df(payload: dict, exam_df: pd.DataFrame) -> pd.DataFrame:
    rows = payload.get("decision_rows", [])
    if rows:
        return pd.DataFrame(rows, columns=["과목", "선택된 시험시간", "선택된 강의실", "TimeMove_i", "RoomChange_i"])

    fallback = exam_df.copy().sort_values(["주차", "요일번호", "시작슬롯", "과목명"])
    return fallback[["과목명", "주차", "요일", "시작", "종료", "강의실", "TimeMove_i", "RoomChange_i"]].reset_index(drop=True)


def render_calendar_grid(df_student: pd.DataFrame, target_week: int):
    st.markdown(f"#### {target_week}주차 캘린더형 시험시간표")
    table_html = build_calendar_html(df_student, target_week)
    st.markdown(table_html, unsafe_allow_html=True)


def student_summary_cards(df_student: pd.DataFrame):
    if df_student.empty:
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("내 시험 개수", 0)
        c2.metric("첫 시험", "-")
        c3.metric("마지막 시험", "-")
        c4.metric("하루 최대 시험 수", 0)
        c5.metric("연속 시험 여부", "없음")
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

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("내 시험 개수", count_exam)
    c2.metric("첫 시험", first_exam.strftime("%m/%d %H:%M"))
    c3.metric("마지막 시험", last_exam.strftime("%m/%d %H:%M"))
    c4.metric("하루 최대 시험 수", max_per_day)
    c5.metric("연속 시험 여부", "있음" if consecutive else "없음")


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
opt_summary_df = build_optimization_summary_df(payload)
verify_df = build_verify_df(payload)
decision_df = build_decision_df(payload, exam_df)
report_images, report_dir = load_report_images()

summary = payload.get("summary", {})

# -------------------------------------------------
# UI
# -------------------------------------------------
st.title("INUTimetable")
st.caption("최적화 결과 조회 서비스 | 충돌 최소화 · 학생 부담 완화")

with st.sidebar:
    st.header("메뉴")
    menu = st.radio("페이지 선택", ["학번별 조회", "전체 시간표", "변경사항 확인", "최적화 결과"], index=0)
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
g4.metric("분반 동시시험", "없음" if int(summary.get("section_overlap_violation", 0)) == 0 else "있음")
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
            df_student = add_change_columns_student(df_student, df_is, row_idx, orig_maps)

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

            def _highlight_change(val):
                txt = str(val)
                if "변경" in txt and txt != "유지":
                    return "color:#c1121f; font-weight:700;"
                return "color:#0b1220;"

            # pandas 버전별 Styler API 차이(3.x: applymap 제거 가능)에 안전하게 대응
            try:
                styled_view = view_df.style.map(
                    _highlight_change,
                    subset=["시간변경여부", "강의실변경여부"],
                )
            except Exception:
                try:
                    styled_view = view_df.style.applymap(
                        _highlight_change,
                        subset=["시간변경여부", "강의실변경여부"],
                    )
                except Exception:
                    styled_view = view_df

            st.dataframe(
                styled_view,
                use_container_width=True,
                hide_index=True,
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
    st.subheader("전체 최적화 시험시간표")

    col1, col2, col3 = st.columns(3)
    course_options = ["전체"] + sorted(exam_df["과목명"].unique().tolist())
    grade_options = ["전체"] + sorted(exam_df["학년"].astype(str).unique().tolist())
    room_options = ["전체"] + [str(r) for r in ROOM_ORDER]

    with col1:
        sel_course = st.selectbox("과목명", course_options, index=0)
    with col2:
        sel_grade = st.selectbox("학년", grade_options, index=0)
    with col3:
        sel_room = st.selectbox("강의실", room_options, index=0)

    df_all = exam_df.copy()
    if sel_course != "전체":
        df_all = df_all[df_all["과목명"] == sel_course]
    if sel_grade != "전체":
        df_all = df_all[df_all["학년"].astype(str) == sel_grade]
    if sel_room != "전체":
        df_all = df_all[df_all["강의실목록"].apply(lambda x: int(sel_room) in set(x))]

    df_all = df_all.sort_values(["주차", "요일번호", "시작슬롯", "과목명"]).reset_index(drop=True)

    cols = ["과목명", "기준과목", "학년", "주차", "요일", "날짜", "시작", "종료", "시험시간(분)", "강의실", "변경상태"]
    st.dataframe(df_all[cols], use_container_width=True, hide_index=True)

    section_check = (
        df_all.groupby(["기준과목", "주차", "요일", "시작"])
        .size()
        .reset_index(name="동시분반수")
    )
    section_check = section_check[section_check["동시분반수"] >= 2]
    if section_check.empty:
        st.success("같은 과목 분반이 같은 시작시간에 동시에 배정된 경우가 없습니다.")
    else:
        st.error("같은 과목 분반 동시 배정이 있습니다.")
        st.dataframe(section_check, use_container_width=True, hide_index=True)

    st.download_button(
        "전체 시간표 CSV 다운로드",
        data=df_all[cols].to_csv(index=False).encode("utf-8-sig"),
        file_name="all_optimized_timetable.csv",
        mime="text/csv",
    )

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

    def highlight_change(row):
        if row["변경상태"] == "유지":
            return [""] * len(row)
        return ["background-color: #1f2937; color: #ffffff; font-weight: 700;"] * len(row)

    st.dataframe(df_ch[cols].style.apply(highlight_change, axis=1), use_container_width=True, hide_index=True)

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

    tab1, tab2, tab3, tab4 = st.tabs(["요약", "제약 검증", "결정변수 결과", "시각화"])

    with tab1:
        st.markdown("#### 목적함수 및 실행 요약")
        st.dataframe(opt_summary_df, use_container_width=True, hide_index=True)

    with tab2:
        st.markdown("#### 제약식 위반 점검")
        st.dataframe(verify_df, use_container_width=True, hide_index=True)

    with tab3:
        st.markdown("#### 선택된 시험시간 및 강의실")
        st.dataframe(decision_df, use_container_width=True, hide_index=True)
        st.download_button(
            "결정변수 결과 다운로드(CSV)",
            data=decision_df.to_csv(index=False).encode("utf-8-sig"),
            file_name="optimized_decision_table.csv",
            mime="text/csv",
        )

    with tab4:
        st.markdown("#### Matplotlib 결과 화면")
        if report_images:
            page_names = [p.name for p in report_images]
            selected_page = st.selectbox("결과 페이지 선택", page_names, index=0)
            selected_path = next((p for p in report_images if p.name == selected_page), None)
            if selected_path is not None:
                st.image(str(selected_path), use_container_width=True)
        else:
            st.info("시각화 PNG 파일이 아직 없습니다. gurobl.py 실행 후 결과_리포트 폴더가 생성되면 여기서 같이 볼 수 있습니다.")
        if report_dir is not None:
            pdf_path = report_dir / "결과_발표링크용.pdf"
            html_path = report_dir / "report.html"
            if pdf_path.exists():
                st.download_button(
                    "발표용 PDF 다운로드",
                    data=pdf_path.read_bytes(),
                    file_name=pdf_path.name,
                    mime="application/pdf",
                )
            if html_path.exists():
                st.caption(f"리포트 HTML: {html_path}")
