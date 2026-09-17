# md_main.py
import streamlit as st
from MD_FS import run_md_fs
from MD_SS import run_md_ss
from MD_general import run_md_general
from weight_db import inject_floating_weight_btn


def run_md_main():
    inject_floating_weight_btn()
    st.button("◀ 이전으로 돌아가기", on_click=lambda: st.session_state.update(page="main"))
    st.title("📋 MD 나누기")

    st.button("FS 나누기",      on_click=lambda: st.session_state.update(page="md_fs"))
    st.button("SS 나누기",      on_click=lambda: st.session_state.update(page="md_ss"))
    st.button("General 나누기", on_click=lambda: st.session_state.update(page="md_general"))


def run_md_fs_page():
    run_md_fs()

def run_md_ss_page():
    run_md_ss()

def run_md_general_page():
    run_md_general()
