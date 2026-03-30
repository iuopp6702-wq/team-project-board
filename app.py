import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import os
import datetime

# 1. 설정 및 데이터 파일 경로
DATA_FILE = 'project_data.csv'
COLUMNS = ['이름', '프로젝트명', '지난주', '진척상황', '최종목표', '진척률(%)']

# 2. 데이터 불러오기 및 초기화 함수
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        # 초기 데이터 (5명분)
        data = {
            '이름': ['팀원1', '팀원2', '팀원3', '팀원4', '팀원5'],
            '프로젝트명': ['미입력'] * 5,
            '지난주': ['미입력'] * 5,
            '진척상황': ['미입력'] * 5,
            '최종목표': ['미입력'] * 5,
            '진척률(%)': [0] * 5
        }
        df = pd.DataFrame(data)
        df.to_csv(DATA_FILE, index=False)
        return df

# 3. 표를 이미지로 변환하는 함수 (투명 배경 및 여백 최소화)
def df_to_image(df):
    # 행/열 개수에 따라 동적으로 크기 조절
    num_rows, num_cols = df.shape
    fig, ax = plt.subplots(figsize=(num_cols * 2, (num_rows + 1) * 0.6))
    ax.axis('off')
    
    # 한글 폰트 설정
    plt.rcParams['font.family'] = 'Malgun Gothic'
    
    table = ax.table(cellText=df.values, colLabels=df.columns, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1, 2) # 셀 높이 조절
    
    # 헤더 및 셀 스타일링
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_text_props(weight='bold', color='white')
            cell.set_facecolor('#4c78a8')
        # 테두리 색상 설정
        cell.set_edgecolor('#dddddd')
    
    buf = io.BytesIO()
    # transparent=True로 배경 투명화, bbox_inches='tight'로 여백 제거
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.05, dpi=300, transparent=True)
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
        # 컬럼명 변경 및 저장
        df.columns = new_columns
        df.to_csv(DATA_FILE, index=False)
        st.success("항목 이름이 변경되었습니다!")
        st.rerun()

# 데이터 편집기
st.subheader(f"📊 {year}년 {month}월 {week} 실시간 공유 표")
edited_df = st.data_editor(df, num_rows="fixed", width="stretch")

# 저장 및 이미지/복사 레이아웃
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    if st.button("💾 변경사항 저장하기", use_container_width=True):
        edited_df.to_csv(DATA_FILE, index=False)
        st.success("데이터가 성공적으로 저장되었습니다!")
        st.rerun()

with col2:
    # 이미지 생성 버튼
    img_buf = df_to_image(edited_df)
    st.download_button(
        label="🖼️ 이미지로 저장",
        data=img_buf,
        file_name=f"AI_Project_Status_{year}_{month}_{week}.png",
        mime="image/png",
        use_container_width=True
    )

with col3:
    # 메일/엑셀용 HTML 표 생성 (검은색 테두리 스타일 포함)
    header_html = "".join([f'<th style="border: 1px solid black; padding: 8px; background-color: #4c78a8; color: white;">{col}</th>' for col in edited_df.columns])
    rows_html = ""
    for _, row in edited_df.iterrows():
        rows_html += "<tr>" + "".join([f'<td style="border: 1px solid black; padding: 8px; text-align: center;">{val}</td>' for val in row]) + "</tr>"
    
    full_html = f'<table style="border-collapse: collapse; width: 100%; border: 1px solid black;"><thead><tr>{header_html}</tr></thead><tbody>{rows_html}</tbody></table>'
    # 자바스크립트에서 쓰기 위해 줄바꿈 및 따옴표 처리
    safe_html = full_html.replace("'", "\\'").replace("\n", "")

    # 📋 메일 발송용 표 복사 버튼 (HTML 리치 텍스트 방식)
    copy_js = f"""
        <button id="copyBtn" style="
            width: 100%;
            height: 38px;
            background-color: #f0f2f6;
            border: 1px solid #dcdfe3;
            border-radius: 8px;
            cursor: pointer;
            color: #31333f;
            font-size: 14px;
            font-weight: 500;
        ">📋 메일용 표 복사</button>
        <script>
        document.getElementById('copyBtn').onclick = function() {{
            const htmlType = 'text/html';
            const htmlContent = '{safe_html}';
            const blob = new Blob([htmlContent], {{ type: htmlType }});
            const data = [new ClipboardItem({{ [htmlType]: blob, 'text/plain': blob }})];
            
            navigator.clipboard.write(data).then(() => {{
                alert("표가 복사되었습니다! 메일(아웃룩/지메일)에 바로 붙여넣으세요(Ctrl+V).");
            }}, (err) => {{
                console.error('복사 실패:', err);
            }});
        }};
        </script>
    """
    import streamlit.components.v1 as components
    components.html(copy_js, height=45)

st.divider()
