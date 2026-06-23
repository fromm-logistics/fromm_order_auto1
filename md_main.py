# md_main.py
import streamlit as st
from MD_FS1 import run_md_fs
from MD_SS import run_md_ss
from MD_general import run_md_general


def run_md_main():
    """MD 나누기 메인 페이지를 렌더링합니다."""
    st.button("◀ 이전으로 돌아가기", on_click=lambda: st.session_state.update(page="main"))
    st.title("📋 MD 나누기")

    st.markdown(
        '<h2 style="color:#4f66b3; font-size:22px; margin-bottom:5px;">'
        '구현된 기능</h2>',
        unsafe_allow_html=True
    )
    st.button("FS 나누기", on_click=lambda: st.session_state.update(page="md_fs"))
    st.button("SS 나누기", on_click=lambda: st.session_state.update(page="md_ss"))
    st.button("General 나누기", on_click=lambda: st.session_state.update(page="md_general"))
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(
        '<h2 style="color:#888888; font-size:28px; margin-bottom:5px;">'
        '구현 예정 기능</h2>',
        unsafe_allow_html=True
    )
    st.button("송장등록 (구현예정)", disabled=True)
    st.button("물류비 시뮬레이터 (구현예정)", disabled=True)
    st.button("포토카드 갯수 (구현예정)", disabled=True)

def run_md_fs_page():
    """FS1 나누기 페이지 호출"""
    run_md_fs()  # MD_FS 모듈의 실행 함수

def run_md_ss_page():
    """SS 나누기 페이지 호출"""
    run_md_ss()  # MD_SS 모듈의 실행 함수

def run_md_general_page():
    """General 나누기 페이지 호출"""
    run_md_general()  # MD_general 모듈의 실행 함수
