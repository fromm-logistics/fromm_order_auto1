# streamlit_main.py
import streamlit as st
from md_main import run_md_main, run_md_fs_page, run_md_ss_page, run_md_general_page
from invoice_main import run_invoice_main
from photocard_main import run_photocard_main

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

# --- 화면 라우팅 처리 ---

# 1. 메인 메뉴 화면
if st.session_state.page == 'main':
    st.title("📋 메인 메뉴")
    st.markdown(
        '<h2 style="color:#1f77b4; font-size:28px; margin-bottom:5px;">'
        '구현된 기능</h2>',
        unsafe_allow_html=True
    )
    st.button("앨범 나누기", on_click=to_album)
    st.button("MD 나누기", on_click=to_md_main)
    st.button("송장", on_click=to_invoice_main)
    st.button("포토카드 수량", on_click=to_photocard_main)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(
        '<h2 style="color:#888888; font-size:28px; margin-bottom:5px;">'
        '구현 예정 기능</h2>',
        unsafe_allow_html=True
    )
    st.button("물류비 시뮬레이터 (구현예정)", disabled=True)

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
