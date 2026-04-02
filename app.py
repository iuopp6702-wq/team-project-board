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
        df = pd.read_csv(url)
        # 데이터가 비어있거나 컬럼수가 부족할 경우를 대비해 기본형태 보장
        if df.empty or len(df.columns) < 6:
            raise Exception("Invalid Data")
        return df
    except Exception:
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

# 4. 이미지 변환 함수
def df_to_image(df):
    wrapped_df = df.copy()
    for col in wrapped_df.columns:
        wrapped_df[col] = wrapped_df[col].apply(lambda x: "\n".join(textwrap.wrap(str(x), width=12)) if len(str(x)) > 12 else x)

    num_rows, num_cols = wrapped_df.shape
    fig, ax = plt.subplots(figsize=(num_cols * 3.0, (num_rows + 1) * 1.8))
    ax.axis('off')

    import matplotlib.font_manager as fm
    for font in ['NanumGothic', 'Malgun Gothic', 'AppleGothic', 'sans-serif']:
        if font in [f.name for f in fm.fontManager.ttflist]:
            plt.rcParams['font.family'] = font
            break

    table = ax.table(cellText=wrapped_df.values, colLabels=wrapped_df.columns, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(13)
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

# 사이드바 설정
with st.sidebar:
    st.header("⚙️ 관리 설정")
    df_raw = load_data()
    with st.expander("표 항목 이름 수정"):
        new_cols = []
        for i, name in enumerate(df_raw.columns):
            new_cols.append(st.text_input(f"항목 {i+1}", value=name, key=f"side_c{i}"))
        if st.button("✅ 항목 이름 저장"):
            df_raw.columns = new_cols
            if save_data(df_raw): st.rerun()
    st.divider()
    st.info("💡 팁: 입력 칸에서 Enter를 누르면 줄바꿈이 됩니다.")

st.title("🚀 음료생산기술팀 AI프로젝트 진행현황")

# 날짜 선택
now = datetime.date.today()
d_col1, d_col2, d_col3, d_col4 = st.columns([1, 1, 1, 2])
with d_col1: year = st.selectbox("📅 년도", range(now.year-1, now.year+2), index=1)
with d_col2: month = st.selectbox("📆 월", range(1, 13), index=now.month-1)
with d_col3: week = st.selectbox("📅 주차", [f"{i}주차" for i in range(1, 6)], index=0)
with d_col4: st.markdown(f"<div style='text-align: right; padding-top: 35px; color: gray;'>오늘: {now.strftime('%Y-%m-%d')}</div>", unsafe_allow_html=True)

st.divider()

# 🚀 에러 수정된 입력판
st.subheader(f"📊 {year}년 {month}월 {week} 실시간 편집 (자동 줄바꿈)")

# 헤더 출력
header_cols = st.columns([1, 2, 2, 2, 2, 1])
for i, col_name in enumerate(df_raw.columns):
    header_cols[i].markdown(f"**{col_name}**")

# 본문 입력 그리드 (iloc 사용하여 KeyError 방지)
updated_rows = []
for i, row in df_raw.iterrows():
    row_cols = st.columns([1, 2, 2, 2, 2, 1])
    
    # .iloc를 사용하여 순서대로 데이터를 안전하게 가져옴
    name = row_cols[0].text_input("이름", value=row.iloc[0], key=f"name_{i}", label_visibility="collapsed")
    proj = row_cols[1].text_area("프로젝트명", value=row.iloc[1], key=f"proj_{i}", height=100, label_visibility="collapsed")
    last = row_cols[2].text_area("지난주", value=row.iloc[2], key=f"last_{i}", height=100, label_visibility="collapsed")
    prog = row_cols[3].text_area("진척상황", value=row.iloc[3], key=f"prog_{i}", height=100, label_visibility="collapsed")
    goal = row_cols[4].text_area("최종목표", value=row.iloc[4], key=f"goal_{i}", height=100, label_visibility="collapsed")
    
    # 진척률 숫자 처리 (안전하게)
    raw_rate = row.iloc[5]
    try:
        rate_val = int(float(raw_rate))
    except:
        rate_val = 0
    rate = row_cols[5].number_input("진척률", value=rate_val, key=f"rate_{i}", label_visibility="collapsed")
    
    updated_rows.append([name, proj, last, prog, goal, rate])

# 데이터프레임 변환
edited_df = pd.DataFrame(updated_rows, columns=df_raw.columns)

st.write("") # 간격

# 하단 버튼
c1, c2 = st.columns(2)
with c1:
    if st.button("💾 변경사항 저장하기", use_container_width=True):
        if save_data(edited_df):
            st.success("✅ 구글 시트에 성공적으로 저장되었습니다!")
            st.rerun()
with c2:
    img_buf = df_to_image(edited_df)
    st.download_button("🖼️ 이미지 파일 저장 (공유용)", data=img_buf, file_name=f"Project_{year}_{month}_{week}.png", mime="image/png", use_container_width=True)

st.divider()
