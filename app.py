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

# 팀원 리스트 고정 (주차별 데이터가 없을 때 기본값으로 사용)
TEAM_MEMBERS = ['조영준', '최광수', '박소연', '차관호', '임완수']

# 2. 데이터 불러오기 함수
def load_data():
    try:
        url = f"{CSV_URL}&cache_bust={datetime.datetime.now().timestamp()}"
        df = pd.read_csv(url)
        return df
    except Exception:
        # 파일이 없거나 오류 시 빈 데이터프레임 반환
        return pd.DataFrame(columns=['주차ID', '이름', '프로젝트명', '지난주', '진척상황', '최종목표', '진척률(%)'])

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
    # 이미지 저장용으로는 '주차ID'를 제외하고 깔끔하게 출력
    display_df = df.drop(columns=['주차ID']) if '주차ID' in df.columns else df
    wrapped_df = display_df.copy()
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

st.markdown("""
<style>
    @media (min-width: 800px) {
        div[data-testid="column"] label { display: none !important; }
    }
    @media (max-width: 799px) {
        .desktop-header { display: none !important; }
        div[data-testid="column"] { margin-bottom: -10px; }
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 15px !important;
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

# 현재 선택된 주차의 고유 ID 생성
target_id = f"{year}-{month}-{week}"

st.divider()

# 데이터 로드 및 필터링
full_df = load_data()

# 1. '주차ID' 컬럼이 없으면 생성 (기존 데이터 호환용)
if '주차ID' not in full_df.columns:
    full_df['주차ID'] = target_id

# 2. 현재 주차의 데이터만 필터링
week_df = full_df[full_df['주차ID'] == target_id].copy()

# 3. 만약 해당 주차의 데이터가 하나도 없다면, 팀원 리스트를 기반으로 초기 데이터 생성
if week_df.empty:
    week_df = pd.DataFrame({
        '주차ID': [target_id] * len(TEAM_MEMBERS),
        '이름': TEAM_MEMBERS,
        '프로젝트명': ['미입력'] * len(TEAM_MEMBERS),
        '지난주': ['미입력'] * len(TEAM_MEMBERS),
        '진척상황': ['미입력'] * len(TEAM_MEMBERS),
        '최종목표': ['미입력'] * len(TEAM_MEMBERS),
        '진척률(%)': ['0'] * len(TEAM_MEMBERS)
    })

st.subheader(f"📊 {year}년 {month}월 {week} 실시간 현황")

# 데스크탑용 헤더 (슬림한 비율 적용: [이름(0.7), 프로젝트(2), 지난주(2.5), 이번주(2.5), 목표(2.5), 진척(0.6)])
st.markdown('<div class="desktop-header">', unsafe_allow_html=True)
header_cols = st.columns([0.7, 2, 2.5, 2.5, 2.5, 0.6])
headers = ["이름", "프로젝트명", "지난주 성과", "이번주 계획", "최종 목표", "진척(%)"]
for i, h in enumerate(headers):
    header_cols[i].markdown(f"**{h}**")
st.markdown('</div>', unsafe_allow_html=True)

# 입력 그리드
updated_rows = []
for i, row in week_df.iterrows():
    with st.container(border=True):
        cols = st.columns([0.7, 2, 2.5, 2.5, 2.5, 0.6])
        
        name = cols[0].text_input(f"n{i}", value=str(row['이름']), key=f"n_{target_id}_{i}")
        proj = cols[1].text_area(f"p{i}", value=str(row['프로젝트명']), key=f"p_{target_id}_{i}", height=100)
        last = cols[2].text_area(f"l{i}", value=str(row['지난주']), key=f"l_{target_id}_{i}", height=100)
        prog = cols[3].text_area(f"pr{i}", value=str(row['진척상황']), key=f"pr_{target_id}_{i}", height=100)
        goal = cols[4].text_area(f"g{i}", value=str(row['최종목표']), key=f"g_{target_id}_{i}", height=100)
        rate = cols[5].text_input(f"r{i}", value=str(row['진척률(%)']), key=f"r_{target_id}_{i}")
        
        updated_rows.append([target_id, name, proj, last, prog, goal, rate])

# 하단 버튼 로직
st.write("")
c1, c2 = st.columns(2)

with c1:
    if st.button("💾 변경사항 저장하기", use_container_width=True):
        # 1. 현재 주차의 수정된 데이터 생성
        new_week_df = pd.DataFrame(updated_rows, columns=['주차ID', '이름', '프로젝트명', '지난주', '진척상황', '최종목표', '진척률(%)'])
        
        # 2. 전체 데이터에서 현재 주차분을 제외한 나머지 데이터와 합치기 (데이터 누적)
        other_weeks_df = full_df[full_df['주차ID'] != target_id]
        final_df = pd.concat([other_weeks_df, new_week_df], ignore_index=True)
        
        if save_data(final_df):
            st.success(f"✅ {target_id} 데이터가 성공적으로 저장되었습니다!")
            st.rerun()

with c2:
    # 현재 화면에 보이는 데이터만 이미지로 저장
    current_edit_df = pd.DataFrame(updated_rows, columns=['주차ID', '이름', '프로젝트명', '지난주', '진척상황', '최종목표', '진척률(%)'])
    img_buf = df_to_image(current_edit_df)
    st.download_button("🖼️ 이미지 파일 저장 (공유용)", data=img_buf, file_name=f"Project_{target_id}.png", mime="image/png", use_container_width=True)
