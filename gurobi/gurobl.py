"""
18과목 시험시간/강의실 동시배정 Gurobi 모델 
구조: 집합 -> 파라미터 -> 목적함수 -> 제약식 -> 결과
"""

from __future__ import annotations

import re
import time
import os
import csv
import json
import html
import base64
import webbrowser
import zipfile
import xml.etree.ElementTree as ET
from datetime import date, datetime
from pathlib import Path

import gurobipy as gp
from gurobipy import GRB


# ---------------------------------------------------------------------
# 파일/기본 설정
# ---------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
IS_PATH = BASE_DIR / "IS.xlsx"
OT_PRIMARY_PATH = BASE_DIR / "OT_all_sessions.xlsx"
OT_LOCAL_PATH = BASE_DIR / "OT_all_sessions (1).xlsx"
OT_FALLBACK_PATH = Path(r"C:\Users\taese\Documents\카카오톡 받은 파일\OT_all_sessions (1).xlsx")

ROOM_ORDER = [401, 478, 479, 482, 483, 502, 583]
ROOM_CAP = {401: 23, 478: 52, 479: 55, 482: 52, 483: 69, 502: 45, 583: 32}

WEIGHT_ROOM_MOVE = 0.1062
WEIGHT_TIME_MOVE = 0.6333
WEIGHT_DAILY = 0.2605

TARGET_WEEK = 8
USE_WEEK_LIMIT = 1

DUR_DEFAULT_SLOTS = 4
DAY_LABELS = {1: "월", 2: "화", 3: "수", 4: "목", 5: "금", 6: "토", 7: "일"}
WEEK_START_DATE = {
    7: date(2026, 4, 13),
    8: date(2026, 4, 20),
    9: date(2026, 4, 27),
}
WEEK_VALUES = [7, 8, 9]
OUTPUT_DIR = Path(__file__).resolve().parent
RESULT_CSV_PATH = OUTPUT_DIR / "결과_결정변수표.csv"
RESULT_TXT_PATH = OUTPUT_DIR / "결과_요약.txt"
RESULT_JSON_PATH = OUTPUT_DIR / "결과_서비스데이터.json"
RESULT_JSON_ASCII_PATH = OUTPUT_DIR / "result_service_data.json"
MODEL_HTML_PATH = OUTPUT_DIR / "수리모형_정리본.html"
REPORT_DIR = OUTPUT_DIR / "결과_리포트"
# 실행 제외 과목(정규화 키 기준)
EXCLUDED_COURSE_KEYS = {"syscapstone", "ergoexpeval"}


def env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or str(raw).strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


# 최대거리 제약 파라미터(고정값): D_max=0, T_max=4
# 결정변수가 아니라 파라미터이다.
D_MAX = 0
T_MAX = 4
# 리포트 생성/자동열기 제어
GENERATE_REPORT = env_int("GENERATE_REPORT", 1)
AUTO_OPEN_REPORT = env_int("AUTO_OPEN_REPORT", 1)


# ---------------------------------------------------------------------
# 유틸
# ---------------------------------------------------------------------
def normalize_name(text: str) -> str:
    if text is None:
        return ""
    x = str(text).strip().replace(" ", "")
    x = re.sub(r"[-_]\d+$", "", x)
    return x


def col_to_index(cell_ref: str) -> int:
    letters = "".join(ch for ch in cell_ref if ch.isalpha())
    idx = 0
    for ch in letters:
        idx = idx * 26 + (ord(ch.upper()) - 64)
    return idx - 1


def parse_int(value) -> int:
    text = str(value).strip() if value is not None else ""
    if text == "":
        return 0
    try:
        return int(float(text))
    except ValueError:
        return 0


def parse_day_value(raw) -> int:
    text = str(raw).strip() if raw is not None else ""
    if text == "":
        return 0
    if text.isdigit():
        v = int(text)
        return v if 1 <= v <= 7 else 0
    lower = text.lower()
    day_map = {
        "mon": 1, "monday": 1, "월": 1, "월요일": 1,
        "tue": 2, "tuesday": 2, "화": 2, "화요일": 2,
        "wed": 3, "wednesday": 3, "수": 3, "수요일": 3,
        "thu": 4, "thursday": 4, "목": 4, "목요일": 4,
        "fri": 5, "friday": 5, "금": 5, "금요일": 5,
        "sat": 6, "saturday": 6, "토": 6, "토요일": 6,
        "sun": 7, "sunday": 7, "일": 7, "일요일": 7,
    }
    return day_map.get(lower, 0)


def parse_week_value(row: dict[str, str]) -> int:
    for key in ("week", "주차"):
        if key in row and str(row.get(key, "")).strip() != "":
            w = parse_int(row.get(key))
            if w in (7, 8, 9):
                return w
    for key in ("date", "날짜"):
        raw = str(row.get(key, "")).strip()
        if not raw:
            continue
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d", "%m-%d"):
            try:
                dt = datetime.strptime(raw, fmt).date()
                if fmt in ("%m/%d", "%m-%d"):
                    dt = date(2026, dt.month, dt.day)
                if date(2026, 4, 13) <= dt <= date(2026, 4, 19):
                    return 7
                if date(2026, 4, 20) <= dt <= date(2026, 4, 26):
                    return 8
                if date(2026, 4, 27) <= dt <= date(2026, 5, 3):
                    return 9
            except ValueError:
                continue
    return TARGET_WEEK


def parse_hhmm_to_min(raw: str) -> int | None:
    text = raw.strip()
    m = re.match(r"^(\d{1,2}):(\d{2})$", text)
    if not m:
        return None
    return int(m.group(1)) * 60 + int(m.group(2))


def minute_to_slot(minute: int) -> int:
    return (minute - 540) // 30


def minute_duration_to_slots(duration_min: int) -> int:
    return (duration_min + 29) // 30


def parse_start_duration_slots(row: dict[str, str]) -> tuple[int, int]:
    start_min = None
    duration_min = None

    if str(row.get("start_min", "")).strip():
        start_min = parse_int(row.get("start_min"))
    if str(row.get("duration_min", "")).strip():
        duration_min = parse_int(row.get("duration_min"))

    start_time = str(row.get("start_time", "")).strip()
    end_time = str(row.get("end_time", "")).strip()
    if start_min is None and start_time:
        start_min = parse_hhmm_to_min(start_time)
    if duration_min is None and start_time and end_time:
        s = parse_hhmm_to_min(start_time)
        e = parse_hhmm_to_min(end_time)
        if s is not None and e is not None and e > s:
            duration_min = e - s

    start_raw = str(row.get("start", "")).strip()
    duration_raw = str(row.get("duration", "")).strip()
    if start_min is None:
        if ":" in start_raw:
            start_min = parse_hhmm_to_min(start_raw)
        elif start_raw and parse_int(start_raw) >= 540:
            start_min = parse_int(start_raw)
    if duration_min is None:
        if ":" in duration_raw:
            parsed = parse_hhmm_to_min(duration_raw)
            if parsed is not None:
                duration_min = parsed
        elif duration_raw and parse_int(duration_raw) >= 30:
            duration_min = parse_int(duration_raw)

    examtime_raw = str(row.get("examtime", "")).strip()
    if examtime_raw:
        m = re.search(r"\d+", examtime_raw)
        if m:
            duration_min = int(m.group(0))

    if start_min is not None and duration_min is not None:
        return minute_to_slot(start_min), max(1, minute_duration_to_slots(duration_min))

    if start_min is None and duration_min is not None and start_raw and ":" not in start_raw:
        return parse_int(start_raw), max(1, minute_duration_to_slots(duration_min))

    start_slot = parse_int(row.get("start", 0))
    dur_slot = max(1, parse_int(row.get("duration", 0)))
    return start_slot, dur_slot


def slot_to_time(slot: int) -> str:
    total_minutes = 9 * 60 + slot * 30
    return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"


def extract_student_id(row: dict[str, str], fallback_idx: int) -> str:
    for key in ("학번", "student_id", "studentid", "id", "ID", "sid"):
        if key in row:
            val = str(row.get(key, "")).strip()
            if val:
                return val
    return f"학생_{fallback_idx + 1}"


def save_result_files(
    inst: dict,
    assignment: dict[int, dict[str, int | list[int]]],
    time_move_map: dict[int, int],
    room_change_map: dict[int, int],
    objective: float,
    room_move_sum: float,
    time_move_sum: float,
    daily_penalty_sum: float,
    overlap_violation: int,
    consecutive_violation: int,
    daily4_count: int,
    runtime_sec: float,
    gurobi_runtime_sec: float,
) -> None:
    with RESULT_TXT_PATH.open("w", encoding="utf-8") as f:
        f.write("===== 18과목 Exact 결과 =====\n")
        f.write(f"Objective = {objective:.4f}\n")
        f.write(f"RoomMoveSum = {room_move_sum:.0f}\n")
        f.write(f"TimeMoveSum = {time_move_sum:.0f}\n")
        f.write(f"DailyPenaltySum = {daily_penalty_sum:.0f}\n")
        f.write(f"동시시험 위반건수 = {overlap_violation}\n")
        f.write(f"연속시험 위반건수 = {consecutive_violation}\n")
        f.write(f"하루 4시험 건수 = {daily4_count}\n")
        f.write(f"RuntimeSec = {runtime_sec:.6f}\n")
        f.write(f"GurobiRuntimeSec = {gurobi_runtime_sec:.6f}\n")

    with RESULT_CSV_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["과목", "주차", "요일", "시작", "종료", "x_iwdt", "z_iwdtr(강의실)", "TimeMove_i", "RoomChange_i"])
        for i in range(inst["n_exams"]):
            info = assignment[i]
            st = int(info["slot_val"])
            et = st + int(inst["exams"][i]["dur_slots"])
            room_label = " ".join(str(r) for r in info["rooms"])
            writer.writerow([
                inst["exams"][i]["name"],
                info["week"],
                DAY_LABELS.get(int(info["dow"]), str(info["dow"])),
                slot_to_time(st),
                slot_to_time(et),
                1,
                room_label,
                time_move_map[i],
                room_change_map[i],
            ])


def write_model_summary_html() -> None:
    template = r"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <title>???? ???</title>
  <script>
    window.MathJax = {
      tex: { inlineMath: [['$', '$'], ['\(', '\)']], displayMath: [['$$','$$']] },
      svg: { fontCache: 'global' }
    };
  </script>
  <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
  <style>
    body { font-family: 'Malgun Gothic', 'NanumGothic', sans-serif; margin: 24px; line-height: 1.7; color: #1f2d3d; }
    h1, h2 { margin: 0 0 8px 0; }
    h1 { font-size: 26px; }
    h2 { font-size: 20px; margin-top: 24px; }
    .box { border: 1px solid #d8e0ea; border-radius: 10px; padding: 14px 16px; margin-top: 10px; background: #fafcff; }
    .eq { background: #f3f6fb; border-radius: 6px; padding: 8px 10px; margin: 8px 0; }
    .desc { color:#30455a; font-size:14px; }
    table { border-collapse: collapse; width: 100%; margin-top: 8px; }
    th, td { border: 1px solid #d8e0ea; padding: 8px; font-size: 14px; }
    th { background: #eef3f9; text-align: left; }
  </style>
</head>
<body>
  <h1>????? ???? ???</h1>
  <div class="box">
    <div>???: ?????=__W_ROOM__, ????=__W_TIME__, ??????=__W_DAILY__</div>
    <div>???? ????: $D_{max}=__D_MAX__$, $T_{max}=__T_MAX__$</div>
  </div>

  <h2>1. ??</h2>
  <div class="box">
    <div class="eq">$$I=\{\text{?? ??}\},\;J=\{\text{??}\},\;W=\{7,8,9\},\;D=\{1,2,3,4,5\},\;T=\{\text{????}\},\;\tau=\{\text{???}\},\;R=\{\text{???}\}$$</div>
  </div>

  <h2>2. ????</h2>
  <div class="box">
    <div class="eq">$$need\_room_i,\;enr_i,\;cap_r,\;enroll_{si},\;OCC_{wdr\tau},\;dur_i$$</div>
    <div class="eq">$$origtime_i=\{(w_0,d_0,t_0)\}$$</div>
  </div>

  <h2>3. ????</h2>
  <div class="box">
    <div class="eq">$$x_{iwdt}\in\{0,1\},\;z_{iwdtr}\in\{0,1\},\;y_{swd}\in\mathbb{Z}_+,\;P_{swd}\ge 0$$</div>
    <div class="eq">$$RoomChange_i\in\{0,1\},\;TimeMove_i\in\{0,1\}$$</div>
  </div>

  <h2>4. ????</h2>
  <div class="box">
    <div class="eq">$$\min\;\alpha\sum_{i\in I}RoomChange_i+\beta\sum_{i\in I}TimeMove_i+\gamma\sum_{s\in J}\sum_{w\in W}\sum_{d\in D}P_{swd}$$</div>
    <div>$$\alpha=__W_ROOM__,\;\beta=__W_TIME__,\;\gamma=__W_DAILY__$$</div>
  </div>

  <h2>5. ???</h2>
  <div class="box">
    <div class="eq">(1) $$\sum_{w\in W}\sum_{d\in D}\sum_{t\in T}x_{iwdt}=1\quad\forall i\in I$$</div>
    <div class="desc">??: ? ??? ??? 1?? ?? ??</div>

    <div class="eq">(2) $$\sum_{r\in R}z_{iwdtr}=need\_room_i\,x_{iwdt}\quad\forall i,w,d,t$$</div>
    <div class="desc">??: ??? ??? ?? ??? ??? ? ??</div>

    <div class="eq">(3) $$\sum_{r\in R}cap_r z_{iwdtr}\ge enr_i x_{iwdt}\quad\forall i,w,d,t$$</div>
    <div class="desc">??: ?? ??? ? ????? ???? ??</div>

    <div class="eq">(4) $$\sum_{i\in I}\sum_{t\in T:t\le\tau<t+dur_i} z_{iwdtr}\le 1-OCC_{wdr\tau}\quad\forall w,d,r,\tau$$</div>
    <div class="desc">??: ?? ???(?)?? ??? ??/???? ??</div>

    <div class="eq">(5) $$\sum_{i\in I}\sum_{t\in T:t\le\tau<t+dur_i} enroll_{si}x_{iwdt}\le 1\quad\forall s,w,d,\tau$$</div>
    <div class="desc">??: ?? ???? ??</div>

    <div class="eq">(6) $$y_{swd}=\sum_{i\in I}\sum_{t\in T}enroll_{si}x_{iwdt}\quad\forall s,w,d$$</div>
    <div class="desc">??: ??? ?? ?? ?? ??</div>

    <div class="eq">(6-1) $$y_{swd}\le3\quad\forall s,w,d$$</div>
    <div class="desc">??: ?? 4? ?? ??</div>

    <div class="eq">(7) $$P_{swd}=(y_{swd}-1)^2$$</div>
    <div class="desc">??: ?? ??? ??</div>

    <div class="eq">(9) ???? ?? ??</div>

    <div class="eq">(11) $$\min_{(w_0,d_0,t_0)\in origtime_i}\left|(w-w_0)\cdot5+(d-d_0)\right|\le D_{max}$$ ??? ? $$x_{iwdt}=0$$</div>
    <div class="eq">(12) $$\min_{(w_0,d_0,t_0)\in origtime_i}\left|t-t_0\right|\le T_{max}$$ ??? ? $$x_{iwdt}=0$$</div>
    <div class="desc">??: ?? ???? ??</div>
  </div>

  <h2>6. ?????? ?? ??(?????)</h2>
  <div class="box">
    <div class="eq">??: $$(D_{max},T_{max})=(0,2),(0,3),(0,4)$$</div>
    <div class="eq">??: $$(0,2)\rightarrow infeasible,\;(0,3)\rightarrow infeasible,\;(0,4)\rightarrow feasible$$</div>
    <div>??? ?? ??? feasible? ??? ?? $D_{max}=0, T_{max}=4$? ??.</div>
  </div>

  <h2>7. ????-?? 1:1 ??</h2>
  <div class="box">
    <table>
      <thead><tr><th>?? ??</th><th>?? ??</th></tr></thead>
      <tbody>
        <tr><td>$x_{iwdt}$</td><td>`x_iwdt`</td></tr>
        <tr><td>$z_{iwdtr}$</td><td>`z_iwdtr`</td></tr>
        <tr><td>$y_{swd}$</td><td>`y_swd`</td></tr>
        <tr><td>$P_{swd}$</td><td>`P_swd`</td></tr>
        <tr><td>$RoomChange_i$</td><td>`RoomChange_i`</td></tr>
        <tr><td>$TimeMove_i$</td><td>`TimeMove_i`</td></tr>
        <tr><td>$OCC_{wdr\tau}$</td><td>`OCC_wdrtau`</td></tr>
        <tr><td>$enroll_{si}$</td><td>`inst["enroll"][s][i]`</td></tr>
      </tbody>
    </table>
  </div>
</body>
</html>"""
    html_text = (
        template
        .replace("__W_ROOM__", str(WEIGHT_ROOM_MOVE))
        .replace("__W_TIME__", str(WEIGHT_TIME_MOVE))
        .replace("__W_DAILY__", str(WEIGHT_DAILY))
        .replace("__D_MAX__", str(D_MAX))
        .replace("__T_MAX__", str(T_MAX))
    )
    MODEL_HTML_PATH.write_text(html_text, encoding="utf-8")


def show_result_plots(
    inst: dict,
    assignment: dict[int, dict[str, int | list[int]]],
    objective: float,
    room_move: float,
    time_move: float,
    daily_penalty: float,
    verify_rows: list[list[str]],
    decision_rows: list[list[str]],
) -> None:
    """
    결과 페이지를 파일로 생성한다.
    - page_00_summary.png: 요약
    - page_room_XXXX.png: 강의실별 페이지
    - report.html: 이전/다음 버튼 페이지
    """
    try:
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle
        from matplotlib.backends.backend_pdf import PdfPages
    except Exception:
        print("시각화 생략: matplotlib 환경 오류(NumPy/Matplotlib 버전 충돌)")
        return

    # 한글 폰트 설정(현재 환경에 있는 폰트만 적용)
    try:
        from matplotlib import font_manager
        installed = {f.name for f in font_manager.fontManager.ttflist}
        pref = ["Malgun Gothic", "NanumGothic", "맑은 고딕", "DejaVu Sans"]
        picked = [f for f in pref if f in installed]
        if not picked:
            picked = ["DejaVu Sans"]
        plt.rcParams["font.family"] = picked
        plt.rcParams["axes.unicode_minus"] = False
    except Exception:
        pass

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    page_files: list[tuple[str, str]] = []
    pdf_path = REPORT_DIR / "결과_발표링크용.pdf"
    pdf = PdfPages(str(pdf_path))

    # 0) 요약 페이지: 결정변수 정의 + 목적함수 값 + 제약 위반 점검
    fig0, ax0 = plt.subplots(figsize=(12, 7))
    ax0.axis("off")
    ax0.set_title("수리모형 실행 결과 요약", fontsize=16, pad=14)

    obj_rows = [
        ["가중치(강의실변경)", f"{WEIGHT_ROOM_MOVE}"],
        ["가중치(시간이동)", f"{WEIGHT_TIME_MOVE}"],
        ["가중치(하루벌점)", f"{WEIGHT_DAILY}"],
        ["강의실변경합", f"{room_move:.0f}"],
        ["시간이동합", f"{time_move:.0f}"],
        ["하루벌점합", f"{daily_penalty:.0f}"],
        ["계산 목적값", f"{WEIGHT_ROOM_MOVE * room_move + WEIGHT_TIME_MOVE * time_move + WEIGHT_DAILY * daily_penalty:.4f}"],
        ["모델 목적값", f"{objective:.4f}"],
    ]

    ax0.text(0.02, 0.92, "결정변수 선택 결과(요약)", fontsize=12, fontweight="bold", va="top")
    tbl_dec = ax0.table(
        cellText=decision_rows,
        colLabels=["과목", "선택 x_iwdt", "선택 z_iwdtr", "TimeMove_i", "RoomChange_i"],
        colLoc="left",
        cellLoc="left",
        bbox=[0.02, 0.48, 0.96, 0.40],
    )
    tbl_dec.auto_set_font_size(False)
    tbl_dec.set_fontsize(9.2)

    ax0.text(0.02, 0.44, "목적함수 결과", fontsize=12, fontweight="bold", va="top")
    tbl_obj = ax0.table(cellText=obj_rows, colLabels=["항목", "값"], colLoc="left", cellLoc="left", bbox=[0.02, 0.20, 0.45, 0.20])
    tbl_obj.auto_set_font_size(False)
    tbl_obj.set_fontsize(10)

    ax0.text(0.53, 0.44, "제약식 위반 검증", fontsize=12, fontweight="bold", va="top")
    tbl_chk = ax0.table(cellText=verify_rows, colLabels=["검증 항목", "위반건수"], colLoc="left", cellLoc="left", bbox=[0.53, 0.20, 0.45, 0.20])
    tbl_chk.auto_set_font_size(False)
    tbl_chk.set_fontsize(9.3)

    ax0.text(0.02, 0.12, "판정: 위반 건수가 모두 0이면 제약식 검증 통과", fontsize=10)
    plt.tight_layout()
    summary_png = REPORT_DIR / "page_00_summary.png"
    fig0.savefig(summary_png, dpi=160, bbox_inches="tight")
    pdf.savefig(fig0)
    plt.close(fig0)
    page_files.append(("요약", summary_png.name))

    # records: (week, dow, room, start_slot, dur, course)
    records: list[tuple[int, int, int, int, int, str]] = []
    for i in range(inst["n_exams"]):
        info = assignment[i]
        week = int(info["week"])
        dow = int(info["dow"])
        start_slot = int(info["slot_idx"])
        dur = int(inst["exams"][i]["dur_slots"])
        course = str(inst["exams"][i]["name"])
        for room in info["rooms"]:
            records.append((week, dow, int(room), start_slot, dur, course))

    rooms = sorted(set(inst["room_no"]))
    weeks_fixed = [7, 8, 9]
    for room in rooms:
        room_records = [rec for rec in records if rec[2] == room]
        fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(10.5, 9), squeeze=False)
        fig.suptitle(f"강의실 {room} 시험시간표", fontsize=15, y=0.995)
        for ridx, week in enumerate(weeks_fixed):
            ax = axes[ridx][0]
            # 기본 축
            ax.set_xlim(0, 5)
            ax.set_ylim(22, 0)
            ax.set_xticks([0.5, 1.5, 2.5, 3.5, 4.5])
            ax.set_xticklabels(["월", "화", "수", "목", "금"], fontsize=8)
            ax.set_yticks(list(range(0, 22)))
            ax.set_yticklabels([slot_to_time(s) for s in range(0, 22)], fontsize=6)

            # 격자
            for x in range(6):
                ax.axvline(x, color="#aab2bd", linewidth=0.7, zorder=0)
            for y in range(23):
                ax.axhline(y, color="#d2d8df", linewidth=0.55, zorder=0)

            # 주차 헤더 색상
            week_colors = {7: "#f7e7be", 8: "#d8ecf7", 9: "#d9f2d8"}
            ax.add_patch(Rectangle((0, -0.9), 5, 0.9, facecolor=week_colors.get(week, "#efefef"), edgecolor="#c8c8c8", linewidth=0.7, clip_on=False))

            # ROOM 라벨은 각 ROOM 첫 블록 위에만
            if week == 7:
                ax.text(0.0, -1.35, f"강의실 {room}", fontsize=9, fontweight="bold", ha="left", va="bottom", clip_on=False)

            week_start = WEEK_START_DATE.get(week)
            if week_start:
                week_end = week_start.fromordinal(week_start.toordinal() + 6)
                week_label = f"{week}주차  {week_start.month}/{week_start.day} ~ {week_end.month}/{week_end.day}"
            else:
                week_label = f"{week}주차"
            ax.text(0.05, -0.25, week_label, fontsize=7, ha="left", va="center", clip_on=False)

            # 시험 블록
            wk_records = [r for r in room_records if r[0] == week]
            for (_, dow, _, start_slot, dur, course) in wk_records:
                if dow < 1 or dow > 5:
                    continue
                x0 = (dow - 1) + 0.02
                y0 = start_slot
                rect = Rectangle((x0, y0), 0.96, dur, facecolor="#dbe8f8", edgecolor="#7f9db9", linewidth=0.8)
                ax.add_patch(rect)
                ax.text(x0 + 0.48, y0 + dur / 2, course, ha="center", va="center", fontsize=5.3, color="#2a4c68")

            # 테두리
            for spine in ax.spines.values():
                spine.set_color("#9aa5b1")
                spine.set_linewidth(0.8)

        fig.tight_layout(rect=[0, 0, 1, 0.985], h_pad=1.2)
        room_png = REPORT_DIR / f"page_room_{room}.png"
        fig.savefig(room_png, dpi=160, bbox_inches="tight")
        pdf.savefig(fig)
        plt.close(fig)
        page_files.append((f"강의실 {room}", room_png.name))

    # HTML 리포트(버튼으로 페이지 이동) - 이미지 내장(base64)로 단일 파일 전달 가능
    sections = []
    for idx, (title, fname) in enumerate(page_files):
        disp = "block" if idx == 0 else "none"
        img_path = REPORT_DIR / fname
        img_b64 = base64.b64encode(img_path.read_bytes()).decode("ascii")
        sections.append(
            f"""
            <section class="page" id="page-{idx}" style="display:{disp}">
              <h2>{html.escape(title)} ({idx+1}/{len(page_files)})</h2>
              <img src="data:image/png;base64,{img_b64}" alt="{html.escape(title)}" />
            </section>
            """
        )
    report_html = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <title>INUTimetable</title>
  <style>
    body {{ font-family: 'Malgun Gothic', 'NanumGothic', sans-serif; margin: 20px; background:#f6f8fb; }}
    .wrap {{ max-width: 1200px; margin: 0 auto; background:#fff; border:1px solid #dde3ea; border-radius:12px; padding:16px; }}
    h1 {{ margin: 0 0 10px 0; }}
    .toolbar {{ display:flex; gap:8px; margin: 8px 0 14px 0; }}
    button {{ border:1px solid #c8d0da; background:#f3f6fb; border-radius:8px; padding:8px 12px; cursor:pointer; }}
    button:hover {{ background:#eaf0f8; }}
    .page img {{ width:100%; height:auto; border:1px solid #d4dbe4; border-radius:8px; }}
    .meta {{ color:#45566c; font-size: 13px; margin-bottom:8px; }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>INUTimetable</h1>
    <div class="meta">생성 파일: {html.escape(str(REPORT_DIR))}</div>
    <div class="toolbar">
      <button onclick="prevPage()">◀ 이전 페이지</button>
      <button onclick="nextPage()">다음 페이지 ▶</button>
    </div>
    {''.join(sections)}
  </div>
  <script>
    let idx = 0;
    const total = {len(page_files)};
    function show(i) {{
      for (let k=0; k<total; k++) {{
        const el = document.getElementById('page-'+k);
        if (el) el.style.display = (k===i) ? 'block' : 'none';
      }}
      idx = i;
    }}
    function nextPage() {{ show((idx + 1) % total); }}
    function prevPage() {{ show((idx - 1 + total) % total); }}
  </script>
</body>
</html>"""
    (REPORT_DIR / "report.html").write_text(report_html, encoding="utf-8")
    pdf.close()
    report_html_path = REPORT_DIR / "report.html"
    print(f"리포트 저장: {report_html_path}")
    print(f"PDF 저장: {pdf_path}")
    # 실행 직후 결과 화면 자동 열기
    if AUTO_OPEN_REPORT == 1:
        try:
            if os.name == "nt":
                os.startfile(str(report_html_path))  # type: ignore[attr-defined]
            else:
                webbrowser.open_new_tab(report_html_path.as_uri())
        except Exception:
            try:
                webbrowser.open_new_tab(report_html_path.as_uri())
            except Exception:
                pass


def read_xlsx_rows(path: Path) -> list[dict[str, str]]:
    ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(path) as zf:
        shared = []
        if "xl/sharedStrings.xml" in zf.namelist():
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in root.findall("main:si", ns):
                shared.append("".join(t.text or "" for t in si.findall(".//main:t", ns)))

        workbook = ET.fromstring(zf.read("xl/workbook.xml"))
        first_sheet = workbook.find("main:sheets/main:sheet", ns)
        if first_sheet is None:
            return []

        rel_id = first_sheet.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
        rel_root = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))

        target = None
        for rel in rel_root.findall("{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"):
            if rel.attrib.get("Id") == rel_id:
                target = rel.attrib.get("Target")
                break
        if not target:
            return []

        target_norm = target.replace("\\", "/")
        if target_norm.startswith("/"):
            target_norm = target_norm.lstrip("/")
        if not target_norm.startswith("xl/"):
            target_norm = "xl/" + target_norm

        sheet_root = ET.fromstring(zf.read(target_norm))
        raw_rows = sheet_root.findall("main:sheetData/main:row", ns)
        if not raw_rows:
            return []

        table = []
        for row in raw_rows:
            values = {}
            for c in row.findall("main:c", ns):
                idx = col_to_index(c.attrib.get("r", "A1"))
                cell_type = c.attrib.get("t")
                value = ""
                if cell_type == "s":
                    v = c.find("main:v", ns)
                    value = shared[int(v.text)] if v is not None and v.text is not None else ""
                elif cell_type == "inlineStr":
                    t = c.find("main:is/main:t", ns)
                    value = t.text if t is not None and t.text is not None else ""
                else:
                    v = c.find("main:v", ns)
                    value = v.text if v is not None and v.text is not None else ""
                values[idx] = value
            table.append(values)

        header_len = max(table[0].keys()) + 1 if table[0] else 0
        headers = [table[0].get(i, "") for i in range(header_len)]
        rows = []
        for row_vals in table[1:]:
            row = {}
            for i, h in enumerate(headers):
                if h:
                    row[h] = row_vals.get(i, "")
            rows.append(row)
        return rows


def resolve_ot_path() -> Path:
    if OT_PRIMARY_PATH.exists():
        return OT_PRIMARY_PATH
    if OT_LOCAL_PATH.exists():
        return OT_LOCAL_PATH
    if OT_FALLBACK_PATH.exists():
        return OT_FALLBACK_PATH
    raise FileNotFoundError(f"OT_all_sessions file not found: {OT_PRIMARY_PATH}")


# ---------------------------------------------------------------------
# 데이터 로드 -> 인스턴스 생성
# ---------------------------------------------------------------------
def parse_ot_metadata() -> dict[str, dict]:
    rows = read_xlsx_rows(resolve_ot_path())
    meta: dict[str, dict] = {}

    for row in rows:
        raw_course = str(row.get("course", "")).strip()
        course_key = normalize_name(raw_course)
        if not course_key:
            continue

        day = parse_day_value(row.get("day", 0))
        week = parse_week_value(row)
        start, duration = parse_start_duration_slots(row)
        room = parse_int(row.get("room", 0))

        if course_key not in meta:
            meta[course_key] = {
                "CourseName": raw_course if raw_course else course_key,
                "OrigSlots": set(),
                "OrigRooms": set(),
                "Sessions": [],
            }

        if day > 0 and week in WEEK_VALUES:
            meta[course_key]["OrigSlots"].add((week, day, start))
        if room in ROOM_CAP:
            meta[course_key]["OrigRooms"].add(room)

        meta[course_key]["Sessions"].append(
            {
                "week": week,
                "day": day,
                "start": start,
                "duration": max(1, duration),
                "room": room,
            }
        )

    return meta


def resolve_available_exam_columns(headers: list[str], course_keys: list[str]) -> dict[str, list[str]]:
    exam_cols = {}
    for exam in course_keys:
        matched = []
        for col in headers:
            ncol = normalize_name(col)
            if ncol == exam or ncol.startswith(exam) or exam.startswith(ncol):
                matched.append(col)
        if matched:
            exam_cols[exam] = matched
    return exam_cols


def compute_course_stats(rows: list[dict[str, str]], exam_cols: dict[str, list[str]], ot_meta: dict[str, dict]) -> dict[str, dict]:
    stats = {
        course: {
            "enrollment": 0,
            "conflict_score": 0,
            "need_room": 1,
            "orig_slot_count": len(ot_meta[course]["OrigSlots"]),
        }
        for course in exam_cols
    }

    for row in rows:
        taken = []
        for course, cols in exam_cols.items():
            if any(parse_int(row.get(col, 0)) > 0 for col in cols):
                stats[course]["enrollment"] += 1
                taken.append(course)
        for course in taken:
            stats[course]["conflict_score"] += len(taken) - 1

    room_caps_desc = sorted(ROOM_CAP.values(), reverse=True)

    def min_rooms_needed(enrollment: int) -> int:
        if enrollment <= 0:
            return 1
        total = 0
        for idx, cap in enumerate(room_caps_desc, start=1):
            total += cap
            if total >= enrollment:
                return idx
        return len(room_caps_desc)

    for course in stats:
        stats[course]["need_room"] = min_rooms_needed(stats[course]["enrollment"])

    return stats


def build_occ_all(
    day_keys: list[tuple[int, int]],
    time_points: list[int],
    rooms: list[int],
    ot_meta: dict[str, dict],
    selected_courses: list[str],
) -> dict[tuple[int, int, int], int]:
    occ = {
        (d_idx, r_idx, tp_idx): 0
        for d_idx in range(len(day_keys))
        for r_idx in range(len(rooms))
        for tp_idx in range(len(time_points))
    }
    day_key_to_idx = {key: idx for idx, key in enumerate(day_keys)}
    allowed = set(selected_courses)

    for course_name, meta in ot_meta.items():
        if course_name not in allowed:
            continue
        for sess in meta["Sessions"]:
            week = sess.get("week")
            day = sess["day"]
            start = sess["start"]
            duration = sess["duration"]
            room = sess["room"]
            if week not in WEEK_VALUES:
                continue
            if room not in rooms:
                continue
            day_key = (week, day)
            if day_key not in day_key_to_idx:
                continue
            d_idx = day_key_to_idx[day_key]
            r_idx = rooms.index(room)
            for tp_idx, tp in enumerate(time_points):
                if start <= tp < start + duration:
                    occ[d_idx, r_idx, tp_idx] = 1
    return occ


def active_slot_indices(start_slot_value: int, time_points: list[int], dur_slots: int) -> list[int]:
    return [idx for idx, tp in enumerate(time_points) if start_slot_value <= tp < start_slot_value + dur_slots]


def build_consecutive_records(inst: dict) -> list[tuple[int, int, int, int, int, int]]:
    records = []
    slot_vals = inst["slot_vals"]

    for s in range(inst["n_stud"]):
        taken = [i for i in range(inst["n_exams"]) if inst["enroll"][s][i] == 1]
        for d in range(inst["n_days"]):
            for i, j in ((i, j) for i in taken for j in taken if i < j):
                for w in range(inst["n_slots"]):
                    for u in range(inst["n_slots"]):
                        start_i = slot_vals[w]
                        start_j = slot_vals[u]
                        dur_i = inst["exams"][i]["dur_slots"]
                        dur_j = inst["exams"][j]["dur_slots"]
                        if start_i + dur_i == start_j:
                            records.append((s, d, i, w, j, u))
                        elif start_j + dur_j == start_i:
                            records.append((s, d, j, u, i, w))

    return list(dict.fromkeys(records))


def build_instance_18() -> dict:
    if not IS_PATH.exists():
        raise FileNotFoundError(f"IS.xlsx not found: {IS_PATH}")

    ot_meta = parse_ot_metadata()
    rows = read_xlsx_rows(IS_PATH)
    if not rows:
        raise RuntimeError("IS.xlsx에서 학생 데이터를 읽지 못했습니다.")
    headers = list(rows[0].keys())

    available = sorted(
        course for course in ot_meta.keys()
        if normalize_name(course).lower() not in EXCLUDED_COURSE_KEYS
    )
    exam_cols_all = resolve_available_exam_columns(headers, available)
    available = [course for course in available if course in exam_cols_all]

    stats = compute_course_stats(rows, {c: exam_cols_all[c] for c in available}, ot_meta)
    selected = [course for course in available if stats[course]["enrollment"] > 0]

    if not selected:
        raise RuntimeError("선택 가능한 과목이 없습니다. 데이터와 제외과목 설정을 확인하세요.")

    exam_cols = {course: exam_cols_all[course] for course in selected}

    picked = [
        row
        for row in rows
        if any(any(parse_int(row.get(col, 0)) > 0 for col in exam_cols[exam]) for exam in selected)
    ]

    start_vals = list(range(0, 19))
    time_points = list(range(0, 22))
    day_keys = [(w, d) for w in WEEK_VALUES for d in range(1, 6)]
    room_vals = ROOM_ORDER[:]

    occ_all = build_occ_all(day_keys, time_points, room_vals, ot_meta, selected)
    day_key_to_idx = {key: idx for idx, key in enumerate(day_keys)}

    exams = []
    for name in selected:
        orig_slots_raw = sorted(ot_meta[name]["OrigSlots"])
        orig_slots = []
        orig_weeks = sorted(set(week for week, _, _ in orig_slots_raw))
        for week, day, start in orig_slots_raw:
            key = (week, day)
            if key in day_key_to_idx:
                orig_slots.append((day_key_to_idx[key] + 1, start))

        if not orig_slots:
            fallback_slots = sorted(
                set(
                    (day_key_to_idx[(sess["week"], sess["day"])] + 1, sess["start"])
                    for sess in ot_meta[name]["Sessions"]
                    if sess.get("day", 0) > 0 and (sess.get("week"), sess.get("day")) in day_key_to_idx
                )
            )
            orig_slots = fallback_slots

        week_sessions = [s for s in ot_meta[name]["Sessions"] if s.get("week") == TARGET_WEEK]
        base_sessions = week_sessions if week_sessions else ot_meta[name]["Sessions"]
        dur_candidates = [int(s.get("duration", DUR_DEFAULT_SLOTS)) for s in base_sessions]
        dur_slots = max(1, max(dur_candidates) if dur_candidates else DUR_DEFAULT_SLOTS)

        exams.append(
            {
                "name": name,
                "enr": stats[name]["enrollment"],
                "need_room": stats[name]["need_room"],
                "dur_slots": dur_slots,
                "orig_slots": orig_slots,
                "orig_weeks": orig_weeks,
                "orig_room_allow": [1 if r in ot_meta[name]["OrigRooms"] else 0 for r in room_vals],
            }
        )

    enroll = []
    student_ids = []
    for ridx, row in enumerate(picked):
        enroll.append([
            1 if any(parse_int(row.get(col, 0)) > 0 for col in exam_cols[exam]) else 0
            for exam in selected
        ])
        student_ids.append(extract_student_id(row, ridx))

    return {
        "n_exams": len(exams),
        "n_stud": len(enroll),
        "n_days": len(day_keys),
        "n_slots": len(start_vals),
        "n_time_points": len(time_points),
        "slot_vals": start_vals,
        "day_keys": day_keys,
        "time_points": time_points,
        "n_rooms": len(room_vals),
        "room_no": room_vals,
        "room_cap": [ROOM_CAP[r] for r in room_vals],
        "occ_all": occ_all,
        "enroll": enroll,
        "student_ids": student_ids,
        "exams": exams,
    }


# ---------------------------------------------------------------------
# 메인 실행
# ---------------------------------------------------------------------
def run_exact_18() -> dict | None:
    inst = build_instance_18()
    write_model_summary_html()

    # ================================================================
    # 1. 집합 정의
    # I: 과목, J: 학생, W: 주차{7,8,9}, D: 요일{1..5}, T: 시작 슬롯, TAU: 시간점, R: 강의실
    # ================================================================
    I = range(inst["n_exams"])
    J = range(inst["n_stud"])
    W = WEEK_VALUES[:]
    D = [1, 2, 3, 4, 5]
    T = range(inst["n_slots"])
    TAU = range(inst["n_time_points"])
    R = range(inst["n_rooms"])
    PEN_N = range(inst["n_exams"] + 1)

    day_key_to_idx = {key: idx for idx, key in enumerate(inst["day_keys"])}
    max_tp = max(inst["time_points"])

    # ================================================================
    # 2. 파라미터 정의
    # ================================================================
    # Delta_i_t_tau: 과목 i가 시작 슬롯 t에서 시간점 tau를 점유하면 1
    Delta_i_t_tau = {}
    valid_start = {}
    for i in I:
        dur = inst["exams"][i]["dur_slots"]
        for t in T:
            st = inst["slot_vals"][t]
            tp_set = set(active_slot_indices(st, inst["time_points"], dur))
            valid_start[i, t] = (st + dur <= max_tp + 1)
            for tau in TAU:
                Delta_i_t_tau[i, t, tau] = 1 if tau in tp_set else 0

    # OCC_wdrtau: 주차 w, 요일 d, 강의실 r, 시간점 tau에 기존 수업 점유가 있으면 1
    OCC_wdrtau = {}
    for w in W:
        for d in D:
            day_idx = day_key_to_idx[(w, d)]
            for r in R:
                for tau in TAU:
                    OCC_wdrtau[w, d, r, tau] = inst["occ_all"].get((day_idx, r, tau), 0)

    # 과목별 원래 시간 슬롯 집합 (week, day, start_slot)
    orig_time_triplets = {}
    for i in I:
        triples = set()
        for day_one_based, start in inst["exams"][i]["orig_slots"]:
            day_idx = day_one_based - 1
            week, dow = inst["day_keys"][day_idx]
            triples.add((week, dow, start))
        orig_time_triplets[i] = triples

    # 최대 이동 제약(기존 기호만 사용):
    # 원래 시간 집합 orig_time_triplets[i]와 비교해서
    # day_dist<=D_MAX AND time_dist<=T_MAX 를 만족하는 (w,d,t)만 허용한다.
    # 만족하지 않는 조합은 x_iwdt=0으로 고정한다.
    allow_iwdt = {}
    for i in I:
        for w in W:
            for d in D:
                for t in T:
                    slot_val = inst["slot_vals"][t]
                    allow = 0
                    for w0, d0, t0 in orig_time_triplets[i]:
                        day_dist = abs((w - w0) * 5 + (d - d0))
                        time_dist = abs(slot_val - t0)
                        if day_dist <= D_MAX and time_dist <= T_MAX:
                            allow = 1
                            break
                    allow_iwdt[i, w, d, t] = allow

    # ================================================================
    # 3. 목적함수식(설정값)
    # Min = WEIGHT_ROOM_MOVE*ΣRoomChange_i
    #     + WEIGHT_TIME_MOVE*ΣTimeMove_i
    #     + WEIGHT_DAILY*ΣP_swd
    # (실제 식은 제약식 이후 setObjective에서 구성)
    # ================================================================

    # 결정변수 정의
    # x_iwdt, z_iwdtr, y_swd, H_swdn, P_swd, RoomChange_i, TimeMove_i
    m = gp.Model("exact_18_exam_word_1to1")

    x_iwdt = m.addVars(I, W, D, T, vtype=GRB.BINARY, name="x_iwdt")
    z_iwdtr = m.addVars(I, W, D, T, R, vtype=GRB.BINARY, name="z_iwdtr")

    y_swd = m.addVars(J, W, D, vtype=GRB.INTEGER, lb=0, name="y_swd")
    H_swdn = m.addVars(J, W, D, PEN_N, vtype=GRB.BINARY, name="H_swdn")
    P_swd = m.addVars(J, W, D, vtype=GRB.CONTINUOUS, lb=0, name="P_swd")

    RoomChange_i = m.addVars(I, vtype=GRB.BINARY, name="RoomChange_i")
    TimeMove_i = m.addVars(I, vtype=GRB.BINARY, name="TimeMove_i")

    # ================================================================
    # 4. 제약식
    # ================================================================
    # (1) 과목 i는 정확히 한 번만 배정
    for i in I:
        # sum_{w,d,t} x_iwdt = 1
        m.addConstr(
            gp.quicksum(x_iwdt[i, w, d, t] for w in W for d in D for t in T) == 1,
            name=f"C1_assign_once_{i}",
        )

    # (2) 시간 배정과 강의실 수 연결 + 범위를 벗어난 시작 슬롯 금지
    for i in I:
        need_room = inst["exams"][i]["need_room"]
        for w in W:
            for d in D:
                for t in T:
                    # sum_r z_iwdtr = need_room_i * x_iwdt
                    m.addConstr(
                        gp.quicksum(z_iwdtr[i, w, d, t, r] for r in R) == need_room * x_iwdt[i, w, d, t],
                        name=f"C2_needroom_link_{i}_{w}_{d}_{t}",
                    )
                    if not valid_start[i, t]:
                        # 유효하지 않은 시작 슬롯은 x_iwdt = 0
                        m.addConstr(x_iwdt[i, w, d, t] == 0, name=f"C2_invalid_start_{i}_{w}_{d}_{t}")
                    # 최대 이동거리(기호 추가 없이 구현): 허용되지 않으면 x_iwdt = 0
                    if allow_iwdt[i, w, d, t] == 0:
                        m.addConstr(x_iwdt[i, w, d, t] == 0, name=f"C11C12_move_limit_{i}_{w}_{d}_{t}")

    # (3) 수용 인원 제약
    for i in I:
        enr = inst["exams"][i]["enr"]
        for w in W:
            for d in D:
                for t in T:
                    # sum_r cap_r * z_iwdtr >= enrollment_i * x_iwdt
                    m.addConstr(
                        gp.quicksum(inst["room_cap"][r] * z_iwdtr[i, w, d, t, r] for r in R) >= enr * x_iwdt[i, w, d, t],
                        name=f"C3_capacity_{i}_{w}_{d}_{t}",
                    )

    # (4) 강의실 중복 금지 + 기존 수업 점유 시간 사용 금지
    for w in W:
        for d in D:
            for r in R:
                for tau in TAU:
                    # sum_{i,t} Delta_i_t_tau * z_iwdtr <= 1 - OCC_wdrtau
                    m.addConstr(
                        gp.quicksum(
                            Delta_i_t_tau[i, t, tau] * z_iwdtr[i, w, d, t, r]
                            for i in I for t in T
                        ) <= 1 - OCC_wdrtau[w, d, r, tau],
                        name=f"C4_room_overlap_occ_{w}_{d}_{r}_{tau}",
                    )

    # (5) 학생 동시시험 금지
    for s in J:
        for w in W:
            for d in D:
                for tau in TAU:
                    # 학생 s 기준 같은 시간점에서 동시 응시 금지
                    m.addConstr(
                        gp.quicksum(
                            inst["enroll"][s][i] * Delta_i_t_tau[i, t, tau] * x_iwdt[i, w, d, t]
                            for i in I for t in T
                        ) <= 1,
                        name=f"C5_student_overlap_{s}_{w}_{d}_{tau}",
                    )

    # (6) 학생 하루 시험 수 y_swd 정의
    for s in J:
        for w in W:
            for d in D:
                # y_swd = sum_{i,t} enroll_si * x_iwdt
                m.addConstr(
                    y_swd[s, w, d] == gp.quicksum(inst["enroll"][s][i] * x_iwdt[i, w, d, t] for i in I for t in T),
                    name=f"C6_ydef_{s}_{w}_{d}",
                )
                # (6-1) 하루 4개 시험 금지(하루 최대 3개 허용)
                m.addConstr(y_swd[s, w, d] <= 3, name=f"C6_1_daily_max3_{s}_{w}_{d}")

    # (7) 하루 시험 수 벌점 P_swd 정의: y=0이면 0, y>=1이면 (y-1)^2
    #     비선형식을 one-hot 선형식으로 구현
    big_m = inst["n_exams"]
    penalty_val = {n: 0 if n == 0 else (n - 1) ** 2 for n in PEN_N}
    for s in J:
        for w in W:
            for d in D:
                # one-hot: 하루 시험 수 범주 n은 하나만 선택
                m.addConstr(gp.quicksum(H_swdn[s, w, d, n] for n in PEN_N) == 1, name=f"C7_onehot_{s}_{w}_{d}")
                for n in PEN_N:
                    # H_swdn=1 이면 y_swd=n 이 되도록 상한/하한 결합
                    m.addConstr(
                        y_swd[s, w, d] - n <= big_m * (1 - H_swdn[s, w, d, n]),
                        name=f"C7_hi_{s}_{w}_{d}_{n}",
                    )
                    m.addConstr(
                        n - y_swd[s, w, d] <= big_m * (1 - H_swdn[s, w, d, n]),
                        name=f"C7_lo_{s}_{w}_{d}_{n}",
                    )
                # P_swd = penalty(n) * H_swdn 의 선형 결합
                m.addConstr(
                    P_swd[s, w, d] == gp.quicksum(penalty_val[n] * H_swdn[s, w, d, n] for n in PEN_N),
                    name=f"C7_Pdef_{s}_{w}_{d}",
                )

    # (8) 강의실 변경 여부 RoomChange_i 정의
    for i in I:
        orig_room_sum = gp.quicksum(
            inst["exams"][i]["orig_room_allow"][r] * z_iwdtr[i, w, d, t, r]
            for w in W for d in D for t in T for r in R
        )
        # 원래 강의실이 하나도 선택되지 않으면 RoomChange_i=1
        m.addConstr(RoomChange_i[i] >= 1 - orig_room_sum, name=f"C8_roomchange_lo_{i}")
        for w in W:
            for d in D:
                for t in T:
                    for r in R:
                        if inst["exams"][i]["orig_room_allow"][r] == 1:
                            # 원래 강의실이 선택되면 RoomChange_i=0 가능
                            m.addConstr(
                                RoomChange_i[i] <= 1 - z_iwdtr[i, w, d, t, r],
                                name=f"C8_roomchange_hi_{i}_{w}_{d}_{t}_{r}",
                            )

    # (9) 연속시험 금지(하드 제약)
    consecutive_records = build_consecutive_records(inst)
    for idx, (_, day_idx, i, t1, j, t2) in enumerate(consecutive_records):
        week, dow = inst["day_keys"][day_idx]
        # 연속 시작 슬롯 조합은 동시 선택 금지
        m.addConstr(
            x_iwdt[i, week, dow, t1] + x_iwdt[j, week, dow, t2] <= 1,
            name=f"C_add_consecutive_forbid_{idx}",
        )

    # (10) 시간이동 여부 TimeMove_i 정의 (원래 시간 유지 여부)
    for i in I:
        orig_sum = gp.quicksum(
            x_iwdt[i, w, d, t] for w in W for d in D for t in T if (w, d, inst["slot_vals"][t]) in orig_time_triplets[i]
        )
        nonorig_sum = gp.quicksum(
            x_iwdt[i, w, d, t] for w in W for d in D for t in T if (w, d, inst["slot_vals"][t]) not in orig_time_triplets[i]
        )
        # 원래 시간이면 0, 원래 시간이 아니면 1이 되도록 결합
        m.addConstr(TimeMove_i[i] >= 1 - orig_sum, name=f"C_add_timemove_lo_{i}")
        m.addConstr(TimeMove_i[i] <= nonorig_sum, name=f"C_add_timemove_hi_{i}")

    # ================================================================
    # 목적함수 구성
    # 최소화 = 강의실변경 + 시간이동 + 하루벌점 (가중치 적용)
    # ================================================================
    total_room_move = gp.quicksum(RoomChange_i[i] for i in I)
    total_time_move = gp.quicksum(TimeMove_i[i] for i in I)
    total_daily = gp.quicksum(P_swd[s, w, d] for s in J for w in W for d in D)

    m.setObjective(
        WEIGHT_ROOM_MOVE * total_room_move
        + WEIGHT_TIME_MOVE * total_time_move
        + WEIGHT_DAILY * total_daily,
        GRB.MINIMIZE,
    )

    # ================================================================
    # 결과 계산 및 출력
    # ================================================================
    wall_start = time.perf_counter()
    m.optimize()
    wall_runtime = time.perf_counter() - wall_start

    if m.SolCount == 0:
        print("No feasible solution found.")
        print(f"GurobiStatus = {m.Status}")
        print(f"RuntimeSec = {wall_runtime:.6f}")
        return

    assignment = {}
    for i in I:
        for w in W:
            for d in D:
                for t in T:
                    if x_iwdt[i, w, d, t].X > 0.5:
                        rooms = [inst["room_no"][r] for r in R if z_iwdtr[i, w, d, t, r].X > 0.5]
                        day_idx = day_key_to_idx[(w, d)]
                        assignment[i] = {
                            "day_idx": day_idx,
                            "week": w,
                            "dow": d,
                            "slot_idx": t,
                            "slot_val": inst["slot_vals"][t],
                            "rooms": rooms,
                        }

    room_change_map = {i: int(round(RoomChange_i[i].X)) for i in I}
    time_move_map = {i: int(round(TimeMove_i[i].X)) for i in I}

    # 제약 검증용 카운트 계산
    assign_once_violation = max(0, inst["n_exams"] - len(assignment))
    room_count_violation = 0
    room_cap_violation = 0
    room_overlap_violation = 0
    roomchange_def_violation = 0
    timemove_def_violation = 0

    room_to_idx = {room_no: ridx for ridx, room_no in enumerate(inst["room_no"])}
    use_count: dict[tuple[int, int, int], int] = {}

    for i in I:
        info = assignment[i]
        rooms = info["rooms"]
        day_idx = int(info["day_idx"])
        slot_val = int(info["slot_val"])
        dur = int(inst["exams"][i]["dur_slots"])
        interval_i = active_slot_indices(slot_val, inst["time_points"], dur)

        if len(rooms) != int(inst["exams"][i]["need_room"]):
            room_count_violation += 1
        cap_sum = sum(inst["room_cap"][room_to_idx[r]] for r in rooms)
        if cap_sum < int(inst["exams"][i]["enr"]):
            room_cap_violation += 1

        for r in rooms:
            ridx = room_to_idx[r]
            for th in interval_i:
                key = (day_idx, ridx, th)
                use_count[key] = use_count.get(key, 0) + 1

        orig_allowed_rooms = {inst["room_no"][r] for r in R if inst["exams"][i]["orig_room_allow"][r] == 1}
        expected_roomchange = 0 if any(r in orig_allowed_rooms for r in rooms) else 1
        if room_change_map[i] != expected_roomchange:
            roomchange_def_violation += 1

        expected_timemove = 0 if (int(info["week"]), int(info["dow"]), slot_val) in orig_time_triplets[i] else 1
        if time_move_map[i] != expected_timemove:
            timemove_def_violation += 1

    for (didx, ridx, th), cnt in use_count.items():
        base_occ = inst["occ_all"].get((didx, ridx, th), 0)
        if cnt + base_occ > 1:
            room_overlap_violation += 1

    overlap_violation = 0
    for s in J:
        for d_idx in range(inst["n_days"]):
            for th in TAU:
                cnt = 0
                for i in I:
                    if inst["enroll"][s][i] == 0:
                        continue
                    info = assignment[i]
                    interval_i = active_slot_indices(
                        int(info["slot_val"]),
                        inst["time_points"],
                        inst["exams"][i]["dur_slots"],
                    )
                    if int(info["day_idx"]) == d_idx and th in interval_i:
                        cnt += 1
                if cnt > 1:
                    overlap_violation += 1

    consecutive_violation = 0
    for _, d_idx, i, t1, j, t2 in consecutive_records:
        a = 1 if int(assignment[i]["day_idx"]) == d_idx and int(assignment[i]["slot_idx"]) == t1 else 0
        b = 1 if int(assignment[j]["day_idx"]) == d_idx and int(assignment[j]["slot_idx"]) == t2 else 0
        if a and b:
            consecutive_violation += 1

    daily4 = 0
    for s in J:
        for d_idx in range(inst["n_days"]):
            cnt = 0
            for i in I:
                if inst["enroll"][s][i] == 1 and int(assignment[i]["day_idx"]) == d_idx:
                    cnt += 1
            if cnt >= 4:
                daily4 += 1

    daily_penalty_calc = 0
    for s in J:
        for d_idx in range(inst["n_days"]):
            n_cnt = 0
            for i in I:
                if inst["enroll"][s][i] == 1 and int(assignment[i]["day_idx"]) == d_idx:
                    n_cnt += 1
            daily_penalty_calc += 0 if n_cnt == 0 else (n_cnt - 1) ** 2
    daily_penalty_def_violation = 0 if int(round(total_daily.getValue())) == int(daily_penalty_calc) else 1

    print(f"===== Exact 결과 (과목 수: {inst['n_exams']}) =====")
    print(f"Objective = {m.ObjVal:.4f}")
    print(f"RoomMoveSum = {total_room_move.getValue():.0f}")
    print(f"TimeMoveSum = {total_time_move.getValue():.0f}")
    print(f"DailyPenaltySum = {total_daily.getValue():.0f}")
    print(f"동시시험 위반건수 = {overlap_violation}")
    print(f"연속시험 위반건수 = {consecutive_violation}")
    print(f"하루 4시험 건수 = {daily4}")
    print(f"RuntimeSec = {wall_runtime:.6f}")
    print(f"GurobiRuntimeSec = {m.Runtime:.6f}")
    print("---- 결정변수 선택표 ----")
    print("과목 | 주차 | 요일 | 시작 | 종료 | x_iwdt | z_iwdtr(강의실) | TimeMove_i | RoomChange_i")
    for i in I:
        info = assignment[i]
        st = int(info["slot_val"])
        et = st + int(inst["exams"][i]["dur_slots"])
        room_label = " ".join(str(r) for r in info["rooms"])
        print(
            f"{inst['exams'][i]['name']} | {info['week']} | {DAY_LABELS.get(int(info['dow']), str(info['dow']))} | "
            f"{slot_to_time(st)} | {slot_to_time(et)} | 1 | {room_label} | {time_move_map[i]} | {room_change_map[i]}"
        )

    verify_rows = [
        ["(1) 과목 1회 배정", str(assign_once_violation)],
        ["(2) 필요강의실 수", str(room_count_violation)],
        ["(3) 수용인원", str(room_cap_violation)],
        ["(4) 강의실 중복/점유", str(room_overlap_violation)],
        ["(5) 학생 동시시험", str(overlap_violation)],
        ["(7) 벌점정의", str(daily_penalty_def_violation)],
        ["(8) 강의실변경정의", str(roomchange_def_violation)],
        ["(9) 연속시험금지", str(consecutive_violation)],
        ["(10) 시간이동정의", str(timemove_def_violation)],
        ["하루 4시험 건수", str(daily4)],
    ]

    decision_rows = []
    for i in I:
        info = assignment[i]
        decision_rows.append([
            inst["exams"][i]["name"],
            f"({info['week']}, {DAY_LABELS.get(int(info['dow']), str(info['dow']))}, {slot_to_time(int(info['slot_val']))})",
            " ".join(str(r) for r in info["rooms"]),
            str(time_move_map[i]),
            str(room_change_map[i]),
        ])

    save_result_files(
        inst=inst,
        assignment=assignment,
        time_move_map=time_move_map,
        room_change_map=room_change_map,
        objective=float(m.ObjVal),
        room_move_sum=float(total_room_move.getValue()),
        time_move_sum=float(total_time_move.getValue()),
        daily_penalty_sum=float(total_daily.getValue()),
        overlap_violation=overlap_violation,
        consecutive_violation=consecutive_violation,
        daily4_count=daily4,
        runtime_sec=wall_runtime,
        gurobi_runtime_sec=float(m.Runtime),
    )
    # 서비스(웹) 전용 데이터 저장
    service_payload = {
        "summary": {
            "objective": float(m.ObjVal),
            "room_move_sum": float(total_room_move.getValue()),
            "time_move_sum": float(total_time_move.getValue()),
            "daily_penalty_sum": float(total_daily.getValue()),
            "overlap_violation": int(overlap_violation),
            "consecutive_violation": int(consecutive_violation),
            "daily4_count": int(daily4),
            "runtime_sec": float(wall_runtime),
            "gurobi_runtime_sec": float(m.Runtime),
        },
        "student_ids": [str(x) for x in inst.get("student_ids", [])],
        "enroll": inst["enroll"],
        "exams": [
            {"name": ex["name"], "dur_slots": int(ex["dur_slots"])}
            for ex in inst["exams"]
        ],
        "assignment": {
            str(i): {
                "week": int(info["week"]),
                "dow": int(info["dow"]),
                "slot_val": int(info["slot_val"]),
                "rooms": [int(r) for r in info["rooms"]],
            }
            for i, info in assignment.items()
        },
        "time_move_map": {str(i): int(v) for i, v in time_move_map.items()},
        "room_change_map": {str(i): int(v) for i, v in room_change_map.items()},
    }
    json_text = json.dumps(service_payload, ensure_ascii=False)
    RESULT_JSON_PATH.write_text(json_text, encoding="utf-8")
    RESULT_JSON_ASCII_PATH.write_text(json_text, encoding="utf-8")

    print(f"결과 파일 저장: {RESULT_TXT_PATH}")
    print(f"결과 파일 저장: {RESULT_CSV_PATH}")
    print(f"결과 파일 저장: {RESULT_JSON_PATH}")
    print(f"결과 파일 저장: {RESULT_JSON_ASCII_PATH}")

    # 시각화/리포트 파일 생성
    if GENERATE_REPORT == 1:
        show_result_plots(
            inst=inst,
            assignment=assignment,
            objective=m.ObjVal,
            room_move=total_room_move.getValue(),
            time_move=total_time_move.getValue(),
            daily_penalty=total_daily.getValue(),
            verify_rows=verify_rows,
            decision_rows=decision_rows,
        )
    return {
        "inst": inst,
        "assignment": assignment,
        "room_change_map": room_change_map,
        "time_move_map": time_move_map,
        "objective": float(m.ObjVal),
        "room_move_sum": float(total_room_move.getValue()),
        "time_move_sum": float(total_time_move.getValue()),
        "daily_penalty_sum": float(total_daily.getValue()),
        "overlap_violation": int(overlap_violation),
        "consecutive_violation": int(consecutive_violation),
        "daily4_count": int(daily4),
        "runtime_sec": float(wall_runtime),
        "gurobi_runtime_sec": float(m.Runtime),
    }


if __name__ == "__main__":
    run_exact_18()
