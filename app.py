import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import os
import datetime

from streamlit_gsheets import GSheetsConnection

# 1. 설정 및 구글 시트 연결
SHEET_URL = "https://docs.google.com/spreadsheets/d/1zTdSMdir4X_h8u4u9w2zN0AAm-4Ir14OU55rSgENaOk/edit?usp=sharing"

# 2. 데이터 불러오기 및 초기화 함수 (구글 시트 연동)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        # 구글 시트에서 데이터 읽기
        df = conn.read(spreadsheet=SHEET_URL, ttl=0) # ttl=0으로 실시간 데이터 로드
        return df
    except Exception:
        # 시트가 비어있거나 오류 시 초기 데이터 생성
        data = {
            '이름': ['팀원1', '팀원2', '팀원3', '팀원4', '팀원5'],
            '프로젝트명': ['미입력'] * 5,
            '지난주': ['미입력'] * 5,
            '진척상황': ['미입력'] * 5,
            '최종목표': ['미입력'] * 5,
            '진척률(%)': [0] * 5
        }
        return pd.DataFrame(data)

# 데이터 업데이트 함수 (구글 시트 저장)
def save_data(df):
    conn = st.connection("gsheets", type=GSheetsConnection)
    conn.update(spreadsheet=SHEET_URL, data=df)
import textwrap

# 3. 표를 이미지로 변환하는 함수 (줄바꿈 기능 추가)
def df_to_image(df):
    # 데이터 내의 긴 텍스트 줄바꿈 처리
    wrapped_df = df.copy()
    for col in wrapped_df.columns:
        wrapped_df[col] = wrapped_df[col].apply(lambda x: "\n".join(textwrap.wrap(str(x), width=15)) if len(str(x)) > 15 else x)

    num_rows, num_cols = wrapped_df.shape
    # 줄바꿈으로 인해 길어질 수 있으므로 이미지 높이 여유 있게 설정
    fig, ax = plt.subplots(figsize=(num_cols * 2.5, (num_rows + 1) * 1.2))
    ax.axis('off')

    import matplotlib.font_manager as fm
    font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
    if os.path.exists(font_path):
        fm.fontManager.addfont(font_path)
        plt.rcParams['font.family'] = 'NanumGothic'
    else:
        plt.rcParams['font.family'] = 'Malgun Gothic'

    table = ax.table(cellText=wrapped_df.values, colLabels=wrapped_df.columns, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(13)
    table.scale(1, 3.5) # 줄바꿈을 위해 셀 높이를 더 높임

    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_text_props(weight='bold', color='white')
            cell.set_facecolor('#4c78a8')
        cell.set_edgecolor('#333333')

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1, dpi=400, transparent=True)
    plt.close(fig)
    buf.seek(0)
    return buf


# 4. Streamlit UI 구성
st.set_page_config(page_title="음료생산기술팀 프로젝트 보드", layout="wide")

# 제목
st.title("🚀 음료생산기술팀 AI프로젝트 진행현황")

# 년/월 및 오늘 날짜 섹션
now = datetime.date.today()
date_col1, date_col2, date_col3, date_col4 = st.columns([1, 1, 1, 2])

with date_col1:
    year = st.selectbox("📅 년도", range(now.year-1, now.year+2), index=1)
with date_col2:
    month = st.selectbox("📆 월", range(1, 13), index=now.month-1)
with date_col3:
    week = st.selectbox("📅 주차", [f"{i}주차" for i in range(1, 6)], index=0)
with date_col4:
    st.markdown(f"<div style='text-align: right; padding-top: 35px; color: gray;'>오늘 날짜: {now.strftime('%Y-%m-%d')}</div>", unsafe_allow_html=True)

st.divider()

# 데이터 로드
df = load_data()

# 4-1. 항목(컬럼) 이름 수정 섹션
with st.expander("⚙️ 표 항목(컬럼) 이름 수정하기"):
    st.info("관리하고 싶은 항목 이름을 수정하세요. 수정 후 아래 '항목 이름 저장'을 누르면 반영됩니다.")
    new_columns = []
    cols = st.columns(len(df.columns))
    for i, col_name in enumerate(df.columns):
        with cols[i]:
            new_name = st.text_input(f"항목 {i+1}", value=col_name, key=f"col_{i}")
            new_columns.append(new_name)
    
    if st.button("✅ 항목 이름 저장"):
        df.columns = new_columns
        save_data(df) # 구글 시트 업데이트
        st.success("항목 이름이 변경되었습니다!")
        st.rerun()

# 데이터 편집기 (모바일 가독성 최적화)
st.subheader(f"📊 {year}년 {month}월 {week} 실시간 공유 표")

first_col = df.columns[0]
last_col = df.columns[-1]

# 컬럼 설정 (이름 칸을 좁게 고정하여 모바일 공간 확보)
column_config = {
    first_col: st.column_config.TextColumn(
        first_col,
        width="small",
        required=True
    ),
    last_col: st.column_config.NumberColumn(
        last_col,
        min_value=0,
        max_value=100,
        format="%d%%",
        width="small"
    )
}

# 모든 컬럼에 대해 기본 너비를 적절히 배분
edited_df = st.data_editor(
    df, 
    num_rows="fixed", 
    width="stretch", 
    column_config=column_config,
    use_container_width=True,
    hide_index=True 
)

# 저장 및 이미지 파일 저장 레이아웃
col1, col2 = st.columns([1, 1])

with col1:
    if st.button("💾 변경사항 저장하기", use_container_width=True):
        save_data(edited_df) # 구글 시트 업데이트
        st.success("데이터가 구글 시트에 성공적으로 저장되었습니다!")
        st.rerun()

with col2:
    # 이미지 생성 버튼 (다운로드용)
    img_buf = df_to_image(edited_df)
    st.download_button(
        label="🖼️ 이미지 파일 저장",
        data=img_buf,
        file_name=f"AI_Project_Status_{year}_{month}_{week}.png",
        mime="image/png",
        use_container_width=True
    )

st.divider()
