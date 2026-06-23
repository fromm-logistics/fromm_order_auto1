# streamlit_main.py
import streamlit as st
from album_copy_nnnnnnn_copy import run_album
from md_main import run_md_main, run_md_fs_page, run_md_ss_page, run_md_general_page
import streamlit as st


#st.set_page_config(page_title="메인 메뉴", layout="wide")

# 페이지 상태 초기화 (메인에서만!)
if 'page' not in st.session_state:
    st.session_state.page = 'main'

def to_album():
    st.session_state.page = 'album_copy_nnnnnnn_copy'
    

def to_md_main():
    st.session_state.page = 'md_main'
    

if st.session_state.page == 'main':
    st.title("📋 메인 메뉴")
    st.markdown(
        '<h2 style="color:#1f77b4; font-size:28px; margin-bottom:5px;">'
        '구현된 기능</h2>',
        unsafe_allow_html=True
    )
    st.button("앨범 나누기", on_click=to_album)
    st.button("MD 나누기", on_click=to_md_main)
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(
        '<h2 style="color:#888888; font-size:28px; margin-bottom:5px;">'
        '구현 예정 기능</h2>',
        unsafe_allow_html=True
    )
    st.button("송장등록 (구현예정)", disabled=True)
    st.button("물류비 시뮬레이터 (구현예정)", disabled=True)
    st.button("포토카드 갯수 (구현예정)", disabled=True)

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
    