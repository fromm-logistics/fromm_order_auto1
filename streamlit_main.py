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
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;600;700&display=swap');

    /* ── 배경 ── */
    .stApp {
        background: #0e0810;
        font-family: 'Noto Sans KR', sans-serif;
    }

    /* 장식용 그라디언트 오브 */
    .stApp::before {
        content: '';
        position: fixed;
        top: -20%;
        left: -10%;
        width: 55%;
        height: 55%;
        background: radial-gradient(ellipse, rgba(200,130,170,0.13) 0%, transparent 70%);
        pointer-events: none;
        z-index: 0;
    }
    .stApp::after {
        content: '';
        position: fixed;
        bottom: -15%;
        right: -10%;
        width: 50%;
        height: 50%;
        background: radial-gradient(ellipse, rgba(160,110,200,0.10) 0%, transparent 70%);
        pointer-events: none;
        z-index: 0;
    }

    /* ── 레이아웃 ── */
    .block-container {
        max-width: 520px !important;
        padding-top: 64px !important;
        position: relative;
        z-index: 1;
    }

    /* ── 헤더 ── */
    .fromm-header {
        text-align: center;
        padding-bottom: 44px;
    }
    .fromm-wordmark {
        font-size: 2.6rem;
        font-weight: 700;
        letter-spacing: 6px;
        text-transform: uppercase;
        background: linear-gradient(135deg, #f0c8d8 0%, #d4a0c0 40%, #b888c8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        display: block;
        margin-bottom: 6px;
    }
    .fromm-sub {
        font-size: 0.78rem;
        letter-spacing: 3px;
        text-transform: uppercase;
        color: rgba(255,255,255,0.3);
        margin: 0;
    }
    .fromm-divider {
        width: 40px;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(200,140,180,0.6), transparent);
        margin: 16px auto 0;
    }

    /* ── 섹션 라벨 ── */
    .fromm-section {
        font-size: 0.68rem;
        font-weight: 600;
        letter-spacing: 3px;
        text-transform: uppercase;
        color: rgba(200,140,175,0.55);
        margin: 0 0 12px 2px;
    }

    /* ── 버튼 ── */
    .stButton > button {
        width: 100% !important;
        background: rgba(255,255,255,0.03) !important;
        color: rgba(255,255,255,0.85) !important;
        border: 1px solid rgba(200,140,175,0.18) !important;
        border-radius: 12px !important;
        padding: 17px 22px !important;
        font-size: 0.97rem !important;
        font-weight: 500 !important;
        font-family: 'Noto Sans KR', sans-serif !important;
        text-align: left !important;
        transition: all 0.25s ease !important;
        margin-bottom: 6px !important;
        backdrop-filter: blur(6px) !important;
        letter-spacing: 0.3px !important;
    }
    .stButton > button:hover {
        background: rgba(200,130,170,0.10) !important;
        border-color: rgba(200,130,170,0.5) !important;
        color: #ffffff !important;
        transform: translateX(5px) !important;
        box-shadow: 0 4px 24px rgba(180,100,150,0.15) !important;
    }
    .stButton > button:active {
        transform: translateX(2px) !important;
    }
    </style>

    <div class="fromm-header">
        <span class="fromm-wordmark">fromm</span>
        <p class="fromm-sub">Logistics System</p>
        <div class="fromm-divider"></div>
    </div>
    <div class="fromm-section">메뉴</div>
    """, unsafe_allow_html=True)

    st.button("📀  앨범 나누기", on_click=to_album)
    st.button("🛍️  MD 나누기", on_click=to_md_main)
    st.button("🧾  송장", on_click=to_invoice_main)
    st.button("🃏  포토카드 개수", on_click=to_photocard_main)
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
