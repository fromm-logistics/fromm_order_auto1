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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Noto+Sans+KR:wght@300;400;500;600;700&display=swap');

    /* ── 배경 ── */
    .stApp {
        background: #0c0810;
        font-family: 'Noto Sans KR', 'Inter', sans-serif;
    }

    /* ── Light Rays 애니메이션 ── */
    @keyframes rotateRays {
        from { transform: translate(-50%, 0) rotate(0deg); }
        to   { transform: translate(-50%, 0) rotate(360deg); }
    }
    @keyframes pulseFade {
        0%, 100% { opacity: 0.85; }
        50%       { opacity: 1.0; }
    }

    .light-rays-wrap {
        position: fixed;
        top: -60vh;
        left: 50%;
        transform: translate(-50%, 0);
        width: 300vw;
        height: 300vh;
        pointer-events: none;
        z-index: 0;
        animation: rotateRays 40s linear infinite, pulseFade 8s ease-in-out infinite;
        background: conic-gradient(
            from 0deg at 50% 50%,
            transparent       0deg,
            rgba(220,155,190,0.22)  4deg,
            transparent       8deg,
            transparent      22deg,
            rgba(190,130,220,0.18) 26deg,
            transparent      30deg,
            transparent      44deg,
            rgba(220,155,190,0.25) 48deg,
            transparent      52deg,
            transparent      70deg,
            rgba(190,130,220,0.18) 73deg,
            transparent      77deg,
            transparent      95deg,
            rgba(220,155,190,0.22) 98deg,
            transparent     102deg,
            transparent     118deg,
            rgba(190,130,220,0.18) 121deg,
            transparent     125deg,
            transparent     145deg,
            rgba(220,155,190,0.20) 148deg,
            transparent     152deg,
            transparent     170deg,
            rgba(190,130,220,0.15) 173deg,
            transparent     177deg,
            transparent     195deg,
            rgba(220,155,190,0.20) 198deg,
            transparent     202deg,
            transparent     220deg,
            rgba(190,130,220,0.18) 223deg,
            transparent     227deg,
            transparent     246deg,
            rgba(220,155,190,0.22) 249deg,
            transparent     253deg,
            transparent     270deg,
            rgba(190,130,220,0.15) 273deg,
            transparent     277deg,
            transparent     295deg,
            rgba(220,155,190,0.20) 298deg,
            transparent     302deg,
            transparent     320deg,
            rgba(190,130,220,0.18) 323deg,
            transparent     327deg,
            transparent     345deg,
            rgba(220,155,190,0.20) 348deg,
            transparent     352deg,
            transparent     360deg
        );
        filter: blur(5px);
    }

    .top-glow {
        position: fixed;
        top: -10vh;
        left: 50%;
        transform: translateX(-50%);
        width: 80vw;
        height: 50vh;
        background: radial-gradient(ellipse at 50% 0%, rgba(210,140,180,0.30) 0%, transparent 70%);
        pointer-events: none !important;
        z-index: 0;
    }

    /* ── 클릭 보장 ── */
    .stButton, .stButton > button {
        position: relative !important;
        z-index: 10 !important;
        pointer-events: auto !important;
    }

    /* ── 레이아웃 ── */
    .block-container {
        max-width: 560px !important;
        padding-top: 56px !important;
        position: relative;
        z-index: 1;
    }

    /* ── 헤더 ── */
    .fromm-header {
        text-align: center;
        padding-bottom: 48px;
    }
    .fromm-wordmark {
        font-size: 2.4rem;
        font-weight: 700;
        letter-spacing: 10px;
        text-transform: uppercase;
        background: linear-gradient(135deg, #f0c8d8 0%, #d4a0c0 45%, #b888c8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        display: block;
        margin-bottom: 8px;
    }
    .fromm-sub {
        font-size: 0.72rem;
        letter-spacing: 4px;
        text-transform: uppercase;
        color: rgba(255,255,255,0.22);
        margin: 0;
    }
    .fromm-divider {
        width: 40px;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(210,140,180,0.6), transparent);
        margin: 20px auto 0;
    }

    /* ── 섹션 그룹 ── */
    .menu-section {
        margin-bottom: 8px;
    }
    .section-label {
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 0 0 8px 0;
        padding: 0 2px;
    }
    .section-label-text {
        font-size: 0.62rem;
        font-weight: 600;
        letter-spacing: 3px;
        text-transform: uppercase;
        color: rgba(200,140,175,0.5);
        white-space: nowrap;
    }
    .section-label-line {
        flex: 1;
        height: 1px;
        background: linear-gradient(90deg, rgba(200,140,175,0.2), transparent);
    }
    .section-gap {
        height: 20px;
    }

    /* ── 버튼 ── */
    .stButton > button {
        width: 100% !important;
        background: rgba(255,255,255,0.03) !important;
        color: rgba(255,255,255,0.80) !important;
        border: 1px solid rgba(210,140,175,0.12) !important;
        border-radius: 10px !important;
        padding: 15px 20px !important;
        font-size: 0.93rem !important;
        font-weight: 500 !important;
        font-family: 'Noto Sans KR', sans-serif !important;
        text-align: left !important;
        transition: all 0.2s ease !important;
        margin-bottom: 4px !important;
        backdrop-filter: blur(8px) !important;
        letter-spacing: 0.2px !important;
    }
    .stButton > button:hover {
        background: rgba(210,130,170,0.08) !important;
        border-color: rgba(210,130,170,0.38) !important;
        color: #ffffff !important;
        transform: translateX(5px) !important;
        box-shadow: 0 3px 20px rgba(180,100,150,0.10) !important;
    }
    .stButton > button:active {
        transform: translateX(2px) !important;
    }
    </style>

    <div class="light-rays-wrap"></div>
    <div class="top-glow"></div>

    <div class="fromm-header">
        <span class="fromm-wordmark">fromm</span>
        <p class="fromm-sub">Logistics System</p>
        <div class="fromm-divider"></div>
    </div>

    <div class="section-label">
        <span class="section-label-text">주문서</span>
        <span class="section-label-line"></span>
    </div>
    """, unsafe_allow_html=True)

    st.button("📀  앨범 나누기", on_click=to_album)
    st.button("🛍️  MD 나누기", on_click=to_md_main)
    st.button("🃏  포토카드 개수", on_click=to_photocard_main)

    st.markdown("""
    <div class="section-gap"></div>
    <div class="section-label">
        <span class="section-label-text">송장 업로드</span>
        <span class="section-label-line"></span>
    </div>
    """, unsafe_allow_html=True)

    st.button("🧾  송장", on_click=to_invoice_main)

    st.markdown("""
    <div class="section-gap"></div>
    <div class="section-label">
        <span class="section-label-text">물류비</span>
        <span class="section-label-line"></span>
    </div>
    """, unsafe_allow_html=True)

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
