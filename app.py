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
        return df
    except:
        return pd.DataFrame({
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
        # JSON 데이터를 문자열로 직접 전송 (Apps Script의 e.postData.contents에서 받기 위함)
        response = requests.post(SCRIPT_URL, data=data_json.encode('utf-8'))
        return response.status_code == 200
    except:
        return False

st.title("🚀 음료생산기술팀 AI프로젝트 현황")
df_raw = load_data()

# 4. 데이터 편집기 (마우스로 칸 조절 가능)
st.info("💡 각 칸의 경계선을 마우스로 드래그하면 너비를 조절할 수 있습니다.")
edited_df = st.data_editor(
    df_raw, 
    use_container_width=True, 
    height=500,
    num_rows="dynamic"  # 행 추가/삭제 가능
)

# 5. 저장 버튼
st.write("")
if st.button("💾 변경사항 저장하기", use_container_width=True):
    if save_data(edited_df):
        st.success("✅ 구글 시트에 성공적으로 저장되었습니다!")
        st.rerun()
    else:
        st.error("❌ 저장 실패! 구글 앱 스크립트 설정을 확인해주세요.")
