from __future__ import annotations

from datetime import datetime, timedelta
import html
import json
import logging
import os
import re
import io
from itertools import combinations
from pathlib import Path
from urllib.parse import quote

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
    .block-container,
    [data-testid="stAppViewContainer"] .main .block-container {
      padding-top: 0.18rem !important;
      padding-bottom: 0.65rem !important;
      max-width: 98vw !important;
    }
    .compact-header {
      margin: 0 0 0.06rem 0;
      padding: 0;
    }
    .compact-header-title {
      font-size: 0.78rem;
      font-weight: 800;
      line-height: 1.0;
      letter-spacing: -0.01em;
      color: #64748b !important;
      margin: 0;
    }
    .compact-header-desc {
      margin-top: 0.02rem;
      font-size: 0.72rem;
      line-height: 1.0;
      color: #64748b !important;
    }
    .compact-section-title {
      margin: 0.08rem 0 0.08rem 0;
      font-size: 0.95rem;
      line-height: 1.05;
      font-weight: 800;
      color: #64748b !important;
    }
    .compact-calendar-title {
      margin: 0.02rem 0 0.06rem 0;
      font-size: 1.05rem;
      line-height: 1.05;
      font-weight: 900;
      color: #0b1220 !important;
    }
    .compact-tabs {
      margin: 0;
      padding: 0;
    }
    [data-testid="stHeader"], [data-testid="stToolbar"] {
      background: transparent !important;
    }
    .stMarkdown, .stCaption, .stText, .stMetricLabel, .stMetricValue, .st-emotion-cache-10trblm {
      color: var(--text-main) !important;
    }
    .stCaption {
      margin: 0 !important;
      font-size: 0.82rem !important;
      line-height: 1.2 !important;
    }
    h1, h2, h3, h4, h5, h6, p, span, label, small, div {
      color: var(--text-main) !important;
    }
    h1 {
      margin: 0 !important;
      padding: 0 !important;
      line-height: 1 !important;
    }
    h2, h3 {
      margin-top: 0.08rem !important;
      margin-bottom: 0.08rem !important;
    }
    p {
      margin-top: 0.05rem !important;
      margin-bottom: 0.08rem !important;
    }
    hr {
      margin: 0.08rem 0 0.15rem 0 !important;
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
      border-radius: 10px;
      padding: 5px 8px;
      min-height: 0 !important;
    }
    div[data-testid="stMetric"] label,
    div[data-testid="stMetric"] [data-testid="stMetricLabel"] {
      font-size: 0.82rem !important;
      line-height: 1.0 !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
      font-size: 1.68rem !important;
      line-height: 1.0 !important;
    }
    .big-summary-row {
      display:grid;
      grid-template-columns: repeat(5, minmax(108px, 1fr));
      gap:8px;
      margin: 4px 0 8px 0;
    }
    .big-summary-card {
      border:1px solid #cbd5e1;
      border-radius:10px;
      background:#ffffff;
      padding:8px 10px;
      min-height:68px;
    }
    .big-summary-title {
      font-size:12px;
      font-weight:700;
      color:#334155 !important;
    }
    .big-summary-value {
      margin-top:4px;
      font-size:18px;
      font-weight:800;
      color:#0b1220 !important;
      line-height:1.2;
      word-break:keep-all;
    }
    .calendar-wrap table {width:100%; border-collapse:collapse; table-layout:fixed; font-size:13px;}
    .calendar-wrap th, .calendar-wrap td {border:1px solid #cfd8e3; padding:5px; vertical-align:top; height:70px;}
    .calendar-wrap th {background:#dbe7f9; text-align:center; font-size:14px; color:var(--text-main);}
    .calendar-wrap .time-col {background:#f3f7fc; width:90px; text-align:center; font-weight:700; color:var(--text-main);}
    .calendar-wrap .exam {background:#dbeafe !important; color:#0b1220 !important; border:2px solid #7aa7df !important; text-align:center;}
    .calendar-wrap .course {font-weight:900; margin-bottom:3px; font-size:13px; color:#0b1220 !important; text-align:center;}
    .calendar-wrap .empty {background:#ffffff;}
    .calendar-wrap .exam-block {
      display:flex !important;
      min-height:58px;
      background:#bfdbfe;
      border:1px solid #60a5fa;
      border-radius:7px;
      padding:6px 8px;
      line-height:1.25;
      white-space:normal;
      word-break:keep-all;
      overflow-wrap:anywhere;
      box-shadow: inset 0 0 0 1px rgba(255,255,255,.45);
      flex-direction:column;
      justify-content:center !important;
      align-items:center !important;
      text-align:center !important;
      width:100%;
      height:100%;
      box-sizing:border-box;
    }
    .calendar-wrap .exam-link {
      text-decoration:none !important;
      color:#0b1220 !important;
      display:block;
    }
    .calendar-wrap .exam-link:hover .exam-block {
      background:#93c5fd;
      border-color:#2563eb;
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
      text-align:center;
      width:100%;
    }
    .calendar-wrap .cont {
      min-height:58px;
      background:#bfdbfe;
      border:1px solid #60a5fa;
      border-radius:7px;
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
      background:#f1f5f9;
      border:1px solid #cbd5e1;
      border-radius:6px;
      padding:5px;
      line-height:1.25;
      font-weight:700;
      color:#0b1220 !important;
      min-height:42px;
    }
    .click-grid-possible {
      background:#ecfdf5;
      border:1px solid #bbf7d0;
      border-radius:6px;
      padding:5px;
      line-height:1.25;
      font-weight:800;
      color:#14532d !important;
      text-align:center;
      min-height:42px;
    }
    .click-grid-selected-move {
      background:#eff6ff;
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
      background:#f8fafc;
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
    .result-table td.change {background:#fff7ed; color:#9a3412 !important; font-weight:800;}
    .result-table td.status-keep {background:#f0fdf4 !important; color:#166534 !important; font-weight:800;}
    .result-table td.status-time {background:#fef9c3 !important; color:#854d0e !important; font-weight:800;}
    .result-table td.status-room {background:#dbeafe !important; color:#1e40af !important; font-weight:800;}
    .result-table td.status-both {background:#ffedd5 !important; color:#9a3412 !important; font-weight:800;}
    .change-legend {
      display:flex;
      flex-wrap:wrap;
      gap:8px;
      margin:8px 0 10px 0;
      font-size:13px;
      font-weight:800;
    }
    .change-legend-item {
      display:inline-flex;
      align-items:center;
      gap:6px;
      padding:5px 9px;
      border:1px solid #d8e0ea;
      border-radius:999px;
      background:#ffffff;
    }
    .change-legend-dot {
      display:inline-block;
      width:12px;
      height:12px;
      border-radius:999px;
      border:1px solid rgba(15,23,42,.12);
    }
    .change-legend-dot.keep {background:#bbf7d0;}
    .change-legend-dot.time {background:#fef08a;}
    .change-legend-dot.room {background:#bfdbfe;}
    .change-legend-dot.both {background:#fed7aa;}
    .overall-legend {
      display:flex;
      flex-wrap:wrap;
      gap:6px;
      margin:1px 0 2px 0;
      font-size:10px;
      font-weight:700;
      color:#334155 !important;
    }
    .overall-legend-item {
      display:flex;
      align-items:center;
      gap:6px;
    }
    .overall-legend-swatch {
      width:12px;
      height:12px;
      border-radius:4px;
      border:1px solid rgba(15,23,42,.12);
      flex:0 0 auto;
    }
    .overall-grade-1 {background:#f8fafc; border-left:4px solid #93c5fd !important;}
    .overall-grade-2 {background:#f8fafc; border-left:4px solid #86efac !important;}
    .overall-grade-3 {background:#f8fafc; border-left:4px solid #fdba74 !important;}
    .overall-grade-4 {background:#f8fafc; border-left:4px solid #fca5a5 !important;}
    .overall-grade-x {background:#e5e7eb;}
    .overall-calendar-wrap table {
      min-width: 1280px;
      table-layout: fixed;
    }
    .overall-calendar-wrap th,
    .overall-calendar-wrap td {
      min-width: 210px;
    }
    .overall-cell-list {
      display:grid;
      gap:6px;
      width:100%;
      max-width:100%;
      box-sizing:border-box;
      overflow:hidden;
    }
    .overall-cell-card {
      display:flex;
      flex-direction:column;
      justify-content:center;
      align-items:center;
      min-height:52px;
      padding:6px 8px;
      border-radius:8px;
      border:1px solid rgba(15,23,42,.10);
      box-sizing:border-box;
      overflow:hidden;
      max-width:100%;
      text-align:center;
      word-break:keep-all;
      overflow-wrap:anywhere;
    }
    .overall-cell-title {
      width:100%;
      font-size:13px;
      font-weight:900;
      color:#0b1220 !important;
      line-height:1.2;
    }
    .overall-cell-sub {
      width:100%;
      margin-top:3px;
      font-size:12px;
      font-weight:700;
      color:#334155 !important;
      line-height:1.2;
    }
    .overall-abs-wrap {
      overflow-x:auto;
      overflow-y:auto;
      padding-bottom:2px;
      margin-top:1px;
      max-height:none;
      width:100%;
      max-width:100vw;
    }
    .overall-abs-shell {
      width:100%;
      min-width:0;
      border:1px solid #d8e0ea;
      border-radius:12px;
      background:#ffffff;
      overflow:visible;
    }
    .overall-abs-header {
      display:grid;
      grid-template-columns: 72px repeat(5, minmax(0, 1fr));
      background:#eaf2ff;
      border-bottom:1px solid #d8e0ea;
    }
    .overall-abs-head {
      padding:4px 3px;
      text-align:center;
      font-size:11px;
      font-weight:900;
      color:#0b1220 !important;
      border-right:1px solid #d8e0ea;
      line-height:1.05;
    }
    .overall-abs-head:last-child {
      border-right:none;
    }
    .overall-abs-body {
      display:grid;
      grid-template-columns: 72px repeat(5, minmax(0, 1fr));
      align-items:stretch;
      overflow:visible;
    }
    .overall-abs-time-axis {
      position:relative;
      background:#f8fbff;
      border-right:1px solid #d8e0ea;
    }
    .overall-abs-time-label {
      position:absolute;
      left:0;
      width:100%;
      transform:translateY(-50%);
      text-align:center;
      font-size:9px;
      font-weight:800;
      color:#334155 !important;
    }
    .overall-abs-day-col {
      position:relative;
      border-right:1px solid #e2e8f0;
      background:
        repeating-linear-gradient(
          to bottom,
          #ffffff 0,
          #ffffff 47px,
          #edf2f7 47px,
          #edf2f7 48px
        );
      overflow:hidden;
    }
    .overall-abs-day-col:last-child {
      border-right:none;
    }
    .overall-abs-event {
      position:absolute;
      padding:2px 4px;
      border-radius:8px;
      border:1px solid rgba(15,23,42,.10);
      box-sizing:border-box;
      overflow:hidden;
      max-width:100%;
      line-height:1.2;
      box-shadow:0 3px 10px rgba(15,23,42,.08);
      z-index:1;
    }
    .overall-abs-title {
      font-size:9px;
      font-weight:900;
      color:#0b1220 !important;
      word-break:keep-all;
      overflow-wrap:anywhere;
      display:-webkit-box;
      -webkit-line-clamp:2;
      -webkit-box-orient:vertical;
      overflow:hidden;
    }
    .overall-abs-sub {
      margin-top:1px;
      font-size:8px;
      font-weight:700;
      color:#334155 !important;
      word-break:keep-all;
      overflow-wrap:anywhere;
      white-space:nowrap;
      overflow:hidden;
      text-overflow:ellipsis;
    }
    .overall-abs-link {
      display:block;
      width:100%;
      height:100%;
      text-decoration:none !important;
      color:inherit !important;
    }
    .sim-note {
      border:1px solid #bfdbfe;
      background:#eff6ff;
      border-radius:12px;
      padding:10px 12px;
      color:#1e3a8a !important;
      font-size:13px;
      line-height:1.45;
      margin:8px 0 10px 0;
    }
    div[data-baseweb="tab-list"] {
      gap: 0.2rem !important;
      margin-bottom: 0.02rem !important;
    }
    button[data-baseweb="tab"] {
      min-height: 26px !important;
      padding: 1px 7px !important;
      font-size: 0.82rem !important;
    }
    .sim-card {
      border:1px solid #d8e0ea;
      background:#ffffff;
      border-radius:14px;
      padding:12px 14px;
      box-shadow:0 4px 14px rgba(15,23,42,.05);
      margin:8px 0;
    }
    .sim-card.status {
      border:1px solid #93c5fd;
      background:#f8fbff;
      box-shadow:0 6px 18px rgba(37,99,235,.08);
    }
    .sim-card.top1 {border:1.5px solid #93c5fd; background:#f8fbff;}
    .sim-card.top2 {border:1.5px solid #bfdbfe; background:#ffffff;}
    .sim-card.top3 {border:1.5px solid #cbd5e1; background:#ffffff;}
    .sim-step-title {
      margin:14px 0 6px 0;
      font-size:17px;
      font-weight:900;
      color:#0f172a !important;
    }
    .sim-action-note {
      color:#475569 !important;
      font-size:12px;
      margin:0 0 8px 0;
    }
    .sim-card-title {
      font-size:15px;
      font-weight:900;
      color:#0b1220 !important;
      margin-bottom:6px;
    }
    .sim-card-line {
      font-size:13px;
      color:#334155 !important;
      line-height:1.45;
      margin:2px 0;
    }
    .sim-badges {
      display:flex;
      flex-wrap:wrap;
      gap:6px;
      margin-top:8px;
    }
    .sim-badge {
      display:inline-block;
      padding:4px 8px;
      border-radius:999px;
      font-size:12px;
      font-weight:800;
      line-height:1.2;
      box-sizing:border-box;
    }
    .sim-badge.ok {
      background:#f0fdf4;
      color:#166534 !important;
      border:1px solid #bbf7d0;
    }
    .sim-badge.warn {
      background:#fffbeb;
      color:#92400e !important;
      border:1px solid #fde68a;
    }
    .sim-badge.risk {
      background:#fef2f2;
      color:#991b1b !important;
      border:1px solid #fecaca;
    }
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
ROOM_CAP = {402: 23, 479: 55, 482: 52, 483: 69, 502: 45, 583: 32}
WEIGHT_ROOM_MOVE = 0.129409615675
WEIGHT_TIME_MOVE = 0.283466518343
WEIGHT_DAILY = 0.587123865982
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

ALIASES = {
    "Calculus(1)": ["Calculus(1)", "Calculus(1)-1", "Calculus(1)-2", "대학수학(1)"],
    "IntroIE&M": ["IntroIE&M", "IntrolE&M", "IntroIEandM", "산업경영공학개론"],
    "GenAIApps": ["GenAI Apps", "GenAIApps", "생성형AI활용", "생성형AI응용"],
    "Database": ["Database", "데이터베이스"],
    "Det.ManageSci": ["Det#ManageSci", "Det.ManageSci", "확정적경영과학", "확정적 경영과학"],
    "Ergonomics": ["Ergonomics", "인간공학"],
    "Prob&Stats(1)": ["Prob&Stats(1)", "Prob&Stats", "확률과통계", "확률및통계", "확률및통계(1)"],
    "ProdDevProcess": ["ProdDevProcess", "제품개발프로세스"],
    "QualityEng": ["QualityEng", "품질공학"],
    "ReinforcLearn": ["ReinforcLearn", "강화학습"],
    "SmartLogistics": ["SmartLogistics", "스마트물류"],
    "DataMining": ["DataMining", "데이터마이닝"],
    "ErgoExpEval": ["ErgoExpEval", "인간공학적실험평가론"],
    "IntroFinEng": ["IntroFinEng", "금융공학개론"],
    "Optim&Apps": ["Optim&Apps", "최적화모델링응용", "최적화모형및응용"],
    "ProdControl": ["ProdControl", "생산통제"],
    "Corp&Safety": ["Corp&Safety", "기업과안전"],
    "SmartMfg&Auto": ["SmartMfg&Auto", "스마트제조자동화", "스마트제조및자동화"],
}

# 학년 파일이 없거나 매칭이 실패해도 화면에서 학년이 비지 않도록 하는 기본값
COURSE_GRADE_FALLBACK = {
    "Calculus(1)": "1",
    "IntroIE&M": "1",
    "GenAIApps": "1",
    "Database": "2",
    "Det.ManageSci": "2",
    "Ergonomics": "2",
    "Prob&Stats(1)": "2",
    "ProdDevProcess": "3",
    "QualityEng": "3",
    "ReinforcLearn": "4",
    "SmartLogistics": "4",
    "DataMining": "3",
    "ErgoExpEval": "3",
    "IntroFinEng": "3",
    "Optim&Apps": "3",
    "ProdControl": "3",
    "Corp&Safety": "4",
    "SmartMfg&Auto": "4",
}

PROFESSOR_EXACT_FALLBACK = {
    "Calculus(1)-1": "이미혜",
    "Calculus(1)-2": "정유정",
    "대학수학(1)-1": "이미혜",
    "대학수학(1)-2": "정유정",
}

PROFESSOR_BASE_FALLBACK = {
    "IntroIE&M": "장석화",
    "산업경영공학개론": "장석화",
    "GenAIApps": "이준혁",
    "생성형AI활용": "이준혁",
    "생성형AI응용": "이준혁",
    "Prob&Stats(1)": "류도현",
    "확률과통계": "류도현",
    "확률및통계(1)": "류도현",
    "Det.ManageSci": "이종헌",
    "확정적경영과학": "이종헌",
    "Ergonomics": "최서빈",
    "인간공학": "최서빈",
    "Database": "이세린",
    "데이터베이스": "이세린",
    "ProdDevProcess": "박기정",
    "제품개발프로세스": "박기정",
    "QualityEng": "정영배",
    "품질공학": "정영배",
    "IntroFinEng": "정지혁",
    "금융공학개론": "정지혁",
    "Optim&Apps": "이종헌",
    "최적화모델링응용": "이종헌",
    "최적화모형및응용": "이종헌",
    "ProdControl": "김병수",
    "생산통제": "김병수",
    "DataMining": "류도현",
    "데이터마이닝": "류도현",
    "SmartMfg&Auto": "김성균",
    "스마트제조자동화": "김성균",
    "스마트제조및자동화": "김성균",
    "ReinforcLearn": "정지혁",
    "강화학습": "정지혁",
    "SmartLogistics": "이준혁",
    "스마트물류": "이준혁",
    "Corp&Safety": "김철홍",
    "기업과안전": "김철홍",
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


def professor_for_course(course: str, base_key: str | None = None, course_name: str | None = None) -> str:
    exact_candidates = [course, course_name or "", to_korean_course_name(course)]
    for cand in exact_candidates:
        cand_norm = normalize_exact(cand)
        for key, professor in PROFESSOR_EXACT_FALLBACK.items():
            if cand_norm == normalize_exact(key):
                return professor

    base_candidates = [
        base_key or "",
        re.sub(r"[-_]\d+$", "", str(course or "").strip()),
        re.sub(r"[-_]\d+$", "", str(course_name or "").strip()),
        re.sub(r"[-_]\d+$", "", to_korean_course_name(course)),
    ]
    for cand in base_candidates:
        cand_norm = normalize_name(cand)
        for key, professor in PROFESSOR_BASE_FALLBACK.items():
            if cand_norm == normalize_name(key):
                return professor
    return "미지정"


def ensure_professor_column(df_src: pd.DataFrame) -> pd.DataFrame:
    out = df_src.copy()
    if "교수" not in out.columns:
        out["교수"] = "미지정"
    for idx, row in out.iterrows():
        professor = str(row.get("교수", "")).strip()
        if not professor or professor == "미지정" or professor.lower() == "nan":
            out.at[idx, "교수"] = professor_for_course(
                str(row.get("과목", "")),
                str(row.get("기준과목", "")),
                str(row.get("과목명", "")),
            )
    return out


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


def normalize_grade_value(value) -> str:
    text = str(value or "").strip()
    if not text or text == "-" or text.lower() == "nan":
        return "-"
    text = text.replace(" ", "")
    m = re.search(r"([1-4])(?:\.0)?", text)
    if not m:
        return "-"
    return f"{m.group(1)}학년"


def normalize_grade_series(series: pd.Series) -> pd.Series:
    return series.apply(normalize_grade_value)


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
                "교수": professor_for_course(ex["name"], ex.get("base_key", ""), to_korean_course_name(ex["name"])),
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
                "강의실": " or ".join(str(r) for r in rooms),
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
    exact_course = normalize_exact(course_name)
    nc = normalize_name(course_name)
    matched = []
    for c in is_cols:
        exact_col = normalize_exact(c)
        ncol = normalize_name(c)
        if exact_course != nc:
            if exact_col == exact_course:
                matched.append(c)
        elif ncol == nc or ncol.startswith(nc) or nc.startswith(ncol):
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

    taken_cols = []
    for c in is_cols:
        try:
            v = float(df_is.at[row_idx, c])
            if v > 0:
                taken_cols.append(c)
        except Exception:
            continue

    taken_exact = {normalize_exact(c) for c in taken_cols}
    taken_base = {normalize_name(c) for c in taken_cols}

    unique_courses = exam_df[["시험인덱스", "과목"]].drop_duplicates()
    for _, r in unique_courses.iterrows():
        idx = int(r["시험인덱스"])
        course = str(r["과목"])
        course_exact = normalize_exact(course)
        course_base = normalize_name(course)
        has_section = course_exact != course_base

        if has_section:
            if course_exact in taken_exact:
                taken_idxs.append(idx)
        else:
            if course_base in taken_base:
                taken_idxs.append(idx)

    return exam_df[exam_df["시험인덱스"].isin(taken_idxs)].copy().sort_values(["주차", "start_dt", "과목"]).reset_index(drop=True)


def intervals_overlap(start_a: float, end_a: float, start_b: float, end_b: float) -> bool:
    return (start_a < end_b) and (start_b < end_a)


def normalize_room_choice(new_room) -> list[int]:
    if isinstance(new_room, (list, tuple, set)):
        return sorted(int(x) for x in new_room)
    text = str(new_room).strip()
    text = text.replace(" or ", "+").replace("/", "+").replace(",", "+")
    if "+" in text:
        return sorted(int(x.strip()) for x in text.split("+") if str(x).strip())
    if " " in text:
        parts = [x.strip() for x in text.split() if x.strip()]
        if len(parts) > 1:
            return sorted(int(float(x)) for x in parts)
    return [int(float(text))]


def format_room_choice(room_choice) -> str:
    return " or ".join(str(x) for x in normalize_room_choice(room_choice))


def format_student_room_choice(room_choice) -> str:
    rooms = normalize_room_choice(room_choice)
    if len(rooms) >= 2:
        return "추후 본인강의실 공지예정"
    return format_room_choice(rooms)


def apply_manual_moves(df_src: pd.DataFrame, manual_moves: dict) -> pd.DataFrame:
    out = df_src.copy()
    for k, mv in manual_moves.items():
        idx = int(k)
        mask = out["시험인덱스"] == idx
        if not mask.any():
            continue
        dur_min = int(out.loc[mask, "시험시간(분)"].iloc[0])
        dur_slots = max(1, int((dur_min + 29) // 30))
        room_list = normalize_room_choice(mv.get("room", mv.get("강의실", [])))
        out.loc[mask, "주차"] = int(mv["week"])
        out.loc[mask, "요일번호"] = int(mv["day"])
        out.loc[mask, "요일"] = DAY_LABELS.get(int(mv["day"]), str(mv["day"]))
        out.loc[mask, "시작슬롯"] = int(mv["start_slot"])
        out.loc[mask, "종료슬롯"] = int(mv["start_slot"]) + dur_slots
        out.loc[mask, "표시종료슬롯"] = float(int(mv["start_slot"])) + (float(dur_min) / 30.0)
        out.loc[mask, "시작"] = slot_to_time(int(mv["start_slot"]))
        out.loc[mask, "종료"] = minute_to_time(540 + int(mv["start_slot"]) * 30 + dur_min)
        out.loc[mask, "강의실목록"] = [room_list for _ in range(int(mask.sum()))]
        out.loc[mask, "강의실"] = format_room_choice(room_list)
    return out


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


def _move_test_same_assignment(candidate: dict, current_row: pd.Series) -> bool:
    current_rooms = sorted(int(x) for x in normalize_room_choice(current_row["강의실목록"]))
    candidate_rooms = sorted(int(x) for x in normalize_room_choice(candidate.get("room_combo", candidate.get("강의실", []))))
    return (
        int(candidate.get("week", current_row["주차"])) == int(current_row["주차"])
        and int(candidate.get("dnum", current_row["요일번호"])) == int(current_row["요일번호"])
        and int(candidate.get("slot", current_row["시작슬롯"])) == int(current_row["시작슬롯"])
        and candidate_rooms == current_rooms
    )


def _move_test_objective_delta(out_eval: dict) -> float:
    room_change_delta = int(out_eval.get("room_change_delta", 0))
    time_move_delta = int(out_eval.get("time_move_delta", 0))
    daily_penalty_delta = int(out_eval.get("daily_penalty_delta", 0))
    objective_delta = (
        WEIGHT_ROOM_MOVE * room_change_delta
        + WEIGHT_TIME_MOVE * time_move_delta
        + WEIGHT_DAILY * daily_penalty_delta
    )
    if room_change_delta == 0 and time_move_delta == 0 and daily_penalty_delta == 0:
        objective_delta = 0.0
    if abs(objective_delta) <= 1e-6:
        objective_delta = 0.0
    return float(objective_delta)


def _move_test_build_candidates(
    exam_df_view: pd.DataFrame,
    target_idx: int,
    student_sets: dict[int, set[int]],
    summary: dict,
    max_candidates: int = 20,
) -> list[dict]:
    target_rows = exam_df_view[exam_df_view["시험인덱스"] == int(target_idx)]
    if target_rows.empty:
        return []
    sel_row = target_rows.iloc[0]
    dur_slots = max(
        1,
        int(float(sel_row.get("표시종료슬롯", sel_row["종료슬롯"])) - float(sel_row["시작슬롯"]) + 0.999999),
    )
    enrollment = len(student_sets.get(int(target_idx), set()))
    need_room = max(1, len(normalize_room_choice(sel_row["강의실목록"])))
    allowed_weeks = [int(sel_row["fixed_week"])] if "fixed_week" in sel_row and pd.notna(sel_row.get("fixed_week")) else [int(sel_row["주차"])]

    current_rooms = normalize_room_choice(sel_row["강의실목록"])
    room_seed: list[int] = []
    for room in current_rooms:
        if int(room) not in ROOM_ORDER:
            continue
        room_idx = ROOM_ORDER.index(int(room))
        for near_idx in range(max(0, room_idx - 2), min(len(ROOM_ORDER), room_idx + 3)):
            room_seed.append(int(ROOM_ORDER[near_idx]))
    if not room_seed:
        room_seed = [int(r) for r in current_rooms] or ROOM_ORDER[:]
    room_seed = list(dict.fromkeys(room_seed))

    room_combo_candidates = []
    for combo in combinations(room_seed, need_room):
        if sum(ROOM_CAP[int(r)] for r in combo) >= enrollment:
            room_combo_candidates.append(tuple(int(r) for r in combo))
    if not room_combo_candidates:
        room_combo_candidates = [tuple(int(r) for r in current_rooms)]

    orig_day = int(sel_row["요일번호"])
    orig_start = int(sel_row["시작슬롯"])
    start_slots_to_search = [
        st_slot for st_slot in range(max(0, orig_start - 2), min(19, orig_start + 3))
        if st_slot + dur_slots <= 22
    ] or [orig_start]

    candidates: list[dict] = []
    for week in allowed_weeks:
        for dnum in [1, 2, 3, 4, 5]:
            for st_slot in start_slots_to_search:
                if st_slot + dur_slots > 22:
                    continue
                for room_combo in room_combo_candidates:
                    if len(candidates) >= max_candidates:
                        return sorted(candidates, key=lambda x: x["sort_key"])
                    out_eval = score_move_impact(
                        exam_df=exam_df_view,
                        target_idx=int(target_idx),
                        new_week=int(week),
                        new_day=int(dnum),
                        new_start=int(st_slot),
                        new_room=list(room_combo),
                        student_sets=student_sets,
                        summary=summary,
                    )
                    if not out_eval.get("feasible", False):
                        continue
                    candidate_room_set = set(int(x) for x in normalize_room_choice(room_combo))
                    current_room_set = set(int(x) for x in current_rooms)
                    candidate = {
                        "week": int(week),
                        "dnum": int(dnum),
                        "slot": int(st_slot),
                        "room_combo": list(room_combo),
                        "학생충돌수": int(out_eval.get("student_conflict_count", 0)),
                        "room_change_delta": int(out_eval.get("room_change_delta", 0)),
                        "time_move_delta": int(out_eval.get("time_move_delta", 0)),
                        "daily_penalty_delta": int(out_eval.get("daily_penalty_delta", 0)),
                        "daily_exam_increase": int(out_eval.get("daily3_increase", 0)) + int(out_eval.get("daily4_increase", 0)),
                    }
                    if _move_test_same_assignment(candidate, sel_row):
                        continue
                    candidate["objective_delta"] = _move_test_objective_delta(candidate)
                    candidate["time_changed"] = (int(dnum), int(st_slot)) != (orig_day, orig_start)
                    candidate["room_changed"] = candidate_room_set != current_room_set
                    candidate["distance_from_current"] = abs(int(dnum) - orig_day) + abs(int(st_slot) - orig_start)
                    candidate["sort_key"] = (
                        float(candidate["objective_delta"]),
                        int(candidate["daily_exam_increase"]),
                        int(bool(candidate["time_changed"])),
                        int(bool(candidate["room_changed"])),
                        int(candidate["distance_from_current"]),
                    )
                    candidates.append(candidate)
    return sorted(candidates, key=lambda x: x["sort_key"])


def _run_move_simulator_state_tests(
    base_df: pd.DataFrame,
    df_is: pd.DataFrame,
    orig_maps: dict[str, dict],
    grade_map: dict[str, str],
    summary: dict,
) -> None:
    logger = logging.getLogger("inutimetable.move_sim_tests")
    failures: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    try:
        working_df = ensure_professor_column(fill_missing_grade(add_change_columns(base_df.copy(), orig_maps, grade_map), grade_map))
        student_sets = build_exam_student_sets(working_df, df_is)
        selected_idx = None
        candidates: list[dict] = []
        for idx in working_df["시험인덱스"].astype(int).tolist():
            candidates = _move_test_build_candidates(working_df, idx, student_sets, summary)
            if candidates:
                selected_idx = int(idx)
                break
        check(selected_idx is not None, "A: 후보가 1개 이상 생성되는 과목을 찾지 못했습니다.")
        if selected_idx is None:
            raise AssertionError("no candidate source")

        selected_row = working_df[working_df["시험인덱스"] == selected_idx].iloc[0]
        check(len(candidates) > 0, "A: move_candidates가 생성되지 않았습니다.")
        check(not any(_move_test_same_assignment(c, selected_row) for c in candidates), "A: 현재 배정과 동일한 후보가 포함되었습니다.")
        check(all(int(c.get("학생충돌수", 0)) == 0 for c in candidates), "강제제약: 학생 동시시험 충돌 후보가 포함되었습니다.")

        zero_delta = {
            "room_change_delta": 0,
            "time_move_delta": 0,
            "daily_penalty_delta": 0,
        }
        check(_move_test_objective_delta(zero_delta) == 0.0, "목적함수: 변화량 0 조건에서 objective_delta가 0이 아닙니다.")

        chosen = candidates[0]
        manual_moves: dict[str, dict] = {}
        history: list[dict] = []
        prev_state = manual_moves.get(str(selected_idx))
        history.append({"idx": selected_idx, "prev": prev_state})
        manual_moves[str(selected_idx)] = {
            "week": int(chosen["week"]),
            "day": int(chosen["dnum"]),
            "start_slot": int(chosen["slot"]),
            "room": normalize_room_choice(chosen["room_combo"]),
        }
        changed_df = apply_manual_moves(base_df, manual_moves)
        changed_df = ensure_professor_column(fill_missing_grade(add_change_columns(changed_df, orig_maps, grade_map), grade_map))
        changed_row = changed_df[changed_df["시험인덱스"] == selected_idx].iloc[0]
        check(int(changed_row["주차"]) == int(chosen["week"]), "B: 변경 완료 후 주차가 display_exam_df에 반영되지 않았습니다.")
        check(int(changed_row["요일번호"]) == int(chosen["dnum"]), "B: 변경 완료 후 요일이 display_exam_df에 반영되지 않았습니다.")
        check(int(changed_row["시작슬롯"]) == int(chosen["slot"]), "B: 변경 완료 후 시작슬롯이 display_exam_df에 반영되지 않았습니다.")
        check(
            sorted(normalize_room_choice(changed_row["강의실목록"])) == sorted(normalize_room_choice(chosen["room_combo"])),
            "B: 변경 완료 후 강의실이 display_exam_df에 반영되지 않았습니다.",
        )
        check("변경상태" in changed_df.columns, "B: 변경사항 확인 탭용 변경상태 컬럼이 없습니다.")

        changed_sets = build_exam_student_sets(changed_df, df_is)
        next_candidates = _move_test_build_candidates(changed_df, selected_idx, changed_sets, summary)
        check(not any(_move_test_same_assignment(c, changed_row) for c in next_candidates), "C: 재탐색 후보가 변경 후 현재 위치를 포함했습니다.")

        other_idx = next((int(x) for x in working_df["시험인덱스"].astype(int).tolist() if int(x) != selected_idx), None)
        move_candidates_state = list(candidates)
        selected_candidate_state = dict(chosen)
        if other_idx is not None:
            move_candidates_state = []
            selected_candidate_state = None
            other_candidates = _move_test_build_candidates(changed_df, other_idx, changed_sets, summary)
            check(move_candidates_state == [], "D: 다른 과목 선택 시 move_candidates가 초기화되지 않았습니다.")
            check(selected_candidate_state is None, "D: 다른 과목 선택 시 selected_candidate가 초기화되지 않았습니다.")
            check(isinstance(other_candidates, list), "D: 다른 과목 후보 탐색 결과가 list가 아닙니다.")

        undo = history.pop()
        if undo["prev"] is None:
            manual_moves.pop(str(undo["idx"]), None)
        else:
            manual_moves[str(undo["idx"])] = undo["prev"]
        undo_df = apply_manual_moves(base_df, manual_moves)
        undo_row = undo_df[undo_df["시험인덱스"] == selected_idx].iloc[0]
        base_row = base_df[base_df["시험인덱스"] == selected_idx].iloc[0]
        check(manual_moves == {}, "E: 이전 후 마지막 manual_move가 제거되지 않았습니다.")
        check(int(undo_row["시작슬롯"]) == int(base_row["시작슬롯"]), "E: 이전 후 display_exam_df가 원본 시작슬롯으로 복구되지 않았습니다.")

        manual_moves = {str(selected_idx): dict(chosen)}
        move_candidates_state = list(candidates)
        selected_candidate_state = dict(chosen)
        manual_moves = {}
        move_candidates_state = []
        selected_candidate_state = None
        reset_df = apply_manual_moves(base_df, manual_moves)
        reset_row = reset_df[reset_df["시험인덱스"] == selected_idx].iloc[0]
        check(manual_moves == {}, "F: 초기화 후 manual_moves가 비워지지 않았습니다.")
        check(move_candidates_state == [], "F: 초기화 후 move_candidates가 비워지지 않았습니다.")
        check(selected_candidate_state is None, "F: 초기화 후 selected_candidate가 비워지지 않았습니다.")
        check(int(reset_row["시작슬롯"]) == int(base_row["시작슬롯"]), "F: 초기화 후 원본 시작슬롯으로 복구되지 않았습니다.")
    except Exception as exc:
        logger.exception("Move simulator state test raised an exception")
        failures.append(f"테스트 실행 예외: {exc}")

    for failure in failures:
        logger.error("Move simulator state test failed: %s", failure)
    if failures:
        raise AssertionError("; ".join(failures))


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
    new_rooms = normalize_room_choice(new_room)

    dur_slots = float(trow["표시종료슬롯"]) - float(trow["시작슬롯"])
    new_end = float(new_start) + dur_slots

    # 1) 강의실 중복 체크
    room_conflicts = []
    others = base[base["시험인덱스"] != target_idx]
    for _, r in others.iterrows():
        if int(r["주차"]) != int(new_week) or int(r["요일번호"]) != int(new_day):
            continue
        rooms = set(normalize_room_choice(r.get("강의실목록", r.get("강의실", []))))
        if not (rooms & set(new_rooms)):
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
    sim.loc[mask, "강의실목록"] = [list(new_rooms)]
    sim.loc[mask, "강의실"] = " ".join(str(x) for x in new_rooms)

    # 변경 건수/영향
    time_changed = int((int(trow["주차"]) != int(new_week)) or (int(trow["요일번호"]) != int(new_day)) or (int(trow["시작슬롯"]) != int(new_start)))
    room_changed = int(set(new_rooms) != set(normalize_room_choice(trow.get("강의실목록", trow.get("강의실", [])))))
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
    room_change_delta = new_room_move - base_room_move
    time_move_delta = new_time_move - base_time_move
    daily_penalty_delta = new_daily_penalty - base_daily_penalty

    objective_delta = (
        WEIGHT_ROOM_MOVE * room_change_delta
        + WEIGHT_TIME_MOVE * time_move_delta
        + WEIGHT_DAILY * daily_penalty_delta
    )
    if abs(objective_delta) <= 1e-6:
        objective_delta = 0.0
    new_obj = base_obj + objective_delta

    return {
        "feasible": True,
        "affected_students": affected_students,
        "student_conflict_count": 0,
        "daily3_increase": after_3 - before_3,
        "daily4_increase": after_4 - before_4,
        "daily_penalty_delta": daily_penalty_delta,
        "room_change_delta": room_change_delta,
        "time_move_delta": time_move_delta,
        "objective_before": base_obj,
        "objective_after": new_obj,
        "objective_delta": objective_delta,
    }


def score_move_impact_relaxed(
    exam_df: pd.DataFrame,
    target_idx: int,
    new_week: int,
    new_day: int,
    new_start: int,
    new_room: int,
    student_sets: dict[int, set[int]],
    summary: dict,
) -> dict:
    """완화 평가: 강의실 중복만 막고(학생 동시시험은 경고치로만 계산) 후보를 보여준다."""
    base = exam_df.copy()
    trow = base[base["시험인덱스"] == target_idx]
    if trow.empty:
        return {"feasible": False, "reason": "대상 과목을 찾지 못했습니다."}
    trow = trow.iloc[0]
    new_rooms = normalize_room_choice(new_room)
    dur_slots = float(trow["표시종료슬롯"]) - float(trow["시작슬롯"])
    new_end = float(new_start) + dur_slots
    if float(new_start) < 0 or float(new_end) > 22:
        return {"feasible": False, "reason": "시간 범위를 벗어납니다."}

    others = base[base["시험인덱스"] != target_idx]
    for _, r in others.iterrows():
        if int(r["주차"]) != int(new_week) or int(r["요일번호"]) != int(new_day):
            continue
        if not (set(new_rooms) & set(normalize_room_choice(r.get("강의실목록", r.get("강의실", []))))):
            continue
        if intervals_overlap(float(new_start), float(new_end), float(r["시작슬롯"]), float(r["표시종료슬롯"])):
            return {"feasible": False, "reason": "강의실 중복"}

    # 학생 동시시험은 제약으로 막지 않고 경고치로만 계산
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

    strict = score_move_impact(
        exam_df=exam_df,
        target_idx=target_idx,
        new_week=new_week,
        new_day=new_day,
        new_start=new_start,
        new_room=new_room,
        student_sets=student_sets,
        summary=summary,
    )
    if strict.get("feasible", False):
        return strict

    return {
        "feasible": True,
        "relaxed": True,
        "affected_students": len(target_students),
        "daily3_increase": 0,
        "daily4_increase": 0,
        "room_change_delta": 0,
        "time_move_delta": 0,
        "objective_before": float(summary.get("objective", 0.0)),
        "objective_after": float(summary.get("objective", 0.0)),
        "objective_delta": 0.0,
        "student_conflict_count": int(student_conflict_count),
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
                    if w == cur_week and d == cur_day and st == cur_start and room in set(normalize_room_choice(target["강의실목록"])):
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
        norm_grade = normalize_grade_value(g)
        if norm_grade == "-":
            continue
        exact_key = normalize_exact(cname)
        base_key = normalize_name(cname)
        matched_course = None
        for course, aliases in ALIASES.items():
            if exact_key == normalize_exact(course) or base_key == normalize_name(course):
                matched_course = course
                break
            if any(exact_key == normalize_exact(alias) or base_key == normalize_name(alias) for alias in aliases):
                matched_course = course
                break

        keys = {exact_key, base_key}
        if matched_course is not None:
            keys.add(normalize_exact(matched_course))
            keys.add(normalize_name(matched_course))
            for alias in ALIASES.get(matched_course, [matched_course]):
                keys.add(normalize_exact(alias))
                keys.add(normalize_name(alias))

        for key in keys:
            if key and key not in grade_map:
                grade_map[key] = norm_grade
    return grade_map


def add_change_columns(df: pd.DataFrame, orig_maps: dict[str, dict], grade_map: dict[str, str] | None = None) -> pd.DataFrame:
    orig_base = orig_maps.get("base", {})
    orig_exact = orig_maps.get("exact", {})
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
        exact_key = normalize_exact(r.get("과목", r.get("과목명", "")))
        meta = orig_exact.get(exact_key)
        if meta is None:
            meta = orig_base.get(key, {"slots": set(), "weekslots": set(), "rooms": set(), "grade": "-"})

        cur_week = int(r["주차"])
        cur_day = int(r["요일번호"])
        cur_start = int(r["시작슬롯"])
        cur_rooms = set(normalize_room_choice(r.get("강의실목록", r.get("강의실", []))))

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
        cur_rooms = set(normalize_room_choice(r.get("강의실목록", r.get("강의실", []))))

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
    # rowspan 기반으로 한 블록(시간 길이만큼 1개 셀)로 렌더링한다.
    slots = list(range(0, 22))
    df_w = df_student[df_student["주차"] == target_week].copy()

    starts: dict[tuple[int, str], dict] = {}
    covered: set[tuple[int, str]] = set()
    for _, r in df_w.iterrows():
        day = str(r.get("요일", ""))
        if day not in DAY_ORDER:
            continue
        s0 = int(r.get("시작슬롯", 0))
        s1 = int(float(r.get("표시종료슬롯", r.get("종료슬롯", s0))) + 0.999999)
        s1 = min(22, max(s0 + 1, s1))
        starts[(s0, day)] = {"row": r, "span": s1 - s0}
        for s in range(s0 + 1, s1):
            covered.add((s, day))

    html_rows = []
    for s in slots:
        cells = [f"<td class='time-col'>{slot_to_time(s)}</td>"]
        for d in DAY_ORDER:
            if (s, d) in covered:
                continue
            if (s, d) in starts:
                info = starts[(s, d)]
                r = info["row"]
                span = int(info["span"])
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
                cells.append(f"<td class='exam' rowspan='{span}'>{text_main}</td>")
            else:
                cells.append("<td class='empty'></td>")
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
        room_df = exam_df[exam_df["강의실목록"].apply(lambda xs: int(room) in set(normalize_room_choice(xs)))].copy()
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
        ["시험 집중도 제한(하루 최대 시험 수 기준)", str(D_MAX)],
        ["시험 집중도 제한(연속 시험 시간 기준)", str(T_MAX)],
        ["강의실 변경 합", str(int(summary.get("room_move_sum", 0)))],
        ["시간 이동 합", str(int(summary.get("time_move_sum", 0)))],
        ["하루 시험 수 증가 합", str(int(summary.get("daily_penalty_sum", 0)))],
        ["학생 동시시험 충돌", str(int(summary.get("overlap_violation", 0)))],
        ["같은과목 분반 연속배정 충돌", str(int(summary.get("section_overlap_violation", 0)))],
        ["하루 4시험 충돌", str(int(summary.get("daily4_count", 0)))],
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
            "(8)": "시험 집중도 계산",
            "(9)": "강의실 변경 반영",
            "(10)": "시간 변경 반영",
            "(11)": "시험 집중도 제한",
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
    out["TC"] = fallback["TimeMove_i"]
    out["RC"] = fallback["RoomChange_i"]
    return out.reset_index(drop=True)


def fill_missing_grade(df: pd.DataFrame, grade_map: dict[str, str]) -> pd.DataFrame:
    out = df.copy()
    if "학년" not in out.columns:
        out["학년"] = "-"
    filled = []
    for _, row in out.iterrows():
        key = str(row.get("정규과목", "")).strip()
        if not key:
            key = normalize_name(row.get("과목", ""))
        grade_val = grade_map.get(key, "-")
        if normalize_grade_value(grade_val) == "-":
            val = str(row.get("학년", "")).strip()
            norm_val = normalize_grade_value(val)
            if norm_val != "-":
                grade_val = norm_val
            else:
                grade_val = fallback_grade_for_course(row.get("과목", row.get("과목명", "")))
        filled.append(grade_val)
    out["학년"] = [normalize_grade_value(v) for v in filled]
    return out


def dataframe_to_html_table(df: pd.DataFrame, highlight_cols: list[str] | None = None) -> str:
    highlight_cols = highlight_cols or []
    parts = ["<div class='result-table-wrap'><table class='result-table'><thead><tr>"]
    for col in df.columns:
        parts.append(f"<th>{html.escape(str(col))}</th>")
    parts.append("</tr></thead><tbody>")

    for _, row in df.iterrows():
        parts.append("<tr>")
        row_status = str(row.get("변경상태", "")).strip()
        for col in df.columns:
            val = "" if pd.isna(row[col]) else str(row[col])
            cls = ""
            if col in highlight_cols:
                status_src = row_status if col == "변경상태" else val
                if status_src == "유지" or val == "유지":
                    cls = " class='status-keep'"
                elif "시간+강의실" in status_src or ("시간" in status_src and "강의실" in status_src):
                    cls = " class='status-both'"
                elif "시간" in status_src:
                    cls = " class='status-time'"
                elif "강의실" in status_src:
                    cls = " class='status-room'"
                elif "변경" in val and val != "유지":
                    cls = " class='change'"
            parts.append(f"<td{cls}>{html.escape(val)}</td>")
        parts.append("</tr>")
    parts.append("</tbody></table></div>")
    return "".join(parts)


def overall_calendar_grade_class(value) -> str:
    grade = normalize_grade_value(value)
    if grade == "1학년":
        return "overall-grade-1"
    if grade == "2학년":
        return "overall-grade-2"
    if grade == "3학년":
        return "overall-grade-3"
    if grade == "4학년":
        return "overall-grade-4"
    return "overall-grade-x"


def build_overall_calendar_html(
    df_src: pd.DataFrame,
    target_week: int,
    selected_exam_idx: int | None = None,
    clickable: bool = False,
) -> str:
    slot_height = 36
    slot_count = 22
    df_w = df_src[df_src["주차"] == target_week].copy()
    if df_w.empty:
        return "<div class='candidate-card'><div class='candidate-card-title'>안내</div><div class='candidate-card-sub'>해당 주차 시험이 없습니다.</div></div>"
    df_w = df_w[df_w["요일번호"].isin([1, 2, 3, 4, 5])].copy()
    if df_w.empty:
        return "<div class='candidate-card'><div class='candidate-card-title'>안내</div><div class='candidate-card-sub'>해당 주차 평일 시험이 없습니다.</div></div>"
    df_w["표시종료슬롯"] = pd.to_numeric(df_w["표시종료슬롯"], errors="coerce").fillna(df_w["종료슬롯"])
    day_events: dict[str, list[dict]] = {day: [] for day in DAY_ORDER}
    for _, r in df_w.sort_values(["요일번호", "시작슬롯", "표시종료슬롯", "과목명"]).iterrows():
        day = str(r.get("요일", ""))
        if day not in DAY_ORDER:
            continue
        event = r.to_dict()
        event["start_slot_float"] = float(r.get("시작슬롯", 0))
        end_slot_float = float(r.get("표시종료슬롯", r.get("종료슬롯", 0)))
        event["end_slot_float"] = max(event["start_slot_float"] + 1.0, min(float(slot_count), end_slot_float))
        day_events[day].append(event)

    legend_items = [
        ("1학년", "overall-grade-1"),
        ("2학년", "overall-grade-2"),
        ("3학년", "overall-grade-3"),
        ("4학년", "overall-grade-4"),
    ]
    html_parts = ["<div class='overall-legend'>"]
    for label, cls in legend_items:
        html_parts.append(
            "<div class='overall-legend-item'>"
            f"<span class='overall-legend-swatch {cls}'></span>"
            f"<span>{html.escape(label)}</span>"
            "</div>"
        )
    html_parts.append("</div>")

    day_headers = []
    week_start = WEEK_START_DATE.get(int(target_week))
    for idx, day_label in enumerate(DAY_ORDER):
        if week_start is not None:
            day_date = week_start + timedelta(days=idx)
            day_headers.append(f"{day_label}<br>{day_date.month}/{day_date.day}")
        else:
            day_headers.append(day_label)
    total_height = slot_count * slot_height

    def build_day_column(events: list[dict]) -> str:
        if not events:
            return f"<div class='overall-abs-day-col' style='height:{total_height}px;'></div>"

        groups: list[list[dict]] = []
        current_group: list[dict] = []
        current_group_end = -1.0
        for event in events:
            start = float(event["start_slot_float"])
            end = float(event["end_slot_float"])
            if not current_group or start < current_group_end:
                current_group.append(event)
                current_group_end = max(current_group_end, end)
            else:
                groups.append(current_group)
                current_group = [event]
                current_group_end = end
        if current_group:
            groups.append(current_group)

        event_divs: list[str] = []
        for group in groups:
            lane_endings: list[float] = []
            lane_by_exam: dict[int, int] = {}
            for event in group:
                start = float(event["start_slot_float"])
                end = float(event["end_slot_float"])
                lane_idx = None
                for idx, lane_end in enumerate(lane_endings):
                    if lane_end <= start:
                        lane_idx = idx
                        lane_endings[idx] = end
                        break
                if lane_idx is None:
                    lane_endings.append(end)
                    lane_idx = len(lane_endings) - 1
                lane_by_exam[int(event["시험인덱스"])] = lane_idx

            lane_count = max(1, len(lane_endings))
            width_pct = 100.0 / lane_count
            for event in group:
                lane_idx = lane_by_exam[int(event["시험인덱스"])]
                left_pct = lane_idx * width_pct
                top_px = float(event["start_slot_float"]) * slot_height
                height_px = max(42.0, (float(event["end_slot_float"]) - float(event["start_slot_float"])) * slot_height - 4.0)
                grade_cls = overall_calendar_grade_class(event.get("학년", "-"))
                selected_style = "border:2px solid #1d4ed8; box-shadow:0 0 0 2px rgba(37,99,235,.18);" if selected_exam_idx is not None and int(event["시험인덱스"]) == int(selected_exam_idx) else ""
                course = html.escape(str(event.get("과목명", event.get("과목", ""))))
                room = html.escape(str(event.get("강의실", "-")))
                time_text = html.escape(f"{event.get('시작', '-')}~{event.get('종료', '-')}")
                event_body = (
                    f"<div class='overall-abs-title'>{course}</div>"
                    f"<div class='overall-abs-sub'>{room}</div>"
                    f"<div class='overall-abs-sub'>{time_text}</div>"
                )
                if clickable:
                    event_body = (
                        f"<a class='overall-abs-link' href='?sim_pick={int(event['시험인덱스'])}&sim_week={int(target_week)}'>"
                        f"{event_body}</a>"
                    )
                event_divs.append(
                    f"<div class='overall-abs-event {grade_cls}' "
                    f"style='top:{top_px:.1f}px; left:calc({left_pct:.6f}% + 2px); width:calc({width_pct:.6f}% - 4px); height:{height_px:.1f}px; {selected_style}'>"
                    f"{event_body}"
                    "</div>"
                )

        return f"<div class='overall-abs-day-col' style='height:{total_height}px;'>{''.join(event_divs)}</div>"

    time_labels = []
    for slot in range(0, slot_count + 1):
        top_px = slot * slot_height
        label = slot_to_time(slot) if slot < slot_count else "20:00"
        time_labels.append(
            f"<div class='overall-abs-time-label' style='top:{top_px}px'>{html.escape(label)}</div>"
        )

    day_columns = [build_day_column(day_events[day]) for day in DAY_ORDER]
    return (
        "<div class='overall-legend'>"
        + "".join(html_parts[1:-1])
        + "</div>"
        + "<div class='overall-abs-wrap'><div class='overall-abs-shell'>"
        + "<div class='overall-abs-header'><div class='overall-abs-head'>시간</div>"
        + "".join(f"<div class='overall-abs-head'>{h}</div>" for h in day_headers)
        + "</div>"
        + "<div class='overall-abs-body'>"
        + f"<div class='overall-abs-time-axis' style='height:{total_height}px'>{''.join(time_labels)}</div>"
        + "".join(day_columns)
        + "</div></div></div>"
    )


def render_calendar_grid(df_student: pd.DataFrame, target_week: int):
    st.markdown(f"#### {target_week}주차 캘린더형 시험시간표")
    table_html = build_overall_calendar_html(df_student, target_week)
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
    room_df = exam_df_src[exam_df_src["강의실목록"].apply(lambda xs: room_no in set(normalize_room_choice(xs)))].copy()
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
            ("총 시험 수", a),
            ("하루 최대 시험 수", b),
            ("시험 없는 날짜 수", c),
            ("첫 시험", d),
            ("마지막 시험", e),
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
        st.markdown(_card_html("0", "0", "15", "-", "-"), unsafe_allow_html=True)
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

    all_exam_dates = set()
    for week_value, week_start in WEEK_START_DATE.items():
        for day_offset in range(5):
            all_exam_dates.add((week_value, (week_start + timedelta(days=day_offset)).strftime("%m/%d")))
    taken_dates = set((int(r["주차"]), str(r["날짜"])) for _, r in df_student.iterrows())
    no_exam_date_count = max(0, len(all_exam_dates - taken_dates))

    st.markdown(
        _card_html(
            str(count_exam),
            str(max_per_day),
            str(no_exam_date_count),
            first_exam.strftime("%m/%d %H:%M"),
            last_exam.strftime("%m/%d %H:%M"),
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
    weeks_present = sorted({int(x) for x in df["주차"].unique().tolist()})
    week_label = "/".join([f"{w}주차" for w in weeks_present]) if weeks_present else "주차 없음"
    ax.set_title(f"학번 {sid} 시험 캘린더 요약 ({week_label})", fontsize=14, pad=10)
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


def make_google_calendar_url(row: pd.Series, sid: str) -> str:
    start = pd.to_datetime(row["start_dt"]).strftime("%Y%m%dT%H%M%S")
    end = pd.to_datetime(row["end_dt"]).strftime("%Y%m%dT%H%M%S")
    title = quote(f"{row.get('과목명', row.get('과목', '시험'))} 시험")
    location = quote(str(row.get("강의실", "-")))
    details = quote(f"INUTimetable 시험시간표 / 학번 {sid}")
    return (
        "https://calendar.google.com/calendar/render?action=TEMPLATE"
        f"&text={title}"
        f"&dates={start}/{end}"
        f"&location={location}"
        f"&details={details}"
    )


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
if "manual_moves" not in st.session_state:
    st.session_state.manual_moves = {}
if "manual_move_history" not in st.session_state:
    st.session_state.manual_move_history = []
if "sim_selected_idx" not in st.session_state:
    st.session_state.sim_selected_idx = None
if "move_candidates" not in st.session_state:
    st.session_state["move_candidates"] = []
if "move_candidate_reasons" not in st.session_state:
    st.session_state["move_candidate_reasons"] = {}
if "move_candidate_meta" not in st.session_state:
    st.session_state["move_candidate_meta"] = None
if "selected_candidate" not in st.session_state:
    st.session_state["selected_candidate"] = None
if "move_apply_notice" not in st.session_state:
    st.session_state["move_apply_notice"] = ""
if "move_search_notice" not in st.session_state:
    st.session_state["move_search_notice"] = ""

exam_df = build_exam_df(payload)
orig_maps = build_original_map(df_ot)
grade_map = build_grade_map_from_courseen(df_courseen)
base_exam_df = add_change_columns(exam_df.copy(), orig_maps, grade_map)
base_exam_df = fill_missing_grade(base_exam_df, grade_map)
base_exam_df = ensure_professor_column(base_exam_df)
display_exam_df = apply_manual_moves(base_exam_df, st.session_state.manual_moves)
display_exam_df = add_change_columns(display_exam_df, orig_maps, grade_map)
display_exam_df = fill_missing_grade(display_exam_df, grade_map)
display_exam_df = ensure_professor_column(display_exam_df)
opt_summary_df = build_optimization_summary_df(payload)
verify_df = build_verify_df(payload)
decision_df = build_decision_df(payload, display_exam_df)
report_images, report_dir = load_report_images()
if report_dir is None:
    report_dir = BASE_DIR / "결과_리포트"
if not report_images:
    generate_fallback_report_images(display_exam_df, payload.get("summary", {}), report_dir)
    report_images, report_dir = load_report_images()

summary = payload.get("summary", {})
if os.environ.get("INUTIMETABLE_RUN_SIM_TESTS") == "1":
    logging.basicConfig(level=logging.ERROR)
    _run_move_simulator_state_tests(base_exam_df, df_is, orig_maps, grade_map, summary)

# -------------------------------------------------
# UI
# -------------------------------------------------
st.markdown(
    """
    <div class="compact-header">
      <div class="compact-header-title">INUTimetable</div>
      <div class="compact-header-desc">충돌 최소화 · 학생 부담 완화 시험시간표</div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("메뉴")
    menu = st.radio("페이지 선택", ["최적화 결과", "개인 조회", "이동 시뮬레이터", "변경사항 확인"], index=0)
    st.markdown("---")
    st.caption(f"결과 파일: {payload_path}")
    st.caption(f"IS 파일: {is_path}")
    if ot_path is not None:
        st.caption(f"OT 파일: {ot_path}")
    if courseen_path is not None:
        st.caption(f"CourseEn 파일: {courseen_path}")

if menu != "최적화 결과":
    g1, g2, g3, g4, g5 = st.columns(5)
    g1.metric("전체 시험 과목 수", int(display_exam_df["과목"].nunique()))
    used_rooms = set(sum([normalize_room_choice(x) for x in display_exam_df["강의실목록"].tolist()], []))
    g2.metric("사용/후보 강의실 수", f"{len(used_rooms)}/{len(ROOM_ORDER)}")
    g3.metric("학생 충돌 여부", "없음" if int(summary.get("overlap_violation", 0)) == 0 else "있음")
    g4.metric("분반 연속배정 충돌", "없음" if int(summary.get("section_overlap_violation", 0)) == 0 else "있음")
    g5.metric("전체 배치 점수", f"{float(summary.get('objective', 0)):.4f}")

if menu == "개인 조회":
    st.subheader("개인 조회")
    lookup_type = st.radio(
        "조회 유형",
        ["학번으로 시험 시간표 검색", "교수명으로 시험 시간표 검색"],
        horizontal=True,
        key="personal_lookup_type",
    )

    if lookup_type == "학번으로 시험 시간표 검색":

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
                df_student = student_exam_df(display_exam_df, df_is, row_idx)
                df_student = add_change_columns_student(df_student, df_is, row_idx, orig_maps, grade_map)
                df_student = fill_missing_grade(df_student, grade_map)
                df_student_display = df_student.copy()
                if "강의실목록" in df_student_display.columns:
                    df_student_display["강의실"] = df_student_display["강의실목록"].apply(format_student_room_choice)

                student_summary_cards(df_student_display)

                week_label = st.radio(
                    "주차 선택",
                    ["7주차", "8주차", "9주차"],
                    horizontal=True,
                    key="week_selector_radio",
                )
                cur_week = int(str(week_label).replace("주차", ""))
                st.markdown(f"### 현재 페이지: {cur_week}주차")
                try:
                    render_calendar_grid(df_student_display, cur_week)
                except Exception:
                    st.warning("해당 주차 렌더링 중 문제가 있어 빈 시간표로 표시합니다.")
                    render_calendar_grid(pd.DataFrame(columns=df_student_display.columns), cur_week)

                st.markdown("#### 시험 상세 표")
                show_cols = [
                    "과목명", "학년", "주차", "요일", "날짜", "시작", "종료", "시험시간(분)", "강의실",
                    "원래시간(내분반)", "원래강의실(내분반)", "시간변경여부", "강의실변경여부",
                ]
                for col in show_cols:
                    if col not in df_student_display.columns:
                        df_student_display[col] = "-"
                view_df = df_student_display[show_cols].copy()
                st.markdown(
                    dataframe_to_html_table(
                        view_df,
                        highlight_cols=["시간변경여부", "강의실변경여부"],
                    ),
                    unsafe_allow_html=True,
                )

                # 개인 시간표 저장
                png_bytes = make_student_calendar_png(df_student_display, sid)
                if png_bytes is not None:
                    st.download_button(
                        "캘린더 이미지 저장(PNG, 전체 주차)",
                        data=png_bytes,
                        file_name=f"student_{sid}_calendar.png",
                        mime="image/png",
                    )
                st.download_button(
                    "시간표 CSV 저장",
                    data=df_student_display[show_cols].to_csv(index=False).encode("utf-8-sig"),
                    file_name=f"student_{sid}_timetable.csv",
                    mime="text/csv",
                )
                st.download_button(
                    "캘린더(.ics) 저장",
                    data=make_student_calendar_ics(df_student_display, sid),
                    file_name=f"student_{sid}_exam_calendar.ics",
                    mime="text/calendar",
                )
                st.caption("iPhone에서는 ICS 미리보기 대신 아래 Google Calendar 링크로 바로 추가할 수도 있습니다.")

                st.markdown("#### Google Calendar 바로 추가")
                for _, row in df_student_display.sort_values(["start_dt", "과목명"]).iterrows():
                    gc_url = make_google_calendar_url(row, sid)
                    left_gc, right_gc = st.columns([4, 1.3])
                    with left_gc:
                        st.markdown(
                            f"**{row['과목명']}**  \n"
                            f"{row['요일']} {row['시작']}~{row['종료']} / {row['강의실']}"
                        )
                    with right_gc:
                        st.markdown(f"[Google Calendar에 추가]({gc_url})")

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

    else:
        st.markdown("#### 교수명으로 시험 시간표 검색")
        all_professor_options = sorted(
            [p for p in display_exam_df.get("교수", pd.Series(dtype=str)).dropna().astype(str).unique().tolist() if p and p != "미지정"]
        )
        if not all_professor_options:
            st.info("등록된 교수 정보가 없습니다.")
        else:
            professor_query = st.text_input("교수명 검색", value="", key="professor_lookup_query")
            professor_options = [
                name for name in all_professor_options
                if not professor_query.strip() or professor_query.strip() in name
            ]
            if not professor_options:
                st.info("검색 조건에 맞는 교수가 없습니다.")
            else:
                selected_professor = st.selectbox("검색 결과에서 선택", professor_options, key="professor_lookup_select")
                df_professor = display_exam_df[display_exam_df["교수"].astype(str) == str(selected_professor)].copy()
                df_professor = df_professor.sort_values(["주차", "요일번호", "시작슬롯", "과목명"]).reset_index(drop=True)

                p1, p2 = st.columns(2)
                p1.metric("담당 시험 수", len(df_professor))
                p2.metric("담당 과목 수", df_professor["과목명"].nunique() if not df_professor.empty else 0)

                if df_professor.empty:
                    st.info("해당 교수의 담당 시험이 없습니다.")
                else:
                    st.markdown("#### 담당 과목 목록")
                    st.write(", ".join(df_professor["과목명"].drop_duplicates().astype(str).tolist()))

                    week_options = [f"{w}주차" for w in [7, 8, 9] if int(w) in set(df_professor["주차"].astype(int).tolist())]
                    if not week_options:
                        week_options = ["7주차", "8주차", "9주차"]
                    professor_week_label = st.radio(
                        "주차 선택",
                        week_options,
                        horizontal=True,
                        key="professor_week_selector_radio",
                    )
                    professor_week = int(str(professor_week_label).replace("주차", ""))
                    render_calendar_grid(df_professor, professor_week)

                    professor_cols = ["교수", "과목명", "주차", "요일", "시작", "종료", "강의실"]
                    for col in professor_cols:
                        if col not in df_professor.columns:
                            df_professor[col] = "-"
                    st.markdown("#### 담당 시험 상세 표")
                    st.markdown(
                        dataframe_to_html_table(df_professor[professor_cols].copy()),
                        unsafe_allow_html=True,
                    )
elif menu == "이동 시뮬레이터":
    st.subheader("이동 시뮬레이터")
    st.info("이동 시뮬레이터는 최적화된 시험시간표에서 특정 시험을 선택한 뒤, 학생 충돌·강의실 중복·수용인원 조건을 만족하는 이동 후보를 탐색하고 변경 사항을 반영하는 기능입니다.")
    exam_df_view = display_exam_df.copy()
    exam_df_view["학년정규화"] = normalize_grade_series(exam_df_view.get("학년", pd.Series(["-"] * len(exam_df_view))))

    qp = st.query_params
    qp_pick_raw = qp.get("sim_pick")
    qp_week_raw = qp.get("sim_week")
    qp_pick = int(qp_pick_raw) if str(qp_pick_raw or "").strip().isdigit() else None
    qp_week = int(qp_week_raw) if str(qp_week_raw or "").strip().isdigit() and int(qp_week_raw) in [7, 8, 9] else None
    qp_sig = f"{qp_pick}|{qp_week}"
    if st.session_state.get("sim_last_pick_qp") != qp_sig:
        st.session_state["sim_last_pick_qp"] = qp_sig
        if qp_week is not None:
            st.session_state["sim_week_view"] = f"{qp_week}주차"
        if qp_pick is not None:
            st.session_state.sim_selected_idx = qp_pick

    sim_week_view = st.radio("주차 선택", ["7주차", "8주차", "9주차"], horizontal=True, key="sim_week_view")

    sim_week_num = int(str(sim_week_view).replace("주차", ""))
    target_grade = "전체"
    selected_course_name = "전체"

    # 캘린더는 항상 수동 변경이 반영된 전체 시간표를 기준으로 표시한다.
    # 과목 선택값은 필터가 아니라 블록 강조용으로만 사용한다.
    calendar_src = display_exam_df.copy()
    calendar_src["학년정규화"] = normalize_grade_series(calendar_src.get("학년", pd.Series(["-"] * len(calendar_src))))
    calendar_src = calendar_src.sort_values(["주차", "요일번호", "시작슬롯", "과목명"]).reset_index(drop=True)

    selected_course_row = None
    if st.session_state.get("sim_selected_idx") is not None:
        selected_pool = exam_df_view[exam_df_view["시험인덱스"] == int(st.session_state["sim_selected_idx"])]
        if not selected_pool.empty:
            selected_course_row = selected_pool.sort_values(["주차", "요일번호", "시작슬롯"]).iloc[0]

    display_week_num = sim_week_num

    current_filter_sig = f"{sim_week_num}|{st.session_state.get('sim_selected_idx')}"
    if st.session_state.get("sim_filter_sig") != current_filter_sig:
        st.session_state.sim_filter_sig = current_filter_sig
        st.session_state["move_candidates"] = []
        st.session_state["move_candidate_reasons"] = {}
        st.session_state["selected_candidate"] = None
        st.session_state["move_candidate_meta"] = None

    selected_exam_idx_for_calendar = None
    if selected_course_row is not None:
        selected_exam_idx_for_calendar = int(selected_course_row["시험인덱스"])

    selectable_all = exam_df_view.copy()
    selectable_all["_week_priority"] = selectable_all["주차"].astype(int).apply(lambda x: 0 if x == int(sim_week_num) else 1)
    selectable_all = selectable_all.sort_values(["_week_priority", "주차", "요일번호", "시작슬롯", "과목명"]).reset_index(drop=True)
    pick_options = []
    if not selectable_all.empty:
        for _, r in selectable_all.iterrows():
            label = f"{r['과목명']} | {r['요일']} {r['시작']}~{r['종료']} | {r['강의실']}"
            pick_options.append((label, int(r["시험인덱스"])))
        pre_label_to_idx = {label: idx for label, idx in pick_options}
        current_pick_label = st.session_state.get("sim_pick_exam")
        if current_pick_label in pre_label_to_idx:
            st.session_state.sim_selected_idx = int(pre_label_to_idx[current_pick_label])
            selected_exam_idx_for_calendar = int(pre_label_to_idx[current_pick_label])
    sel_idx: int | None = None
    sim_day_no: int | None = None
    sim_start_slot: int | None = None
    sim_room_choice: list[int] | None = None
    chosen_row = None

    def _candidate_meta(row_like, current_row) -> dict:
        row = row_like.to_dict() if hasattr(row_like, "to_dict") else dict(row_like)
        old_day = int(current_row["요일번호"])
        old_start = int(current_row["시작슬롯"])
        new_day = int(row.get("dnum", old_day))
        new_start = int(row.get("slot", old_start))
        old_rooms = set(int(x) for x in normalize_room_choice(current_row["강의실목록"]))
        new_rooms = set(int(x) for x in normalize_room_choice(row.get("room_combo", row.get("강의실", []))))
        daily_change = int(row.get("하루3개증가", 0)) + int(row.get("하루4개증가", 0))
        time_changed = (old_day, old_start) != (new_day, new_start)
        room_changed = old_rooms != new_rooms
        dmax_violation = abs(new_day - old_day) > D_MAX
        tmax_violation = abs(new_start - old_start) > T_MAX
        room_change_delta = int(row.get("room_change_delta", 1 if room_changed else 0))
        time_move_delta = int(row.get("time_move_delta", 1 if time_changed else 0))
        daily_penalty_delta = int(row.get("daily_penalty_delta", 0))
        objective_delta = (
            WEIGHT_ROOM_MOVE * room_change_delta
            + WEIGHT_TIME_MOVE * time_move_delta
            + WEIGHT_DAILY * daily_penalty_delta
        )
        if room_change_delta == 0 and time_move_delta == 0 and daily_penalty_delta == 0:
            objective_delta = 0.0
        if abs(objective_delta) <= 1e-6:
            objective_delta = 0.0
        return {
            "time_changed": bool(row.get("time_changed", time_changed)),
            "room_changed": bool(row.get("room_changed", room_changed)),
            "daily_exam_increase": int(row.get("daily_exam_increase", daily_change)),
            "daily_penalty_delta": daily_penalty_delta,
            "room_change_delta": room_change_delta,
            "time_move_delta": time_move_delta,
            "dmax_violation": bool(row.get("dmax_violation", dmax_violation)),
            "tmax_violation": bool(row.get("tmax_violation", tmax_violation)),
            "objective_increase": objective_delta > 1e-6,
            "objective_delta": objective_delta,
        }

    def _is_same_assignment(row_like, current_row) -> bool:
        row = row_like.to_dict() if hasattr(row_like, "to_dict") else dict(row_like)
        current_rooms = sorted(int(x) for x in normalize_room_choice(current_row["강의실목록"]))
        candidate_rooms = sorted(int(x) for x in normalize_room_choice(row.get("room_combo", row.get("강의실", []))))
        return (
            int(row.get("week", current_row["주차"])) == int(current_row["주차"])
            and int(row.get("dnum", current_row["요일번호"])) == int(current_row["요일번호"])
            and int(row.get("slot", current_row["시작슬롯"])) == int(current_row["시작슬롯"])
            and candidate_rooms == current_rooms
        )

    def _candidate_sort_key(row_like, current_row):
        row = row_like.to_dict() if hasattr(row_like, "to_dict") else dict(row_like)
        meta = _candidate_meta(row, current_row)
        distance = int(
            row.get(
                "distance_from_current",
                abs(int(row.get("dnum", current_row["요일번호"])) - int(current_row["요일번호"]))
                + abs(int(row.get("slot", current_row["시작슬롯"])) - int(current_row["시작슬롯"])),
            )
        )
        return (
            float(meta["objective_delta"]),
            int(meta["daily_exam_increase"]),
            int(bool(meta["time_changed"])),
            int(bool(meta["room_changed"])),
            distance,
        )

    def _candidate_reason_text(meta: dict) -> str:
        reasons = []
        if not meta["objective_increase"]:
            reasons.append("목적함수 변화 최소")
        if meta["daily_exam_increase"] == 0:
            reasons.append("하루 시험 수 증가 없음")
        if not meta["time_changed"]:
            reasons.append("기존 시간 유지")
        if not meta["room_changed"]:
            reasons.append("기존 강의실 유지")
        return " / ".join(reasons) if reasons else "강제제약 만족 후보"

    def _badge_html(label: str, level: str) -> str:
        return f"<span class='sim-badge {level}'>{html.escape(label)}</span>"

    def _objective_status_text(objective_delta: float) -> str:
        if objective_delta > 1e-6:
            return f"목적함수 증가 (Δ {objective_delta:+.4f})"
        if objective_delta < -1e-6:
            return f"목적함수 감소 (Δ {objective_delta:+.4f})"
        return "목적함수 변화 없음 (Δ +0.0000)"

    with st.container():
        st.caption(f"현재 적용된 수동 변경: {len(st.session_state.manual_moves)}건")
        if st.session_state.get("move_apply_notice"):
            st.success(st.session_state["move_apply_notice"])
            st.session_state["move_apply_notice"] = ""
        if st.session_state.get("move_search_notice"):
            st.info(st.session_state["move_search_notice"])
            st.session_state["move_search_notice"] = ""

        calendar_slot = st.empty()

        if not pick_options:
            calendar_week_src = calendar_src[calendar_src["주차"] == display_week_num].copy()
            calendar_slot.markdown(
                build_overall_calendar_html(calendar_week_src, display_week_num, selected_exam_idx_for_calendar, clickable=True),
                unsafe_allow_html=True,
            )
            st.info("이동 가능한 시험이 없습니다.")
        else:
            pick_labels = [x[0] for x in pick_options]
            label_to_idx = {label: idx for label, idx in pick_options}
            selected_from_click = st.session_state.get("sim_selected_idx", None)
            default_pick_idx = 0
            if selected_from_click is not None:
                for i, (_, idx) in enumerate(pick_options):
                    if int(idx) == int(selected_from_click):
                        default_pick_idx = i
                        break
            pick_label = st.selectbox("이동할 과목 선택", pick_labels, index=default_pick_idx, key="sim_pick_exam")
            sel_idx = int(label_to_idx[pick_label])
            if st.session_state.get("sim_selected_idx") != sel_idx:
                st.session_state["move_candidates"] = []
                st.session_state["move_candidate_reasons"] = {}
                st.session_state["selected_candidate"] = None
                st.session_state["move_candidate_meta"] = None
            st.session_state.sim_selected_idx = sel_idx
            sel_row = exam_df_view[exam_df_view["시험인덱스"] == sel_idx].iloc[0]
            selected_exam_idx_for_calendar = int(sel_idx)
            calendar_week_src = calendar_src[calendar_src["주차"] == display_week_num].copy()
            calendar_slot.markdown(
                build_overall_calendar_html(calendar_week_src, display_week_num, selected_exam_idx_for_calendar, clickable=True),
                unsafe_allow_html=True,
            )
            st.caption(
                f"선택 시험: {sel_row['과목명']} | "
                f"{sel_row['요일']} {sel_row['시작']}~{sel_row['종료']} | "
                f"{sel_row['강의실']}"
            )
            st.caption("이동할 과목을 선택한 뒤 후보 탐색을 눌러주세요.")

            current_candidate_context = {
                "sel_idx": int(sel_idx),
                "week": int(display_week_num),
                "course": str(sel_row["과목명"]),
            }
            if st.session_state.get("move_candidate_meta") != current_candidate_context:
                st.session_state["move_candidates"] = []
                st.session_state["move_candidate_reasons"] = {}
                st.session_state["selected_candidate"] = None
                st.session_state["move_candidate_meta"] = current_candidate_context

            dur_slots = max(
                1,
                int(float(sel_row.get("표시종료슬롯", sel_row["종료슬롯"])) - float(sel_row["시작슬롯"]) + 0.999999),
            )
            enrollment = int(sel_row.get("수강인원", 0))
            need_room = max(1, len(normalize_room_choice(sel_row["강의실목록"])))
            # 후보 탐색은 현재 화면에 반영된 배정 주차만 빠르게 확인한다.
            allowed_weeks = [int(sel_row["주차"])]

            current_rooms = normalize_room_choice(sel_row["강의실목록"])
            room_combo_candidates = []
            for combo in combinations([int(r) for r in ROOM_ORDER], need_room):
                total_cap = sum(ROOM_CAP[int(r)] for r in combo)
                if total_cap >= enrollment:
                    room_combo_candidates.append(tuple(int(r) for r in combo))
            if not room_combo_candidates:
                room_combo_candidates = [tuple(int(r) for r in current_rooms)]

            orig_start_slot = int(sel_row["시작슬롯"])
            start_slots_to_search = [
                st_slot for st_slot in range(max(0, orig_start_slot - 2), min(19, orig_start_slot + 3))
                if st_slot + dur_slots <= 22
            ]
            if not start_slots_to_search:
                start_slots_to_search = [orig_start_slot]

            blocked_counts = {
                "주차 고정 위반": 0,
                "필요강의실수/수용인원 부족": 0,
                "강의실 중복": 0,
                "학생 동시시험": 0,
                "분반 연속배정 불가": 0,
                "표시 후보 수": 0,
                "탐색 표시 상한": 20,
                "탐색 조기중단": 0,
            }
            scorer = score_move_impact
            st.markdown("<div class='sim-step-title'>4. 후보 탐색</div>", unsafe_allow_html=True)
            st.markdown("<div class='sim-action-note'>탐색 속도를 위해 현재 주차, 현재 시작시간 주변을 우선 확인합니다.</div>", unsafe_allow_html=True)
            if st.button("후보 탐색", key="search_move_candidates_btn", type="primary"):
                move_candidates: list[dict] = []
                progress_box = st.empty()
                progress_text = st.empty()
                progress_bar = st.progress(0)
                total_steps = max(1, len(allowed_weeks) * 5 * len(start_slots_to_search) * len(room_combo_candidates))
                current_step = 0
                try:
                    stop_search = False
                    student_sets = build_exam_student_sets(exam_df_view, df_is)
                    with st.spinner("후보 탐색 중입니다..."):
                        progress_box.info("상위 이동 후보를 탐색 중입니다...")
                        progress_text.caption("잠시만 기다려주세요. 탐색 범위 내 후보를 확인하고 있습니다.")
                        for week in allowed_weeks:
                            for dnum in [1, 2, 3, 4, 5]:
                                for st_slot in start_slots_to_search:
                                    if st_slot + dur_slots > 22:
                                        continue
                                    for room_combo in room_combo_candidates:
                                        current_step += 1
                                        progress = min(current_step / total_steps, 1.0)
                                        progress_text.caption(f"탐색 범위 내 후보 확인 중... {current_step} / {total_steps}")
                                        progress_bar.progress(progress)
                                        if len(move_candidates) >= 20:
                                            stop_search = True
                                            progress_bar.progress(1.0)
                                            progress_text.caption("탐색 속도를 위해 상위 후보만 표시합니다.")
                                            break
                                        out_eval = scorer(
                                            exam_df=exam_df_view,
                                            target_idx=sel_idx,
                                            new_week=int(week),
                                            new_day=int(dnum),
                                            new_start=int(st_slot),
                                            new_room=list(room_combo),
                                            student_sets=student_sets,
                                            summary=summary,
                                        )
                                        if out_eval.get("feasible", False):
                                            warning_items = []
                                            orig_day = int(sel_row["요일번호"])
                                            orig_start = int(sel_row["시작슬롯"])
                                            current_room_set = set(int(x) for x in normalize_room_choice(sel_row["강의실목록"]))
                                            candidate_room_set = set(int(x) for x in normalize_room_choice(room_combo))
                                            if (
                                                int(week) == int(sel_row["주차"])
                                                and int(dnum) == orig_day
                                                and int(st_slot) == orig_start
                                                and sorted(candidate_room_set) == sorted(current_room_set)
                                            ):
                                                continue
                                            room_change_delta = int(out_eval.get("room_change_delta", 0))
                                            time_move_delta = int(out_eval.get("time_move_delta", 0))
                                            daily_penalty_delta = int(out_eval.get("daily_penalty_delta", 0))
                                            objective_delta = (
                                                WEIGHT_ROOM_MOVE * room_change_delta
                                                + WEIGHT_TIME_MOVE * time_move_delta
                                                + WEIGHT_DAILY * daily_penalty_delta
                                            )
                                            if room_change_delta == 0 and time_move_delta == 0 and daily_penalty_delta == 0:
                                                objective_delta = 0.0
                                            if abs(objective_delta) <= 1e-6:
                                                objective_delta = 0.0
                                            time_changed = (int(dnum), int(st_slot)) != (orig_day, orig_start)
                                            room_changed = candidate_room_set != current_room_set
                                            daily_exam_increase = int(out_eval.get("daily3_increase", 0)) + int(out_eval.get("daily4_increase", 0))
                                            distance_from_current = abs(int(dnum) - orig_day) + abs(int(st_slot) - orig_start)
                                            if abs(int(dnum) - orig_day) > D_MAX:
                                                warning_items.append("하루 시험 수 기준 초과")
                                            if abs(int(st_slot) - orig_start) > T_MAX:
                                                warning_items.append("연속 시험 시간 기준 초과")
                                            if time_changed:
                                                warning_items.append("시간 변경 발생")
                                            if room_changed:
                                                warning_items.append("강의실 변경 발생")
                                            if daily_exam_increase > 0:
                                                warning_items.append("하루 시험 수 증가")
                                            if objective_delta > 1e-6:
                                                warning_items.append("목적함수 증가")

                                            move_candidates.append(
                                                {
                                                    "요일": DAY_LABELS.get(dnum, str(dnum)),
                                                    "시작": slot_to_time(st_slot),
                                                    "종료": minute_to_time(540 + st_slot * 30 + int(sel_row["시험시간(분)"])),
                                                    "강의실": format_room_choice(room_combo),
                                                    "room_combo": list(room_combo),
                                                    "영향학생수": int(out_eval.get("affected_students", 0)),
                                                    "학생충돌수": int(out_eval.get("student_conflict_count", 0)),
                                                    "하루3개증가": int(out_eval.get("daily3_increase", 0)),
                                                    "하루4개증가": int(out_eval.get("daily4_increase", 0)),
                                                    "목적함수변화": float(objective_delta),
                                                    "daily_exam_increase": int(daily_exam_increase),
                                                    "daily_penalty_delta": int(daily_penalty_delta),
                                                    "room_change_delta": int(room_change_delta),
                                                    "time_move_delta": int(time_move_delta),
                                                    "time_changed": bool(time_changed),
                                                    "room_changed": bool(room_changed),
                                                    "distance_from_current": int(distance_from_current),
                                                    "경고": ", ".join(warning_items) if warning_items else "-",
                                                    "week": int(week),
                                                    "dnum": int(dnum),
                                                    "slot": int(st_slot),
                                                }
                                            )
                                        else:
                                            reason = str(out_eval.get("reason", ""))
                                            if "강의실 중복" in reason:
                                                blocked_counts["강의실 중복"] += 1
                                            elif "학생 동시시험" in reason:
                                                blocked_counts["학생 동시시험"] += 1
                                        if stop_search:
                                            break
                                    if stop_search:
                                        break
                                if stop_search:
                                    break
                            if stop_search:
                                break
                    progress_bar.progress(1.0)
                    move_candidates = sorted(
                        move_candidates,
                        key=lambda x: _candidate_sort_key(x, sel_row),
                    )
                except Exception as _calc_err:
                    st.error(f"후보 계산 중 오류: {_calc_err}")
                blocked_counts["표시 후보 수"] = len(move_candidates)
                blocked_counts["탐색 조기중단"] = 1 if len(move_candidates) >= int(blocked_counts.get("탐색 표시 상한", 20)) else 0
                st.session_state["move_candidates"] = move_candidates
                st.session_state["move_candidate_reasons"] = blocked_counts
                st.session_state["move_candidate_meta"] = current_candidate_context
                if move_candidates:
                    if len(move_candidates) >= 20:
                        st.session_state["move_search_notice"] = "탐색 속도를 위해 상위 20개 후보만 표시합니다."
                    else:
                        st.session_state["move_search_notice"] = f"탐색 범위 내에서 찾은 후보 {len(move_candidates)}개를 표시합니다."
                    progress_text.caption(st.session_state["move_search_notice"])
                    progress_box.success(st.session_state["move_search_notice"])
                else:
                    st.session_state["move_search_notice"] = "현재 조건에서 가능한 이동 후보가 없습니다."
                    progress_text.caption(st.session_state["move_search_notice"])
                    progress_box.info(st.session_state["move_search_notice"])

            stored_candidates = st.session_state.get("move_candidates", [])
            if stored_candidates:
                stored_candidates = [
                    c for c in stored_candidates
                    if not _is_same_assignment(c, sel_row)
                ]
                stored_candidates = sorted(stored_candidates, key=lambda x: _candidate_sort_key(x, sel_row))
                st.session_state["move_candidates"] = stored_candidates
            stored_reasons = st.session_state.get("move_candidate_reasons", {})
            if stored_candidates:
                if len(stored_candidates) >= int(stored_reasons.get("탐색 표시 상한", 20)):
                    st.caption(f"탐색 속도를 위해 상위 {len(stored_candidates)}개 후보만 표시합니다.")
                else:
                    st.caption(f"표시 후보 {len(stored_candidates)}개")
            if not stored_candidates:
                if stored_reasons:
                    st.info("현재 조건에서 가능한 이동 후보가 없습니다.")
                    for label, count in stored_reasons.items():
                        if label in ["표시 후보 수", "탐색 표시 상한", "탐색 조기중단"]:
                            continue
                        st.write(f"- {label}: {int(count)}개")
                else:
                    st.info("과목을 선택한 뒤 후보 탐색 버튼을 눌러 이동 가능한 시험 후보를 확인하세요.")
            else:
                st.markdown("<div class='sim-step-title'>5. 후보 리스트</div>", unsafe_allow_html=True)
                st.markdown(
                    "<div class='sim-note'>아래 후보는 학생 동시시험, 강의실 중복, 수용인원 조건을 만족한 후보입니다.</div>",
                    unsafe_allow_html=True,
                )
                cand_df = pd.DataFrame(stored_candidates)
                cand_df["시간후보"] = cand_df.apply(lambda r: f"{r['요일']} {r['시작']}~{r['종료']}", axis=1)
                time_summary = (
                    cand_df.groupby("시간후보", sort=False)
                    .agg(
                        요일=("요일", "first"),
                        시작=("시작", "first"),
                        종료=("종료", "first"),
                        목적함수변화=("목적함수변화", "min"),
                        영향학생수=("영향학생수", "min"),
                        하루시험수변화=("daily_exam_increase", "min"),
                        가능강의실수=("강의실", "nunique"),
                    )
                    .reset_index()
                )
                time_summary = time_summary.sort_values(
                    ["목적함수변화", "하루시험수변화", "영향학생수", "요일", "시작"]
                ).reset_index(drop=True)
                st.markdown("##### STEP 2. 이동 가능한 시간 후보 선택")
                st.dataframe(
                    time_summary[["시간후보", "목적함수변화", "영향학생수", "하루시험수변화", "가능강의실수"]],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "시간후보": "이동 가능 시간",
                        "목적함수변화": st.column_config.NumberColumn("목적함수 변화", format="%+.4f"),
                        "영향학생수": "영향 학생",
                        "하루시험수변화": "하루 시험 수 변화",
                        "가능강의실수": "가능 강의실",
                    },
                )
                time_label_map = {
                    row["시간후보"]: (
                        f"{row['시간후보']} | Δ {float(row['목적함수변화']):+.4f} | "
                        f"영향학생 {int(row['영향학생수'])}명 | 가능 강의실 {int(row['가능강의실수'])}개"
                    )
                    for _, row in time_summary.iterrows()
                }
                time_opts = list(time_label_map.values())
                reverse_time_label_map = {v: k for k, v in time_label_map.items()}
                tsel_label = st.selectbox("STEP 2 시간 후보", time_opts, key="sim_time_filter")
                tsel = reverse_time_label_map[tsel_label]
                cand_time_df = cand_df[
                    cand_df["시간후보"] == tsel
                ].copy()
                st.markdown("##### STEP 3. 선택 시간에서 가능한 강의실 선택")
                room_summary = cand_time_df[["강의실", "목적함수변화", "영향학생수", "daily_exam_increase", "경고"]].copy()
                room_summary = room_summary.sort_values(["목적함수변화", "daily_exam_increase", "영향학생수", "강의실"]).reset_index(drop=True)
                st.dataframe(
                    room_summary.rename(columns={"daily_exam_increase": "하루시험수변화"}),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "강의실": "가능 강의실",
                        "목적함수변화": st.column_config.NumberColumn("목적함수 변화", format="%+.4f"),
                        "영향학생수": "영향 학생",
                        "하루시험수변화": "하루 시험 수 변화",
                        "경고": "경고",
                    },
                )
                room_label_map = {
                    str(row["강의실"]): (
                        f"{row['강의실']} | Δ {float(row['목적함수변화']):+.4f} | "
                        f"영향학생 {int(row['영향학생수'])}명"
                    )
                    for _, row in room_summary.iterrows()
                }
                room_opts = list(room_label_map.values())
                reverse_room_label_map = {v: k for k, v in room_label_map.items()}
                rsel_label = st.selectbox("STEP 3 강의실 후보", room_opts, key="sim_room_filter_by_time")
                rsel = reverse_room_label_map[rsel_label]
                cand_choice_df = cand_time_df[cand_time_df["강의실"].astype(str) == str(rsel)].copy()
                chosen_row = cand_choice_df.iloc[0]
                st.session_state["selected_candidate"] = chosen_row.to_dict()
                tday = str(chosen_row["요일"])
                tstart = str(chosen_row["시작"])
                sim_day_no = int(chosen_row["dnum"])
                sim_start_slot = int(chosen_row["slot"])
                sim_room_choice = list(chosen_row["room_combo"])
                chosen_meta = _candidate_meta(chosen_row, sel_row)
                chosen_badges = [
                    _badge_html("✅ 학생충돌 없음", "ok"),
                    _badge_html("✅ 강의실중복 없음", "ok"),
                ]
                if chosen_meta["dmax_violation"]:
                    chosen_badges.append(_badge_html("⚠ 하루 시험 수 기준 초과", "warn"))
                if chosen_meta["tmax_violation"]:
                    chosen_badges.append(_badge_html("⚠ 연속 시험 시간 기준 초과", "warn"))
                if chosen_meta["daily_exam_increase"] > 0:
                    chosen_badges.append(_badge_html("⚠ 하루 시험 수 증가", "warn"))
                if chosen_meta["time_changed"]:
                    chosen_badges.append(_badge_html("⚠ 시간 변경 발생", "warn"))
                if chosen_meta["room_changed"]:
                    chosen_badges.append(_badge_html("⚠ 강의실 변경 발생", "warn"))
                if chosen_meta["objective_increase"]:
                    chosen_badges.append(_badge_html("⚠ 목적함수 증가", "risk"))

                st.markdown("<div class='sim-step-title'>STEP 4. 선택 후보 요약</div>", unsafe_allow_html=True)
                st.markdown(
                    "<div class='sim-card'>"
                    "<div class='sim-card-title'>선택한 이동안</div>"
                    f"<div class='sim-card-line'>이동 시간: {html.escape(tday)} {html.escape(tstart)}~{html.escape(str(chosen_row['종료']))}</div>"
                    f"<div class='sim-card-line'>강의실: {html.escape(str(chosen_row['강의실']))}</div>"
                    f"<div class='sim-card-line'>강제제약 통과 여부: 통과</div>"
                    f"<div class='sim-card-line'>{html.escape(_objective_status_text(chosen_meta['objective_delta']))}</div>"
                    f"<div class='sim-card-line'>하루 시험 수 변화: {chosen_meta['daily_exam_increase']:+d}</div>"
                    f"<div class='sim-card-line'>시간 변경 여부(TC): {'예' if chosen_meta['time_changed'] else '아니오'}</div>"
                    f"<div class='sim-card-line'>강의실 변경 여부(RC): {'예' if chosen_meta['room_changed'] else '아니오'}</div>"
                    f"<div class='sim-badges'>{''.join(chosen_badges)}</div>"
                    "</div>",
                    unsafe_allow_html=True,
                )

    st.markdown("<div class='sim-step-title'>STEP 5. 변경 실행</div>", unsafe_allow_html=True)
    st.markdown("<div class='sim-action-note'>선택 후보를 검토한 뒤 변경을 반영하거나, 마지막 변경을 되돌리거나, 전체 수동 변경을 초기화합니다.</div>", unsafe_allow_html=True)
    button_row = st.columns(3)
    with button_row[0]:
        if st.button(
            "변경 완료",
            key="apply_move_btn",
            type="primary",
            disabled=sel_idx is None or sim_day_no is None or sim_start_slot is None or sim_room_choice is None or st.session_state.get("selected_candidate") is None,
        ):
            selected_candidate = st.session_state.get("selected_candidate") or {}
            prev_state = st.session_state.manual_moves.get(str(sel_idx))
            st.session_state.manual_move_history.append({"idx": int(sel_idx), "prev": prev_state})
            st.session_state.manual_moves[str(sel_idx)] = {
                "week": int(selected_candidate.get("week", chosen_row["week"] if chosen_row is not None else display_week_num)),
                "day": int(sim_day_no),
                "start_slot": int(sim_start_slot),
                "room": normalize_room_choice(selected_candidate.get("room_combo", sim_room_choice)),
            }
            st.session_state["move_candidates"] = []
            st.session_state["move_candidate_reasons"] = {}
            st.session_state["selected_candidate"] = None
            st.session_state["move_candidate_meta"] = None
            st.session_state["move_apply_notice"] = "✅ 변경이 반영되었습니다."
            st.rerun()
    with button_row[1]:
        if st.button("이전", key="undo_last_move_btn"):
            if st.session_state.manual_move_history:
                item = st.session_state.manual_move_history.pop()
                idx_key = str(item["idx"])
                prev = item["prev"]
                if prev is None:
                    st.session_state.manual_moves.pop(idx_key, None)
                else:
                    st.session_state.manual_moves[idx_key] = prev
                st.session_state["move_candidates"] = []
                st.session_state["move_candidate_reasons"] = {}
                st.session_state["selected_candidate"] = None
                st.session_state["move_candidate_meta"] = None
                st.rerun()
    with button_row[2]:
        if st.button("초기화", key="reset_to_gurobi_btn"):
            st.session_state.manual_moves = {}
            st.session_state.manual_move_history = []
            st.session_state.sim_selected_idx = None
            st.session_state["move_candidates"] = []
            st.session_state["move_candidate_reasons"] = {}
            st.session_state["selected_candidate"] = None
            st.session_state["move_candidate_meta"] = None
            st.session_state["move_apply_notice"] = "초기화되었습니다."
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
                    "강의실": format_room_choice(mv["room"]),
                }
            )
        sim_df = pd.DataFrame(rows).sort_values(["주차", "요일", "시작"])
        st.dataframe(sim_df, use_container_width=True, hide_index=True)
        st.download_button(
            "시뮬레이션 결과 CSV 다운로드",
            data=sim_df.to_csv(index=False).encode("utf-8-sig"),
            file_name="simulation_moves.csv",
            mime="text/csv",
        )
elif menu == "변경사항 확인":
    st.subheader("기존 대비 변경사항 확인")

    df_ch = display_exam_df.copy().sort_values(["변경상태", "주차", "요일번호", "시작슬롯"]) 
    changed_only = st.checkbox("변경된 과목만 보기", value=False)
    if changed_only:
        df_ch = df_ch[df_ch["변경상태"] != "유지"]

    cols = [
        "과목명", "학년", "기존시간", "시작", "종료", "시험시간(분)", "요일", "주차", "기존강의실", "강의실",
        "시간변경여부", "강의실변경여부", "변경상태",
    ]

    view_ch = df_ch[cols].copy()
    st.markdown(
        """
        <div class='change-legend'>
          <span class='change-legend-item'><span class='change-legend-dot keep'></span>초록 = 유지</span>
          <span class='change-legend-item'><span class='change-legend-dot time'></span>노랑 = 시간 변경</span>
          <span class='change-legend-item'><span class='change-legend-dot room'></span>파랑 = 강의실 변경</span>
          <span class='change-legend-item'><span class='change-legend-dot both'></span>주황 = 시간+강의실 변경</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
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
    st.markdown("<div class='compact-calendar-title'>전체 시험 캘린더</div>", unsafe_allow_html=True)
    overall_exam_df = display_exam_df.copy()
    week_values = [w for w in [7, 8, 9] if int(w) in set(overall_exam_df["주차"].astype(int).tolist())]
    if not week_values:
        st.info("표시할 전체 캘린더 데이터가 없습니다.")
    else:
        week_tabs = st.tabs([f"Week {w}" for w in week_values])
        for tab, week_value in zip(week_tabs, week_values):
            with tab:
                st.markdown(
                    build_overall_calendar_html(overall_exam_df, int(week_value)),
                    unsafe_allow_html=True,
                )

    if st.session_state.manual_moves:
        st.info("현재 화면에는 수동 변경이 반영되어 있으며, 목적함수 및 제약 검증값은 Gurobi 원본 결과입니다.")

    used_rooms = set(sum([normalize_room_choice(x) for x in display_exam_df["강의실목록"].tolist()], []))
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("목적함수값", f"{float(summary.get('objective', 0)):.4f}")
    k2.metric("총 시험 수", int(display_exam_df["과목"].nunique()))
    k3.metric("학생충돌 여부", "없음" if int(summary.get("overlap_violation", 0)) == 0 else "있음")
    k4.metric("사용 강의실 수", len(used_rooms))
    k5.metric("분반 연속배정 충돌", "없음" if int(summary.get("section_overlap_violation", 0)) == 0 else "있음")

    with st.expander("최적화 설정 정보", expanded=False):
        st.markdown(
            f"- 강의실 이동 가중치: `{WEIGHT_ROOM_MOVE:.4f}`\n"
            f"- 시간 이동 가중치: `{WEIGHT_TIME_MOVE:.4f}`\n"
            f"- 하루 시험 수 가중치: `{WEIGHT_DAILY:.4f}`\n"
            f"- 요일 이동 허용 범위: `{D_MAX}`\n"
            f"- 시간 이동 허용 범위: `{T_MAX}`"
        )

    st.markdown("#### 결과 표")
    st.dataframe(opt_summary_df, use_container_width=True, hide_index=True)

    st.markdown("#### 제약식 위반표")
    st.dataframe(verify_df, use_container_width=True, hide_index=True)

    st.markdown("#### 결정변수 결과")
    st.dataframe(decision_df, use_container_width=True, hide_index=True)
    st.caption("TC: 시간 변경 여부 / RC: 강의실 변경 여부")
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

    room_image_paths = []
    if report_dir is not None:
        for room in ROOM_ORDER:
            room_path = report_dir / f"page_room_{room}.png"
            if room_path.exists():
                room_image_paths.append((room, room_path))
    if room_image_paths:
        st.markdown("#### 강의실별 시각화")
        room_tabs = st.tabs([f"{room}호" for room, _ in room_image_paths])
        for room_tab, (room, room_path) in zip(room_tabs, room_image_paths):
            with room_tab:
                st.image(str(room_path), use_container_width=True)





