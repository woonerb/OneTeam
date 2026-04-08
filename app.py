import streamlit as st
import os
import pandas as pd
from datetime import datetime
import base64
import yfinance as yf
import FinanceDataReader as fdr
import json

# ==========================================
# [기능 설정] 데이터 저장소 초기화
# ==========================================
ATTACHMENTS_DIR = "attachments"
SHOUTS_FILE = "shouts.json"
REPORT_ATTACHMENTS_DIR = "report_attachments"
REPORTS_FILE = "reports.json"

os.makedirs(ATTACHMENTS_DIR, exist_ok=True)
os.makedirs(REPORT_ATTACHMENTS_DIR, exist_ok=True)

if not os.path.exists(SHOUTS_FILE):
    with open(SHOUTS_FILE, "w", encoding="utf-8") as f: json.dump([], f)
if not os.path.exists(REPORTS_FILE):
    with open(REPORTS_FILE, "w", encoding="utf-8") as f: json.dump([], f)

def load_shouts():
    with open(SHOUTS_FILE, "r", encoding="utf-8") as f: return json.load(f)

def save_shout(author, msg, files):
    shouts = load_shouts()
    saved_file_names = []
    for uploaded_file in files:
        file_path = os.path.join(ATTACHMENTS_DIR, uploaded_file.name)
        with open(file_path, "wb") as f: f.write(uploaded_file.getbuffer())
        saved_file_names.append(uploaded_file.name)
    shouts.append({"author": author, "msg": msg, "files": saved_file_names, "time": datetime.now().strftime("%H:%M")})
    with open(SHOUTS_FILE, "w", encoding="utf-8") as f: json.dump(shouts, f)

def load_reports():
    with open(REPORTS_FILE, "r", encoding="utf-8") as f: return json.load(f)

def save_report(title, author, content, files):
    reports = load_reports()
    saved_file_names = []
    for uploaded_file in files:
        file_path = os.path.join(REPORT_ATTACHMENTS_DIR, uploaded_file.name)
        with open(file_path, "wb") as f: f.write(uploaded_file.getbuffer())
        saved_file_names.append(uploaded_file.name)
    reports.insert(0, {
        "id": len(reports) + 1, "title": title, "author": author, "content": content,
        "files": saved_file_names, "date": datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    with open(REPORTS_FILE, "w", encoding="utf-8") as f: json.dump(reports, f)

# ==========================================
# [팝업 UI] 리포트 및 외치기
# ==========================================
@st.dialog("📄 리포트 상세 보기", width="large")
def show_report_detail(report):
    st.markdown(f"#### {report['title']}")
    st.markdown(f"<span style='font-size: 11px;'>**작성자:** {report['author']} | **작성일:** {report['date']}</span>", unsafe_allow_html=True)
    st.divider()
    st.markdown(f"<div style='font-size: 11px; min-height: 100px;'>{report['content']}</div>", unsafe_allow_html=True)
    st.divider()
    
    if report['files']:
        st.write("📎 **첨부파일**")
        for fname in report['files']:
            file_path = os.path.join(REPORT_ATTACHMENTS_DIR, fname)
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    st.download_button(label=f"⬇️ {fname}", data=f, file_name=fname, key=f"rpt_dl_{report['id']}_{fname}")
    
    st.write("")
    if st.button("🗑️ 이 리포트 삭제하기", use_container_width=True, type="secondary"):
        reports = load_reports()
        updated_reports = [r for r in reports if r['id'] != report['id']]
        with open(REPORTS_FILE, "w", encoding="utf-8") as f: json.dump(updated_reports, f)
        st.success("삭제되었습니다. (창을 닫고 새로고침 해주세요)")
        st.rerun()

@st.dialog("📂 전체 투자 리포트 및 작성", width="large")
def show_all_reports_dialog():
    tab1, tab2 = st.tabs(["📋 전체 목록", "✍️ 새 리포트 업로드"])
    with tab1:
        reports = load_reports()
        if not reports: st.info("등록된 리포트가 없습니다.")
        else:
            for r in reports:
                if st.button(f"[{r['date']}] {r['title']} - {r['author']}", key=f"all_rpt_{r['id']}", use_container_width=True):
                    show_report_detail(r)
    with tab2:
        st.markdown("<span style='font-size: 11px;'>새로운 인사이트를 공유하세요.</span>", unsafe_allow_html=True)
        rpt_title = st.text_input("리포트 제목")
        rpt_content = st.text_area("리포트 요약 및 본문", height=100)
        rpt_files = st.file_uploader("관련 자료 첨부", accept_multiple_files=True)
        if st.button("🚀 업로드", use_container_width=True):
            if not rpt_title or not rpt_content: st.warning("제목과 본문을 입력해주세요.")
            else:
                save_report(rpt_title, st.session_state.nickname, rpt_content, rpt_files)
                st.success("등록 완료!")
                st.rerun()

@st.dialog("📢 외치기 수신함")
def show_shouts_dialog():
    shouts = load_shouts()
    if not shouts:
        st.write("새로운 외치기가 없습니다.")
        return
    if 'shout_idx' not in st.session_state: st.session_state.shout_idx = len(shouts) - 1
    idx = st.session_state.shout_idx
    total = len(shouts)
    current_shout = shouts[idx]

    st.markdown(f"<span style='font-size: 11px;'>**보낸사람:** 👤{current_shout['author']} `{current_shout['time']}`</span>", unsafe_allow_html=True)
    st.info(current_shout['msg'])
    if current_shout['files']:
        st.write("📎 **첨부파일**")
        for fname in current_shout['files']:
            file_path = os.path.join(ATTACHMENTS_DIR, fname)
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    st.download_button(label=f"⬇️ {fname}", data=f, file_name=fname, key=f"dl_{idx}_{fname}")
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("◀ 이전", disabled=(idx == 0), use_container_width=True):
            st.session_state.shout_idx -= 1
            st.rerun()
    with col2: st.markdown(f"<div style='text-align: center; margin-top: 5px; font-size: 11px;'><b>{idx + 1} / {total}</b></div>", unsafe_allow_html=True)
    with col3:
        if st.button("다음 ▶", disabled=(idx == total - 1), use_container_width=True):
            st.session_state.shout_idx += 1
            st.rerun()

@st.dialog("📢 새 외치기 작성")
def write_shout_dialog():
    msg = st.text_area("전체 팀원에게 전달할 메시지", height=80)
    uploaded_files = st.file_uploader("첨부파일(최대 5개)", accept_multiple_files=True)
    if len(uploaded_files) > 5: st.error("🚨 최대 5개까지만 가능합니다.")
    if st.button("🚀 전체 전송", use_container_width=True):
        if not msg: st.warning("내용을 입력해주세요.")
        elif len(uploaded_files) <= 5:
            save_shout(st.session_state.nickname, msg, uploaded_files)
            st.success("전송 완료!")
            st.session_state.last_seen_shout_count = len(load_shouts()) 
            st.session_state.shout_idx = st.session_state.last_seen_shout_count - 1
            st.rerun()

# ==========================================
# 기존 API 로직 및 이미지 강제 추적기
# ==========================================
def get_image_as_base64(filename):
    # [수정됨] 경로를 찾지 못하는 버그를 막기 위해 모든 가능성을 탐색합니다.
    paths_to_try = [
        filename, # 1. 현재 터미널 실행 폴더
        os.path.join(os.getcwd(), filename) # 2. 강제 절대 경로 조합
    ]
    
    # 3. 만약 파이썬 스크립트 위치가 확인된다면 그곳도 탐색
    if '__file__' in globals():
        paths_to_try.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), filename))

    for path in paths_to_try:
        if os.path.exists(path):
            try:
                with open(path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode()
                    # 파일 확장자에 따라 MIME 타입 자동 지정
                    mime_type = "image/jpeg" if filename.lower().endswith(".jpg") or filename.lower().endswith(".jpeg") else "image/png"
                    return f"data:{mime_type};base64,{encoded_string}"
            except Exception:
                continue
    return None

@st.cache_data(ttl=3600)
def fetch_global_data(ticker, target_date):
    try:
        end_date = pd.to_datetime(target_date) + pd.Timedelta(days=1)
        start_date = end_date - pd.Timedelta(days=7)
        df = yf.download(ticker, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'), progress=False)
        if len(df) >= 2:
            current_val = float(df['Close'].iloc[-1].iloc[0]) if isinstance(df['Close'], pd.DataFrame) else float(df['Close'].iloc[-1])
            prev_val = float(df['Close'].iloc[-2].iloc[0]) if isinstance(df['Close'], pd.DataFrame) else float(df['Close'].iloc[-2])
            delta_val = current_val - prev_val
            delta_pct = (delta_val / prev_val) * 100
            return current_val, delta_val, delta_pct
        return 0.0, 0.0, 0.0
    except: return 0.0, 0.0, 0.0

@st.cache_data(ttl=3600)
def fetch_kr_bond_data(target_date):
    try:
        end_date = pd.to_datetime(target_date) + pd.Timedelta(days=1)
        start_date = end_date - pd.Timedelta(days=10)
        df = fdr.DataReader('KR3YT=RR', start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
        if len(df) >= 2:
            current_val = float(df['Close'].iloc[-1])
            prev_val = float(df['Close'].iloc[-2])
            delta_val = current_val - prev_val
            delta_pct = (delta_val / prev_val) * 100
            return current_val, delta_val, delta_pct
        return 0.0, 0.0, 0.0
    except: return 0.0, 0.0, 0.0

def get_market_weather(asset_type, d_val, d_pct):
    if asset_type == "stock":
        if d_pct > 0.5: return "☀️"
        elif d_pct < -0.5: return "☁️"
        else: return "⛅"
    elif asset_type == "currency":
        if d_pct < -0.3: return "☀️"
        elif d_pct > 0.3: return "☁️"
        else: return "⛅"
    elif asset_type == "bond":
        if d_val < -0.02: return "☀️"
        elif d_val > 0.02: return "☁️"
        else: return "⛅"
    elif asset_type == "fear":
        if d_pct < -1.0: return "☀️"
        elif d_pct > 1.0: return "☁️"
        else: return "⛅"
    return "⛅"

# 1. 화면 설정
st.set_page_config(layout="wide", page_title="아이엠 원 팀")

# CSS 주입
st.markdown("""
    <style>
        .block-container { padding-top: 2rem !important; padding-bottom: 0rem !important; margin-top: 0 !important; }
        [data-testid="stMetricLabel"] p { font-size: 10px !important; font-weight: bold !important; margin-bottom: 2px !important;}
        [data-testid="stMetricValue"] { font-size: 16px !important; }
        [data-testid="stMetricDelta"] svg { width: 9px !important; height: 9px !important; }
        [data-testid="stMetricDelta"] div { font-size: 9px !important; }
        .stAlert p { font-size: 10px !important; margin: 0 !important; padding: 2px !important;}
        .stAlert { min-height: 20px !important; padding: 5px !important; margin-bottom: 5px !important; }
        .stMarkdown p { font-size: 10px !important; margin-bottom: 5px !important; }
        .stButton button { font-size: 10px !important; padding: 2px 5px !important; min-height: 24px !important; height: 26px !important;}
        .stTextInput input { font-size: 10px !important; height: 26px !important; min-height: 26px !important;}
        .stChatInput textarea { font-size: 10px !important; min-height: 30px !important; padding: 5px !important;}
        hr { margin: 8px 0px !important; }
        .header-container { display: flex; align-items: center; gap: 15px; margin-bottom: 10px; padding-top: 10px; }
        .header-text { font-size: 28px !important; font-weight: 900 !important; color: #1f1f1f; line-height: 1; margin: 0; padding: 0; }
        
        /* [원본 복원] 투명화 효과 삭제. 원본 파일 그대로 출력 */
        .header-container img { height: 32px !important; display: block; border-radius: 4px; box-shadow: 0px 1px 3px rgba(0,0,0,0.2); } 
        
        .wc-container { 
            display: flex; flex-wrap: wrap; justify-content: center; align-items: center; 
            gap: 12px; padding: 30px; background-color: rgba(255, 255, 255, 0.05); 
            border-radius: 15px; margin-bottom: 8px; overflow: hidden; position: relative; min-height: 200px; 
        }
        .wc-container span { display: inline-block; line-height: 1; transition: all 0.3s ease; text-shadow: 0px 2px 4px rgba(0,0,0,0.1); position: relative; }
        .wc-container span:hover { transform: scale(1.1); z-index: 10; }
    </style>
""", unsafe_allow_html=True)

current_shouts = load_shouts()
if 'last_seen_shout_count' not in st.session_state: st.session_state.last_seen_shout_count = len(current_shouts)
if len(current_shouts) > st.session_state.last_seen_shout_count:
    st.session_state.shout_idx = len(current_shouts) - 1
    st.session_state.last_seen_shout_count = len(current_shouts)
    show_shouts_dialog()

# ==========================================
# 화면 레이아웃
# ==========================================
# 폴더 내에 im_logo.png 나 im_logo.jpg 가 있으면 알아서 잡아냅니다.
logo_base64 = get_image_as_base64("im_logo.png") 
if not logo_base64: 
    logo_base64 = get_image_as_base64("im_logo.jpg") 

if logo_base64:
    logo_html = f'<img src="{logo_base64}"/>'
else:
    # 정 못찾았을 경우 에러 방지용 이모티콘
    logo_html = f'<span style="font-size: 32px; line-height: 1;">🏢</span>'

st.markdown(f"<div class='header-container'>{logo_html}<div class='header-text'>아이엠 원 팀</div></div>", unsafe_allow_html=True)
st.divider()

TARGET_DATE = "2026-03-31"
left_column, right_column = st.columns([3, 1])

kospi_v, kospi_d, kospi_p = fetch_global_data("^KS11", TARGET_DATE)
sp500_v, sp500_d, sp500_p = fetch_global_data("^GSPC", TARGET_DATE)
usdkrw_v, usdkrw_d, usdkrw_p = fetch_global_data("KRW=X", TARGET_DATE)
ndx_v, ndx_d, ndx_p = fetch_global_data("^IXIC", TARGET_DATE)
kr3y_v, kr3y_d, kr3y_p = fetch_kr_bond_data(TARGET_DATE)
tnx_v, tnx_d, tnx_p = fetch_global_data("^TNX", TARGET_DATE)
wti_v, wti_d, wti_p = fetch_global_data("CL=F", TARGET_DATE)
gold_v, gold_d, gold_p = fetch_global_data("GC=F", TARGET_DATE)
vix_v, vix_d, vix_p = fetch_global_data("^VIX", TARGET_DATE)

weather_list = [
    get_market_weather('stock', kospi_d, kospi_p), get_market_weather('stock', sp500_d, sp500_p),
    get_market_weather('currency', usdkrw_d, usdkrw_p), get_market_weather('stock', ndx_d, ndx_p),
    get_market_weather('bond', kr3y_d, kr3y_p), get_market_weather('bond', tnx_d, tnx_p),
    get_market_weather('fear', wti_d, wti_p), get_market_weather('fear', gold_d, gold_p),
    get_market_weather('fear', vix_d, vix_p)
]
bad_count = weather_list.count("☁️")

if bad_count <= 3:
    total_weather_icon, weather_reason, box_color, border_color = "☀️ 맑음", f"위험 시그널 {bad_count}개. 투자 심리 안정.", "rgba(0, 230, 118, 0.1)", "#00E676"
elif bad_count <= 6:
    total_weather_icon, weather_reason, box_color, border_color = "⛅ 구름조금", f"위험 시그널 {bad_count}개. 불확실성 장세.", "rgba(255, 213, 79, 0.1)", "#FFD54F"
else:
    total_weather_icon, weather_reason, box_color, border_color = "⛈️ 뇌우", f"위험 시그널 {bad_count}개. 리스크 관리 필요.", "rgba(255, 82, 82, 0.1)", "#FF5252"

with left_column:
    st.markdown(f"<div style='padding: 8px; border-left: 4px solid {border_color}; background-color: {box_color}; border-radius: 4px; margin-bottom: 8px;'><div style='font-size: 10px; font-weight: bold; color: #B0BEC5; margin-bottom: 2px;'>현재 iM 기상도</div><div style='font-size: 16px; font-weight: bold; margin-bottom: 2px;'>{total_weather_icon}</div><div style='font-size: 10px; line-height: 1.2;'>{weather_reason}</div></div>", unsafe_allow_html=True)
    st.markdown("<h3 style='font-size: 11px; margin-bottom: 5px; margin-top: 5px;'>📊 그룹 통합 금융 지표</h3>", unsafe_allow_html=True)
    
    if 'show_all_metrics' not in st.session_state: st.session_state.show_all_metrics = False
    def format_metric(val, d_val, d_pct, prefix="", suffix="", is_rate=False):
        if val == 0.0: return "API 에러", "데이터 없음"
        if is_rate: return f"{val:.2f}{suffix}", f"{d_val:+.2f}%p"
        return f"{prefix}{val:,.2f}{suffix}", f"{d_val:+,.2f} ({d_pct:+.2f}%)"

    col1, col2, col3, col_btn = st.columns([3, 3, 3, 1])
    with col1: st.metric(label=f"코스피 {weather_list[0]}", value=format_metric(kospi_v, kospi_d, kospi_p)[0], delta=format_metric(kospi_v, kospi_d, kospi_p)[1])
    with col2: st.metric(label=f"S&P 500 {weather_list[1]}", value=format_metric(sp500_v, sp500_d, sp500_p)[0], delta=format_metric(sp500_v, sp500_d, sp500_p)[1])
    with col3: st.metric(label=f"환율 {weather_list[2]}", value=format_metric(usdkrw_v, usdkrw_d, usdkrw_p)[0], delta=format_metric(usdkrw_v, usdkrw_d, usdkrw_p)[1])
    
    with col_btn:
        st.write("") 
        if st.button("접기/펴기", key="metric_toggle"): st.session_state.show_all_metrics = not st.session_state.show_all_metrics; st.rerun()

    if st.session_state.show_all_metrics:
        row2_col1, row2_col2, row2_col3, _ = st.columns([3, 3, 3, 1])
        with row2_col1: st.metric(label=f"나스닥 {weather_list[3]}", value=format_metric(ndx_v, ndx_d, ndx_p)[0], delta=format_metric(ndx_v, ndx_d, ndx_p)[1])
        with row2_col2: st.metric(label=f"국고채3년 {weather_list[4]}", value=format_metric(kr3y_v, kr3y_d, kr3y_p, suffix="%", is_rate=True)[0], delta=format_metric(kr3y_v, kr3y_d, kr3y_p, suffix="%", is_rate=True)[1])
        with row2_col3: st.metric(label=f"미국채10년 {weather_list[5]}", value=format_metric(tnx_v, tnx_d, tnx_p, suffix="%", is_rate=True)[0], delta=format_metric(tnx_v, tnx_d, tnx_p, suffix="%", is_rate=True)[1])
        row3_col1, row3_col2, row3_col3, _ = st.columns([3, 3, 3, 1])
        with row3_col1: st.metric(label=f"WTI 원유 {weather_list[6]}", value=format_metric(wti_v, wti_d, wti_p, prefix="$")[0], delta=format_metric(wti_v, wti_d, wti_p, prefix="$")[1])
        with row3_col2: st.metric(label=f"금(Gold) {weather_list[7]}", value=format_metric(gold_v, gold_d, gold_p, prefix="$")[0], delta=format_metric(gold_v, gold_d, gold_p, prefix="$")[1])
        with row3_col3: st.metric(label=f"VIX {weather_list[8]}", value=format_metric(vix_v, vix_d, vix_p)[0], delta=format_metric(vix_v, vix_d, vix_p)[1])

    st.write("---")
    st.markdown("<h3 style='font-size: 11px; margin-bottom: 5px; margin-top: 0px;'>☁️ 경제 키워드 (포컬 스타일)</h3>", unsafe_allow_html=True)
    wordcloud_html = "<div class='wc-container'><span style='font-size: 34px; color: #00D2A0; font-weight: 900; order: 1;'>iM뱅크 시중은행</span><span style='font-size: 32px; color: #FF5252; font-weight: 900; order: 2;'>환율 방어</span><span style='font-size: 26px; color: #00E676; font-weight: 800; order: 3;'>국고채 3년물</span><span style='font-size: 24px; color: #FFFFFF; font-weight: 800; order: 4;'>인플레이션 둔화</span><span style='font-size: 22px; color: #00B0FF; font-weight: 700; order: 5;'>채권운용 전략</span><span style='font-size: 14px; color: #00D2A0; order: 6;'>외국인 순매수</span><span style='font-size: 13px; color: #E0E0E0; order: 7;'>기준금리 인하</span><span style='font-size: 12px; color: #FFD54F; order: 8;'>연준(Fed)</span><span style='font-size: 10px; color: #B0BEC5; order: 9;'>밸류업 프로그램</span><span style='font-size: 9px; color: #9E9E9E; order: 10;'>CPI</span><span style='font-size: 8px; color: #757575; order: 11;'>지정학적 리스크</span></div>"
    st.markdown(wordcloud_html, unsafe_allow_html=True)
    st.write("---")
    
    col_rpt1, col_rpt2 = st.columns([8, 2])
    with col_rpt1: st.markdown("<h3 style='font-size: 11px; margin-bottom: 0px;'>📝 투자 리포트</h3>", unsafe_allow_html=True)
    with col_rpt2:
        if st.button("➕ 전체", use_container_width=True): show_all_reports_dialog()
            
    reports_data = load_reports()
    if not reports_data: st.info("➕ 버튼으로 리포트 작성")
    else:
        for r in reports_data[:5]:
            if st.button(f"📄 {r['title']} [{r['author']} | {r['date']}]", key=f"main_rpt_{r['id']}", use_container_width=True):
                show_report_detail(r)

with right_column:
    st.markdown("<h3 style='font-size: 11px; margin-bottom: 5px;'>💬 오픈채팅</h3>", unsafe_allow_html=True)
    if 'nickname' not in st.session_state: st.session_state.nickname = "원팀맨"
    st.session_state.nickname = st.text_input("닉네임", st.session_state.nickname, label_visibility="collapsed")
    col_shout_btn, col_read_btn = st.columns(2)
    with col_shout_btn:
        if st.button("📢 외치기", use_container_width=True): write_shout_dialog()
    with col_read_btn:
        unread_count = len(current_shouts) - st.session_state.get('shout_idx', len(current_shouts) - 1) - 1
        btn_text = f"📫 ({unread_count})" if unread_count > 0 else "📫 수신함"
        if st.button(btn_text, use_container_width=True): show_shouts_dialog()
    st.write("---")
    today_str = datetime.now().strftime("%Y%m%d")
    chat_file = f"chat_{today_str}.txt"
    if not os.path.exists(chat_file):
        with open(chat_file, "w", encoding="utf-8") as f: f.write("")
    with open(chat_file, "r", encoding="utf-8") as f: chat_history = f.readlines()
    chat_container = st.container(height=300)
    with chat_container:
        for line in chat_history:
            if " | " in line:
                parts = line.strip().split(" | ", 2)
                if len(parts) == 3:
                    user, time, msg = parts
                    if user == "캡틴칼퇴": user = "원팀맨"
                    role = "user" if user == st.session_state.nickname else "assistant"
                    with st.chat_message(role):
                        st.markdown(f"<span style='font-size: 9px;'>**{user}** `{time}`</span>", unsafe_allow_html=True)
                        st.markdown(f"<div style='font-size: 10px; margin-top: 2px;'>{msg}</div>", unsafe_allow_html=True)
    new_msg = st.chat_input("인사이트 공유...")
    if new_msg:
        current_time = datetime.now().strftime("%H:%M")
        with open(chat_file, "a", encoding="utf-8") as f: f.write(f"{st.session_state.nickname} | {current_time} | {new_msg}\n")
        st.rerun()