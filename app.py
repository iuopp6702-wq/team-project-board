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
SCRIPT_URL = "https://script.google.com/macros/s/AKfycby9Wuiw1cDH47fvbEtigKz-yXNqVZz_KTHNcBeQkmxz4Xdy9BBgWoKcasWKLP1c4acM/exec"

# 2. 데이터 불러오기 함수
def load_data():
    try:
        url = f"{CSV_URL}&cache_bust={datetime.datetime.now().timestamp()}"
        df = pd.read_csv(url)
        if df.empty or len(df.columns) < 6: raise Exception("Invalid Data")
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

# 5. UI 구성 및 모바일 최적화 CSS
st.set_page_config(page_title="음료생산기술팀 프로젝트 보드", layout="wide")

st.markdown("""
<style>
    /* 데스크탑: 입력 칸의 라벨을 숨겨서 표처럼 보이게 함 */
    @media (min-width: 800px) {
        div[data-testid="column"] label {
            display: none !important;
        }
    }
    
    /* 모바일: 상단 헤더 줄을 숨기고 카드 간격 조정 */
    @media (max-width: 799px) {
        .desktop-header {
            display: none !important;
        }
        div[data-testid="column"] {
            margin-bottom: -10px;
        }
    }
    
    /* 카드 스타일 보강 */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 15px !important;
    }
</style>
""", unsafe_allow_html=True)

# 사이드바
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
    st.info("💡 모바일에서는 각 칸에 이름이 표시됩니다.")

st.title("🚀 음료생산기술팀 AI프로젝트 진행현황")

# 날짜 선택
now = datetime.date.today()
d_col1, d_col2, d_col3, d_col4 = st.columns([1, 1, 1, 2])
with d_col1: year = st.selectbox("📅 년도", range(now.year-1, now.year+2), index=1)
with d_col2: month = st.selectbox("📆 월", range(1, 13), index=now.month-1)
with d_col3: week = st.selectbox("📅 주차", [f"{i}주차" for i in range(1, 6)], index=0)
with d_col4: st.markdown(f"<div style='text-align: right; padding-top: 35px; color: gray;'>오늘: {now.strftime('%Y-%m-%d')}</div>", unsafe_allow_html=True)

st.divider()

# 🚀 반응형 입력판
st.subheader(f"📊 {year}년 {month}월 {week} 실시간 현황")

# 데스크탑용 헤더 (모바일에서는 숨겨짐)
st.markdown('<div class="desktop-header">', unsafe_allow_html=True)
header_cols = st.columns([1, 2, 2, 2, 2, 1])
for i, col_name in enumerate(df_raw.columns):
    header_cols[i].markdown(f"**{col_name}**")
st.markdown('</div>', unsafe_allow_html=True)

# 본문 입력 그리드 (카드 형태)
updated_rows = []
for i, row in df_raw.iterrows():
    # 각 팀원을 테두리가 있는 컨테이너(카드)로 묶음
    with st.container(border=True):
        row_cols = st.columns([1, 2, 2, 2, 2, 1])
        
        name = row_cols[0].text_input(df_raw.columns[0], value=row.iloc[0], key=f"name_{i}")
        proj = row_cols[1].text_area(df_raw.columns[1], value=row.iloc[1], key=f"proj_{i}", height=68)
        last = row_cols[2].text_area(df_raw.columns[2], value=row.iloc[2], key=f"last_{i}", height=68)
        prog = row_cols[3].text_area(df_raw.columns[3], value=row.iloc[3], key=f"prog_{i}", height=68)
        goal = row_cols[4].text_area(df_raw.columns[4], value=row.iloc[4], key=f"goal_{i}", height=68)
        
        raw_rate = row.iloc[5]
        rate = row_cols[5].text_input(df_raw.columns[5], value=str(raw_rate), key=f"rate_{i}")
        
        updated_rows.append([name, proj, last, prog, goal, rate])

edited_df = pd.DataFrame(updated_rows, columns=df_raw.columns)

# 하단 버튼
st.write("")
c1, c2 = st.columns(2)
with c1:
    if st.button("💾 변경사항 저장하기", use_container_width=True):
        if save_data(edited_df):
            st.success("✅ 성공적으로 저장되었습니다!")
            st.rerun()
with c2:
    img_buf = df_to_image(edited_df)
    st.download_button("🖼️ 이미지 파일 저장 (공유용)", data=img_buf, file_name=f"Project_{year}_{month}_{week}.png", mime="image/png", use_container_width=True)

st.divider()
