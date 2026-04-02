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

# 4. 이미지 변환 함수 (줄바꿈 대폭 강화 - 10자 기준)
def df_to_image(df):
    wrapped_df = df.copy()
    for col in wrapped_df.columns:
        # 10자마다 줄바꿈하여 2줄 이상 확보
        wrapped_df[col] = wrapped_df[col].apply(lambda x: "\n".join(textwrap.wrap(str(x), width=10)) if len(str(x)) > 10 else x)

    num_rows, num_cols = wrapped_df.shape
    fig, ax = plt.subplots(figsize=(num_cols * 3.2, (num_rows + 1) * 2.0))
    ax.axis('off')

    import matplotlib.font_manager as fm
    for font in ['NanumGothic', 'Malgun Gothic', 'AppleGothic', 'sans-serif']:
        if font in [f.name for f in fm.fontManager.ttflist]:
            plt.rcParams['font.family'] = font
            break

    table = ax.table(cellText=wrapped_df.values, colLabels=wrapped_df.columns, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(15)
    # 셀 높이(scale)를 5.5로 대폭 높여서 2줄을 기본 할당
    table.scale(1, 5.5)

    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_text_props(weight='bold', color='white')
            cell.set_facecolor('#4c78a8')
        cell.set_edgecolor('#333333')

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.3, dpi=300, transparent=True)
    plt.close(fig)
    buf.seek(0)
    return buf

# 5. UI 구성
st.set_page_config(page_title="음료생산기술팀 프로젝트 보드", layout="wide")

# 줄바꿈을 위한 커스텀 CSS (웹 화면 미리보기용)
st.markdown("""
    <style>
    .wrapped-table {
        width: 100%;
        border-collapse: collapse;
        font-family: sans-serif;
    }
    .wrapped-table th, .wrapped-table td {
        border: 1px solid #ddd;
        padding: 12px;
        text-align: center;
        white-space: pre-wrap; /* 이 설정이 핵심: 자동 줄바꿈 */
        word-break: break-all;
    }
    .wrapped-table th {
        background-color: #4c78a8;
        color: white;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

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

# 항목명 수정
with st.expander("⚙️ 표 항목 이름 수정"):
    new_cols = []
    cols = st.columns(len(df.columns))
    for i, name in enumerate(df.columns):
        with cols[i]: new_cols.append(st.text_input(f"항목 {i+1}", value=name, key=f"c{i}"))
    if st.button("✅ 항목 이름 저장"):
        df.columns = new_cols
        if save_data(df): st.rerun()

# 편집기 (여기선 한 줄로 보임)
st.subheader("✍️ 데이터 편집 (칸을 눌러 수정하세요)")
edited_df = st.data_editor(df, num_rows="fixed", use_container_width=True, hide_index=True)

st.divider()

# 🚀 줄바꿈 미리보기 (여기가 엑셀처럼 보임)
st.subheader(f"👀 {year}년 {month}월 {week} 줄바꿈 미리보기 (이미지 저장 결과)")
html_table = f"<table class='wrapped-table'><thead><tr>"
for col in edited_df.columns: html_table += f"<th>{col}</th>"
html_table += "</tr></thead><tbody>"
for _, row in edited_df.iterrows():
    html_table += "<tr>"
    for val in row: html_table += f"<td>{val}</td>"
    html_table += "</tr>"
html_table += "</tbody></table>"
st.markdown(html_table, unsafe_allow_html=True)

st.write("") # 공백

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
