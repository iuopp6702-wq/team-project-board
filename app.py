import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import os
import datetime
import requests
import textwrap

# 1. 설정 및 구글 시트 연결
SHEET_ID = "1zTdSMdir4X_h8u4u9w2zN0AAm-4Ir14OU55rSgENaOk"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyZrclcILnQO7b1LsfrbNoCVfpbhMgP2O6ZXLRC051Cx0YVcwmTl8-gSr5lmEPx2Gmc/exec"

# 2. 데이터 불러오기 함수
def load_data():
    try:
        url = f"{CSV_URL}&cache_bust={datetime.datetime.now().timestamp()}"
        return pd.read_csv(url)
    except Exception:
        st.warning("⚠️ 데이터를 가져오는 중입니다...")
        return pd.DataFrame({
            '이름': ['팀원1', '팀원2', '팀원3', '팀원4', '팀원5'],
            '프로젝트명': ['미입력'] * 5,
            '지난주': ['미입력'] * 5,
            '진척상황': ['미입력'] * 5,
            '최종목표': ['미입력'] * 5,
            '진척률(%)': [0] * 5
        })

# 3. 데이터 저장 함수
def save_data(df):
    try:
        data_json = df.to_json(orient='records', force_ascii=False)
        response = requests.post(SCRIPT_URL, data=data_json, headers={'Content-Type': 'application/json'})
        return response.status_code == 200
    except Exception as e:
        st.error(f"❌ 저장 오류: {e}")
        return False

# 4. 이미지 변환 함수 (인당 2줄 높이 넉넉히 할당)
def df_to_image(df):
    wrapped_df = df.copy()
    for col in wrapped_df.columns:
        # 약 13자마다 줄바꿈하여 가독성 확보
        wrapped_df[col] = wrapped_df[col].apply(lambda x: "\n".join(textwrap.wrap(str(x), width=13)) if len(str(x)) > 13 else x)

    num_rows, num_cols = wrapped_df.shape
    # 이미지 높이를 인당 2줄 이상 충분히 나오도록 설정
    fig, ax = plt.subplots(figsize=(num_cols * 2.8, (num_rows + 1) * 1.6))
    ax.axis('off')

    # 한글 폰트 설정
    import matplotlib.font_manager as fm
    for font in ['NanumGothic', 'Malgun Gothic', 'AppleGothic', 'sans-serif']:
        if font in [f.name for f in fm.fontManager.ttflist]:
            plt.rcParams['font.family'] = font
            break

    table = ax.table(cellText=wrapped_df.values, colLabels=wrapped_df.columns, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(14)
    # 셀 높이(scale)를 5.0으로 설정하여 인당 2줄 공간 확보
    table.scale(1, 5.0)

    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_text_props(weight='bold', color='white')
            cell.set_facecolor('#4c78a8')
        cell.set_edgecolor('#333333')

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.2, dpi=300, transparent=True)
    plt.close(fig)
    buf.seek(0)
    return buf

# 5. UI 구성
st.set_page_config(page_title="음료생산기술팀 프로젝트 보드", layout="wide")
st.title("🚀 음료생산기술팀 AI프로젝트 진행현황")

# 날짜 선택
now = datetime.date.today()
d_col1, d_col2, d_col3, d_col4 = st.columns([1, 1, 1, 2])
with d_col1: year = st.selectbox("📅 년도", range(now.year-1, now.year+2), index=1)
with d_col2: month = st.selectbox("📆 월", range(1, 13), index=now.month-1)
with d_col3: week = st.selectbox("📅 주차", [f"{i}주차" for i in range(1, 6)], index=0)
with d_col4: st.markdown(f"<div style='text-align: right; padding-top: 35px; color: gray;'>오늘: {now.strftime('%Y-%m-%d')}</div>", unsafe_allow_html=True)

st.divider()

# 데이터 로드
df = load_data()

# 표 편집기 설정 (글자가 짤리지 않게 칸을 넓게 할당)
column_config = {}
for col in df.columns:
    if "진척률" in col or "이름" in col:
        column_config[col] = st.column_config.Column(width="small")
    else:
        # 내용 칸을 '대형'으로 설정하여 편집 시 가독성 확보
        column_config[col] = st.column_config.Column(width="large")

st.subheader(f"📊 {year}년 {month}월 {week} 실시간 현황")
edited_df = st.data_editor(
    df, 
    num_rows="fixed", 
    use_container_width=True, 
    hide_index=True,
    column_config=column_config
)

# 하단 버튼
c1, c2 = st.columns(2)
with c1:
    if st.button("💾 변경사항 저장하기", use_container_width=True):
        if save_data(edited_df):
            st.success("성공적으로 저장되었습니다!")
            st.rerun()
with c2:
    img_buf = df_to_image(edited_df)
    st.download_button("🖼️ 이미지 파일 저장", data=img_buf, file_name=f"Project_{year}_{month}_{week}.png", mime="image/png", use_container_width=True)

st.divider()

# 항목명 수정 (맨 아래로 이동시켜 가독성 방해 최소화)
with st.expander("⚙️ 표 항목 이름 수정하기"):
    new_cols = []
    cols = st.columns(len(df.columns))
    for i, name in enumerate(df.columns):
        with cols[i]: new_cols.append(st.text_input(f"항목 {i+1}", value=name, key=f"c{i}"))
    if st.button("✅ 항목 이름 저장"):
        df.columns = new_cols
        if save_data(df): st.rerun()
