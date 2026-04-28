[실행 방법 - 다른 컴퓨터]
1) 폴더 전체를 그대로 복사합니다.
2) Gurobi 라이선스가 활성화된 PC에서 터미널을 열고 아래 실행:
   pip install -r requirements.txt
   python gurobl.py

[필수 파일]
- gurobl.py
- IS.xlsx
- OT_all_sessions.xlsx  (또는 OT_all_sessions (1).xlsx)
- requirements.txt

[생성 결과]
- 결과_요약.txt
- 결과_결정변수표.csv
- 결과_서비스데이터.json
- 결과_리포트\report.html
- 결과_리포트\결과_발표링크용.pdf

[현재 고정 설정]
- 최대요일이동: 0
- 최대시간이동: 4
