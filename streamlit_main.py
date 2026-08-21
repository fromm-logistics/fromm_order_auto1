# streamlit_main.py
import streamlit as st
from album_copy_nnnnnnn_copy import run_album
from md_main import run_md_main, run_md_fs_page, run_md_ss_page, run_md_general_page
from invoice_main import run_invoice_main
from photocard_main import run_photocard_main
from logistics_simulator import run_logistics_simulator

# 페이지 상태 초기화 (메인에서만!)
if 'page' not in st.session_state:
    st.session_state.page = 'main'

# 송장 서브 메뉴 상태도 메인에서 기본 정의
if 'invoice_courier' not in st.session_state:
    st.session_state.invoice_courier = None
if 'invoice_region' not in st.session_state:
    st.session_state.invoice_region = None

# --- 페이지 이동용 콜백 함수들 ---
def to_album():
    st.session_state.page = 'album_copy_nnnnnnn_copy'

def to_md_main():
    st.session_state.page = 'md_main'

def to_invoice_main():
    st.session_state.page = 'invoice_main'
    st.session_state.invoice_courier = None
    st.session_state.invoice_region = None

def to_photocard_main():
    st.session_state.page = 'photocard'

def to_logistics_simulator():
    st.session_state.page = 'logistics_simulator'

# --- 화면 라우팅 처리 ---

# 1. 메인 메뉴 화면
if st.session_state.page == 'main':
    st.markdown("""
    <style>
    /* ── 배경 그라디언트 ── */
    .stApp {
        background: linear-gradient(160deg, #0d1117 0%, #161b27 50%, #0d1117 100%);
    }

    /* ── 사이드바 숨기기 영역 제거용 ── */
    [data-testid="stSidebar"] { display: none; }

    /* ── 메인 컨테이너 중앙 정렬 ── */
    .block-container {
        max-width: 560px !important;
        padding-top: 60px !important;
    }

    /* ── 헤더 타이틀 ── */
    .main-title {
        text-align: center;
        padding: 0 0 36px 0;
    }
    .main-title .logo {
        font-size: 3rem;
        display: block;
        margin-bottom: 8px;
    }
    .main-title h1 {
        font-size: 1.9rem;
        font-weight: 700;
        color: #f0f4ff;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .main-title p {
        color: #6b7a99;
        font-size: 0.9rem;
        margin: 6px 0 0 0;
    }

    /* ── 섹션 라벨 ── */
    .section-label {
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #4a90d9;
        margin: 28px 0 10px 2px;
    }

    /* ── 버튼 카드 스타일 ── */
    .stButton > button {
        width: 100% !important;
        background: rgba(255,255,255,0.04) !important;
        color: #e8edf5 !important;
        border: 1px solid rgba(255,255,255,0.09) !important;
        border-radius: 14px !important;
        padding: 18px 22px !important;
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        text-align: left !important;
        transition: all 0.2s ease !important;
        margin-bottom: 2px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3) !important;
        letter-spacing: 0.2px !important;
    }
    .stButton > button:hover {
        background: rgba(74, 144, 217, 0.12) !important;
        border-color: rgba(74, 144, 217, 0.4) !important;
        color: #ffffff !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(74, 144, 217, 0.15) !important;
    }
    .stButton > button:active {
        transform: translateY(0px) !important;
    }

    /* ── 구분선 ── */
    hr { border-color: rgba(255,255,255,0.07) !important; }
    </style>

    <div class="main-title">
        <span class="logo">📦</span>
        <h1>Fromm Logistics</h1>
        <p>물류 자동화 도구 모음</p>
    </div>
    <div class="section-label">메뉴</div>
    """, unsafe_allow_html=True)

    st.button("📀  앨범 나누기", on_click=to_album)
    st.button("🛍️  MD 나누기", on_click=to_md_main)
    st.button("🧾  송장", on_click=to_invoice_main)
    st.button("🃏  포토카드 수", on_click=to_photocard_main)
    st.button("📊  물류비 시뮬레이터", on_click=to_logistics_simulator)

# 2. 송장
elif st.session_state.page == 'invoice_main':
    run_invoice_main()

# 3. 기존 기타 페이지들
elif st.session_state.page == 'album_copy_nnnnnnn_copy':
    run_album()

elif st.session_state.page == 'md_main':
    run_md_main()

elif st.session_state.page == 'md_fs':
    run_md_fs_page()

elif st.session_state.page == 'md_ss':
    run_md_ss_page()

elif st.session_state.page == 'md_general':
    run_md_general_page()

elif st.session_state.page == 'photocard':
    run_photocard_main()

elif st.session_state.page == 'logistics_simulator':
    run_logistics_simulator()
