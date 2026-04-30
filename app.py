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

TEAM_MEMBERS = ['조영준', '최광수', '박소연', '차관호', '임완수']

# 2. 데이터 불러오기 함수
def load_data():
    try:
        url = f"{CSV_URL}&cache_bust={datetime.datetime.now().timestamp()}"
        df = pd.read_csv(url)
        # 컬럼명 매핑 (구 시트 데이터 호환성 유지)
        df = df.rename(columns={'지난주': '실적', '진척상황': '차주 계획'})
        return df
    except Exception:
        return pd.DataFrame(columns=['주차ID', '이름', '프로젝트명', '실적', '차주 계획', '최종목표', '진척률(%)'])

# 3. 데이터 저장 함수
def save_data(df):
    try:
        # 저장 시에는 구 시트 컬럼명으로 다시 변경하여 저장 (앱스 스크립트/시트 구조 유지)
        save_df = df.rename(columns={'실적': '지난주', '차주 계획': '진척상황'})
        data_json = save_df.to_json(orient='records', force_ascii=False)
        response = requests.post(SCRIPT_URL, data=data_json, headers={'Content-Type': 'application/json'})
        return response.status_code == 200
    except Exception as e:
        st.error(f"❌ 저장 오류: {e}")
        return False

# 4. 이미지 변환 함수
def df_to_image(df):
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
        div[data-testid="column"] label { 
            display: block !important; 
            font-weight: bold;
            margin-bottom: -15px;
            color: #4c78a8;
        }
        div[data-testid="column"] { margin-bottom: 5px; }
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 15px !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🚀 음료생산기술팀 AI프로젝트 진행현황")

# --- 주차 선택 로직 (세션 상태 및 URL 동기화) ---
now = datetime.date.today()
params = st.query_params

# 1. 초기값 결정 (URL -> 세션 -> 기본값 순)
if "year" not in st.session_state:
    if "year" in params:
        try: st.session_state.year = int(params["year"])
        except: st.session_state.year = now.year
    else:
        st.session_state.year = now.year

if "month" not in st.session_state:
    if "month" in params:
        try: st.session_state.month = int(params["month"])
        except: st.session_state.month = now.month
    else:
        st.session_state.month = now.month

if "week" not in st.session_state:
    if "week" in params:
        st.session_state.week = params["week"]
    else:
        # 오늘 날짜를 기준으로 주차 계산 (7일 단위)
        current_week_num = (now.day - 1) // 7 + 1
        if current_week_num > 5: current_week_num = 5
        st.session_state.week = f"{current_week_num}주차"

# 2. 날짜 선택 UI
d_col1, d_col2, d_col3, d_col4 = st.columns([1, 1, 1, 2])

with d_col1:
    year_options = list(range(now.year-1, now.year+2))
    try: y_idx = year_options.index(st.session_state.year)
    except: y_idx = 1
    year = st.selectbox("📅 년도", year_options, index=y_idx, key="year_select")

with d_col2:
    month_options = list(range(1, 13))
    try: m_idx = month_options.index(st.session_state.month)
    except: m_idx = now.month - 1
    month = st.selectbox("📆 월", month_options, index=m_idx, key="month_select")

with d_col3:
    week_options = [f"{i}주차" for i in range(1, 6)]
    try: w_idx = week_options.index(st.session_state.week)
    except: w_idx = 0
    week = st.selectbox("📅 주차", week_options, index=w_idx, key="week_select")

with d_col4:
    st.markdown(f"<div style='text-align: right; padding-top: 35px; color: gray;'>오늘: {now.strftime('%Y-%m-%d')}</div>", unsafe_allow_html=True)

# 3. 선택된 값을 세션 및 URL에 업데이트
if (st.session_state.year != year or 
    st.session_state.month != month or 
    st.session_state.week != week):
    st.session_state.year = year
    st.session_state.month = month
    st.session_state.week = week
    st.query_params.update(year=year, month=month, week=week)
    st.rerun()

target_id = f"{year}-{month}-{week}"

st.divider()

# 데이터 로드
full_df = load_data()

# 1. 해당 주차 데이터가 있는지 확인
week_df = full_df[full_df['주차ID'] == target_id].copy()

# 2. 해당 주차 데이터가 없으면, '가장 최근에 저장된 데이터'를 가져와서 복사
if week_df.empty:
    if not full_df.empty:
        latest_ids = full_df['주차ID'].unique()
        if len(latest_ids) > 0:
            last_id = latest_ids[-1]
            week_df = full_df[full_df['주차ID'] == last_id].copy()
            week_df['주차ID'] = target_id
    
    if week_df.empty:
        week_df = pd.DataFrame({
            '주차ID': [target_id] * len(TEAM_MEMBERS),
            '이름': TEAM_MEMBERS,
            '프로젝트명': ['미입력'] * len(TEAM_MEMBERS),
            '실적': ['미입력'] * len(TEAM_MEMBERS),
            '차주 계획': ['미입력'] * len(TEAM_MEMBERS),
            '최종목표': ['미입력'] * len(TEAM_MEMBERS),
            '진척률(%)': ['0'] * len(TEAM_MEMBERS)
        })

st.subheader(f"📊 {year}년 {month}월 {week} 실시간 현황")

# 헤더 (슬림 비율 유지)
st.markdown('<div class="desktop-header">', unsafe_allow_html=True)
header_cols = st.columns([0.7, 2, 2.5, 2.5, 2.5, 0.6])
headers = ["이름", "프로젝트명", "실적", "차주 계획", "최종 목표", "진척(%)"]
for i, h in enumerate(headers):
    header_cols[i].markdown(f"**{h}**")
st.markdown('</div>', unsafe_allow_html=True)

# 입력 그리드
updated_rows = []
for i, row in week_df.iterrows():
    with st.container(border=True):
        # 팀원 이름 강조 (모바일/데스크톱 공통)
        st.markdown(f"### 👤 {row['이름']}")
        cols = st.columns([0.7, 2, 2.5, 2.5, 2.5, 0.6])
        
        # 라벨 표시 (CSS로 데스크톱에서 숨김 처리됨)
        name = cols[0].text_input("이름", value=str(row['이름']), key=f"n_{target_id}_{i}")
        proj = cols[1].text_area("프로젝트명", value=str(row['프로젝트명']), key=f"p_{target_id}_{i}", height=100)
        last = cols[2].text_area("실적", value=str(row['실적']), key=f"l_{target_id}_{i}", height=100)
        prog = cols[3].text_area("차주 계획", value=str(row['차주 계획']), key=f"pr_{target_id}_{i}", height=100)
        goal = cols[4].text_area("최종 목표", value=str(row['최종목표']), key=f"g_{target_id}_{i}", height=100)
        rate = cols[5].text_input("진척(%)", value=str(row['진척률(%)']), key=f"r_{target_id}_{i}")
        
        updated_rows.append([target_id, name, proj, last, prog, goal, rate])

# 저장 버튼
st.write("")
c1, c2 = st.columns(2)

with c1:
    if st.button("💾 변경사항 저장하기", use_container_width=True):
        new_week_df = pd.DataFrame(updated_rows, columns=['주차ID', '이름', '프로젝트명', '실적', '차주 계획', '최종목표', '진척률(%)'])
        
        # 최신 데이터를 다시 불러와서 다른 주차 데이터가 유실되지 않도록 병합
        fresh_full_df = load_data()
        if not fresh_full_df.empty:
            other_weeks_df = fresh_full_df[fresh_full_df['주차ID'] != target_id]
            final_df = pd.concat([other_weeks_df, new_week_df], ignore_index=True)
        else:
            final_df = new_week_df
            
        if save_data(final_df):
            st.success(f"✅ {target_id} 데이터가 성공적으로 저장되었습니다!")
            st.cache_data.clear() # 캐시 강제 삭제
            st.rerun()

with c2:
    current_edit_df = pd.DataFrame(updated_rows, columns=['주차ID', '이름', '프로젝트명', '실적', '차주 계획', '최종목표', '진척률(%)'])
    # 이미지 저장용 컬럼명 변경
    img_df = current_edit_df.rename(columns={
        '최종목표': '최종 목표',
        '진척률(%)': '진척(%)'
    })
    img_buf = df_to_image(img_df)
    st.download_button("🖼️ 이미지 파일 저장 (공유용)", data=img_buf, file_name=f"Project_{target_id}.png", mime="image/png", use_container_width=True)
