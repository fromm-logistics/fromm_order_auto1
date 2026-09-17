# md_main.py
import streamlit as st
from MD_FS import run_md_fs
from MD_SS import run_md_ss
from MD_general import run_md_general
from weight_db import WEIGHT_SPREADSHEET_ID

SHEET_URL = f"https://docs.google.com/spreadsheets/d/{WEIGHT_SPREADSHEET_ID}/"


def run_md_main():
    st.button("◀ 이전으로 돌아가기", on_click=lambda: st.session_state.update(page="main"))
    st.title("📋 MD 나누기")

    st.button("FS 나누기",      on_click=lambda: st.session_state.update(page="md_fs"))
    st.button("SS 나누기",      on_click=lambda: st.session_state.update(page="md_ss"))
    st.button("General 나누기", on_click=lambda: st.session_state.update(page="md_general"))

    st.markdown("---")
    st.subheader("⚖️ 재고 무게 관리")
    st.link_button("🔗 구글 시트에서 무게 수정하기", SHEET_URL)


def run_md_fs_page():
    run_md_fs()

def run_md_ss_page():
    run_md_ss()

def run_md_general_page():
    run_md_general()
