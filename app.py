import streamlit as st
import pandas as pd
import datetime
import requests

# 1. 설정 (제공해주신 URL 적용)
SHEET_ID = "1zTdSMdir4X_h8u4u9w2zN0AAm-4Ir14OU55rSgENaOk"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycby9Wuiw1cDH47fvbEtigKz-yXNqVZz_KTHNcBeQkmxz4Xdy9BBgWoKcasWKLP1c4acM/exec"

st.set_page_config(page_title="음료생산기술팀 프로젝트 보드", layout="wide")

# 2. 데이터 불러오기 함수
def load_data():
    try:
        url = f"{CSV_URL}&cache_bust={datetime.datetime.now().timestamp()}"
        df = pd.read_csv(url)
        if df.empty: raise Exception
        
        # '주차' 컬럼이 없으면 생성
        if '주차' not in df.columns:
            df.insert(0, '주차', '미입력')
            
        return df
    except:
        return pd.DataFrame({
            '주차': ['미입력']*5,
            '이름': ['팀원1', '팀원2', '팀원3', '팀원4', '팀원5'],
            '프로젝트명': ['미입력']*5, 
            '지난주': ['미입력']*5, 
            '진척상황': ['미입력']*5, 
            '최종목표': ['미입력']*5, 
            '진척률(%)': [0]*5
        })

# 3. 데이터 저장 함수
def save_data(df):
    try:
        data_json = df.to_json(orient='records', force_ascii=False)
        response = requests.post(SCRIPT_URL, data=data_json.encode('utf-8'))
        return response.status_code == 200
    except:
        return False

st.title("🚀 음료생산기술팀 AI프로젝트 현황")
df_raw = load_data()

# 4. 입력 화면 구성 (헤더 포함)
st.markdown("---")
# 비율 조정: [주차(0.8), 이름(0.7), 프로젝트(2), 지난주(2.5), 이번주(2.5), 목표(2.5), 진척(0.6)]
h_cols = st.columns([0.8, 0.7, 2, 2.5, 2.5, 2.5, 0.6])
headers = ["주차", "이름", "프로젝트명", "지난주 성과", "이번주 계획", "최종 목표", "진척(%)"]
for i, h in enumerate(headers):
    h_cols[i].write(f"**{h}**")

updated_rows = []
for i, row in df_raw.iterrows():
    with st.container():
        cols = st.columns([0.8, 0.7, 2, 2.5, 2.5, 2.5, 0.6])
        
        # 각 데이터 타입에 맞춰 안전하게 불러오기
        val_week = str(row.get('주차', '미입력'))
        val_name = str(row.get('이름', ''))
        val_proj = str(row.get('프로젝트명', ''))
        val_last = str(row.get('지난주', ''))
        val_prog = str(row.get('진척상황', ''))
        val_goal = str(row.get('최종목표', ''))
        val_rate = str(row.get('진척률(%)', '0'))

        week = cols[0].text_input(f"w{i}", value=val_week, label_visibility="collapsed")
        name = cols[1].text_input(f"n{i}", value=val_name, label_visibility="collapsed")
        proj = cols[2].text_area(f"p{i}", value=val_proj, height=100, label_visibility="collapsed")
        last = cols[3].text_area(f"l{i}", value=val_last, height=100, label_visibility="collapsed")
        prog = cols[4].text_area(f"pr{i}", value=val_prog, height=100, label_visibility="collapsed")
        goal = cols[5].text_area(f"g{i}", value=val_goal, height=100, label_visibility="collapsed")
        rate = cols[6].text_input(f"r{i}", value=val_rate, label_visibility="collapsed")
        
        updated_rows.append([week, name, proj, last, prog, goal, rate])

# 5. 저장 버튼
st.write("")
if st.button("💾 변경사항 저장하기", use_container_width=True):
    # 컬럼 순서를 맞춰서 저장
    new_df = pd.DataFrame(updated_rows, columns=['주차', '이름', '프로젝트명', '지난주', '진척상황', '최종목표', '진척률(%)'])
    if save_data(new_df):
        st.success("✅ 구글 시트에 성공적으로 저장되었습니다!")
        st.rerun()
    else:
        st.error("❌ 저장 실패! 구글 앱 스크립트 설정을 확인해주세요.")
