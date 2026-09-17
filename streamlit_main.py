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
    # CSS 단독 주입
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600&display=swap');
.stApp { background: #0f1117; font-family: 'Noto Sans KR', sans-serif; }
.stButton, .stButton > button { position: relative !important; z-index: 10 !important; pointer-events: auto !important; }
.block-container { max-width: 640px !important; padding-top: 0 !important; position: relative; z-index: 1; }
.fromm-topbar { display: flex; align-items: center; padding: 28px 0; border-bottom: 1px solid rgba(255,255,255,0.06); margin-bottom: 36px; }
.fromm-logo-mark { width: 28px; height: 28px; background: #c890b8; border-radius: 6px; display: flex; align-items: center; justify-content: center; margin-right: 10px; font-size: 14px; flex-shrink: 0; }
.fromm-wordmark { font-size: 12px; font-weight: 600; letter-spacing: 3px; text-transform: uppercase; color: #e0e0e0; margin-right: 10px; }
.fromm-vdivider { width: 1px; height: 13px; background: rgba(255,255,255,0.15); margin-right: 10px; }
.fromm-system { font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: rgba(255,255,255,0.28); }
.fromm-section-header { display: flex; align-items: center; gap: 10px; margin: 0 0 8px; }
.fromm-section-label { font-size: 10px; font-weight: 600; letter-spacing: 2.5px; text-transform: uppercase; color: rgba(180,130,160,0.6); white-space: nowrap; }
.fromm-section-line { flex: 1; height: 1px; background: rgba(255,255,255,0.06); }
.fromm-section-gap { height: 20px; }
.stButton > button { width: 100% !important; background: rgba(255,255,255,0.03) !important; color: rgba(255,255,255,0.80) !important; border: 1px solid rgba(255,255,255,0.07) !important; border-radius: 10px !important; padding: 14px 16px !important; font-size: 13px !important; font-weight: 500 !important; font-family: 'Noto Sans KR', sans-serif !important; text-align: left !important; transition: background 0.18s, border-color 0.18s !important; margin-bottom: 4px !important; letter-spacing: 0.2px !important; }
.stButton > button:hover { background: rgba(200,130,170,0.07) !important; border-color: rgba(200,130,170,0.28) !important; color: #ffffff !important; }
.stButton > button:active { transform: scale(0.99) !important; }
</style>
""", unsafe_allow_html=True)

    # 헤더 HTML
    st.markdown("""
<div class="fromm-topbar">
    <div class="fromm-logo-mark">📦</div>
    <span class="fromm-wordmark">FROMM</span>
    <span class="fromm-vdivider"></span>
    <span class="fromm-system">Logistics System</span>
</div>
<div class="fromm-section-header">
    <span class="fromm-section-label">주문서</span>
    <span class="fromm-section-line"></span>
</div>
""", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.button("📀  앨범 나누기", on_click=to_album, use_container_width=True)
    with col2:
        st.button("🛍️  MD 나누기", on_click=to_md_main, use_container_width=True)
    with col3:
        st.button("🃏  포토카드 개수", on_click=to_photocard_main, use_container_width=True)

    st.markdown("""
<div class="fromm-section-gap"></div>
<div class="fromm-section-header">
    <span class="fromm-section-label">송장 업로드</span>
    <span class="fromm-section-line"></span>
</div>
""", unsafe_allow_html=True)

    st.button("🧾  송장", on_click=to_invoice_main, use_container_width=True)

    st.markdown("""
<div class="fromm-section-gap"></div>
<div class="fromm-section-header">
    <span class="fromm-section-label">물류비</span>
    <span class="fromm-section-line"></span>
</div>
""", unsafe_allow_html=True)

    st.button("📊  물류비 시뮬레이터", on_click=to_logistics_simulator, use_container_width=True)

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
