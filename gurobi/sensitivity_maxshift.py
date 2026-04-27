import csv
import os
import re
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODEL = BASE_DIR / 'gurobl.py'
OUT_CSV = BASE_DIR / '민감도_최대거리_결과.csv'

D_CAND = [0, 1, 2]
T_CAND = [2, 3, 4, 5, 6]

def parse_metric(text: str, key: str, cast=float, default=None):
    m = re.search(rf"{re.escape(key)}\s*=\s*([-+]?\d+(?:\.\d+)?)", text)
    if not m:
        return default
    return cast(float(m.group(1))) if cast is int else cast(m.group(1))

def parse_korean_count(text: str, key: str):
    m = re.search(rf"{re.escape(key)}\s*=\s*(\d+)", text)
    return int(m.group(1)) if m else None

rows = []
for dmax in D_CAND:
    for tmax in T_CAND:
        env = os.environ.copy()
        env['MAX_DAY_SHIFT'] = str(dmax)
        env['MAX_TIME_SHIFT'] = str(tmax)
        env['GENERATE_REPORT'] = '0'
        env['AUTO_OPEN_REPORT'] = '0'

        proc = subprocess.run(
            [sys.executable, str(MODEL)],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            env=env,
        )
        out = (proc.stdout or '') + '\n' + (proc.stderr or '')

        infeasible = ('No feasible solution found' in out) or ('infeasible' in out.lower())

        row = {
            'Dmax': dmax,
            'Tmax': tmax,
            'feasible': 0 if infeasible else 1,
            'objective': None if infeasible else parse_metric(out, 'Objective', float, None),
            'time_move_sum': None if infeasible else parse_metric(out, 'TimeMoveSum', int, None),
            'room_move_sum': None if infeasible else parse_metric(out, 'RoomMoveSum', int, None),
            'daily_penalty_sum': None if infeasible else parse_metric(out, 'DailyPenaltySum', int, None),
            'overlap_violation': None if infeasible else parse_korean_count(out, '동시시험 위반건수'),
            'consecutive_violation': None if infeasible else parse_korean_count(out, '연속시험 위반건수'),
            'daily4_count': None if infeasible else parse_korean_count(out, '하루 4시험 건수'),
            'return_code': proc.returncode,
        }
        rows.append(row)
        print(f"Dmax={dmax}, Tmax={tmax} -> feasible={row['feasible']}, obj={row['objective']}")

with OUT_CSV.open('w', newline='', encoding='utf-8-sig') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

# 선택 규칙: feasible & 위반0 중 최소 완화(Dmax,Tmax), 동률은 objective 최소
cands = [
    r for r in rows
    if r['feasible'] == 1 and (r['overlap_violation'] or 0) == 0 and (r['consecutive_violation'] or 0) == 0 and (r['daily4_count'] or 0) == 0
]
if cands:
    best = sorted(cands, key=lambda r: (r['Dmax'], r['Tmax'], r['objective'] if r['objective'] is not None else 1e18))[0]
    print('\n[추천 조합]')
    print(best)
else:
    print('\n[추천 조합] 조건 만족 조합 없음')

print(f"\n저장 완료: {OUT_CSV}")
